---
layout: post
title: 'Self signed certificates in Windows 11'
tags: ["self-signed", "certificates", "Windows"]
featured_image_thumbnail: assets/images/posts/certswin/lock_thumbnail.jpg
featured_image: assets/images/posts/certswin/lock.jpg
featured: false
hidden: false
---

If you generate your own, self-signed root certificate Windows will complain about it because Windows doesn't trust you.
It is a good thing but it also is annoying. I'll show you how you can add your self-signed certificate to the certificate store so 
Windows 11 will trust you.

<!--more-->

After following [this guide](https://bert.emelis.net/posts/1-Certificate-management) you have your own, self-signed certificate. It's the `~/keys/ca/root-ca.crt` file. There are a few steps to follow but none of them involves a command line.

I created this guide on Windows 11, Windows 10 should also be OK.

### Open the Microsoft Management Console

Open the "start menu" and type `mmc`. Windows will search for a program that matches "mmc". Click the icon with the red toolbox. This will open the "Microsoft Management Console" which looks like this:

![Microsoft Management Console](/assets/images/posts/certswin/01-mmc.png)

### Add certificate manager

In the MMC, go to "File" >> "Add/Remove Snap-in". A new window will open.

![Microsoft Management Console](/assets/images/posts/certswin/02-snapin.png)

From the list of snap-ins, chose "Certificates" and click "Add" and follow the wizard:

Select "Computer account"
![Computer account](/assets/images/posts/certswin/03-compacc.png)

And next chose "Local computer" (no other choices are available.) and click "Finish".
![Local computer](/assets/images/posts/certswin/04-localcomp.png)

The snap-in is added, you can now click "OK
![OK](/assets/images/posts/certswin/05-ok.png)

### List certificates

![Certificates](/assets/images/posts/certswin/06-certificates.png)

You can now browse through the already available certificates. In the middle pane, double click "Certificates (local Computer)" and then "Trusted Root Certificate Authorities" and finally "Certificates". you'll see a list of all root CAs the computer trusts. We created our own root certificate authority so we will have to add ours here.

![Certificates open](/assets/images/posts/certswin/07-certificatesopen.png)

### Add our Root CA

With the list of certificates in the middle pane, right-click on "Certificates" in the left pane, go the "All Tasks" and "Import". Alternatively, you can select "Action" from the top menu bar, go to "All Tasks" and finally "Import". Follow the wizard.

![Import wizard 1](/assets/images/posts/certswin/08-import1.png)

Click "Next"

![Import wizard 2](/assets/images/posts/certswin/09-import2.png)

Browse to your root certificate (`keys/ca/root-ca.crt`) and click "Next".

![Import wizard 3](/assets/images/posts/certswin/10-import3.png)

Click "Next" again. The wizard already selected the right option for us to store the new certificate in the right store.

### Check and done!

Your certificate is now added to Windows. Your computer will now trust all the certificates that have been signed by this root certificate (and derivates). You might need to restart your browser for it to work with the newly added certificate.

---

<small>Notary sign image by <a href="https://pixabay.com/users/tama66-1032521/?utm_source=link-attribution&amp;utm_medium=referral&amp;utm_campaign=image&amp;utm_content=3617525">Peter H</a> from <a href="https://pixabay.com/?utm_source=link-attribution&amp;utm_medium=referral&amp;utm_campaign=image&amp;utm_content=3617525">Pixabay</a></small>
