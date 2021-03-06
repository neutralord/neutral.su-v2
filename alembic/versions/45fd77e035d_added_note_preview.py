"""Added note preview

Revision ID: 45fd77e035d
Revises: 36e3cf26d28
Create Date: 2015-09-16 20:23:37.583948

"""

# revision identifiers, used by Alembic.
revision = '45fd77e035d'
down_revision = '36e3cf26d28'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notes', sa.Column('preview', sa.Text(), nullable=True))
    op.add_column('notes', sa.Column('read_more_label', sa.String(length=255), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('notes', 'read_more_label')
    op.drop_column('notes', 'preview')
    ### end Alembic commands ###
