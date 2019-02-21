# -*- coding: utf-8 -*-
"""Application configuration."""

from os import environ, getenv, path

ENV = getenv("ENV", "dev")
SHIBBOLETH_DISABLED = getenv("SHIBBOLETH_DISABLED")

ORCID_API_HOST_URL = "https://api.sandbox.orcid.org/" if ENV != "prod" else "https://api.orcid.org/"
ORCID_API_VERSION = "v2.0"
ORCID_API_BASE = ORCID_API_HOST_URL + ORCID_API_VERSION + '/'
ORCID_BASE_URL = "https://sandbox.orcid.org/" if ENV != "prod" else "https://orcid.org/"

# NB! Set up the key. See: http://flask.pocoo.org/docs/latest/quickstart/#sessions
SECRET_KEY = getenv("SECRET_KEY", b'\xe3\x94a\x14-sT`\x92\x8a0\x16\r\xe1zb')
SENTRY_DSN = getenv("SENTRY_DSN")

# TODO: Soon to be depricated:
SALT = getenv("TOKEN_PASSWORD_SALT")

# NZ ORCIDHUB API client ID and secret
ORCID_CLIENT_ID = getenv("ORCID_CLIENT_ID")
ORCID_CLIENT_SECRET = getenv("ORCID_CLIENT_SECRET")

# Change the URL as per the enviornment
AUTHORIZATION_BASE_URL = 'https://sandbox.orcid.org/oauth/authorize' \
    if ENV != "prod" else "https://orcid.org/oauth/authorize"
TOKEN_URL = 'https://sandbox.orcid.org/oauth/token' if ENV != "prod" else "https://orcid.org/oauth/token"

# Database connection url
DATABASE_URL = getenv("DATABASE_URL", "sqlite:///data.db")
BACKUP_DATABASE_URL = getenv("BACKUP_DATABASE_URL")
LOAD_TEST = getenv("LOAD_TEST")

# NB! Disable in production
if ENV in ("dev0", ):
    DEBUG = '1'
    MAIL_DEBUG = '1'
    TESTING = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_PROFILER_ENABLED = True
    OAUTHLIB_INSECURE_TRANSPORT = '1'
    environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    TEMPLATES_AUTO_RELOAD = True
    # EXPLAIN_TEMPLATE_LOADING = True

OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 86400  # Default Bearer token expires time, default is 3600.

# add mail server config
MAIL_PORT = int(getenv("MAIL_PORT", 25))
MAIL_SUPPRESS_SEND = False
MAIL_DEFAULT_SENDER = getenv("MAIL_DEFAULT_SENDER", "no-reply@orcidhub.org.nz")
MAIL_SERVER = getenv("MAIL_SERVER", "gateway")

MEMBER_API_FORM_BASE_URL = "https://orcid.org/content/register-client-application-sandbox" \
    if ENV != "prod" else "https://orcid.org/content/register-client-application-production-trusted-party"

NOTE_ORCID = 'An NZ ORCID Hub integration for'
CRED_TYPE_PREMIUM = 2
APP_NAME = 'NZ ORCID HUB'
APP_DESCRIPTION = 'This is an ORCID integration through the NZ ORCID HUB connecting'
APP_URL = "https://" + (ENV + ".orcidhub.org.nz" if ENV != "prod" else "orcidhub.org.nz")
SEED_HUB_ADMIN = getenv("SEED_HUB_ADMIN", "rad42@mailinator.com")

# External Shibboleth SP login URL (e.g., https://test.orcidhub.org.nz/Tuakiri/login)
EXTERNAL_SP = getenv("EXTERNAL_SP") if ENV != "prod" else None

DEFAULT_COUNTRY = "NZ"

if ENV == "dev":
    GA_TRACKING_ID = "UA-99022483-1"
elif ENV == "test":
    GA_TRACKING_ID = "UA-99022483-2"
elif ENV == "dev0":
    GA_TRACKING_ID = "UA-99022483-3"
else:
    GA_TRACKING_ID = "UA-99022483-4"

DEFAULT_EMAIL_TEMPLATE = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{SUBJECT}</title>
    <meta name="keywords" content="ORCID HUB,New Zealand,NZ,orcid"/>
  </head>
  <body>
    <div style="font-family: Arial, Verdana, Georgia, and Times New Roman; background-color: white; color: black;">
      <table style="vertical-align: middle; background-color: black; color: white; width: 100%;">
        <tr>
          <td>&nbsp;</td>
          <td align="right">
            <img src="{LOGO}" title="NZ ORCID Hub" alt="NZ ORCID Hub" style="display:block;" />
          </td>
        </tr>
      </table>
      {MESSAGE}
      <p>If you received this email in error, or you have questions about the responsibilities
      involved, please contact: <a href="mailto:orcid@royalsociety.org.nz">
      orcid@royalsociety.org.nz</a></p>
      <p>For information about ORCID go to the
      <a href="https://royalsociety.org.nz/orcid-in-new-zealand/what-is-orcid/orcid-for-researchers/">What is ORCID?</a>
       page of our website.</p>
      <hr>
      <p>This email was sent to <a href="mailto:{EMAIL}">{EMAIL}</a></p>
      <!--  Footer Details -->
      <table style="vertical-align: top; background-color: black; color: white; width: 100%; margin-top: 25px;">
        <tr>
          <td>
            <p style="vertical-align: top; padding-left: 15px;">
            Contact details for the NZ ORCID Hub<br>
            Phone: (04) 472 7421<br>
            PO Box 598, Wellington 6140<br>
            <b><a style="text-decoration: none; color: white;"
                  href="mailto:orcid@royalsociety.org.nz">orcid@royalsociety.org.nz</a></b>
            </p>
          </td>
          <td style="vertical-align: top;">
            <p class="copyright"><a href="https://creativecommons.org/licenses/by/4.0/"
            target="_blank"><img
            src="{BASE_URL}/static/images/CC-BY-icon-80x15.png" alt="CC-BY" /></a></p>
          </td>
        </tr>
      </table>
    </div>
  </body>
</html>
"""

DKIP_KEY_PATH = path.join(path.dirname(path.relpath(path.relpath(__file__))), ".keys", "dkim.key")

# RQ:
RQ_REDIS_URL = getenv("RQ_REDIS_URL")
RQ_QUEUE_CLASS = "orcid_hub.queuing.ThrottledQueue"

# rq-dashboard config:
RQ_POLL_INTERVAL = 5000  #: Web interface poll period for updates in ms
WEB_BACKGROUND = "gray"
