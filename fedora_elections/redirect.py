import flask

from urlparse import urljoin, urlparse


def is_safe_url(target):
    ref_url = urlparse(flask.request.host_url)
    test_url = urlparse(urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def safe_redirect_back(next=None, fallback=('index', {})):
    targets = []
    if next:
        targets.append(next)
    if 'next' in flask.request.args and \
       flask.request.args['next']:
        targets.append(flask.request.args['next'])
    targets.append(flask.url_for(fallback[0], **fallback[1]))
    for target in targets:
        if is_safe_url(target):
            return flask.redirect(target)
