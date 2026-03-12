"""add_instruments_table

Add instruments table for DB-backed instrument configuration.
Replaces file/env-based InstrumentSettings singleton with runtime-editable DB records.

Revision ID: 20260312_add_instruments_table
Revises: 9dd55b733f64
Create Date: 2026-03-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260312_add_instruments_table'
down_revision: Union[str, Sequence[str], None] = 'a8124fdea538'  # Latest migration in the chain
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create instruments table and seed default data."""
    # Create instruments table with MySQL-specific features
    # Using raw SQL for: JSON type, TINYINT(1), and proper charset/collation
    op.execute("""
        CREATE TABLE IF NOT EXISTS instruments (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            instrument_id   VARCHAR(64) NOT NULL UNIQUE COMMENT 'Logical ID, e.g. DAQ973A_1',
            instrument_type VARCHAR(64) NOT NULL COMMENT 'Driver type, e.g. DAQ973A',
            name            VARCHAR(128) NOT NULL,
            conn_type       VARCHAR(32) NOT NULL COMMENT 'VISA | SERIAL | TCPIP_SOCKET | GPIB | LOCAL',
            conn_params     JSON NOT NULL COMMENT 'Connection parameters (address, port, baudrate…)',
            enabled         TINYINT(1) NOT NULL DEFAULT 1,
            description     TEXT,
            created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_instruments_type (instrument_type),
            INDEX idx_instruments_enabled (enabled)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
          COMMENT='Instrument connection configurations (DB-backed, runtime editable)';
    """)

    # Seed default instruments (idempotent via ON DUPLICATE KEY UPDATE)
    # This allows the migration to be re-run safely on deployments that already
    # executed the raw SQL migration (database/migrations/add_instruments_table.sql)
    #
    # 注意：使用 DBAPI connection 直接執行 SQL，完全繞過 SQLAlchemy 的參數解析，
    # 避免 JSON 中的 ":5000" 被誤解為 bind parameter。
    from sqlalchemy.engine import Connection
    conn = op.get_bind()
    if isinstance(conn, Connection):
        # SQLAlchemy Connection - use the raw DBAPI connection
        dbapi_conn = conn.connection
        cursor = dbapi_conn.cursor()
    else:
        # Already a DBAPI connection
        cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO instruments (instrument_id, instrument_type, name, conn_type, conn_params, enabled, description)
        VALUES
          ('DAQ973A_1', 'DAQ973A', 'Keysight DAQ973A #1',
           'VISA', '{"address":"TCPIP0::192.168.1.10::inst0::INSTR","timeout":5000}',
           0, 'Keysight DAQ973A data acquisition system'),

          ('MODEL2303_1', 'MODEL2303', 'Keysight 2303 Power Supply #1',
           'VISA', '{"address":"TCPIP0::192.168.1.11::inst0::INSTR","timeout":5000}',
           0, 'Keysight 2303 power supply'),

          ('console_1', 'console', 'Console Command (default)',
           'LOCAL', '{"address":"local://console"}',
           1, 'Virtual instrument for OS subprocess command execution'),

          ('comport_1', 'comport', 'COM Port Command (default)',
           'LOCAL', '{"address":"local://comport"}',
           1, 'Virtual instrument for serial port command execution'),

          ('tcpip_1', 'tcpip', 'TCP/IP Command (default)',
           'LOCAL', '{"address":"local://tcpip"}',
           1, 'Virtual instrument for TCP/IP socket command execution')
        ON DUPLICATE KEY UPDATE
          name        = VALUES(name),
          conn_type   = VALUES(conn_type),
          conn_params = VALUES(conn_params),
          description = VALUES(description)
    """)
    cursor.close()


def downgrade() -> None:
    """Downgrade schema: Remove instruments table."""
    op.execute("DROP TABLE IF EXISTS instruments;")
