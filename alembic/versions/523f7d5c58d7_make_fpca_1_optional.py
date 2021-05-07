"""Make FPCA+1 optional

Revision ID: 523f7d5c58d7
Revises: 5ecdd55b4af4
Create Date: 2021-05-07 15:13:07.218758

"""

# revision identifiers, used by Alembic.
revision = '523f7d5c58d7'
down_revision = '5ecdd55b4af4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Add the FPCA+1 requirement option to elections"""
    op.add_column(
            'requires_plusone',
            sa.Column(sa.Boolean, default=False)
    )

def downgrade():
    """Drop the FPCA+1 requirement option"""
    op.remove_column(
            'requires_plusone'
    )
