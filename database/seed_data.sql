-- Seed data for WebPDTool
-- This file contains initial data for development and testing

USE webpdtool;

-- Insert default admin user (password: admin123)
-- Password hash generated using bcrypt
INSERT INTO users (username, password_hash, role, full_name, email, is_active) VALUES
('admin', '$2b$12$C40iFImcWrcBAx.iFRs1ZejI5M/tkTLJ.FaP2LFA.oH7L8uzhaEpi', 'ADMIN', 'System Administrator', 'admin@example.com', TRUE),
('engineer1', '$2b$12$C40iFImcWrcBAx.iFRs1ZejI5M/tkTLJ.FaP2LFA.oH7L8uzhaEpi', 'ENGINEER', 'Test Engineer 1', 'engineer1@example.com', TRUE),
('operator1', '$2b$12$C40iFImcWrcBAx.iFRs1ZejI5M/tkTLJ.FaP2LFA.oH7L8uzhaEpi', 'OPERATOR', 'Test Operator 1', 'operator1@example.com', TRUE);

-- Insert sample projects
INSERT INTO projects (project_code, project_name, description, is_active) VALUES
('PROJ001', 'Demo Project 1', 'Demo project for testing', TRUE),
('PROJ002', 'Demo Project 2', 'Another demo project', TRUE);

-- Insert sample stations
INSERT INTO stations (station_code, station_name, project_id, is_active) VALUES
('STA001', 'Test Station 1', 1, TRUE),
('STA002', 'Test Station 2', 1, TRUE),
('STA003', 'Test Station 3', 2, TRUE);

-- Insert sample configurations
INSERT INTO configurations (config_key, config_value, category, description, is_system) VALUES
('app_title', '"WebPDTool"', 'general', 'Application title', TRUE),
('test_timeout', '300', 'testing', 'Default test timeout in seconds', FALSE),
('modbus_enabled', 'true', 'modbus', 'Enable Modbus communication', FALSE),
('sfc_enabled', 'false', 'sfc', 'Enable SFC integration', FALSE);

-- Note: Test plans will be populated when CSV files are uploaded through the application
