---
layout: post
title: 'Certificate management'
tags: ["OpenSSL", "self-signed", "certificates"]
featured_image_thumbnail: assets/images/posts/certman/lock_thumbnail.jpg
featured_image: assets/images/posts/certman/lock.jpg
featured: false
hidden: false
---

OpenSSL and certificate management are a black box to me. So I thought I'd better write down how I managed to create my certificates. I followed this tutorial: [https://pki-tutorial.readthedocs.io/en/latest/index.html](https://pki-tutorial.readthedocs.io/en/latest/index.html).

<!--more-->

There are a lot of OpenSSL tutorials online to create your self-signed certificates. And in fact, when you have a public-facing service you'd better stick to trusted platforms like [Let's Encrypt](https://www.letsencrypt.org). For our internal services, I'm trustworthy enough to have my own certificate authority. I want to create certificates for my OpenVPN server, my Mosquitto broker and the Cockpit control panel.

DISCLAIMER: The following steps are from [https://pki-tutorial.readthedocs.io/en/latest/index.html](https://pki-tutorial.readthedocs.io/en/latest/index.html). They are more elaborate than most other guides but the steps are clear and understandable and you learn how the chain of trust works.

ATTENTION: Private keys are to be kept strictly private so you don't want the key files to be exposed to the Internet. It is best to set up the key infrastructure on a computer that is not connected to the Internet to prevent any unauthorized access. Alternatively, instead of generating the PKI in your home directory, you can put all the files on removable media like a USB stick and store it somewhere safe.

## Preparation

You probably already have everything installed on your system. I'm creating the certificates on my Lubuntu laptop and afterwards I'll transfer them to the server.
It works equally fine in WSL or WSL2 on Windows.

In case you haven't installed anything yet:

```
$ sudo apt update && sudo apt install openssl
```

Now, prepare the config files and directory layout:

```
$ mkdir ~/keys
$ cd ~/keys
$ mkdir -p ca/root-ca/private ca/root-ca/db crl certs etc
$ chmod 700 ca/root-ca/private
$ touch etc/root-ca.conf etc/tls-ca.conf etc/tls-server.conf etc/tls-client.conf
```

File `etc/root-ca.conf`

```
# ACME Root CA

[ default ]
ca                      = root-ca                   # CA name
dir                     = .                         # Top dir
base_url                = http://www.acme.com/ca    # CA base URL
aia_url                 = $base_url/$ca.cer         # CA certificate URL
crl_url                 = $base_url/$ca.crl         # CRL distribution point
name_opt                = multiline,-esc_msb,utf8   # Display UTF-8 characters

# CA certificate request

[ req ]
default_bits            = 4096                  # RSA key size
encrypt_key             = yes                   # Protect private key
default_md              = sha256                # MD to use
utf8                    = yes                   # Input is UTF-8
string_mask             = utf8only              # Emit UTF-8 strings
prompt                  = no                    # Don't prompt for DN
distinguished_name      = ca_dn                 # DN section
req_extensions          = ca_reqext             # Desired extensions

[ ca_dn ]
countryName             = "US"
organizationName        = "Acme"
organizationalUnitName  = "Acme Certificate Authority"
commonName              = "Acme Root CA"

[ ca_reqext ]
keyUsage                = critical,keyCertSign,cRLSign
basicConstraints        = critical,CA:true
subjectKeyIdentifier    = hash

# CA operational settings

[ ca ]
default_ca              = root_ca               # The default CA section

[ root_ca ]
certificate             = $dir/ca/$ca.crt       # The CA cert
private_key             = $dir/ca/$ca/private/$ca.key # CA private key
new_certs_dir           = $dir/ca/$ca           # Certificate archive
serial                  = $dir/ca/$ca/db/$ca.crt.srl # Serial number file
crlnumber               = $dir/ca/$ca/db/$ca.crl.srl # CRL number file
database                = $dir/ca/$ca/db/$ca.db # Index file
unique_subject          = no                    # Require unique subject
default_days            = 3652                  # How long to certify for
default_md              = sha256                # MD to use
policy                  = match_pol             # Default naming policy
email_in_dn             = no                    # Add email to cert DN
preserve                = no                    # Keep passed DN ordering
name_opt                = $name_opt             # Subject DN display options
cert_opt                = ca_default            # Certificate display options
copy_extensions         = none                  # Copy extensions from CSR
x509_extensions         = signing_ca_ext        # Default cert extensions
default_crl_days        = 365                   # How long before next CRL
crl_extensions          = crl_ext               # CRL extensions

[ match_pol ]
countryName             = match                 # Must match 'US'
stateOrProvinceName     = optional              # Included if present
localityName            = optional              # Included if present
organizationName        = match                 # Must match 'Acme'
organizationalUnitName  = supplied              # Must be present
commonName              = supplied              # Must be present

[ any_pol ]
domainComponent         = optional
countryName             = optional
stateOrProvinceName     = optional
localityName            = optional
organizationName        = optional
organizationalUnitName  = optional
commonName              = optional
emailAddress            = optional

# Extensions

[ root_ca_ext ]
keyUsage                = critical,keyCertSign,cRLSign
basicConstraints        = critical,CA:true
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always

[ signing_ca_ext ]
keyUsage                = critical,keyCertSign,cRLSign
basicConstraints        = critical,CA:true,pathlen:0
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always
authorityInfoAccess     = @issuer_info
crlDistributionPoints   = @crl_info

[ crl_ext ]
authorityKeyIdentifier  = keyid:always
authorityInfoAccess     = @issuer_info

[ issuer_info ]
caIssuers;URI.0         = $aia_url

[ crl_info ]
URI.0                   = $crl_url
```

In file `etc/tls-ca.conf`

```
# Acme TLS CA

[ default ]
ca                      = tls-ca                # CA name
dir                     = .                     # Top dir
base_url                = http://www.acme.com/ca    # CA base URL
aia_url                 = $base_url/$ca.cer     # CA certificate URL
crl_url                 = $base_url/$ca.crl     # CRL distribution point
name_opt                = multiline,-esc_msb,utf8 # Display UTF-8 characters

# CA certificate request

[ req ]
default_bits            = 4096                  # RSA key size
encrypt_key             = yes                   # Protect private key
default_md              = sha256                # MD to use
utf8                    = yes                   # Input is UTF-8
string_mask             = utf8only              # Emit UTF-8 strings
prompt                  = no                    # Don't prompt for DN
distinguished_name      = ca_dn                 # DN section
req_extensions          = ca_reqext             # Desired extensions

[ ca_dn ]
countryName             = "US"
organizationName        = "Acme"
organizationalUnitName  = "Acme Certificate Authority"
commonName              = "Acme TLS CA"

[ ca_reqext ]
keyUsage                = critical,keyCertSign,cRLSign
basicConstraints        = critical,CA:true,pathlen:0
subjectKeyIdentifier    = hash

# CA operational settings

[ ca ]
default_ca              = tls_ca                # The default CA section

[ tls_ca ]
certificate             = $dir/ca/$ca.crt       # The CA cert
private_key             = $dir/ca/$ca/private/$ca.key # CA private key
new_certs_dir           = $dir/ca/$ca           # Certificate archive
serial                  = $dir/ca/$ca/db/$ca.crt.srl # Serial number file
crlnumber               = $dir/ca/$ca/db/$ca.crl.srl # CRL number file
database                = $dir/ca/$ca/db/$ca.db # Index file
unique_subject          = no                    # Require unique subject
default_days            = 730                   # How long to certify for
default_md              = sha256                # MD to use
policy                  = match_pol             # Default naming policy
email_in_dn             = no                    # Add email to cert DN
preserve                = no                    # Keep passed DN ordering
name_opt                = $name_opt             # Subject DN display options
cert_opt                = ca_default            # Certificate display options
copy_extensions         = copy                  # Copy extensions from CSR
x509_extensions         = server_ext            # Default cert extensions
default_crl_days        = 1                     # How long before next CRL
crl_extensions          = crl_ext               # CRL extensions

[ match_pol ]
countryName             = match                 # Must match 'US'
stateOrProvinceName     = optional              # Included if present
localityName            = optional              # Included if present
organizationName        = match                 # Must match 'Acme'
organizationalUnitName  = supplied              # Must be present
commonName              = supplied              # Must be present

[ extern_pol ]
countryName             = supplied              # Must be present
stateOrProvinceName     = optional              # Included if present
localityName            = optional              # Included if present
organizationName        = supplied              # Must be present
organizationalUnitName  = supplied              # Must be present
commonName              = supplied              # Must be present

[ any_pol ]
domainComponent         = optional
countryName             = optional
stateOrProvinceName     = optional
localityName            = optional
organizationName        = optional
organizationalUnitName  = optional
commonName              = optional
emailAddress            = optional

# Extensions

[ server_ext ]
keyUsage                = critical,digitalSignature,keyEncipherment
basicConstraints        = CA:false
extendedKeyUsage        = serverAuth,clientAuth
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always
authorityInfoAccess     = @issuer_info
crlDistributionPoints   = @crl_info

[ client_ext ]
keyUsage                = critical,digitalSignature
basicConstraints        = CA:false
extendedKeyUsage        = clientAuth
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always
authorityInfoAccess     = @issuer_info
crlDistributionPoints   = @crl_info

[ crl_ext ]
authorityKeyIdentifier  = keyid:always
authorityInfoAccess     = @issuer_info

[ issuer_info ]
caIssuers;URI.0         = $aia_url

[ crl_info ]
URI.0                   = $crl_url
```

In file `etc/tls-server.conf`

```
# TLS server certificate request

[ default ]
SAN                     = DNS:acme.com      # Default value

[ req ]
default_bits            = 4096                  # RSA key size
encrypt_key             = no                    # Protect private key
default_md              = sha256                # MD to use
utf8                    = yes                   # Input is UTF-8
string_mask             = utf8only              # Emit UTF-8 strings
prompt                  = yes                   # Prompt for DN
distinguished_name      = server_dn             # DN template
req_extensions          = server_reqext         # Desired extensions

[ server_dn ]
countryName             = "1. Country Name (2 letters) (eg, US)       "
countryName_max         = 2
stateOrProvinceName     = "2. State or Province Name   (eg, region)   "
localityName            = "3. Locality Name            (eg, city)     "
organizationName        = "4. Organization Name        (eg, company)  "
organizationalUnitName  = "5. Organizational Unit Name (eg, section)  "
commonName              = "6. Common Name              (eg, FQDN)     "
commonName_max          = 64

[ server_reqext ]
keyUsage                = critical,digitalSignature,keyEncipherment
extendedKeyUsage        = serverAuth,clientAuth
subjectKeyIdentifier    = hash
subjectAltName          = $ENV::SAN
```

In file `etc/tls-client.conf`

```
# TLS client certificate request

[ req ]
default_bits            = 4096                  # RSA key size
encrypt_key             = yes                   # Protect private key
default_md              = sha256                # MD to use
utf8                    = yes                   # Input is UTF-8
string_mask             = utf8only              # Emit UTF-8 strings
prompt                  = yes                   # Prompt for DN
distinguished_name      = client_dn             # DN template
req_extensions          = client_reqext         # Desired extensions

[ client_dn ]
countryName             = "1. Country Name (2 letters) (eg, US)       "
countryName_max         = 2
stateOrProvinceName     = "2. State or Province Name   (eg, region)   "
localityName            = "3. Locality Name            (eg, city)     "
organizationName        = "4. Organization Name        (eg, company)  "
organizationalUnitName  = "5. Organizational Unit Name (eg, section)  "
commonName              = "6. Common Name              (eg, full name)"
commonName_max          = 64
emailAddress            = "7. Email Address            (eg, name@fqdn)"
emailAddress_max        = 40

[ client_reqext ]
keyUsage                = critical,digitalSignature
extendedKeyUsage        = clientAuth
subjectKeyIdentifier    = hash
subjectAltName          = email:move
```

## Setup CA

A certificate authority takes care of signing certificates and keeping track which certificates it has signed but also which ones it has revoked. We will set up this infrastructure.

```
$ cp /dev/null ca/root-ca/db/root-ca.db
$ cp /dev/null ca/root-ca/db/root-ca.db.attr
$ echo 01 > ca/root-ca/db/root-ca.crt.srl
$ echo 01 > ca/root-ca/db/root-ca.crl.srl
```

### Create a CA request

```
$ openssl req -new \
    -config etc/root-ca.conf \
    -out ca/root-ca.csr \
    -keyout ca/root-ca/private/root-ca.key
```

When asked for a passphrase, enter your password. The command uses the info from the `root-ca.conf` file. The result is a private key and a CSR (certificate signing request).

### Create a CA certificate

```
$ openssl ca -selfsign \
    -config etc/root-ca.conf \
    -in ca/root-ca.csr \
    -out ca/root-ca.crt \
    -extensions root_ca_ext
```

We now have a self-signed root CA. This CA is the origin of trust in your public key infrastructure. To create "usable" certificates, you also need to have signing certificates. These are created in the next part. Notice the `-selfsign` option.

#### CRL

The root CA can also revoke certificates. Hence we have to create the certificate revoke list.

```
$ openssl ca -gencrl \
    -config etc/root-ca.conf \
    -out crl/root-ca.crl
```

### Create TLS server CA

The TLS-server CA is an intermediate certificate that will be used to sign all TLS certificates. If that doesn't make sense think of this: Would the president sign all the passports of his citizens by himself? Probably not. The president does however grant certain people the right to sign on his behalf. That's what we're also doing by creating a TLS server CA.

First, create the directories to store the files.

```
$ mkdir -p ca/tls-ca/private ca/tls-ca/db
$ chmod 700 ca/tls-ca/private
```

Create the database:

```
$ cp /dev/null ca/tls-ca/db/tls-ca.db
$ cp /dev/null ca/tls-ca/db/tls-ca.db.attr
$ echo 01 > ca/tls-ca/db/tls-ca.crt.srl
$ echo 01 > ca/tls-ca/db/tls-ca.crl.srl
```

### Create a CA request

```
$ openssl req -new \
    -config etc/tls-ca.conf \
    -out ca/tls-ca.csr \
    -keyout ca/tls-ca/private/tls-ca.key
```

As a regular CA, this creates the private key and a CSR. Also, give the key a password to protect from unauthorized use.

### Create CA

```
$ openssl ca \
    -config etc/root-ca.conf \
    -in ca/tls-ca.csr \
    -out ca/tls-ca.crt \
    -extensions signing_ca_ext
```

The root CA validates and signs the request, creating the TLS server CA.

It all starts coming together when looking at the parameters for the command: We create a ca (`openssl ca -out ca/tls-ca.crt`) using the CRS (-in ca/tls-ca.csr). The outcome is a signing CA (-extension signing_ca_ext). Mind that we here use the root CA's config file. After all, the request was made by the TLS server CA's config and now the work has to be done by the root.

#### CRL

Also here, create a certificate revoke list.

```
openssl ca -gencrl \
    -config etc/tls-ca.conf \
    -out crl/tls-ca.crl
```

#### PEM bundle

The PEM bundle is a certificate chain.

```
$ cat ca/tls-ca.crt ca/root-ca.crt > \
    ca/tls-ca-chain.pem
```

If you look at the contents of the file, it is nothing more than the root certificate and the tls-server certificate pasted after each other.

## Issuing certificates

Our infrastructure is ready to create certificates that will be deployed to our servers.

Let's create a certificate for our Cockpit control panel. The control panel is reachable on "cpanel.acme.com"[^1].

[^1]: The control panel is only reachable from the LAN. Its domain name is defined in the router's dnsmasq service.

Our infrastructure is completely ready now. When we want to have a certificate for one of our services we create a request and the authority signs it. Think of it like these real-world analogies:

- bank notes backed up by a central bank
- passports signed by a country's representative
- contracts notarized by a notary

### Create a TLS server request

```
$ SAN=DNS:cpanel.acme.com \
openssl req -new \
    -config etc/tls-server.conf \
    -out certs/cpanel.acme.com.csr \
    -keyout certs/cpanel.acme.com.key
```

Mind the environment variable we set first. We also don't set a passphrase.

### Create the TLS certificate

```
$ openssl ca \
    -config etc/tls-ca.conf \
    -in certs/cpanel.acme.com.csr \
    -out certs/cpanel.acme.com.crt \
    -extensions server_ext
```

If this is your first certificate, a copy will be stored under `ca/tls-ca/01.pem`.

Which files do you need in your actual service?

- tls-ca.crt: the public root certificate as the basis of trust
- cpanel.acme.com.crt: the public server certificate which has the FQDN incorporated
- cpanel.acme.com.key: the private key to be able to decrypt

#### Copy to cockpit

Cockpit [requires](https://cockpit-project.org/guide/228/https.html) to have the server certificate and the intermediate certificate in the same file.
Although not mentioned in the docs, I also had to copy the private key into the same file to get it working. Also, notice the file extension change 
when moving the certificate chain to Cockpit: `.crt` becomes `.cert`.

```
$ cat certs/cpanel.acme.com.crt ca/tls-ca.crt certs/cpanel.acme.com.key > certs/cpanel.acme.com-chain.crt
```

Copy `certs/cpanel.acme.com-chain.cert` to your server and place it in Cockpit's config directory.

```
$ sudo mv cpanel.acme.com-chain.crt /etc/cockpit/ws-certs.d/cpanel.acme.com.cert
```

Give the files the proper ownership and permissions:

```
$ sudo chown root:cockpit-ws /etc/cockpit/ws-certs.d/cpanel.acme.com.cert
$ sudo chmod 640 /etc/cockpit/ws-certs.d/cpanel.acme.com.cert
```

## Revoking certificates

Should you want to revoke a certificate (the private key has been compromised) before its expiration date, you can add it to the CRL (certificate revoke list). You have to know the id-number of the certificate though. If you didn't remember, look into the signing-db: `~/keys/ca/signing-ca/db/signing-ca.db`.

### Revoke a certificate

```
openssl ca \
    -config etc/signing-ca.conf \
    -revoke ca/signing-ca/01.pem \
    -crl_reason superseded
```

The compromised certificate is marked 'revoked' and will be included in new CRLs the CA issues.

### Create a CRL

```
openssl ca -gencrl \
    -config etc/signing-ca.conf \
    -out crl/signing-ca.crl
```

## Adding your own certificates your system

You've set up your own public key infrastructure and certificate authority. However, your browser (and other programs) doesn't know about this.

To have your computer trust the root certificate, copy it to `/usr/local/share/ca-certificates/`.

```
$ sudo cp ~/keys/ca/root-ca.crt /usr/local/share/ca-certificates/
$ sudo update-ca-certificates
```

If you use Firefox as I do, you will notice that your cockpit login page still shows a warning. Firefox does not take your system's certificates as a trusted store. To solve this, head over to [this post](/posts/2-Firefox-and-self-signed-certificates).

You'll then have this screen:

![trusted cockpit](/assets/images/posts/certman/cockpit.jpg)

It still says the certificate is not trusted by Mozilla, but since you trust it Firefox won't make a fuss about it.

---

<small>Lock photo by <a href="https://pixabay.com/users/pasja1000-6355831/?utm_source=link-attribution&amp;utm_medium=referral&amp;utm_campaign=image&amp;utm_content=3745490">pasja1000</a> from <a href="https://pixabay.com/?utm_source=link-attribution&amp;utm_medium=referral&amp;utm_campaign=image&amp;utm_content=3745490">Pixabay</a></small>
