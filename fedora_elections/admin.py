# -*- coding: utf-8 -*-
#
# Copyright © 2012  Red Hat, Inc.
# Copyright © 2012  Ian Weller <ianweller@fedoraproject.org>
# Copyright © 2012  Toshio Kuratomi <tkuratom@redhat.com>
# Copyright © 2012  Frank Chiulli <fchiulli@fedoraproject.org>
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2, or (at your option) any later version.  This
# program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the GNU
# General Public License along with this program; if not, write to the Free
# Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA. Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public License and
# may only be used or replicated with the express permission of Red Hat, Inc.
#
# Author(s):        Ian Weller <ianweller@fedoraproject.org>
#                   Toshio Kuratomi <tkuratom@redhat.com>
#                   Frank Chiulli <fchiulli@fedoraproject.org>
#                   Pierre-Yves Chibon <pingou@fedoraproject.org>
#
from __future__ import unicode_literals, absolute_import

from datetime import datetime, time
from functools import wraps

import flask
from sqlalchemy.exc import SQLAlchemyError
from fedora.client import AuthError

from fedora_elections import fedmsgshim
from fedora_elections import forms
from fedora_elections import models
from fedora_elections import (
    APP, SESSION, ACCOUNTS, is_authenticated, is_admin
)
from fasjson_client.errors import APIError


def election_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return flask.redirect(flask.url_for(
                'auth_login', next=flask.request.url))
        if not is_admin(flask.g.fas_user):
            flask.abort(403)
        return f(*args, **kwargs)
    return decorated_function


@APP.route('/admin/new', methods=('GET', 'POST'))
@election_admin_required
def admin_new_election():
    form = forms.ElectionForm()
    if form.validate_on_submit():

        if form.max_votes.data:
            try:
                form.max_votes.data = int(form.max_votes.data)
            except ValueError:
                form.max_votes.data = None
        else:
            form.max_votes.data = None

        election = models.Election(
            shortdesc=form.shortdesc.data,
            alias=form.alias.data,
            description=form.description.data,
            url=form.url.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            seats_elected=form.seats_elected.data,
            embargoed=int(form.embargoed.data),
            url_badge=form.url_badge.data,
            voting_type=form.voting_type.data,
            max_votes=form.max_votes.data,
            candidates_are_fasusers=int(form.candidates_are_fasusers.data),
            fas_user=flask.g.fas_user.username,
        )

        # Fix start_date and end_date to use datetime
        election.start_date = datetime.combine(election.start_date, time())
        election.end_date = datetime.combine(election.end_date,
                                             time(23, 59, 59))
        SESSION.add(election)

        # Add admin groups if there are any
        for admin_grp in form.admin_grp.data.split(','):
            if admin_grp.strip():
                admin = models.ElectionAdminGroup(
                    election=election,
                    group_name=admin_grp.strip(),
                )
                SESSION.add(admin)

        # Add legal voters groups if there are any
        for voter_grp in form.lgl_voters.data.split(','):
            if voter_grp.strip():
                lglvoters = models.LegalVoter(
                    election=election,
                    group_name=voter_grp.strip(),
                )
                SESSION.add(lglvoters)

        SESSION.commit()

        fedmsgshim.publish(
            topic="election.new",
            msg=dict(
                agent=flask.g.fas_user.username,
                election=election.to_json(),
                )
        )

        flask.flash('Election "%s" added' % election.alias)
        return flask.redirect(flask.url_for(
            'admin_view_election', election_alias=election.alias))
    return flask.render_template(
        'admin/election_form.html',
        form=form,
        submit_text='Create election')


