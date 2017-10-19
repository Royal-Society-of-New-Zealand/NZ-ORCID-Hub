FROM centos:centos7

LABEL maintainer="The University of Auckland" \
	version="2.1" \
	description="NZ ORCiD Hub Application Image with Development support"

ADD http://download.opensuse.org/repositories/security://shibboleth/CentOS_7/security:shibboleth.repo /etc/yum.repos.d/shibboleth.repo
ADD http://repo1.maven.org/maven2/io/swagger/swagger-codegen-cli/2.2.2/swagger-codegen-cli-2.2.2.jar swagger-codegen-cli.jar
ADD https://api.orcid.org/resources/swagger.json /orcid/swagger.json

COPY conf/app.wsgi /var/www/html/
# prefix "ZZ" added, that it gest inluded the very end (after Shibboleth gets loaded)
COPY conf/app.conf /etc/httpd/conf.d/ZZ-app.conf
COPY requirements.txt /requirements.txt
COPY run-app /usr/local/bin/
COPY ./conf /conf

RUN yum -y update \ 
    && yum -y install https://centos7.iuscommunity.org/ius-release.rpm \
    && yum -y install \
        java \
    	shibboleth.x86_64 \
    	httpd \
	mod_ssl \
    	gcc.x86_64 \
        httpd-devel.x86_64 \
	python36u.x86_64 \
	python36u-devel.x86_64 \
	python36u-pip \
    && pip3.6 install mod_wsgi psycopg2 \
    && pip3.6 install -r /requirements.txt \
    && sed -i 's/"PUBLIC" ]/"PUBLIC", "PRIVATE" ]/g' /orcid/swagger.json \
    && java -jar swagger-codegen-cli.jar generate -l python -i /orcid/swagger.json -o orcid \
    && sed -i '597 s#return parse(string)#return datetime.fromtimestamp(float(string)/1000)#' orcid/swagger_client/api_client.py \
    && sed -i '596 s#from dateutil.parser import parse#from datetime import datetime#' orcid/swagger_client/api_client.py \
    && cd orcid \
    && python3.6 setup.py install \
    && rm -f /requirements.txt \
    && /usr/bin/mod_wsgi-express module-config >/etc/httpd/conf.modules.d/10-wsgi.conf \
    && [ -d /var/run/lock ] || mkdir -p /var/run/lock \
    && [ -d /var/lock/subsys/ ] || mkdir -p /var/lock/subsys/ \
    && echo $'export LD_LIBRARY_PATH=/opt/shibboleth/lib64:$LD_LIBRARY_PATH\n' > /etc/sysconfig/shibd \
    && chmod +x /etc/sysconfig/shibd /etc/shibboleth/shibd-redhat \
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
	glibc-devel \
	glibc-headers \
	httpd-devel \
	java-1.8.0-openjdk-headless \
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
	python36u-devel \
	python36u-pip \
	python-javapackages \
	python-lxml \
	ttmkfdir \
	tzdata-java \
	xorg-x11-fonts-Type1 \
	xorg-x11-font-utils \
    && chmod +x /usr/local/bin/run-app \
    && cd /var/lib/rpm \
    && rm -rf __db* \
    && rpm --rebuilddb \
    && yum -y clean all \
    && rm -rf /var/cache/yum \
    && rm -rf $HOME/.pip/cache \
    && rm -rf /var/cache/*/* /anaconda-post.log \
    && rm -f /swagger-codegen-cli.jar /orcid_swagger.json \
    && rm -rf /swagger_client.egg-info /orcid


EXPOSE 80 443

CMD ["run-app"]
