"""Store fas_name locally

Revision ID: 2b8f5a6f10a4
Revises: d07c5ef2d03
Create Date: 2016-01-21 16:53:38.956503

"""
from alembic import op

import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2b8f5a6f10a4"
down_revision = "d07c5ef2d03"


def upgrade():
    """ Add the fas_name column to the candidates table. """
    op.add_column("candidates", sa.Column("fas_name", sa.Unicode(150), nullable=True))


def downgrade():
    """ Drop the fas_name column from the candidates table. """
    op.drop_column("candidates", "fas_name")
