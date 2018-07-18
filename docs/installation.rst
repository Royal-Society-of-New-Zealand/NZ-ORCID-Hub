.. _installation:

ORCID Hub Installation
======================

Python Version
--------------

We recommend using the latest version of Python 3: Python3.6.

Dependencies
------------

In order to enable authentication via ORCID you need to acquire ORCID API creadential:

   - Create or login with an existing account at https://orcid.org (or https://sandbox.orcid.org)
   - Navigate to "Developer Tools" (https://orcid.org/developer-tools or https://sandbox.orcid.org/developer-tools);
   - Add http://127.0.0.1:5000/auth to redirect URLs and hit *Save*;
   - Copy CLIENT_ID and CLIENT_SECRET and set up environment varliables ORCID_CLIENT_ID and ORCID_CLIENT_SECRET with these values;
   - run :shell:`

TODO: acquire ORCID API creadentials, add the link

Sign up at ORCID with your email address.

Optional dependencies
~~~~~~~~~~~~~~~~~~~~~

For the integration with Shibboleth, the application should be deployed on Apache web server with ...
TODO: set up SENTRY account...


Minial Deployment
-----------------

Minimal runnig ORCID Hub (assuming you have created and activated Python 3.6 virtual environment):

.. code-block:: bash

   virtualenv -p python3.6 venv
   . ./venv/bin/activate
   pip install -U 'orcid-hub'
   orcidhub cradmin myadmin@mydomain.net --orcid YOUR-ORCID-ID -O YOUR-ORGANISATION-NAME
   orcidhub run


By defaul the application will create a Sqlite3 database.
You can customize the backend specifying *DATABASE_URL* (defaul: *sqlite:///orcidhub.db*), for example:

.. code-block:: bash

   export DATABASE_URL=postgresql://test.orcidhub.org.nz:5432/orcidhub
   # OR
   export DATABASE_URL=sqlite:///data.db


It is possible to run the application as stand-alone Python Flask application using another remote
application instance for Tuakiri user authentication. For example, if the remote
(another application instance) url is https://dev.orcidhub.org.nz, all you need is to set up
environment varliable `export EXTERNAL_SP=https://dev.orcidhub.org.nz/Tuakiri/SP`.

.. code-block:: bash

   export EXTERNAL_SP=https://dev.orcidhub.org.nz/Tuakiri/SP
   export DATABASE_URL=sqlite:///data.db
   export FLASK_ENV=development
   orcidhub run


To connect to the PostgreSQL node (if you are using the doker image):

.. code-block:: bash

   export PGHOST=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker-compose ps -q db))
   export DATABASE_URL=postgresql://orcidhub:p455w0rd@${PGHOST}:5432/orcidhub

