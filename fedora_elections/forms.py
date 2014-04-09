from flask.ext import wtf
import wtforms

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
        choices=[('range', 'Range Voting'),
                 ('simple', 'Simple Voting')],
        default='range')

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

    def __init__(form, election_id=None, *args, **kwargs):
        super(ElectionForm, form).__init__(*args, **kwargs)
        form._election_id = election_id

    def validate_summary(form, field):
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
