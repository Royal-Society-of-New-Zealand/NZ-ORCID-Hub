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
    RELOAD_CMD="sudo service nginx restart; cd /home/ec2-user/dev; /usr/local/bin/docker-compose restart app; sleep 5"

#. If you are using **nginx**, add a location for the verification (/etc/nginx/nginx.conf), e.g.,:

   .. code-block:: nginx

    server {
            listen 80;
            server_name dev.orcidhub.org.nz;
            server_tokens off;
            root         /usr/share/nginx/html;

            location ^~ /.well-known/acme-challenge/ {
                    default_type "text/plain";
                    alias /home/ec2-user/.well-known/acme-challenge/;
            }

            # more_clear_headers Server;
            # more_set_headers 'Server: ORCID HUB';
            location / {
                    proxy_set_header        Host                    $host;
                    proxy_set_header        X-Real-IP               $remote_addr;
                    proxy_set_header        X-Forwarded-For         $proxy_add_x_forwarded_for;
                    proxy_set_header        X-Forwarded-Proto       $scheme;

                    proxy_redirect          off;
                    proxy_pass              http://172.33.0.99;
            }
    }
    server {
            listen 443 ssl;
            server_name dev.orcidhub.org.nz;
            server_tokens off;
            # more_clear_headers Server;
            # more_set_headers 'Server: ORCID HUB';

            ssl_certificate "/home/ec2-user/.getssl/dev.orcidhub.org.nz/fullchain.crt";
            ssl_certificate_key "/home/ec2-user/.getssl/dev.orcidhub.org.nz/dev.orcidhub.org.nz.key";

            # It is *strongly* recommended to generate unique DH parameters
            # Generate them with: openssl dhparam -out /etc/pki/nginx/dhparams.pem 2048
            #ssl_dhparam "/etc/pki/nginx/dhparams.pem";
            ssl_session_cache shared:SSL:1m;
            ssl_session_timeout  10m;
            ssl_protocols TLSv1.2 TLSv1.3;
            ssl_ciphers HIGH:SEED:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!RSAPSK:!aDH:!aECDH:!EDH-DSS-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA:!SRP;
            ssl_prefer_server_ciphers on;

            location / {
                    proxy_set_header        Host                    $host;
                    proxy_set_header        X-Real-IP               $remote_addr;
                    proxy_set_header        X-Forwarded-For         $proxy_add_x_forwarded_for;
                    proxy_set_header        X-Forwarded-Proto       $scheme;

                    proxy_redirect          off;
                    proxy_pass              https://172.33.0.99;
            }

            location /static {
                    root /home/ec2-user/dev/orcid_hub;
            }

            root         /usr/share/nginx/html;

            # Load configuration files for the default server block.
            include /etc/nginx/default.d/*.conf;

            error_page 404 /404.html;
                location = /40x.html {
            }

            error_page 500 502 503 504 /50x.html;
                location = /50x.html {
            }
    }

#. Request a certifcate and deploy it: `./getssl orcidhub.org.nz`
#. Add automatic update to your crontab, eg:

   .. code-block:: crontab
  
    42 23 * * * /home/ec2-user/getssl -u -a -q


Need more help
______________

For more guidance on troubleshooting docker see :ref:`Troubleshooting <troubleshooting>`
