---
layout: post
title: "Containerized Nginx reverse-proxy and Let's Encrypt certificates"
tags: ["Nginx", "Let's Encrypt", "HTTP3", "Podman"]
featured_image_thumbnail: assets/images/posts/letsencrypt/switch_thumbnail.jpg
featured_image: assets/images/posts/letsencrypt/switch.jpg
featured: false
hidden: false
---

When exposing services running on your home server to the Internet, you only allow encrypted connections. I'm exposing Home Assistant, Jellyfin and some other things via a containerized Nginx with HTTP3 and I use Let's Encrypt to supply certificates.

With this setup, you have an A+ rating at Qualys.

<!--more-->

## What's in this guide?

When you follow this guide you will have:

- Nginx set up as a reverse proxy
- Nginx running in a container
- HTTP3 support in Nginx
- TLS provided by Let's Encrypt certificates
- Certificates installed by containerized Certbot
- Automatic renewal of certificates using a systemd timer

Prerequisites:
- A container engine like Podman or Docker. I'm using Podman on an RHEL system (with SELinux enforced)
- Podman-compose or docker-compose

Port forwarding and firewall management are out of the scope of this guide. For HTTP3 you will need to open port 80/TCP (only to redirect to port 443) and port 443 (UDP and TCP).

## HTTP3 and Nginx

