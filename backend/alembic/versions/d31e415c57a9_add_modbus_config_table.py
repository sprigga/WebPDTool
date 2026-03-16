"""add modbus config table

Revision ID: d31e415c57a9
Revises: 6ebc9c26834b
Create Date: 2026-03-16 14:32:45.852151

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd31e415c57a9'
down_revision: Union[str, Sequence[str], None] = '6ebc9c26834b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'modbus_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('station_id', sa.Integer(), nullable=False),
        sa.Column('server_host', sa.String(length=255), nullable=False),
        sa.Column('server_port', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('delay_seconds', sa.Float(), nullable=False),
        sa.Column('ready_status_address', sa.String(length=20), nullable=False),
        sa.Column('ready_status_length', sa.Integer(), nullable=False),
        sa.Column('read_sn_address', sa.String(length=20), nullable=False),
        sa.Column('read_sn_length', sa.Integer(), nullable=False),
        sa.Column('test_status_address', sa.String(length=20), nullable=False),
        sa.Column('test_status_length', sa.Integer(), nullable=False),
        sa.Column('in_testing_value', sa.String(length=20), nullable=False),
        sa.Column('test_finished_value', sa.String(length=20), nullable=False),
        sa.Column('test_result_address', sa.String(length=20), nullable=False),
        sa.Column('test_result_length', sa.Integer(), nullable=False),
        sa.Column('test_no_result', sa.String(length=20), nullable=False),
        sa.Column('test_pass_value', sa.String(length=20), nullable=False),
        sa.Column('test_fail_value', sa.String(length=20), nullable=False),
        sa.Column('simulation_mode', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['station_id'], ['stations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('station_id')
    )
    op.create_index(op.f('ix_modbus_configs_station_id'), 'modbus_configs', ['station_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_modbus_configs_station_id'), table_name='modbus_configs')
    op.drop_table('modbus_configs')
