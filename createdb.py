from fedora_elections import APP
from fedora_elections.models import create_tables

create_tables(APP.config["DB_URL"], debug=True)
