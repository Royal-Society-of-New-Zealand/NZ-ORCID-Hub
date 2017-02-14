FROM centos:centos7

MAINTAINER The University of Auckland

RUN yum -y update \
    && curl http://download.opensuse.org/repositories/security://shibboleth/CentOS_7/security:shibboleth.repo -o /etc/yum.repos.d/shibboleth.repo \
    && yum -y install httpd shibboleth.x86_64 mod_ssl \
    && yum -y clean all

COPY run-httpd-shibd /usr/local/bin/

RUN [ -d /var/run/lock ] || mkdir -p /var/run/lock \
    && [ -d /var/lock/subsys/ ] || mkdir -p /var/lock/subsys/ \
    && chmod +x /etc/shibboleth/shibd-redhat \
    && echo $'export LD_LIBRARY_PATH=/opt/shibboleth/lib64:$LD_LIBRARY_PATH\n'\
       > /etc/sysconfig/shibd \
    && chmod +x /etc/sysconfig/shibd /etc/shibboleth/shibd-redhat /usr/local/bin/run-httpd-shibd

EXPOSE 80 443

CMD ["run-httpd-shibd"]

