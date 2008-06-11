%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?pyver: %define pyver %(%{__python} -c "import sys ; print sys.version[:3]")}

Name:           fedora-elections
Version:        0.1.0
Release:        1%{?dist}
Summary:        Elections Application for Fedora Project

Group:          Development/Languages
License:        GPLv2
URL:            http://www.fedorahosted.org/elections
Source0:        elections-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch

BuildRequires:  python-devel python-setuptools-devel TurboGears
Requires:       TurboGears >= 1.0.4
Requires:       python-sqlalchemy >= 0.4
Requires:       python-fedora >= 0.2.99.10
Requires:       python-genshi

%description
Fedora Elections is a web application designed to process and run elections
for the Fedora Project built with TurboGears.

%prep
%setup -q -n elections-%{version}


%build
%{__python} setup.py build --install-data='%{_datadir}' --install-conf='%{_sysconfdir}'

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --install-data='%{_datadir}' --install-conf='%{_sysconfdir}' --root %{buildroot}
%{__mkdir_p} %{buildroot}%{_sbindir}
%{__mv} %{buildroot}%{_bindir}/start-elections %{buildroot}%{_sbindir}
%{__cp} examples/elections.wsgi %{buildroot}%{_datadir}/elections/

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc COPYING elections.sql
%{_datadir}/elections/
%{_sbindir}/*
%attr(640,root,root) %config(noreplace) %{_sysconfdir}/*



%changelog
* Wed Jun 11 2008 Nigel Jones <dev@nigelj.com> - 0.1.0-1
- Ready for initial deployment

* Fri Jun 6 2008 Nigel Jones <dev@nigelj.com> - 0.0.9-1
- Bump

* Thu May 22 2008 Nigel Jones <dev@nigelj.com> - 0.0.5-1
- Initial RPM - Ready to go!
