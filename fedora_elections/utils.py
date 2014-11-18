import fedora_elections

from fedora.client import AuthError


def build_name_map(election):
    """ Returns a mapping of candidate ids to fas human_names. """
    if not election.candidates_are_fasusers:
        return {}

    return dict([
        (str(candidate.id), get_fas_human_name(candidate.name))
        for candidate in election.candidates
    ])


@fedora_elections.cache.cache_on_arguments()
def get_fas_human_name(username):
    """ Given a fas username, return the fas human_name if possible.

    If the user has their name set to private or they don't exist, we just
    return the given username as a stand-in.
    """
    try:
        return fedora_elections.FAS2.person_by_username(username)['human_name']
    except (KeyError, AuthError), err:
        fedora_elections.APP.logger.debug(err)
        return username
