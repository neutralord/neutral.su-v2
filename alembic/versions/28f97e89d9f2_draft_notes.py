"""Draft notes

Revision ID: 28f97e89d9f2
Revises: 45fd77e035d
Create Date: 2017-03-06 13:03:18.967460

"""

# revision identifiers, used by Alembic.
revision = '28f97e89d9f2'
down_revision = '45fd77e035d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notes', sa.Column('is_draft', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('notes', 'is_draft')
    # ### end Alembic commands ###
