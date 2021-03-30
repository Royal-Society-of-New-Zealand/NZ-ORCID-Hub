Server Certifcates
------------------

This document gives some pointers, hints and tips on how to create and setup server certificats.

Instaall getssl and setup certiicates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Install **getssl** following the instruction at https://github.com/srvrco/getssl
#. Create your domain configuration, eg: `./getssl -c orcidhub.org.nz`
#. Modify the configuration, eg, **~/.getssl/orcidhub.org.nz/getssl.cfg** so that the key and the certificate chain gets placed in the right place:

   .. code-block:: bash
  
    CA="https://acme-v02.api.letsencrypt.org"
    
    ACL=('/home/ec2-user/.well-known/acme-challenge')
    
    DOMAIN_CERT_LOCATION="/home/ec2-user/.keys/orcidhub.org.nz.crt" # this is domain cert
    DOMAIN_KEY_LOCATION="/home/ec2-user/.keys/prod-server.key" # this is domain key
    CA_CERT_LOCATION="/home/ec2-user/.keys/CA.crt" # this is CA cert
    DOMAIN_CHAIN_LOCATION="/home/ec2-user/.keys/prod-server.crt" # this is the domain cert and CA cert
    
    # The command needed to reload apache / nginx or whatever you use
    RELOAD_CMD="docker-compose restart app; sleep 5"

#. Request a certifcate and deploy it: `./getssl orcidhub.org.nz`
#. Add automatic update to your crontab, eg:

   .. code-block:: crontab
  
    23 42 * * * /home/ec2-user/getssl -u -a -q


Need more help
______________

For more guidance on troubleshooting docker see :ref:`Troubleshooting <troubleshooting>`
