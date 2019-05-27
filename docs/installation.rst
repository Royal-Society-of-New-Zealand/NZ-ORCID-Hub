.. _installation:

ORCID Hub Installation
======================

NB the Hub is intended to be, and the core code is, cross-platform; however it's much
simpler to get a fully functioning instance with \*nix.  Install instructions for an
evaluation Hub instance on Windows will follow as the kinks are worked out.

There are three different routes to getting an ORCID Hub instance up and running:

    - managing the dependencies yourself

        - via the ORCID-Hub PyPI Python package
        - setting up from the GitHub source

    - via the orcidhub Docker Image

Reasons to choose between the route:

The Docker image, and to a lesser extent the PyPI package, gives a very quick to launch
an instance of the Hub for evaluation. With the PyPI package you need to add sendmail
and redis for typical functions; while running from source will also be prompted to set up
the backend database.  Running from the GitHub source will be a little slower to get
going and involves more moving parts but provides the easiest way to allow you to
customise the look and feel to suit your Consortium.
NB all routes out of the box will launch an unmodified version of the NZ ORCID Hub
including local references to New Zealand and the Royal Society Te Apārangi.

Managing the dependencies yourself
----------------------------------

The Hub requires Python 3.x.  We recommend both Python3.6, and running the Hub with a
virtual environment, e.g. in your working directory:

.. code-block:: bash

   virtualenv -p python3.6 venv
   . ./venv/bin/activate

The Hub uses a database backend, with either `SQLite <https://www.sqlite.org/index.html>`_ or
`PostgreSQL <https://www.postgresql.org/>`_ supported.  We currently recommend PostgreSQL 11.
NB if no database url is given the Hub defaults to an embedded SQLite store.

