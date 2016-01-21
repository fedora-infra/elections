# -*- coding: utf-8 -*-

import fedora_elections

from fedora.client import AuthError


def build_name_map(election):
    """ Returns a mapping of candidate ids to fas human_names. """
    if not election.candidates_are_fasusers:
        return {}

    return dict([
        (str(candidate.id), candidate.fas_name)
        for candidate in election.candidates
    ])
