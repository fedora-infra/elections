Documentation

* What is fedora-election?
fedora-elections is a web application written in python and based on 
TurboGears which aim to help to make decisions where is necessary to 
give a preferences. 
This project is developed over fedoraproject requests, but, 
can be easily adapt to be used from any other association/project.
Fedora-elections is integrated with Fedora Account System (FAS) and
provides an agile and easy interface to make decision using votes.


* Installation
You can get files by svn repository. You need a valid FAS account in
particular you need to upload your ssh public key because svn require 
authentication also to checkout/update.

Before launch fedora-elections, you need this packages installed on your 
machine:
 - postgresql-server
 - TurboGears
 - CherryPy
 - python-fedora (you need to enable fedora testing-updates repository)

Before start fedora elections you need to set-up property your database.

Copy your dev-dist.cfg to dev.cfg and start to edit it. This is your 
development configuration file. prod.cfg is your Production configuration
file.

 - sqlite
SQLite is useful to quick start because doesn't need any type of
configuration.
You have just to edit dev.cfg and make sure you have a line like this:
	
	sqlalchemy.dburi="sqlite://path_of_your_database"

 - PostgreSQL
First of all you need to create and configure an user and database 
and give permission on it.

su - postgres 
createuse felections
createdb -O felections felections
psql felections felection < /path/to/election/trunk/elections.sql

(don't forget to edit your pg_sql.conf data and assign to felections on 
your host)

* How to start
Fedora-elections can be started by running the 
start-elections.py script.


* How to contribute
If you find bug or want to propose ideas or stuff to be implemented or if 
you are interested to became a developer for this project just
ask on #fedora-admin irc channel on irc.freenode.net or use our
web site https://fedorahosted.org/elections.

* Licence
fedora-elections is licenced under GPL v2.


