"""add_nats_fields_to_user_postgres

Revision ID: a6e17595c115
Revises: 2cda74106066
Create Date: 2025-05-29 15:22:05.641607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6e17595c115'
down_revision: Union[str, None] = '2cda74106066'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
