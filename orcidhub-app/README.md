
## Usage:

1. run container: `docker run --name app nad2000/orcidhub-app` (**NB!** nad2000 will be replaced)
1. find container IP address: `docker inspect --format '{{ .NetworkSettings.IPAddress }}' app`
1. verify it's running: `curl $(docker inspect --format '{{ .NetworkSettings.IPAddress }}' app)`

