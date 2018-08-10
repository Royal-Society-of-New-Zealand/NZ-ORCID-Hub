#!/usr/bin/env bash

# Script location directory:
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH=$DIR
export FLASK_APP=orcid_hub
export LANG=en_US.UTF-8
export RQ_REDIS_URL="${RQ_REDIS_URL:-redis://redis:6379/0}"
[ -z "$DATABASE_URL" ] && DATABASE_URL=postgresql://orcidhub@db:5432/orcidhub?options='-c statement_timeout=3000'
export DATABASE_URL

# Add $RANDOM to make the neame unique:
exec flask rq worker -n ORCIDHUB.$$.$RANDOM $@
