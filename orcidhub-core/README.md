Steps to execute this application
-------------

If you are running this application for the first time then follow steps a to d:
	a) From the project directory run pip install -r requirement.txt
	b) install run install_package.sh to install postgress and required libraries
	c) Create database and user in postgres
	
> - CREATE USER orcidhub WITH PASSWORD '*****';
> - CREATE DATABASE orcidhub;
> - GRANT ALL PRIVILEGES ON DATABASE orcidhub to orcidhub;.


d) Run initializedb.py to create table in postgres

Run application.py
Open link http://127.0.0.1:5000/orcidhub/index2
