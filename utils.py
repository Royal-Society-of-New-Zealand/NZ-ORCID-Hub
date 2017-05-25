# -*- coding: utf-8 -*-
"""Various utilities."""

import os
import textwrap

import flask
import jinja2
import jinja2.ext
from flask_mail import Message

from application import app, mail
from config import APP_NAME, MAIL_DEFAULT_SENDER


def send_email(template, recipient, sender=(APP_NAME, MAIL_DEFAULT_SENDER), subject=None,
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

    rendered = template.make_module(vars=kwargs)

    if subject is None:
        subject = getattr(rendered, "subject", "Welcome to the NZ ORCID Hub")

    with app.app_context():
        msg = Message(subject=subject)
        msg.add_recipient(recipient)
        msg.html = str(rendered)
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
