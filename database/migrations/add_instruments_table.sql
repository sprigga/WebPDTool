-- Migration: Add instruments table for DB-backed instrument configuration
-- Replaces file/env-based InstrumentSettings singleton with runtime-editable DB records.
-- Run on existing deployments that were initialized before this table was added to schema.sql.
--
-- Usage:
--   docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool < database/migrations/add_instruments_table.sql

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

-- Seed default instruments (idempotent via ON DUPLICATE KEY UPDATE)
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
  description = VALUES(description);
