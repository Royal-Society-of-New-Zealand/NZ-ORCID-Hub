#!/usr/bin/env bash

# Script location directory:
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH=$DIR
export FLASK_ENV=development
export FLASK_APP=orcid_hub
export LANG=en_US.UTF-8
export ENV=test
ENV=dev0

##   flask process
export DATABASE_URL="sqlite:///:memory:"
export EXTERNAL_SP=''
# EXTERNAL_SP=https://dev.orcidhub.org.nz/Tuakiri/SP
# [ -z $RQ_REDIS_URL ] && RQ_REDIS_URL=redis://redis:6379/0
export RQ_REDIS_URL
export LOAD_TEST=1
export RQ_ASYNC=0
export RQ_CONNECTION_CLASS=fakeredis.FakeStrictRedis

[[ $@ ==  *tests* || $@ == *test*.py* ]] || dest=tests
pytest --ignore=venv --ignore=orcid_api -v --cov-config .coveragerc  --cov . $dest $@

# OAUTHLIB_INSECURE_TRANSPORT=1
# ORCID_CLIENT_ID=APP-6D4L3L2H5L36H6GE
# ORCID_CLIENT_SECRET=4234539a-b3f9-4988-8772-160db671d814
# P12_PASSWORD=p455w0rd
# PAGER=most
