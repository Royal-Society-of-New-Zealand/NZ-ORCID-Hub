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

MAIL_USERNAME = environ.get("MAIL_USERNAME", "AKIAJZ573F4QPLWSXTJA")
MAIL_PASSWORD = environ.get("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = environ.get("MAIL_DEFAULT_SENDER", "no-reply@orcidhub.org.nz")
MAIL_SERVER = environ.get("MAIL_SERVER", "email-smtp.us-east-1.amazonaws.com")

TOKEN_PASSWORD_SALT = environ.get("TOKEN_PASSWORD_SALT")
TOKEN_SECRET_KEY = environ.get("TOKEN_SECRET_KEY")
