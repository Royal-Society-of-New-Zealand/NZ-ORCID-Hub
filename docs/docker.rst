Application Docker Image
------------------------

Application Docker Image (`orcidhub/app`_) is packaged with: - CentOS 7
- Apache 2.4 - Python 3.6 - mod_wsgi (Pythgon/WSGI Apache module) -
psycopg2 (native PostgreSQL Python DB-API 2.0 driver) - PyPI packages
necessary for the application

Usage
~~~~~

1. run application containers: ``docker-compose up -d``
2. find container IP address:
   ``docker inspect --format '{{.NetworkSettings.IPAddress}}' app``
3. verify it’s running:
   ``http $(docker inspect --format '{{.NetworkSettings.IPAddress}}' app)``

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

The application image uses several environment variables which are easy
to miss. These ariable should be set up for the specific runtime
environment.

ENV
^^^

The runtime environment name (default: *test*)

SHIB_SP_DOMAINNAME
^^^^^^^^^^^^^^^^^^

Your *Service Provider* domain name (default: \*${ENV}.“*)

SHIB_IDP_DOMAINNAME
^^^^^^^^^^^^^^^^^^^

Your *Idendtity Provider* domain name, e.g.,
*http://directory.tuakiri.ac.nz*

SHIB_SSO_DS_URL
^^^^^^^^^^^^^^^

SSO discovery service URL (default:
*https://${SHIB_IDP_DOMAINNAME}/ds/DS*)

SHIB_METADATA_PROVIDER_URI
^^^^^^^^^^^^^^^^^^^^^^^^^^

*Shibboleth* SAML 2.0 meta data provider URI (more at:
https://wiki.shibboleth.net/confluence/display/SHIB2/NativeSPMetadataProvider)

SHIB_METADATA_CERT_FILE
^^^^^^^^^^^^^^^^^^^^^^^

Meta data signig certificat

ORCID_CLIENT_ID and ORCID_CLIENT_SECRET
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Orcid API client ID and secret

Steps to execute this application
---------------------------------

If you are running this application for the first time then follow steps
a to d:

a) From the project directory run pip3 install -r requirement.txt
b) install run install_package.sh to install postgress and required libraries
c) Create database and user in postgres

.. code-block:: sql

    CREATE USER orcidhub WITH PASSWORD ‘***’;
    CREATE DATABASE orcidhub;
    GRANT ALL PRIVILEGES ON DATABASE orcidhub to orcidhub;


d) Run `orcidhub initdb` to create the tables in the application database.

.. _Application Docker Image: #application-docker-image
.. _Usage: #usage
.. _Environment Variables: #environment-variables
.. _ENV: #env
.. _SHIB_SP_DOMAINNAME: #shib-sp-domainname
.. _SHIB_IDP_DOMAINNAME: #shib-idp-domainname
.. _SHIB_SSO_DS_URL: #shib-sso-ds-url
.. _SHIB_METADATA_PROVIDER_URI: #shib-metadata-provider-uri
.. _SHIB_METADATA_CERT_FILE: #shib-metadata-cert-file
.. _ORCID_CLIENT_ID and ORCID_CLIENT_SECRET: #orcid-client-id-and-orcid-client-secret
.. _Steps to execute this application: #steps-to-execute-this-application
.. _Development Environment: #development-environment
.. _orcidhub/app: https://hub.docker.com/r/orcidhub/app/

.. |Build Status| image:: https://travis-ci.org/Royal-Society-of-New-Zealand/NZ-ORCID-Hub.svg?branch=master
   :target: https://travis-ci.org/Royal-Society-of-New-Zealand/NZ-ORCID-Hub
.. |Coverage Status| image:: https://coveralls.io/repos/github/Royal-Society-of-New-Zealand/NZ-ORCID-Hub/badge.svg
   :target: https://coveralls.io/github/Royal-Society-of-New-Zealand/NZ-ORCID-Hub
