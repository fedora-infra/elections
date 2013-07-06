from fedora_elections import app, db

from datetime import datetime

class Election(db.Model):
    __tablename__ = 'elections'

    id = db.Column(db.Integer, primary_key=True)
    summary = db.Column(db.Unicode(150), unique=True, nullable=False)
    alias = db.Column(db.Unicode(100), unique=True, nullable=False)
    description = db.Column(db.UnicodeText, nullable=False)
    url = db.Column(db.Unicode(250), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    number_elected = db.Column(db.Integer, nullable=False, default=1)
    embargoed = db.Column(db.Boolean, nullable=False, default=True)
    frontpage = db.Column(db.Boolean, nullable=False, default=False)
    voting_type = db.Column(db.Unicode(100), nullable=False, default=u'range')
    candidates_are_fasusers = db.Column(db.Boolean, nullable=False,
                                        default=False)
    fas_user = db.Column(db.Unicode(50), nullable=False)

    @property
    def status(self):
        if datetime.now() < self.start_date:
            return 'Pending'
        else:
            if datetime.now() < self.end_date:
                return 'In progress'
            else:
                if self.embargoed:
                    return 'Embargoed'
                else:
                    return 'Ended'

    @property
    def locked(self):
        return datetime.now() >= self.start_date


class ElectionAdminGroup(db.Model):
    __tablename__ = 'electionadmingroups'

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'),
                            nullable=False)
    election = db.relationship('Election', backref=db.backref('admin_groups',
                                                              lazy='dynamic'))
    group_name = db.Column(db.Unicode(150), nullable=False)
    role_required = db.Column(db.Enum(u'user', u'sponsor', u'administrator'),
                              nullable=False)


class Candidate(db.Model):
    __tablename__ = 'candidates'

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'),
                            nullable=False)
    election = db.relationship('Election', backref=db.backref('candidates',
                                                              lazy='dynamic'))
    name = db.Column(db.Unicode(150), nullable=False)  # FAS username if
                                                       # candidates_are_fasusers
    url = db.Column(db.Unicode(250))

    @property
    def vote_count(self):
        values = [v.value for v in self.votes]
        return sum(values)


class LegalVoter(db.Model):
    __tablename__ = 'legalvoters'

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'),
                            nullable=False)
    election = db.relationship('Election', backref=db.backref('legal_voters',
                                                              lazy='dynamic'))
    # special names:
    #     "cla + one" = cla_done + 1 non-cla group
    group_name = db.Column(db.Unicode(150), nullable=False)


class Vote(db.Model):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'),
                            nullable=False)
    election = db.relationship('Election', backref=db.backref('votes',
                                                              lazy='dynamic'))
    voter = db.Column(db.Unicode(150), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'),
                             nullable=False)
    candidate = db.relationship('Candidate', backref=db.backref('votes',
                                                                lazy='dynamic'))
    value = db.Column(db.Integer, nullable=False)
