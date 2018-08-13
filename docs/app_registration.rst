.. _app_registration:

ORCID Hub API Appliction Registration
=====================================

In order to user ORCID Hub API you first need to register your application navigating to `Settings -> Hub API Registration`:

.. image:: images/api_app_registration.png

.. image:: images/app_registration_form.png

When you register your appliction the Hub generates application credentials, a pair of keys: *CLIENT_ID* and *CLIENT_SECRET*:


.. image:: images/app_credentials.png


You have to make sure that *CLIENT_SECRET* doesn't get composed. Make sure you neven included the client secret in the source of your appliction. If you have even a slightest suspicion about having leaked the client secret as soon as possible reset it using the same form:

.. image:: images/reset_client_secret.png