@APP.route('/admin/<election_alias>/', methods=('GET', 'POST'))
@election_admin_required
def admin_view_election(election_alias):
    election = models.Election.get(SESSION, alias=election_alias)
    if not election:
        flask.abort(404)
    if flask.request.method == 'GET':
        form = forms.ElectionForm(election.id, obj=election)
    else:
        form = forms.ElectionForm(election.id)

    if form.validate_on_submit():
        form.embargoed.data = int(form.embargoed.data)
        if form.max_votes.data:
            try:
                form.max_votes.data = int(form.max_votes.data)
            except ValueError:
                form.max_votes.data = None
        else:
            form.max_votes.data = None

        form.candidates_are_fasusers.data = int(
            form.candidates_are_fasusers.data)
        form.populate_obj(election)

        # Fix start_date and end_date to use datetime
        election.start_date = datetime.combine(election.start_date, time())
        election.end_date = datetime.combine(election.end_date,
                                             time(23, 59, 59))
        SESSION.add(election)

        admin_groups = set(election.admin_groups_list)

        new_groups = set(
            [grp.strip() for grp in form.admin_grp.data.split(',')])

        # Add the new admin groups
        for admin_grp in new_groups.difference(admin_groups):
            admin = models.ElectionAdminGroup(
                election=election,
                group_name=admin_grp,
            )
            SESSION.add(admin)

        # Remove the admin groups that were removed with this edition
        for admin_grp in admin_groups.difference(new_groups):
            admingrp = models.ElectionAdminGroup.by_election_id_and_name(
                SESSION, election.id, admin_grp)
            SESSION.delete(admingrp)

        legal_voters = set(election.legal_voters_list)

        new_lgl_voters_groups = set(
            [grp.strip() for grp in form.lgl_voters.data.split(',')
             if grp.strip()])

        # Add the new legal voter groups
        for lgl_grp in new_lgl_voters_groups.difference(legal_voters):
            admin = models.LegalVoter(
                election=election,
                group_name=lgl_grp,
            )
            SESSION.add(admin)

        # Remove the legal voter groups that were removed with this edition
        for lgl_grp in legal_voters.difference(new_lgl_voters_groups):
            admingrp = models.LegalVoter.by_election_id_and_name(
                SESSION, election.id, lgl_grp)
            SESSION.delete(admingrp)

        SESSION.commit()
        fedmsgshim.publish(
            topic="election.edit",
            msg=dict(
                agent=flask.g.fas_user.username,
                election=election.to_json(),
            )
        )
        flask.flash('Election "%s" saved' % election.alias)
        return flask.redirect(flask.url_for(
            'admin_view_election', election_alias=election.alias))

    form.admin_grp.data = ', '.join(election.admin_groups_list)
    form.lgl_voters.data = ', '.join(election.legal_voters_list)

    return flask.render_template(
        'admin/view_election.html',
        election=election,
        form=form,
        submit_text='Edit election')


@APP.route('/admin/<election_alias>/candidates/new', methods=('GET', 'POST'))
@election_admin_required
def admin_add_candidate(election_alias):
    election = models.Election.get(SESSION, alias=election_alias)
    if not election:
        flask.abort(404)

    form = forms.CandidateForm()
    if form.validate_on_submit():

        fas_name = None
        if election.candidates_are_fasusers:  # pragma: no cover
            try:
                if APP.config.get('FASJSON'):
                    user = ACCOUNTS.get_user(
                        username=form.name.data).result
                    fas_name = f"{user['givenname']} {user['surname']}"
                else:
                    fas_name = ACCOUNTS.person_by_username(
                        form.name.data)['human_name']
            except (KeyError, AuthError, APIError):
                flask.flash(
                    'User `%s` does not have a FAS account.'
                    % form.name.data, 'error')
                return flask.redirect(
                    flask.url_for(
                        'admin_add_candidate',
                        election_alias=election_alias))

        candidate = models.Candidate(
            election=election,
            name=form.name.data,
            url=form.url.data,
            fas_name=fas_name,
        )

        SESSION.add(candidate)
        SESSION.commit()
        flask.flash('Candidate "%s" saved' % candidate.name)
        fedmsgshim.publish(
            topic="candidate.new",
            msg=dict(
                agent=flask.g.fas_user.username,
                election=candidate.election.to_json(),
                candidate=candidate.to_json(),
            )
        )
        return flask.redirect(flask.url_for(
            'admin_view_election', election_alias=election.alias))

    return flask.render_template(
        'admin/candidate.html',
        form=form,
        submit_text='Add candidate')


@APP.route('/admin/<election_alias>/candidates/new/multi',
           methods=('GET', 'POST'))
