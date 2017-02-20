#!/bin/bash
DOMAIN="$1"
if [ -z "$DOMAIN" ]; then
    echo "Usage: $(basename $0) <domain>"
    exit 11
fi

fail_if_error() {
  [ $1 != 0 ] && {
    exit 10
    unset PASSPHRASE
  }
}
  export PASSPHRASE=$(head -c 64 /dev/urandom  | base64)

  subj="
C=NZ
ST=Auckland
O=The University of Auckland
localityName=Auckland
commonName=$DOMAIN
organizationalUnitName=IT Strategy, Policy, and Planning
emailAddress=nz-orcid-hub-gg@aucklanduni.ac.nz
"

openssl genrsa -des3 -out $DOMAIN.key -passout env:PASSPHRASE 2048
fail_if_error $?

openssl req \
    -new \
    -batch \
    -subj "$(echo -n "$subj" | tr "\n" "/")" \
    -key $DOMAIN.key \
    -out $DOMAIN.csr \
    -passin env:PASSPHRASE 
fail_if_error $?
cp $DOMAIN.key $DOMAIN.key.org
fail_if_error $?

# Strip the passphrase from our RSA-key to not get prompted when Apache (or any other webserver) starts:
openssl rsa -in $DOMAIN.key.org -out $DOMAIN.key -passin env:PASSPHRASE
fail_if_error $?

# Create the certificate file:
openssl x509 -req -days 1365 -in $DOMAIN.csr -signkey $DOMAIN.key -out $DOMAIN.crt
fail_if_error $?

