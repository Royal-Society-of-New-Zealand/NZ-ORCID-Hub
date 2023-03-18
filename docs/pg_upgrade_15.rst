PostgreSQL Upgrade From Version 9.6, 10.x, 11.x to 15.x
=======================================================

Please follow the steps bellow:

#. Dump DB using the current PostgreSQL version **pg_dump**: ``pg_dump --disable-triggers -d orcidhub -U orcidhub | xz -e - | pv > full.sql.xz``
#. Stop and drop existing containers and remove ``/var/lib/docker``.
#. Upgrade docker and docker-compose (1.23.0) following https://docs.docker.com/install/linux/docker-ce/centos/#os-requirements

    .. code-block:: shell

     sudo curl -L https://github.com/docker/compose/releases/download/1.23.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
     sudo chmod +x /usr/local/bin/docker-compose
#. Move **pgdata** directory and recreate it: ``mv pgdata pgdata_; mkdir pgdata``
#. Recreate solution: ``docker-compose up -d``
#. Restored DB: ``xz -d -c ./full.sql.xz | psql -d orcidhub -U postgres -f - &>log.log``
#. If you had customized the configuration, copy your configuration files form the backup directory **pgdata_** (*pg_hba.conf* and *pg_ident.conf*)
#. And finally restart the solution.
