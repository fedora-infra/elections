This file is for you to describe the elections2 application. Typically
you would include information such as the information below:

Dependencies
============

- TurboGears 2
   tested with:
    - TurboGears2-2.0.3-4.el6
    - TurboGears2-2.1-0.3.rc1.dev1048.fc14
- python-sqlalchemy
   tested with:
    - python-sqlalchemy-0.5.5-2.1.el6
    - python-sqlalchemy-0.6.8-1.fc14
- python-tgext-admin
- python-repoze-what-quickstart
- python-tgext-crud
- python-sprox


Installation and Setup
======================

Install ``elections2`` using the setup.py script::

    $ cd elections2
    $ python setup.py install

Create the egg_info
    $ python setup.py egg_info

Create the project database for any model classes defined::

    $ paster setup-app development.ini

Start the paste http server::

    $ paster serve development.ini

While developing you may want the server to reload after changes in package files (or its dependencies) are saved. This can be achieved easily by adding the --reload option::

    $ paster serve --reload development.ini

Then you are ready to go.
