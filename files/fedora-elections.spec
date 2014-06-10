%define modname fedora_elections

Name:           fedora-elections
Version:        2.0.2
Release:        1%{?dist}
Summary:        Fedora elections application

Group:          Development/Languages
License:        GPLv2+
URL:            https://github.com/fedora-infra/elections
Source0:        %{name}/%{name}-%{version}.tar.gz
#Source0:        https://fedorahosted.org/releases/f/a/%{name}/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python-fedora
BuildRequires:  python-fedora-flask
BuildRequires:  python-flask-wtf
BuildRequires:  python-kitchen
BuildRequires:  python-openid
BuildRequires:  python-openid-teams
BuildRequires:  python-openid-cla
BuildRequires:  python-setuptools
BuildRequires:  python-wtforms

Requires:       python-fedora
Requires:       python-fedora-flask
Requires:       python-flask-wtf
Requires:       python-kitchen
Requires:       python-openid
Requires:       python-openid-teams
Requires:       python-openid-cla
Requires:       python-wtforms

# EPEL6
%if ( 0%{?rhel} && 0%{?rhel} == 6 )
BuildRequires:  python-sqlalchemy0.7
Requires:  python-sqlalchemy0.7
%else
BuildRequires:  python-sqlalchemy > 0.5
Requires:  python-sqlalchemy > 0.5
%endif


%description
fedora-elections is the Fedora Elections application.

%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT


# Install apache configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/
install -m 644 files/fedora-elections.conf \
  $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/fedora-elections.conf

# Install configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/fedora-elections
install -m 644 files/fedora-elections.cfg \
  $RPM_BUILD_ROOT/%{_sysconfdir}/fedora-elections/fedora-elections.cfg

# Install WSGI file
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/fedora-elections
install -m 644 files/fedora-elections.wsgi \
  $RPM_BUILD_ROOT/%{_datadir}/fedora-elections/fedora-elections.wsgi

# Install the createdb script
install -m 644 createdb.py \
  $RPM_BUILD_ROOT/%{_datadir}/fedora-elections/fedora-elections_createdb.py

# Install the alembic configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/fedora-elections
install -m 644 files/alembic.ini \
  $RPM_BUILD_ROOT/%{_sysconfdir}/fedora-elections/alembic.ini

# Install the alembic files
cp -r alembic \
  $RPM_BUILD_ROOT/%{_datadir}/fedora-elections/alembic

install -m 644 files/update_1_to_2.sql \
  $RPM_BUILD_ROOT/%{_datadir}/fedora-elections/update_1_to_2.sql



%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.cfg
%config(noreplace) %{_sysconfdir}/%{name}/alembic.ini
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%{python_sitelib}/%{modname}/
%{python_sitelib}/%{modname}*.egg-info/
%{_datadir}/%{name}


%changelog
* Sat May 03 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 2.0.2-1
- Update to 2.0.2
- Fix is_safe_url method, imports were different here

* Sat May 03 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 2.0.1-1
- Update to 2.0.1
- Fix redirection after login

* Wed Apr 09 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 2.0-1
- Clean up the spec with the changes made on the setup.py
- Remove instanciated a sqlite database
- Install the sql upgrade script from elections v1 to elections v2

* Tue Sep 02 2013 Frank Chiulli <fchiulli@fedoraproject.org> - 2-1
- Simple voting

* Sat May 04 2013 Frank Chiulli <fchiulli@fedoraproject.org> - 2-0
- Creation
