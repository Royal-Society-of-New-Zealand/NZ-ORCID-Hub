.. role:: bash(code)
   :language: bash

Shibboleth installation and SP Creation
=======================================

#. First install Shibboleth. For Ubuntu machine follow the below steps::

    sudo apt-get install shibboleth-sp2-schemas libapache2-mod-shib2
    sudo apt-get update
    sudo a2enmod shib2
    sudo service apache2 restart
#. Modify /etc/hosts file to allow url that you decided to go with, Basically add SP URL (your **sp.example.org**).
#. Follow documentation given at below link: https://tuakiri.ac.nz/confluence/display/Tuakiri/Installing+Shibboleth+2.x+SP+on+RedHat+based+Linux. Primarily the documentation given under `Federation Membership <https://tuakiri.ac.nz/confluence/display/Tuakiri/Installing+Shibboleth+2.x+SP+on+RedHat+based+Linux#InstallingShibboleth2.xSPonRedHatbasedLinux-FederationMembership>`_ and `Configuration <https://tuakiri.ac.nz/confluence/display/Tuakiri/Installing+Shibboleth+2.x+SP+on+RedHat+based+Linux#InstallingShibboleth2.xSPonRedHatbasedLinux-Configuration>`_ sections.
#. You also have to generate certificate to paste in New SP request, which can be done by below sample command::

      sudo /usr/sbin/shib-keygen -f -u ubuntu -g ubuntu -h ubuntu.auckland.ac.nz -e http://ubuntu.auckland.ac.nz/shibboleth
#. Steps to enable https (if in case your require). Command for generating self-singed certificate::

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout orcid.key -out orcid.crt

  then copy both the generated certificates into `/etc/apache2/sites-available` (you can copy that those to anywhere).
  Just have to update file with name `default-ssl.conf`::

    SSLCertificateFile /etc/apache2/sites-available/orcid.crt
    SSLCertificateKeyFile /etc/apache2/sites-available/orcid.key

    sudo a2enmod ssl
    sudo service apache2 restart
#. Enable proxy mode’s in apache2 mod-enable folder so that apache can talk to your local server:::

    a2enmod proxy_http and a2enmod proxy
#. Download the metadata signing certificate for the federation metadata into `/etc/shibboleth`:::

    wget https://directory.test.tuakiri.ac.nz/metadata/tuakiri-test-metadata-cert.pem -O /etc/shibboleth/tuakiri-test-metadata-cert.pem
#. The Shibboleth SP installation needs to be configured to map attributes received from the IdP - in `/etc/shibboleth/attribute-map.xml`. Change the attribute mapping definition by either editing the file and uncommenting attributes to be accepted, or replace the file with the recommended Tuakiri  attribute-map.xml file mapping all Tuakiri attributes (and optionally comment out those attributes not used by your SP).
#. Check if shibboleth 2.xml and apache 2.conf are configured correctly.
