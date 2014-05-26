# -*- coding: utf-8 -*-


import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy import func as safunc
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import relation, relationship
from sqlalchemy.orm import backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm.collections import mapped_collection
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_
from sqlalchemy.sql.expression import Executable, ClauseElement

BASE = declarative_base()

from datetime import datetime


def create_tables(db_url, alembic_ini=None, debug=False):
    """ Create the tables in the database using the information from the
    url obtained.

    :arg db_url, URL used to connect to the database. The URL contains
        information with regards to the database engine, the host to
        connect to, the user and password and the database name.
          ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg alembic_ini, path to the alembic ini file. This is necessary
        to be able to use alembic correctly, but not for the unit-tests.
    :kwarg debug, a boolean specifying wether we should have the verbose
        output of sqlalchemy or not.
    :return a session that can be used to query the database.

    """
    engine = create_engine(db_url, echo=debug)
    BASE.metadata.create_all(engine)
    # engine.execute(collection_package_create_view(driver=engine.driver))
    if db_url.startswith('sqlite:'):  # pragma: no cover
        # Ignore the warning about con_record
        # pylint: disable=W0613
        def _fk_pragma_on_connect(dbapi_con, con_record):
            ''' Tries to enforce referential constraints on sqlite. '''
            dbapi_con.execute('pragma foreign_keys=ON')
        sa.event.listen(engine, 'connect', _fk_pragma_on_connect)

    if alembic_ini is not None:  # pragma: no cover
        # then, load the Alembic configuration and generate the
        # version table, "stamping" it with the most recent rev:

        # Ignore the warning missing alembic
        # pylint: disable=F0401
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(alembic_ini)
        command.stamp(alembic_cfg, "head")

    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession


def create_session(db_url, debug=False, pool_recycle=3600):
    """ Create the Session object to use to query the database.

    :arg db_url: URL used to connect to the database. The URL contains
    information with regards to the database engine, the host to connect
    to, the user and password and the database name.
      ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg debug: a boolean specifying wether we should have the verbose
        output of sqlalchemy or not.
    :return a Session that can be used to query the database.

    """
    engine = sa.create_engine(
        db_url, echo=debug, pool_recycle=pool_recycle)
    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession


class Election(BASE):
    __tablename__ = 'elections'

    id = sa.Column(sa.Integer, primary_key=True)
    shortdesc = sa.Column(sa.Unicode(150), unique=True, nullable=False)
    alias = sa.Column(sa.Unicode(100), unique=True, nullable=False)
    description = sa.Column(sa.UnicodeText, nullable=False)
    url = sa.Column(sa.Unicode(250), nullable=False)
    start_date = sa.Column(sa.DateTime, nullable=False)
    end_date = sa.Column(sa.DateTime, nullable=False)
    seats_elected = sa.Column(sa.Integer, nullable=False, default=1)
    embargoed = sa.Column(sa.Integer, nullable=False, default=0)
    voting_type = sa.Column(sa.Unicode(100), nullable=False, default=u'range')
    max_votes = sa.Column(sa.Integer, nullable=True)
    candidates_are_fasusers = sa.Column(
        sa.Integer, nullable=False, default=0)
    fas_user = sa.Column(sa.Unicode(50), nullable=False)

    def to_json(self):
        ''' Return a json representation of this object. '''
        return dict(
            shortdesc=self.shortdesc,
            alias=self.alias,
            description=self.description,
            url=self.url,
            start_date=self.start_date.strftime('%Y-%m-%d %H:%M'),
            end_date=self.end_date.strftime('%Y-%m-%d %H:%M'),
            embargoed=self.embargoed,
            voting_type=self.voting_type,
        )

    @property
    def admin_groups_list(self):
        return sorted([grp.group_name for grp in self.admin_groups])

    @property
    def legal_voters_list(self):
        return sorted([grp.group_name for grp in self.legal_voters])

    @property
    def status(self):
        now = datetime.utcnow()
        if now.date() < self.start_date.date():
            return 'Pending'
        else:
            if now.date() <= self.end_date.date():
                return 'In progress'
            else:
                if self.embargoed:
                    return 'Embargoed'
                else:
                    return 'Ended'

    @property
    def locked(self):
        return datetime.now() >= self.start_date

    @classmethod
    def search(cls, session, alias=None, shortdesc=None,
               fas_user=None):
        """ Search the election and filter based on the arguments passed.
        """
        query = session.query(cls)

        if alias is not None:
            query = query.filter(cls.alias == alias)

        if shortdesc is not None:
            query = query.filter(cls.shortdesc == shortdesc)

        if fas_user is not None:
            query = query.filter(cls.fas_user == fas_user)

        query = query.order_by(sa.desc(cls.start_date))

        return query.all()

    @classmethod
    def by_alias(cls, session, alias):
        """ Return a specific election based on its alias. """
        return session.query(cls).filter(cls.alias == alias).first()

    get = by_alias

    @classmethod
    def get_older_election(cls, session, limit):
        """ Return all the election which end_date if older than the
        provided limit.
        """
        query = session.query(
            cls
        ).filter(
            cls.end_date < limit
        ).order_by(
            sa.desc(cls.start_date)
        )

        return query.all()

    @classmethod
    def get_open_election(cls, session, limit):
        """ Return all the election which start_date is lower and the
        end_date if greater or equal to the provided limit.
        """
        query = session.query(
            cls
        ).filter(
            cls.start_date < limit
        ).filter(
            cls.end_date >= limit
        ).order_by(
            sa.desc(cls.start_date)
        )

        return query.all()

    @classmethod
    def get_next_election(cls, session, limit):
        """ Return all the future elections whose start_date is greater than
        the provided limit.
        """
        query = session.query(
            cls
        ).filter(
            cls.start_date > limit
        ).order_by(
            sa.desc(cls.start_date)
        )

        return query.all()


