# syntax=docker/dockerfile:experimental
FROM centos:centos7 AS centos
LABEL maintainer="PRODATA TAPUI Ltd." \
	description="Centos image with Apache and Shiboleth"
# ADD http://download.opensuse.org/repositories/security://shibboleth/CentOS_7/security:shibboleth.repo /etc/yum.repos.d/shibboleth.repo
ADD https://shibboleth.net/cgi-bin/sp_repo.cgi?platform=CentOS_7 /etc/yum.repos.d/shibboleth.repo
RUN yum -y install \
        https://repo.ius.io/ius-release-el7.rpm \
        https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
    && yum -y remove pgdg-redhat-repo-42.0-32 && yum clean all \
    && yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm \
    && yum clean all  \
    && yum -y update \
    && yum -y upgrade \
    && yum -y install \
        bzip2 \
        lzma \
        openssl11 openssl11-lib \
        shibboleth.x86_64 \
    	httpd \
        mod_ssl \
    && yum clean all  \
    && cd /var/lib/rpm \
    && rm -rf __db* \
    && rpm --rebuilddb \
    && yum -y clean all \
    && rm -rf /var/cache/yum \
    && rm -rf $HOME/.pip/cache \
    && rm -rf /var/cache/*/* /anaconda-post.log \
    && rm -rf /requirements.txt /swagger_client.egg-info /setup.* /orcid_*

FROM centos  AS sources
LABEL maintainer="PRODATA TAPUI Ltd." \
	description="Off-line cache of the sources"
RUN echo $'Downloading the sourcs' \
    && curl -O http://ftp.mirrorservice.org/sites/sourceware.org/pub/gcc/releases/gcc-12.2.0/gcc-12.2.0.tar.gz \
    && curl -O https://www.python.org/ftp/python/3.11.2/Python-3.11.2.tar.xz

FROM centos as gcc
ENV LANG=en_US.UTF-8

LABEL maintainer="PRODATA TAPUI Ltd." \
	description="Centos image with the most recetn GCC"

RUN --mount=type=bind,from=sources,source=/,target=/sources yum -y install \
        gcc \
        bzip2 \
        lzma xz-devel \
        openssl11 openssl11-lib openssl11-devel \
        ncurses-devel \
        libuuid-devel \
        shibboleth.x86_64 \
    	httpd \
        mod_ssl \
    && echo $'Installing GCC 12.2...' \
    && tar xf /sources/gcc-12.2.0.tar.gz \
    && cd gcc-12.2.0 \
    && ./contrib/download_prerequisites \
    && ./configure --disable-multilib --enable-languages=c,c++ \
    && make -j 4 && make install ; cd $HOME ; hash -r \
    && echo $'Installing Python 3.11...' \
    && tar xf /sources/Python-3.11.2.tar.xz \
    && cd Python-3.11.2 \
    && export \
        CFLAGS="$CFLAGS $(pkg-config --cflags openssl11)" \
        LDFLAGS="$LDFLAGS $(pkg-config --libs openssl11)" \
        LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib \
    && ./configure --enable-optimizations --enable-shared \
    && make && make install ; cd $HOME ; hash -r \
    && python3.11 -m ensurepip --upgrade \
    && python3.11 -m pip install -U pip ; hash -r \
    && yum -y install git httpd-devel \
    && echo $'RPMs installed...' \
    && echo $'/usr/local/lib\n' > /etc/ld.so.conf.d/local.conf \
    && pip install -U mod_wsgi psycopg2-binary \
    && pip install -U -r requirements.txt \
    && /usr/local/bin/mod_wsgi-express module-config >/etc/httpd/conf.modules.d/10-wsgi.conf \
    && [ -d /var/run/lock ] || mkdir -p /var/run/lock \
    && [ -d /var/lock/subsys/ ] || mkdir -p /var/lock/subsys/ \
    && echo $'export LD_LIBRARY_PATH=/usr/local/lib:/opt/shibboleth/lib64:$LD_LIBRARY_PATH\n' > /etc/sysconfig/shibd \
    && yum erase -y \
        alsa-lib \
        apr-util-devel \
        copy-jdk-configs \
        cpp \
        cyrus-sasl-devel \
        expat-devel \
        fontconfig \
        fontpackages-filesystem \
        freetype \
        gcc \
        giflib \
        git \
        glibc-devel \
        glibc-headers \
        httpd-devel \
        javapackages-tools \
        kernel-headers \
        libdb-devel \
        libfontenc \
        libICE \
        libjpeg-turbo \
        libpng \
        libSM \
        libX11 \
        libX11-common \
        libXau \
        libxcb \
        libXcomposite \
        libXext \
        libXfont \
        libXi \
        libXrender \
        libxslt \
        libXtst \
        lksctp-tools \
        openldap-devel \
        perl \
        python36-devel \
        python36-pip \
        python-javapackages \
        python-lxml \
        ttmkfdir \
        xorg-x11-fonts-Type1 \
        xorg-x11-font-utils \
        java-1.8.0-openjdk-headless \
        tzdata-java \
    && chmod +x /usr/local/bin/run-app \
    && cd /var/lib/rpm \
    && rm -rf __db* \
    && rpm --rebuilddb \
    && yum -y clean all \
    && chmod +x /etc/shibboleth/shibd-redhat \
    && rm -rf /var/cache/yum \
    && rm -rf $HOME/.pip/cache \
    && rm -rf /var/cache/*/* /anaconda-post.log \
    && rm -rf /requirements.txt /swagger_client.egg-info /setup.* /orcid_*


