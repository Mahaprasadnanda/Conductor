"""Add ServiceAuthMode to Service

Revision ID: 2462e1a85c97
Revises: 7c86dc976bbe
Create Date: 2026-08-02 20:14:13.612552

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2462e1a85c97'
down_revision = '7c86dc976bbe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    serviceauthmode = sa.Enum('PUBLIC', 'JWT_REQUIRED', 'API_KEY_REQUIRED', 'DISABLED', name='serviceauthmode')
    serviceauthmode.create(op.get_bind(), checkfirst=True)
    op.add_column('services', sa.Column('authentication_mode', serviceauthmode, nullable=False, server_default='JWT_REQUIRED'))

def downgrade() -> None:
    op.drop_column('services', 'authentication_mode')
    serviceauthmode = sa.Enum('PUBLIC', 'JWT_REQUIRED', 'API_KEY_REQUIRED', 'DISABLED', name='serviceauthmode')
    serviceauthmode.drop(op.get_bind(), checkfirst=True)