Before you start you need to establish a means of authenticating the user
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to enable login via ORCID you'll need to acquire ORCID API credentials for your
Hub.  As this is only an 'authenticate' call, the `public API <https://support.orcid.org/hc/en-us/articles/360006897174>`_ is fine.  If you're new to
the ORCID API, public API credentials for the ORCID sandbox can be obtained like so:

   - Create or login with an existing account at https://sandbox.orcid.org;
   - Navigate to "Developer Tools" (https://sandbox.orcid.org/developer-tools);
   - Add your instance (e.g. for a local install http://127.0.0.1:5000/auth) to the allowed redirect URL list and hit *Save*;
   - Copy the resulting CLIENT_ID and CLIENT_SECRET for the needed environment variables: ORCID_CLIENT_ID and ORCID_CLIENT_SECRET

To enable Identity Federation SSO, you'll either need to configure your Hub instance
as a Shibboleth Service Provider. As well as registering your instance SP, running
Shibboleth also comes with its own dependency of Apache. See: `Shibboleth installation and
SP Creation <http://docs.orcidhub.org.nz/latest/shibboleth.rst>`_.

As an alternative to setting up the instance as a SP, it is possible to run the application
as a stand-alone Python Flask application and use another remote application for user
authentication. For example, if the remote SP is being provided by
https://dev.orcidhub.org.nz, all you need is to set up the *EXTERNAL_SP* environment
variable, e.g.,

.. code-block:: bash

   export EXTERNAL_SP=https://dev.orcidhub.org.nz/Tuakiri/SP

Optional dependencies
^^^^^^^^^^^^^^^^^^^^^

To enable the Hub to send email and act on task queues, you'll need to install
`redis <https://redis.io>`_ for your environment as well as configuring your environment's
sendmail service. More information on setting up sendmail can be found here:
`Sendmail Configuration <http://docs.orcidhub.org.nz/latest/sendmail.rst>`_.

The NZ ORCID Hub uses `Sentry <https://sentry.io/welcome/>`_ for error tracking and user
feedback.  We've found it a great service, but this is optional and likely unnecessary for
any evaluation.

Setting environment variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A Hub instance needs a range of environment variable to be set in order to function.
These can be set manually or by script at each runtime or, for ease, managed via a
settings.cfg file.  The variables that must be set in your environment are: FLASK_APP,
PYTHONPATH, and if you're using them DATABASE_URL and EXTERNAL_SP, e.g.:

.. code-block:: bash

   export FLASK_APP='orcid-hub'
   export FLASK_ENV='development'
   DIR='$( cd '$( dirname '${BASH_SOURCE[0]}' )' && pwd )'
   export PYTHONPATH=$DIR
   export LANG=en_US.UTF-8
   export DATABASE_URL='postgresql://orcidhub:****@localhost:5432/orcidhub'
   export EXTERNAL_SP='https://dev.orcidhub.org.nz/Tuakiri/SP'

For convenience you might want to script this initial setup.

The following variables can be provided by either settings.cfg placed in the /instance
folder OR by directly exporting to the environment:

==========================  ==================
Variable                    Description
==========================  ==================
ENV                         The runtime environment name (default: *dev*)
DEFAULT_COUNTRY             The Country default for any ORCID writes (default: *NZ*)
NOTE_ORCID                  Default note text for ORCID API requests (default: *An NZ ORCID Hub integration for*)
CRED_TYPE_PREMIUM           The default type of credentials requested (default: *2*, i.e,. "Premium Member")
APP_NAME                    Default App name prefix for ORCID API requests (default: *NZ ORCID HUB for*)
APP_DESCRIPTION             Default App description prefix for ORCID API requests (default: *This is an ORCID integration through the NZ ORCID HUB connecting*)
==========================  ==================

Configuring authentication services, i.e., in the absence of EXTERNAL_SP, or if using ORCID only

==========================  ==================
Variable                    Description
==========================  ==================
SHIB_IDP_DOMAINNAME         Your **Identity Providers** domain name (default: *http://directory.tuakiri.ac.nz*)
SHIB_METADATA_CERT_FILE     Meta data signing certificate location (default: *conf/tuakiri-test-metadata-cert.pem*)
SHIB_METADATA_PROVIDER_URI  **Shibboleth** SAML 2.0 meta data provider URI [NativeSPMetadataProvider](https://wiki.shibboleth.net/confluence/display/SHIB2/NativeSPMetadataProvider) (default: *https://engine.surfconext.nl/authentication/idp/metadata*)
SHIB_SP_DOMAINNAME          Your **Service Providers** domain name (default: *${ENV}.<container domainname>*)
SHIB_SSO_DS_URL             SSO discovery service URL (default: *https://${SHIB_IDP_DOMAINNAME}/ds/DS*)
ORCID_CLIENT_ID             Orcid API client ID and secret, e.g., *0000-1234-2922-7589*
ORCID_CLIENT_SECRET         Orcid API client ID and secret, e.g., *b25ab710-89b1-49e8-65f4-8df4f038dce9*
==========================  ==================

Configuring mail and redis defaults

==========================  ==================
Variable                    Description
==========================  ==================
MAIL_SERVER                 Mail server's name or IP (default: *dev.orcidhub.org.nz*)
MAIL_PORT                   Port for sending mail (default: *25*)
MAIL_DEFAULT_SENDER         Mail from Hub to be sent as (default *no-reply@orcidhub.org.nz*)
RQ_REDIS_URL                Redis server for rq (default *redis://localhost:6379/0*)
==========================  ==================

Optional variables

==========================  ==================
Variable                    Description
==========================  ==================
SECRET_KEY                  To specify the Hub secret key for data encryption (optional)
SENTRY_DSN                  Sentry project DSN (optional)
GA_TRACKING_ID              Google Analytics Tracking ID (optional)
==========================  ==================

Minimal deployment via PyPI
---------------------------

Assuming you have created and activated your Python 3.6 virtual environment and are in
your working directory, a minimal ORCID Hub instance can be quickly set up with PyPI
package and the following steps:

.. code-block:: bash

   pip install -U 'orcid-hub'

By default the PyPI application creates an embedded Sqlite3 database.
To use another backend, specify the engine and location via the *DATABASE_URL* environment
variable from its default (*sqlite:///data.db*).
Ensure the environment variables are set, settings.cfg is configured, and then create the
first user as a Hub Administrator

.. code-block:: bash

   orcidhub cradmin myadmin@mydomain.net --orcid YOUR-ORCID-ID -O YOUR-ORGANISATION-NAME

This command will create a Hub Admin user with email myadmin@mydomain.net, and if
using ORCID authentication, i.e., you've set ORCID API credentials,  YOUR-ORCID-ID, and
at the same time registering the first organisation with YOUR-ORGANISATION-NAME.

Launch the Hub with:

.. code-block:: bash

   orcidhub run

The result you can expect is for the terminal to start logging HTTP requests to the
new development Hub instance that you are serving from your localhost.  Navigate to
this instance in any modern browser and you should be able to sign in with your chosen
service.

NB: However until the rq worker and scheduler are running this instance will not
be able to action batch tasks and so won't send mail.

Minimal deployment via GitHub source
------------------------------------

Running the Hub from source is very similar to setting up from the PyPI orcid-hub
package. Ensure that git is installed and then from a terminal, clone the Hub source
into a suitable location and if desired switch to the branch.  NB: default master is
Hub's core development branch, origin/prod is the most current stable production release.
The folder NZ-ORCID-Hub now becomes your working directory:

.. code-block:: bash

   git clone https://github.com/Royal-Society-of-New-Zealand/NZ-ORCID-Hub.git
   cd NZ-ORCID-Hub
   git checkout origin/prod

Create the additional directories that a running Hub will require, enable the
recommended python virtual environment, and install the Hub's requirements:

.. code-block:: bash

   mkdir -p data/redis pgdata
   virtualenv -p python3.6 venv
   . ./venv/bin/activate
   sudo apt install python3.6-dev
   pip install -U pip
   pip install -U -r dev_requirements.txt

Set environment variables, and (optionally) create and configure instance/settings.cfg.
NB by pulling source code the instance folder will have been created with a
settings.sample.cfg that can be used as a guide.

Once the environment has been set up you create the Hub superuser and launch for the
first time:

.. code-block:: bash

   flask cradmin myadmin@mydomain.net --orcid YOUR-ORCID-ID -O YOUR-ORGANISATION-NAME
   flask run

The terminal should show the Hub logging, and served from localhost.  As with PyPI,
additional processes are needed for this instance to start responding to tasks.

Launch queue worker and a scheduler
-----------------------------------

To enable the Hub to action tasks, redis must be installed and running, and two
additional processes need to be active.  The easiest way to launch these is opening
another terminal, navigate to the project directory and enable your virtual python
environment. Set up at least the PYTHONPATH, FLASK_APP and FLASK_ENV environment
variables (and if non-default RQ_REDIS_URL). Once the environment established,
launch these processes with either:

For a PyPI-based instance or

.. code-block:: bash

   orcidhub rq scheduler & orcidhub rq worker --logging_level info

For a source-based instance.

.. code-block:: bash

   ./flask.sh rq scheduler & ./flask.sh rq worker --logging_level info

In either case this terminal should now report the birth of the worker process,
and a fully functioning test Hub should now be being served.
