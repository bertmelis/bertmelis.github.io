---
layout: post
title: 'Eaton UPS monitoring'
#tags: [server, Debian, UPS]
tags: server Debian UPS Eaton
featured_image_thumbnail: assets/images/posts/ups/power_thumbnail.jpg
featured_image: assets/images/posts/ups/power.jpg
featured: false
hidden: false
---

Power outages are rare nowadays. But they are not nonexistent. I bought a second hand UPS and a new battery to keep my server up during an eventual short outage.

<!--more-->

So I bought a second hand Eaton Ellipse ASR 750. It's a rather old device but it came with a new battery. And it has a USB connection so I plugged it into my server and started with [Network UPS tools](https://networkupstools.org/).

## Installation

Network UPS Tools or NUT has been around for ages, so it made it's way into the standard Debian repo's.

```
$ sudo apt install nut
```

This installs `bash-completion libupsclient4 nut-client nut-server`. Your machine may yield different results.

There were some error messages. We'll take care of them later:

```
Created symlink /etc/systemd/system/multi-user.target.wants/nut-monitor.service → /lib/systemd/system/nut-monitor.service.
Job for nut-monitor.service failed because the service did not take the steps required by its unit configuration.
See "systemctl status nut-monitor.service" and "journalctl -xe" for details.
invoke-rc.d: initscript nut-client, action "start" failed.
● nut-monitor.service - Network UPS Tools - power device monitor and shutdown controller
   Loaded: loaded (/lib/systemd/system/nut-monitor.service; enabled; vendor preset: enabled)
   Active: failed (Result: protocol) since Mon 2021-04-19 20:34:41 CEST; 10ms ago
  Process: 31660 ExecStart=/sbin/upsmon (code=exited, status=0/SUCCESS)
      CPU: 2ms

Apr 19 20:34:41 server systemd[1]: Starting Network UPS Tools - power device monitor and shutdown controller...
Apr 19 20:34:41 server upsmon[31660]: upsmon disabled, please adjust the configuration to your needs
Apr 19 20:34:41 server upsmon[31660]: Then set MODE to a suitable value in /etc/nut/nut.conf to enable it
Apr 19 20:34:41 server systemd[1]: nut-monitor.service: Can't open PID file /run/nut/upsmon.pid (yet?) after start: No such file or directory
Apr 19 20:34:41 server systemd[1]: nut-monitor.service: Failed with result 'protocol'.
Apr 19 20:34:41 server systemd[1]: Failed to start Network UPS Tools - power device monitor and shutdown controller.
Apr 19 20:34:41 server systemd[1]: nut-monitor.service: Consumed 2ms CPU time.
```

Now check if the UPS is connected and recognized:

```
$ lsusb | grep UPS
Bus 001 Device 002: ID 0463:ffff MGE UPS Systems UPS
```
Bingo!

- Vendor ID : 0463
- Device ID : ffff


## Configuration

We will now set up nut to check on the UPS.

In the file `/etc/nut/ups.conf` we add the following:

```
[eaton]
driver = usbhid-ups
port = auto
desc = "Eaton Ellipse ASR 750"
synchronous = "yes"
```

Let's test

```
# this doesn't work
$ upsdrvctl start
-bash: upsdrvctl: command not found
# should be somewhere...
$ whereis upsdrvctl
upsdrvctl: /usr/sbin/upsdrvctl /usr/share/man/man8/upsdrvctl.8.gz
$ /usr/sbin/upsdrvctl start
Network UPS Tools - UPS driver controller 2.7.4
Can't open /etc/nut/ups.conf: Can't open /etc/nut/ups.conf: Permission denied
```

My UPS only has one "consumer" which it my server. So NUT can perfectly be set to `standalone` mode.

In the file `/etc/nut/nut.conf` set:

```
...
MODE=standalone
```

With the driver configured, there are two services left: **upsd** and **upsmon**.

**upsd**, or the daemon will serve the UPS data to the clients and is listening on localhost, port 3493.

In the file `/etc/nut/uspd.conf` set:

```
...
# comment out this line:
LISTEN 127.0.0.1 3493
...
```

**upsmon** interacts with upsd it's configuration is two-fold: access.

In the file `/etc/nut/upsd.users` set:

```
[upsmonitor]
password = ups_password
upsmon master
```

The daemon is listening and knows who to allow access. So now configure the monitor.

In the file `/etc/nut/upsmon.conf` add:

```
MONITOR eaton@localhost 1 upsmonitor ups_password master
```

## Test

You could simply pull the plug. But first make sure all services are running correctly!

```
$ sudo systemctl start ups-driver
$ sudo systemctl start nut-server
$ sudo systemctl start ups-monitor
```

A reboot may work too because the services are marked for auto-start.

You can check the installation with:

