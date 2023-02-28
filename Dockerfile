# syntax=docker/dockerfile:experimental
FROM centos:centos7 AS orcidhub
LABEL maintainer="PRODATA TAPUI Ltd." \
	description="Centos image with Apache and Shiboleth"
ARG http_proxy
# ADD http://download.opensuse.org/repositories/security://shibboleth/CentOS_7/security:shibboleth.repo /etc/yum.repos.d/shibboleth.repo
ADD https://shibboleth.net/cgi-bin/sp_repo.cgi?platform=CentOS_7 /etc/yum.repos.d/shibboleth.repo
RUN test -n "${http_proxy}" && export ftp_proxy=$http_proxy https_proxy=$http_proxy \
    && yum -y install \
        https://repo.ius.io/ius-release-el7.rpm \
        https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
    && yum -y remove pgdg-redhat-repo-42.0-32 && yum clean all \
    && yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm \
    && yum install -y centos-release-scl \
    && yum clean all  \
    && yum -y update \
    && yum -y upgrade \
    && yum -y install \
        devtoolset-8 \
    	httpd \
        apr-util-devel \
        bzip2-devel \
        cscope \
        cyrus-sasl-devel \
        diffstat \
        doxygen \
        expat-devel \
        freetype-devel \
        gdbm-devel \
        gettext \
        git \
        glib-networking \
        glibc-devel \
        httpd-devel \
        hwdata \
        indent \
        intltool \
        json-glib \
        libdb-devel \
        libdhash-devel \
        libdrm-devel \
        libffi-devel \
        libglvnd-core-devel \
        libglvnd-devel \
        libpng-devel \
        libtirpc-devel \
        libtool \
        libuuid-devel \
        libxcb-devel \
        libzip-devel \
        lzma \
        lzma-sdk-devel \
        mesa-khr-devel \
        mesa-libGL-devel \
        ncurses-devel \
        net-tools \
        openldap-devel \
        openssl11 \
        openssl11-devel \
        openssl11-lib \
        readline-devel \
        shibboleth.x86_64 \
        sqlite-devel \
        subversion \
        systemtap-sdt-devel \
        tcl-devel \
        tix-devel \
        tk-devel \
        xz-devel \
        mod_ssl \
    && scl enable devtoolset-8 bash \
    && echo $'Building Python 3.11...' \
    && curl -O https://www.python.org/ftp/python/3.11.2/Python-3.11.2.tar.xz \
    && tar xf Python-3.11.2.tar.xz \
    && cd Python-3.11.2 \
    && export \
        CFLAGS="$CFLAGS $(pkg-config --cflags openssl11)" \
        LDFLAGS="$LDFLAGS $(pkg-config --libs openssl11)" \
        LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib \
    && ./configure --enable-optimizations --enable-shared \
    && echo $'/usr/local/lib\n' > /etc/ld.so.conf.d/local.conf \
    && ldconfig \
    && make && make install ; cd $HOME ; hash -r \
    && python3.11 -m ensurepip --upgrade \
    && python3 -m pip install -U pip \
    && pip install -U mod_wsgi psycopg2-binary \
    && echo $'export LD_LIBRARY_PATH=/usr/local/lib:/opt/shibboleth/lib64:$LD_LIBRARY_PATH\n' > /etc/sysconfig/shibd \
    && yum clean all  \
    && cd /var/lib/rpm \
    && rm -rf __db* \
    && rpm --rebuilddb \
    && yum -y clean all \
    && chmod -f +x /etc/shibboleth/shibd-redhat \
    && rm -rf /var/cache/yum \
    && rm -rf $HOME/.pip/cache \
    && rm -rf /var/cache/*/* /anaconda-post.log


    # && yum erase -y \
    #     "gcc-c++" \
    #     alsa-lib \
    #     apr-util-devel \
    #     bzip2-devel \
    #     copy-jdk-configs \
    #     cyrus-sasl-devel \
    #     expat-devel \
    #     expat-devel \
    #     fontconfig \
    #     fontpackages-filesystem \
    #     freetype \
    #     freetype-devel \
    #     gdbm-devel \
    #     giflib \
    #     git \
    #     glib-networking \
    #     glibc-devel \
    #     glibc-headers \
    #     httpd-devel \
    #     hwdata \
    #     java-1.8.0-openjdk-headless \
    #     javapackages-tools \
    #     json-glib \
    #     kernel-headers \
    #     libICE \
    #     libSM \
    #     libX11 \
    #     libX11-common \
    #     libXau \
    #     libXcomposite \
    #     libXext \
    #     libXfont \
    #     libXi \
    #     libXrender \
    #     libXtst \
    #     libdb-devel \
    #     libdhash-devel \
    #     libdrm-devel \
    #     libffi-devel \
    #     libfontenc \
    #     libglvnd-core-devel \
    #     libglvnd-devel \
    #     libjpeg-turbo \
    #     libpng \
    #     libpng-devel \
    #     libtirpc-devel \
    #     libuuid-devel \
    #     libxcb \
    #     libxcb-devel \
    #     libxslt \
    #     libzip-devel \
    #     lksctp-tools \
    #     lzma-sdk-devel \
    #     mesa-khr-devel \
    #     mesa-libGL-devel \
    #     ncurses-devel \
    #     net-tools \
    #     openldap-devel \
    #     openssl11-devel \
    #     perl \
    #     python-javapackages \
    #     python-lxml \
    #     readline-devel \
    #     sqlite-devel \
    #     systemtap \
    #     systemtap-sdt-devel \
    #     tcl-devel \
    #     tix-devel \
    #     tk-devel \
    #     ttmkfdir \
    #     tzdata-java \
    #     xorg-x11-font-utils \
    #     xorg-x11-fonts-Type1 \
    #     xz-devel \






#FROM centos  AS sources
#LABEL maintainer="PRODATA TAPUI Ltd." \
#	description="Off-line cache of the sources"
#RUN echo $'Downloading the sourcs' \
#    && curl -O http://ftp.mirrorservice.org/sites/sourceware.org/pub/gcc/releases/gcc-12.2.0/gcc-12.2.0.tar.gz \
#    && curl -O https://www.python.org/ftp/python/3.11.2/Python-3.11.2.tar.xz

#FROM centos AS gcc
#ENV LANG=en_US.UTF-8
#ARG http_proxy

#LABEL maintainer="PRODATA TAPUI Ltd." \
#	description="Centos image with the most recetn GCC"

## yum group install -y "Development Tools" \
#RUN --mount=type=bind,from=sources,source=/,target=/sources \
#    test -n "${http_proxy}" && export ftp_proxy=$http_proxy https_proxy=$http_proxy \
#    && yum -y install \
#        "gcc-c++" \
#        bzip2 lzma xz-devel \
#        openssl11 openssl11-lib openssl11-devel \
#        ncurses-devel libuuid-devel \
#    && echo $'Building GCC 12.2...' \
#    && tar xf /sources/gcc-12.2.0.tar.gz \
#    && cd gcc-12.2.0 \
#    && ./contrib/download_prerequisites \
#    && ./configure --disable-multilib --enable-languages=c,c++ \
#    && make -j 4 && make install ; cd $HOME ; hash -r \
#    && echo $'Installing and re-Building GCC 12.2...' \
#    && yum erase -y "gcc-c++" gcc cpp ; hash -r \
#    && cd gcc-12.2.0 \
#    && make clean \
#    && ./configure --disable-multilib --enable-languages=c,c++ \
#    && make -j 4 && make install ; cd $HOME ; hash -r \
#    && [ -d /var/run/lock ] || mkdir -p /var/run/lock \
#    && [ -d /var/lock/subsys/ ] || mkdir -p /var/lock/subsys/ \
#    && echo $'export LD_LIBRARY_PATH=/usr/local/lib:/opt/shibboleth/lib64:$LD_LIBRARY_PATH\n' > /etc/sysconfig/shibd \
#    && yum erase -y \
#        alsa-lib \
#        apr-util-devel \
#        copy-jdk-configs \
#        cpp \
#        cyrus-sasl-devel \
#        expat-devel \
#        fontconfig \
#        fontpackages-filesystem \
#        freetype \
#        gcc \
#        giflib \
#        git \
#        glibc-devel \
#        glibc-headers \
#        httpd-devel \
#        javapackages-tools \
#        kernel-headers \
#        libdb-devel \
#        libfontenc \
#        libICE \
#        libjpeg-turbo \
#        libpng \
#        libSM \
#        libX11 \
#        libX11-common \
#        libXau \
#        libxcb \
#        libXcomposite \
#        libXext \
#        libXfont \
#        libXi \
#        libXrender \
#        libxslt \
#        libXtst \
#        lksctp-tools \
#        openldap-devel \
#        perl \
#        python36-devel \
#        python36-pip \
#        python-javapackages \
#        python-lxml \
#        ttmkfdir \
#        xorg-x11-fonts-Type1 \
#        xorg-x11-font-utils \
#        java-1.8.0-openjdk-headless \
#        tzdata-java \
#    && cd /var/lib/rpm \
#    && rm -rf __db* \
#    && rpm --rebuilddb \
#    && yum -y clean all \
#    && rm -rf /var/cache/yum \
#    && rm -rf $HOME/.pip/cache \
#    && rm -rf /var/cache/*/* /anaconda-post.log \
#    && rm -rf /requirements.txt /swagger_client.egg-info /setup.* /orcid_*


