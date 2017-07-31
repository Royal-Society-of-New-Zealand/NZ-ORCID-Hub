# -*- coding: utf-8 -*-
"""Various utilities."""

import os
import textwrap
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

from application import app
from config import ENV
from models import (Affiliation, AffiliationRecord, OrcidToken, Organisation, Role, Task, User,
                    UserInvitation, UserOrg)


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
    serializer = URLSafeTimedSerializer(app.config['TOKEN_SECRET_KEY'])
    salt = app.config['TOKEN_PASSWORD_SALT']
    if len(kwargs) == 0:
        return serializer.dumps(args[0] if len(args) == 1 else args, salt=salt)
    else:
        return serializer.dumps(kwargs.values()[0] if len(kwargs) == 1 else kwargs, salt=salt)


# Token Expiry after 15 days.
def confirm_token(token, expiration=1300000):
    """Genearate confirmaatin token."""
    serializer = URLSafeTimedSerializer(app.config['TOKEN_SECRET_KEY'])
    try:
        data = serializer.loads(token, salt=app.config['TOKEN_PASSWORD_SALT'], max_age=expiration)
    except:
        return False
    return data


def append_qs(url, **qs):
    """Appends new query strings to an arbitraty URL."""
    return url + ('&' if urlparse(url).query else '?') + urlencode(qs)


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
    print("*****", inviter, org, email, first_name, last_name, affiliation_types)

    try:
        email = email.lower()
        user, _ = User.get_or_create(email=email)
        user.first_name = first_name
        user.last_name = last_name
        user.roles |= Role.RESEARCHER
        user.email = email
        user.organisation = org
        with app.app_context():
            token = generate_confirmation_token(email=email, org_name=org.name)
            send_email(
                "email/researcher_invitation.html",
                recipient=(user.organisation.name, user.email),
                reply_to=(inviter.name, inviter.email),
                token=token,
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

    except Exception as ex:
        raise ex
        print("Exception occured while sending mails %r" % str(ex), "danger")


def create_or_update_affiliation(user, records, *args, **kwargs):
    """Creates or updates affiliation record of a user.

    1. Retries user edurcation and employment surramy from ORCID;
    2. Match the recodrs with the summary;
    3. If there is match update the record;
    4. If no match create a new one."""
    # TODO:
    pass


def process_affiliation_records(max_rows=20):
    """Process uploaded affiliation records."""
    set_server_name()

    tasks = (Task.select(Task, AffiliationRecord, User, Organisation).where(
        AffiliationRecord.processed_at.is_null() & AffiliationRecord.is_active).join(
            AffiliationRecord, on=(Task.id == AffiliationRecord.task_id)).join(
                User,
                JOIN.LEFT_OUTER,
                on=((User.email == AffiliationRecord.identifier) |
                    (User.eppn == AffiliationRecord.identifier) |
                    (User.orcid == AffiliationRecord.identifier))).join(
                        Organisation,
                        JOIN.LEFT_OUTER,
                        on=(Organisation.name == AffiliationRecord.organisation)).limit(max_rows))
    for (org_id,
         user), tasks_by_user in groupby(tasks, lambda t: (t.org_id, t.affiliation_record.user, )):
        if (user.id is None or user.orcid is None or OrcidToken.select().where(
            (OrcidToken.user_id == user.id) & (OrcidToken.org_id == org_id) &
            (OrcidToken.scope.contains("/activities/update"))).exists()):  # noqa: E129
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
                )
            }

            for invitation, affiliations in invitation_dict.items():
                send_user_initation(*invitation, affiliations)
        else:  # user exits and we have tokens
            for task in tasks_by_user:
                print("***", task, ':', user.orcid)
                create_or_update_affiliation(user, task.affiliation_record)
