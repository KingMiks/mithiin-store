"""add stripe session id to order

Revision ID: aab4c7edf88b
Revises: b02180450855
Create Date: 2026-10-06 10:27:21.832596

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aab4c7edf88b'
down_revision = 'b02180450855'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stripe_session_id', sa.String(length=200), nullable=True))
        batch_op.create_unique_constraint('uq_order_stripe_session_id', ['stripe_session_id'])


def downgrade():
    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.drop_constraint('uq_order_stripe_session_id', type_='unique')
        batch_op.drop_column('stripe_session_id')
