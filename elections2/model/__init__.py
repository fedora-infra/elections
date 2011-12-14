# -*- coding: utf-8 -*-
"""The application's model objects"""

from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.orm import scoped_session, sessionmaker, mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime, String
#from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

# Global session manager: DBSession() returns the Thread-local
# session object appropriate for the current web request.
maker = sessionmaker(autoflush=True, autocommit=False,
                     extension=ZopeTransactionExtension())
DBSession = scoped_session(maker)

# Base class for all of our model classes: By default, the data model is
# defined with SQLAlchemy's declarative extension, but if you need more
# control, you can switch to the traditional method.
DeclarativeBase = declarative_base()

# There are two convenient ways for you to spare some typing.
# You can have a query property on all your model classes by doing this:
# DeclarativeBase.query = DBSession.query_property()
# Or you can use a session-aware mapper as it was used in TurboGears 1:
# DeclarativeBase = declarative_base(mapper=DBSession.mapper)

# Global metadata.
# The default metadata is the one from the declarative base.
metadata = DeclarativeBase.metadata

# If you have multiple databases with overlapping table names, you'll need a
# metadata for each database. Feel free to rename 'metadata2'.
#metadata2 = MetaData()

#####
# Generally you will not want to define your table's mappers, and data objects
# here in __init__ but will want to create modules them in the model directory
# and import them at the bottom of this file.
#
######

def init_model(engine):
    """Call me before using any of the tables or classes in the model."""

    DBSession.configure(bind=engine)
    metadata.bind = engine
    # If you are using reflection to introspect your database and create
    # table objects for you, your tables must be defined and mapped inside
    # the init_model function, so that the engine is available if you
    # use the model outside tg2, you need to make sure this is called before
    # you use the model.

    # View in the DB.  Needs to have the column keys defined


# Import your model modules here.
from elections2.model.auth import User, Group, Permission

#
# Classes to map to
#


class LegalVoters(DeclarativeBase):
    """
    Define the voters.
    """
    __tablename__ = 'legalvoters'

    #{ Columns
    id = Column(Integer, autoincrement=True, primary_key=True, unique=True)
    election_id = Column(Integer, ForeignKey('elections.id'), nullable=False)
    group_name = Column(Unicode(150), nullable=False)

    #{ Special methods
    def __repr__(self):
        return '<LegalVoters: group=%r>' % self.group_name

    def __unicode__(self):
        return self.group_name
    #}


class ElectionAdmins(DeclarativeBase):
    """
    Define the Admins.
    """
    __tablename__ = 'electionadmins'

    #{ Columns
    id = Column(Integer, autoincrement=True, primary_key=True, unique=True)
    election_id = Column(Integer, ForeignKey('elections.id'), nullable=False)
    group_name = Column(Unicode(150), nullable=False)

    #{ Special methods
    def __repr__(self):
        return '<ElectionAdmins: group=%r>' % self.group_name

    def __unicode__(self):
        return self.group_name
    #}


class Elections(DeclarativeBase):
    """
    Define the different elections.
    """
    __tablename__ = 'elections'

    #{ Columns
    id = Column(Integer, autoincrement=True, primary_key=True)
    shortdesc = Column(Unicode(150), unique=True, nullable=False)
    alias = Column(Unicode(150), unique=True, nullable=False)
    description = Column(Unicode(150), unique=True, nullable=False)
    url = Column(Unicode(150), unique=True, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    seats_elected = Column(Integer, nullable=False)
    votes_per_user = Column(Integer, nullable=False)
    embargoed = Column(Integer, nullable=False, default=0)
    usefas = Column(Integer, nullable=False, default=0)
    allow_nominations = Column(Integer, nullable=False, default=0)
    nominations_until = Column(DateTime)

    #{ Relations
    legalVoters =  relation('LegalVoters')
    candidates = relation('Candidates')
    #uservotes = relation('UserVoteCount')

    #{ Special methods
    def __repr__(self):
        return '<Elections: election=%r>' % self.shortdesc

    def __unicode__(self):
        return self.shortdesc
    #}


class Votes(DeclarativeBase):
    """
    Define the different votes.
    """
    __tablename__ = 'votes'

    #{ Columns
    id = Column(Integer, autoincrement=True, primary_key=True, unique=True)
    election_id = Column(Integer, ForeignKey('elections.id'), nullable=False)
    voter = Column(Unicode(150), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False)
    weight = Column(Integer, nullable=False)

    #{ Special methods
    def __repr__(self):
        return '<Votes: voter=%r>' % self.voter

    def __unicode__(self):
        return self.voter
    #}


class Candidates(DeclarativeBase):
    """
    Define the candidates.
    """
    __tablename__ = 'candidates'

    #{ Columns
    id = Column(Integer, autoincrement=True, primary_key=True)
    election_id = Column(Integer, ForeignKey('elections.id'),
            primary_key=True, nullable=False)
    name = Column(Unicode(150), nullable=False)
    url = Column(Unicode(150))
    formalname = Column(Unicode(150), nullable=True)
    human = Column(Integer)
    status = Column(Integer)

    #{ Relations
    votes = relation('Votes', backref='candidate'),
    #tally = relation('VoteTally', backref='candidate')
    
    #{ Special methods
    def __repr__(self):
        return '<Candidates: candidate=%r>' % self.name

    def __unicode__(self):
        return self.name
    #}
