# -*- coding: utf-8 -*-
"""The application's model objects"""

from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.orm import scoped_session, sessionmaker, mapper, relation
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime, String
#from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

from fedora.tg.json import SABase

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

    #
    # See the following example:

    #global t_reflected

    #t_reflected = Table("Reflected", metadata,
    #    autoload=True, autoload_with=engine)
    ElectionsTable = Table('elections', metadata, autoload=True)
    VotesTable = Table('votes', metadata, autoload=True)
    CandidatesTable = Table('candidates', metadata, autoload=True)
    LegalVotersTable = Table('legalvoters', metadata, autoload=True)
    ElectionAdminsTable = Table('electionadmins', metadata, autoload=True)

    # View in the DB.  Needs to have the column keys defined
    VoteTallyTable = Table('fvotecount', metadata,
        Column('id', Integer,
                ForeignKey('candidates.id'), primary_key=True),
        Column('election_id', Integer),
        Column('name', String, nullable=False),
        Column('novotes', Integer, nullable=False)
    )
    UserVoteCountTable = Table('uservotes', metadata,
        Column('election_id', Integer, ForeignKey('elections.id'), primary_key=True),
        Column('voter', String, nullable=False, primary_key=True),
        Column('novotes', Integer, nullable=False)
    )

    #mapper(Reflected, t_reflected)
    mapper(Elections, ElectionsTable, properties = {
        'legalVoters': relation(LegalVoters, backref='election'),
        'candidates': relation(Candidates, backref='election'),
        'uservotes': relation(UserVoteCount, backref='election')
        })
    mapper(Votes, VotesTable)
    mapper(Candidates, CandidatesTable, properties = {
        'votes': relation(Votes, backref='candidate'),
        'tally': relation(VoteTally, backref='candidate')
        })
    mapper(LegalVoters, LegalVotersTable)
    mapper(ElectionAdmins, ElectionAdminsTable)
    mapper(VoteTally, VoteTallyTable)
    mapper(UserVoteCount, UserVoteCountTable)

# Import your model modules here.
from elections2.model.auth import User, Group, Permission

#
# Classes to map to
#

class Elections(SABase):
    pass

class Votes(SABase):
    pass

class Candidates(SABase):
    pass

class LegalVoters(SABase):
    pass

class ElectionAdmins(SABase):
    pass

class VoteTally(SABase):
    pass

class UserVoteCount(SABase):
    pass