class ElectionAdminGroup(BASE):
    __tablename__ = 'electionadmins'

    id = sa.Column(sa.Integer, primary_key=True)
    election_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('elections.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False)
    group_name = sa.Column(sa.Unicode(150), nullable=False)

    election = relationship(
        'Election', backref=backref('admin_groups', lazy='dynamic'))

    @classmethod
    def by_election_id(cls, session, election_id):
        """ Return all the ElectionAdminGroup having a specific election_id.
        """
        return session.query(
            cls
        ).filter(
            cls.election_id == election_id
        ).all()

    @classmethod
    def by_election_id_and_name(cls, session, election_id, group_name):
        """ Return the ElectionAdminGroup having a specific election_id
        and group_name.
        """
        return session.query(
            cls
        ).filter(
            cls.election_id == election_id
        ).filter(
            cls.group_name == group_name
        ).first()


class Candidate(BASE):
    __tablename__ = 'candidates'

    id = sa.Column(sa.Integer, primary_key=True)
    election_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(
            'elections.id',
            ondelete='RESTRICT',
            onupdate='CASCADE'),
        nullable=False)
    # FAS username if candidates_are_fasusers
    name = sa.Column(sa.Unicode(150), nullable=False)
    url = sa.Column(sa.Unicode(250))

    election = relationship(
        'Election', backref=backref('candidates', lazy='dynamic'))

    def to_json(self):
        ''' Return a json representation of this object. '''
        return dict(
            name=self.name,
            url=self.url,
        )

    @property
    def vote_count(self):
        values = [v.value for v in self.votes]
        return sum(values)

    @classmethod
    def by_id(cls, session, candidate_id):
        """ Return a specific election based on its alias. """
        return session.query(cls).filter(cls.id == candidate_id).first()

    get = by_id


class LegalVoter(BASE):
    __tablename__ = 'legalvoters'

    id = sa.Column(sa.Integer, primary_key=True)
    election_id = sa.Column(
        sa.Integer,
        sa.ForeignKey('elections.id', ondelete='RESTRICT', onupdate='CASCADE'),
        nullable=False)
    group_name = sa.Column(sa.Unicode(150), nullable=False)

    election = relationship(
        'Election', backref=backref('legal_voters', lazy='dynamic'))
    # special names:
    #     "cla + one" = cla_done + 1 non-cla group

    @classmethod
    def by_election_id_and_name(cls, session, election_id, group_name):
        """ Return the ElectionAdminGroup having a specific election_id
        and group_name.
        """
        return session.query(
            cls
        ).filter(
            cls.election_id == election_id
        ).filter(
            cls.group_name == group_name
        ).first()


class Vote(BASE):
    __tablename__ = 'votes'

    __table_args__ = (sa.UniqueConstraint('election_id', 'voter',
                                          'candidate_id',
                                          name='eid_voter_cid'), {})

    id = sa.Column(sa.Integer, primary_key=True)
    election_id = sa.Column(sa.Integer, sa.ForeignKey('elections.id'),
                            nullable=False)
    voter = sa.Column(sa.Unicode(150), nullable=False)
    timestamp = sa.Column(sa.DateTime, nullable=False, default=safunc.now())
    candidate_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(
            'candidates.id',
            ondelete='RESTRICT',
            onupdate='CASCADE'),
        nullable=False)
    value = sa.Column(sa.Integer, nullable=False)

    election = relationship(
        'Election', backref=backref('votes', lazy='dynamic'))
    candidate = relationship(
        'Candidate', backref=backref('votes', lazy='dynamic'))

    @classmethod
    def of_user_on_election(cls, session, user, election_id, count=False):
        """ Return the votes of a user on a specific election.
        If count if True, then return the number of votes instead of the
        actual votes.
        """
        query = session.query(
            cls
        ).filter(
            cls.election_id == election_id
        ).filter(
            cls.voter == user
        ).order_by(
            cls.timestamp
        )

        if count:
            return query.count()
        else:
            return query.all()

    @classmethod
    def get_election_stats(cls, session, election_id):
        """ Return a dictionnary containing some statistics about the
        specified elections.
        (Number of voters, number of votes per candidates, total number
        of votes)
        """

        stats = {}

        n_voters = session.query(
            sa.func.distinct(cls.voter)
        ).filter(
            cls.election_id == election_id
        ).count()
        stats['n_voters'] = n_voters

        n_votes = session.query(
            cls
        ).filter(
            cls.election_id == election_id
        ).filter(
            cls.value > 0
        ).count()
        stats['n_votes'] = n_votes

        election = session.query(
            Election
        ).filter(
            Election.id == election_id
        ).first()

        candidate_voters = {}
        cnt = 0
        for cand in election.candidates:
            cnt += 1
            n_voters = session.query(
                sa.func.distinct(cls.voter)
            ).filter(
                cls.election_id == election_id
            ).filter(
                cls.candidate_id == cand.id
            ).filter(
                cls.value > 0
            ).count()
            candidate_voters[cand.name] = n_voters

        stats['candidate_voters'] = candidate_voters
        stats['n_candidates'] = cnt

        return stats
