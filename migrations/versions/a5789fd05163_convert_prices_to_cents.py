"""convert prices to cents

Revision ID: a5789fd05163
Revises: aab4c7edf88b
Create Date: 2026-11-06 15:16:22.251585

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5789fd05163'
down_revision = 'aab4c7edf88b'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('UPDATE "order" SET price_paid = price_paid * 100')
    op.execute('UPDATE product SET price = price * 100')


def downgrade():
    op.execute('UPDATE "order" SET price_paid = price_paid / 100')
    op.execute('UPDATE product SET price = price / 100')
