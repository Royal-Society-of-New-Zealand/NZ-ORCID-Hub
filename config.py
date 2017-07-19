# -*- coding: utf-8 -*-
"""Application configuration."""

from os import environ, urandom

ENV = environ.get("ENV", "dev")

ORCID_API_BASE = "https://api.sandbox.orcid.org/v2.0/" if ENV != "prod" else "https://api.orcid.org/v2.0/"
ORCID_BASE_URL = "https://sandbox.orcid.org/" if ENV != "prod" else "https://orcid.org/"

SECRET_KEY = environ.get("SECRET_KEY", urandom(42).hex())

# NZ ORCIDHUB API client ID and secret
NZ_ORCIDHUB_CLIENT_ID = environ.get("NZ_ORCIDHUB_CLIENT_ID", "APP-42W3G8FS4OHGM562")
NZ_ORCIDHUB_CLIENT_SECRET = environ.get("NZ_ORCIDHUB_CLIENT_SECRET")

# Change the URL as per the enviornment
AUTHORIZATION_BASE_URL = 'https://sandbox.orcid.org/oauth/authorize' \
    if ENV != "prod" else "https://orcid.org/oauth/authorize"
TOKEN_URL = 'https://sandbox.orcid.org/oauth/token' if ENV != "prod" else "https://orcid.org/oauth/token"
SCOPE_ACTIVITIES_UPDATE = ['/activities/update']
SCOPE_READ_LIMITED = ['/read-limited']
SCOPE_AUTHENTICATE = ['/authenticate']

# Database connection url
DATABASE_URL = environ.get("DATABASE_URL")
BACKUP_DATABASE_URL = environ.get("BACKUP_DATABASE_URL")

if not DATABASE_URL:
    POSTGRES_PASSWORD = environ.get("POSTGRES_PASSWORD") or environ.get("PGPASSWORD") or "p455w0rd"
    DB_NAME = environ.get("PGDATABASE", "orcidhub")
    DB_USERNAME = environ.get("PGUSER", "orcidhub")
    DB_PASSWORD = POSTGRES_PASSWORD
    DB_HOSTNAME = environ.get("PGHOST", "db")
    DATABASE_URL = "postgresql://" + DB_NAME
    if POSTGRES_PASSWORD:
        DATABASE_URL += ':' + POSTGRES_PASSWORD
    DATABASE_URL += "@" + DB_HOSTNAME + ":5432/" + DB_NAME

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

# add mail server config
MAIL_PORT = int(environ.get("MAIL_PORT", 25))
MAIL_SUPPRESS_SEND = False
MAIL_DEFAULT_SENDER = environ.get("MAIL_DEFAULT_SENDER", "no-reply@orcidhub.org.nz")
MAIL_SERVER = environ.get("MAIL_SERVER", "gateway")

TOKEN_PASSWORD_SALT = environ.get("TOKEN_PASSWORD_SALT")
TOKEN_SECRET_KEY = environ.get("TOKEN_SECRET_KEY")

MEMBER_API_FORM_BASE_URL = "https://orcid.org/content/register-client-application-sandbox" \
    if ENV != "prod" else "https://orcid.org/content/register-client-application-production-trusted-party"

NEW_CREDENTIALS = 'New_Credentials'
NOTE_ORCID = 'An NZ ORCID Hub integration for'
CRED_TYPE_PREMIUM = 2
APP_NAME = 'NZ ORCID HUB'
APP_DESCRIPTION = 'This is an ORCID integration through the NZ ORCID HUB connecting'
APP_URL = "https://" + (ENV + ".orcidhub.org.nz" if ENV != "prod" else "orcidhub.org.nz")

# External Shibboleth SP login URL (e.g., https://test.orcidhub.org.nz/Tuakiri/login)
if ENV != "prod":
    EXTERNAL_SP = environ.get("EXTERNAL_SP")

DEFAULT_COUNTRY = "NZ"

if ENV == "dev":
    GA_TRACKING_ID = "UA-99022483-1"
elif ENV == "test":
    GA_TRACKING_ID = "UA-99022483-2"
elif ENV == "dev0":
    GA_TRACKING_ID = "UA-99022483-3"
else:
    GA_TRACKING_ID = "UA-99022483-4"

SENTRY_DSN = "https://bb596bd75ad4490c80ee0a7c22943a94:a53ff6a9eb5b439e87d8553f162a6658@sentry.io/172044"
