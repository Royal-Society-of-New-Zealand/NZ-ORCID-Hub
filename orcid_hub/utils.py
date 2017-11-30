# -*- coding: utf-8 -*-
"""Various utilities."""

import logging
import os
import textwrap
from datetime import datetime
from itertools import filterfalse, groupby
from os.path import splitext
from urllib.parse import urlencode, urlparse

import emails
import flask
import jinja2
import jinja2.ext
import requests
from flask_login import current_user
from html2text import html2text
from itsdangerous import URLSafeTimedSerializer
from peewee import JOIN

from . import app, orcid_client
from .config import ENV, EXTERNAL_SP
from .models import (AFFILIATION_TYPES, Affiliation, AffiliationRecord, FundingContributor,
                     FundingRecord, OrcidToken, Organisation, Role, Task, Url, User,
                     UserInvitation, UserOrg)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

EDU_CODES = {"student", "edu"}
EMP_CODES = {"faculty", "staff", "emp"}


def send_email(template_filename,
               recipient,
               cc_email=None,
               sender=(app.config.get("APP_NAME"), app.config.get("MAIL_DEFAULT_SENDER")),
               reply_to=None,
               subject=None,
               **kwargs):
    """Send an email, acquiring its payload by rendering a jinja2 template.

    :type template_filename: :class:`str`
    :param subject: the subject of the email
    :param template_filename: name of the template_filename file in ``templates/emails`` to use
    :type recipient: :class:`tuple` (:class:`str`, :class:`str`)
    :param recipient: 'To' (name, email)
    :type sender: :class:`tuple` (:class:`str`, :class:`str`)
    :param sender: 'From' (name, email)
    * `recipient` and `sender` are made available to the template as variables
    * In any email tuple, name may be ``None``
    * The subject is retrieved from a sufficiently-global template variable;
      typically set by placing something like
      ``{% set subject = "My Subject" %}``
      at the top of the template used (it may be inside some blocks
      (if, elif, ...) but not others (rewrap, block, ...).
      If it's not present, it defaults to "My Subject".
    * With regards to line lengths: :class:`email.mime.text.MIMEText` will
      (at least, in 2.7) encode the body of the text in base64 before sending
      it, text-wrapping the base64 data. You will therefore not have any
      problems with SMTP line length restrictions, and any concern to line
      lengths is purely aesthetic or to be nice to the MUA.
      :class:`RewrapExtension` may be used to wrap blocks of text nicely.
      Note that ``{{ variables }}`` in manually wrapped text can cause
      problems!
    """
    if not template_filename.endswith(".html"):
        template_filename += ".html"
    if flask.current_app:
        # use the app's env if it's available, so that url_for may be used
        jinja_env = flask.current_app.jinja_env
    else:
        path = os.path.join(os.path.dirname(__file__), "templates")
        loader = jinja2.FileSystemLoader(path)
        jinja_env = jinja2.Environment(
            loader=loader, extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_'])

    jinja_env = jinja_env.overlay(autoescape=False, extensions=[RewrapExtension])

    def get_template(filename):
        try:
            return jinja_env.get_template(filename)
        except jinja2.exceptions.TemplateNotFound:
            return None

    def _jinja2_email(name, email):
        if name is None:
            hint = 'name was not set for email {0}'.format(email)
            name = jinja_env.undefined(name='name', hint=hint)
        return {"name": name, "email": email}

    template = get_template(template_filename)
    plain_template = get_template(splitext(template_filename)[0] + ".plain")

    kwargs["sender"] = _jinja2_email(*sender)
    kwargs["recipient"] = _jinja2_email(*recipient)
    if subject is not None:
        kwargs["subject"] = subject
    if reply_to is None:
        reply_to = sender

    rendered = template.make_module(vars=kwargs)
    plain_rendered = plain_template.make_module(vars=kwargs) if plain_template else html2text(
        str(rendered))

    if subject is None:
        subject = getattr(rendered, "subject", "Welcome to the NZ ORCID Hub")

    msg = emails.html(
        subject=subject,
        mail_from=(app.config.get("APP_NAME", "ORCID Hub"), app.config.get("MAIL_DEFAULT_SENDER")),
        html=str(rendered),
        text=str(plain_rendered))
    dkip_key_path = os.path.join(app.root_path, ".keys", "dkim.key")
    if os.path.exists(dkip_key_path):
        msg.dkim(key=open(dkip_key_path), domain="orcidhub.org.nz", selector="default")
    if cc_email:
        msg.cc.append(cc_email)
    msg.set_headers({"reply-to": reply_to})
    msg.mail_to.append(recipient)

    msg.send(smtp=dict(host=app.config["MAIL_SERVER"], port=app.config["MAIL_PORT"]))


class RewrapExtension(jinja2.ext.Extension):
    """The :mod:`jinja2` extension adds a ``{% rewrap %}...{% endrewrap %}`` block.

    The contents in the rewrap block are modified as follows
    * whitespace at the start and end of lines is discarded
    * the contents are split into 'paragraphs' separated by blank lines
    * empty paragraphs are discarded - so two blank lines is equivalent to
      one blank line, and blank lines at the start and end of the block
      are effectively discarded
    * lines in each paragraph are joined to one line, and then text wrapped
      to lines `width` characters wide
    * paragraphs are re-joined into text, with blank lines insert in between
      them
    It does not insert a newline at the end of the block, which means that::
        Something, then a blank line
        {% block rewrap %}
        some text
        {% endblock %}
        After another blank line
    will do what you expect.
    You may optionally specify the width like so::
        {% rewrap 72 %}
    It defaults to 78.
    """

    tags = set(['rewrap'])

    def parse(self, parser):  # noqa: D102
        # first token is 'rewrap'
        lineno = parser.stream.next().lineno

        if parser.stream.current.type != 'block_end':
            width = parser.parse_expression()
        else:
            width = jinja2.nodes.Const(78)

        body = parser.parse_statements(['name:endrewrap'], drop_needle=True)

        call = self.call_method('_rewrap', [width])
        return jinja2.nodes.CallBlock(call, [], [], body).set_lineno(lineno)

    def _rewrap(self, width, caller):
        contents = caller()
        lines = [line.strip() for line in contents.splitlines()]
        lines.append('')

        paragraphs = []
        start = 0
        while start != len(lines):
            end = lines.index('', start)
            if start != end:
                paragraph = ' '.join(lines[start:end])
                paragraphs.append(paragraph)
            start = end + 1

        new_lines = []

        for paragraph in paragraphs:
            if new_lines:
                new_lines.append('')
            new_lines += textwrap.wrap(paragraph, width)

        # under the assumption that there will be a newline immediately after
        # the endrewrap block, don't put a newline on the end.
        return '\n'.join(new_lines)


def generate_confirmation_token(*args, **kwargs):
    """Generate Organisation registration confirmation token."""
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    salt = app.config["SALT"]
    if len(kwargs) == 0:
        return serializer.dumps(args[0] if len(args) == 1 else args, salt=salt)
    else:
        return serializer.dumps(kwargs.values()[0] if len(kwargs) == 1 else kwargs, salt=salt)


# Token Expiry after 15 days.
def confirm_token(token, expiration=1300000):
    """Genearate confirmaatin token."""
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    try:
        data = serializer.loads(token, salt=app.config["SALT"], max_age=expiration)
    except Exception:
        return False
    return data


def append_qs(url, **qs):
    """Append new query strings to an arbitraty URL."""
    return url + ('&' if urlparse(url).query else '?') + urlencode(qs, doseq=True)


def track_event(category, action, label=None, value=0):
    """Track application events with Google Analytics."""
    ga_tracking_id = app.config.get("GA_TRACKING_ID")
    if not ga_tracking_id:
        return

    data = {
        "v": "1",  # API Version.
        "tid": ga_tracking_id,  # Tracking ID / Property ID.
        # Anonymous Client Identifier. Ideally, this should be a UUID that
        # is associated with particular user, device, or browser instance.
        "cid": current_user.uuid,
        "t": "event",  # Event hit type.
        "ec": category,  # Event category.
        "ea": action,  # Event action.
        "el": label,  # Event label.
        "ev": value,  # Event value, must be an integer
    }

    response = requests.post("http://www.google-analytics.com/collect", data=data)

    # If the request fails, this will raise a RequestException. Depending
    # on your application's needs, this may be a non-error and can be caught
    # by the caller.
    response.raise_for_status()
    # Returning response only for test, but can be used in application for some other reasons
    return response


def set_server_name():
    """Set the server name for batch processes."""
    if not app.config.get("SERVER_NAME"):
        if EXTERNAL_SP:
            app.config["SERVER_NAME"] = "127.0.0.1:5000"
        else:
            app.config[
                "SERVER_NAME"] = "orcidhub.org.nz" if ENV == "prod" else ENV + ".orcidhub.org.nz"


def send_funding_invitation(inviter, org, email, name, task_id=None, **kwargs):
    """Send an funding invitation to join ORCID Hub logging in via ORCID."""
    try:
        logger.info(f"*** Sending an funding invitation to '{name} <{email}>' "
                    f"submitted by {inviter} of {org}")

        email = email.lower()
        user, user_created = User.get_or_create(email=email)
        if user_created:
            user.name = name
            user.created_by = inviter.id
        else:
            user.updated_by = inviter.id

        user.organisation = org
        user.roles |= Role.RESEARCHER

        token = generate_confirmation_token(email=email, org=org.name)
        with app.app_context():
            url = flask.url_for('orcid_login', invitation_token=token, _external=True)
            invitation_url = flask.url_for(
                "short_url", short_id=Url.shorten(url).short_id, _external=True)
            send_email(
                "email/funding_invitation.html",
                recipient=(user.organisation.name, user.email),
                reply_to=(inviter.name, inviter.email),
                invitation_url=invitation_url,
                org_name=user.organisation.name,
                user=user)

        user.save()

        user_org, user_org_created = UserOrg.get_or_create(user=user, org=org)
        if user_org_created:
            user_org.created_by = inviter.id
        else:
            user_org.updated_by = inviter.id
        user_org.affiliations = 0
        user_org.save()

        ui = UserInvitation.create(
            task_id=task_id,
            invitee_id=user.id,
            inviter_id=inviter.id,
            org=org,
            email=email,
            first_name=name,
            affiliations=0,
            organisation=org.name,
            disambiguated_id=org.disambiguated_id,
            disambiguation_source=org.disambiguation_source,
            token=token)

        status = "The invitation sent at " + datetime.now().isoformat(timespec="seconds")
        (FundingContributor.update(status=FundingContributor.status + "\n" + status).where(
            FundingContributor.status.is_null(False), FundingContributor.email == email).execute())
        (FundingContributor.update(status=status).where(
            FundingContributor.status.is_null(), FundingContributor.email == email).execute())
        return ui

    except Exception as ex:
        logger.error(f"Exception occured while sending mails {ex}")
        raise ex


def create_or_update_funding(user, org_id, records, *args, **kwargs):
    """Create or update funding record of a user."""
    records = list(unique_everseen(records, key=lambda t: t.funding_record.id))
    org = Organisation.get(id=org_id)
    client_id = org.orcid_client_id
    api = orcid_client.MemberAPI(org, user)

    profile_record = api.get_record()

    if profile_record:
        activities = profile_record.get("activities-summary")

        def is_org_rec(rec):
            return (rec.get("source").get("source-client-id")
                    and rec.get("source").get("source-client-id").get("path") == client_id)

        fundings = []

        for r in activities.get("fundings").get("group"):
            fs = r.get("funding-summary")[0]
            if is_org_rec(fs):
                fundings.append(fs)

        taken_put_codes = {
            r.funding_record.funding_contributor.put_code
            for r in records if r.funding_record.funding_contributor.put_code
        }

        def match_put_code(records, funding_record, funding_contributor):
            """Match and asign put-code to a single funding record and the existing ORCID records."""
            if funding_contributor.put_code:
                return
            for r in records:
                put_code = r.get("put-code")
                if put_code in taken_put_codes:
                    continue

                if ((r.get("title") is None and r.get("title").get("title") is None
                     and r.get("title").get("title").get("value") is None and r.get("type") is None
                     and r.get("organization") is None
                     and r.get("organization").get("name") is None)
                        or (r.get("title").get("title").get("value") == funding_record.title
                            and r.get("type") == funding_record.type
                            and r.get("organization").get("name") == funding_record.org_name)):
                    funding_contributor.put_code = put_code
                    funding_contributor.save()
                    taken_put_codes.add(put_code)
                    app.logger.debug(
                        f"put-code {put_code} was asigned to the funding record "
                        f"(ID: {funding_record.id}, Task ID: {funding_record.task_id})")
                    break

        for task_by_user in records:
            fr = task_by_user.funding_record
            fc = task_by_user.funding_record.funding_contributor
            match_put_code(fundings, fr, fc)

        for task_by_user in records:
            fc = task_by_user.funding_record.funding_contributor

            try:
                put_code, orcid, created = api.create_or_update_funding(task_by_user)
                if created:
                    fc.add_status_line(f"Funding record was created.")
                else:
                    fc.add_status_line(f"Funding record was updated.")
                fc.orcid = orcid
                fc.put_code = put_code
                fc.processed_at = datetime.now()

            except Exception as ex:
                logger.exception(f"For {user} encountered exception")
                fc.add_status_line(f"Exception occured processing the record: {ex}.")

            finally:
                fc.save()
    else:
        # TODO: Invitation resend in case user revokes organisation permissions
        app.logger.debug(f"Should resend an invite to the researcher asking for permissions")
        return


def send_user_invitation(inviter,
                         org,
                         email,
                         first_name,
                         last_name,
                         affiliation_types=None,
                         orcid=None,
                         department=None,
                         organisation=None,
                         city=None,
                         state=None,
                         country=None,
                         course_or_role=None,
                         start_date=None,
                         end_date=None,
                         affiliations=None,
                         disambiguated_id=None,
                         disambiguation_source=None,
                         task_id=None,
                         **kwargs):
    """Send an invitation to join ORCID Hub logging in via ORCID."""
    try:
        logger.info(f"*** Sending an invitation to '{first_name} {last_name} <{email}>' "
                    f"submitted by {inviter} of {org} for affiliations: {affiliation_types}")

        email = email.lower()
        user, user_created = User.get_or_create(email=email)
        if user_created:
            user.first_name = first_name
            user.last_name = last_name
        user.organisation = org
        user.roles |= Role.RESEARCHER

        token = generate_confirmation_token(email=email, org=org.name)
        with app.app_context():
            url = flask.url_for('orcid_login', invitation_token=token, _external=True)
            invitation_url = flask.url_for(
                "short_url", short_id=Url.shorten(url).short_id, _external=True)
            send_email(
                "email/researcher_invitation.html",
                recipient=(user.organisation.name, user.email),
                reply_to=(inviter.name, inviter.email),
                invitation_url=invitation_url,
                org_name=user.organisation.name,
                user=user)

        user.save()

        user_org, user_org_created = UserOrg.get_or_create(user=user, org=org)
        if user_org_created:
            user_org.created_by = inviter.id
        else:
            user_org.updated_by = inviter.id

        if affiliations is None and affiliation_types:
            affiliations = 0
            if affiliation_types & {"faculty", "staff"}:
                affiliations = Affiliation.EMP
            if affiliation_types & {"student", "alum"}:
                affiliations |= Affiliation.EDU
        user_org.affiliations = affiliations

        user_org.save()
        ui = UserInvitation.create(
            task_id=task_id,
            invitee_id=user.id,
            inviter_id=inviter.id,
            org=org,
            email=email,
            first_name=first_name,
            last_name=last_name,
            orcid=orcid,
            department=department,
            organisation=org.name,
            city=city,
            state=state,
            country=country,
            course_or_role=course_or_role,
            start_date=start_date,
            end_date=end_date,
            affiliations=affiliations,
            disambiguated_id=disambiguated_id,
            disambiguation_source=disambiguation_source,
            token=token)

        status = "The invitation sent at " + datetime.now().isoformat(timespec="seconds")
        (AffiliationRecord.update(status=AffiliationRecord.status + "\n" + status).where(
            AffiliationRecord.status.is_null(False), AffiliationRecord.email == email).execute())
        (AffiliationRecord.update(status=status).where(AffiliationRecord.status.is_null(),
                                                       AffiliationRecord.email == email).execute())
        return ui

    except Exception as ex:
        logger.error(f"Exception occured while sending mails {ex}")
        raise ex


def unique_everseen(iterable, key=None):
    """List unique elements, preserving order. Remember all elements ever seen.

    The snippet is taken form https://docs.python.org/3.6/library/itertools.html#itertools-recipes
    >>> unique_everseen('AAAABBBCCDAABBB')
    A B C D
    >>> unique_everseen('ABBCcAD', str.lower)
    A B C D
    """
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element


def create_or_update_affiliations(user, org_id, records, *args, **kwargs):
    """Create or update affiliation record of a user.

    1. Retries user edurcation and employment surramy from ORCID;
    2. Match the recodrs with the summary;
    3. If there is match update the record;
    4. If no match create a new one.
    """
    records = list(unique_everseen(records, key=lambda t: t.affiliation_record.id))
    org = Organisation.get(id=org_id)
    client_id = org.orcid_client_id
    api = orcid_client.MemberAPI(org, user)
    profile_record = api.get_record()
    if profile_record:
        activities = profile_record.get("activities-summary")

        def is_org_rec(rec):
            return (rec.get("source").get("source-client-id")
                    and rec.get("source").get("source-client-id").get("path") == client_id)

        employments = [
            r for r in (activities.get("employments").get("employment-summary")) if is_org_rec(r)
        ]
        educations = [
            r for r in (activities.get("educations").get("education-summary")) if is_org_rec(r)
        ]

        taken_put_codes = {
            r.affiliation_record.put_code
            for r in records if r.affiliation_record.put_code
        }

        def match_put_code(records, affiliation_record):
            """Match and asign put-code to a single affiliation record and the existing ORCID records."""
            if affiliation_record.put_code:
                return
            for r in records:
                put_code = r.get("put-code")
                if put_code in taken_put_codes:
                    continue

                if ((r.get("start-date") is None and r.get("end-date") is None
                     and r.get("department-name") is None and r.get("role-title") is None)
                        or (r.get("start-date") == affiliation_record.start_date
                            and r.get("department-name") == affiliation_record.department_name
                            and r.get("role-title") == affiliation_record.role_title)):
                    affiliation_record.put_code = put_code
                    taken_put_codes.add(put_code)
                    app.logger.debug(
                        f"put-code {put_code} was asigned to the affiliation record "
                        f"(ID: {affiliation_record.id}, Task ID: {affiliation_record.task_id})")
                    break

        for task_by_user in records:
            ar = task_by_user.affiliation_record
            at = ar.affiliation_type.lower()
            if at in EMP_CODES:
                match_put_code(employments, ar)
            elif at in EDU_CODES:
                match_put_code(educations, ar)

        for task_by_user in records:
            ar = task_by_user.affiliation_record
            at = ar.affiliation_type.lower()

            if at in EMP_CODES:
                affiliation = Affiliation.EMP
            elif at in EDU_CODES:
                affiliation = Affiliation.EDU
            else:
                logger.info(f"For {user} not able to determine affiliaton type with {org}")
                ar.processed_at = datetime.now()
                ar.add_status_line(f"Unsupported affiliation type '{at}' allowed values are: " +
                                   ', '.join(at for at in AFFILIATION_TYPES))
                ar.save()
                continue

            try:
                put_code, orcid, created = api.create_or_update_affiliation(
                    affiliation=affiliation, **ar._data)
                if created:
                    ar.add_status_line(f"{str(affiliation)} record was created.")
                else:
                    ar.add_status_line(f"{str(affiliation)} record was updated.")
                ar.orcid = orcid
                ar.put_code = put_code
                ar.processed_at = datetime.now()

            except Exception as ex:
                logger.exception(f"For {user} encountered exception")
                ar.add_status_line(f"Exception occured processing the record: {ex}.")

            finally:
                ar.save()
    else:
        for task_by_user in records:
            user = User.get(
                email=task_by_user.affiliation_record.email, organisation=task_by_user.org)
            user_org = UserOrg.get(user=user, org=task_by_user.org)
            token = generate_confirmation_token(email=user.email, org=org.name)
            with app.app_context():
                url = flask.url_for('orcid_login', invitation_token=token, _external=True)
                invitation_url = flask.url_for(
                    "short_url", short_id=Url.shorten(url).short_id, _external=True)
                send_email(
                    "email/researcher_reinvitation.html",
                    recipient=(user.organisation.name, user.email),
                    reply_to=(task_by_user.created_by.name, task_by_user.created_by.email),
                    invitation_url=invitation_url,
                    org_name=user.organisation.name,
                    user=user)
            UserInvitation.create(
                invitee_id=user.id,
                inviter_id=task_by_user.created_by.id,
                org=org,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                orcid=user.orcid,
                organisation=org.name,
                city=org.city,
                state=org.state,
                country=org.country,
                start_date=task_by_user.affiliation_record.start_date,
                end_date=task_by_user.affiliation_record.end_date,
                affiliations=user_org.affiliations,
                disambiguated_id=org.disambiguated_id,
                disambiguation_source=org.disambiguation_source,
                token=token)

            status = "Exception occured while accessing user's profile. " \
                     "Hence, The invitation resent at " + datetime.now().isoformat(timespec="seconds")
            (AffiliationRecord.update(status=AffiliationRecord.status + "\n" + status).where(
                AffiliationRecord.status.is_null(False),
                AffiliationRecord.email == user.email).execute())
            (AffiliationRecord.update(status=status).where(
                AffiliationRecord.status.is_null(),
                AffiliationRecord.email == user.email).execute())
            return


def process_funding_records(max_rows=20):
    """Process uploaded affiliation records."""
    set_server_name()
    task_ids = set()
    funding_ids = set()
    """This query is to retrieve Tasks associated with funding records, which are not processed but are active"""

    tasks = (Task.select(
        Task, FundingRecord, FundingContributor,
        User, UserInvitation.id.alias("invitation_id"), OrcidToken).where(
            FundingRecord.processed_at.is_null(), FundingContributor.processed_at.is_null(),
            FundingRecord.is_active,
            (OrcidToken.id.is_null(False) |
             ((FundingContributor.status.is_null()) |
              (FundingContributor.status.contains("sent").__invert__())))).join(
                  FundingRecord, on=(Task.id == FundingRecord.task_id)).join(
                      FundingContributor,
                      on=(FundingRecord.id == FundingContributor.funding_record_id)).join(
                          User,
                          JOIN.LEFT_OUTER,
                          on=((User.email == FundingContributor.email) |
                              (User.orcid == FundingContributor.orcid)))
             .join(Organisation, JOIN.LEFT_OUTER, on=(Organisation.id == Task.org_id)).join(
                 UserInvitation,
                 JOIN.LEFT_OUTER,
                 on=((UserInvitation.email == FundingContributor.email)
                     & (UserInvitation.task_id == Task.id))).join(
                         OrcidToken,
                         JOIN.LEFT_OUTER,
                         on=((OrcidToken.user_id == User.id)
                             & (OrcidToken.org_id == Organisation.id)
                             & (OrcidToken.scope.contains("/activities/update")))).limit(max_rows))

    for (task_id, org_id, funding_record_id, user), tasks_by_user in groupby(tasks, lambda t: (
            t.id,
            t.org_id,
            t.funding_record.id,
            t.funding_record.funding_contributor.user,)):
        """If we have the token associated to the user then update the funding record, otherwise send him an invite"""
        if (user.id is None or user.orcid is None or not OrcidToken.select().where(
            (OrcidToken.user_id == user.id) & (OrcidToken.org_id == org_id) &
            (OrcidToken.scope.contains("/activities/update"))).exists()):  # noqa: E127, E129

            for k, tasks in groupby(
                    tasks_by_user,
                    lambda t: (
                        t.created_by,
                        t.org,
                        t.funding_record.funding_contributor.email,
                        t.funding_record.funding_contributor.name, )
            ):  # noqa: E501
                send_funding_invitation(*k, task_id=task_id)
        else:
            create_or_update_funding(user, org_id, tasks_by_user)
        task_ids.add(task_id)
        funding_ids.add(funding_record_id)

        for funding_record in FundingRecord.select().where(FundingRecord.id << funding_ids):
            # The funding record is processed for all contributors
            if not (FundingContributor.select().where(
                    FundingContributor.funding_record_id == funding_record.id,
                    FundingContributor.processed_at.is_null()).exists()):
                funding_record.processed_at = datetime.now()
                funding_record.add_status_line(
                    f"Funding record is processed, and now the funding record will appear on contributors profile"
                )
                funding_record.save()

        for task in Task.select().where(Task.id << task_ids):
            # The task is completed (Once all records are processed):
            if not (FundingRecord.select().where(FundingRecord.task_id == task.id,
                                                 FundingRecord.processed_at.is_null()).exists()):
                task.completed_at = datetime.now()
                task.save()


def process_affiliation_records(max_rows=20):
    """Process uploaded affiliation records."""
    set_server_name()
    # TODO: optimize removing redudnt fields
    # TODO: perhaps it should be broken into 2 queries
    task_ids = set()
    tasks = (Task.select(
        Task, AffiliationRecord, User, UserInvitation.id.alias("invitation_id"), OrcidToken).where(
            AffiliationRecord.processed_at.is_null(), AffiliationRecord.is_active,
            ((User.id.is_null(False) & User.orcid.is_null(False) & OrcidToken.id.is_null(False)) |
             ((User.id.is_null() | User.orcid.is_null() | OrcidToken.id.is_null()) &
              UserInvitation.id.is_null() &
              (AffiliationRecord.status.is_null()
               | AffiliationRecord.status.contains("sent").__invert__())))).join(
                   AffiliationRecord, on=(Task.id == AffiliationRecord.task_id)).join(
                       User,
                       JOIN.LEFT_OUTER,
                       on=((User.email == AffiliationRecord.email) |
                           (User.orcid == AffiliationRecord.orcid))).join(
                               Organisation, JOIN.LEFT_OUTER, on=(Organisation.id == Task.org_id))
             .join(
                 UserInvitation,
                 JOIN.LEFT_OUTER,
                 on=((UserInvitation.email == AffiliationRecord.email) &
                     (UserInvitation.task_id == Task.id))).join(
                         OrcidToken,
                         JOIN.LEFT_OUTER,
                         on=((OrcidToken.user_id == User.id) &
                             (OrcidToken.org_id == Organisation.id) &
                             (OrcidToken.scope.contains("/activities/update")))).limit(max_rows))
    for (task_id, org_id, user), tasks_by_user in groupby(tasks, lambda t: (
            t.id,
            t.org_id,
            t.affiliation_record.user, )):
        if (user.id is None or user.orcid is None or not OrcidToken.select().where(
            (OrcidToken.user_id == user.id) & (OrcidToken.org_id == org_id) &
            (OrcidToken.scope.contains("/activities/update"))).exists()):  # noqa: E127, E129

            # maps invitation attributes to affiliation type set:
            # - the user who uploaded the task;
            # - the user organisation;
            # - the invitee email;
            # - the invitee first_name;
            # - the invitee last_name
            invitation_dict = {
                k: set(t.affiliation_record.affiliation_type.lower() for t in tasks)
                for k, tasks in groupby(
                    tasks_by_user,
                    lambda t: (t.created_by, t.org, t.affiliation_record.email, t.affiliation_record.first_name, t.affiliation_record.last_name)  # noqa: E501
                )  # noqa: E501
            }
            for invitation, affiliations in invitation_dict.items():
                send_user_invitation(*invitation, affiliations, task_id=task_id)
        else:  # user exits and we have tokens
            create_or_update_affiliations(user, org_id, tasks_by_user)
        task_ids.add(task_id)
    for task in Task.select().where(Task.id << task_ids):
        # The task is completed (all recores are processed):
        if not (AffiliationRecord.select().where(
                AffiliationRecord.task_id == task.id,
                AffiliationRecord.processed_at.is_null()).exists()):
            task.completed_at = datetime.now()
            task.save()
            error_count = AffiliationRecord.select().where(
                AffiliationRecord.task_id == task.id, AffiliationRecord.status**"%error%").count()
            row_count = task.record_count
            orcid_rec_count = task.affiliationrecord_set.select(
                AffiliationRecord.orcid).distinct().count()

            with app.app_context():
                protocol_scheme = 'http'
                if not EXTERNAL_SP:
                    protocol_scheme = 'https'
                export_url = flask.url_for(
                    "affiliationrecord.export",
                    export_type="csv",
                    _scheme=protocol_scheme,
                    task_id=task.id,
                    _external=True)
                send_email(
                    "email/task_completed.html",
                    subject="Affiliation Process Update",
                    recipient=(task.created_by.name, task.created_by.email),
                    error_count=error_count,
                    row_count=row_count,
                    orcid_rec_count=orcid_rec_count,
                    export_url=export_url,
                    filename=task.filename)