@election_admin_required
def admin_add_multi_candidate(election_alias):
    election = models.Election.get(SESSION, alias=election_alias)
    if not election:
        flask.abort(404)

    form = forms.MultiCandidateForm()
    if form.validate_on_submit():

        candidates_name = []
        for entry in form.candidate.data.strip().split("|"):
            candidate = entry.split("!")

            fas_name = None
            if election.candidates_are_fasusers:  # pragma: no cover
                try:
                    if APP.config.get('FASJSON'):
                        user = ACCOUNTS.get_user(
                            username=candidate[0]).result
                        fas_name = f"{user['givenname']} {user['surname']}"
                    else:
                        fas_name = ACCOUNTS.person_by_username(
                            candidate[0])['human_name']
                except (KeyError, AuthError, APIError):
                    SESSION.rollback()
                    flask.flash(
                        'User `%s` does not have a FAS account.'
                        % candidate[0], 'error')
                    return flask.redirect(
                        flask.url_for(
                            'admin_add_candidate',
                            election_alias=election_alias))

            # No url
            if len(candidate) == 1:
                cand = models.Candidate(
                    election=election,
                    name=candidate[0],
                    fas_name=fas_name)
                SESSION.add(cand)
                candidates_name.append(cand.name)
            # With url
            elif len(candidate) == 2:
                cand = models.Candidate(
                    election=election,
                    name=candidate[0],
                    url=candidate[1],
                    fas_name=fas_name)
                SESSION.add(cand)
                candidates_name.append(cand.name)
            else:
                flask.flash("There was an issue!")
            fedmsgshim.publish(
                topic="candidate.new",
                msg=dict(
                    agent=flask.g.fas_user.username,
                    election=cand.election.to_json(),
                    candidate=cand.to_json(),
                )
            )

        SESSION.commit()
        flask.flash('Added %s candidates' % len(candidates_name))
        return flask.redirect(flask.url_for(
            'admin_view_election', election_alias=election.alias))

    return flask.render_template(
        'admin/candidate_multi.html',
        form=form,
        submit_text='Add candidates')


@APP.route('/admin/<election_alias>/candidates/<int:candidate_id>/edit',
           methods=('GET', 'POST'))
@election_admin_required
def admin_edit_candidate(election_alias, candidate_id):
    election = models.Election.get(SESSION, alias=election_alias)
    candidate = models.Candidate.get(SESSION, candidate_id=candidate_id)

    if not election or not candidate:
        flask.abort(404)

    if candidate.election != election:
        flask.abort(404)

    form = forms.CandidateForm(obj=candidate)
    if form.validate_on_submit():
        form.populate_obj(candidate)

        if election.candidates_are_fasusers:  # pragma: no cover
            try:
                if APP.config.get('FASJSON'):
                    user = ACCOUNTS.get_user(
                        username=candidate.name).result
                    candidate.fas_name = f"{user['givenname']} {user['surname']}"
                else:
                    candidate.fas_name = ACCOUNTS.person_by_username(
                        candidate.name)['human_name']
            except (KeyError, AuthError, APIError):
                SESSION.rollback()
                flask.flash(
                    'User `%s` does not have a FAS account.'
                    % candidate.name, 'error')
                return flask.redirect(flask.url_for(
                    'admin_edit_candidate',
                    election_alias=election_alias,
                    candidate_id=candidate_id))

        SESSION.commit()
        flask.flash('Candidate "%s" saved' % candidate.name)
        fedmsgshim.publish(
            topic="candidate.edit",
            msg=dict(
                agent=flask.g.fas_user.username,
                election=candidate.election.to_json(),
                candidate=candidate.to_json(),
            )
        )
        return flask.redirect(flask.url_for(
            'admin_view_election', election_alias=election.alias))

    return flask.render_template(
        'admin/candidate.html',
        form=form,
        submit_text='Edit candidate')


@APP.route('/admin/<election_alias>/candidates/<int:candidate_id>/delete',
           methods=('GET', 'POST'))
@election_admin_required
def admin_delete_candidate(election_alias, candidate_id):
    election = models.Election.get(SESSION, alias=election_alias)
    candidate = models.Candidate.get(SESSION, candidate_id=candidate_id)

    if not election or not candidate:
        flask.abort(404)

    if candidate.election != election:
        flask.abort(404)

    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        candidate_name = candidate.name
        try:
            SESSION.delete(candidate)
            SESSION.commit()
            flask.flash('Candidate "%s" deleted' % candidate_name)
            fedmsgshim.publish(
                topic="candidate.delete",
                msg=dict(
                    agent=flask.g.fas_user.username,
                    election=candidate.election.to_json(),
                    candidate=candidate.to_json(),
                )
            )
        except SQLAlchemyError as err:
            SESSION.rollback()
            APP.logger.debug('Could not delete candidate')
            APP.logger.exception(err)
            flask.flash(
                'Could not delete this candidate. Is it already part of an '
                'election?', 'error'
            )
        return flask.redirect(flask.url_for(
            'admin_view_election', election_alias=election.alias))

    return flask.render_template(
        'admin/delete_candidate.html',
        form=form,
        candidate=candidate)
