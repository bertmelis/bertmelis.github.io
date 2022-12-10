---
layout: post
title: 'Hardware transcoding for Jellyfin'
tags: ["Jellyfin", "Podman", "SELinux"]
featured_image_thumbnail: assets/images/posts/transcode/chip_thumbnail.jpg
featured_image: assets/images/posts/transcode/chip.jpg
featured: false
hidden: false
---

After relying on MiniDLNA for a long time I switched to Jellyfin as my media server. And I decided to give transcoding on-the-fly a go. Getting it to work wasn't difficult but not as easy as toggling a switch either.
How to get hardware transcoding working in Jellyfin for a J4105 processor?

<!--more-->

## Getting started

I'm not going to go into detail on how to get Jellyfin itself up and running. Jellyfin has great documentation. IT even has a section about Podman. This itself is already remarkable. For most software "containers" as the same as Docker.

I'm running Podman on Rocky Linux 9. My machine has an Intel J4105 processor.

This is the command to get the container up:

```
$ podman run \
  --cgroups=no-conmon \
  --sdnotify=conmon \
  -d \
  --rm
  --label io.containers.autoupdate=registry \
  --name jellyfin \
  --net=host \
  --user $(id -u):$(id -g) \
  --userns keep-id \
  --group-add keep-groups \
  -v /home/user/jellyfin/cache:/cache:Z \
  -v /home/user/jellyfin/config:/config:Z \
  -v /mnt/data/media:/media:ro,z \
  --device=/dev/dri/renderD128:/dev/dri/renderD128 \
  --device=/dev/dri/card0:/dev/dri/card0 \
  jellyfin/jellyfin:latest
```

It's a long command but you can easily hide this in a container-compose.yml file. Or create a systemd file and run it using systemd. The command is taken from the [documentation](https://jellyfin.org/docs/general/administration/installing/#podman). Changes are:

- use host networking instead of just port mapping. This is to enable DLNA discovery.
- use plain volume mount for media
- add the devices to the container.

This last change is important of course. Without the hardware devices to transcode, you can't use them obviously.

Don't forget to open the relevant ports in your firewall.

Browse to your Jellyfin instance and add some libraries. Test and play around. I added some 4k films and enabled the DLNA server.

## Enable hardware transcoding

As soon as I [https://jellyfin.org/docs/general/administration/hardware-acceleration](enabled hardware transcoding), my (old) telefision refused to play the 4k movies I added. "This file is not supported" it said.

I had set the hardware acceleration to "Intel Quicksync (QSV)". After all, Intel itself says [on their website](https://www.intel.com/content/www/us/en/products/sku/128989/intel-celeron-j4105-processor-4m-cache-up-to-2-50-ghz/specifications.html) that the processor supports it.

I clearly need some extra configuration to do. There are some references in Jellyfin's documentation but it's not a step-by-step guide.

## Getting it to work

### Enable driver

Most important step is to verify if the driver is enabled the kernel options are set:

```
$ sudo modinfo i915 | egrep -i "guc|huc|dmc"

firmware:       i915/kbl_huc_4.0.0.bin
firmware:       i915/cml_huc_4.0.0.bin
firmware:       i915/icl_huc_9.0.0.bin
firmware:       i915/ehl_huc_9.0.0.bin
...
firmware:       i915/glk_dmc_ver1_04.bin
firmware:       i915/dg1_dmc_ver2_02.bin
firmware:       i915/adls_dmc_ver2_01.bin
firmware:       i915/adlp_dmc_ver2_14.bin
parm:           enable_guc:Enable GuC load for GuC submission and/or HuC load. Required functionality can be selected using bitmask values. (-1=auto [default], 0=disable, 1=GuC submission, 2=HuC load) (int)
parm:           guc_log_level:GuC firmware logging level. Requires GuC to be loaded. (-1=auto [default], 0=disable, 1..4=enable with verbosity min..max) (int)
parm:           guc_firmware_path:GuC firmware path to use instead of the default one (charp)
parm:           huc_firmware_path:HuC firmware path to use instead of the default one (charp)
parm:           dmc_firmware_path:DMC firmware path to use instead of the default one (charp)
```


Create a file `/etc/modprobe.d/i915.conf`:

```
options i915 enable_guc=2
```

Then update GRUB (mind that I'm on Rocky Linux, your command might need to be adapted):

```
$ sudi grub2-mkconfig -o /boot/efi/EFI/rocky/grub.cfg
```

Rebuild initramfs:

```
$ sudo dracut --force
```

Then reboot.

Verify:

```
$ dmesg | grep drm
[    6.270645] systemd[1]: Starting Load Kernel Module drm...
[    6.333527] ACPI: bus type drm_connector registered
[    7.116873] i915 0000:00:02.0: [drm] couldn't get memory information
[    7.118726] i915 0000:00:02.0: [drm] Applying Increase DDI Disabled quirk
[    7.123425] i915 0000:00:02.0: [drm] Finished loading DMC firmware i915/glk_dmc_ver1_04.bin (v1.4)
[    8.233395] i915 0000:00:02.0: [drm] failed to retrieve link info, disabling eDP
[    8.261328] i915 0000:00:02.0: [drm] GuC firmware i915/glk_guc_69.0.3.bin version 69.0
[    8.261347] i915 0000:00:02.0: [drm] HuC firmware i915/glk_huc_4.0.0.bin version 4.0
[    8.275174] i915 0000:00:02.0: [drm] HuC authenticated
[    8.275189] i915 0000:00:02.0: [drm] GuC submission disabled
[    8.275193] i915 0000:00:02.0: [drm] GuC SLPC disabled
[    8.277572] [drm] Initialized i915 1.6.0 20201103 for 0000:00:02.0 on minor 0
[    8.282514] i915 0000:00:02.0: [drm] Cannot find any crtc or sizes
[    8.285528] i915 0000:00:02.0: [drm] Cannot find any crtc or sizes
[    8.287996] i915 0000:00:02.0: [drm] Cannot find any crtc or sizes
```

Step one done!

### Permissions

To avoid issues with filesystem permissions inside and outside the container I opted to just give rw access to all on both the `/dev/dri/card0` and `/dev/dri/renderD128`. My user had group access to both paths but the groups inside and outside the container are not the same and filesystem permissions fail. By granting everyone read and write access, this issue is out of the way.

This is how it looks like on my side:

```
$ ls -al /dev/dri
total 0
drwxr-xr-x.  3 root root        100 Dec 10 09:20 .
drwxr-xr-x. 21 root root       3520 Dec 10 09:20 ..
drwxr-xr-x.  2 root root         80 Dec 10 09:20 by-path
crw-rw-rw-.  1 root video  226,   0 Dec 10 09:20 card0
crw-rw-rw-.  1 root render 226, 128 Dec 10 09:20 renderD128
```

### SELinux

Playback still doesn't work. A common trick I try is to temporarily disable SELinux.
Also this time: magic! Transcoding works!

And now we need to enable SELinux again.

```
$ sudo setsebool -P container_use_devices=true
```

and

```
$ sudo ausearch -c 'ffmpeg' --raw | audit2allow -M ffmpeg-renderD128
******************** IMPORTANT ***********************
To make this policy package active, execute:

semodule -i ffmpeg-renderD128.pp
$ sudo semodule -i ffmpeg-renderD128.pp
```

Don't forget to re-enable SELinux.

## Done!

You can now enjoy hardware supported transcoding in Jellyfin on your J4105 machine.

---

Chip Photo by <a href="https://unsplash.com/@briankost?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Brian Kostiuk</a> on <a href="https://unsplash.com/s/photos/processor?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>