#FROM centos as runtime
#ENV LANG=en_US.UTF-8
#ARG http_proxy

#LABEL maintainer="PRODATA TAPUI Ltd." \
#	description="Centos image with the most recetn GCC, Python, Apache, and WSGI"

## ADD http://download.opensuse.org/repositories/security://shibboleth/CentOS_7/security:shibboleth.repo /etc/yum.repos.d/shibboleth.repo
#ADD https://shibboleth.net/cgi-bin/sp_repo.cgi?platform=CentOS_7 /etc/yum.repos.d/shibboleth.repo

#RUN --mount=type=bind,from=sources,source=/,target=/sources \
#    test -n "${http_proxy}" && export ftp_proxy=$http_proxy https_proxy=$http_proxy \
#    && yum -y install \
#        bzip2 \
#        lzma xz-devel \
#        openssl11 openssl11-lib openssl11-devel \
#        ncurses-devel \
#        libuuid-devel \
#        shibboleth.x86_64 \
#    	httpd \
#        mod_ssl \
#    && yum group install -y "Development Tools" \
#    && echo $'Building GCC 12.2...' \
#    && tar xf /sources/gcc-12.2.0.tar.gz \
#    && cd gcc-12.2.0 \
#    && ./contrib/download_prerequisites \
#    && ./configure --disable-multilib --enable-languages=c,c++ \
#    && make -j 4 && make install ; cd $HOME ; hash -r \
#    && [ -d /var/run/lock ] || mkdir -p /var/run/lock \
#    && [ -d /var/lock/subsys/ ] || mkdir -p /var/lock/subsys/ \
#    && echo $'export LD_LIBRARY_PATH=/usr/local/lib:/opt/shibboleth/lib64:$LD_LIBRARY_PATH\n' > /etc/sysconfig/shibd \
#    && yum erase -y \
#        alsa-lib \
#        apr-util-devel \
#        copy-jdk-configs \
#        cpp \
#        cyrus-sasl-devel \
#        expat-devel \
#        fontconfig \
#        fontpackages-filesystem \
#        freetype \
#        gcc \
#        giflib \
#        git \
#        glibc-devel \
#        glibc-headers \
#        httpd-devel \
#        javapackages-tools \
#        kernel-headers \
#        libdb-devel \
#        libfontenc \
#        libICE \
#        libjpeg-turbo \
#        libpng \
#        libSM \
#        libX11 \
#        libX11-common \
#        libXau \
#        libxcb \
#        libXcomposite \
#        libXext \
#        libXfont \
#        libXi \
#        libXrender \
#        libxslt \
#        libXtst \
#        lksctp-tools \
#        openldap-devel \
#        perl \
#        python36-devel \
#        python36-pip \
#        python-javapackages \
#        python-lxml \
#        ttmkfdir \
#        xorg-x11-fonts-Type1 \
#        xorg-x11-font-utils \
#        java-1.8.0-openjdk-headless \
#        tzdata-java \
#    && cd /var/lib/rpm \
#    && rm -rf __db* \
#    && rpm --rebuilddb \
#    && yum -y clean all \
#    && rm -rf /var/cache/yum \
#    && rm -rf $HOME/.pip/cache \
#    && rm -rf /var/cache/*/* /anaconda-post.log \
#    && rm -rf /requirements.txt /swagger_client.egg-info /setup.* /orcid_*


