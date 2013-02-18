import __main__
__main__.__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

from fedora_elections import app
app.run(host='0.0.0.0', port=80)
