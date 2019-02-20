.. _sendmail:

Sendmail configuration
======================

Enable access to the *sendmail* server from containers on the host. Find
and edit **/etc/mail/sendmail.mc** accordingly to make it listen on the
docker network and enable the relay:

::

    DAEMON_OPTIONS(`Port=smtp,Addr=172.18.0.1, Name=MTA')dnl
    FEATURE(`relay_based_on_MX')dnl

Grant **relay** access from the docker container network editing
**/etc/mail/access**, e.g.:

::

    Connect:localhost.localdomain           RELAY
    Connect:localhost                       RELAY
    Connect:127.0.0.1                       RELAY
    Connect:172                             RELAY


And don't forget to rebuild the configuration and restart *sendmail*:

.. code-block:: bash

    sudo m4 /etc/mail/sendmail.mc > /etc/mail/sendmail.cf
    sudo chmod 644 /etc/mail/sendmail.cf
    sudo /etc/init.d/sendmail restart
