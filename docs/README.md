# NZ-ORCID-Hub [![Build Status](https://travis-ci.org/Royal-Society-of-New-Zealand/NZ-ORCID-Hub.svg?branch=master)](https://travis-ci.org/Royal-Society-of-New-Zealand/NZ-ORCID-Hub)[![Coverage Status](https://coveralls.io/repos/github/Royal-Society-of-New-Zealand/NZ-ORCID-Hub/badge.svg)](https://coveralls.io/github/Royal-Society-of-New-Zealand/NZ-ORCID-Hub)
The home of development for the New Zealand ORCID Hub.

- [Application Docker Image](#application-docker-image)
  * [Usage](#usage)
  * [Environment Variables](#environment-variables)
    + [ENV](#env)
    + [SHIB_SP_DOMAINNAME](#shib-sp-domainname)
    + [SHIB_IDP_DOMAINNAME](#shib-idp-domainname)
    + [SHIB_SSO_DS_URL](#shib-sso-ds-url)
    + [SHIB_METADATA_PROVIDER_URI](#shib-metadata-provider-uri)
    + [SHIB_METADATA_CERT_FILE](#shib-metadata-cert-file)
    + [ORCID_CLIENT_ID and ORCID_CLIENT_SECRET](#orcid-client-id-and-orcid-client-secret)
- [Steps to execute this application](#steps-to-execute-this-application)
- [Development Environment](#development-environment)


## Application Docker Image

Application Docker Image ([orcidhub/app](https://hub.docker.com/r/orcidhub/app/)) is packaged with:
 - CentOS 7
 - Apache 2.4
 - Python 3.6
 - mod_wsgi (Pythgon/WSGI Apache module)
 - psycopg2 (native PostgreSQL Python DB-API 2.0 driver)
 - PyPI packages necessary for the application

### Usage 

1. run application containers: `docker-compose up -d`
1. find container IP address: `docker inspect --format '{{.NetworkSettings.IPAddress}}' app`
1. verify it's running: `http $(docker inspect --format '{{.NetworkSettings.IPAddress}}' app)`

### Environment Variables

The application image uses several environment variables which are easy to miss. These ariable should be set up for the specific runtime environment.

#### ENV

The runtime environment name (default: **test**)

#### SHIB_SP_DOMAINNAME

Your **Service Provider** domain name (default: **${ENV}.<container domainname>"**)

#### SHIB_IDP_DOMAINNAME

Your **Idendtity Provider** domain name, e.g., *http://directory.tuakiri.ac.nz*

#### SHIB_SSO_DS_URL

SSO discovery service URL (default: **https://${SHIB_IDP_DOMAINNAME}/ds/DS**)

#### SHIB_METADATA_PROVIDER_URI

**Shibboleth** SAML 2.0 meta data provider URI (moro at: https://wiki.shibboleth.net/confluence/display/SHIB2/NativeSPMetadataProvider)

#### SHIB_METADATA_CERT_FILE

Meta data signig certificat

#### ORCID_CLIENT_ID and ORCID_CLIENT_SECRET

Orcid API client ID and secret

## Steps to execute this application

If you are running this application for the first time then follow steps a to d:
	a) From the project directory run pip3 install -r requirement.txt
	b) install run install_package.sh to install postgress and required libraries
	c) Create database and user in postgres
	
> - CREATE USER orcidhub WITH PASSWORD '*****';
> - CREATE DATABASE orcidhub;
> - GRANT ALL PRIVILEGES ON DATABASE orcidhub to orcidhub;.


d) Run initializedb.py to create table in postgres

Run application.py
Open link https://test.orcidhub.org.nz/index

## Development Environment

It is possible to run the application as stand-alone Python Flask application using another remote
application instance for Tuakiri user authentication. For example, if the remote 
(another application instance) url is https://dev.orcidhub.org.nz, all you need is to set up 
environment varliable `export EXTERNAL_SP=https://dev.orcidhub.org.nz/Tuakiri/SP`.

In order to siplify the development environemt you can user Sqlite3 DB for the backend. 
To set up the database use environment variable DATABASE_URL, e.g., 
`export DATABASE_URL=sqlite:///data.db` and run application
either directly invoking it with `python application.py` or using Flask CLI 
(http://flask.pocoo.org/docs/0.12/cli/):

```
export EXTERNAL_SP=https://dev.orcidhub.org.nz/Tuakiri/SP
export DATABASE_URL=sqlite:///data.db
export FLASK_APP=/path/to/main.py
export PYTHONPATH=$(dirname $FLASK_APP)  ## flask run has problems with setting up search paths
export FLASK_DEBUG=1
flask run
```

You can add these setting to you virtual environment activation script, e.g. (assuming it's located in the root directory):

```
export FLASK_APP=$(dirname $VIRTUAL_ENV)/main.py
export PYTHONPATH=$(dirname $FLASK_APP)
export EXTERNAL_SP=https://dev.orcidhub.org.nz/Tuakiri/SP
export DATABASE_URL=sqlite:///data.db
export FLASK_DEBUG=1
```

To connect to the PostgreSQL node:

```
export PGHOST=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker-compose ps -q db))
export DATABASE_URL=postgresql://orcidhub:p455w0rd@${PGHOST}:5432/orcidhub
```
