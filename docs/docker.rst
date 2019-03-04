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
#. Create the environment conviguration file **.env** from **.env.sample**
#. Set up environment variables UID and GID: `export GID=$(id -g) UID` (it would be helpful to add this to your user shell run command script, e.g., *.bashrc*)
#. Generate SSL the server key and a self signed certificata in **.keys** directory, e.g., `cd .keys; ../gen-keys/genkey.sh dev.orcidhub.org.nz; cd -`
#. Create PostgreSQL instace folder: `mkdir -p pgdata data/redis`
#. Run application containers: `docker-compose up -d`
#. Register a Hub administrator, e.g., `docker-compose exec app ./flask.sh cradmin -V rad42@mailinator.com` (more options available: `docker-compose exec app ./flask.sh cradmin --help`)
#. Open the Hub Appliction in a browser using http://localhost.

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

The application image uses several environment variables which are easy
to miss. These ariable should be set up for the specific runtime
environment. The configuration should set up in the *.env* file:

==========================  ==================
Variable                    Description
==========================  ==================
ENV                         The runtime environment name (default: *test*)
SHIB_IDP_DOMAINNAME         Your **Idendtity Provider** domain name (default: *http://directory.tuakiri.ac.nz*)
SHIB_METADATA_CERT_FILE     Meta data signig certificate (default: *conf/tuakiri-test-metadata-cert.pem*)
SHIB_METADATA_PROVIDER_URI  **Shibboleth** SAML 2.0 meta data provider URI [NativeSPMetadataProvider](https://wiki.shibboleth.net/confluence/display/SHIB2/NativeSPMetadataProvider) (default: *https://engine.surfconext.nl/authentication/idp/metadata*)
SHIB_SP_DOMAINNAME          Your **Service Provider** domain name (default: *${ENV}.<container domainname>*)
SHIB_SSO_DS_URL             SSO discovery service URL (default: *https://${SHIB_IDP_DOMAINNAME}/ds/DS*)
ORCID_CLIENT_ID             Orcid API client ID and secret, e.g., *0000-1234-2922-7589*
ORCID_CLIENT_SECRET         Orcid API client ID and secret, e.g., *b25ab710-89b1-49e8-65f4-8df4f038dce9*
PGPASSWORD                  PostgreSQL password
PGPORT                      The port on which PostgreSQL should be mapped to (should be unique) (default: 5432)
SECRET_KEY                  Hub secret key for data encryption
SENTRY_DSN                  Sentry DSN (optional)
SUBNET                      2 first octets (it should be unique for each enviroment run on the same machine), (default: *172.33*)
==========================  ==================
