.. _webhooks:

ORCID API Proxy
===============

An API proxy is an interface that provides controlled access to other system backend
services. Rather than having them being consumed directly, those services can be accessed
indirectly via the Edge API proxy. ORCID API Proxy provides value-added
features such as:

 - Security
 - Rate limiting
 - Transformations
 - Fault handling


THE NZ ORCID Hub provides direct access to user access tokens. Using these access tokens, you
can directly access ORCID's API. First, you need to obtain a client credential access token 
and use the NZ ORCID Hub to do the 3-legged authentication dance to obtain access tokens for users, which are then
stored at ORCID Hub database. These tokens are used to access users' ORCID records:

.. image:: images/orcid_api_directly.png

However, an easier way is to use the NZ ORCID Hub's API Proxy. To access the ORCID API Proxy, you need to use
API access tokens. Unlike the previous method, you need only aquire a client credential token, which you can use to access all user profiles, for users who are affiliated with your organisation.

.. image:: images/orcid_api_proxy.png


For testing purpose you can use `cURL<https://en.wikipedia.org/wiki/CURL>`_, for example,

.. code-block:: shell

    curl -X POST -d "client_id=CLIENT_ID&client_secret=CLIENT_SECRET&grant_type=client_credentials" https://test.orcidhub.org.nz/oauth/token

You will get a JSON document with an access token, which you can use to make calls to ORCID Hub API
including ORCID API Proxy:

.. code-block:: json

    {
        "access_token": "Qy4OCN3Ab6674JjzbFVR473j3oKVgn",
        "expires_in": 86400,
        "token_type": "Bearer",
        "scope": ""
    }


For example, to retrieve a user profile:


.. code-block:: shell

    curl -X GET "https://test.orcidhub.org.nz/orcid/api/v2.1/0000-0001-8228-7153" -H "accept: application/vnd.orcid+xml; qs=5" -H "authorization: Bearer jxDJWSna7wG73FoMSjOMRlq5pF1TZ4"


You can explore ORCID Hub API at https://test.orcidhub.org.nz/api-docs or https://orcidhub.org.nz/api-docs, and ORCID API at https://api.orcid.org/v2.1/#/Member_API_v2.1.

