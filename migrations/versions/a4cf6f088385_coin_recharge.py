"""coin_recharge

Revision ID: a4cf6f088385
Revises: f70a22b6019b
Create Date: 2023-10-17 02:50:35.612443

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4cf6f088385'
down_revision = 'f70a22b6019b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('CoinRechargeCodes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('amount', sa.Integer(), nullable=True),
    sa.Column('moderator_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['moderator_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_CoinRechargeCodes_timestamp'), 'CoinRechargeCodes', ['timestamp'], unique=False)
    op.create_table('CoinTransactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.String(), nullable=True),
    sa.Column('amount', sa.Integer(), nullable=True),
    sa.Column('sender_id', sa.Integer(), nullable=True),
    sa.Column('receiver_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_CoinTransactions_timestamp'), 'CoinTransactions', ['timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_CoinTransactions_timestamp'), table_name='CoinTransactions')
    op.drop_table('CoinTransactions')
    op.drop_index(op.f('ix_CoinRechargeCodes_timestamp'), table_name='CoinRechargeCodes')
    op.drop_table('CoinRechargeCodes')
    # ### end Alembic commands ###
