Load Testing
============

1. Reset application Apache access log in the application container: `cat /dev/null  > /var/log/httpd/orcidhub_log`;
1. Restart the application: `cat /dev/null  > /var/log/httpd/orcidhub_log`;
1. Start *nmon* on the box under the test and start moninotring CPUs and the memory;
1. Increase Java heap limit: `HEAP="-Xms512m -Xmx4096m"` on the box you will run *jmeter*;
1. Run jmeter test, e.g., `jmeter.sh -n -t simple.jmx`;
1. Retrieve the access log from the applicatio container: `ssh  ec2-user@dev.orcidhub.org.nz 'docker-compose exec -T app cat /var/log/httpd/orcidhub_log' > orcidhub_log`
1. Run *goaccess* to generate a perormance report: `goaccess  orcidhub_log -p goaccessrc.conf  -o report.html`
