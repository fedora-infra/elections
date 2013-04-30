Name:           fedora-elections
Version:        0.1
Release:        1%{?dist}
Summary:        Fedora elections application

Group:          Development/Languages
License:        GPLv2+
URL:            https://github.com/fedora-infra/elections
Source0:        https://fedorahosted.org/releases/f/a/%{name}/%{name}-%{version}.tar.gz


BuildArch:      noarch

BuildRequires:  python
BuildRequires:  python-devel
BuildRequires:  python-beaker
BuildRequires:  python-fedora
BuildRequires:  python-fedora-flask
BuildRequires:  python-flask
BuildRequires:  python-flask-babel
BuildRequires:  python-flask-sqlalchemy
BuildRequires:  python-flask-wtforms
BuildRequires:  python-kitchen
BuildRequires:  python-setuptools
BuildRequires:  python-setuptools-devel
BuildRequires:  python-sqlalchemy0.7

Requires:       python-beaker
Requires:       python-fedora
Requires:       python-fedora-flask
Requires:       python-flask
Requires:       python-flask-babel
Requires:       python-flask-sqlalchemy
Requires:       python-flask-wtforms
Requires:       python-jinja2
Requires:       python-kitchen
Requires:       python-sqlalchemy0.7


%description
fedora-elections is the Fedora Elections application.

%prep
%setup -q


%build
# Remove CFLAGS=... for noarch packages (unneeded)
CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --install-data=%{_datadir} --root $RPM_BUILD_ROOT

%{__mkdir_p} %{buildroot}%{_sysconfdir}/%{name}
%{__mkdir_p} %{buildroot}%{_sysconfdir}/httpd/conf.d
%{__mkdir_p} %{buildroot}%{_datadir}/%{name}
%{__mkdir_p} %{buildroot}%{_datadir}/%{name}/static

%{__install} -m 644 fedora_elections.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/fedora_elections.conf
%{__install} -m 644 fedora_elections/static/* %{buildroot}%{_datadir}/%{name}/static
%{__install} -m 644 %{name}.cfg.sample %{buildroot}%{_sysconfdir}/%{name}/%{name}.cfg
%{__install} -m 644 createdb.py %{buildroot}%{_datadir}/%{name}/createdb.py
%{__install} -m 644 %{name}.wsgi %{buildroot}%{_datadir}/%{name}/%{name}.wsgi



%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.cfg
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%{_datadir}/%{name}
%{python_sitelib}/*


%changelog
* Wed Mar 06 2013 Frank Chiulli <fchiulli@fedoraproject.org> - 0.1
- Creation
