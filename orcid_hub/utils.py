# -*- coding: utf-8 -*-
"""Various utilities."""

import json
import logging
import os
import random
import string
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from itertools import filterfalse, groupby
from urllib.parse import quote, urlencode, urlparse

import chardet
import emails
import flask
import requests
import yaml
from flask import request, url_for
from flask_login import current_user
from html2text import html2text
from itsdangerous import (BadSignature, SignatureExpired, TimedJSONWebSignatureSerializer)
from jinja2 import Template
from orcid_api.rest import ApiException
from peewee import JOIN, SQL
from yaml.dumper import Dumper
from yaml.representer import SafeRepresenter

from . import app, orcid_client, rq
from .models import (AFFILIATION_TYPES, Affiliation, AffiliationRecord, Delegate, FundingInvitee,
                     FundingRecord, KeywordRecord, Log, OtherNameRecord, OrcidToken, Organisation,
                     OrgInvitation, PartialDate, PeerReviewExternalId, PeerReviewInvitee,
                     PeerReviewRecord, ResearcherUrlRecord, Role, Task, User, UserInvitation,
                     UserOrg, WorkInvitee, WorkRecord, get_val)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

EDU_CODES = {"student", "edu", "education"}
EMP_CODES = {"faculty", "staff", "emp", "employment"}

ENV = app.config.get("ENV")
EXTERNAL_SP = app.config.get("EXTERNAL_SP")


def get_next_url():
    """Retrieve and sanitize next/return URL."""
    _next = request.args.get("next") or request.args.get("_next") or request.args.get("url")

    if _next and ("orcidhub.org.nz" in _next or _next.startswith("/") or "127.0" in _next
                  or "localhost" in _next or "c9users.io" in _next):
        return _next

    try:
        if Delegate.select().where(Delegate.hostname ** f"%{urlparse(_next).netloc}%").exists():
            return _next
    except:
        pass

    return None


def is_valid_url(url):
    """Validate URL (expexted to have a path)."""
    try:
        result = urlparse(url)
        return result.scheme and result.netloc and (result.path or result.path == '')
    except:
        return False


def read_uploaded_file(form):
    """Read up the whole content and deconde it and return the whole content."""
    if "file_" not in request.files:
        return
    raw = request.files[form.file_.name].read()
    detected_encoding = chardet.detect(raw).get('encoding')
    if detected_encoding:
        return raw.decode(detected_encoding)
    else:
        for encoding in "utf-8", "utf-8-sig", "utf-16":
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
    return raw.decode("latin-1")


