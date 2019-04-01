#!/bin/bash
DOMAIN="$1"
if [ -z "$DOMAIN" ]; then
  echo "Usage: $(basename $0) <domain>"
  exit 11
fi
HOST="${DOMAIN%%.*}"

fail_if_error() {
  [ $1 != 0 ] && {
  exit 10
  unset PASSPHRASE
}
}

export PASSPHRASE=$(head -c 64 /dev/urandom  | base64)
subj="
"
ALTNAME=DNS:sp.$DOMAIN,DNS:sentry.$DOMAIN,DNS:api.$DOMAIN,URI:https://$DOMAIN/shibboleth,URI:https://$DOMAIN/Shibboleth.sso

SSLCNF=$(mktemp -t --suffix=.cfg)
cat >$SSLCNF <<EOF
[ CA_default ]
copy_extensions = copy
# OpenSSL configuration file for creating keypair
[req]
prompt=no
default_bits=3072
encrypt_key=no
default_md=sha256
distinguished_name=dn
# PrintableStrings only
string_mask=MASK:0002
x509_extensions=ext
[dn]
CN=$DOMAIN
C=NZ
ST=Auckland
O=The University of Auckland
L=Auckland
OU=IT Strategy, Policy, and Planning
emailAddress=nz-orcid-hub-gg@aucklanduni.ac.nz
[ext]
subjectAltName=$ALTNAME
subjectKeyIdentifier=hash
EOF

openssl genrsa -des3 -out $DOMAIN.key -passout env:PASSPHRASE 2048
fail_if_error $?

openssl req \
  -reqexts ext \
  -new \
  -batch \
  -config $SSLCNF \
  -key $DOMAIN.key \
  -out $DOMAIN.csr \
  -passin env:PASSPHRASE
fail_if_error $?
cp $DOMAIN.key $DOMAIN.key._
fail_if_error $?

# Strip the passphrase from our RSA-key to not get prompted when Apache (or any other webserver) starts:
openssl rsa -in $DOMAIN.key._ -out $HOST-server.key -passin env:PASSPHRASE
fail_if_error $?

# Create a self-signed certificate:
openssl x509 -req -days 1365 -in $DOMAIN.csr -signkey $HOST-server.key -out $HOST-server.crt -extensions ext -extfile $SSLCNF
fail_if_error $?

[ ! -d CSR ] && mkdir CSR
mv $DOMAIN.csr CSR/
