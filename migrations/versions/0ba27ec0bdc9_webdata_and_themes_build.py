"""WebData and Themes Build

Revision ID: 0ba27ec0bdc9
Revises: b1419510dbdf
Create Date: 2023-06-24 11:24:02.189140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ba27ec0bdc9'
down_revision = 'b1419510dbdf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('web_datas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('name_abbreviation', sa.String(length=32), nullable=True),
    sa.Column('logo', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('name_abbreviation')
    )
    op.create_table('themes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('first', sa.String(length=32), nullable=True),
    sa.Column('second', sa.String(length=32), nullable=True),
    sa.Column('third', sa.String(length=32), nullable=True),
    sa.Column('forth', sa.String(length=32), nullable=True),
    sa.Column('web_data_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['web_data_id'], ['web_datas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('themes')
    op.drop_table('web_datas')
    # ### end Alembic commands ###
