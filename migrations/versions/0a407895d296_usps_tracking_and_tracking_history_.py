"""USPS Tracking and Tracking History models added

Revision ID: 0a407895d296
Revises: 3ca898bab9f7
Create Date: 2024-09-27 05:13:57.554811

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a407895d296'
down_revision = '3ca898bab9f7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('trackings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tracking_number', sa.String(length=128), nullable=True),
    sa.Column('address', sa.String(length=128), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tracking_number')
    )
    op.create_table('tracking_histories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Text(), nullable=True),
    sa.Column('details', sa.Text(), nullable=True),
    sa.Column('location', sa.Text(), nullable=True),
    sa.Column('tracking_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['tracking_id'], ['trackings.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('vending_coin', sa.INTEGER(), nullable=True))
    op.drop_constraint(None, 'CommentDislikes', type_='foreignkey')
    op.create_foreign_key(None, 'CommentDislikes', 'posts', ['comment_id'], ['id'])
    op.drop_table('tracking_histories')
    op.drop_table('trackings')
    # ### end Alembic commands ###
