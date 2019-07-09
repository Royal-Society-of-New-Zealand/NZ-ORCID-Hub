.. _sendmail:

Sendmail configuration
======================

The hub instance uses the OS mail functions in order to send email.  For \*nix
that's likely to be sendmail either on the Host or a dedicated mail server.

WARNING: Take care; testing the Hub with mail sent out under an illegal name, e.g.,
`myuser@myhost-virtualbox` is a great way to get your IP blacklisted, so ensure you've
sendmail configured correctly.

Sendmail configuration for source or PyPI
-----------------------------------------

On the basis that your environment is able to send email with an address (and from
an IP) that is allowed by your domain, your hub instance email is enabled by setting
the following variables: MAIL_SERVER; MAIL_PORT; and MAIL_DEFAULT_SENDER.

NB: To ensure delivery and avoid appearing spammy, we have both SPF and DKIM enabled
for our dev, UAT, and production environments.

Sendmail configuration for Docker
---------------------------------

To send email from the Docker-based instance, you'll need to edit
**/etc/mail/sendmail.mc** accordingly to make it listen on the docker network and
enable the relay.

Find the IP that your container is being served from:

.. code-block:: bash

   docker inspect nzorcidhub_app_1 | grep IPAddress

With that IP, enable access to the *sendmail* server from the containers on the host,
e.g., for the default container IP (172.33.0.1) add the following to **sendmail.mc**:

::

    DAEMON_OPTIONS(`Port=smtp,Addr=172.33.0.1, Name=MTA')dnl
    FEATURE(`relay_based_on_MX')dnl

Grant **relay** access from the docker container network editing
**/etc/mail/access**, e.g.:

::

    Connect:localhost.localdomain           RELAY
    Connect:localhost                       RELAY
    Connect:127.0.0.1                       RELAY
    Connect:172                             RELAY

And don't forget to rebuild the configuration and restart *sendmail*, i.e.,:

.. code-block:: bash

    sudo m4 /etc/mail/sendmail.mc > /etc/mail/sendmail.cf
    sudo chmod 644 /etc/mail/sendmail.cf
    sudo /etc/init.d/sendmail restart
