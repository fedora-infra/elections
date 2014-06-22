# -*- coding: utf-8 -*-

import flask
import wtforms
from flask.ext import wtf

from fedora_elections import SESSION
from fedora_elections.models import Election


class ElectionForm(wtf.Form):
    shortdesc = wtforms.TextField(
        'Summary<span class="error">*</span>', [
            wtforms.validators.Required(),
            wtforms.validators.Length(max=150)])

    alias = wtforms.TextField(
        'Alias<span class="error">*</span>', [
            wtforms.validators.Required(),
            wtforms.validators.Length(max=100),
            wtforms.validators.Regexp(
                '[a-z0-9_-]+',
                message=('Alias may only contain lower case letters, numbers, '
                         'hyphens and underscores.')),
        ])

    description = wtforms.TextAreaField(
        'Description<span class="error">*</span>', [
            wtforms.validators.Required()])

    voting_type = wtforms.RadioField(
        'Type<span class="error">*</span>',
        choices=[
            ('range', 'Range Voting'),
            ('simple', 'Simple Voting (choose one candidate in the list)'),
            ('range_3', 'Simplified Range Voting (max is set below)'),
            ('select', 'Select Voting (checkboxes for each candidate, '
             'maximum number of votes set below)'),
        ],
        default='range')

    max_votes = wtforms.TextField(
        'Maximum Range/Votes',
        [wtforms.validators.optional()])

    url = wtforms.TextField(
        'URL<span class="error">*</span>', [
            wtforms.validators.Required(),
            wtforms.validators.URL(),
            wtforms.validators.Length(max=250)])

    start_date = wtforms.DateField(
        'Start date<span class="error">*</span>', [
            wtforms.validators.Required()])

    end_date = wtforms.DateField(
        'End date<span class="error">*</span>', [
            wtforms.validators.Required()])

    seats_elected = wtforms.IntegerField(
        'Number elected<span class="error">*</span>', [
            wtforms.validators.Required(),
            wtforms.validators.NumberRange(min=1)],
        default=1)

    candidates_are_fasusers = wtforms.BooleanField(
        'Candidates are FAS users?')

    embargoed = wtforms.BooleanField('Embargo results?', default=True)

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


class CandidateForm(wtf.Form):
    name = wtforms.TextField('Name', [wtforms.validators.Required()])
    url = wtforms.TextField('URL', [wtforms.validators.Length(max=250)])


class MultiCandidateForm(wtf.Form):
    candidate = wtforms.TextField(
        'Candidates', [wtforms.validators.Required()])


class ConfirmationForm(wtf.Form):
    pass


def get_range_voting_form(candidates, max_range):
    class RangeVoting(wtf.Form):
        action = wtforms.HiddenField()

    for candidate in candidates:
        title = candidate.name
        if candidate.url:
            title = '%s <a href="%s">[Info]</a>' % (title, candidate.url)
        field = wtforms.SelectField(
            title,
            choices=[(str(item), item) for item in range(max_range + 1)]
        )
        setattr(RangeVoting, candidate.name, field)

    return RangeVoting()


def get_simple_voting_form(candidates):
    class SimpleVoting(wtf.Form):
        action = wtforms.HiddenField()

    titles = []
    for candidate in candidates:
        title = candidate.name
        if candidate.url:
            title = '%s <a href="%s">[Info]</a>' % (title, candidate.url)
        titles.append((str(candidate.id), title))
    field = wtforms.RadioField(
        'Candidates',
        choices=titles
    )
    setattr(SimpleVoting, 'candidate', field)

    return SimpleVoting()


def get_select_voting_form(candidates, max_selection):
    class SelectVoting(wtf.Form):
        action = wtforms.HiddenField()

    for candidate in candidates:
        title = candidate.name
        if candidate.url:
            title = '%s <a href="%s">[Info]</a>' % (title, candidate.url)
        field = wtforms.BooleanField(
            title,
        )
        setattr(SelectVoting, candidate.name, field)

    # TODO: See if we can add a form wide validation using max_selection

    return SelectVoting()