def send_email(template,
               recipient,
               cc_email=None,
               sender=(app.config.get("APP_NAME"), app.config.get("MAIL_DEFAULT_SENDER")),
               reply_to=None,
               subject=None,
               base=None,
               logo=None,
               org=None,
               **kwargs):
    """Send an email, acquiring its payload by rendering a jinja2 template.

    :type template: :class:`str`
    :param subject: the subject of the email
    :param base: the base template of the email messagess
    :param template: name of the template file in ``templates/emails`` to use
    :type recipient: :class:`tuple` (:class:`str`, :class:`str`)
    :param recipient: 'To' (name, email) or just an email address
    :type sender: :class:`tuple` (:class:`str`, :class:`str`)
    :param sender: 'From' (name, email)
    :param org: organisation on which behalf the email is sent
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
    if not org and current_user and not current_user.is_anonymous:
        org = current_user.organisation
    app = flask.current_app
    jinja_env = flask.current_app.jinja_env

    if logo is None:
        if org and org.logo:
            logo = url_for("logo_image", token=org.logo.token, _external=True)
        else:
            logo = url_for("static", filename="images/banner-small.png", _external=True)

    if not base and org:
        if org.email_template_enabled and org.email_template:
            base = org.email_template

    if not base:
        base = app.config.get("DEFAULT_EMAIL_TEMPLATE")

    jinja_env = jinja_env.overlay(autoescape=False)

    def _jinja2_email(name, email):
        if name is None:
            hint = 'name was not set for email {0}'.format(email)
            name = jinja_env.undefined(name='name', hint=hint)
        return {"name": name, "email": email}

    if '\n' not in template and template.endswith(".html"):
        template = jinja_env.get_template(template)
    else:
        template = Template(template)

    kwargs["sender"] = _jinja2_email(*sender)
    if isinstance(recipient, str):
        recipient = (recipient, recipient, )
    kwargs["recipient"] = _jinja2_email(*recipient)
    if subject is not None:
        kwargs["subject"] = subject
    if reply_to is None:
        reply_to = sender

    rendered = template.make_module(vars=kwargs)
    if subject is None:
        subject = getattr(rendered, "subject", "Welcome to the NZ ORCID Hub")

    html_msg = base.format(
        EMAIL=kwargs["recipient"]["email"],
        SUBJECT=subject,
        MESSAGE=str(rendered),
        LOGO=logo,
        BASE_URL=url_for("index", _external=True)[:-1],
        INCLUDED_URL=kwargs.get("invitation_url", '') or kwargs.get("include_url", ''))

    plain_msg = html2text(html_msg)

    msg = emails.html(
        subject=subject,
        mail_from=(app.config.get("APP_NAME", "ORCID Hub"), app.config.get("MAIL_DEFAULT_SENDER")),
        html=html_msg,
        text=plain_msg)
    dkim_key_path = app.config["DKIM_KEY_PATH"]
    if os.path.exists(dkim_key_path):
        msg.dkim(key=open(dkim_key_path), domain="orcidhub.org.nz", selector="default")
    elif dkim_key_path:
        raise Exception(f"Cannot find DKIM key file: {dkim_key_path}!")
    if cc_email:
        msg.cc.append(cc_email)
    msg.set_headers({"reply-to": reply_to})
    msg.mail_to.append(recipient)
    resp = msg.send(smtp=dict(host=app.config["MAIL_SERVER"], port=app.config["MAIL_PORT"]))
    if not resp.success:
        raise Exception(f"Failed to email the message: {resp.error}. Please contact a Hub administrator!")


def new_invitation_token(length=5):
    """Generate a unique invitation token."""
    while True:
        token = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
        if not (UserInvitation.select(SQL("1")).where(UserInvitation.token == token)
                | OrgInvitation.select(SQL("1")).where(OrgInvitation.token == token)).exists():
            break
    return token


def generate_confirmation_token(*args, expiration=1300000, **kwargs):
    """Generate Organisation registration confirmation token.

    Invitation Token Expiry for Admins is 15 days, whereas for researchers the token expiry is of 30 days.
    """
    serializer = TimedJSONWebSignatureSerializer(app.secret_key, expires_in=expiration)
    if len(kwargs) == 0:
        return serializer.dumps(args[0] if len(args) == 1 else args)
    else:
        return serializer.dumps(kwargs.values()[0] if len(kwargs) == 1 else kwargs)


def confirm_token(token, unsafe=False):
    """Genearate confirmaatin token."""
    serializer = TimedJSONWebSignatureSerializer(app.secret_key)
    # TODO: remove teh global SALT
    salt = app.config.get("SALT")
    try:
        if unsafe:
            try:
                data = serializer.loads_unsafe(token, salt=salt)
            except BadSignature:  # try again w/o the global salt
                data = serializer.loads_unsafe(token)
        else:
            try:
                data = serializer.loads(token, salt=salt)
            except BadSignature:  # try again w/o the global salt
                data = serializer.loads(token)
    except SignatureExpired as ex:
        return False, ex.payload

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


def send_work_funding_peer_review_invitation(inviter, org, email, first_name=None, last_name=None, task_id=None,
                                             invitation_template=None, token_expiry_in_sec=1300000, **kwargs):
    """Send a work, funding or peer review invitation to join ORCID Hub logging in via ORCID."""
    try:
        logger.info(f"*** Sending an invitation to '{first_name} <{email}>' "
                    f"submitted by {inviter} of {org}")

        email = email.lower()
        user, user_created = User.get_or_create(email=email)
        if user_created:
            user.created_by = inviter.id
        else:
            user.updated_by = inviter.id

        if first_name and not user.first_name:
            user.first_name = first_name

        if last_name and not user.last_name:
            user.last_name = last_name

        user.organisation = org
        user.roles |= Role.RESEARCHER
        token = new_invitation_token()
        with app.app_context():
            invitation_url = flask.url_for(
                "orcid_login",
                invitation_token=token,
                _external=True,
                _scheme="http" if app.debug else "https")
            send_email(
                invitation_template,
                recipient=(user.organisation.name, user.email),
                reply_to=(inviter.name, inviter.email),
                invitation_url=invitation_url,
                org_name=user.organisation.name,
                org=org,
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
            first_name=first_name,
            last_name=last_name,
            affiliations=0,
            organisation=org.name,
            disambiguated_id=org.disambiguated_id,
            disambiguation_source=org.disambiguation_source,
            token=token)

        return ui

    except Exception as ex:
        logger.error(f"Exception occured while sending mail: {ex}")
        raise ex


def is_org_rec(org, rec):
    """Test if the record was authoritized by the organisation."""
    client_id = org.orcid_client_id
    source_client_id = rec.get("source").get("source-client-id")
    return (source_client_id and source_client_id.get("path") == client_id)


def create_or_update_work(user, org_id, records, *args, **kwargs):
    """Create or update work record of a user."""
    records = list(unique_everseen(records, key=lambda t: t.record.id))
    org = Organisation.get(id=org_id)
    api = orcid_client.MemberAPI(org, user)

    profile_record = api.get_record()

    if profile_record:
        activities = profile_record.get("activities-summary")

        works = []

        for r in activities.get("works").get("group"):
            ws = r.get("work-summary")[0]
            if is_org_rec(org, ws):
                works.append(ws)

        taken_put_codes = {
            r.record.invitee.put_code
            for r in records if r.record.invitee.put_code
        }

        def match_put_code(records, record, invitee):
            """Match and assign put-code to a single work record and the existing ORCID records."""
            if invitee.put_code:
                return
            for r in records:
                put_code = r.get("put-code")
                if put_code in taken_put_codes:
                    continue

                if ((r.get("title") is None and r.get("title").get("title") is None
                     and r.get("title").get("title").get("value") is None and r.get("type") is None)
                        or (r.get("title").get("title").get("value") == record.title
                            and r.get("type") == record.type)):
                    invitee.put_code = put_code
                    invitee.save()
                    taken_put_codes.add(put_code)
                    app.logger.debug(
                        f"put-code {put_code} was asigned to the work record "
                        f"(ID: {record.id}, Task ID: {record.task_id})")
                    break

        for task_by_user in records:
            wr = task_by_user.record
            wi = task_by_user.record.invitee
            match_put_code(works, wr, wi)

        for task_by_user in records:
            wi = task_by_user.record.invitee

            try:
                put_code, orcid, created = api.create_or_update_work(task_by_user)
                if created:
                    wi.add_status_line(f"Work record was created.")
                else:
                    wi.add_status_line(f"Work record was updated.")
                wi.orcid = orcid
                wi.put_code = put_code

            except Exception as ex:
                logger.exception(f"For {user} encountered exception")
                exception_msg = json.loads(ex.body) if hasattr(ex, "body") else str(ex)
                wi.add_status_line(f"Exception occured processing the record: {exception_msg}.")
                wr.add_status_line(
                    f"Error processing record. Fix and reset to enable this record to be processed: {exception_msg}."
                )

            finally:
                wi.processed_at = datetime.utcnow()
                wr.save()
                wi.save()
    else:
        # TODO: Invitation resend in case user revokes organisation permissions
        app.logger.debug(f"Should resend an invite to the researcher asking for permissions")
        return


def create_or_update_peer_review(user, org_id, records, *args, **kwargs):
    """Create or update peer review record of a user."""
    records = list(unique_everseen(records, key=lambda t: t.record.id))
    org = Organisation.get(id=org_id)
    api = orcid_client.MemberAPI(org, user)

    profile_record = api.get_record()

    if profile_record:
        activities = profile_record.get("activities-summary")

        peer_reviews = []

        for r in activities.get("peer-reviews").get("group"):
            peer_review_summary = r.get("peer-review-summary")
            for ps in peer_review_summary:
                if is_org_rec(org, ps):
                    peer_reviews.append(ps)

        taken_put_codes = {
            r.record.invitee.put_code
            for r in records if r.record.invitee.put_code
        }

        def match_put_code(records, record, invitee, taken_external_id_values):
            """Match and assign put-code to a single peer review record and the existing ORCID records."""
            if invitee.put_code:
                return
            for r in records:
                put_code = r.get("put-code")

                external_id_value = r.get("external-ids").get("external-id")[0].get("external-id-value") if r.get(
                    "external-ids") and r.get("external-ids").get("external-id") and r.get("external-ids").get(
                    "external-id")[0].get("external-id-value") else None

                if put_code in taken_put_codes:
                    continue

                if (r.get("review-group-id")
                        and r.get("review-group-id") == record.review_group_id
                        and external_id_value in taken_external_id_values):  # noqa: E127
                    invitee.put_code = put_code
                    invitee.save()
                    taken_put_codes.add(put_code)
                    app.logger.debug(
                        f"put-code {put_code} was asigned to the peer review record "
                        f"(ID: {record.id}, Task ID: {record.task_id})")
                    break

        for task_by_user in records:
            pr = task_by_user.record
            pi = pr.invitee

            external_ids = PeerReviewExternalId.select().where(PeerReviewExternalId.record_id == pr.id)
            taken_external_id_values = {ei.value for ei in external_ids if ei.value}
            match_put_code(peer_reviews, pr, pi, taken_external_id_values)

        for task_by_user in records:
            pr = task_by_user.record
            pi = pr.invitee

            try:
                put_code, orcid, created = api.create_or_update_peer_review(task_by_user)
                if created:
                    pi.add_status_line(f"Peer review record was created.")
                else:
                    pi.add_status_line(f"Peer review record was updated.")
                pi.orcid = orcid
                pi.put_code = put_code

            except Exception as ex:
                logger.exception(f"For {user} encountered exception")
                exception_msg = json.loads(ex.body) if hasattr(ex, "body") else str(ex)
                pi.add_status_line(f"Exception occured processing the record: {exception_msg}.")
                pr.add_status_line(
                    f"Error processing record. Fix and reset to enable this record to be processed: {exception_msg}."
                )

            finally:
                pi.processed_at = datetime.utcnow()
                pr.save()
                pi.save()
    else:
        # TODO: Invitation resend in case user revokes organisation permissions
        app.logger.debug(f"Should resend an invite to the researcher asking for permissions")
        return


def create_or_update_funding(user, org_id, records, *args, **kwargs):
    """Create or update funding record of a user."""
    records = list(unique_everseen(records, key=lambda t: t.record.id))
    org = Organisation.get(org_id)
    api = orcid_client.MemberAPI(org, user)

    profile_record = api.get_record()

    if profile_record:
        activities = profile_record.get("activities-summary")

        fundings = []

        for r in activities.get("fundings").get("group"):
            fs = r.get("funding-summary")[0]
            if is_org_rec(org, fs):
                fundings.append(fs)

        taken_put_codes = {
            r.record.invitee.put_code
            for r in records if r.record.invitee.put_code
        }

        def match_put_code(records, record, invitee):
            """Match and asign put-code to a single funding record and the existing ORCID records."""
            if invitee.put_code:
                return
            for r in records:
                put_code = r.get("put-code")
                if put_code in taken_put_codes:
                    continue

                if ((r.get("title") is None and r.get("title").get("title") is None
                     and r.get("title").get("title").get("value") is None and r.get("type") is None
                     and r.get("organization") is None
                     and r.get("organization").get("name") is None)
                        or (r.get("title").get("title").get("value") == record.title
                            and r.get("type") == record.type
                            and r.get("organization").get("name") == record.org_name)):
                    invitee.put_code = put_code
                    invitee.save()
                    taken_put_codes.add(put_code)
                    app.logger.debug(
                        f"put-code {put_code} was asigned to the funding record "
                        f"(ID: {record.id}, Task ID: {record.task_id})")
                    break

        for task_by_user in records:
            fr = task_by_user.record
            fi = task_by_user.record.invitee
            match_put_code(fundings, fr, fi)

        for task_by_user in records:
            fi = task_by_user.record.invitee

            try:
                put_code, orcid, created = api.create_or_update_funding(task_by_user)
                if created:
                    fi.add_status_line(f"Funding record was created.")
                else:
                    fi.add_status_line(f"Funding record was updated.")
                fi.orcid = orcid
                fi.put_code = put_code

            except Exception as ex:
                logger.exception(f"For {user} encountered exception")
                if ex and hasattr(ex, "body"):
                    exception_msg = json.loads(ex.body)
                else:
                    exception_msg = str(ex)
                fi.add_status_line(f"Exception occured processing the record: {exception_msg}.")
                fr.add_status_line(
                    f"Error processing record. Fix and reset to enable this record to be processed: {exception_msg}."
                )

            finally:
                fi.processed_at = datetime.utcnow()
                fr.save()
                fi.save()
    else:
        # TODO: Invitation resend in case user revokes organisation permissions
        app.logger.debug(f"Should resend an invite to the researcher asking for permissions")
        return


@rq.job(timeout=300)
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
                         cc_email=None,
                         token_expiry_in_sec=1300000,
                         **kwargs):
    """Send an invitation to join ORCID Hub logging in via ORCID."""
    try:
        if isinstance(inviter, int):
            inviter = User.get(id=inviter)
        if isinstance(org, int):
            org = Organisation.get(id=org)
        if isinstance(start_date, list):
            start_date = PartialDate(*start_date)
        if isinstance(end_date, list):
            end_date = PartialDate(*end_date)
        set_server_name()
        logger.info(f"*** Sending an invitation to '{first_name} {last_name} <{email}>' "
                    f"submitted by {inviter} of {org} for affiliations: {affiliation_types}")

        email = email.lower()
        user, user_created = User.get_or_create(email=email)
        if user_created:
            user.first_name = first_name
            user.last_name = last_name
        user.organisation = org
        user.roles |= Role.RESEARCHER
        token = new_invitation_token()
        with app.app_context():
            invitation_url = flask.url_for(
                "orcid_login",
                invitation_token=token,
                _external=True,
                _scheme="http" if app.debug else "https")
            send_email(
                "email/researcher_invitation.html",
                recipient=(user.organisation.name, user.email),
                reply_to=(inviter.name, inviter.email),
                cc_email=cc_email,
                invitation_url=invitation_url,
                org_name=user.organisation.name,
                org=org,
                user=user)

        user.save()

        user_org, user_org_created = UserOrg.get_or_create(user=user, org=org)
        if user_org_created:
            user_org.created_by = inviter.id
        else:
            user_org.updated_by = inviter.id

        if affiliations is None and affiliation_types:
            affiliations = 0
            if affiliation_types & EMP_CODES:
                affiliations = Affiliation.EMP
            if affiliation_types & EDU_CODES:
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
            organisation=organisation,
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

        status = "The invitation sent at " + datetime.utcnow().isoformat(timespec="seconds")
        (AffiliationRecord.update(status=AffiliationRecord.status + "\n" + status).where(
            AffiliationRecord.status.is_null(False), AffiliationRecord.email == email).execute())
        (AffiliationRecord.update(status=status).where(AffiliationRecord.status.is_null(),
                                                       AffiliationRecord.email == email).execute())
        return ui.id

    except Exception as ex:
        logger.exception(f"Exception occured while sending mail {ex}")
        raise


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


def create_or_update_researcher_url(user, org_id, records, *args, **kwargs):
    """Create or update researcher url record of a user."""
    records = list(unique_everseen(records, key=lambda t: t.researcher_url_record.id))
    org = Organisation.get(id=org_id)
    profile_record = None
    token = OrcidToken.select(OrcidToken.access_token).where(OrcidToken.user_id == user.id, OrcidToken.org_id == org.id,
                                                             OrcidToken.scope.contains("/person/update")).first()
    if token:
        api = orcid_client.MemberAPI(org, user, access_token=token.access_token)
        profile_record = api.get_record()
    if profile_record:
        activities = profile_record.get("person")

        researcher_urls = [
            r for r in (activities.get("researcher-urls").get("researcher-url")) if is_org_rec(org, r)
        ]

        taken_put_codes = {
            r.researcher_url_record.put_code
            for r in records if r.researcher_url_record.put_code
        }

        def match_put_code(records, record):
            """Match and assign put-code to the existing ORCID records."""
            for r in records:
                try:
                    orcid, put_code = r.get('path').split("/")[-3::2]
                except Exception:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")

                if (r.get("url-name") == record.name
                    and get_val(r, "url", "value") == record.value
                    and get_val(r, "visibility") == record.visibility
                    and get_val(r, "display-index") == record.display_index):         # noqa: E129
                    record.put_code = put_code
                    record.orcid = orcid
                    return True

                if record.put_code:
                    return

                if put_code in taken_put_codes:
                    continue

                if ((r.get("url-name") is None and get_val(r, "url", "value") is None)
                    or (r.get("url-name") == record.name
                        and get_val(r, "url", "value") == record.value)):
                    record.put_code = put_code
                    record.orcid = orcid
                    taken_put_codes.add(put_code)
                    app.logger.debug(
                        f"put-code {put_code} was asigned to the researcher url record "
                        f"(ID: {record.id}, Task ID: {record.task_id})")
                    break

        for task_by_user in records:
            try:
                rr = task_by_user.researcher_url_record
                no_orcid_call = match_put_code(researcher_urls, rr)

                if no_orcid_call:
                    rr.add_status_line("Researcher url record unchanged.")
                else:
                    put_code, orcid, created = api.create_or_update_researcher_url(**rr._data)
                    if created:
                        rr.add_status_line("Researcher Url record was created.")
                    else:
                        rr.add_status_line("Researcher Url record was updated.")
                    rr.orcid = orcid
                    rr.put_code = put_code
            except ApiException as ex:
                if ex.status == 404:
                    rr.put_code = None
                elif ex.status == 401:
                    token.delete_instance()
                logger.exception(f'Exception occured {ex}')
                rr.add_status_line(f"ApiException: {ex}")
            except Exception as ex:
                logger.exception(f"For {user} encountered exception")
                rr.add_status_line(f"Exception occured processing the record: {ex}.")

            finally:
                rr.processed_at = datetime.utcnow()
                rr.save()
    else:
        # TODO: Invitation resend in case user revokes organisation permissions
        app.logger.debug(f"Should resend an invite to the researcher asking for permissions")
        return


def create_or_update_other_name(user, org_id, records, *args, **kwargs):
    """Create or update Other name record of a user."""
    records = list(unique_everseen(records, key=lambda t: t.other_name_record.id))
    org = Organisation.get(id=org_id)
    profile_record = None
    token = OrcidToken.select(OrcidToken.access_token).where(OrcidToken.user_id == user.id, OrcidToken.org_id == org.id,
                                                             OrcidToken.scope.contains("/person/update")).first()
    if token:
        api = orcid_client.MemberAPI(org, user, access_token=token.access_token)
        profile_record = api.get_record()
    if profile_record:
        activities = profile_record.get("person")

        other_name_records = [
            r for r in (activities.get("other-names").get("other-name")) if is_org_rec(org, r)
        ]

        taken_put_codes = {
            r.other_name_record.put_code
            for r in records if r.other_name_record.put_code
        }

        def match_put_code(records, other_name_record):
            """Match and assign put-code to the existing ORCID records."""
            for r in records:
                try:
                    orcid, put_code = r.get('path').split("/")[-3::2]
                except Exception:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")

                if (r.get("content") == other_name_record.content
                    and get_val(r, "visibility") == other_name_record.visibility
                    and get_val(r, "display-index") == other_name_record.display_index):         # noqa: E129
                    other_name_record.put_code = put_code
                    other_name_record.orcid = orcid
                    return True

                if other_name_record.put_code:
                    return

                if put_code in taken_put_codes:
                    continue

                if (r.get("content") is None or r.get("content") == other_name_record.content):
                    other_name_record.put_code = put_code
                    other_name_record.orcid = orcid
                    taken_put_codes.add(put_code)
                    app.logger.debug(
                        f"put-code {put_code} was asigned to the other name record "
                        f"(ID: {other_name_record.id}, Task ID: {other_name_record.task_id})")
                    break

        for task_by_user in records:
            try:
                rr = task_by_user.other_name_record
                no_orcid_call = match_put_code(other_name_records, rr)

                if no_orcid_call:
                    rr.add_status_line("Other Name url record unchanged.")
                else:
                    put_code, orcid, created = api.create_or_update_other_name(**rr._data)
                    if created:
                        rr.add_status_line("Other Name record was created.")
                    else:
                        rr.add_status_line("Other Name record was updated.")
                    rr.orcid = orcid
                    rr.put_code = put_code
            except ApiException as ex:
                if ex.status == 404:
                    rr.put_code = None
                elif ex.status == 401:
                    token.delete_instance()
                logger.exception(f'Exception occured {ex}')
                rr.add_status_line(f"ApiException: {ex}")
            except Exception as ex:
                logger.exception(f"For {user} encountered exception")
                rr.add_status_line(f"Exception occured processing the record: {ex}.")

            finally:
                rr.processed_at = datetime.utcnow()
                rr.save()
    else:
        # TODO: Invitation resend in case user revokes organisation permissions
        app.logger.debug(f"Should resend an invite to the researcher asking for permissions")
        return


def create_or_update_keyword(user, org_id, records, *args, **kwargs):
    """Create or update Keyword record of a user."""
    records = list(unique_everseen(records, key=lambda t: t.keyword_record.id))
    org = Organisation.get(id=org_id)
    profile_record = None
    token = OrcidToken.select(OrcidToken.access_token).where(OrcidToken.user_id == user.id, OrcidToken.org_id == org.id,
                                                             OrcidToken.scope.contains("/person/update")).first()
    if token:
        api = orcid_client.MemberAPI(org, user, access_token=token.access_token)
        profile_record = api.get_record()
    if profile_record:
        activities = profile_record.get("person")

        keyword_records = [
            r for r in (activities.get("keywords").get("keyword")) if is_org_rec(org, r)
        ]

        taken_put_codes = {
            r.keyword_record.put_code
            for r in records if r.keyword_record.put_code
        }

        def match_put_code(records, keyword_record):
            """Match and assign put-code to the existing ORCID records."""
            for r in records:
                try:
                    orcid, put_code = r.get('path').split("/")[-3::2]
                except Exception:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")

                if (r.get("content") == keyword_record.content
                    and get_val(r, "visibility") == keyword_record.visibility
                    and get_val(r, "display-index") == keyword_record.display_index):         # noqa: E129
                    keyword_record.put_code = put_code
                    keyword_record.orcid = orcid
                    return True

                if keyword_record.put_code:
                    return

                if put_code in taken_put_codes:
                    continue

                if (r.get("content") is None or r.get("content") == keyword_record.content):
                    keyword_record.put_code = put_code
                    keyword_record.orcid = orcid
                    taken_put_codes.add(put_code)
                    app.logger.debug(
                        f"put-code {put_code} was asigned to the keyword record "
                        f"(ID: {keyword_record.id}, Task ID: {keyword_record.task_id})")
                    break

        for task_by_user in records:
            try:
                rr = task_by_user.keyword_record
                no_orcid_call = match_put_code(keyword_records, rr)

                if no_orcid_call:
                    rr.add_status_line("Keyword record unchanged.")
                else:
                    put_code, orcid, created = api.create_or_update_keyword(**rr._data)
                    if created:
                        rr.add_status_line("Keyword record was created.")
                    else:
                        rr.add_status_line("Keyword record was updated.")
                    rr.orcid = orcid
                    rr.put_code = put_code
            except ApiException as ex:
                if ex.status == 404:
                    rr.put_code = None
                elif ex.status == 401:
                    token.delete_instance()
                logger.exception(f'Exception occured {ex}')
                rr.add_status_line(f"ApiException: {ex}")
            except Exception as ex:
                logger.exception(f"For {user} encountered exception")
                rr.add_status_line(f"Exception occured processing the record: {ex}.")

            finally:
                rr.processed_at = datetime.utcnow()
                rr.save()
    else:
        # TODO: Invitation resend in case user revokes organisation permissions
        app.logger.debug(f"Should resend an invite to the researcher asking for permissions")
        return


def create_or_update_affiliations(user, org_id, records, *args, **kwargs):
    """Create or update affiliation record of a user.

    1. Retries user edurcation and employment summamy from ORCID;
    2. Match the recodrs with the summary;
    3. If there is match update the record;
    4. If no match create a new one.
    """
    records = list(unique_everseen(records, key=lambda t: t.record.id))
    org = Organisation.get(id=org_id)
    api = orcid_client.MemberAPI(org, user)
    profile_record = api.get_record()
    if profile_record:
        activities = profile_record.get("activities-summary")

        employments = [
            r for r in (activities.get("employments").get("employment-summary")) if is_org_rec(org, r)
        ]
        educations = [
            r for r in (activities.get("educations").get("education-summary")) if is_org_rec(org, r)
        ]

        taken_put_codes = {
            r.record.put_code
            for r in records if r.record.put_code
        }

        edu_put_codes = [e["put-code"] for e in educations]
        emp_put_codes = [e["put-code"] for e in employments]

        def match_put_code(records, record):
            """Match and asign put-code to a single affiliation record and the existing ORCID records."""
            for r in records:
                try:
                    orcid, put_code = r.get('path').split("/")[-3::2]
                except Exception:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
                start_date = record.start_date.as_orcid_dict() if record.start_date else None
                end_date = record.end_date.as_orcid_dict() if record.end_date else None

                if (r.get("start-date") == start_date and r.get(
                    "end-date") == end_date and r.get(
                    "department-name") == record.department
                    and r.get("role-title") == record.role
                    and get_val(r, "organization", "name") == record.organisation
                    and get_val(r, "organization", "address", "city") == record.city
                    and get_val(r, "organization", "address", "region") == record.state
                    and get_val(r, "organization", "address", "country") == record.country
                    and get_val(r, "organization", "disambiguated-organization",
                                "disambiguated-organization-identifier") == record.disambiguated_id
                    and get_val(r, "organization", "disambiguated-organization",
                                "disambiguation-source") == record.disambiguation_source):
                    record.put_code = put_code
                    record.orcid = orcid
                    return True

                if record.put_code:
                    return

                if put_code in taken_put_codes:
                    continue

                if ((r.get("start-date") is None and r.get("end-date") is None and r.get(
                    "department-name") is None and r.get("role-title") is None)
                    or (r.get("start-date") == start_date and r.get("department-name") == record.department
                        and r.get("role-title") == record.role)):
                    record.put_code = put_code
                    record.orcid = orcid
                    taken_put_codes.add(put_code)
                    app.logger.debug(
                        f"put-code {put_code} was asigned to the affiliation record "
                        f"(ID: {record.id}, Task ID: {record.task_id})")
                    break

        for task_by_user in records:
            try:
                ar = task_by_user.record
                at = ar.affiliation_type.lower() if ar.affiliation_type else None
                no_orcid_call = False

                if ar.delete_record and profile_record:
                    if ar.put_code in emp_put_codes:
                        affiliation = Affiliation.EMP
                    elif ar.put_code in edu_put_codes:
                        affiliation = Affiliation.EDU
                    else:
                        affiliation = None
                    for a in employments:
                        if a["put-code"] == ar.put_code:
                            affiliation = Affiliation.EMP
                            break
                    if not affiliation:
                        for a in employments:
                            if a["put-code"] == ar.put_code:
                                affiliation = Affiliation.EDU
                                break

                    try:
                        if affiliation:
                            if affiliation == Affiliation.EDU:
                                api.delete_education(user.orcid, ar.put_code)
                            else:
                                api.delete_employment(user.orcid, ar.put_code)
                            ar.add_status_line(f"Record was sucessfully deleted.")
                            app.logger.info(f"ORCID record of {user} with put-code {ar.put_code} was deleted.")
                        else:
                            ar.add_status_line(
                                f"There is no record with the given put-code {ar.put_code} in the user {user} profile."
                            )
                    except Exception as ex:
                        ar.add_status_line(f"Exception occured processing the record: {ex}.")
                    ar.processed_at = datetime.utcnow()
                    ar.save()
                    continue

                if at in EMP_CODES:
                    no_orcid_call = match_put_code(employments, ar)
                    affiliation = Affiliation.EMP
                elif at in EDU_CODES:
                    no_orcid_call = match_put_code(educations, ar)
                    affiliation = Affiliation.EDU
                else:
                    logger.info(f"For {user} not able to determine affiliaton type with {org}")
                    ar.add_status_line(
                        f"Unsupported affiliation type '{at}' allowed values are: " + ', '.join(
                            at for at in AFFILIATION_TYPES))
                    ar.save()
                    continue

                if no_orcid_call:
                    ar.add_status_line(f"{str(affiliation)} record unchanged.")
                else:
                    put_code, orcid, created = api.create_or_update_affiliation(
                        affiliation=affiliation, **ar._data)
                    if created:
                        ar.add_status_line(f"{str(affiliation)} record was created.")
                    else:
                        ar.add_status_line(f"{str(affiliation)} record was updated.")
                    ar.orcid = orcid
                    ar.put_code = put_code

            except Exception as ex:
                logger.exception(f"For {user} encountered exception")
                ar.add_status_line(f"Exception occured processing the record: {ex}.")

            finally:
                ar.processed_at = datetime.utcnow()
                ar.save()
    else:
        for task_by_user in records:
            user = User.get(
                email=task_by_user.record.email, organisation=task_by_user.org)
            user_org = UserOrg.get(user=user, org=task_by_user.org)
            token = new_invitation_token()
            with app.app_context():
                invitation_url = flask.url_for(
                    "orcid_login",
                    invitation_token=token,
                    _external=True,
                    _scheme="http" if app.debug else "https")
                send_email(
                    "email/researcher_reinvitation.html",
                    recipient=(user.organisation.name, user.email),
                    reply_to=(task_by_user.created_by.name, task_by_user.created_by.email),
                    invitation_url=invitation_url,
                    org_name=user.organisation.name,
                    org=org,
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
                start_date=task_by_user.record.start_date,
                end_date=task_by_user.record.end_date,
                affiliations=user_org.affiliations,
                disambiguated_id=org.disambiguated_id,
                disambiguation_source=org.disambiguation_source,
                token=token)

            status = "Exception occured while accessing user's profile. " \
                     "Hence, The invitation resent at " + datetime.utcnow().isoformat(timespec="seconds")
            (AffiliationRecord.update(status=AffiliationRecord.status + "\n" + status).where(
                AffiliationRecord.status.is_null(False),
                AffiliationRecord.email == user.email).execute())
            (AffiliationRecord.update(status=status).where(
                AffiliationRecord.status.is_null(),
                AffiliationRecord.email == user.email).execute())
            return


@rq.job(timeout=300)
def process_work_records(max_rows=20, record_id=None):
    """Process uploaded work records."""
    set_server_name()
    task_ids = set()
    work_ids = set()
    """This query is to retrieve Tasks associated with work records, which are not processed but are active"""

    tasks = (Task.select(
        Task, WorkRecord, WorkInvitee, User,
        UserInvitation.id.alias("invitation_id"), OrcidToken).where(
            WorkRecord.processed_at.is_null(), WorkInvitee.processed_at.is_null(),
            WorkRecord.is_active,
            (OrcidToken.id.is_null(False)
             | ((WorkInvitee.status.is_null())
                | (WorkInvitee.status.contains("sent").__invert__())))).join(
                    WorkRecord, on=(Task.id == WorkRecord.task_id).alias("record")).join(
                        WorkInvitee, on=(WorkRecord.id == WorkInvitee.record_id).alias("invitee")).join(
                            User,
                            JOIN.LEFT_OUTER,
                            on=((User.email == WorkInvitee.email)
                                | ((User.orcid == WorkInvitee.orcid)
                                   & (User.organisation_id == Task.org_id)))).join(
                                       Organisation,
                                       JOIN.LEFT_OUTER,
                                       on=(Organisation.id == Task.org_id)).join(
                                           UserOrg,
                                           JOIN.LEFT_OUTER,
                                           on=((UserOrg.user_id == User.id)
                                               & (UserOrg.org_id == Organisation.id))).join(
                                                   UserInvitation,
                                                   JOIN.LEFT_OUTER,
                                                   on=((UserInvitation.email == WorkInvitee.email)
                                                       & (UserInvitation.task_id == Task.id))).
             join(
                 OrcidToken,
                 JOIN.LEFT_OUTER,
                 on=((OrcidToken.user_id == User.id)
                     & (OrcidToken.org_id == Organisation.id)
                     & (OrcidToken.scope.contains("/activities/update")))).limit(max_rows))
    if record_id:
        tasks = tasks.where(WorkRecord.id == record_id)

    for (task_id, org_id, record_id, user), tasks_by_user in groupby(tasks, lambda t: (
            t.id,
            t.org_id,
            t.record.id,
            t.record.invitee.user,)):
        # If we have the token associated to the user then update the work record,
        # otherwise send him an invite
        if (user.id is None or user.orcid is None or not OrcidToken.select().where(
            (OrcidToken.user_id == user.id) & (OrcidToken.org_id == org_id)
                & (OrcidToken.scope.contains("/activities/update"))).exists()):  # noqa: E127, E129

            for k, tasks in groupby(
                    tasks_by_user,
                    lambda t: (
                        t.created_by,
                        t.org,
                        t.record.invitee.email,
                        t.record.invitee.first_name,
                        t.record.invitee.last_name, )
            ):  # noqa: E501
                email = k[2]
                token_expiry_in_sec = 2600000
                status = "The invitation sent at " + datetime.utcnow().isoformat(
                    timespec="seconds")
                try:
                    # For researcher invitation the expiry is 30 days, if it is reset then it is 2 weeks.
                    if WorkInvitee.select().where(
                            WorkInvitee.email == email, WorkInvitee.status ** "%reset%").count() != 0:
                        token_expiry_in_sec = 1300000
                    send_work_funding_peer_review_invitation(
                        *k,
                        task_id=task_id,
                        token_expiry_in_sec=token_expiry_in_sec,
                        invitation_template="email/work_invitation.html")

                    (WorkInvitee.update(status=WorkInvitee.status + "\n" + status).where(
                        WorkInvitee.status.is_null(False), WorkInvitee.email == email).execute())
                    (WorkInvitee.update(status=status).where(
                        WorkInvitee.status.is_null(), WorkInvitee.email == email).execute())
                except Exception as ex:
                    (WorkInvitee.update(
                        processed_at=datetime.utcnow(),
                        status=f"Failed to send an invitation: {ex}.").where(
                            WorkInvitee.email == email,
                            WorkInvitee.processed_at.is_null())).execute()
        else:
            create_or_update_work(user, org_id, tasks_by_user)
        task_ids.add(task_id)
        work_ids.add(record_id)

    for record in WorkRecord.select().where(WorkRecord.id << work_ids):
        # The Work record is processed for all invitees
        if not (WorkInvitee.select().where(
                WorkInvitee.record_id == record.id,
                WorkInvitee.processed_at.is_null()).exists()):
            record.processed_at = datetime.utcnow()
            if not record.status or "error" not in record.status:
                record.add_status_line("Work record is processed.")
            record.save()

    for task in Task.select().where(Task.id << task_ids):
        # The task is completed (Once all records are processed):
        if not (WorkRecord.select().where(WorkRecord.task_id == task.id, WorkRecord.processed_at.is_null()).exists()):
            task.completed_at = datetime.utcnow()
            task.save()
            error_count = WorkRecord.select().where(
                WorkRecord.task_id == task.id, WorkRecord.status**"%error%").count()
            row_count = task.record_count

            with app.app_context():
                export_url = flask.url_for(
                    "workrecord.export",
                    export_type="json",
                    _scheme="http" if EXTERNAL_SP else "https",
                    task_id=task.id,
                    _external=True)
                send_email(
                    "email/work_task_completed.html",
                    subject="Work Process Update",
                    recipient=(task.created_by.name, task.created_by.email),
                    error_count=error_count,
                    row_count=row_count,
                    export_url=export_url,
                    task_name="Work",
                    filename=task.filename)


@rq.job(timeout=300)
def process_peer_review_records(max_rows=20, record_id=None):
    """Process uploaded peer_review records."""
    set_server_name()
    task_ids = set()
    peer_review_ids = set()
    """This query is to retrieve Tasks associated with peer review records, which are not processed but are active"""
    tasks = (Task.select(
        Task, PeerReviewRecord, PeerReviewInvitee, User,
        UserInvitation.id.alias("invitation_id"), OrcidToken).where(
            PeerReviewRecord.processed_at.is_null(), PeerReviewInvitee.processed_at.is_null(),
            PeerReviewRecord.is_active,
            (OrcidToken.id.is_null(False)
             | ((PeerReviewInvitee.status.is_null())
                | (PeerReviewInvitee.status.contains("sent").__invert__())))).join(
                    PeerReviewRecord, on=(Task.id == PeerReviewRecord.task_id).alias("record")).join(
                        PeerReviewInvitee,
                        on=(PeerReviewRecord.id == PeerReviewInvitee.record_id).alias("invitee")).join(
                            User,
                            JOIN.LEFT_OUTER,
                            on=((User.email == PeerReviewInvitee.email)
                                | ((User.orcid == PeerReviewInvitee.orcid)
                                   & (User.organisation_id == Task.org_id)))).join(
                                       Organisation,
                                       JOIN.LEFT_OUTER,
                                       on=(Organisation.id == Task.org_id)).join(
                                           UserOrg,
                                           JOIN.LEFT_OUTER,
                                           on=((UserOrg.user_id == User.id)
                                               & (UserOrg.org_id == Organisation.id))).
             join(
                 UserInvitation,
                 JOIN.LEFT_OUTER,
                 on=((UserInvitation.email == PeerReviewInvitee.email)
                     & (UserInvitation.task_id == Task.id))).join(
                         OrcidToken,
                         JOIN.LEFT_OUTER,
                         on=((OrcidToken.user_id == User.id)
                             & (OrcidToken.org_id == Organisation.id)
                             & (OrcidToken.scope.contains("/activities/update")))).limit(max_rows))
    if record_id:
        tasks = tasks.where(PeerReviewRecord.id == record_id)

    for (task_id, org_id, record_id, user), tasks_by_user in groupby(tasks, lambda t: (
            t.id,
            t.org_id,
            t.record.id,
            t.record.invitee.user,)):
        """If we have the token associated to the user then update the peer record, otherwise send him an invite"""
        if (user.id is None or user.orcid is None or not OrcidToken.select().where(
            (OrcidToken.user_id == user.id) & (OrcidToken.org_id == org_id)
                & (OrcidToken.scope.contains("/activities/update"))).exists()):  # noqa: E127, E129

            for k, tasks in groupby(
                    tasks_by_user,
                    lambda t: (
                        t.created_by,
                        t.org,
                        t.record.invitee.email,
                        t.record.invitee.first_name,
                        t.record.invitee.last_name, )
            ):  # noqa: E501
                email = k[2]
                token_expiry_in_sec = 2600000
                status = "The invitation sent at " + datetime.utcnow().isoformat(
                    timespec="seconds")
                try:
                    if PeerReviewInvitee.select().where(PeerReviewInvitee.email == email,
                                                        PeerReviewInvitee.status
                                                        ** "%reset%").count() != 0:
                        token_expiry_in_sec = 1300000
                    send_work_funding_peer_review_invitation(
                        *k,
                        task_id=task_id,
                        token_expiry_in_sec=token_expiry_in_sec,
                        invitation_template="email/peer_review_invitation.html")

                    (PeerReviewInvitee.update(
                        status=PeerReviewInvitee.status + "\n" + status).where(
                            PeerReviewInvitee.status.is_null(False),
                            PeerReviewInvitee.email == email).execute())
                    (PeerReviewInvitee.update(status=status).where(
                        PeerReviewInvitee.status.is_null(),
                        PeerReviewInvitee.email == email).execute())
                except Exception as ex:
                    (PeerReviewInvitee.update(
                        processed_at=datetime.utcnow(),
                        status=f"Failed to send an invitation: {ex}.").where(
                            PeerReviewInvitee.email == email,
                            PeerReviewInvitee.processed_at.is_null())).execute()
        else:
            create_or_update_peer_review(user, org_id, tasks_by_user)
        task_ids.add(task_id)
        peer_review_ids.add(record_id)

    for record in PeerReviewRecord.select().where(PeerReviewRecord.id << peer_review_ids):
        # The Peer Review record is processed for all invitees
        if not (PeerReviewInvitee.select().where(
                PeerReviewInvitee.record_id == record.id,
                PeerReviewInvitee.processed_at.is_null()).exists()):
            record.processed_at = datetime.utcnow()
            if not record.status or "error" not in record.status:
                record.add_status_line("Peer Review record is processed.")
            record.save()

    for task in Task.select().where(Task.id << task_ids):
        # The task is completed (Once all records are processed):
        if not (PeerReviewRecord.select().where(PeerReviewRecord.task_id == task.id,
                                                PeerReviewRecord.processed_at.is_null()).exists()):
            task.completed_at = datetime.utcnow()
            task.save()
            error_count = PeerReviewRecord.select().where(
                PeerReviewRecord.task_id == task.id, PeerReviewRecord.status ** "%error%").count()
            row_count = task.record_count

            with app.app_context():
                export_url = flask.url_for(
                    "peerreviewrecord.export",
                    export_type="json",
                    _scheme="http" if EXTERNAL_SP else "https",
                    task_id=task.id,
                    _external=True)
                send_email(
                    "email/work_task_completed.html",
                    subject="Peer Review Process Update",
                    recipient=(task.created_by.name, task.created_by.email),
                    error_count=error_count,
                    row_count=row_count,
                    export_url=export_url,
                    task_name="Peer Review",
                    filename=task.filename)


@rq.job(timeout=300)
def process_funding_records(max_rows=20, record_id=None):
    """Process uploaded affiliation records."""
    set_server_name()
    task_ids = set()
    funding_ids = set()
    """This query is to retrieve Tasks associated with funding records, which are not processed but are active"""
    tasks = (Task.select(
        Task, FundingRecord, FundingInvitee, User,
        UserInvitation.id.alias("invitation_id"), OrcidToken).where(
            FundingRecord.processed_at.is_null(), FundingInvitee.processed_at.is_null(),
            FundingRecord.is_active,
            (OrcidToken.id.is_null(False)
             | ((FundingInvitee.status.is_null())
                | (FundingInvitee.status.contains("sent").__invert__())))).join(
                    FundingRecord, on=(Task.id == FundingRecord.task_id).alias("record")).join(
                        FundingInvitee,
                        on=(FundingRecord.id == FundingInvitee.record_id).alias("invitee")).join(
                            User,
                            JOIN.LEFT_OUTER,
                            on=((User.email == FundingInvitee.email)
                                | ((User.orcid == FundingInvitee.orcid)
                                   & (User.organisation_id == Task.org_id)))).join(
                                       Organisation,
                                       JOIN.LEFT_OUTER,
                                       on=(Organisation.id == Task.org_id)).join(
                                           UserOrg,
                                           JOIN.LEFT_OUTER,
                                           on=((UserOrg.user_id == User.id)
                                               & (UserOrg.org_id == Organisation.id))).
             join(
                 UserInvitation,
                 JOIN.LEFT_OUTER,
                 on=((UserInvitation.email == FundingInvitee.email)
                     & (UserInvitation.task_id == Task.id))).join(
                         OrcidToken,
                         JOIN.LEFT_OUTER,
                         on=((OrcidToken.user_id == User.id)
                             & (OrcidToken.org_id == Organisation.id)
                             & (OrcidToken.scope.contains("/activities/update")))).limit(max_rows))
    if record_id:
        tasks = tasks.where(FundingRecord.id == record_id)

    for (task_id, org_id, record_id, user), tasks_by_user in groupby(tasks, lambda t: (
            t.id,
            t.org_id,
            t.record.id,
            t.record.invitee.user,)):
        """If we have the token associated to the user then update the funding record, otherwise send him an invite"""
        if (user.id is None or user.orcid is None or not OrcidToken.select().where(
            (OrcidToken.user_id == user.id) & (OrcidToken.org_id == org_id)
                & (OrcidToken.scope.contains("/activities/update"))).exists()):  # noqa: E127, E129

            for k, tasks in groupby(
                    tasks_by_user,
                    lambda t: (
                        t.created_by,
                        t.org,
                        t.record.invitee.email,
                        t.record.invitee.first_name,
                        t.record.invitee.last_name, )
            ):  # noqa: E501
                email = k[2]
                token_expiry_in_sec = 2600000
                status = "The invitation sent at " + datetime.utcnow().isoformat(
                    timespec="seconds")
                try:
                    if FundingInvitee.select().where(
                            FundingInvitee.email == email,
                            FundingInvitee.status ** "%reset%").count() != 0:
                        token_expiry_in_sec = 1300000
                    send_work_funding_peer_review_invitation(
                        *k,
                        task_id=task_id,
                        token_expiry_in_sec=token_expiry_in_sec,
                        invitation_template="email/funding_invitation.html")

                    (FundingInvitee.update(status=FundingInvitee.status + "\n" + status).where(
                        FundingInvitee.status.is_null(False),
                        FundingInvitee.email == email).execute())
                    (FundingInvitee.update(status=status).where(
                        FundingInvitee.status.is_null(),
                        FundingInvitee.email == email).execute())
                except Exception as ex:
                    (FundingInvitee.update(
                        processed_at=datetime.utcnow(),
                        status=f"Failed to send an invitation: {ex}.").where(
                            FundingInvitee.email == email,
                            FundingInvitee.processed_at.is_null())).execute()
        else:
            create_or_update_funding(user, org_id, tasks_by_user)
        task_ids.add(task_id)
        funding_ids.add(record_id)

    for record in FundingRecord.select().where(FundingRecord.id << funding_ids):
        # The funding record is processed for all invitees
        if not (FundingInvitee.select().where(
                FundingInvitee.record_id == record.id,
                FundingInvitee.processed_at.is_null()).exists()):
            record.processed_at = datetime.utcnow()
            if not record.status or "error" not in record.status:
                record.add_status_line("Funding record is processed.")
            record.save()

    for task in Task.select().where(Task.id << task_ids):
        # The task is completed (Once all records are processed):
        if not (FundingRecord.select().where(FundingRecord.task_id == task.id,
                                             FundingRecord.processed_at.is_null()).exists()):
            task.completed_at = datetime.utcnow()
            task.save()
            error_count = FundingRecord.select().where(
                FundingRecord.task_id == task.id, FundingRecord.status**"%error%").count()
            row_count = task.record_count

            with app.app_context():
                export_url = flask.url_for(
                    "fundingrecord.export",
                    export_type="json",
                    _scheme="http" if EXTERNAL_SP else "https",
                    task_id=task.id,
                    _external=True)
                send_email(
                    "email/funding_task_completed.html",
                    subject="Funding Process Update",
                    recipient=(task.created_by.name, task.created_by.email),
                    error_count=error_count,
                    row_count=row_count,
                    export_url=export_url,
                    filename=task.filename)


@rq.job(timeout=300)
def process_affiliation_records(max_rows=20, record_id=None):
    """Process uploaded affiliation records."""
    set_server_name()
    # TODO: optimize removing redundant fields
    # TODO: perhaps it should be broken into 2 queries
    task_ids = set()
    tasks = (Task.select(
        Task, AffiliationRecord, User, UserInvitation.id.alias("invitation_id"), OrcidToken).where(
            AffiliationRecord.processed_at.is_null(), AffiliationRecord.is_active,
            ((User.id.is_null(False) & User.orcid.is_null(False) & OrcidToken.id.is_null(False))
             | ((User.id.is_null() | User.orcid.is_null() | OrcidToken.id.is_null())
                & UserInvitation.id.is_null()
                & (AffiliationRecord.status.is_null()
                   | AffiliationRecord.status.contains("sent").__invert__())))).join(
                       AffiliationRecord, on=(Task.id == AffiliationRecord.task_id).alias("record")).join(
                           User,
                           JOIN.LEFT_OUTER,
                           on=((User.email == AffiliationRecord.email)
                               | ((User.orcid == AffiliationRecord.orcid)
                                  & (User.organisation_id == Task.org_id)))).join(
                                   Organisation,
                                   JOIN.LEFT_OUTER,
                                   on=(Organisation.id == Task.org_id)).join(
                                       UserOrg,
                                       JOIN.LEFT_OUTER,
                                       on=((UserOrg.user_id == User.id)
                                           & (UserOrg.org_id == Organisation.id))).
             join(
                 UserInvitation,
                 JOIN.LEFT_OUTER,
                 on=((UserInvitation.email == AffiliationRecord.email)
                     & (UserInvitation.task_id == Task.id))).join(
                         OrcidToken,
                         JOIN.LEFT_OUTER,
                         on=((OrcidToken.user_id == User.id)
                             & (OrcidToken.org_id == Organisation.id)
                             & (OrcidToken.scope.contains("/activities/update")))).limit(max_rows))
    if record_id:
        if isinstance(record_id, list):
            tasks = tasks.where(AffiliationRecord.id.in_(record_id))
        else:
            tasks = tasks.where(AffiliationRecord.id == record_id)
    for (task_id, org_id, user), tasks_by_user in groupby(tasks, lambda t: (
            t.id,
            t.org_id,
            t.record.user, )):
        if (user.id is None or user.orcid is None or not OrcidToken.select().where(
            (OrcidToken.user_id == user.id) & (OrcidToken.org_id == org_id)
                & (OrcidToken.scope.contains("/activities/update"))).exists()):  # noqa: E127, E129
            # maps invitation attributes to affiliation type set:
            # - the user who uploaded the task;
            # - the user organisation;
            # - the invitee email;
            # - the invitee first_name;
            # - the invitee last_name
            invitation_dict = {
                k: set(t.record.affiliation_type.lower() for t in tasks)
                for k, tasks in groupby(
                    tasks_by_user,
                    lambda t: (t.created_by, t.org, t.record.email, t.record.first_name, t.record.last_name)  # noqa: E501
                )  # noqa: E501
            }
            for invitation, affiliations in invitation_dict.items():
                email = invitation[2]
                token_expiry_in_sec = 2600000
                try:
                    # For researcher invitation the expiry is 30 days, if it is reset then it 2 weeks.
                    if AffiliationRecord.select().where(
                            AffiliationRecord.task_id == task_id, AffiliationRecord.email == email,
                            AffiliationRecord.status ** "%reset%").count() != 0:
                        token_expiry_in_sec = 1300000
                    send_user_invitation(
                        *invitation,
                        affiliations,
                        task_id=task_id,
                        token_expiry_in_sec=token_expiry_in_sec)
                except Exception as ex:
                    (AffiliationRecord.update(
                        processed_at=datetime.utcnow(),
                        status=f"Failed to send an invitation: {ex}.").where(
                            AffiliationRecord.task_id == task_id, AffiliationRecord.email == email,
                            AffiliationRecord.processed_at.is_null())).execute()
        else:  # user exits and we have tokens
            create_or_update_affiliations(user, org_id, tasks_by_user)
        task_ids.add(task_id)
    for task in Task.select().where(Task.id << task_ids):
        # The task is completed (all recores are processed):
        if not (AffiliationRecord.select().where(
                AffiliationRecord.task_id == task.id,
                AffiliationRecord.processed_at.is_null()).exists()):
            task.completed_at = datetime.utcnow()
            task.save()
            error_count = AffiliationRecord.select().where(
                AffiliationRecord.task_id == task.id, AffiliationRecord.status**"%error%").count()
            row_count = task.record_count
            orcid_rec_count = task.affiliation_records.select(
                AffiliationRecord.orcid).distinct().count()

            with app.app_context():
                export_url = flask.url_for(
                    "affiliationrecord.export",
                    export_type="csv",
                    _scheme="http" if EXTERNAL_SP else "https",
                    task_id=task.id,
                    _external=True)
                try:
                    send_email(
                        "email/task_completed.html",
                        subject="Affiliation Process Update",
                        recipient=(task.created_by.name, task.created_by.email),
                        error_count=error_count,
                        row_count=row_count,
                        orcid_rec_count=orcid_rec_count,
                        export_url=export_url,
                        filename=task.filename)
                except Exception:
                    logger.exception(
                        "Failed to send batch process comletion notification message.")


@rq.job(timeout=300)
def process_researcher_url_records(max_rows=20, record_id=None):
    """Process uploaded researcher_url records."""
    set_server_name()
    # TODO: optimize removing redundant fields
    # TODO: perhaps it should be broken into 2 queries
    task_ids = set()
    tasks = (Task.select(
        Task, ResearcherUrlRecord, User, UserInvitation.id.alias("invitation_id"), OrcidToken).where(
            ResearcherUrlRecord.processed_at.is_null(), ResearcherUrlRecord.is_active,
            ((User.id.is_null(False) & User.orcid.is_null(False) & OrcidToken.id.is_null(False))
             | ((User.id.is_null() | User.orcid.is_null() | OrcidToken.id.is_null())
                & UserInvitation.id.is_null()
                & (ResearcherUrlRecord.status.is_null()
                   | ResearcherUrlRecord.status.contains("sent").__invert__())))).join(
                       ResearcherUrlRecord, on=(Task.id == ResearcherUrlRecord.task_id)).join(
                           User,
                           JOIN.LEFT_OUTER,
                           on=((User.email == ResearcherUrlRecord.email)
                               | ((User.orcid == ResearcherUrlRecord.orcid)
                                  & (User.organisation_id == Task.org_id)))).join(
                                   Organisation,
                                   JOIN.LEFT_OUTER,
                                   on=(Organisation.id == Task.org_id)).join(
                                       UserOrg,
                                       JOIN.LEFT_OUTER,
                                       on=((UserOrg.user_id == User.id)
                                           & (UserOrg.org_id == Organisation.id))).
             join(
                 UserInvitation,
                 JOIN.LEFT_OUTER,
                 on=((UserInvitation.email == ResearcherUrlRecord.email)
                     & (UserInvitation.task_id == Task.id))).join(
                         OrcidToken,
                         JOIN.LEFT_OUTER,
                         on=((OrcidToken.user_id == User.id)
                             & (OrcidToken.org_id == Organisation.id)
                             & (OrcidToken.scope.contains("/person/update")))).limit(max_rows))
    if record_id:
        tasks = tasks.where(ResearcherUrlRecord.id == record_id)
    for (task_id, org_id, user), tasks_by_user in groupby(tasks, lambda t: (
            t.id,
            t.org_id,
            t.researcher_url_record.user, )):
        if (user.id is None or user.orcid is None or not OrcidToken.select().where(
            (OrcidToken.user_id == user.id) & (OrcidToken.org_id == org_id)
                & (OrcidToken.scope.contains("/person/update"))).exists()):  # noqa: E127, E129
            for k, tasks in groupby(
                    tasks_by_user,
                    lambda t: (t.created_by, t.org, t.researcher_url_record.email, t.researcher_url_record.first_name,
                               t.researcher_url_record.last_name)):  # noqa: E501
                try:
                    email = k[2]
                    send_work_funding_peer_review_invitation(
                        *k,
                        task_id=task_id,
                        invitation_template="email/person_update_invitation.html")
                    status = "The invitation sent at " + datetime.utcnow().isoformat(timespec="seconds")
                    (ResearcherUrlRecord.update(status=ResearcherUrlRecord.status + "\n" + status).where(
                        ResearcherUrlRecord.status.is_null(False), ResearcherUrlRecord.email == email).execute())
                    (ResearcherUrlRecord.update(status=status).where(ResearcherUrlRecord.status.is_null(),
                                                                     ResearcherUrlRecord.email == email).execute())
                except Exception as ex:
                    (ResearcherUrlRecord.update(
                        processed_at=datetime.utcnow(),
                        status=f"Failed to send an invitation: {ex}.").where(
                            ResearcherUrlRecord.task_id == task_id, ResearcherUrlRecord.email == email,
                            ResearcherUrlRecord.processed_at.is_null())).execute()
        else:
            create_or_update_researcher_url(user, org_id, tasks_by_user)
        task_ids.add(task_id)
    for task in Task.select().where(Task.id << task_ids):
        # The task is completed (all recores are processed):
        if not (ResearcherUrlRecord.select().where(
                ResearcherUrlRecord.task_id == task.id,
                ResearcherUrlRecord.processed_at.is_null()).exists()):
            task.completed_at = datetime.utcnow()
            task.save()
            error_count = ResearcherUrlRecord.select().where(
                ResearcherUrlRecord.task_id == task.id, ResearcherUrlRecord.status**"%error%").count()
            row_count = task.record_count

            with app.app_context():
                export_url = flask.url_for(
                    "researcherurlrecord.export",
                    export_type="json",
                    _scheme="http" if EXTERNAL_SP else "https",
                    task_id=task.id,
                    _external=True)
                try:
                    send_email(
                        "email/work_task_completed.html",
                        subject="Researcher Url Record Process Update",
                        recipient=(task.created_by.name, task.created_by.email),
                        error_count=error_count,
                        row_count=row_count,
                        export_url=export_url,
                        task_name="Researcher Url",
                        filename=task.filename)
                except Exception:
                    logger.exception(
                        "Failed to send batch process completion notification message.")


@rq.job(timeout=300)
def process_other_name_records(max_rows=20, record_id=None):
    """Process uploaded Other Name records."""
    set_server_name()
    # TODO: optimize
    task_ids = set()
    tasks = (Task.select(
        Task, OtherNameRecord, User, UserInvitation.id.alias("invitation_id"), OrcidToken).where(
            OtherNameRecord.processed_at.is_null(), OtherNameRecord.is_active,
            ((User.id.is_null(False) & User.orcid.is_null(False) & OrcidToken.id.is_null(False))
             | ((User.id.is_null() | User.orcid.is_null() | OrcidToken.id.is_null())
                & UserInvitation.id.is_null()
                & (OtherNameRecord.status.is_null()
                   | OtherNameRecord.status.contains("sent").__invert__())))).join(
                       OtherNameRecord, on=(Task.id == OtherNameRecord.task_id)).join(
                           User,
                           JOIN.LEFT_OUTER,
                           on=((User.email == OtherNameRecord.email)
                               | ((User.orcid == OtherNameRecord.orcid)
                                  & (User.organisation_id == Task.org_id)))).join(
                                   Organisation,
                                   JOIN.LEFT_OUTER,
                                   on=(Organisation.id == Task.org_id)).join(
                                       UserOrg,
                                       JOIN.LEFT_OUTER,
                                       on=((UserOrg.user_id == User.id)
                                           & (UserOrg.org_id == Organisation.id))).
             join(
                 UserInvitation,
                 JOIN.LEFT_OUTER,
                 on=((UserInvitation.email == OtherNameRecord.email)
                     & (UserInvitation.task_id == Task.id))).join(
                         OrcidToken,
                         JOIN.LEFT_OUTER,
                         on=((OrcidToken.user_id == User.id)
                             & (OrcidToken.org_id == Organisation.id)
                             & (OrcidToken.scope.contains("/person/update")))).limit(max_rows))
    if record_id:
        tasks = tasks.where(OtherNameRecord.id == record_id)
    for (task_id, org_id, user), tasks_by_user in groupby(tasks, lambda t: (
            t.id,
            t.org_id,
            t.other_name_record.user, )):
        if (user.id is None or user.orcid is None or not OrcidToken.select().where(
            (OrcidToken.user_id == user.id) & (OrcidToken.org_id == org_id)
                & (OrcidToken.scope.contains("/person/update"))).exists()):  # noqa: E127, E129
            for k, tasks in groupby(
                    tasks_by_user,
                    lambda t: (t.created_by, t.org, t.other_name_record.email, t.other_name_record.first_name,
                               t.other_name_record.last_name)):  # noqa: E501
                try:
                    email = k[2]
                    send_work_funding_peer_review_invitation(
                        *k,
                        task_id=task_id,
                        invitation_template="email/person_update_invitation.html")
                    status = "The invitation sent at " + datetime.utcnow().isoformat(timespec="seconds")
                    (OtherNameRecord.update(status=OtherNameRecord.status + "\n" + status).where(
                        OtherNameRecord.status.is_null(False), OtherNameRecord.email == email).execute())
                    (OtherNameRecord.update(status=status).where(OtherNameRecord.status.is_null(),
                                                                 OtherNameRecord.email == email).execute())
                except Exception as ex:
                    (OtherNameRecord.update(
                        processed_at=datetime.utcnow(),
                        status=f"Failed to send an invitation: {ex}.").where(
                            OtherNameRecord.task_id == task_id, OtherNameRecord.email == email,
                            OtherNameRecord.processed_at.is_null())).execute()
        else:
            create_or_update_other_name(user, org_id, tasks_by_user)
        task_ids.add(task_id)
    for task in Task.select().where(Task.id << task_ids):
        # The task is completed (all recores are processed):
        if not (OtherNameRecord.select().where(
                OtherNameRecord.task_id == task.id,
                OtherNameRecord.processed_at.is_null()).exists()):
            task.completed_at = datetime.utcnow()
            task.save()
            error_count = OtherNameRecord.select().where(
                OtherNameRecord.task_id == task.id, OtherNameRecord.status**"%error%").count()
            row_count = task.record_count

            with app.app_context():
                export_url = flask.url_for(
                    "othernamerecord.export",
                    export_type="json",
                    _scheme="http" if EXTERNAL_SP else "https",
                    task_id=task.id,
                    _external=True)
                try:
                    send_email(
                        "email/work_task_completed.html",
                        subject="Other Name Record Process Update",
                        recipient=(task.created_by.name, task.created_by.email),
                        error_count=error_count,
                        row_count=row_count,
                        export_url=export_url,
                        task_name="Other Name",
                        filename=task.filename)
                except Exception:
                    logger.exception(
                        "Failed to send batch process completion notification message.")


@rq.job(timeout=300)
def process_keyword_records(max_rows=20, record_id=None):
    """Process uploaded Keyword records."""
    set_server_name()
    # TODO: optimize
    task_ids = set()
    tasks = (Task.select(
        Task, KeywordRecord, User, UserInvitation.id.alias("invitation_id"), OrcidToken).where(
            KeywordRecord.processed_at.is_null(), KeywordRecord.is_active,
            ((User.id.is_null(False) & User.orcid.is_null(False) & OrcidToken.id.is_null(False))
             | ((User.id.is_null() | User.orcid.is_null() | OrcidToken.id.is_null())
                & UserInvitation.id.is_null()
                & (KeywordRecord.status.is_null()
                   | KeywordRecord.status.contains("sent").__invert__())))).join(
                       KeywordRecord, on=(Task.id == KeywordRecord.task_id)).join(
                           User,
                           JOIN.LEFT_OUTER,
                           on=((User.email == KeywordRecord.email)
                               | ((User.orcid == KeywordRecord.orcid)
                                  & (User.organisation_id == Task.org_id)))).join(
                                   Organisation,
                                   JOIN.LEFT_OUTER,
                                   on=(Organisation.id == Task.org_id)).join(
                                       UserOrg,
                                       JOIN.LEFT_OUTER,
                                       on=((UserOrg.user_id == User.id)
                                           & (UserOrg.org_id == Organisation.id))).
             join(
                 UserInvitation,
                 JOIN.LEFT_OUTER,
                 on=((UserInvitation.email == KeywordRecord.email)
                     & (UserInvitation.task_id == Task.id))).join(
                         OrcidToken,
                         JOIN.LEFT_OUTER,
                         on=((OrcidToken.user_id == User.id)
                             & (OrcidToken.org_id == Organisation.id)
                             & (OrcidToken.scope.contains("/person/update")))).limit(max_rows))
    if record_id:
        tasks = tasks.where(KeywordRecord.id == record_id)
    for (task_id, org_id, user), tasks_by_user in groupby(tasks, lambda t: (
            t.id,
            t.org_id,
            t.keyword_record.user, )):
        if (user.id is None or user.orcid is None or not OrcidToken.select().where(
            (OrcidToken.user_id == user.id) & (OrcidToken.org_id == org_id)
                & (OrcidToken.scope.contains("/person/update"))).exists()):  # noqa: E127, E129
            for k, tasks in groupby(
                    tasks_by_user,
                    lambda t: (t.created_by, t.org, t.keyword_record.email, t.keyword_record.first_name,
                               t.keyword_record.last_name)):  # noqa: E501
                try:
                    email = k[2]
                    send_work_funding_peer_review_invitation(
                        *k,
                        task_id=task_id,
                        invitation_template="email/person_update_invitation.html")
                    status = "The invitation sent at " + datetime.utcnow().isoformat(timespec="seconds")
                    (KeywordRecord.update(status=KeywordRecord.status + "\n" + status).where(
                        KeywordRecord.status.is_null(False), KeywordRecord.email == email).execute())
                    (KeywordRecord.update(status=status).where(KeywordRecord.status.is_null(),
                                                               KeywordRecord.email == email).execute())
                except Exception as ex:
                    (KeywordRecord.update(
                        processed_at=datetime.utcnow(),
                        status=f"Failed to send an invitation: {ex}.").where(
                            KeywordRecord.task_id == task_id, KeywordRecord.email == email,
                            KeywordRecord.processed_at.is_null())).execute()
        else:
            create_or_update_keyword(user, org_id, tasks_by_user)
        task_ids.add(task_id)
    for task in Task.select().where(Task.id << task_ids):
        # The task is completed (all recores are processed):
        if not (KeywordRecord.select().where(
                KeywordRecord.task_id == task.id,
                KeywordRecord.processed_at.is_null()).exists()):
            task.completed_at = datetime.utcnow()
            task.save()
            error_count = KeywordRecord.select().where(
                KeywordRecord.task_id == task.id, KeywordRecord.status**"%error%").count()
            row_count = task.record_count

            with app.app_context():
                export_url = flask.url_for(
                    "keywordrecord.export",
                    export_type="json",
                    _scheme="http" if EXTERNAL_SP else "https",
                    task_id=task.id,
                    _external=True)
                try:
                    send_email(
                        "email/work_task_completed.html",
                        subject="Keyword Record Process Update",
                        recipient=(task.created_by.name, task.created_by.email),
                        error_count=error_count,
                        row_count=row_count,
                        export_url=export_url,
                        task_name="Keyword",
                        filename=task.filename)
                except Exception:
                    logger.exception(
                        "Failed to send batch process completion notification message.")


@rq.job(timeout=300)
def process_tasks(max_rows=20):
    """Handle batch task expiration.

    Send a information messages about upcoming removal of the processed/uploaded tasks
    based on date whichever is greater either created_at + month or updated_at + 2 weeks
    and removal of expired tasks based on the expiry date.

    Args:
        max_rows (int): The maximum number of rows that will get processed in one go.

    Returns:
        int. The number of processed task records.

    """
    Task.delete().where((Task.expires_at < datetime.utcnow())).execute()

    tasks = Task.select().where(Task.expires_at.is_null())
    if max_rows and max_rows > 0:
        tasks = tasks.limit(max_rows)
    for task in tasks:

        max_created_at_expiry = (task.created_at + timedelta(weeks=4))
        max_updated_at_expiry = (task.updated_at + timedelta(weeks=2))

        max_expiry_date = max_created_at_expiry

        if max_created_at_expiry < max_updated_at_expiry:
            max_expiry_date = max_updated_at_expiry

        task.expires_at = max_expiry_date
        task.save()

    tasks = Task.select().where(
            Task.expires_at.is_null(False),
            Task.expiry_email_sent_at.is_null(),
            Task.expires_at < (datetime.now() + timedelta(weeks=1)))
    if max_rows and max_rows > 0:
        tasks = tasks.limit(max_rows)
    for task in tasks:

        if task.records is None:
            continue

        export_model = task.record_model._meta.name + ".export"
        error_count = task.error_count

        set_server_name()
        with app.app_context():
            export_url = flask.url_for(
                export_model,
                export_type="csv",
                _scheme="http" if EXTERNAL_SP else "https",
                task_id=task.id,
                _external=True)
            send_email(
                "email/task_expiration.html",
                task=task,
                subject="Batch process task is about to expire",
                recipient=(task.created_by.name, task.created_by.email),
                error_count=error_count,
                export_url=export_url)
        task.expiry_email_sent_at = datetime.utcnow()
        task.save()


def get_client_credentials_token(org, scope="/webhook"):
    """Request a cient credetials grant type access token and store it.

    The any previously requesed with the give scope tokens will be deleted.
    """
    resp = requests.post(
        app.config["TOKEN_URL"],
        headers={"Accept": "application/json"},
        data=dict(
            client_id=org.orcid_client_id,
            client_secret=org.orcid_secret,
            scope=scope,
            grant_type="client_credentials"))
    OrcidToken.delete().where(OrcidToken.org == org, OrcidToken.scope == "/webhook").execute()
    data = resp.json()
    token = OrcidToken.create(
        org=org,
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        scope=data.get("scope") or scope,
        expires_in=data["expires_in"])
    return token


@rq.job(timeout=300)
def register_orcid_webhook(user, callback_url=None, delete=False):
    """Register or delete an ORCID webhook for the given user profile update events.

    If URL is given, it will be used for as call-back URL.
    """
    set_server_name()
    local_handler = (callback_url is None)

    if local_handler and delete and user.organisations.where(Organisation.webhook_enabled).count() > 0:
        return

    try:
        token = OrcidToken.get(org=user.organisation, scope="/webhook")
    except OrcidToken.DoesNotExist:
        token = get_client_credentials_token(org=user.organisation, scope="/webhook")
    if local_handler:
        with app.app_context():
            callback_url = quote(url_for("update_webhook", user_id=user.id), safe='')
    elif '/' in callback_url or ':' in callback_url:
        callback_url = quote(callback_url, safe='')
    url = f"{app.config['ORCID_API_HOST_URL']}{user.orcid}/webhook/{callback_url}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token.access_token}",
        "Content-Length": "0"
    }
    resp = requests.delete(url, headers=headers) if delete else requests.put(url, headers=headers)
    if local_handler and resp.status_code // 200 == 1:
        if delete:
            user.webhook_enabled = False
        else:
            user.webhook_enabled = True
        user.save()
    return resp


@rq.job(timeout=300)
def invoke_webhook_handler(webhook_url=None, orcid=None, updated_at=None, message=None,
                           attempts=3):
    """Propagate 'updated' event to the organisation event handler URL."""
    url = app.config["ORCID_BASE_URL"] + orcid
    if message is None:
        message = {
            "orcid": orcid,
            "updated-at": updated_at.isoformat(timespec="minutes"),
            "url": url
        }
    resp = requests.post(webhook_url + '/' + orcid, json=message)
    if resp.status_code // 200 != 1:
        if attempts > 0:
            invoke_webhook_handler.schedule(
                timedelta(minutes=5), message=message, attempts=attempts - 1)
    return resp


@rq.job(timeout=300)
def enable_org_webhook(org):
    """Enable Organisation Webhook."""
    org.webhook_enabled = True
    org.save()
    for u in org.users:
        if not u.webhook_enabled:
            register_orcid_webhook.queue(u)


@rq.job(timeout=300)
def disable_org_webhook(org):
    """Disable Organisation Webhook."""
    org.webhook_enabled = False
    org.save()
    for u in org.users.where(User.webhook_enabled):
        register_orcid_webhook.queue(u, delete=True)


def process_records(n):
    """Process first n records and run other batch tasks."""
    process_affiliation_records(n)
    process_funding_records(n)
    process_work_records(n)
    process_peer_review_records(n)
    process_researcher_url_records(n)
    process_other_name_records(n)
    process_keyword_records(n)
    # process_tasks(n)


@rq.job(timeout=300)
def send_orcid_update_summary(org_id=None):
    """Send organisation researcher ORCID profile update summary report."""
    first = date.today().replace(day=1)
    previous_last = first - timedelta(days=1)
    previous_first = previous_last.replace(day=1)

    if org_id is None:
        for o in (Organisation.select(Organisation.id).distinct().join(
            UserOrg, on=UserOrg.org_id == Organisation.id).join(
                User, on=User.id == UserOrg.user_id).where(
                    Organisation.webhook_enabled, Organisation.email_notifications_enabled)
                .where(
                    User.orcid_updated_at >= previous_first,
                    User.orcid_updated_at < first)):
            send_orcid_update_summary.queue(o.id)
        return

    org = Organisation.select().where(Organisation.id == org_id).first()
    if org and org.webhook_enabled and org.email_notifications_enabled:
        updated_users = org.users.where(User.orcid_updated_at >= previous_first,
                                        User.orcid_updated_at < first)
        recipient = org.notification_email or (org.tech_contact.name, org.tech_contact.email)
        if updated_users.exists():
            message_template = """<p>The flollowing user profiles were updated
            from {{date_from}} until {{date_to}}:</p>
            <ul>
            {% for u in updated_users %}
                <li>{{u.name}} ({{u.email}},
                <a href="{{orcid_base_url}}{{u.orcid}}" target="_blank">{{u.orcid}}</a>,
                updated at {{u.orcid_updated_at.isoformat(sep=" ", timespec="seconds")}});
                </li>
            {% endfor %}
            </ul>
            """
            set_server_name()
            with app.app_context():
                send_email(
                    message_template,
                    org=org,
                    recipient=recipient,
                    subject="Updated ORCID Profiles",
                    date_from=previous_first,
                    date_to=previous_last,
                    updated_users=updated_users,
                    orcid_base_url=app.config["ORCID_BASE_URL"])


@rq.job(timeout=300)
def sync_profile(task_id, delay=0.1):
    """Verify and sync the user profile."""
    if not task_id:
        return
    try:
        task = Task.get(task_id)
    except Task.DoesNotExist:
        return
    org = task.org
    if not org.disambiguated_id:
        return
    api = orcid_client.MemberAPI(org=org)
    count = 0
    for u in task.org.users.select(User, OrcidToken.access_token.alias("access_token")).where(
            User.orcid.is_null(False)).join(
            OrcidToken,
            on=((OrcidToken.user_id == User.id) & OrcidToken.scope.contains("/activities/update"))).naive():
        Log.create(task=task_id, message=f"Processing user {u} / {u.orcid} profile.")
        api.sync_profile(user=u, access_token=u.access_token, task=task)
        count += 1
        time.sleep(delay)
    Log.create(task=task_id, message=f"In total, {count} user profiles were synchronized.")


class SafeRepresenterWithISODate(SafeRepresenter):
    """Customized representer for datetaime rendering in ISO format."""

    def represent_datetime(self, data):
        """Customize datetime rendering in ISO format."""
        value = data.isoformat(timespec="seconds")
        return self.represent_scalar('tag:yaml.org,2002:timestamp', value)


def dump_yaml(data):
    """Dump the objects into YAML representation."""
    yaml.add_representer(datetime, SafeRepresenterWithISODate.represent_datetime, Dumper=Dumper)
    yaml.add_representer(defaultdict, SafeRepresenter.represent_dict)
    return yaml.dump(data)
