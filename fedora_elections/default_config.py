# -*- coding: utf-8 -*-

'''
Fedora elections default configuration.
'''
import os
from datetime import timedelta
from fedora_elections.mail_logging import MSG_FORMAT, ContextInjector

# Set the time after which the session expires
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

FEDORA_ELECTIONS_ADMIN_GROUP = 'elections'

# url to the database server:
DB_URL = 'sqlite:////var/tmp/elections_dev.sqlite'


# You will want to change this for your install
SECRET_KEY = 'change me'

FASJSON = False

FAS_BASE_URL = 'https://admin.stg.fedoraproject.org/accounts/'
FAS_USERNAME = ''
FAS_PASSWORD = ''
FAS_CHECK_CERT = False


OIDC_CLIENT_SECRETS = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'client_secrets.json')
OIDC_SCOPES = ['openid', 'email', 'profile', 'https://id.fedoraproject.org/scope/groups', 'https://id.fedoraproject.org/scope/agreements']
OIDC_OPENID_REALM = 'http://localhost:5005/oidc_callback'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "email_format": {"format": MSG_FORMAT},
    },
    "filters": {"myfilter": {"()": ContextInjector}},
    "handlers": {
        "console": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "email": {
            "level": "ERROR",
            "formatter": "email_format",
            "class": "logging.handlers.SMTPHandler",
            "mailhost": "localhost",
            "fromaddr": "elections@localhost",
            "toaddrs": "elections@localhost",
            "subject": "ERROR on elections",
            "filters": ["myfilter"],
        },
    },
    # The root logger configuration; this is a catch-all configuration
    # that applies to all log messages not handled by a different logger
    "root": {
        "level": "DEBUG",
        "handlers": ["console"]
    },
    "loggers": {
        "fedora_elections": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "flask": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "flask_oidc": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "sqlalchemy": {
            "handlers": ["console"],
            "level": "WARN",
            "propagate": False,
        },
        "fedora_messaging": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "pika": {
            "handlers": ["console"],
            "level": "WARN",
            "propagate": True,
        },
    },
}
