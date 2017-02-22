# You should put the valid member API client id
# of Research Organisation in place of this dummy data
client_id = "APP-AAAAAAAAA"

# You should put the valid member API Secret id of
# Research Organisation in place of this dummy data
client_secret = "AAAA-AAA-AA-AAA-AAAAA"

# Change the URL as per the enviornment
authorization_base_url = 'https://sandbox.orcid.org/oauth/authorize'
token_url = 'https://pub.sandbox.orcid.org/oauth/token'
scope = ['/authenticate']

# Put your application redirect URL in place of dummy data
redirect_uri = 'https://AAAA'

# Put the postgresql connection url
SQLALCHEMY_DATABASE_URI = 'postgresql://AAA:AAA@localhost:5432/AAAA'
SQLALCHEMY_MIGRATE_REPO = 'db_repository'
