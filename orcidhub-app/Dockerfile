FROM nad2000/shibboleth-sp

MAINTAINER The University of Auckland

RUN yum -y update \ 
    && yum -y install mod_wsgi \
    && yum -y clean all

#COPY run-httpd-shibd /usr/local/bin/

#RUN [ -d /var/run/lock ] || mkdir -p /var/run/lock \
#    && [ -d /var/lock/subsys/ ] || mkdir -p /var/lock/subsys/ \
#    && chmod +x /etc/shibboleth/shibd-redhat \
#    && echo $'export LD_LIBRARY_PATH=/opt/shibboleth/lib64:$LD_LIBRARY_PATH\n'\
#       > /etc/sysconfig/shibd \
#    && chmod +x /etc/sysconfig/shibd /etc/shibboleth/shibd-redhat /usr/local/bin/run-httpd-shibd
#
EXPOSE 80 443

CMD ["run-httpd-shibd"]

