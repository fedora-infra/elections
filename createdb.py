import __main__
__main__.__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

from fedora_elections import db
db.create_all()
