.. _development_env:

#######################
Development Environment
#######################

Minimal runnig ORCID Hub (assuming you have created and activated Python 3.6 virtual environment):

.. code-block:: bash

   virtualenv -p python3.6 venv
   . ./venv/bin/activate
   pip install -U 'orcid-hub[dev]'
   orcidhub initdb
   orcidhub cradmin myadmin@mydomain.net  # use a valid email
   orcidhub run


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
