# -*- coding: utf-8 -*-
"""Various utilities."""

import logging
import os
import textwrap
from datetime import datetime
from itertools import groupby
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

import orcid_client
from application import app
from config import (ENV, EXTERNAL_SP, ORCID_BASE_URL, SCOPE_ACTIVITIES_UPDATE, SCOPE_READ_LIMITED)
from models import (Affiliation, AffiliationRecord, OrcidToken, Organisation, Role, Task, User,
                    UserInvitation, UserOrg)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def send_email(template_filename,
               recipient,
               cc_email=None,
               sender=(app.config.get("APP_NAME"), app.config.get("MAIL_DEFAULT_SENDER")),
               reply_to=None,
               subject=None,
               **kwargs):
    """
    Send an email, acquiring its payload by rendering a jinja2 template
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
    plain_rendered = plain_template.make_module(
        vars=kwargs) if plain_template else html2text(str(rendered))

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
    """
    The :mod:`jinja2` extension adds a ``{% rewrap %}...{% endrewrap %}`` block
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

    def parse(self, parser):
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
    except:
        return False
    return data


def append_qs(url, **qs):
    """Appends new query strings to an arbitraty URL."""
    return url + ('&' if urlparse(url).query else '?') + urlencode(qs, doseq=True)


def track_event(category, action, label=None, value=0):
    """Track application events with Google Analytics."""
    GA_TRACKING_ID = app.config.get("GA_TRACKING_ID")
    if not GA_TRACKING_ID:
        return

    data = {
        "v": "1",  # API Version.
        "tid": GA_TRACKING_ID,  # Tracking ID / Property ID.
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


def set_server_name():
    """Set the server name for batch processes."""

    if not app.config.get("SERVER_NAME"):
        if EXTERNAL_SP:
            app.config["SERVER_NAME"] = "127.0.0.1:5000"
        else:
            app.config[
                "SERVER_NAME"] = "orcidhub.org.nz" if ENV == "prod" else ENV + ".orcidhub.org.nz"


def send_user_initation(inviter,
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
                        disambiguation_org_id=None,
                        disambiguation_org_source=None,
                        **kwargs):
    """Send an invitation to join ORCID Hub logging in via ORCID."""

    try:
        logger.info(f"*** Sending an invitation to '{first_name} {last_name} <{email}>' "
                    f"submitted by {inviter} of {org} for affiliations: {affiliation_types}")

        email = email.lower()
        user, _ = User.get_or_create(email=email)
        user.first_name = first_name
        user.last_name = last_name
        user.roles |= Role.RESEARCHER
        user.email = email
        user.organisation = org
        with app.app_context():
            email_and_organisation = email + ";" + org.name
            token = generate_confirmation_token(email_and_organisation)
            send_email(
                "email/researcher_invitation.html",
                recipient=(user.organisation.name, user.email),
                reply_to=(inviter.name, inviter.email),
                invitation_token=token,
                org_name=user.organisation.name,
                user=user)

        user.save()

        user_org, user_org_created = UserOrg.get_or_create(user=user, org=org)

        if affiliations is None and affiliation_types:
            affiliations = 0
            if affiliation_types & {"faculty", "staff"}:
                affiliations = Affiliation.EMP
            if affiliation_types & {"student", "alum"}:
                affiliations |= Affiliation.EDU
        user_org.affiliations = affiliations

        user_org.save()
        UserInvitation.create(
            invitee_id=user.id,
            inviter_id=inviter.id,
            org=org,
            email=email,
            first_name=first_name,
            last_name=last_name,
            orcid=orcid,
            department=department,
            organisation=organisation,
            city=city,
            state=state,
            country=country,
            course_or_role=course_or_role,
            start_date=start_date,
            end_date=end_date,
            affiliations=affiliations,
            disambiguation_org_id=disambiguation_org_id,
            disambiguation_org_source=disambiguation_org_source,
            token=token)

        status = "The invitation sent at " + datetime.now().isoformat(timespec="seconds")
        (AffiliationRecord.update(status=AffiliationRecord.status + "\n" + status).where(
            AffiliationRecord.status.is_null(False),
            AffiliationRecord.identifier == email).execute())
        (AffiliationRecord.update(status=status).where(
            AffiliationRecord.status.is_null(), AffiliationRecord.identifier == email).execute())

    except Exception as ex:
        logger.error(f"Exception occured while sending mails {ex}")
        raise ex


def create_or_update_affiliation(user, org_id, records, *args, **kwargs):
    """Creates or updates affiliation record of a user.

    1. Retries user edurcation and employment surramy from ORCID;
    2. Match the recodrs with the summary;
    3. If there is match update the record;
    4. If no match create a new one."""
    # TODO:
    orcid_token = None
    try:
        org = Organisation.get(id=org_id)
        orcid_token = OrcidToken.get(
            user=user, org=org, scope=SCOPE_READ_LIMITED[0] + "," + SCOPE_ACTIVITIES_UPDATE[0])
    except Exception as ex:
        logger.error(f"Exception occured while retriving ORCID Token {ex}")
        return None

    orcid_client.configuration.access_token = orcid_token.access_token
    api_instance = orcid_client.MemberAPIV20Api()

    url = urlparse(ORCID_BASE_URL)
    source_clientid = orcid_client.SourceClientId(
        host=url.hostname,
        path=org.orcid_client_id,
        uri="http://" + url.hostname + "/client/" + org.orcid_client_id)

    for task_by_user in records:
        ar = task_by_user.affiliation_record

        organisation_address = orcid_client.OrganizationAddress(city=ar.city, country=org.country)

        disambiguated_organization_details = orcid_client.DisambiguatedOrganization(
            disambiguated_organization_identifier=org.disambiguation_org_id,
            disambiguation_source=org.disambiguation_org_source)

        at = ar.affiliation_type.lower()
        if at in {"faculty", "staff", "emp"}:
            rec = orcid_client.Employment()
        elif at in {"student", "edu"}:
            rec = orcid_client.Education()
        else:
            logger.info(f"For {user} not able to determine affiliaton type with {org}")
            ar.processed_at = datetime.now()
            ar.add_status_line(
                f"Unsupported affiliation type '{at}' for {user} affiliaton type with {org}")
            ar.save()
            continue

        rec.source = orcid_client.Source(
            source_orcid=None, source_client_id=source_clientid, source_name=org.name)

        rec.organization = orcid_client.Organization(
            name=ar.organisation,
            address=organisation_address,
            disambiguated_organization=disambiguated_organization_details)

        if ar.put_code:
            rec.put_code = ar.put_code

        rec.department_name = ar.department
        rec.role_title = ar.role
        if ar.start_date:
            rec.start_date = ar.start_date.as_orcid_dict()
        if ar.end_date:
            rec.end_date = ar.end_date.as_orcid_dict()

        # TODO: need to check if the entry doesn't exist already: if it does then only update
        # TODO: handle 'update' cases when put-code is preset
        # TODO: handle updates when entry is partial (missing role, time ranges, department etc....)
        try:
            if at in {"faculty", "staff", "emp"}:
                if ar.put_code:
                    api_call = api_instance.update_employment
                else:
                    api_call = api_instance.create_employment
            elif at in {"student", "edu"}:
                if ar.put_code:
                    api_call = api_instance.update_education
                else:
                    api_call = api_instance.create_education

            params = dict(orcid=user.orcid, body=rec, _preload_content=False)
            if ar.put_code:
                params["put_code"] = ar.put_code
            resp = api_call(**params)
            logger.info(
                f"For {user} the ORCID record was {'updated' if ar.put_code else 'created'} from {org}"
            )
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    put_code = int(location.split("/")[-1])
                except:
                    logger.exception("Failed to get put-code from the response.")
                    ar.add_status_line("Failed to get put-code from the response.")
                else:
                    ar.put_code = put_code
                    ar.add_status_line(f"Affiliation record was created: {location}")
            elif resp.status == 200:
                ar.add_status_line("Affiliation record was updated")
            else:
                msg = f"Problem with adding a record to profile. Status Code: {resp.status}"
                logger.error(msg)
                ar.add_status_line(msg)

            ar.processed_at = datetime.now()
            ar.save()

        except:
            logger.exception(f"For {user} encountered exception")


def process_affiliation_records(max_rows=20):
    """Process uploaded affiliation records."""
    set_server_name()
    # TODO: optimize removing redudnt fields
    # TODO: perhaps it should be broken into 2 queries
    task_ids = set()
    tasks = (
        Task.select(Task, AffiliationRecord, User,
                    UserInvitation.id.alias("invitation_id"), OrcidToken)
        .where(AffiliationRecord.processed_at.is_null(), AffiliationRecord.is_active, (
            (User.id.is_null(False) & User.orcid.is_null(False) & OrcidToken.id.is_null(False)) | (
                (User.id.is_null() | User.orcid.is_null() | OrcidToken.id.is_null()) &
                UserInvitation.id.is_null() &
                (AffiliationRecord.status.is_null() |
                 AffiliationRecord.status.contains("sent").__invert__())))).join(
                     AffiliationRecord, on=(Task.id == AffiliationRecord.task_id)).join(
                         User,
                         JOIN.LEFT_OUTER,
                         on=((User.email == AffiliationRecord.identifier) |
                             (User.eppn == AffiliationRecord.identifier) |
                             (User.orcid == AffiliationRecord.identifier))).join(
                                 Organisation,
                                 JOIN.LEFT_OUTER,
                                 on=(Organisation.id == Task.org_id))
        .join(
            UserInvitation,
            JOIN.LEFT_OUTER,
            on=(UserInvitation.email == AffiliationRecord.identifier)).join(
                OrcidToken,
                JOIN.LEFT_OUTER,
                on=((OrcidToken.user_id == User.id) & (OrcidToken.org_id == Organisation.id) &
                    (OrcidToken.scope.contains("/activities/update")))).limit(max_rows))
    for (task_id, org_id, user), tasks_by_user in groupby(
            tasks, lambda t: (t.id, t.org_id, t.affiliation_record.user, )):
        if (user.id is None or user.orcid is None or not OrcidToken.select().where(
            (OrcidToken.user_id == user.id) & (OrcidToken.org_id == org_id) &
            (OrcidToken.scope.contains("/activities/update"))).exists()):  # noqa: E127, E129

            # maps invitation attributes to affiliation type set:
            # - the user who uploaded the task;
            # - the user organisation;
            # - the invitee identifier (email address in this case);
            # - the invitee first_name;
            # - the invitee last_name
            invitation_dict = {
                k: set(t.affiliation_record.affiliation_type.lower() for t in tasks)
                for k, tasks in groupby(
                    tasks_by_user,
                    lambda t: (t.created_by, t.org, t.affiliation_record.identifier, t.affiliation_record.first_name, t.affiliation_record.last_name)  # noqa: E501
                )  # noqa: E501
            }
            for invitation, affiliations in invitation_dict.items():
                send_user_initation(*invitation, affiliations)
        else:  # user exits and we have tokens
            create_or_update_affiliation(user, org_id, tasks_by_user)
        task_ids.add(task_id)
    for task in Task.select().where(Task.id << task_ids):
        # The task is completed (all recores are processed):
        if not (AffiliationRecord.select().where(
                AffiliationRecord.task_id == task.id,
                AffiliationRecord.processed_at.is_null()).exists()):
            task.completed_at = datetime.now()
            task.save()
            with app.app_context():
                export_url = flask.url_for(
                    "affiliationrecord.export", export_type="csv", task_id=task.id, _external=True)
                send_email(
                    "email/task_completed.html",
                    subject="Affiliation Process Update",
                    recipient=(task.created_by.name, task.created_by.email),
                    export_url=export_url,
                    filename=task.filename)
