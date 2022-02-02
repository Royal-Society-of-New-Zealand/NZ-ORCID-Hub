#!/usr/bin/env bash

# Script location directory:
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH=$DIR
# export FLASK_ENV=development
export FLASK_APP=orcid_hub
export LANG=en_US.UTF-8
export ENV=test
# ENV=dev0

##   flask process
export DATABASE_URL="sqlite:///:memory:"
export EXTERNAL_SP=''
# EXTERNAL_SP=https://dev.orcidhub.org.nz/Tuakiri/SP
# [ -z $RQ_REDIS_URL ] && RQ_REDIS_URL=redis://redis:6379/0
export RQ_REDIS_URL=''
export LOAD_TEST=1
export RQ_ASYNC=0
export RQ_CONNECTION_CLASS=fakeredis.FakeStrictRedis

export ORCID_API_BASE="https://api.sandbox.orcid.org/v2.0/"
export ORCID_BASE_URL="https://sandbox.orcid.org/"
export SECRET_KEY="***********"

export AUTHORIZATION_BASE_URL="${ORCID_BASE_URL}oauth/authorize"
export TOKEN_URL="${ORCID_BASE_URL}oauth/token"

export TESTING=True
export OAUTHLIB_INSECURE_TRANSPORT=1
export TEMPLATES_AUTO_RELOAD=True
export OAUTH2_PROVIDER_TOKEN_EXPIRES_IN=86400

# add mail server config
# MAIL_PORT=2525
# MAIL_SUPPRESS_SEND=False
# MAIL_DEFAULT_SENDER="no-reply@orcidhub.org.nz"
# MAIL_SERVER="dev.orcidhub.org.nz"

export MEMBER_API_FORM_BASE_URL="https://orcid.org/content/register-client-application-sandbox"
export MEMBER_API_FORM_MAIL=0
export NOTE_ORCID="An NZ ORCID Hub integration for"
export CRED_TYPE_PREMIUM=2
export APP_NAME="NZ ORCID HUB"
export APP_DESCRIPTION="This is an ORCID integration through the NZ ORCID HUB connecting"
export DEFAULT_COUNTRY="NZ"


[[ $@ ==  *tests* || $@ == *test*.py* ]] || dest=tests
pytest --ignore=venv --ignore=orcid_api -v --cov-config .coveragerc  --cov . $dest $@

# OAUTHLIB_INSECURE_TRANSPORT=1
# ORCID_CLIENT_ID=APP-6D4L3L2H5L36H6GE
# ORCID_CLIENT_SECRET=4234539a-b3f9-4988-8772-160db671d814
# P12_PASSWORD=p455w0rd
# PAGER=most

