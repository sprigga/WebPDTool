-- Add switch_mode column to test_plans table
-- Migration: Add instrument/switch mode field for dynamic parameter form
-- Date: 2026-02-09

USE webpdtool;

-- Add switch_mode column
ALTER TABLE test_plans
ADD COLUMN switch_mode VARCHAR(50) NULL COMMENT 'Instrument/switch mode (DAQ973A, MODEL2303, comport, etc.)'
AFTER test_type;

-- Create index for better query performance
CREATE INDEX idx_test_plans_switch_mode ON test_plans(switch_mode);

-- Verify the change
SHOW COLUMNS FROM test_plans LIKE 'switch_mode';
