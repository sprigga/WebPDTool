"""add_test_plan_name_to_test_plans

Revision ID: 9dd55b733f64
Revises: 0232af89acc2
Create Date: 2025-12-19 14:38:32.776431

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9dd55b733f64'
down_revision: Union[str, Sequence[str], None] = '0232af89acc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 新增 test_plan_name 欄位到 test_plans 表
    op.add_column('test_plans', sa.Column('test_plan_name', sa.String(length=100), nullable=True, comment='測試計劃名稱'))


def downgrade() -> None:
    """Downgrade schema."""
    # 移除 test_plan_name 欄位
    op.drop_column('test_plans', 'test_plan_name')
