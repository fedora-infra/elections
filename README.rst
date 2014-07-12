================
Fedora Elections
================

* What is fedora-election?

fedora-elections is a web application written in python and based on flask.
It implements the Range Voting system (http://rangevoting.org).

This project was developed using fedoraproject requests, but, can be easily
adapted to other projects.  Fedora-elections is integrated with the Fedora
Account System (FAS).


Running from a checkout:
========================

Install Prerequisites
---------------------
Before launching fedora-elections, the following packages should be installed:
 - httpd
 - libxslt
 - python
 - python-backports-ssl_match_hostname
 - python-bunch
 - python-chardet
 - python-fedora
 - python-fedora-flask
 - python-flask
 - python-flask-sqlalchemy
 - python-flask-wtf
 - python-flask-script
 - python-jinja2
 - python-kitchen
 - python-lxml
 - python-openid
 - python-ordereddict
 - python-ordereddict
 - python-setuptools
 - python-simplejson
 - python-six
 - python-sqlalchemy0.7
 - python-urllib3
 - python-wtforms


Get the source code
-------------------
The project is hosted on https://fedorahosted.org/

More precisely at: https://fedorahosted.org/elections

You can obtain the code via:

  ::

    git clone http://git.fedorahosted.org/git/elections.git

For commodity reason, a clone is available on github:
https://github.com/fedora-infra/elections


Configure the application
-------------------------
An example configuration file is provided at: ``files/fedora-elections.cfg``


Create a database
-----------------
Run:

  ::

      python runserver.py create_database


Starting the Application
------------------------

There are 2 ways to start the application:
   * without apache
   * with apache


* How to start without apache on localhost:5000 (useful for development):

   ::

    python runserver.py run


* How to start with http

  Next copy the file ``fedora-elections.conf`` file to your apache conf.d
  directory:

    ::

      sudo cp files/fedora-elections.conf /etc/httpd/conf.d/.

  Place the file ``fedora-elections.wsgi`` for example in /var/www

  ::

      sudo cp files/fedora-elections.wsgi /var/www

  Adjust the apache configuration file to point to it

  Adjust the wsgi file installed in /var/www to point to fedora_elections


  Place the fedora-elections configuration file in
  ``/etc/fedora-elections/fedora-elections.cfg``

  ::

    sudo mkdir -p /etc/fedora-elections/
    sudo cp files/fedora-elections.cfg /etc/fedora-elections/

  Restart apache:

    sudo /etc/init.d/httpd  restart

* How to contribute

If you find bug or want to propose ideas or stuff to be implemented or if
you are interested to became a developer for this project just
ask on #fedora-admin irc channel on irc.freenode.net or use our
web site https://fedorahosted.org/elections.

* Licence

fedora-elections is licenced under GPL v2.
