""" This is a temporary shim that allows fedmsg to be an optional dependency of
elections.  If fedmsg is installed, these function calls will try to actually
send messages.  If it is not installed, it will return silently.

  :Author: Ralph Bean <rbean@redhat.com>

"""

import warnings


def publish(*args, **kwargs):  # pragma: no cover
    try:
        import fedmsg
        fedmsg.publish(*args, **kwargs)
    except Exception, e:
        warnings.warn(str(e))
