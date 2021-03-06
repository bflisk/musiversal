"""updated blacklist and source tables

Revision ID: f3dfbe841160
Revises: 8c5508170501
Create Date: 2021-11-28 15:28:36.209671

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3dfbe841160'
down_revision = '8c5508170501'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('_alembic_tmp_blacklist')
    with op.batch_alter_table('blacklist', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reason', sa.String(length=120), nullable=True))
        batch_op.drop_column('track_pos')

    with op.batch_alter_table('source', schema=None) as batch_op:
        batch_op.add_column(sa.Column('art', sa.String(length=1024), nullable=True))
        batch_op.add_column(sa.Column('href', sa.String(length=1024), nullable=True))
        batch_op.drop_constraint('fk_source_playlist_id_playlist', type_='foreignkey')
        batch_op.drop_column('playlist_id')

    with op.batch_alter_table('track', schema=None) as batch_op:
        batch_op.drop_constraint('fk_track_source_id_source', type_='foreignkey')
        batch_op.drop_column('source_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('track', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_id', sa.VARCHAR(length=64), nullable=True))
        batch_op.create_foreign_key('fk_track_source_id_source', 'source', ['source_id'], ['id'])

    with op.batch_alter_table('source', schema=None) as batch_op:
        batch_op.add_column(sa.Column('playlist_id', sa.INTEGER(), nullable=True))
        batch_op.create_foreign_key('fk_source_playlist_id_playlist', 'playlist', ['playlist_id'], ['id'])
        batch_op.drop_column('href')
        batch_op.drop_column('art')

    with op.batch_alter_table('blacklist', schema=None) as batch_op:
        batch_op.add_column(sa.Column('track_pos', sa.INTEGER(), nullable=True))
        batch_op.drop_column('reason')

    op.create_table('_alembic_tmp_blacklist',
    sa.Column('playlist_id', sa.INTEGER(), nullable=True),
    sa.Column('reason', sa.VARCHAR(length=120), nullable=True),
    sa.Column('track_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['playlist_id'], ['playlist.id'], name='fk_blacklist_playlist_id_playlist'),
    sa.ForeignKeyConstraint(['track_id'], ['track.id'], name='fk_blacklist_track_id_track')
    )
    # ### end Alembic commands ###
