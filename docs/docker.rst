Application Docker Image
------------------------

Application Docker Image (`orcidhub/app`) is packaged with:

 - CentOS 7
 - Apache 2.4
 - Python 3.6
 - mod_wsgi (Pythgon/WSGI Apache module)
 - psycopg2 (native PostgreSQL Python DB-API 2.0 driver)
 - PyPI packages necessary for the application

Usage
~~~~~

The following steps will set up a local ORCID Hub application instance using docker.

#. Install **docker** following the instruction at https://docs.docker.com/install/linux/docker-ce/ubuntu/
#. Install **git** and **docker-compose**: `sudo apt install -y git docker-compose`
#. Add your user to the **docker** user group: https://docs.docker.com/install/linux/linux-postinstall/#manage-docker-as-a-non-root-user
#. And configure Docker to start on boot: https://docs.docker.com/install/linux/linux-postinstall/#configure-docker-to-start-on-boot
#. Clone the project repository: `git clone https://github.com/Royal-Society-of-New-Zealand/NZ-ORCID-Hub.git`
#. Change the current directory: `cd NZ-ORCID-Hub`
#. Create the environment configuration file **.env** from **.env.sample**
#. Set up environment variables UID and GID: `export GID=$(id -g) UID`
#. Generate SSL the server key and a self signed certificata in **.keys** directory, e.g., `cd .keys; ../gen-keys/genkey.sh dev.orcidhub.org.nz; cd -`
#. Create PostgreSQL and redis instance folders: `mkdir -p pgdata data/redis`
#. Run application containers: `docker-compose up -d`
#. Register a Hub administrator, e.g., `docker-compose exec app ./flask.sh cradmin -V rad42@mailinator.com` (more options available: `docker-compose exec app ./flask.sh cradmin --help`)
#. Enable sendmail, see `Sendmail configuration <http://docs.orcidhub.org.nz/latest/sendmail.rst>`_
#. Open the Hub Application in a browser using http://localhost.

If successful, you will have five containers running: nzorcidhub_worker_1,
nzorcidhub_scheduler_1, nzorcidhub_app_1, nzorcidhub_redis_1, and nzorcidhub_db_1.
App is the core Hub code, and the process to connect to for users.
Redis, worker, and scheduler are the processes that managing the Hub's task queue.

Every subsequent restart can be achieved with:

.. code-block:: bash

   export GID=$(id -g) UID
   docker-compose up -d

from within the source directory.  If/when you wish to stop the Hub simply:

.. code-block:: bash

   docker-compose down

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

The application image uses several environment variables which are easy
to miss. These variables should be set up for the specific runtime
environment with the configuration specified in the *.env* file:

==========================  ==================
Variable                    Description
==========================  ==================
ENV                         The runtime environment name (default: *test*)
SHIB_IDP_DOMAINNAME         Your **Identity Provider** domain name (default: *http://directory.tuakiri.ac.nz*)
SHIB_METADATA_CERT_FILE     Meta data signing certificate (default: *conf/tuakiri-test-metadata-cert.pem*)
SHIB_METADATA_PROVIDER_URI  **Shibboleth** SAML 2.0 meta data provider URI [NativeSPMetadataProvider](https://wiki.shibboleth.net/confluence/display/SHIB2/NativeSPMetadataProvider) (default: *https://engine.surfconext.nl/authentication/idp/metadata*)
SHIB_SP_DOMAINNAME          Your **Service Provider** domain name (default: *${ENV}.<container domainname>*)
SHIB_SSO_DS_URL             SSO discovery service URL (default: *https://${SHIB_IDP_DOMAINNAME}/ds/DS*)
ORCID_CLIENT_ID             Orcid API client ID and secret, e.g., *0000-1234-2922-7589*
ORCID_CLIENT_SECRET         Orcid API client ID and secret, e.g., *b25ab710-89b1-49e8-65f4-8df4f038dce9*
PGPASSWORD                  PostgreSQL password
PGPORT                      The port on which PostgreSQL should be mapped to (should be unique) (default: 5432)
SECRET_KEY                  Hub secret key for data encryption
SENTRY_DSN                  Sentry DSN (optional)
SUBNET                      2 first octets (it should be unique for each environment run on the same machine), (default: *172.33*)
==========================  ==================

Common problems
~~~~~~~~~~~~~~~

Error at SSL creation in setup
______________________________

If you get the error "unable to write random state" at SSL certificate creation,
you need to get ownership of ~/.rnd (which is likely owned by root). The
easiest way to fix is to delete this file:

.. code-block:: bash

   sudo rm ~/.rnd

and retry this step.

Can only docker/docker-compose with sudo
________________________________________

If `docker-compose up` fails the most likely cause is
that you need to add the current user to the docker group.

.. code-block:: bash

   sudo usermod -aG docker {your-user}

Once done, log out/in or restart to have this change take effect.

NB this is likely unsuitable for any production instance as the user will
now be able to run containers to obtain root privileges.
See: https://docs.docker.com/engine/security/security/#docker-daemon-attack-surface

Services report error(s) during docker-compose up
_________________________________________________

If `docker-compose up` fails at nzorcidhub_app_1, e.g., with
"ERROR: for nzorcidhub_app_1  cannot start service app...Bind for 0.0.0.0:443
failed:  port is already allocated" because you have other services using these
ports, alternative ports for the Hub instance can be set in **.env**.

==========================  ==================
Variable                    Description
==========================  ==================
HTTP_PORT                   alternative http port (default: *80*)
HTTPS_PORT                  alternative https port (default: *443*)
==========================  ==================

If it's just a remnant of an earlier `docker-compose pull` or similar, a restart
or killing the docker-proxy process will clear this isssue, e.g.,

.. code-block:: bash

   sudo lsof -i:433 | grep LISTEN
   sudo kill {PID identified above}

If `docker-compose up` fails at nzorcidhub_db_1, you've likely forgotten to
precede this command with the necessary `export GID=$(id -g) UID`.

Need more help
______________

For more guidance on troubleshooting docker see
`Troubleshooting <http://docs.orcidhub.org.nz/latest/troubleshooting.rst>`_
