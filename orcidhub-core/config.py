from os import environ

# Orcid API client ID and secret
client_id = environ.get("ORCID_CLIENT_ID", "APP-TF7LKIE084PYTQ59")
client_secret = environ.get("ORCID_CLIENT_SECRET")

# Change the URL as per the enviornment
authorization_base_url = 'https://sandbox.orcid.org/oauth/authorize'
token_url = 'https://pub.sandbox.orcid.org/oauth/token'
scope = ['/authenticate']

# Application redirect URL:
redirect_uri = "https://" + environ.get("ENV", "dev") + ".orcidhub.org.nz/auth"

# Postgresql connection url
POSTGRES_PASSWORD = environ.get("POSTGRES_PASSWORD")
SQLALCHEMY_DATABASE_URI = "postgresql://orcidhub"
if POSTGRES_PASSWORD:
    SQLALCHEMY_DATABASE_URI += ':' + POSTGRES_PASSWORD
SQLALCHEMY_DATABASE_URI += "@" + environ.get("PGHOST", "db") + ":5432/orcidhub"
SQLALCHEMY_MIGRATE_REPO = 'db_repository'

DB_NAME = environ.get("PGDATABASE", "orcidhub")
DB_USERNAME = environ.get("PGUSER", "orcidhub")
DB_PASSWORD = environ.get("PGPASSWORD", environ.get("POSTGRES_PASSWORD", "p455w0rd"))
DB_HOSTNAME = environ.get("PGHOST", "db")

MAIL_USERNAME = environ.get("MAIL_USERNAME", "AKIAICSRSUE3LNBSIBVQ")
MAIL_PASSWORD = environ.get("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = environ.get("MAIL_DEFAULT_SENDER", "no-reply@orcidhub.org.nz")
MAIL_SERVER = environ.get("MAIL_SERVER", "email-smtp.us-east-1.amazonaws.com")

TOKEN_PASSWORD_SALT = environ.get("TOKEN_PASSWORD_SALT")
TOKEN_SECRET_KEY = environ.get("TOKEN_SECRET_KEY")

MEMBER_API_FORM_BASE_URL = environ.get("MEMBER_API_FORM_BASE_URL",
                                       "https://orcid.org/content/register-client-application-sandbox")
NEW_CREDENTIALS = 'New_Credentials'
NOTE_ORCID = 'ORCID Hub integration for'
CRED_TYPE_PREMIUM = 2
APP_NAME = 'ORCID HUB'
APP_DESCRIPTION = 'We are having an ORCID integration through ORCID HUB New Zealand'
APP_URL = "https://" + environ.get("ENV", "dev") + ".orcidhub.org.nz"
