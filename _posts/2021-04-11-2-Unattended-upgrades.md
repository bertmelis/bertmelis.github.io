---
layout: post
title: 'Unattended upgrades on Debian 10'
tags: server Debian
featured_image_thumbnail: assets/images/posts/unattended/coffee_thumbnail.jpg
featured_image: assets/images/posts/unattended/coffee.jpg
featured: false
hidden: false
---

Updating is good. But even on Debian "hoping that things won't break" is sometimes part of the update strategy. Except for security. Let's enable unattended updates. 

<!--more-->

My server does auto-update but not major upgrades. Major upgrades wait for my manual intervention.

## Preparation

to enable automatic updates, a package called `unattended-upgrades` has to be enabled.

```
$ sudo apt install --no-install-recommends unattended-upgrades apt-listchanges
```

On my system this installs: `apt-listchanges python-apt-common python3-apt python3-debconf python3-distro-info unattended-upgrades`.

## Configuration

Settings for the automatic updates are in `/etc/apt/apt.conf.d/02periodic`.

Edit the file (and create if nonexistent):

```
$ sudo nano /etc/apt/apt.conf.d/02periodic
```

Copy the following content into the file and adjust to your liking:

```
// Control parameters for cron jobs by /etc/cron.daily/apt-compat //


// Enable the update/upgrade script (0=disable)
APT::Periodic::Enable "1";


// Do "apt-get update" automatically every n-days (0=disable)
APT::Periodic::Update-Package-Lists "1";


// Do "apt-get upgrade --download-only" every n-days (0=disable)
APT::Periodic::Download-Upgradeable-Packages "1";


// Run the "unattended-upgrade" security upgrade script
// every n-days (0=disabled)
// Requires the package "unattended-upgrades" and will write
// a log in /var/log/unattended-upgrades
APT::Periodic::Unattended-Upgrade "1";


// Do "apt-get autoclean" every n-days (0=disable)
APT::Periodic::AutocleanInterval "21";


// Send report mail to root
//     0:  no report             (or null string)
//     1:  progress report       (actually any string)
//     2:  + command outputs     (remove -qq, remove 2>/dev/null, add -d)
//     3:  + trace on
APT::Periodic::Verbose "2";
```

Test with:

```
$ sudo unattended-upgrade -d
```

If you installed [Logwatch](/posts/Logwatch), updates will be included in the daily report.

<small>Coffe machine Image by <a href="https://pixabay.com/users/holnsteiner-5407239/?utm_source=link-attribution&amp;utm_medium=referral&amp;utm_campaign=image&amp;utm_content=2329366">Hans Peter Holnsteiner</a> from <a href="https://pixabay.com/?utm_source=link-attribution&amp;utm_medium=referral&amp;utm_campaign=image&amp;utm_content=2329366">Pixabay</a></small>
