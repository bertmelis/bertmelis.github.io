---
layout: post
title: 'Finishing Rocky setup'
tags: Rocky Linux
featured_image_thumbnail: assets/images/posts/rocky/hercules_thumbnail.jpg
featured_image: assets/images/posts/rocky/hercules.jpg
featured: false
hidden: false
---

After the basic installation of Rocky Linux, it's time to finish the setup. We're preparing the system to actually deploy useful stuff.

<!--more-->

### Check

when you finished the [basic setup](posts/Rocky-Linux), you can log in via the terminal or via the web gui (Cockpit). Check basic settings like *hostname*, *time and timezone* and so on.

Cockpit shosw some statistics about your system. If you want to persist them you'll have to install **pcp**. this can be done through the GUI. Alternatively, install **cockpit-pcp** using the command line:

```
$ sudo yum install cockpit-pcp
```

On the "Software updates" tab in the GUI, I also enabled automatic software updates (for security related updates) and kernel patches. As the screen tells you, this means the server will reboot from time to time. Keep this in mind when you manually start programs you rely on. On the same page, you can do a manual update.

### Add disks

Before adding my data disk (in the OS, that is), I added the relevant cockpit addon and smartmontools. The disk supports SMART.

```
$ sudo yum smartmontools cockpit-storaged
```

Create a mount point:

```
$ sudo mkdir /mnt/data
```

Now add the disk. first find it's UUID.

```
$ sudo blkid
/dev/sdb1: UUID="1fdd1ceb-70e8-476b-819d-d7082c7b4749" BLOCK_SIZE="4096" TYPE="ext4" PARTUUID="4f330730-6bd1-4325-9343-37242b985408"
/dev/sda1: UUID="D41A-D5C0" BLOCK_SIZE="512" TYPE="vfat" PARTLABEL="EFI System Partition" PARTUUID="fca2473b-8a02-4600-a776-d9e58b572b32"
/dev/sda2: UUID="106247eb-24a7-4d88-857b-937a09100aba" BLOCK_SIZE="512" TYPE="xfs" PARTUUID="429fe31a-6a8b-4682-8103-a646248bc767"
/dev/sda3: UUID="9RG0BQ-1yKg-Nem8-O1vF-f20Q-YI45-WWJ7t7" TYPE="LVM2_member" PARTUUID="99e3b950-819c-428e-a391-6f962dbbfc1f"
/dev/mapper/rl_server-root: UUID="89b352ee-e051-4a94-bb3e-87d6348dc8d9" BLOCK_SIZE="512" TYPE="xfs"
/dev/mapper/rl_server-swap: UUID="91074d79-f7f3-4ec2-a824-2c530aec8ad7" TYPE="swap"
/dev/mapper/rl_server-home: UUID="43034b2e-0af3-49be-be5a-c4b7ed46b0aa" BLOCK_SIZE="512" TYPE="xfs"
```

The top entry is the right one. It's the only with ext4. I know the drive is formatted like that. If you're unsure, manually mount and check. Add it to `fstab`.

```
$ sudo nano /etc/fstab
```

Add a line like this:

```
UUID=1fdd1ceb-70e8-476b-819d-d7082c7b4749 /mnt/data auto nofail,noatime,noexec,errors=remount-ro 0 0
```

Every item is separated by a space. Some explanation:
- **UUID**: the long code found by `blkid`
- **mount point**: where in the filesystem will the disk be attached
- **filesystem type**:  etx4 or leave auto
- **options**
	- nofail: ignore errors at boot when disk is not there
	- noatime: don't save access time (files and dirs)
	- noexec: don't allow executables on this drive
	- errors=remount-ro: when errors are encountered, remount the drive read-only to avoid further damage
- **0**: dump, leave disabled
- **0**: fsck, set to zero to skip checks at boot

If you want it, you can also use the disk's SMART capabilities:

```
$ sudo systemctl start smartd
$ sudo systemctl enable smartd
```

### Podman

On my Debian installation I ran Podman and a few virtual machines. It's my goal to move everything to [Podman](https://podman.io/). Podman is Redhats Docker. It runs daemonless and is capable of running rootless. These are advantages but my bring some difficulties, especially with SELinux. We'll see where it goes.

At least installation is simple:

```
$ sudo yum install podman cockpit-podman
```

### On last thing

while we're at it, we might want to enable the "extra packages for enterprise linux". Up to now we didn't need any extra packages but we might run into this in the future and who knows, cause some headscratching. It doesn't hurt to enable it:

```
$ sudo yum install epel-release
```

---

Photo Hercule's Rock by Dzidek Lasek, https://pixabay.com/photos/paternal-national-park-autumn-2742115/
