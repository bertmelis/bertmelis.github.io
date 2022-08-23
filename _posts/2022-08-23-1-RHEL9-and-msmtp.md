---
layout: post
title: 'RHEL 9 and msmtp'
tags: ["Rocky Linux", "msmtp"]
featured_image_thumbnail: assets/images/posts/msmtp/mailbox_thumbnail.jpg
featured_image: assets/images/posts/msmtp/mailbox.jpg
featured: false
hidden: false
---

I use [msmtp](https://marlam.de/msmtp/) as a simple smtp relay to forward system messages to my Gmail address. After upgrading Rocky Linux to version 9, I noticed msmtp isn't (yet?) available in the repos. So I built it myself.

<!--more-->

### My first rpm ever

I surely could download the source code and install all the dependencies and tools to build and install. However, I don't want to clutter my base system with all these one-time tools. So I decided to build it in a container. I'm way out of my comfort zone here.

After some trial and error and browsing for solutions I ended up with this result.

### Preparation

I'm building on the server so all the action below is done over an ssh connection.
At the time of writing, the latest version of msmtp is 1.8.22.


```
$ mkdir -p msmtp/{build,src} && cd msmtp
$ touch Containerfile build.bash build/build_rpm.bash build/msmtp.spec
```

You now should have the following layout:

```
$ -- msmtp
       |
       +-- build
       |     |
       |     +-- build_rpm.bash
       |     +-- msmtp.spec
       +-- src (empty dir)
       +-- Containerfile
       +-- build.bash
```

Let's see what should be in the files.

#### Containerfile

```
FROM rockylinux:9
RUN dnf install -y epel-release dnf-plugins-core
RUN dnf config-manager --set-enabled crb
RUN dnf install -y rpm-build redhat-rpm-config make gcc nano git tar unzip rpmlint autoconf automake libtool && \
    dnf clean all
RUN mkdir -p /rpmbuild/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
COPY build/build_rpm.bash /rpmbuild/build_rpm.bash
COPY build/msmtp.spec /rpmbuild/msmtp.spec
ADD src /rpmbuild/rpmbuild/SOURCES/
```

Breakdown of the Containerfile: We start from the same base system as we're going to run the result on. Next, we enable extra repos to be able to find msmtp's dependencies and the developer tools. (Red Hat call this CRB or CodeReady Linux Builder repository.) We're then able to install everything we need to build the rpm.

All that's left is to prepare the directory structure and copy/add all the files.

#### build.bash

```shell
#!/bin/bash

PACKAGE_TO_BUILD=msmtp

# directory where the rpm will be stored
if [ -d artifacts ] ; then
 rm -rf artifacts
fi
mkdir artifacts
chmod 777 artifacts

# First build an image that contains the sources and necessary packages for rpmbuild
podman build -t ${PACKAGE_TO_BUILD}-build .

# then run the image
if [ -z $WORKSPACE ] ; then
  WORKSPACE=$(pwd)
fi
podman run --rm -e PACKAGE=${PACKAGE_TO_BUILD} -v ${WORKSPACE}/artifacts:/artifacts:Z ${PACKAGE_TO_BUILD}-build /rpmbuild/build_rpm.bash
```

This is the script that eventually will launch the container to build the rpm. It's simple. All it does is create an output directory, build the image and run the image. Nothing special here.

`chmod +x` so the file is executable.

#### build/build_rpm.bash

```shell
#!/bin/bash

# check if spec file is present
cd /rpmbuild
if [ ! -f ./${PACKAGE}.spec ] ; then
 echo Sorry, can not find rpm spec file
 exit 1
fi
cp ${PACKAGE}.spec /rpmbuild/rpmbuild/SPECS
dnf builddep -y ${PACKAGE}.spec

# then execute the rpmbuild command
cd rpmbuild
rpmbuild -ba --define "_topdir `pwd`" ./SPECS/${PACKAGE}.spec
# copy the rpms to the artifact directory.
if [[ -d /artifacts ]] ; then
 cp ./RPMS/x86_64/${PACKAGE}*.rpm /artifacts/
fi
```

It's again a quite short script. It performs a check for the .spec file and then installs the dependencies that are specified in that spec file.
When that's done, the rpm is built and copied into the `artifacts` directory (which is created by the build.bash script above)

Don't forget to `chmod +x` the file.

#### msmtp.spec

```
Name:           msmtp
Version:        1.8.22
Release:        1%{?dist}
Summary:        SMTP client
License:        GPLv3+
URL:            https://marlam.de/%{name}/
Source0:        https://marlam.de/%{name}/releases/%{name}-%{version}.tar.xz
#Patch1:        msmtp-0001-Fix-linking-w-o-gsasl.patch

BuildRequires: make
%if 0%{?el5}
BuildRequires:  openssl-devel
%else
BuildRequires:  gnutls-devel
%endif

BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  gcc
BuildRequires:  gettext-devel
BuildRequires:  libidn-devel
BuildRequires:  libgsasl-devel
BuildRequires:  libsecret-devel

Requires(post):         %{_sbindir}/alternatives
Requires(postun):       %{_sbindir}/alternatives

%description
It forwards messages to an SMTP server which does the delivery.
Features include:
  * Sendmail compatible interface (command line options and exit codes).
  * Authentication methods PLAIN,LOGIN,CRAM-MD5,DIGEST-MD5,GSSAPI,and NTLM
  * TLS/SSL both in SMTP-over-SSL mode and in STARTTLS mode.
  * Fast SMTP implementation using command pipe-lining.
  * Support for Internationalized Domain Names (IDN).
  * DSN (Delivery Status Notification) support.
  * RMQS (Remote Message Queue Starting) support (ETRN keyword).
  * IPv6 support.

%prep
%autosetup -p1

%build
autoreconf -ivf
%configure --disable-rpath --with-libsecret --with-libgsasl %{?el5:--with-ssl=openssl}
make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot} INSTALL='install -p'
rm -f scripts/Makefile*
%find_lang %{name}
rm -f %{buildroot}%{_infodir}/dir

# setup dummy files for alternatives
touch %{buildroot}%{_bindir}/msmtp

%post
%{_sbindir}/update-alternatives --install %{_sbindir}/sendmail mta %{_bindir}/msmtp 40 \
  --slave %{_prefix}/lib/sendmail mta-sendmail %{_bindir}/msmtp \
  --slave %{_mandir}/man8/sendmail.8.gz mta-sendmailman %{_mandir}/man1/msmtp.1.gz \
  --slave %{_bindir}/mailq mta-mailq %{_bindir}/msmtp \
  --slave %{_mandir}/man1/mailq.1.gz mta-mailqman %{_mandir}/man1/msmtp.1.gz

%postun
if [ $1 -eq 0 ] ; then
        %{_sbindir}/update-alternatives --remove mta %{_bindir}/msmtp
fi

%files -f %{name}.lang
%license COPYING
%doc AUTHORS NEWS README THANKS scripts
%doc doc/msmtprc-system.example doc/msmtprc-user.example
%{_bindir}/%{name}*
%{_infodir}/%{name}.info*
%{_mandir}/man1/%{name}*.1*

%changelog
* Wed Aug 10 2022 My Name <e_mail@domain.com> - 1.8.22-1
- Ver. 1.8.22
```

This file I copied from Fedora's source and happened to work on RHEL9 which isn't a surprise of course.

### Get the source

One last thing before building is getting the actual source code. So download the `.tar.xz` file [here](https://marlam.de/msmtp/download/) and put it in the `src` directory. You don't need to untar.

### Build!

Now, just run the script:

```
$ ./build.bash
```

It builds an image called "msmtp-build". Then creates a container that builds the rpm (and destroys the container afterwards).

Install msmtp by a simple:

```
$ sudo dnf install artifacts/msmtp-1.8.22-1.el9.x86_64.rpm
```

Done! Configure msmtp the same way as on other Linux systems like [I did here](https://bert.emelis.net/posts/1-MSMTP).

Instead of copy pasting, you can download the whole set of files from my Github: [build-msmtp](https://github.com/bertmelis/build-msmtp).

---
