## Application Docker Image

Application Docker Image ([orcidhub/app](https://hub.docker.com/r/orcidhub/app/)) is packaged with:
 - CentOS 7
 - Apache 2.4
 - PostreSQL 9.2 Client
 - Python 3.6
 - mod_wsgi (Pythgon/WSGI Apache module)
 - psycopg2 (native PostgreSQL Python DB-API 2.0 driver)
 - PyPI packages necessary for the application

### Usage 

1. run container: `docker run --name app orcidhub/app`
1. find container IP address: `docker inspect --format '{{.NetworkSettings.IPAddress}}' app`
1. verify it's running: `curl $(docker inspect --format '{{.NetworkSettings.IPAddress}}' app)`

## Steps to execute this application

If you are running this application for the first time then follow steps a to d:
	a) From the project directory run pip3 install -r requirement.txt
	b) install run install_package.sh to install postgress and required libraries
	c) Create database and user in postgres
	
> - CREATE USER orcidhub WITH PASSWORD '*****';
> - CREATE DATABASE orcidhub;
> - GRANT ALL PRIVILEGES ON DATABASE orcidhub to orcidhub;.


d) Run initializedb.py to create table in postgres

Run application.py
Open link https://test.orcidhub.org.nz/index
