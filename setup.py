## These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources


from setuptools import setup, find_packages

setup( name = 'fedora-elections'
     , version = '0.1'
     , author = 'Frank Chiulli'
     , author_email = 'fchiulli@fedoraproject.org'
     , packages = find_packages()
     , zip_safe = False
     , include_package_data = True
     , install_requires = ['Flask', 'SQLAlchemy>=0.7', 'flask-sqlalchemy']
     )
