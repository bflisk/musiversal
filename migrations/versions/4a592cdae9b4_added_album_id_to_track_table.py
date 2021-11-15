"""added album id to track table

Revision ID: 4a592cdae9b4
Revises: 017900da4c8c
Create Date: 2021-11-14 17:14:45.417663

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a592cdae9b4'
down_revision = '017900da4c8c'
branch_labels = None
depends_on = None

naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('album', schema=None, naming_convention=naming_convention) as batch_op:
        batch_op.drop_constraint('fk_album_track_id_track', type_='foreignkey')
        batch_op.drop_column('track_id')

    with op.batch_alter_table('artist', schema=None, naming_convention=naming_convention) as batch_op:
        batch_op.add_column(sa.Column('href', sa.String(length=1024), nullable=True))

    with op.batch_alter_table('track', schema=None, naming_convention=naming_convention) as batch_op:
        batch_op.add_column(sa.Column('album_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'album', ['album_id'], ['id'])
        batch_op.create_foreign_key(None, 'source', ['source_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('track', schema=None, naming_convention=naming_convention) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('album_id')

    with op.batch_alter_table('artist', schema=None, naming_convention=naming_convention) as batch_op:
        batch_op.drop_column('href')

    with op.batch_alter_table('album', schema=None, naming_convention=naming_convention) as batch_op:
        batch_op.add_column(sa.Column('track_id', sa.INTEGER(), nullable=True))
        batch_op.create_foreign_key(None, 'track', ['track_id'], ['id'])

    # ### end Alembic commands ###