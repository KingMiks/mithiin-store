"""rename cut to shape

Revision ID: 15ff54a59b25
Revises: a5789fd05163
Create Date: 2026-11-16 12:48:40.287969

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15ff54a59b25'
down_revision = 'a5789fd05163'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("product") as batch_op:
        batch_op.alter_column("cut", new_column_name="shape")


def downgrade():
    with op.batch_alter_table("product") as batch_op:
        batch_op.alter_column("shape", new_column_name="cut")
