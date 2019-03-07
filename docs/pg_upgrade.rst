PostgreSQL Upgrade From Version 9.6 to 10.x, 11.x
=================================================

Please follow the steps bellow:

#. Modify DB schema executing script bellow.
#. Dump DB using the current PostgreSQL version **pg_dump**: ``pg_dump --disable-triggers -d orcidhub -U orcidhub > full.sql``
#. Stop and drop existing containers and remove ``/var/lib/docker``.
#. Upgrade docker and docker-compose (1.23.0) following https://docs.docker.com/install/linux/docker-ce/centos/#os-requirements

    .. code-block:: shell

     sudo curl -L https://github.com/docker/compose/releases/download/1.23.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
     sudo chmod +x /usr/local/bin/docker-compose
#. Move **pgdata** directory and recreate it: ``mv pgdata pgdata_; mkdir pgdata``
#. Recreate solution: ``docker-compose up -d``
#. Restored DB: ``psql -d orcidhub -U postgres -f full.sql &>log.log``
#. If you had customized the configuration, copy your configuration files form the backup directory **pgdata_**
#. And finally restart the solution.

Database upgrade script:

.. code-block:: sql

  ALTER TABLE client ALTER COLUMN created_at SET DEFAULT (now() AT TIME ZONE 'UTC');
  ALTER TABLE orcidtoken ALTER COLUMN created_at SET DEFAULT (now() AT TIME ZONE 'UTC');
  ALTER TABLE org_invitation ALTER COLUMN created_at SET DEFAULT (now() AT TIME ZONE 'UTC');
  ALTER TABLE organisation ALTER COLUMN created_at SET DEFAULT (now() AT TIME ZONE 'UTC');
  ALTER TABLE task ALTER COLUMN created_at SET DEFAULT (now() AT TIME ZONE 'UTC');
  ALTER TABLE url ALTER COLUMN created_at SET DEFAULT (now() AT TIME ZONE 'UTC');
  ALTER TABLE "user" ALTER COLUMN created_at SET DEFAULT (now() AT TIME ZONE 'UTC');
  ALTER TABLE user_invitation ALTER COLUMN created_at SET DEFAULT (now() AT TIME ZONE 'UTC');
  ALTER TABLE user_org ALTER COLUMN created_at SET DEFAULT (now() AT TIME ZONE 'UTC');
  ALTER TABLE user_organisation_affiliation ALTER COLUMN created_at SET DEFAULT (now() AT TIME ZONE 'UTC');

  ALTER TABLE client ALTER COLUMN client_id SET NOT NULL;

  ALTER TABLE orcidtoken DROP COLUMN IF EXISTS created_by_id;
  ALTER TABLE orcidtoken DROP COLUMN IF EXISTS updated_by_id;
  ALTER TABLE user_organisation_affiliation DROP COLUMN IF EXISTS created_by_id;
  ALTER TABLE user_organisation_affiliation DROP COLUMN IF EXISTS updated_by_id;
  ALTER TABLE funding_contributor DROP COLUMN IF EXISTS status;
  ALTER TABLE "user" DROP COLUMN IF EXISTS edu_person_shared_token;
  ALTER TABLE task DROP COLUMN IF EXISTS is_task_expiry_email_sent;
  ALTER TABLE funding_contributor DROP COLUMN IF EXISTS put_code;
  ALTER TABLE funding_contributor DROP COLUMN IF EXISTS processed_at;

  ALTER TABLE audit.orcidtoken DROP COLUMN IF EXISTS created_by_id;
  ALTER TABLE audit.orcidtoken DROP COLUMN IF EXISTS updated_by_id;
  ALTER TABLE audit.user_organisation_affiliation DROP COLUMN IF EXISTS created_by_id;
  ALTER TABLE audit.user_organisation_affiliation DROP COLUMN IF EXISTS updated_by_id;
  ALTER TABLE audit."user" DROP COLUMN IF EXISTS edu_person_shared_token;

  DROP TABLE IF EXISTS ttt;
  DROP TABLE IF EXISTS ttt2;
  DROP TABLE IF EXISTS testtable;
  DROP TABLE IF EXISTS testtablewithbooleanfield;

  UPDATE affiliation_record SET country = LEFT(country,2) WHERE length(country) > 2;
  UPDATE audit.affiliation_record SET country = LEFT(country,2) WHERE length(country) > 2;

  ALTER TABLE funding_invitees ALTER COLUMN orcid TYPE character(19);
  ALTER TABLE peer_review_invitee ALTER COLUMN orcid TYPE character(19);
  ALTER TABLE work_contributor ALTER COLUMN orcid TYPE character(19);
  ALTER TABLE work_invitees ALTER COLUMN orcid TYPE character(19);

  ALTER TABLE orcidtoken ALTER COLUMN expires_in TYPE integer;
  ALTER TABLE audit.orcidtoken ALTER COLUMN expires_in TYPE integer;
