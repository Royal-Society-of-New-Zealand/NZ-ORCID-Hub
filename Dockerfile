# syntax=docker/dockerfile:experimental
FROM centos:centos7 AS orcidhub
LABEL maintainer="PRODATA TAPUI Ltd." \
	description="Centos image with Apache and Shiboleth"
ARG http_proxy
# ADD http://download.opensuse.org/repositories/security://shibboleth/CentOS_7/security:shibboleth.repo /etc/yum.repos.d/shibboleth.repo
ADD https://shibboleth.net/cgi-bin/sp_repo.cgi?platform=CentOS_7 /etc/yum.repos.d/shibboleth.repo
COPY conf/app.wsgi /var/www/html/
# prefix "ZZ" added, that it gest inluded the very end (after Shibboleth gets loaded)
COPY conf/app.conf /etc/httpd/conf.d/ZZ-app.conf
COPY requirements.txt /
# COPY setup.* orcid* /
COPY run-app /usr/local/bin/
COPY ./conf /conf
RUN test -n "${http_proxy}" && export ftp_proxy=$http_proxy https_proxy=$http_proxy \
    && yum -y install \
        https://repo.ius.io/ius-release-el7.rpm \
        https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
    && yum -y remove pgdg-redhat-repo-42.0-32 && yum clean all \
    && yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm \
    && yum install -y centos-release-scl \
    && yum clean all  \
    && yum update -y \
    && yum upgrade -y \
    && yum install -y devtoolset-8 \
    && yum install -y \
        postgresql15 \
        shibboleth.x86_64 \
    	httpd \
        cscope \
        doxygen \
        gettext \
        diffstat \
        libtool \
        net-tools \
        git \
        openssl11 \
        openssl11-libs \
        hwdata \
        intltool \
        lzma \
        json-glib \
        mod_ssl \
    && yum -y install \
        apr-util-devel \
        bzip2-devel \
        cyrus-sasl-devel \
        expat-devel \
        freetype-devel \
        gdbm-devel \
        glib-networking \
        glibc-devel \
        httpd-devel \
        libdb-devel \
        libdhash-devel \
        libdrm-devel \
        libffi-devel \
        libglvnd-core-devel \
        libglvnd-devel \
        libpng-devel \
        libtirpc-devel \
        libuuid-devel \
        libxcb-devel \
        libzip-devel \
        lzma-sdk-devel \
        ncurses-devel \
        openldap-devel \
        openssl11-devel \
        readline-devel \
        sqlite-devel \
        systemtap-sdt-devel \
        tcl-devel \
        tix-devel \
        tk-devel \
        xz-devel \
    && echo $'Building Python 3.11...' \
    && curl -O https://www.python.org/ftp/python/3.11.2/Python-3.11.2.tar.xz \
    && tar xf Python-3.11.2.tar.xz \
    && cd Python-3.11.2 \
    && export \
        CFLAGS="$CFLAGS $(pkg-config --cflags openssl11)" \
        LDFLAGS="$LDFLAGS $(pkg-config --libs openssl11)" \
        LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib \
    && scl enable devtoolset-8 bash \
    && source /opt/rh/devtoolset-8/enable ; hash -r \
    && ./configure --enable-optimizations --enable-shared \
    && make && make install ; cd $HOME ; hash -r \
    && echo $'/usr/local/lib\n' > /etc/ld.so.conf.d/local.conf \
    && ldconfig \
    && python3.11 -m ensurepip --upgrade \
    && python3 -m pip install -U pip \
    && pip install -U mod_wsgi psycopg2-binary \
    && /usr/local/bin/mod_wsgi-express module-config >/etc/httpd/conf.modules.d/10-wsgi.conf \
    && mkdir -p /var/run/lock && mkdir -p /var/lock/subsys \
    && echo $'export LD_LIBRARY_PATH=/usr/local/lib:/opt/shibboleth/lib64:$LD_LIBRARY_PATH\n' > /etc/sysconfig/shibd \
    && chmod -f +x /usr/local/bin/run-app \
    && pip install -U -r /requirements.txt \
    && pip install -U 'flask<2.2.3' \
    && pip install -U 'flask<2.3.0' \
    && yum erase -y \
        gcc \
        devtoolset-8 \
        devtoolset-8-binutils \
        devtoolset-8-dwz \
        devtoolset-8-dyninst \
        devtoolset-8-elfutils \
        devtoolset-8-elfutils-libelf \
        devtoolset-8-elfutils-libs \
        devtoolset-8-gcc \
        devtoolset-8-gcc-c++ \
        devtoolset-8-gcc-gfortran \
        devtoolset-8-gdb \
        devtoolset-8-ltrace \
        devtoolset-8-make \
        devtoolset-8-memstomp \
        devtoolset-8-oprofile \
        devtoolset-8-perftools \
        devtoolset-8-runtime \
        devtoolset-8-strace \
        devtoolset-8-systemtap \
        devtoolset-8-systemtap-client \
        devtoolset-8-systemtap-runtime \
        devtoolset-8-toolchain \
        devtoolset-8-valgrind \
        alsa-lib \
        copy-jdk-configs \
        fontconfig \
        fontpackages-filesystem \
        freetype \
        gcc-c++ \
        giflib \
        git \
        glib-networking \
        glibc-headers \
        hwdata \
        java-1.8.0-openjdk-headless \
        javapackages-tools \
        json-glib \
        kernel-headers \
        libICE \
        libSM \
        libX11 \
        libX11-common \
        libXau \
        libXcomposite \
        libXext \
        libXfont \
        libXi \
        libXrender \
        libXtst \
        libfontenc \
        libjpeg-turbo \
        libpng \
        libxcb \
        libxslt \
        lksctp-tools \
        net-tools \
        perl \
        python-javapackages \
        python-lxml \
        systemtap \
        ttmkfdir \
        tzdata-java \
        xorg-x11-font-utils \
        xorg-x11-fonts-Type1 \
        perl \
        perl-Carp.noarch \
        perl-Data-Dumper \
        perl-Encode \
        perl-Error.noarch \
        perl-Exporter.noarch \
        perl-File-Path.noarch \
        perl-File-Temp.noarch \
        perl-Filter \
        perl-Getopt-Long.noarch \
        perl-Git.noarch \
        perl-HTTP-Tiny.noarch \
        perl-PathTools \
        perl-Pod-Escapes.noarch \
        perl-Pod-Perldoc.noarch \
        perl-Pod-Simple.noarch \
        perl-Pod-Usage.noarch \
        perl-Scalar-List-Utils \
        perl-Socket \
        perl-Storable \
        perl-TermReadKey \
        perl-Test-Harness.noarch \
        perl-Text-ParseWords.noarch \
        perl-Thread-Queue.noarch \
        perl-Time-HiRes \
        perl-Time-Local.noarch \
        perl-XML-Parser \
        perl-constant.noarch \
        perl-libs \
        perl-macros \
        perl-parent.noarch \
        perl-podlators.noarch \
        perl-threads \
        perl-threads-shared \
    && yum erase -y \
        apr-devel \
        apr-util-devel \
        bzip2-devel \
        cyrus-sasl-devel \
        devtoolset-8-libquadmath-devel \
        devtoolset-8-libstdc++-devel \
        devtoolset-8-systemtap-devel \
        expat-devel \
        fontconfig-devel \
        freetype-devel \
        gdbm-devel \
        gettext-common-devel.noarch \
        gettext-devel \
        glibc-devel \
        httpd-devel \
        kernel-debug-devel \
        keyutils-libs-devel \
        krb5-devel \
        libX11-devel \
        libXau-devel \
        libXft-devel \
        libXrender-devel \
        libcom_err-devel \
        libdb-devel \
        libdhash-devel \
        libdrm-devel \
        libffi-devel \
        libglvnd-core-devel \
        libglvnd-devel \
        libpng-devel \
        libselinux-devel \
        libsepol-devel \
        libtirpc-devel \
        libuuid-devel \
        libverto-devel \
        libxcb-devel \
        libzip-devel \
        lzma-sdk-devel \
        ncurses-devel \
        openldap-devel \
        openssl11-devel \
        pcre-devel \
        readline-devel \
        sqlite-devel \
        systemtap-sdt-devel \
        tcl-devel \
        tix-devel \
        tk-devel \
        xorg-x11-proto-devel.noarch \
        xz-devel \
        zlib-devel \
    && yum clean all  \
    && cd /var/lib/rpm \
    && rm -rf __db* \
    && rpm --rebuilddb \
    && yum -y clean all \
    && chmod -f +x /etc/shibboleth/shibd-redhat \
    && rm -rf /var/cache/yum /Python-3.11.2.tar.xz /Python-3.11.2 \
    && rm -rf $HOME/.pip/cache \
    && rm -rf /var/cache/*/* /anaconda-post.log /requirements.txt

EXPOSE 80 443

CMD ["run-app"]
