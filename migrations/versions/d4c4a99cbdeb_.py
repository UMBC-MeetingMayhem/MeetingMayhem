"""empty message

Revision ID: d4c4a99cbdeb
Revises: 7def9d0fe456
Create Date: 2022-07-26 00:01:34.147295

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4c4a99cbdeb'
down_revision = '7def9d0fe456'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('message', sa.Column('time_am_pm', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('message', 'time_am_pm')
    # ### end Alembic commands ###
