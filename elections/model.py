from turbogears.database import metadata, mapper, get_engine,session
# import some basic SQLAlchemy classes for declaring the data model
# (see http://www.sqlalchemy.org/docs/04/ormtutorial.html)
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.orm import relation
# import some datatypes for table columns from SQLAlchemy
# (see http://www.sqlalchemy.org/docs/04/types.html for more)
from sqlalchemy import String, Unicode, Integer, DateTime, Boolean
# A few sqlalchemy tricks:
# Allow viewing foreign key relations as a dictionary
from sqlalchemy.orm.collections import column_mapped_collection, attribute_mapped_collection
# Allow us to reference the remote table of a many:many as a simple list
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import select, and_

from sqlalchemy.exceptions import InvalidRequestError

from fedora.tg.json import SABase

# Bind us to the database definedin the config file.
get_engine()

#
# Tables mapped from the DB
#

ElectionsTable = Table('elections', metadata, autoload=True)
VotesTable = Table('votes', metadata, autoload=True)
CandidatesTable = Table('candidates', metadata, autoload=True)
LegalVotersTable = Table('legalvoters', metadata, autoload=True)

# View in the DB.  Needs to have the column keys defined
VoteTallyTable = Table('votecount', metadata,
    Column('candidate_id', Integer,
            ForeignKey('candidates.id'), primary_key=True),
    Column('novotes', Integer, nullable=False)
)

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

class VoteTally(SABase):
    pass

#
# set up mappers between tables and classes
#

mapper(Elections, ElectionsTable)
mapper(Votes, VotesTable, properties = {
    'candidate': relation(Candidates, backref='votes')
    })
mapper(Candidates, CandidatesTable, properties = {
    'election': relation(Elections, backref='candidates')
    })
mapper(LegalVoters, LegalVotersTable, properties = {
    'election': relation(Elections, backref='legalVoters')
    })
mapper(VoteTally, VoteTallyTable, properties = {
    'candidate': relation(Candidates, backref='tally')
    })