#FROM centos AS python
#ENV LANG=en_US.UTF-8
#ARG http_proxy

#LABEL maintainer="PRODATA TAPUI Ltd." \
#	description="Centos image with Python build"

## ADD http://download.opensuse.org/repositories/security://shibboleth/CentOS_7/security:shibboleth.repo /etc/yum.repos.d/shibboleth.repo

#RUN --mount=type=bind,from=sources,source=/,target=/sources \
#    --mount=type=bind,from=gcc,source=/,target=/gcc_build \
#    test -n "${http_proxy}" && export ftp_proxy=$http_proxy https_proxy=$http_proxy \
#    && yum -y install \
#        bzip2 lzma xz-devel \
#        openssl11 openssl11-lib openssl11-devel \
#        ncurses-devel libuuid-devel \
#    && echo $'Installing GCC 12.2...' \
#    && cd /gcc_build/gcc-12.2.0 \
#    && make install ; cd $HOME ; hash -r \


#    # && echo $'Building Python 3.11...' \
#    # && tar xf /sources/Python-3.11.2.tar.xz \
#    # && cd Python-3.11.2 \
#    && export \
#        CFLAGS="$CFLAGS $(pkg-config --cflags openssl11)" \
#        LDFLAGS="$LDFLAGS $(pkg-config --libs openssl11)" \
#        LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib \
#    # && ./configure --enable-optimizations --enable-shared \
#    # && make && make install ; cd $HOME ; hash -r \
#    # && python3.11 -m ensurepip --upgrade \

