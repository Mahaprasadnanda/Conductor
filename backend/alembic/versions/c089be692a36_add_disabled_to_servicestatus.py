"""add_disabled_to_servicestatus

Revision ID: c089be692a36
Revises: c55351248e8b
Create Date: 2026-08-16 20:04:39.667290

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c089be692a36'
down_revision = 'c55351248e8b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use execute to alter the enum type
    op.execute("ALTER TYPE servicestatus ADD VALUE IF NOT EXISTS 'DISABLED'")

def downgrade() -> None:
    # Downgrading enums in Postgres is hard, we'll leave it
    pass
