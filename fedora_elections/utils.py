# -*- coding: utf-8 -*-

import fedora_elections


def build_name_map(election):
    """ Returns a mapping of candidate ids to fas human_names. """
    if not election.candidates_are_fasusers:
        return {}

    return dict([
        (str(candidate.id), candidate.fas_name or candidate.name)
        for candidate in election.candidates
    ])
