#################################
Orcid Hub DB Recovery From Backup
#################################


.. role:: bash(code)
   :language: bash


.. role:: sql(code)
   :language: sql


Full DB Recovery
****************

#. Stop the DB server, if it's running: :bash:`docker-compose stop db`;

#. Remove all existing files and subdirectories under the cluster data directory and under the root directories of any tablespaces you are using.

#. Restore DB "cluster" data directory using the latest DB file backup `YYYY-MM-DDTHHMMSS.tar.bz2` located in `~/archive` into `~/pgdata` directroy;

#. Create a recovery command file `recovery.conf` in the cluster data directory. You might also want to temporarily modify pg_hba.conf to prevent users from connecting until you are sure the recovery was successful::

    restore_command = 'test -f /archive/%f.bz2 && bzip2 -c -d /archive/%f.bz2 >%p'

#. Start the server: :bash:`docker-compose start db`. The server will go into recovery mode and proceed to read through the archived WAL files it needs. Should the recovery be terminated because of an external error, the server can simply be restarted and it will continue recovery. Upon completion of the recovery process, the server will rename recovery.conf to recovery.done (to prevent accidentally re-entering recovery mode later) and then commence normal database operations.

#. Verify that the recovery was successful using the DB container logs: :bash:`docker-compose logs db`. The log should look like as follows::

    db_1         | 2018-06-05 01:01:29.011 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
    db_1         | 2018-06-05 01:01:29.011 UTC [1] LOG:  listening on IPv6 address "::", port 5432
    db_1         | 2018-06-05 01:01:29.029 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
    db_1         | 2018-06-05 01:01:29.047 UTC [10] LOG:  database system was interrupted; last known up at 2018-06-04 14:00:13 UTC
    db_1         | 2018-06-05 01:01:29.060 UTC [10] LOG:  starting archive recovery
    db_1         | 2018-06-05 01:01:29.130 UTC [10] LOG:  restored log file "000000010000000000000077" from archive
    db_1         | 2018-06-05 01:01:29.177 UTC [10] LOG:  redo starts at 0/77000028
    db_1         | 2018-06-05 01:01:29.179 UTC [10] LOG:  consistent recovery state reached at 0/77000130
    db_1         | 2018-06-05 01:01:29.180 UTC [1] LOG:  database system is ready to accept read only connections
    db_1         | 2018-06-05 01:01:29.259 UTC [10] LOG:  restored log file "000000010000000000000078" from archive
    db_1         | 2018-06-05 01:01:29.449 UTC [10] LOG:  restored log file "000000010000000000000079" from archive
    db_1         | 2018-06-05 01:01:29.571 UTC [10] LOG:  restored log file "00000001000000000000007A" from archive
    db_1         | 2018-06-05 01:01:29.691 UTC [10] LOG:  restored log file "00000001000000000000007B" from archive
    db_1         | 2018-06-05 01:01:29.803 UTC [10] LOG:  restored log file "00000001000000000000007C" from archive
    db_1         | 2018-06-05 01:01:29.844 UTC [10] LOG:  redo done at 0/7B03A158
    db_1         | 2018-06-05 01:01:29.844 UTC [10] LOG:  last completed transaction was at log time 2018-06-05 00:59:41.700382+00
    db_1         | 2018-06-05 01:01:29.930 UTC [10] LOG:  restored log file "00000001000000000000007B" from archive
    db_1         | 2018-06-05 01:01:29.982 UTC [10] LOG:  selected new timeline ID: 2
    db_1         | 2018-06-05 01:01:30.247 UTC [10] LOG:  archive recovery complete
    db_1         | 2018-06-05 01:01:30.356 UTC [1] LOG:  database system is ready to accept connections


Point-in-Time Recovery (PITR)
*****************************

By default, recovery will recover to the end of the WAL log. In order to perform **PITR** the following parameters can be used to specify an earlier stopping point. At most one of ``recovery_target``, ``recovery_target_lsn``, ``recovery_target_name``, ``recovery_target_time``, or ``recovery_target_xid`` can be used; if more than one of these is specified in the configuration file, the last entry will be used. Also you would need to add ``recovery_target_action = promote`` to `recovery.conf`. Alernatively, you can exeucute: :sql:`SELECT pg_xlog_replay_resume();`

For example, in order to recoer **DB** untill the state at, let's say, ``Tue Jun  4 01:33:53 UTC 2018`` you would need to add to `recovery.conf`::

 recovery_target_time = '2018-06-04 01:33:53 UTC'
 recovery_target_action = promote

Setting Up Hot Stand-up DB
**************************

In order to setup a hot stand-by DB. The `recovery.conf` should have following settings::

 # rename this file to recovery.conf and change master DB server IP address:
 standby_mode = 'on'
 restore_command = 'test -f /archive/%f.bz2 && bzip2 -c -d /archive/%f.bz2 >%p'
 primary_conninfo = 'host=MASTER_SERVER_IP port=5432 user=postgres'
 trigger_file = '/var/lib/postgresql/data/pg_failover_trigger.00'


Where *MASTER_SERVER_IP* should be your master DB private or public IP address. Make sure the master DB server can be accessed from the stand-by server.

