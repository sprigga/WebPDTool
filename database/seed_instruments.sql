-- Seed: Default instruments (mirrors instrument_config.py defaults)
-- Run after schema.sql: mysql -u... webpdtool < database/seed_instruments.sql
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
  name = VALUES(name),
  conn_type = VALUES(conn_type),
  conn_params = VALUES(conn_params),
  description = VALUES(description);
