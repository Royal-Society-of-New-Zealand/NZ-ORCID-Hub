#!/usr/bin/env bash

# Script location directory:
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH=$DIR
export FLASK_APP=orcid_hub
export LANG=en_US.UTF-8
export ENV=test

##   flask process
export DATABASE_URL="sqlite:///:memory:"
export EXTERNAL_SP=''
[ -z $RQ_REDIS_URL ] && RQ_REDIS_URL=redis://redis:6379/0
export RQ_REDIS_URL
export LOAD_TEST=1
export RQ_ASYNC=0
export RQ_CONNECTION_CLASS=fakeredis.FakeStrictRedis

[[ $@ ==  *tests* || $@ == *test*.py* ]] || dest=tests
pytest --ignore=venv --ignore=orcid_api -v --cov-config .coveragerc  --cov . $dest $@
