---
layout: post
title: 'Basic configuration of my home server'
tags: ["Debian"]
featured_image_thumbnail: assets/images/posts/basic/debian_thumbnail.jpg
featured_image: assets/images/posts/basic/debian.jpg
featured: false
hidden: false
---

I chose Debian as operating system. It is secure and lean. But this also means a couple of extra steps to make it usable.

<!--more-->

## Installation

For convenience I used a keyboard and monitor for [the installation](https://www.debian.org/releases/stable/installmanual) of Debian 10.

I followed the on screen instruction but a few things are worth mentioning:

- The `root` user didn't get a password. Hence it cannot login but it also means the regular user I created was given `sudo` rights.
- I unchecked all the optional packages so the system was minimal.

Before going completely headless, I installed some basic utilities and an SSH server:

```
$ sudo apt install openssh-server wget gnupg ca-certificates
```

The ssh-server is enabled and started by default. We can now reach the server remotely. All subsequent commands are done on my laptop running Ubuntu. for windows I strongly recommend to use [WSL](https://docs.microsoft.com/en-us/windows/wsl/).

## Connect remotely via SSH

Open a terminal window and check if you already have existing keys:

```
$ ls -al ~/.ssh/id_*.pub
```

If you already have existing keys, you can reuse the old ones and skip the next step. If not, generate new keys:

```
$ ssh-keygen -t rsa -b 4096 -C "name@domain.com"
```

- When asked for the location to save the key press \<enter\> to save in the default location.
- You can set a passphrase but most people don't. Just press \<enter\> for an emtpy passphrase.


The key will be stored in `/home/username/.ssh/`. Check with the same command as above:

```
$ ls -al ~/.ssh/id_*.pub
```

Now copy your key to the server:

```
$ ssh-copy-id remote_username@server_ip_address
```

You can now log in without using your password to the server:

```
$ ssh remote_username@server_ip_address
```

You might want to disable password login now.

```
$ sudo nano /etc/dssh/sshd_config

# uncomment and set to 'no'
PasswordAuthentication no
# you might as well change these:
PermitRootLogin no
PermitRootLogin prohibit-password
```

Reload the ssh service:

```
$ sudo systemctl reload ssh
```

## Solve a minor annoyance

One thing that annoys me is this:
Whenever I install something, this error message pops up:

```
perl: warning: Setting locale failed.   
perl: warning: Please check that your locale settings:   
        LANGUAGE = "en_US:en",   
        LC_ALL = (unset),   
        LC_MESSAGES = "en_US.UTF-8",   
        LANG = "en_US.UTF-8"   
    are supported and installed on your system.   
perl: warning: Falling back to the standard locale ("C").
```

I can safely ignore but it annoys me. To solve:

```
$ sudo nano /etc/default/locale

# add this to the file
LC_CTYPE="en_US.UTF-8"
LC_ALL="en_US.UTF-8"
LANG="en_US.UTF-8"
```

## Additional drivers

When browsing the logs (or on-screen) you might spot an error like this:

```
r8169 0000:03:00.0: firmware: failed to load rtl_nic/rtl8168g-3.fw
```

Realtek drivers are not *enabled* by default because they contain non-free code. I don't mind using non-free drivers. Let's add them.

```
$ sudo nano /etc/apt/sources.list.d/nonfree.list

# Add this to the file
deb http://httpredir.debian.org/debian/ buster main contrib non-free
```

```
$ sudo apt update

# and check with

$ sudo apt policy firmware-realtek

# Result:
firmware-realtek:
  Installed: (none)
  Candidate: 20190114-2
  Version table:
     20190114-2 500
        500 http://httpredir.debian.org/debian buster/non-free amd64 Packages
```

Install them:

```
$ sudo apt install firmware-realtek firmware-misc-nonfree
```

Keep the non-free repo active for driver updates.

## IPv6

I don't use IPv6, my home network doesn't need it. So I better disable it.

```
$ sude nano /etc/sysctl.d/99-sysctl.conf
```

Add

```
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
```

Remove hosts:

```
$ sudo nano /etc/hosts
```

commend out:

```
#::1     localhost ip6-localhost ip6-loopback
#ff02::1 ip6-allnodes
#ff02::2 ip6-allrouters
```
---

<small>Debian in the sky image by [https://www.reddit.com/r/SkyPorn/comments/mr1t3a/winter_in_finland/](https://www.reddit.com/r/SkyPorn/comments/mr1t3a/winter_in_finland/)</small>
