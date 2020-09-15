# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import flask
import wtforms
try:
    from flask_wtf import FlaskForm
except ImportError:
    from flask_wtf import Form as FlaskForm


from fedora.client import AuthError
from fedora_elections import SESSION, ACCOUNTS, APP
from fedora_elections.models import Election
from fasjson_client.errors import APIError


class ElectionForm(FlaskForm):
    shortdesc = wtforms.TextField(
        'Summary', [
            wtforms.validators.Required(),
            wtforms.validators.Length(max=150)])

    alias = wtforms.TextField(
        'Alias', [
            wtforms.validators.Required(),
            wtforms.validators.Length(max=100),
            wtforms.validators.Regexp(
                '[a-z0-9_-]+',
                message=('Alias may only contain lower case letters, numbers, '
                         'hyphens and underscores.')),
        ])

    description = wtforms.TextAreaField(
        'Description', [
            wtforms.validators.Required()])

    voting_type = wtforms.SelectField(
        'Type',
        choices=[
            ('range', 'Range Voting'),
            ('simple', 'Simple Voting (choose one candidate in the list)'),
            ('range_simple', 'Simplified Range Voting (max is set below)'),
            ('select', 'Select Voting (checkboxes for each candidate, '
             'maximum number of votes set below)'),
            ('irc', '+1/0/-1 voting'),
        ],
        default='range')

    max_votes = wtforms.TextField(
        'Maximum Range/Votes',
        [wtforms.validators.optional()])

    url = wtforms.TextField(
        'URL', [
            wtforms.validators.Required(),
            wtforms.validators.URL(),
            wtforms.validators.Length(max=250)])

    start_date = wtforms.DateField(
        'Start date', [
            wtforms.validators.Required()])

    end_date = wtforms.DateField(
        'End date', [
            wtforms.validators.Required()])

    seats_elected = wtforms.IntegerField(
        'Number elected', [
            wtforms.validators.Required(),
            wtforms.validators.NumberRange(min=1)],
        default=1)

    candidates_are_fasusers = wtforms.BooleanField(
        'Candidates are FAS users?')

    embargoed = wtforms.BooleanField('Embargo results?', default=True)

    url_badge = wtforms.TextField(
        'Badge URL (optional)', [
            wtforms.validators.Optional(),
            wtforms.validators.URL(),
            wtforms.validators.Length(max=250)])

    lgl_voters = wtforms.TextField(
        'Legal voters groups', [wtforms.validators.optional()])

    admin_grp = wtforms.TextField(
        'Admin groups', [wtforms.validators.optional()])

    def __init__(form, election_id=None, *args, **kwargs):
        super(ElectionForm, form).__init__(*args, **kwargs)
        form._election_id = election_id

    def validate_shortdesc(form, field):
        check = Election.search(SESSION, shortdesc=form.shortdesc.data)
        if check:
            if not (form._election_id and form._election_id == check[0].id):
                raise wtforms.ValidationError(
                    'There is already another election with this summary.')

    def validate_alias(form, field):
        if form.alias.data == 'new':
            raise wtforms.ValidationError(flask.Markup(
                'The alias cannot be <code>new</code>.'))
        check = Election.search(SESSION, alias=form.alias.data)
        if check:
            if not (form._election_id and form._election_id == check[0].id):
                raise wtforms.ValidationError(
                    'There is already another election with this alias.')

    def validate_end_date(form, field):
        if form.end_date.data <= form.start_date.data:
            raise wtforms.ValidationError(
                'End date must be later than start date.')


class CandidateForm(FlaskForm):
    name = wtforms.TextField('Name', [wtforms.validators.Required()])
    url = wtforms.TextField('URL', [wtforms.validators.Length(max=250)])


class MultiCandidateForm(FlaskForm):
    candidate = wtforms.TextField(
        'Candidates', [wtforms.validators.Required()])


class ConfirmationForm(FlaskForm):
    pass


def get_range_voting_form(candidates, max_range):
    class RangeVoting(FlaskForm):
        action = wtforms.HiddenField()

    for candidate in candidates:
        title = candidate.fas_name or candidate.name
        if candidate.url:
            title = '%s <a href="%s" target="_blank" rel="noopener noreferrer">[Info]</a>' % (title, candidate.url)
        field = wtforms.SelectField(
            title,
            choices=[(str(item), item) for item in range(max_range + 1)]
        )
        setattr(RangeVoting, str(candidate.id), field)

    return RangeVoting()


def get_simple_voting_form(candidates, fasusers):
    class SimpleVoting(FlaskForm):
        action = wtforms.HiddenField()

    titles = []
    for candidate in candidates:
        title = candidate.fas_name or candidate.name
        if fasusers:  # pragma: no cover
            # We can't cover FAS integration
            try:
                if APP.config.get('FASJSON'):
                    user = ACCOUNTS.get_user(
                        username=candidate.name).result
                    title = f"{user['givenname']} {user['surname']}"
                else:
                    title = ACCOUNTS.person_by_username(
                        candidate.name)['human_name']
            except (KeyError, AuthError, APIError) as err:
                APP.logger.debug(err)
        if candidate.url:
            title = '%s <a href="%s" target="_blank" rel="noopener noreferrer">[Info]</a>' % (title, candidate.url)
        titles.append((str(candidate.id), title))
    field = wtforms.RadioField(
        'Candidates',
        choices=titles
    )
    setattr(SimpleVoting, 'candidate', field)

    return SimpleVoting()


def get_irc_voting_form(candidates, fasusers):
    class IrcVoting(FlaskForm):
        action = wtforms.HiddenField()

    for candidate in candidates:
        field = wtforms.SelectField(
            candidate.name,
            choices=[('0', 0), ('1', 1), ('-1', -1)]
        )
        setattr(IrcVoting, candidate.name, field)

    return IrcVoting()


def get_select_voting_form(candidates, max_selection):
    class SelectVoting(FlaskForm):
        action = wtforms.HiddenField()

    for candidate in candidates:
        title = candidate.fas_name or candidate.name
        if candidate.url:
            title = '%s <a href="%s" target="_blank" rel="noopener noreferrer">[Info]</a>' % (title, candidate.url)
        field = wtforms.BooleanField(
            title,
        )
        setattr(SelectVoting, candidate.name, field)

    # TODO: See if we can add a form wide validation using max_selection

    return SelectVoting()
