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
SQLALCHEMY_DATABASE_URI += "@db:5432/orcidhub"
SQLALCHEMY_MIGRATE_REPO = 'db_repository'

DB_NAME = environ.get("PGDATABASE", "orcidhub")
DB_USERNAME = environ.get("PGUSER", "orcidhub")
DB_PASSWORD = environ.get("POSTGRES_PASSWORD", environ.get("POSTGRES_PASSWORD", "p455w0rd"))
DB_HOSTNAME = environ.get("PGHOST", "db")
