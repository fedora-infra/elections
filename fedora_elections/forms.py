from flask.ext import wtf

from fedora_elections.models import Election


class ElectionForm(wtf.Form):
    summary = wtf.TextField('Summary', [wtf.validators.Required(),
                                        wtf.validators.Length(max=150)])
    alias = wtf.TextField('Alias', [
            wtf.validators.Required(),
            wtf.validators.Length(max=100),
            wtf.validators.Regexp('[a-z0-9_-]+',
                                  message=('Alias may only contain lower case '
                                           'letters, numbers, hyphens and '
                                           'underscores.')),
    ])
    description = wtf.TextAreaField('Description', [wtf.validators.Required()])
    url = wtf.TextField('URL', [wtf.validators.Required(),
                                wtf.validators.URL(),
                                wtf.validators.Length(max=250)])
    start_date = wtf.DateField('Start date', [wtf.validators.Required()])
    end_date = wtf.DateField('End date', [wtf.validators.Required()])
    number_elected = wtf.IntegerField('Number elected',
                                      [wtf.validators.Required(),
                                       wtf.validators.NumberRange(min=1)],
                                      default=1)
    candidates_are_fasusers = wtf.BooleanField('Candidates are FAS users?')
    frontpage = wtf.BooleanField('Show on front page?')
    embargoed = wtf.BooleanField('Embargo results?', default=True)

    def __init__(form, election_id=None, *args, **kwargs):
        super(ElectionForm, form).__init__(*args, **kwargs)
        form._election_id = election_id

    def validate_summary(form, field):
        check = Election.query.filter_by(summary=form.summary.data).all()
        if check:
            if not (form._election_id and form._election_id == check[0].id):
                raise wtf.ValidationError('There is already another election '
                                          'with this summary.')

    def validate_alias(form, field):
        if form.alias.data == 'new':
            raise wtf.ValidationError(flask.Markup('The alias cannot be '
                                                   '<code>new</code>.'))
        check = Election.query.filter_by(alias=form.alias.data).all()
        if check:
            if not (form._election_id and form._election_id == check[0].id):
                raise wtf.ValidationError('There is already another election '
                                          'with this alias.')

    def validate_end_date(form, field):
        if form.end_date.data <= form.start_date.data:
            raise wtf.ValidationError('End date must be later than '
                                      'start date.')


class CandidateForm(wtf.Form):
    name = wtf.TextField('Name', [wtf.validators.Required()])
    url = wtf.TextField('URL', [wtf.validators.Length(max=250)])


class LoginForm(wtf.Form):
    username = wtf.TextField('Username', [wtf.validators.Required()])
    password = wtf.PasswordField('Password', [wtf.validators.Required()])


class ConfirmationForm(wtf.Form):
    pass