[HTTP3](https://en.wikipedia.org/wiki/HTTP/3) may be officially released as a standard, in Nginx it has not yet made it into the stable release.
Nginx does, however, have the code ready for those brave enough to try. And we sure are brave, aren't we?

F5, the company behind Nginx even provides a ready-to-use Dockerfile so you can build Nginx yourself. This also comes in handy if you want to add your own modules.

The source of the `Containerfile` is found on the Nginx website: [https://www.nginx.com/blog/our-roadmap-quic-http-3-support-nginx/](https://www.nginx.com/blog/our-roadmap-quic-http-3-support-nginx/)

Copy and paste the code from the blog entry and confirm it builds.

```
$ podman build -t nginx-http3 .
```

## Directory structure and files

Because I'm going to run an Nginx and Certbot container separately, I have to take care of the directory structure. I also want the Nginx logs to persist, outside of the container, so I can run log-parsing services like fail2ban.

```
$ home - nginx
           |
           + container-compose.yml
           + Containerfile
           +- conf
           |    |
           |    + nginx.conf
           |    + http3.conf
           |    + letsencrypt-acme-challenge.conf
           |    +- conf.d
           |         |
           |         + sub.domain.tld.conf
           +- data
           |   |
           |   +- letsencrypt
           |   +- www
           +- log
               |
               +- letsencrypt
               +- nginx
                    |
                    + access.log
                    + error.log
```

(directories have a dash before their name)

The Nginx log files are already created. I noticed that Nginx sometimes has problems with creating the files on startup.

`~/nginx/container-compose.yml`:

```
version: "3.9"
services:
  nginx-http3:
    build: ./
    container_name: nginx
    #restart: unless-stopped
    volumes:
      - ~/nginx/conf:/etc/nginx:Z,ro
      - ~/nginx/log:/var/log:z
      - ~/nginx/data/www:/srv:z,ro
      - ~/nginx/data/letsencrypt:/letsencrypt:z,ro
    network_mode: host
    #ports:
    #  - "80:80"
    #  - "443:443/tcp"
    #  - "443:443/udp"
    #networks:
    #  - nginx_backend

#networks:
#  nginx_backend:
#    name: nginx_backend
```

A few words of explanation here:

- The Nginx container uses host networking mode. This is to have the real client's IP address available for logging purposes. There is [a new network driver](https://github.com/containers/podman/pull/16141) coming to Podman but it hasn't made it to the standard RHEL repos yet.
- Because we use the host network, you cannot connect to a second Podman network. Backend services will have to expose their port on the post to be reachable. Note that their port should still be firewalled.
- Volumes are mapped as we created them in our home directory. They all are read-only except the log directory. Don't forget the SELinux flags!

`~/nginx/Containerfile`:

```
FROM nginx AS build

WORKDIR /src
RUN apt-get update && apt-get install -y git gcc make autoconf libtool perl
RUN git clone -b v3.6.1 https://github.com/libressl-portable/portable.git libressl && \
    cd libressl && \
    ./autogen.sh && \
    ./configure && \
    make check && \
    make install

RUN apt-get install -y mercurial libperl-dev libpcre3-dev zlib1g-dev libxslt1-dev libgd-ocaml-dev libgeoip-dev
RUN hg clone -b quic https://hg.nginx.org/nginx-quic && \
    cd nginx-quic && \
    auto/configure `nginx -V 2>&1 | sed "s/ \-\-/ \\\ \n\t--/g" | grep "\-\-" | grep -ve opt= -e param= -e build=` \
      --with-http_v3_module --with-stream_quic_module \
      --with-debug --build=nginx-quic \
      --with-cc-opt="-I/src/libressl/build/include" --with-ld-opt="-L/src/libressl/build/lib" --with-ld-opt="-static" && \
    make

FROM nginx
COPY --from=build /src/nginx-quic/objs/nginx /usr/sbin
RUN /usr/sbin/nginx
EXPOSE 80 443 443/udp
```

Mind that HTTP3 uses UDP on port 443. You can leave out the `--with-debug` option if you're not interested in debugging. Because it's still an experimental build, I'm leaving it.

`~/nginx/conf/nginx.conf`

```
worker_processes  4;

error_log  /var/log/nginx/error.log  warn;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    log_format quic '$remote_addr - $remote_user [$time_local] '
                      '"$request" $status $body_bytes_sent '
                      '"$http_referer" "$http_user_agent" "$http3"';

    access_log  /var/log/nginx/access.log  quic;

    include /etc/nginx/conf.d/*.conf;
}
```

`~/nginx/conf/http3.conf`

```
ssl_protocols TLSv1.2 TLSv1.3; # TLSv1.3 necessary for http3
quic_retry on;
ssl_early_data on;

#ssl_prefer_server_ciphers on; # Let the client choose, as of 2022-05 these ciphers are all still secure.
ssl_dhparam /etc/nginx/dhparams4096.pem; # generate with 'openssl dhparam -out dhparam.pem 4096'
ssl_ciphers TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
ssl_ecdh_curve X25519:prime256v1:secp384r1;

ssl_session_cache shared:SSL:5m;
ssl_session_timeout 1h;
ssl_session_tickets off;
ssl_buffer_size 4k; # This is for performance rather than security, the optimal value depends on each site.
                                # 16k default, 4k is a good first guess and likely more performant.

ssl_stapling on;      # As of 2022-05 this version of nginx dosen't support ssl-stapling, but it might be in the future.
ssl_stapling_verify on;
resolver 192.168.130.10 8.8.8.8 valid=300s; # Use whichever resolvers you'd like, these are Cloudflare's and is one of the fastest DNS resolvers.
resolver_timeout 5s;

proxy_request_buffering off;

add_header alt-svc 'h3=":443"; ma=86400'; # Absolutely necessary header. This informs the client that HTTP/3 is available.
add_header Strict-Transport-Security max-age=15768000; # Optional but good, client should always try to use HTTPS, even for initial requests.

gzip off; #https://en.wikipedia.org/wiki/BREACH
```

Mind that certificates will be specified by the per-server configuration file

`letsencrypt-acme-challenge.conf`

```
location ^~ /.well-known/acme-challenge/ {
    default_type "text/plain";
    root /srv/letsencrypt;
}
location = /.well-known/acme-challenge/ {
    return 404;
}
```

`~/nginx/conf/conf.d/sub.domain.tld`

```
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    listen 80;
    #listen [::]:80;
    server_name sub.domain.tld;

    # Uncomment to redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    listen 443 http3
    listen [::]:443 ssl http2;
    listen [::]:443 http3
    server_name sub.domain.tld;

    # use a variable to store the upstream proxy
    # in this example we are using a hostname which is resolved via DNS
    # (if you aren't using DNS remove the resolver line and change the variable to point to an IP address e.g `set $jellyfin 127.0.0.1`)
    set $backend_service backend_service;
    #resolver 127.0.0.1 valid=30;

    include /etc/nginx/http3.conf;

    ssl_certificate /letsencrypt/live/sub.domain.tld/fullchain.pem;
    ssl_certificate_key /letsencrypt/live/sub.domain.tld/privkey.pem;
    ssl_trusted_certificate /letsencrypt/live/sub.domain.tld/chain.pem;

    # Security / XSS Mitigation Headers
    # NOTE: X-Frame-Options may cause issues with the webOS app
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options "nosniff";

    # Content Security Policy
    # See: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
    # Enforces https content and restricts JS/CSS to origin
    # External Javascript (such as cast_sender.js for Chromecast) must be whitelisted.
    # NOTE: The default CSP headers may cause issues with the webOS app
    #add_header Content-Security-Policy "default-src https: data: blob: http://image.tmdb.org; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' https://www.gstatic.com/cv/js/sender/v1/cast_sender.js https://www.gstatic.com/eureka/clank/95/cast_sender.js https://www.gstatic.com/eureka/clank/96/cast_sender.js https://www.gstatic.com/eureka/clank/97/cast_sender.js https://www.youtube.com blob:; worker-src 'self' blob:; connect-src 'self'; object-src 'none'; frame-ancestors 'self'";

    # enable Letsencrypt validation
    include /etc/nginx/letsencrypt-acme-challenge.conf;

    proxy_buffering off;

    location / {
        proxy_pass http://$backend_service:port;
        proxy_set_header Host $host;
        proxy_redirect http:// https://;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }
}
```

The per-service configuration files will be different depending on the actual backend service. This example is taken from my Home Assistant setup. Obviously, the domain name has to be changed but also this line might need a change:

`set $backend_service backend_service;`

It puts the name of the host where the service is reachable into a variable. Since Nginx is running in the host network stack, you might want to point it to `localhost` or `127.0.0.1`.

Please consult the documentation of the service you want to make available.

## First run

If you start the Nginx container now, it will fail. This is because the certificates are not yet available and the server will throw an error. To overcome this, you can run Certbot in standalone mode.

Make sure port 80 is not firewalled on your server. Also, check that your router is properly forwarding the port.

Try out with

```
$ podman run -it --rm -p 80:80 -v ~/nginx/data/letsencrypt:/etc/letsencrypt:z -v ~/nginx/log:/var/log:z certbot/certbot certonly --standalone --staging --dry-run --key-type ecdsa --rsa-key-size 4096 -d sub.domain.tld
```

And do it for real with

```
podman run -it --rm -p 80:80 -v ~/nginx/data/letsencrypt:/etc/letsencrypt:z -v ~/nginx/log:/var/log:z certbot/certbot certonly --standalone --key-type ecdsa --rsa-key-size 4096 -d sub.domain.tld
```

Certbot will ask you a few questions such as your e-mail address and if you could agree with their terms. I assume you do. This info will be stored so you can automate the command when renewing. You can provide multiple domains by adding extra `-d domain` arguments.

Now that you have the certificates, you can start Nginx:

```
[nginx] $ podman-compose --no-pod up -d
```

## Automatically start Nginx

Podman provides a simple way to generate systemd service files. So we make use of this functionality to auto-start Nginx when booting the server:

Make sure the Nginx container is still running.

Go to ~/.config/systemd/user

```
[~/.config/systemd/user] $ podman generate systemd --new --name --files nginx
[~/.config/systemd/user] $ systemctl --user daemon-reload
[~/.config/systemd/user] $ systemctl --user enable container-nginx.service
[~/.config/systemd/user] $ systemctl --user start container-nginx.service
```

## Automatic renewal

Certbot is not integrated into the Nginx container so we must run it separately. This is quite straightforward with Systemd timers.

We're still in the `~/.config/systemd/user` directory and create two files.

`renew-certificates.service`

```
[Unit]
Description=Renew Let's Encrypt certificates
After=container-nginx.service

[Service]
Type=oneshot
ExecStart=podman run -it --rm -v %h/nginx/data/letsencrypt:/etc/letsencrypt:z -v %h/nginx/data/www/letsencrypt:/srv/letsencrypt:z -v %h/nginx/log:/var/log:z certbot/certbot renew --webroot -w /srv/letsencrypt
ExecStart=podman exec nginx nginx -s reload

[Install]
WantedBy=default.target
```

There are two commands in this unit file. The first command checks for renewal. The second command reloads Nginx inside its container so new certificates are picked up. Mind that changes in configuration files are also picked up. If you made changes that contain errors, neither the changes nor new certificates are activated.

`renew-certificates.timer`

```
[Unit]
Description=Renew Let's Encrypt certificates daily at 01:30

[Timer]
OnCalendar=*-*-* 01:30:00

[Install]
WantedBy=timers.target
```

Enable the timer:

```
$ systemctl --user daemon-reload
$ systemctl --user enable renew-certificates.timer
```

Done! Now you have a running Nginx reverse proxy with Let's Encrypt certificates and automatic renewal.
At the time of writing, this setup has an A+ rating at [Qualys SSL Labs](https://www.ssllabs.com/ssltest/).

---

Switch Photo by <a href="https://unsplash.com/@thomasjsn?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Thomas Jensen</a> on <a href="https://unsplash.com/s/photos/network?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>
