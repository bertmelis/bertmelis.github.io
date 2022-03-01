---
layout: post
title: 'Moved to Rocky Linux'
tags: Rocky Linux
featured_image_thumbnail: assets/images/posts/rocky/morskieoko_thumbnail.jpg
featured_image: assets/images/posts/rocky/morskieoko.jpg
featured: true
hidden: false
---

I've always been a big fan of Debian's ultra stability. But stability came with Debian's number one downside: old packages. I took a leap of faith and switched to Rocky Linux.

<!--more-->

### Step 1: Backup

Although my data is on a separate drive, I backed up everything. Not only data (documents, music, pictures...) but also all my settings (Containerfiles and volumes most noteably).

### Step 2: Installation

Rocky Linux has plenty of documentation and this obviously included the installation procedure. Mind that for installation I use a monitor, keyboard and mouse.

In short:

- Download the appropriate image. I chose the minimal version
- Flash to an USB drive (I use BalenaEtcher for this)
- Reboot the server and adjust the boot settings in BIOS to boot from the USB drive
- Reboot again and follow the on screen instructions.

Things I did during installation:
- Enable network. My server gets it's IP via DHCP but with a static lease it always get's the same address.
- Adjust the timezone, and enable network time. Mind that you first have to enable network before enabling network time.
- Enable "Security Policy". This enables SELinux.
- Software Selection: set it to "Minimal Install". I'm freaky about this. If you're more relaxed you could opt for "Server".
- Keep the root account disabled
- Create a non-root account but make it administrator
- Select the "Installation Destination". On My system, I've got two disks: one for the OS and related and one for data. Obviously I select the OS drive and opt for automatic storage configuration. I don't want to preserve anything so I "reclaim" all space on the drive. This deletes everything that is currently on the drive.

Click "Begin Installation" and done.

### Step 3: Finish setup

After rebooting, your trusted but boring login screen will be served. But this is not Debian anymore. We can now have an almost-built-in management interface.

Install by

```
sudo yum install cockpit
```

And enable by

```
sudo enable cockpit.socket
sudo systemctl start cockpit.socket
```

You can now browse to http://your.server.ip:9090. Cockpit will add a firewall rule to allow traffic to port 9090.

Et voilà, you're ready to go.

### Attention!

Rocky Linux comes with SELinux. It can by really annoying but that's a good thing.
If you would like to enable TLS on your cockpit gui, you might experience the joys of dealing with SELinux.
Imagine you upload your certificate to your home directory and move it into place from there. Then your file doesn't have the right label and cockpit won't be able to read it.
Cockpit will only give you an error saying it failed to start. Whether this is SELinux related or not, you can easily check by running

```
$ sudo setenforce 0
```

Probably cockpit will happily serve you the webpage over TLS. But we want to enable SELinux again so we have to restore the file labels:

```
$ sudo restorecon -rv F /etc/cockpit
restorecon: lstat(/etc/cockpit/F) failed: No such file or directory
Relabeled /etc/cockpit/ws-certs.d/your-cert.cert from unconfined_u:object_r:user_home_t:s0 to unconfirmed_u:object_r:etc_t:s0
Relabeled /etc/cockpit/ws-certs.d/your-cert.key from unconfined_u:object_r:user_home_t:s0 to unconfirmed_u:object_r:etc_t:s0
```

You can now enable SELinux again using cockpit or on the command line (`sudo setenforce 1`).


Photo Morskie Oko by Greg Trowman, https://unsplash.com/photos/D9QmRGgxRkk
