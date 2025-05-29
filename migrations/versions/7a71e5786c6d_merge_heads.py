"""merge heads

Revision ID: 7a71e5786c6d
Revises: a6e17595c115, 2cda74106066
Create Date: 2025-05-29 15:23:01.176135

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a71e5786c6d'
down_revision: Union[str, None] = ('a6e17595c115', '2cda74106066')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
