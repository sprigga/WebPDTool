"""add_project_id_to_test_plans

Revision ID: a8124fdea538
Revises: 20250109_change_measured_value
Create Date: 2026-01-29 15:18:44.225794

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8124fdea538'
down_revision: Union[str, Sequence[str], None] = '20250109_change_measured_value'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add project_id column to test_plans table if it doesn't exist
    op.execute("""
        ALTER TABLE test_plans
        ADD COLUMN IF NOT EXISTS project_id INT NOT NULL AFTER id,
        ADD CONSTRAINT fk_test_plans_project_id FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove project_id column
    op.execute("""
        ALTER TABLE test_plans
        DROP FOREIGN KEY IF EXISTS fk_test_plans_project_id,
        DROP COLUMN IF EXISTS project_id
    """)
