# MAILTO=
# SHELL=/bin/bash
TS_LABEL=$(date +%FT%s)
PATH=/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/aws/bin:$HOME/.local/bin:$HOME/bin:$PATH:/usr/local/bin

[ ! -f docker-compose.yml ] && cd $HOME
if docker-compose -q db &>/dev/null ; then
  docker-compose exec -T db psql -U postgres -c "VACUUM FULL ANALYZE;"
  docker-compose exec -T db psql -U postgres -c "VACUUM FULL ANALYZE;" -d orcidhub
  # docker-compose exec -T db psql -U postgres -c "SELECT pg_start_backup('$TS_LABEL', false);"
  docker-compose exec -T db psql -U postgres -c "SELECT pg_backup_start('$TS_LABEL');"
  sudo bash -c 'sync; echo 3 > /proc/sys/vm/drop_caches'
  # tar cjf ./backup/$TS_LABEL.tar.bz2 ./pgdata ; mv ./backup/$TS_LABEL.tar.bz2 ./archive/
  sudo XZ_OPT="-9 --memory=100000000" tar cJf ./backup/$TS_LABEL.tar.xz ./pgdata 
else
  # Backup host DB cluster:
  cd $HOME
  export PGUSER=postgres
  # psql -c "VACUUM FULL ANALYZE;"
  # psql -c "VACUUM FULL ANALYZE;" -d orcidhub
  # psql -c "VACUUM FULL ANALYZE;" -d orcidhub_dev
  # psql -c "VACUUM FULL ANALYZE;" -d orcidhub_test
  # psql -U postgres -c "SELECT pg_start_backup('$TS_LABEL', false);"
  vacuumdb -a -z
  psql -c "SELECT pg_start_backup('$TS_LABEL');"
  # tar cjf ./backup/$TS_LABEL.tar.bz2 ./pgdata ; mv ./backup/$TS_LABEL.tar.bz2 ./archive/
  sudo bash -c 'sync; echo 3 > /proc/sys/vm/drop_caches'
  sudo XZ_OPT="-9 --memory=1000000000" tar cJf ./backup/$TS_LABEL.tar.xz -C $(psql -t -c "SHOW data_directory;")/.. ./data 
fi
sudo mv ./backup/$TS_LABEL.tar.xz ./archive/
if docker-compose -q db &>/dev/null ; then
  # docker-compose exec -T db psql -U postgres -c "SELECT pg_stop_backup();"
  docker-compose exec -T db psql -U postgres -c "SELECT pg_backup_stop();"
else
  psql -c "SELECT pg_stop_backup();"
fi

sudo chmod g+r archive/00*.xz
sudo find ./archive -mtime +3 -name 20??-??-??\* -exec rm {} \;
sudo find ./archive -mtime +4 -name 000\*.xz -exec rm {} \;
