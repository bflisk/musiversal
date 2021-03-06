"""added title column to source column

Revision ID: b35d6393e063
Revises: f3dfbe841160
Create Date: 2021-11-28 16:13:01.709545

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b35d6393e063'
down_revision = 'f3dfbe841160'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('source', schema=None) as batch_op:
        batch_op.add_column(sa.Column('title', sa.String(length=128), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('source', schema=None) as batch_op:
        batch_op.drop_column('title')

    # ### end Alembic commands ###
