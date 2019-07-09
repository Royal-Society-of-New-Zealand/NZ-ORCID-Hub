#!/bin/bash
set -e



cat >>$PGDATA/postgresql.conf <<EOF

wal_level = logical  # Adds information necessary to support logical decoding
wal_compression = on  # Compresses full-page writes written in WAL file.
archive_mode = on  # Allows archiving of WAL files using archive_command.
archive_command = 'test -f /archive/%f.bz2 || (bzip2 -c %p >/backup/%f.bz2 && mv /backup/%f.bz2 /archive/)'
archive_timeout = 3600
max_wal_senders = 5  # Sets the maximum number of simultaneously running WAL sender processes.

#hot_standby = 'on'  # uncomment on "slave" DB server and create recovery.conf

ssl = on

EOF
sed -i 's/#ssl = off/ssl = on/' $PGDATA/postgresql.conf

cat >>$PGDATA/_recovery.conf <<EOF
# rename this file to recovery.conf and change master DB server IP address:
standby_mode = 'on'
restore_command = 'test -f /archive/%f.bz2 && bzip2 -c -d /archive/%f.bz2 >%p'
primary_conninfo = 'host=MASTER_SERVER_IP port=5432 user=postgres'
trigger_file = '$PGDATA/pg_failover_trigger.00'
EOF


sed -i '/host all all all md5/d' $PGDATA/pg_hba.conf
cat >>$PGDATA/pg_hba.conf <<EOF

# Add here the access from the "slave" DB servers:
local    replication     postgres                            trust
hostssl  replication     postgres        34.225.18.251/32    trust
hostssl  all             all             34.225.18.251/32    trust
host     orcidhub        orcidhub        $(hostname -I|tr -d ' \n')/24     trust
host     orcidhub        orcidhub        app                 trust
# host   all             all             gateway             trust
EOF

createdb -U "$POSTGRES_USER" orcidhub
createdb -U "$POSTGRES_USER" sentry

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d orcidhub <<-EOSQL
  CREATE USER orcidhub WITH PASSWORD '${POSTGRES_PASSWORD}';
  GRANT ALL PRIVILEGES ON DATABASE orcidhub TO orcidhub;

  CREATE OR REPLACE FUNCTION promote_standby() RETURNS VOID
  SECURITY DEFINER LANGUAGE SQL AS 'COPY (SELECT 1) TO ''$PGDATA/pg_failover_trigger.00''';
  GRANT EXECUTE ON FUNCTION promote_standby() TO orcidhub;
EOSQL

cd $PGDATA
export PASSPHRASE=$(head -c 64 /dev/urandom  | base64)
openssl genrsa -des3 -passout env:PASSPHRASE -out server_.key 1024
openssl rsa -in server_.key -out server.key -passin env:PASSPHRASE
chmod 400 server.key
openssl req -new -key server.key -days 3650 -out server.crt -x509 -subj '/CN=orcidhubdb'
cp server.crt root.crt
