# -*- coding: utf-8 -*-
"""Various utilities."""

import os
import textwrap
from urllib.parse import urlencode, urlparse

import flask
import jinja2
import jinja2.ext
import requests
from flask_login import current_user
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from peewee import JOIN

from application import app, mail
from models import AffiliationRecord, Organisation, Task, User


def send_email(template,
               recipient,
               cc_email,
               sender=(app.config.get("APP_NAME"), app.config.get("MAIL_DEFAULT_SENDER")),
               reply_to=None,
               subject=None,
               **kwargs):
    """
    Send an email, acquiring its payload by rendering a jinja2 template
    :type template: :class:`str`
    :param subject: the subject of the email
    :param template: name of the template file in ``templates/emails`` to use
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
    if flask.current_app:
        # use the app's env if it's available, so that url_for may be used
        jinja_env = flask.current_app.jinja_env
    else:
        path = os.path.join(os.path.dirname(__file__), "templates")
        loader = jinja2.FileSystemLoader(path)
        jinja_env = jinja2.Environment(
            loader=loader, extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_'])

    jinja_env = jinja_env.overlay(autoescape=False, extensions=[RewrapExtension])

    def _jinja2_email(name, email):
        if name is None:
            hint = 'name was not set for email {0}'.format(email)
            name = jinja_env.undefined(name='name', hint=hint)
        return {"name": name, "email": email}

    template = jinja_env.get_template(template)

    kwargs["sender"] = _jinja2_email(*sender)
    kwargs["recipient"] = _jinja2_email(*recipient)
    if subject is not None:
        kwargs["subject"] = subject
    if reply_to is None:
        reply_to = sender

    rendered = template.make_module(vars=kwargs)

    if subject is None:
        subject = getattr(rendered, "subject", "Welcome to the NZ ORCID Hub")

    with app.app_context():
        msg = Message(subject=subject)
        msg.add_recipient(recipient)
        msg.reply_to = reply_to
        msg.html = str(rendered)
        msg.sender = sender
        if cc_email:
            msg.cc.append(cc_email)
        # TODO: implement async sedning
        mail.send(msg)


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


def generate_confirmation_token(email):
    """Generate Organisation registration confirmation token."""
    serializer = URLSafeTimedSerializer(app.config['TOKEN_SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['TOKEN_PASSWORD_SALT'])


# Token Expiry after 15 days.
def confirm_token(token, expiration=1300000):
    """Genearate confirmaatin token."""
    serializer = URLSafeTimedSerializer(app.config['TOKEN_SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=app.config['TOKEN_PASSWORD_SALT'], max_age=expiration)
    except:
        return False
    return email


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


def process_affiliation_records():
    """Process uploaded affiliation records."""
    tasks = (Task.select(Task, AffiliationRecord, User, Organisation).where(
        AffiliationRecord.processed_at >> None & AffiliationRecord.is_active).join(
            AffiliationRecord, on=(Task.id == AffiliationRecord.task_id)).join(
                User,
                JOIN.LEFT_OUTER,
                on=((User.email == AffiliationRecord.identifier) |
                    (User.eppn == AffiliationRecord.identifier) |
                    (User.orcid == AffiliationRecord.identifier))).join(
                        Organisation,
                        JOIN.LEFT_OUTER,
                        on=(Organisation.name == AffiliationRecord.organisation)))
    for t in tasks:

        if not t.affiliation_record.user or t.affiliation_record.user.orcid is None:
            # TODO: send an invitation
            print("***", t, t.affiliation_record)
            pass
        else:
            # TODO: update or create ORCID profile record
            pass
            print("***", t, ':', t.affiliation_record.user.orcid)
