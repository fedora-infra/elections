"""Add badge support to elections

Revision ID: 5ecdd55b4af4
Revises: 2b8f5a6f10a4
Create Date: 2019-03-18 12:21:59.536380

"""

# revision identifiers, used by Alembic.
revision = '5ecdd55b4af4'
down_revision = '2b8f5a6f10a4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    """ Add the url_badge column to the Elections table. """
    op.add_column(
        'elections',
        sa.Column('url_badge', sa.Unicode(250), nullable=True)
    )


def downgrade():
    """ Drop the url_badge column from the Elections table. """
    op.drop_column('elections', 'url_badge')
