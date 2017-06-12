#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER orcidhub WITH PASSWORD '${POSTGRES_PASSWORD}';
    CREATE DATABASE orcidhub;
    GRANT ALL PRIVILEGES ON DATABASE orcidhub TO orcidhub;
EOSQL

cat >>/var/lib/postgresql/data <<EOF

## add to pg_hba.conf:
## local   replication     postgres		trust 
wal_level = logical
wal_compression = on  # Compresses full-page writes written in WAL file.
archive_mode = on  # Allows archiving of WAL files using archive_command.
archive_command = 'test ! -f /backup/%f.bz2 && bzip2 -c %p >/backup/%f.bz2'
max_wal_senders = 3  # Sets the maximum number of simultaneously running WAL sender processes.
EOF

