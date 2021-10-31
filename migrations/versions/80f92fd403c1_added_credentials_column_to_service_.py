"""added credentials column to service table

Revision ID: 80f92fd403c1
Revises: 35a988d5dcc6
Create Date: 2021-10-31 18:20:01.735758

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '80f92fd403c1'
down_revision = '35a988d5dcc6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('service', sa.Column('credentials', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('service', 'credentials')
    # ### end Alembic commands ###
