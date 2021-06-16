Fedora Elections
================

`fedora-elections` is a web application written in Python and based on Flask.
It implements the [Range Voting system](http://rangevoting.org "Center for Range Voting").

This project was developed using Fedora Project requests but can be easily
adapted to other projects. Fedora Elections is integrated with the Fedora
Account System (FAS).


## Creating a development environment

To work on the Fedora Elections web application, you will need to create a
development environment to test your changes. This is simplified by using
[Vagrant](https://www.vagrantup.com/ "Vagrant by Hashicorp"), a powerful and
useful tool for creating development environments on your workstation.


### Using Vagrant

You can quickly start hacking on the Fedora Elections web application using the
Vagrant setup included in the elections repo is super simple.

First, install Vagrant, the `vagrant-libvirt` plugin, and the `vagrant-sshfs`
plugin from the official Fedora repos:

```
sudo dnf install vagrant vagrant-libvirt vagrant-sshfs
```

Now, from the main directory (the one with the `Vagrantfile` in it), run the
`vagrant up` command to provision your development environment:

```
vagrant up
```

When completed, you will be able to SSH into your development virtual machine
with `vagrant ssh` and run the command to start the Fedora Elections server:

```
vagrant ssh
[vagrant@localhost ~]$ pushd /vagrant/; ./runserver.py --host "0.0.0.0";
```

Once that is running, go to [localhost:5005](http://localhost:5005/) in your
browser to see your running Fedora Elections test instance.


### A note about fonts

Fedora Elections uses web fonts hosted in Fedora's infrastructure that might
not work when hacking locally due to CORS restrictions. If you install the
fonts yourself, the Fedora Elections website will look the same as it would
when deployed to production.

You can install the fonts with this command.

```
sudo dnf install open-sans-fonts
```

### A note about the git branches

You will find different git branches in the git repository of elections, here is
a short description of what they are meant for.

Elections originally followed the [git flow](https://nvie.com/posts/a-successful-git-branching-model/)
development model before moving to being deployed in OpenShift using s2i (source
to image) in a more continuous deployment model. You will find traces of these
different models in the git branches.

* ``develop``: this is the default branch of the project, the one you are
  checked out on when you clone the repository. This is the place where all the
  development happens. Your **Pull-Requests should target this branch**.
* ``master``: this is the branch in which ``develop`` is merged into when a new
  release is made. So you will find ``master`` the lastest stable release
  basically.
* ``staging``: this is the branch from which the staging instance of elections
  is being deployed. That branch contains a few commits that are not in
  ``develop`` as they relate to making elections be easily deployable in
  openshift via s2i. These changes are not code related and thus do not need to
  be present in ``develop``. This branch is rebased on the top of ``develop`` and
  force-pushed when staging is being updated.
  Your Pull-Request should not target this branch.
* ``production``: similarly to the ``staging`` branch above, this is the branch
  the production instance of election is being deployed from. Here as well it
  contains a few extra commits that are related to configuring elections for
  openshift/s2i, and here as well the branch is rebased, on the top of
  ``staging`` and force-pushed when production is being updated.
  Your Pull-Request should not target this branch.

## How to launch Fedora Elections

The following steps will get the rest of the application running. Make sure to
use your Vagrant development environment when following these steps.

### Prerequisites

Before launching fedora-elections, the following packages should be installed:

* `httpd`
* `libxslt`
* `python`
* `python-backports-ssl_match_hostname`
* `python-bunch`
* `python-chardet`
* `python-fedora`
* `python-fedora-flask`
* `python-flask`
* `python-flask-sqlalchemy`
* `python-flask-wtf`
* `python-jinja2`
* `python-kitchen`
* `python-lxml`
* `python-openid`
* `python-ordereddict`
* `python-ordereddict`
* `python-setuptools`
* `python-simplejson`
* `python-six`
* `python-sqlalchemy0.7`
* `python-urllib3`
* `python-wtforms`

### Get the source code

This project is hosted on [Pagure](https://pagure.io/elections "Fedora Infrastructure Elections application").
For convenience, a mirror is also hosted on [GitHub](https://github.com/fedora-infra/elections "fedora-infra/elections: Fedora Infrastructure Elections application").

You can obtain the code via:

```
git clone https://pagure.io/elections.git
```

### Install pip requirements w/ tox for testing

Set up venv (replacing `<base_path_for_venv>` and `<venv_name>`):

```
pip install --user virtualenv tox
mkvirtualenv <base_path_for_venv>/<venv_name>
. <base_path_for_venv>/<venv_name>
```

Install requirements:

```
pip install -r requirements.txt
```

### Configure the application

An example configuration file is provided [here](https://pagure.io/elections/blob/master/f/files/fedora-elections.cfg "files/fedora-elections.cfg").

### Register the application using openid-connect

From root of project, run:

```
oidc-register https://iddev.fedorainfracloud.org/ http://localhost:5005
```

### Create database

Run:

```
python createdb.py
```

### Create a local configuration file

Run:

```
cat > config <<EOL
OIDC_ID_TOKEN_COOKIE_SECURE = False
OIDC_REQUIRE_VERIFIED_EMAIL = False
EOL
```


### Starting the app

There are 2 ways to start the application:

* Without Apache
* With Apache

#### Without Apache

This is useful for a quick development instance, when you don't have to worry
about security yet. Do not run this in production. The server will start on
http://127.0.0.1:5005.

```
./runserver.py -c config
```

#### With Apache

Copy `fedora-elections.conf` to your Apache conf.d directory:

```
sudo cp files/fedora-elections.conf /etc/httpd/conf.d/.
```

Next, place `fedora-elections.wsgi` in `/var/www`:

```
sudo cp files/fedora-elections.wsgi /var/www
```

Adjust the Apache configuration file to point to your web directory. Then,
adjust the `.wsgi` file in `/var/www` to point to the `fedora_elections`
directory.

Place the configuration file in `/etc/fedora-elections/fedora-elections.cfg`
and adjust it as you wish.

```
sudo mkdir -p /etc/fedora-elections/
sudo cp files/fedora-elections.cfg /etc/fedora-elections/
```

Now, restart Apache:

```
sudo systemctl restart httpd
```


### Running tests
fedora-elections uses `tox` to simplify testing, and support testing across multiple environments.

Refer to earlier in this section on "How to launch Fedora Elections" in this document to get set up with `tox`

To run tests, simply run:

```
tox
```


## How to contribute

As mentioned earlier, this project is primarily hosted on [Pagure](https://pagure.io/elections "Fedora Infrastructure Elections application").
There is a mirror on [GitHub](https://github.com/fedora-infra/elections "fedora-infra/elections: Fedora Infrastructure Elections application"),
but only for convenience. Pagure is the preferred platform for accepting
contributions. To file an issue, RFE, or other ticket, you must use Pagure. See
other issues already filed [here](https://pagure.io/elections/issues).

If you are interested in working on this project, ask in `#fedora-admin`
on irc.libera.chat or say hello on the [Fedora Infrastructure mailing list](https://lists.fedoraproject.org/admin/lists/infrastructure@lists.fedoraproject.org/).


## License

fedora-elections is licensed under the GPLv2.
