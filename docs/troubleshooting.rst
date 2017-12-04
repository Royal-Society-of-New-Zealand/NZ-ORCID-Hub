.. _troubleshooting:

Troubleshooting
===============

Places to look up, if there is any issues:

-  docker logs, e.g., ``docker-compose logs app`` or
   ``docker-compose logs db``
-  application logs, e.g.,
   ``docker-compose exec app tail /var/log/httpd/test.orcidhub.org.nz-error.log``
-  Shibboleth logs in the container: ``/var/log/shibboleth/`` and
   ``/var/log/shibboleth-www/``
