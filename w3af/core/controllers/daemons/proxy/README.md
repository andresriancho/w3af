# Generate new CA

openssl genrsa -out ca.key 2048
openssl req -new -x509 -key ca.key -out ca.crt