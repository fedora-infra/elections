sudo cp -v files/fedora-elections.conf /etc/httpd/conf.d/.
cp files/fedora-elections.wsgi /var/www
mkdir -pv /etc/fedora-elections/
cp -v files/fedora-elections.cfg /etc/fedora-elections/