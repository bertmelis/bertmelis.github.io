---
layout: post
title: 'Self signed certificates in Firefox'
tags: OpenSSL self-signed Firefox
featured_image_thumbnail: assets/images/posts/firefox/notary_thumbnail.jpg
featured_image: assets/images/posts/firefox/notary.jpg
featured: false
hidden: false
---

Even if you have imported your self-signed root certificate to your system, Firefox won't use it. This has to be solved and I found a way.

<!--more-->

You could just add an exception for your website to Firefox, but it still shows the little warning icon in the address bar to show something's fishy.

Firefox uses it's own certificate store and doesn't care about the certificates the system trusts.

Luckily, [this answer on Ask Ubuntu](https://askubuntu.com/questions/244582/add-certificate-authorities-system-wide-on-firefox) has the path to the the answer. At the time of writing, the answer is not the accepted one, nor has it a high rating. But in my opinion it is the best one.

Even [Mozilla's website](https://support.mozilla.org/en-US/kb/setting-certificate-authorities-firefox) mentions it.

## Install the replacement lib

The trick is changing Firefoxes behaviour by using another certificate management library.

The replacement lib is to be found on [their website](https://p11-glue.github.io/p11-glue/p11-kit.html) or on their [Github page](https://github.com/p11-glue/p11-kit). The lib is also available on Ubuntu's repos.

```
$ sudo apt install p11-kit
```

On my system it was already installed. Yeah!

## Instruct Firefox to use the p11-kit

Unlike in the Ask Ubuntu answer (which is already a few years old), Firefox has to option to import security modules. So we'll include the P11-kit module to import the certificates from our system into Firefox.

### Open the settings page in Firefox

![Preferences](/assets/images/posts/firefox/1-preferences.jpg)

### Click "Privicy & Security" and scroll to "Security"

![Security settings](/assets/images/posts/firefox/2-security.jpg)

### View certificates

When you click "View Certificates" you'll get a list with all the trusted root certificates. Yours will not be in the list.

![Certificates list](/assets/images/posts/firefox/3-certificates.jpg)

Clost this screen.

### Add the custom module

Back in the settings screen, click "Security Devices". you'll get a screen with all the modules that take care of certificate management.

![Security devices](/assets/images/posts/firefox/4-load.jpg)

click "Load".

![Add kit](/assets/images/posts/firefox/5-kit.jpg)

Give the added module a sensible name and put in the path to the P11-kit module:

- Module name: P11 kit
- Module filename: /usr/lib/x86_64-linux-gnu/pkcs11/p11-kit-trust.so

Click "OK" The Device manager now shows the included module with it's certificate source.

![Added module](/assets/images/posts/firefox/6-added.jpg)

### Check certificates

when you click "View Certificates" in the settings screen, you can find your self-signed root certificate in the certificates list.

![Certificates](/assets/images/posts/firefox/7-certificates.jpg)

Unlike the answer on Ask Ubuntu, the added module is a setting that survives updates.

<small>Notary sign image by <a href="https://pixabay.com/users/tama66-1032521/?utm_source=link-attribution&amp;utm_medium=referral&amp;utm_campaign=image&amp;utm_content=3617525">Peter H</a> from <a href="https://pixabay.com/?utm_source=link-attribution&amp;utm_medium=referral&amp;utm_campaign=image&amp;utm_content=3617525">Pixabay</a></small>
