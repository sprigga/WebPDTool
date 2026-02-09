-- WebPDTool Database Schema
-- MySQL 8.0+

-- Create database
CREATE DATABASE IF NOT EXISTS webpdtool
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE webpdtool;

-- Users table
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('ENGINEER', 'OPERATOR', 'ADMIN') NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Projects table
CREATE TABLE projects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_project_code (project_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Stations table
CREATE TABLE stations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    station_code VARCHAR(50) NOT NULL,
    station_name VARCHAR(100) NOT NULL,
    project_id INT NOT NULL,
    test_plan_path VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE KEY unique_station (project_id, station_code),
    INDEX idx_station_code (station_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Test Plans table (完整結構 - 包含所有 CSV 匯入欄位)
CREATE TABLE test_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    -- 專案和工站關聯
    project_id INT NOT NULL,
    station_id INT NOT NULL,
    test_plan_name VARCHAR(100),
    -- 核心測試欄位
    item_no INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    test_type VARCHAR(50) NOT NULL,
    parameters JSON,
    lower_limit DECIMAL(15,6),
    upper_limit DECIMAL(15,6),
    unit VARCHAR(20),
    enabled BOOLEAN DEFAULT TRUE,
    sequence_order INT NOT NULL,
    -- CSV 匯入欄位 (對應 PDTool4 格式)
    item_key VARCHAR(50) COMMENT 'ItemKey - 項目鍵值',
    value_type VARCHAR(50) COMMENT 'ValueType - 數值類型 (string/integer/float)',
    limit_type VARCHAR(50) COMMENT 'LimitType - 限制類型 (lower/upper/both/equality/inequality/partial/none)',
    eq_limit VARCHAR(100) COMMENT 'EqLimit - 等於限制',
    pass_or_fail VARCHAR(20) COMMENT 'PassOrFail - 通過或失敗',
    measure_value VARCHAR(100) COMMENT 'measureValue - 測量值',
    execute_name VARCHAR(100) COMMENT 'ExecuteName - 執行名稱',
    case_type VARCHAR(50) COMMENT 'case - 案例類型',
    command VARCHAR(500) COMMENT 'Command - 命令',
    timeout INT COMMENT 'Timeout - 超時時間(毫秒)',
    use_result VARCHAR(100) COMMENT 'UseResult - 使用結果',
    wait_msec INT COMMENT 'WaitmSec - 等待毫秒',
    -- 時間戳記
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- 外鍵和索引
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
    INDEX idx_station_sequence (station_id, sequence_order),
    INDEX idx_project_station (project_id, station_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Test Sessions table
CREATE TABLE test_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    serial_number VARCHAR(100) NOT NULL,
    station_id INT NOT NULL,
    user_id INT NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    final_result ENUM('PASS', 'FAIL', 'ABORT') NULL,
    total_items INT,
    pass_items INT,
    fail_items INT,
    test_duration_seconds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (station_id) REFERENCES stations(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_serial_number (serial_number),
    INDEX idx_station_time (station_id, start_time),
    INDEX idx_result (final_result)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Test Results table
CREATE TABLE test_results (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    test_plan_id INT NOT NULL,
    item_no INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    measured_value DECIMAL(15,6),
    lower_limit DECIMAL(15,6),
    upper_limit DECIMAL(15,6),
    unit VARCHAR(20),
    result ENUM('PASS', 'FAIL', 'SKIP', 'ERROR') NOT NULL,
    error_message TEXT,
    test_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_duration_ms INT,
    FOREIGN KEY (session_id) REFERENCES test_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (test_plan_id) REFERENCES test_plans(id),
    INDEX idx_session (session_id),
    INDEX idx_result (result),
    INDEX idx_test_time (test_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Configurations table
CREATE TABLE configurations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSON NOT NULL,
    category VARCHAR(50),
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- SFC Logs table
CREATE TABLE sfc_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    operation VARCHAR(50) NOT NULL,
    request_data JSON,
    response_data JSON,
    status ENUM('SUCCESS', 'FAILED', 'TIMEOUT') NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES test_sessions(id) ON DELETE CASCADE,
    INDEX idx_session (session_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Modbus Logs table
CREATE TABLE modbus_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    register_address INT NOT NULL,
    operation ENUM('READ', 'WRITE') NOT NULL,
    value VARCHAR(255),
    status ENUM('SUCCESS', 'FAILED') NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
