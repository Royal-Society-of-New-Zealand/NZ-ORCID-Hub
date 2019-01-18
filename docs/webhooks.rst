.. _webhooks:

Webhooks
========

What is an ORCID webhook?
-------------------------

A webhook, according to `Wikipedia <https://en.wikipedia.org/wiki/Webhook>`_ is "a method of augmenting or altering the behaviour of a web page, or web application, with custom callbacks. These callbacks may be maintained, modified, and managed by third-party users and developers who may not necessarily be affiliated with the originating website or application.". In simple terms, a webhook allows your application to recieve notifications from another application. In the ORCID contex, the ORCID webhooks provides a mechanism for recieving user prifle uppade notifications, enabling applications to be informed when data within an ORCID record changes.


What is an ORCID Hub webhook?
-----------------------------

The ORCID Hub (hereafter preferred to as "the Hub") provide efficient way of managing the webhooks for all organisation users, so that, you do not need to register a webhook for each and every user yourself.
In addition, for the orginisations that do not have their own integration solutions, the Hub offeres a emial notification handler, which sends an email notification upon receiving a user record update event from ORCID Hub.

Webhook Registration
--------------------

.. figure:: images/webhooks_registration.png
    :alt: Webhook Registration
    :align: center

    Webhook Registration


.. figure:: images/webhooks_menu.png
    :alt: Navigation to the Webhook menu
    :align: center

    Navigation to the Webhook menu


.. figure:: images/webhooks_form.png
    :alt: Webhook registration form
    :align: center

    Webhook registration form

.. figure:: images/webhooks_invocation.png
    :alt: Webhooks in action
    :align: center

    Webhooks in action