##     && python3.11 -m pip install -U pip ; hash -r \
##     && yum -y install git httpd-devel \
##     && echo $'RPMs installed...' \
##     && echo $'/usr/local/lib\n' > /etc/ld.so.conf.d/local.conf \
##     && pip install -U mod_wsgi psycopg2-binary \
##     && /usr/local/bin/mod_wsgi-express module-config >/etc/httpd/conf.modules.d/10-wsgi.conf \
##     &&  mkdir -p /var/run/lock \
##     &&  mkdir -p /var/lock/subsys/ \
##     && echo $'export LD_LIBRARY_PATH=/usr/local/lib:/opt/shibboleth/lib64:$LD_LIBRARY_PATH\n' > /etc/sysconfig/shibd \
##     && yum erase -y \
##         alsa-lib \
##         apr-util-devel \
##         copy-jdk-configs \
##         cpp \
##         cyrus-sasl-devel \
##         expat-devel \
##         fontconfig \
##         fontpackages-filesystem \
##         freetype \
##         gcc \
##         giflib \
##         git \
##         glibc-devel \
##         glibc-headers \
##         httpd-devel \
##         javapackages-tools \
##         kernel-headers \
##         libdb-devel \
##         libfontenc \
##         libICE \
##         libjpeg-turbo \
##         libpng \
##         libSM \
##         libX11 \
##         libX11-common \
##         libXau \
##         libxcb \
##         libXcomposite \
##         libXext \
##         libXfont \
##         libXi \
##         libXrender \
##         libxslt \
##         libXtst \
##         lksctp-tools \
##         openldap-devel \
##         perl \
##         python36-devel \
##         python36-pip \
##         python-javapackages \
##         python-lxml \
##         ttmkfdir \
##         xorg-x11-fonts-Type1 \
##         xorg-x11-font-utils \
##         java-1.8.0-openjdk-headless \
##         tzdata-java \
##     && chmod -f +x /usr/local/bin/run-app \
##     && cd /var/lib/rpm \
##     && rm -rf __db* \
##     && rpm --rebuilddb \
##     && yum -y clean all \
##     && chmod -f +x /etc/shibboleth/shibd-redhat \
##     && rm -rf /var/cache/yum \
##     && rm -rf $HOME/.pip/cache \
##     && rm -rf /var/cache/*/* /anaconda-post.log \
##     && rm -rf /requirements.txt /swagger_client.egg-info /setup.* /orcid_*


#FROM centos as orcidhub
#ENV LANG=en_US.UTF-8

#LABEL maintainer="PRODATA TAPUI Ltd." \
#	description="NZ ORCiD Hub Application Image with Development support"

