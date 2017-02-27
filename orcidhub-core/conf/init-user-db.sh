#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER orcidhub WITH PASSWORD '${POSTGRES_PASSWORD}';
    CREATE DATABASE orcidhub;
    GRANT ALL PRIVILEGES ON DATABASE orcidhub TO orcidhub;
EOSQL
