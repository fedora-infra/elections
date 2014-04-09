import __main__
__main__.__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

from fedora_elections import APP
from fedora_elections.models import create_tables
create_tables(APP.config['DB_URL'], debug=True)