FROM centos as runtime
ENV LANG=en_US.UTF-8

LABEL maintainer="PRODATA TAPUI Ltd." \
	description="Centos image with the most recetn GCC, Python, Apache, and "

# ADD http://download.opensuse.org/repositories/security://shibboleth/CentOS_7/security:shibboleth.repo /etc/yum.repos.d/shibboleth.repo
ADD https://shibboleth.net/cgi-bin/sp_repo.cgi?platform=CentOS_7 /etc/yum.repos.d/shibboleth.repo

RUN --mount=type=bind,from=sources,source=/,target=/sources yum -y install \
        gcc \
        bzip2 \
        lzma xz-devel \
        openssl11 openssl11-lib openssl11-devel \
        ncurses-devel \
        libuuid-devel \
        shibboleth.x86_64 \
    	httpd \
        mod_ssl \
    && echo $'Installing GCC 12.2...' \
    && tar xf /sources/gcc-12.2.0.tar.gz \
    && cd gcc-12.2.0 \
    && ./contrib/download_prerequisites \
    && ./configure --disable-multilib --enable-languages=c,c++ \
    && make -j 4 && make install ; cd $HOME ; hash -r \
    && echo $'Installing Python 3.11...' \
    && tar xf /sources/Python-3.11.2.tar.xz \
    && cd Python-3.11.2 \
    && export \
        CFLAGS="$CFLAGS $(pkg-config --cflags openssl11)" \
        LDFLAGS="$LDFLAGS $(pkg-config --libs openssl11)" \
        LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib \
    && ./configure --enable-optimizations --enable-shared \
    && make && make install ; cd $HOME ; hash -r \
    && python3.11 -m ensurepip --upgrade \
    && python3.11 -m pip install -U pip ; hash -r \
    && yum -y install git httpd-devel \
    && echo $'RPMs installed...' \
    && echo $'/usr/local/lib\n' > /etc/ld.so.conf.d/local.conf \
    && pip install -U mod_wsgi psycopg2-binary \
    && pip install -U -r requirements.txt \
    && /usr/local/bin/mod_wsgi-express module-config >/etc/httpd/conf.modules.d/10-wsgi.conf \
    && [ -d /var/run/lock ] || mkdir -p /var/run/lock \
    && [ -d /var/lock/subsys/ ] || mkdir -p /var/lock/subsys/ \
    && echo $'export LD_LIBRARY_PATH=/usr/local/lib:/opt/shibboleth/lib64:$LD_LIBRARY_PATH\n' > /etc/sysconfig/shibd \
    && yum erase -y \
        alsa-lib \
        apr-util-devel \
        copy-jdk-configs \
        cpp \
        cyrus-sasl-devel \
        expat-devel \
        fontconfig \
        fontpackages-filesystem \
        freetype \
        gcc \
        giflib \
        git \
        glibc-devel \
        glibc-headers \
        httpd-devel \
        javapackages-tools \
        kernel-headers \
        libdb-devel \
        libfontenc \
        libICE \
        libjpeg-turbo \
        libpng \
        libSM \
        libX11 \
        libX11-common \
        libXau \
        libxcb \
        libXcomposite \
        libXext \
        libXfont \
        libXi \
        libXrender \
        libxslt \
        libXtst \
        lksctp-tools \
        openldap-devel \
        perl \
        python36-devel \
        python36-pip \
        python-javapackages \
        python-lxml \
        ttmkfdir \
        xorg-x11-fonts-Type1 \
        xorg-x11-font-utils \
        java-1.8.0-openjdk-headless \
        tzdata-java \
    && chmod +x /usr/local/bin/run-app \
    && cd /var/lib/rpm \
    && rm -rf __db* \
    && rpm --rebuilddb \
    && yum -y clean all \
    && chmod +x /etc/shibboleth/shibd-redhat \
    && rm -rf /var/cache/yum \
    && rm -rf $HOME/.pip/cache \
    && rm -rf /var/cache/*/* /anaconda-post.log \
    && rm -rf /requirements.txt /swagger_client.egg-info /setup.* /orcid_*


FROM centos as orcidhub
ENV LANG=en_US.UTF-8

LABEL maintainer="PRODATA TAPUI Ltd." \
	description="NZ ORCiD Hub Application Image with Development support"

# fix download.opensuse.org not available
##RUN sed -i 's|download|downloadcontent|g' /etc/yum.repos.d/shibboleth.repo
COPY conf/app.wsgi /var/www/html/
# prefix "ZZ" added, that it gest inluded the very end (after Shibboleth gets loaded)
COPY conf/app.conf /etc/httpd/conf.d/ZZ-app.conf
COPY requirements.txt /
# COPY setup.py /
# COPY orcid_api /orcid_api
# COPY orcid_hub /orcid_hub
COPY setup.* orcid* /
COPY run-app /usr/local/bin/
COPY ./conf /conf

# && chmod +x /etc/sysconfig/shibd /etc/shibboleth/shibd-redhat \
# RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm \
RUN --mount=type=bind,from=runtime,source=/,target=/runtime yum -y install \
        gcc \
        bzip2 \
        lzma xz-devel \
        openssl11 openssl11-lib openssl11-devel \
        ncurses-devel \
        libuuid-devel \
        shibboleth.x86_64 \
    	httpd \
        mod_ssl \
    && echo $'Installing GCC 12.2...' \
    && tar xf /sources/gcc-12.2.0.tar.gz \
    && cd gcc-12.2.0 \
    && ./contrib/download_prerequisites \
    && ./configure --disable-multilib --enable-languages=c,c++ \
    && make -j 4 && make install ; cd $HOME ; hash -r \
    && echo $'Installing Python 3.11...' \
    && tar xf /sources/Python-3.11.2.tar.xz \
    && cd Python-3.11.2 \
    && export \
        CFLAGS="$CFLAGS $(pkg-config --cflags openssl11)" \
        LDFLAGS="$LDFLAGS $(pkg-config --libs openssl11)" \
        LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib \
    && ./configure --enable-optimizations --enable-shared \
    && make && make install ; cd $HOME ; hash -r \
    && python3.11 -m ensurepip --upgrade \
    && python3.11 -m pip install -U pip ; hash -r \
    && yum -y install git httpd-devel \
    && echo $'RPMs installed...' \
    && echo $'/usr/local/lib\n' > /etc/ld.so.conf.d/local.conf \
    && pip install -U mod_wsgi psycopg2-binary \
    && pip install -U -r requirements.txt \
    && /usr/local/bin/mod_wsgi-express module-config >/etc/httpd/conf.modules.d/10-wsgi.conf \
    && [ -d /var/run/lock ] || mkdir -p /var/run/lock \
    && [ -d /var/lock/subsys/ ] || mkdir -p /var/lock/subsys/ \
    && echo $'export LD_LIBRARY_PATH=/usr/local/lib:/opt/shibboleth/lib64:$LD_LIBRARY_PATH\n' > /etc/sysconfig/shibd \
    && yum erase -y \
        alsa-lib \
        apr-util-devel \
        copy-jdk-configs \
        cpp \
        cyrus-sasl-devel \
        expat-devel \
        fontconfig \
        fontpackages-filesystem \
        freetype \
        gcc \
        giflib \
        git \
        glibc-devel \
        glibc-headers \
        httpd-devel \
        javapackages-tools \
        kernel-headers \
        libdb-devel \
        libfontenc \
        libICE \
        libjpeg-turbo \
        libpng \
        libSM \
        libX11 \
        libX11-common \
        libXau \
        libxcb \
        libXcomposite \
        libXext \
        libXfont \
        libXi \
        libXrender \
        libxslt \
        libXtst \
        lksctp-tools \
        openldap-devel \
        perl \
        python36-devel \
        python36-pip \
        python-javapackages \
        python-lxml \
        ttmkfdir \
        xorg-x11-fonts-Type1 \
        xorg-x11-font-utils \
        java-1.8.0-openjdk-headless \
        tzdata-java \
    && chmod +x /usr/local/bin/run-app \
    && cd /var/lib/rpm \
    && rm -rf __db* \
    && rpm --rebuilddb \
    && yum -y clean all \
    && chmod +x /etc/shibboleth/shibd-redhat \
    && rm -rf /var/cache/yum \
    && rm -rf $HOME/.pip/cache \
    && rm -rf /var/cache/*/* /anaconda-post.log \
    && rm -rf /requirements.txt /swagger_client.egg-info /setup.* /orcid_*


EXPOSE 80 443

CMD ["run-app"]
