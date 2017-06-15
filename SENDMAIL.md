Enable access to the *sendmail* server from containers on the host. Find and edit **/etc/mail/sendmail.mc** accordingly to make it listen on the docker network and enable the relay:

```
DAEMON_OPTIONS(`Port=smtp,Addr=172.18.0.1, Name=MTA')dnl
FEATURE(`relay_based_on_MX')dnl
```

