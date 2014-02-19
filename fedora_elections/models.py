# -*- coding: utf-8 -*-


import sqlalchemy as sa
from sqlalchemy import create_engine
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
    #engine.execute(collection_package_create_view(driver=engine.driver))
    if db_url.startswith('sqlite:'):
        ## Ignore the warning about con_record
        # pylint: disable=W0613
        def _fk_pragma_on_connect(dbapi_con, con_record):
            ''' Tries to enforce referential constraints on sqlite. '''
            dbapi_con.execute('pragma foreign_keys=ON')
        sa.event.listen(engine, 'connect', _fk_pragma_on_connect)

    if alembic_ini is not None:  # pragma: no cover
        # then, load the Alembic configuration and generate the
        # version table, "stamping" it with the most recent rev:

        ## Ignore the warning missing alembic
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
    engine = sa.create_engine(db_url,
                                      echo=debug,
                                      pool_recycle=pool_recycle)
    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession


class Election(BASE):
    __tablename__ = 'elections'

    id = sa.Column(sa.Integer, primary_key=True)
    summary = sa.Column(sa.Unicode(150), unique=True, nullable=False)
    alias = sa.Column(sa.Unicode(100), unique=True, nullable=False)
    description = sa.Column(sa.UnicodeText, nullable=False)
    url = sa.Column(sa.Unicode(250), nullable=False)
    start_date = sa.Column(sa.DateTime, nullable=False)
    end_date = sa.Column(sa.DateTime, nullable=False)
    number_elected = sa.Column(sa.Integer, nullable=False, default=1)
    embargoed = sa.Column(sa.Boolean, nullable=False, default=True)
    frontpage = sa.Column(sa.Boolean, nullable=False, default=False)
    voting_type = sa.Column(sa.Unicode(100), nullable=False, default=u'range')
    candidates_are_fasusers = sa.Column(sa.Boolean, nullable=False,
                                        default=False)
    fas_user = sa.Column(sa.Unicode(50), nullable=False)

    @property
    def status(self):
        now = datetime.utcnow()
        if now < self.start_date:
            return 'Pending'
        else:
            if now < self.end_date:
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
    def search(cls, session, frontpage=None, alias=None, summary=None,
               fas_user=None):
        """ Search the election and filter based on the arguments passed.
        """
        query = session.query(cls)

        if frontpage is not None:
            query = query.filter(cls.frontpage == frontpage)

        if alias is not None:
            query = query.filter(cls.alias == alias)

        if summary is not None:
            query = query.filter(cls.summary == summary)

        if fas_user is not None:
            query = query.filter(cls.fas_user == fas_user)

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
            cls.start_date
        )

        return query.all()

    @classmethod
    def get_open_election(cls, session, limit):
        """ Return all the election which end_date if greater or equal to
        the provided limit.
        """
        query = session.query(
            cls
        ).filter(
            cls.end_date >= limit
        ).order_by(
            cls.start_date
        )

        return query.all()


class ElectionAdminGroup(BASE):
    __tablename__ = 'electionadmingroups'

    id = sa.Column(sa.Integer, primary_key=True)
    election_id = sa.Column(sa.Integer, sa.ForeignKey('elections.id'),
                            nullable=False)
    election = relationship(
        'Election', backref=backref('admin_groups', lazy='dynamic'))
    group_name = sa.Column(sa.Unicode(150), nullable=False)
    role_required = sa.Column(sa.Enum(u'user', u'sponsor', u'administrator'),
                              nullable=False)


    @classmethod
    def by_election_id(cls, session, election_id):
        """ Return all the ElectionAdminGroup having a specific election_id.
        """
        return session.query(
            cls
        ).filter(
            cls.election_id == election_id
        ).all()



class Candidate(BASE):
    __tablename__ = 'candidates'

    id = sa.Column(sa.Integer, primary_key=True)
    election_id = sa.Column(sa.Integer, sa.ForeignKey('elections.id'),
                            nullable=False)
    election = relationship(
        'Election', backref=backref('candidates', lazy='dynamic'))
    name = sa.Column(sa.Unicode(150), nullable=False)  # FAS username if
                                                       # candidates_are_fasusers
    url = sa.Column(sa.Unicode(250))

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
    election_id = sa.Column(sa.Integer, sa.ForeignKey('elections.id'),
                            nullable=False)
    election = relationship(
        'Election', backref=backref('legal_voters', lazy='dynamic'))
    # special names:
    #     "cla + one" = cla_done + 1 non-cla group
    group_name = sa.Column(sa.Unicode(150), nullable=False)


class Vote(BASE):
    __tablename__ = 'votes'

    __table_args__ = (sa.UniqueConstraint('election_id', 'voter',
                                          'candidate_id',
                                          name='eid_voter_cid'), {} )

    id = sa.Column(sa.Integer, primary_key=True)
    election_id = sa.Column(sa.Integer, sa.ForeignKey('elections.id'),
                            nullable=False)
    election = relationship(
        'Election', backref=backref('votes', lazy='dynamic'))
    voter = sa.Column(sa.Unicode(150), nullable=False)
    timestamp = sa.Column(sa.DateTime, nullable=False)
    candidate_id = sa.Column(sa.Integer, sa.ForeignKey('candidates.id'),
                             nullable=False)
    candidate = relationship(
        'Candidate', backref=backref('votes', lazy='dynamic'))
    value = sa.Column(sa.Integer, nullable=False)

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
        )

        if count:
            return query.count()
        else:
            return query.all()