```
$ upsc eaton@localhost
battery.charge: 100
battery.charge.low: 30
battery.runtime: 3000
battery.type: PbAc
device.mfr: EATON
device.model: Ellipse 750
device.serial: BDCL440GL
device.type: ups
driver.name: usbhid-ups
driver.parameter.pollfreq: 30
driver.parameter.pollinterval: 2
driver.parameter.port: auto
driver.parameter.synchronous: yes
driver.version: 2.7.4
driver.version.data: MGE HID 1.39
driver.version.internal: 0.41
input.transfer.high: 264
input.transfer.low: 184
outlet.1.desc: PowerShare Outlet 1
outlet.1.id: 2
outlet.1.status: on
outlet.1.switchable: no
outlet.desc: Main Outlet
outlet.id: 1
outlet.switchable: no
output.frequency.nominal: 50
output.voltage: 230.0
output.voltage.nominal: 230
ups.beeper.status: enabled
ups.delay.shutdown: 20
ups.delay.start: 30
ups.load: 2
ups.mfr: EATON
ups.model: Ellipse 750
ups.power.nominal: 750
ups.productid: ffff
ups.serial: BDCL440GL
ups.status: OL
ups.timer.shutdown: -1
ups.timer.start: -10
ups.vendorid: 0463
```

### Connection refused?

NUT runs as *nut* user and has no access to USB by default. So we have to create udev-rules to solve this.

Create a file `/etc/udev/rules.d/90-nut-ups.rules` with the following content. Mind the idVendor and idProduct we discovered in the first step.

```
# Eaton ellipse ASR 750
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="0463", ATTR{idProduct}=="ffff", MODE="0660", GROUP="nut"
```

### The UPS is gone?

Sometimes the UPS driver fails and loses connection. That would be disastrous. After all, the knowing how the UPS is doing is crucial for a gracious shutdown should the battery get low.

You can find out with this command:

```
$ /bin/upsc eaton | grep 'device.type'
Init SSL without certificate database
Error: Data stale
```

Data stale? Then reload the driver. While we could restart the basic `sudo /lib/nut/usbhid-ups -a eaton` this doesn't help when the `nut-driver` service already failed. So we restart the service and the service will take care of restarting the underlying driver.

```
$ sudo systemctl restart nut-driver
Network UPS Tools - UPS driver controller (2.7.4)
USB communication driver 0.33
Network UPS Tools - Generic HID driver 0.41 (2.7.4)
Using subdriver: MGE HID 1.39
Duplicate driver instance detected! Terminating other driver!

# Now check again
$ /bin/upsc eaton | grep 'device.type'
Init SSL without certificate database
device.type: ups
```

Best to put this in a script and run regularly.

Create a file ~/checkups.sh

```
#!/bin/bash

if [[ $(/bin/upsc eaton | grep 'device.type') == *ups ]]; then
  exit 0
else
  systemctl restart nut-driver
fi
```

The frequency to run this script depends on the size of the UPS and the power of your server. The power source of my server is rated 80W. The UPS is 750VA or 450W with a 12V/9Ah battery. The battery can deliver about 108VAh. On maximum load it should theoretically last about one hour. So a safe interval of checking every 10 minutes should be more than enough. There is one thing we have to take care of though. The default values in `upsmon.conf` make upsmon check the UPS every 5 seconds. When a UPS isn't answering to the polls it is marked "stale". When this condition lasts for more then `DEADTIME`, the UPS is marked "dead".

I chose a checking frequency of 60 seconds while on AC power and 10 seconds while on battery power.

Since we only check the USB connection every 10 minutes but poll every minute, or 10 seconds depending on the power source, we should set `DEADTIME` and `NOCOMMWARNTIME` to 600 seconds. This will avoid spamming of the log when the USB connection to the UPS goes down.

In file `/etc/nut/upsmon.conf`:

```
POLLFREQ 60
POLLFREQALERT 10
DEADTIME 600
NOCOMMWARNTIME 600
```

While we could use `systemd` for this, `crontab` is more straightforward and equally reliable.

`Cron` is running out of the box on Debian 10 but it doesn't hurt to check:

```
$ sudo systemctl start cron
● cron.service - Regular background program processing daemon
   Loaded: loaded (/lib/systemd/system/cron.service; enabled; vendor preset: enabled)
   Active: active (running) since Sat 2021-04-12 17:44:11 CEST; 2 days ago
     Docs: man:cron(8)
 Main PID: 412 (cron)
    Tasks: 2 (limit: 4915)
   Memory: 190.7M
      CPU: 1min 58.452s
...
```

The script has to run as `root` since we don't want to be asked for our `sudo` password when we're low on power. So use `$ sudo crontab -e` instead of your user's `$ crontab -e`.

```
$ sudo crontab -e

# add in the following
# the script will run every half hour, 5 past the hour and at 35 past
5,35 * * * * /home/<username>/checkups.sh 2>&1 | /usr/bin/logger -t checkups

```

I stop worrying about ungraceful shutdown because of power outages.

## Live test

I did a live test by pulling the plug on the UPS and checked the UPS's parameters a few times.

```
$ upsc eaton@localhost | grep 'battery'
Init SSL without certificate database
battery.charge: 91
battery.charge.low: 30
battery.runtime: 2730
battery.type: PbAc
```

> "I love it when a plan comes together." <cite>- Colonel John “Hannibal” Smith -</cite>

---

<small>Power meter photo by <a href="https://unsplash.com/@tanerardali?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">taner ardalı</a> on <a href="https://unsplash.com/s/photos/power-meter?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a></small>
  