## fix download.opensuse.org not available
###RUN sed -i 's|download|downloadcontent|g' /etc/yum.repos.d/shibboleth.repo
#COPY conf/app.wsgi /var/www/html/
## prefix "ZZ" added, that it gest inluded the very end (after Shibboleth gets loaded)
#COPY conf/app.conf /etc/httpd/conf.d/ZZ-app.conf
#COPY requirements.txt /
## COPY setup.py /
## COPY orcid_api /orcid_api
## COPY orcid_hub /orcid_hub
#COPY setup.* orcid* /
#COPY run-app /usr/local/bin/
#COPY ./conf /conf

## && chmod -f +x /etc/sysconfig/shibd /etc/shibboleth/shibd-redhat \
## RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm \
#RUN --mount=type=bind,from=runtime,source=/,target=/runtime yum -y install \
#        gcc \
#        bzip2 \
#        lzma xz-devel \
#        openssl11 openssl11-lib openssl11-devel \
#        ncurses-devel \
#        libuuid-devel \
#        shibboleth.x86_64 \
#    	httpd \
#        mod_ssl \
#    && echo $'Installing GCC 12.2...' \
#    && tar xf /sources/gcc-12.2.0.tar.gz \
#    && cd gcc-12.2.0 \
#    && ./contrib/download_prerequisites \
#    && ./configure --disable-multilib --enable-languages=c,c++ \
#    && make -j 4 && make install ; cd $HOME ; hash -r \
#    && echo $'Installing Python 3.11...' \
#    && tar xf /sources/Python-3.11.2.tar.xz \
#    && cd Python-3.11.2 \
#    && export \
#        CFLAGS="$CFLAGS $(pkg-config --cflags openssl11)" \
#        LDFLAGS="$LDFLAGS $(pkg-config --libs openssl11)" \
#        LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib \
#    && ./configure --enable-optimizations --enable-shared \
#    && make && make install ; cd $HOME ; hash -r \
#    && python3.11 -m ensurepip --upgrade \
#    && python3.11 -m pip install -U pip ; hash -r \
#    && yum -y install git httpd-devel \
#    && echo $'RPMs installed...' \
#    && echo $'/usr/local/lib\n' > /etc/ld.so.conf.d/local.conf \
#    && pip install -U mod_wsgi psycopg2-binary \
#    && pip install -U -r requirements.txt \
#    && /usr/local/bin/mod_wsgi-express module-config >/etc/httpd/conf.modules.d/10-wsgi.conf \
#    && [ -d /var/run/lock ] || mkdir -p /var/run/lock \
#    && [ -d /var/lock/subsys/ ] || mkdir -p /var/lock/subsys/ \
#    && echo $'export LD_LIBRARY_PATH=/usr/local/lib:/opt/shibboleth/lib64:$LD_LIBRARY_PATH\n' > /etc/sysconfig/shibd \
#    && yum erase -y \
#        alsa-lib \
#        apr-util-devel \
#        copy-jdk-configs \
#        cpp \
#        cyrus-sasl-devel \
#        expat-devel \
#        fontconfig \
#        fontpackages-filesystem \
#        freetype \
#        gcc \
#        giflib \
#        git \
#        glibc-devel \
#        glibc-headers \
#        httpd-devel \
#        javapackages-tools \
#        kernel-headers \
#        libdb-devel \
#        libfontenc \
#        libICE \
#        libjpeg-turbo \
#        libpng \
#        libSM \
#        libX11 \
#        libX11-common \
#        libXau \
#        libxcb \
#        libXcomposite \
#        libXext \
#        libXfont \
#        libXi \
#        libXrender \
#        libxslt \
#        libXtst \
#        lksctp-tools \
#        openldap-devel \
#        perl \
#        python36-devel \
#        python36-pip \
#        python-javapackages \
#        python-lxml \
#        ttmkfdir \
#        xorg-x11-fonts-Type1 \
#        xorg-x11-font-utils \
#        java-1.8.0-openjdk-headless \
#        tzdata-java \
#    && chmod -f +x /usr/local/bin/run-app \
#    && cd /var/lib/rpm \
#    && rm -rf __db* \
#    && rpm --rebuilddb \
#    && yum -y clean all \
#    && chmod -f +x /etc/shibboleth/shibd-redhat \
#    && rm -rf /var/cache/yum \
#    && rm -rf $HOME/.pip/cache \
#    && rm -rf /var/cache/*/* /anaconda-post.log \
#    && rm -rf /requirements.txt /swagger_client.egg-info /setup.* /orcid_*


EXPOSE 80 443

CMD ["run-app"]
