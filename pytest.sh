#!/usr/bin/env bash

# Script location directory:
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH=$DIR
export FLASK_APP=orcid_hub
export LANG=en_US.UTF-8

##   flask process
export DATABASE_URL="sqlite:///:memory:"
export EXTERNAL_SP=''
pytest --ignore=venv --ignore=orcid_api -v --cov-config .coveragerc  --cov . tests $@
