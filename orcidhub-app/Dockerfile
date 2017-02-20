FROM nad2000/shibboleth-sp

MAINTAINER The University of Auckland

RUN yum -y update \ 
    && yum -y install https://centos7.iuscommunity.org/ius-release.rpm \
    && yum -y install \
    	gcc.x86_64 \
	httpd-devel.x86_64 \
	python36u.x86_64 \
	python36u-devel.x86_64 \
	python36u-pip \
    && pip3.6 install mod_wsgi \
    && yum -y erase gcc.x86_64 python36u-devel.x86_64 httpd-devel.x86_64 \
    && yum -y clean all \
    && /usr/bin/mod_wsgi-express module-config >/etc/httpd/conf.modules.d/10-wsgi.conf

COPY app.wsgi /var/www/html/
COPY app.conf /etc/httpd/conf.d/

EXPOSE 80 443

CMD ["run-httpd-shibd"]

