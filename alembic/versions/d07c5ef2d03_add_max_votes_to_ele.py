"""Add max_votes to election


Revision ID: d07c5ef2d03
Revises: None
Create Date: 2014-05-26 16:33:50.812050

"""

# revision identifiers, used by Alembic.
revision = 'd07c5ef2d03'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    """ Add the max_votes column to the Elections table. """
    op.add_column(
        'elections',
        sa.Column('max_votes', sa.Integer, nullable=True)
    )


def downgrade():
    """ Drop the max_votes column from the Elections table. """
    op.drop_column('elections', 'max_votes')
