"""change_measured_value_to_text

Revision ID: 6ebc9c26834b
Revises: 20260312_add_instruments_table
Create Date: 2026-03-16 09:12:24.467326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '6ebc9c26834b'
down_revision: Union[str, Sequence[str], None] = '20260312_add_instruments_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Expand measured_value from VARCHAR(100) to TEXT to support long console/command output."""
    op.alter_column('test_results', 'measured_value',
                    existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=100),
                    type_=sa.Text(),
                    existing_nullable=True)


def downgrade() -> None:
    """Revert measured_value from TEXT back to VARCHAR(100)."""
    op.alter_column('test_results', 'measured_value',
                    existing_type=sa.Text(),
                    type_=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=100),
                    existing_nullable=True)
