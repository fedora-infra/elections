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

from datetime import datetime, time
from functools import wraps

import flask
from sqlalchemy.exc import SQLAlchemyError

from fedora_elections import fedmsgshim
from fedora_elections import forms
from fedora_elections import models
from fedora_elections import (
    APP, SESSION, is_authenticated, is_admin, is_election_admin,
    is_safe_url, safe_redirect_back
)


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


@APP.route('/admin/')
@election_admin_required
def admin_view_elections():
    elections = models.Election.search(SESSION)

    return flask.render_template(
        'admin/all_elections.html',
        elections=elections)


@APP.route('/admin/new', methods=('GET', 'POST'))
@election_admin_required
def admin_new_election():
    form = forms.ElectionForm()
    if form.validate_on_submit():

        election = models.Election(
            shortdesc=form.shortdesc.data,
            alias=form.alias.data,
            description=form.description.data,
            url=form.url.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            seats_elected=form.seats_elected.data,
            embargoed=int(form.embargoed.data),
            voting_type=form.voting_type.data,
            candidates_are_fasusers=form.candidates_are_fasusers.data,
            fas_user=flask.g.fas_user.username,
        )

        # Fix start_date and end_date to use datetime
        election.start_date = datetime.combine(election.start_date, time())
        election.end_date = datetime.combine(election.end_date,
                                             time(23, 59, 59))
        SESSION.add(election)

        admin = models.ElectionAdminGroup(
            election=election,
            group_name=APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
        )
        SESSION.add(admin)

        SESSION.commit()

        fedmsgshim.publish(
            topic="election.new",
            msg=dict(
                agent=flask.g.fas_user.username,
                election=election.to_json(),
                )
        )

        flask.flash('Election "%s" added' % election.alias)
        fedmsgshim.publish(topic="election.new", msg=election)
        return flask.redirect(flask.url_for(
            'admin_view_election', election_alias=election.alias))
    return flask.render_template(
        'admin/election_form.html',
        form=form,
        submit_text='Create election')


@APP.route('/admin/<election_alias>/')
@election_admin_required
def admin_view_election(election_alias):
    election = models.Election.get(SESSION, alias=election_alias)
    if not election:
        flask.abort(404)

    return flask.render_template(
        'admin/view_election.html',
        election=election)


@APP.route('/admin/<election_alias>/edit', methods=('GET', 'POST'))
@election_admin_required
def admin_edit_election(election_alias):
    election = models.Election.get(SESSION, alias=election_alias)
    if not election:
        flask.abort(404)

    form = forms.ElectionForm(election.id, obj=election)
    if form.validate_on_submit():
        form.embargoed.data = int(form.embargoed.data)
        form.populate_obj(election)
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

    return flask.render_template(
        'admin/election_form.html',
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
        candidate = models.Candidate(
            election=election,
            name=form.name.data,
            url=form.url.data
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
            #No url
            if len(candidate) == 1:
                cand = models.Candidate(
                    election=election,
                    name=candidate[0])
                SESSION.add(cand)
                candidates_name.append(cand.name)
            # With url
            elif len(candidate) == 2:
                cand = models.Candidate(
                    election=election,
                    name=candidate[0],
                    url=candidate[1])
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
        except SQLAlchemyError, err:
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
