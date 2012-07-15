import flask
from flask.ext.fas import FAS
from flask.ext.sqlalchemy import SQLAlchemy

from datetime import datetime, time
from functools import wraps
from urlparse import urlparse, urljoin

app = flask.Flask(__name__)
app.config.from_object('fedora_elections.default_config')
app.config.from_envvar('FEDORA_ELECTIONS_CONFIG')

# set up SQLAlchemy
db = SQLAlchemy(app)

# set up FAS
fas = FAS(app)


# modular imports
from fedora_elections import forms, models, redirect


def remove_csrf(form_data):
    return dict([(k, v) for k, v in form_data.items() if k != 'csrf'])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if flask.g.fas_user is None:
            return flask.redirect(flask.url_for('auth_login',
                                                next=flask.request.url))
        return f(*args, **kwargs)
    return decorated_function


def election_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if flask.g.fas_user is None:
            return flask.redirect(flask.url_for('auth_login',
                                                next=flask.request.url))
        if app.config['FEDORA_ELECTIONS_ADMIN_GROUP'] not in \
           flask.g.fas_user.groups:
            flask.abort(403)
        return f(*args, **kwargs)
    return decorated_function


### LIST VIEWS #############################################

@app.route('/')
def index():
    elections = models.Election.query.filter_by(frontpage=True).all()
    return flask.render_template('list/index.html', elections=elections)


@app.route('/archive')
def archived_elections():
    raise NotImplementedError


### AUTH VIEWS #############################################

@app.route('/login', methods=('GET', 'POST'))
def auth_login():
    if flask.g.fas_user:
        return redirect.safe_redirect_back()
    form = forms.LoginForm()
    if form.validate_on_submit():
        if fas.login(form.username.data, form.password.data):
            flask.flash('Welcome, %s' % flask.g.fas_user.username)
            return redirect.safe_redirect_back()
        else:
            flask.flash('Incorrect username or password')
    return flask.render_template('auth/login.html', form=form)


@app.route('/logout')
def auth_logout():
    if not flask.g.fas_user:
        return safe_redirect_back()
    fas.logout()
    flask.flash('You have been logged out')
    return redirect.safe_redirect_back()


### ELECTION ADMIN VIEWS ###################################

@app.route('/admin/')
@election_admin_required
def admin_view_elections():
    elections = models.Election.query.filter_by().all()
    return flask.render_template('admin/all_elections.html',
                                 elections=elections)


@app.route('/admin/new', methods=("GET", "POST"))
@election_admin_required
def admin_new_election():
    form = forms.ElectionForm()
    if form.validate_on_submit():
        election = models.Election(**remove_csrf(form.data))
        # Fix start_date and end_date to use datetime
        election.start_date = datetime.combine(election.start_date, time())
        election.end_date = datetime.combine(election.end_date,
                                             time(23, 59, 59))
        db.session.add(election)
        admin = models.ElectionAdminGroup(election=election,
                                          group_name=app.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
                                          role_required=u'user')
        db.session.add(admin)
        db.session.commit()
        flask.flash('Election "%s" added' % election.summary)
        return flask.redirect(flask.url_for('admin_view_election',
                                            election_alias=election.alias))
    return flask.render_template('admin/election_form.html', form=form,
                                 submit_text='Create election')


@app.route('/admin/<election_alias>/')
@election_admin_required
def admin_view_election(election_alias):
    election = models.Election.query.filter_by(alias=election_alias).first()
    if not election:
        flask.abort(404)
    return flask.render_template('admin/view_election.html', election=election)


@app.route('/admin/<election_alias>/edit', methods=("GET", "POST"))
@election_admin_required
def admin_edit_election(election_alias):
    election = models.Election.query.filter_by(alias=election_alias).first()
    if not election:
        flask.abort(404)
    form = forms.ElectionForm(election.id, obj=election)
    if form.validate_on_submit():
        form.populate_obj(election)
        db.session.commit()
        flask.flash('Election "%s" saved' % election.summary)
        return flask.redirect(flask.url_for('admin_view_election',
                                            election_alias=election.alias))
    return flask.render_template('admin/election_form.html', form=form,
                                 submit_text='Edit election')


@app.route('/admin/<election_alias>/candidates/new', methods=("GET", "POST"))
@election_admin_required
def admin_add_candidate(election_alias):
    election = models.Election.query.filter_by(alias=election_alias).first()
    if not election:
        flask.abort(404)
    form = forms.CandidateForm()
    if form.validate_on_submit():
        candidate = models.Candidate(election=election,
                                     **remove_csrf(form.data))
        db.session.add(candidate)
        db.session.commit()
        flask.flash('Candidate "%s" saved' % candidate.name)
        return flask.redirect(flask.url_for('admin_view_election',
                                            election_alias=election.alias))
    return flask.render_template('admin/candidate.html', form=form,
                                 submit_text='Add candidate')


@app.route('/admin/<election_alias>/candidates/<int:candidate_id>/edit',
           methods=("GET", "POST"))
@election_admin_required
def admin_edit_candidate(election_alias, candidate_id):
    election = models.Election.query.filter_by(alias=election_alias).first()
    candidate = models.Candidate.query.filter_by(id=candidate_id).first()
    if not election or not candidate:
        flask.abort(404)
    if candidate.election != election:
        flask.abort(404)
    form = forms.CandidateForm(obj=candidate)
    if form.validate_on_submit():
        form.populate_obj(candidate)
        db.session.commit()
        flask.flash('Candidate "%s" saved' % candidate.name)
        return flask.redirect(flask.url_for('admin_view_election',
                                            election_alias=election.alias))
    return flask.render_template('admin/candidate.html', form=form,
                                 submit_text='Edit candidate')


@app.route('/admin/<election_alias>/candidates/<int:candidate_id>/delete',
           methods=("GET", "POST"))
@election_admin_required
def admin_delete_candidate(election_alias, candidate_id):
    election = models.Election.query.filter_by(alias=election_alias).first()
    candidate = models.Candidate.query.filter_by(id=candidate_id).first()
    if not election or not candidate:
        flask.abort(404)
    if candidate.election != election:
        flask.abort(404)
    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        db.session.delete(candidate)
        candidate_name = candidate.name
        db.session.commit()
        flask.flash('Candidate "%s" deleted' % candidate_name)
        return flask.redirect(flask.url_for('admin_view_election',
                                            election_alias=election.alias))
    return flask.render_template('admin/delete_candidate.html', form=form,
                                 candidate=candidate)
