#!/bin/bash
set -e

cat >>/var/lib/postgresql/data/postgresql.conf <<EOF

wal_level = logical  # Adds information necessary to support logical decoding
wal_compression = on  # Compresses full-page writes written in WAL file.
archive_mode = on  # Allows archiving of WAL files using archive_command.
archive_command = 'test ! -f /archive/%f.bz2 && bzip2 -c %p >/backup/%f.bz2 && mv /backup/%f.bz2 /archive/'
archive_timeout = 3600
max_wal_senders = 5  # Sets the maximum number of simultaneously running WAL sender processes.

#hot_standby = 'on'  # uncomment on "slave" DB server and create recovery.conf:
EOF

cat >>/var/lib/postgresql/data/_recovery.conf <<EOF
# rename this file to recovery.conf and change master DB server IP address:
restore_command = 'test -f /archive/%f.bz2 && bzip2 -c -d /archive/%f.bz2 >%p'
primary_conninfo = 'host=MASTER_SERVER_IP port=5432 user=postgres'
EOF

cat >>/var/lib/postgresql/data/pg_hba.conf <<EOF

# Add here the access from the "slave" DB servers:
local   replication     postgres                                    trust
host    replication     postgres        34.225.18.251/32            trust
host    all             all             34.225.18.251/32            trust
EOF

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER orcidhub WITH PASSWORD '${POSTGRES_PASSWORD}';
    CREATE DATABASE orcidhub;
    GRANT ALL PRIVILEGES ON DATABASE orcidhub TO orcidhub;
EOSQL

