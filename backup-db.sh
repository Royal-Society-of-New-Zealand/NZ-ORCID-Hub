# MAILTO=
# SHELL=/bin/bash
TS_LABEL=$(date +%FT%s)
PATH=/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/aws/bin:$HOME/.local/bin:$HOME/bin:$PATH:/usr/local/bin

sudo bash -c 'sync; echo 3 > /proc/sys/vm/drop_caches'
[ ! -f docker-compose.yml ] && cd $HOME
docker-compose exec -T db psql -U postgres -c "VACUUM FULL ANALYZE;"
docker-compose exec -T db psql -U postgres -c "VACUUM FULL ANALYZE;" -d orcidhub
docker-compose exec -T db psql -U postgres -c "SELECT pg_start_backup('$TS_LABEL', false);"
# tar cjf ./backup/$TS_LABEL.tar.bz2 ./pgdata ; mv ./backup/$TS_LABEL.tar.bz2 ./archive/
XZ_OPT="-9 --memory=100000000" tar cJf ./backup/$TS_LABEL.tar.xz ./pgdata ; mv ./backup/$TS_LABEL.tar.xz ./archive/
docker-compose exec -T db psql -U postgres -c "SELECT pg_stop_backup();"
find ./archive -mtime +10 -exec rm {} \;
