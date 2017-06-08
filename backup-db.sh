TS_LABEL=$(date +%FT%s)
#cd $HOME
docker-compose exec db psql -U postgres -c "SELECT pg_start_backup('$TS_LABEL', false, false);"
tar cjf ./backup/$TS_LABEL.tar.bz2 ./pgdata
docker-compose exec db psql -U postgres -c "SELECT pg_stop_backup(true);"

