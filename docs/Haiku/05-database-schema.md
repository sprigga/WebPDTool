# 05 - 資料庫架構

## 資料庫概覽

```
資料庫：webpdtool
字元集：utf8mb4
排序規則：utf8mb4_unicode_ci
表數：7 個核心表
總列數：~100 列
主要索引：20+ 個
```

## 7 個核心表詳解

### 1. users (使用者表)

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('ADMIN', 'ENGINEER', 'OPERATOR') NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB;
```

**用途:** 使用者認證和與角色管理
**關係:** 1:N → test_sessions

**欄位說明:**
| 欄位 | 型別 | 說明 |
|------|------|------|
| username | STRING | 唯一登入名 |
| password_hash | STRING | bcrypt hash |
| role | ENUM | ADMIN/ENGINEER/OPERATOR |
| is_active | BOOL | 賬戶啟用狀態 |

**查詢示例:**
```sql
-- 按 role 分組統計
SELECT role, COUNT(*) FROM users GROUP BY role;

-- 查詢活躍工程師
SELECT * FROM users WHERE role='ENGINEER' AND is_active=TRUE;
```

### 2. projects (專案表)

```sql
CREATE TABLE projects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_project_code (project_code)
) ENGINE=InnoDB;
```

**用途:** 專案/測試活動容器
**關係:** 1:N → stations (1:N → test_plans)

**欄位說明:**
| 欄位 | 說明 |
|------|------|
| project_code | PDTool4 專案號 (唯一) |
| project_name | 顯示名稱 |
| description | 專案描述 |

**資料示例:**
```
project_code = "PROJ001"
project_name = "產品 A 測試"
description = "2026 年 Q1 生產測試"
```

### 3. stations (工站表)

```sql
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
) ENGINE=InnoDB;
```

**用途:** 定義測試位置/裝置
**關係:** N:1 ← projects (1:N → test_plans, test_sessions)

**欄位說明:**
| 欄位 | 說明 |
|------|------|
| station_code | 工站編號 |
| project_id | 所屬專案 |
| test_plan_path | 測試計劃檔案路徑 |

**資料示例:**
```
station_code = "STATION_A"
station_name = "功能測試工站 A"
project_id = 1
```

### 4. test_plans (測試計劃表 - 最複雜)

```sql
CREATE TABLE test_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,

    -- 關聯關係
    project_id INT NOT NULL,
    station_id INT NOT NULL,

    -- 基本資訊
    test_plan_name VARCHAR(100),

    -- 測試項詳情 (從 CSV 匯入)
    item_no INT,                           -- 項號
    item_name VARCHAR(255),                -- 項名稱
    test_type VARCHAR(50),                 -- PowerRead/PowerSet/... (20+ 種)
    test_time_unit VARCHAR(10),

    -- 測試 limits
    upper_limit DECIMAL(10,6),
    lower_limit DECIMAL(10,6),
    expected_value VARCHAR(255),           -- 期望值 (通常為字串)

    -- 驗證引數
    limit_type VARCHAR(20),                -- lower/upper/both/equality/inequality/partial/none
    value_type VARCHAR(20),                -- string/integer/float

    -- 測量引數 (JSON)
    parameters JSON,  -- 如：{"channel": 1, "range": "AUTO"}

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
    INDEX idx_session_id (station_id),
    INDEX idx_item_no (item_no)
) ENGINE=InnoDB;
```

**用途:** 儲存 CSV 匯入的測試規範
**關係:** N:1 ← stations, N:1 → test_results

**關鍵字段:**
| 欄位 | 型別 | 說明 | 示例 |
|------|------|------|------|
| test_type | STRING | 測量型別 | "PowerRead" |
| limit_type | STRING | 7 種驗證規則 | "both" |
| value_type | STRING | 3 種值型別 | "float" |
| parameters | JSON | 硬體引數 | {"channel": 1} |
| expected_value | STRING | 期望值 | "5.0" |

**驗證規則組合 (7 × 3 = 21 種):**
```
limit_type:
  - 'lower'      ≥ lower_limit
  - 'upper'      ≤ upper_limit
  - 'both'       lower_limit ≤ value ≤ upper_limit
  - 'equality'   value == expected_value
  - 'inequality' value != expected_value
  - 'partial'    substring match (string only)
  - 'none'       always pass

value_type:
  - 'string'     字串比較
  - 'integer'    整數比較
  - 'float'      浮點數比較
```

**資料示例:**
```json
{
  "item_no": 1,
  "item_name": "電源輸入電壓",
  "test_type": "PowerRead",
  "limit_type": "both",
  "value_type": "float",
  "lower_limit": 4.5,
  "upper_limit": 5.5,
  "parameters": {
    "channel": 1,
    "range": "AUTO",
    "timeout_ms": 5000
  }
}
```

### 5. test_sessions (測試會話表)

```sql
CREATE TABLE test_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,

    -- 關聯關係
    user_id INT NOT NULL,
    station_id INT NOT NULL,

    -- 被測物件
    serial_number VARCHAR(100),            -- DUT 序列號
    dut_sn VARCHAR(100),                   -- 裝置序列號

    -- 執行時間
    start_time TIMESTAMP,
    end_time TIMESTAMP,

    -- 執行狀態
    status ENUM('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'ABORTED'),

    -- 最終結果
    final_result ENUM('PASS', 'FAIL', 'ABORT'),

    -- 執行選項
    run_all_test BOOLEAN DEFAULT FALSE,    -- runAllTest 模式開關

    -- 錯誤資訊
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_station_id (station_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;
```

**用途:** 追蹤單次測試會話執行
**關係:** N:1 ← users, stations (1:N → test_results)

**關鍵字段:**
| 欄位 | 值 | 說明 |
|------|-----|------|
| status | PENDING → RUNNING → COMPLETED | 執行階段 |
| final_result | PASS/FAIL/ABORT | 最終結果 |
| run_all_test | true/false | 故障是否繼續 |

**生命週期:**
```
建立 → PENDING
│
啟動 → RUNNING
│
├─ 正常完成 → COMPLETED (final_result=PASS/FAIL)
├─ 使用者中止 → ABORTED (final_result=ABORT)
└─ 系統錯誤 → FAILED (final_result=FAIL)
```

**資料示例:**
```
start_time = 2026-03-11 10:00:00
end_time = 2026-03-11 10:05:30
status = COMPLETED
final_result = PASS  (所有 items 都通過)
run_all_test = false
duration = 5 分 30 秒
```

### 6. test_results (測試結果表 - 明細)

```sql
CREATE TABLE test_results (
    id INT PRIMARY KEY AUTO_INCREMENT,

    -- 關聯關係
    test_plan_id INT NOT NULL,
    test_session_id INT NOT NULL,

    -- 測試項資訊
    item_no INT,
    item_name VARCHAR(255),

    -- 測量值
    measured_value VARCHAR(255),           -- 實測值 (字串儲存)

    -- 驗證範圍
    lower_limit DECIMAL(10,6),
    upper_limit DECIMAL(10,6),

    -- 驗證引數
    limit_type VARCHAR(20),                -- 從 test_plan 複製
    value_type VARCHAR(20),

    -- 驗證結果
    validation_result ENUM('PASS', 'FAIL', 'ERROR'),
    error_message TEXT,

    -- 執行時間
    execution_time_ms INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (test_plan_id) REFERENCES test_plans(id),
    FOREIGN KEY (test_session_id) REFERENCES test_sessions(id) ON DELETE CASCADE,
    INDEX idx_test_session_id (test_session_id),
    INDEX idx_validation_result (validation_result),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;
```

**用途:** 儲存單個測試項的執行結果
**關係:** N:1 ← test_plans, test_sessions

**關鍵字段:**
| 欄位 | 值 | 說明 |
|------|-----|------|
| measured_value | "5.2" | 實測值 (字串) |
| validation_result | PASS/FAIL/ERROR | 驗證結果 |
| error_message | "Exceeds upper limit" | 錯誤原因 |
| execution_time_ms | 1250 | 執行耗時 (毫秒) |

**驗證結果含義:**
```
PASS   - 測量值在規範範圍內，符合驗證規則
FAIL   - 測量值不符合驗證規則
ERROR  - 測量過程出錯 (硬體失效、連線斷、超時等)
```

**資料示例:**
```json
{
  "item_no": 1,
  "item_name": "電源輸入電壓",
  "measured_value": "5.15",
  "lower_limit": 4.5,
  "upper_limit": 5.5,
  "limit_type": "both",
  "value_type": "float",
  "validation_result": "PASS",
  "execution_time_ms": 850
}
```

### 7. sfc_logs (SFC 日誌表)

```sql
CREATE TABLE sfc_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,

    -- 關聯
    test_session_id INT NOT NULL,

    -- 日誌資料 (JSON 格式)
    log_data JSON,

    -- 時間戳
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (test_session_id) REFERENCES test_sessions(id) ON DELETE CASCADE,
    INDEX idx_test_session_id (test_session_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;
```

**用途:** 儲存製造系統整合日誌
**關係:** N:1 ← test_sessions

**使用場景:**
- 與 SFC (生產管理系統) 整合
- 記錄生產相關的元資料
- 可選功能

**資料示例:**
```json
{
  "log_data": {
    "product_id": "SKU123456",
    "production_line": "LINE_A",
    "batch_code": "B2026031101",
    "timestamp": "2026-03-11T10:05:30Z"
  }
}
```

## 關係圖

```
users
  └─ 1:N ──→ test_sessions
             │
             ├─ N:1 ←── stations
             │             │
             │             ├─ N:1 ←── projects
             │             │
             │             └─ 1:N ──→ test_plans
             │
             ├─ 1:N ──→ test_results
             │             │
             │             └─ N:1 ←── test_plans
             │
             └─ 1:N ──→ sfc_logs
```

## 索引策略

### 效能關鍵索引

```sql
-- 認證查詢
CREATE INDEX idx_users_username ON users(username);

-- Session 查詢 (最常見)
CREATE INDEX idx_test_sessions_station_id ON test_sessions(station_id);
CREATE INDEX idx_test_sessions_status ON test_sessions(status);
CREATE INDEX idx_test_sessions_created_at ON test_sessions(created_at);

-- Result 查詢 (複雜篩選)
CREATE INDEX idx_test_results_session_id ON test_results(test_session_id);
CREATE INDEX idx_test_results_validation ON test_results(validation_result);
CREATE INDEX idx_test_results_created_at ON test_results(created_at);

-- 組合索引 (多條件查詢)
CREATE INDEX idx_composite_session_result
ON test_results(test_session_id, validation_result);
```

## 查詢示例

### 1. 獲取最近的測試會話

```sql
SELECT
    s.id, s.serial_number, s.status, s.final_result,
    s.start_time, s.end_time,
    st.station_name,
    u.username
FROM test_sessions s
JOIN stations st ON s.station_id = st.id
JOIN users u ON s.user_id = u.id
WHERE s.station_id = ? AND s.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY s.created_at DESC
LIMIT 50;
```

### 2. 統計通過率

```sql
SELECT
    DATE(s.created_at) as test_date,
    COUNT(CASE WHEN r.validation_result = 'PASS' THEN 1 END) as pass_count,
    COUNT(CASE WHEN r.validation_result = 'FAIL' THEN 1 END) as fail_count,
    COUNT(r.id) as total_count,
    ROUND(100.0 * COUNT(CASE WHEN r.validation_result = 'PASS' THEN 1 END)
          / COUNT(r.id), 2) as pass_rate
FROM test_results r
JOIN test_sessions s ON r.test_session_id = s.id
GROUP BY DATE(s.created_at)
ORDER BY test_date DESC;
```

### 3. 專案級統計

```sql
SELECT
    p.project_name,
    COUNT(DISTINCT s.id) as total_sessions,
    COUNT(CASE WHEN s.final_result = 'PASS' THEN 1 END) as pass_sessions,
    ROUND(100.0 * COUNT(CASE WHEN s.final_result = 'PASS' THEN 1 END)
          / COUNT(DISTINCT s.id), 2) as pass_rate
FROM test_sessions s
JOIN stations st ON s.station_id = st.id
JOIN projects p ON st.project_id = p.id
WHERE s.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY p.id, p.project_name
ORDER BY pass_rate DESC;
```

### 4. 故障項排行

```sql
SELECT
    tp.item_no,
    tp.item_name,
    COUNT(*) as fail_count,
    COUNT(DISTINCT s.id) as impacted_sessions
FROM test_results tr
JOIN test_plans tp ON tr.test_plan_id = tp.id
JOIN test_sessions s ON tr.test_session_id = s.id
WHERE tr.validation_result = 'FAIL'
  AND s.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY tp.id, tp.item_no, tp.item_name
ORDER BY fail_count DESC
LIMIT 20;
```

## 資料量估計

### 典型生產環境

```
Users:         50-500 個
Projects:      5-50 個
Stations:      10-200 個
Test Plans:    100-2000 個
Test Sessions: ~1000 個/月
Test Results:  ~50K-500K 個/月 (取決於每個 session 的 items 數)
SFC Logs:      可選，~100K 條/月
```

### 儲存空間

```
假設：500 個 users, 50 個 projects, 100 個 stations,
      1000 個 test_plans, 10 萬條 session, 200 萬條 result

My SQL 8.0 InnoDB:
- users:           ~200KB
- projects:        ~50KB
- stations:        ~100KB
- test_plans:      ~5MB (JSON 引數)
- test_sessions:   ~200MB
- test_results:    ~800MB
- sfc_logs:        可選 ~100-500MB
─────────────────────
總計：              ~1-1.5GB
```

## 備份和恢復

### 備份策略

```bash
# 每日備份
docker-compose exec db mysqldump -uroot -p"${MYSQL_ROOT_PASSWORD}" \
  webpdtool > backup_$(date +%Y%m%d).sql

# 增量備份 (需啟用 binary logs)
```

### 資料遷移

```bash
# 匯出
mysqldump -updtool -p webpdtool > webpdtool.sql

# 匯入
mysql -updtool -p newdb < webpdtool.sql
```

## 資料完整性

### 外鍵約束

```sql
ON DELETE CASCADE  -- 刪除 project 時刪除 stations 和 test_plans
ON DELETE SET NULL -- 刪除 user 時設 session.user_id 為 NULL (建議)
```

### 事務一致性

```python
# Python/SQLAlchemy 中
async def create_test_session(db, data):
    async with db.begin():  # 事務開始
        session = TestSession(**data)
        db.add(session)
        # 如果失敗則自動 rollback
    # 提交
```

## 效能優化建議

1. **定期清理過期資料** - 刪除 6 個月前的 test_results
2. **分割槽表** - test_results 按月份分割槽
3. **讀寫分離** - 報表查詢用從庫
4. **快取熱資料** - Redis 快取常用查詢結果
5. **批量操作** - 匯入 CSV 時使用批量 INSERT

## 下一步

- **瞭解 API**: [06-api-endpoints.md](06-api-endpoints.md)
- **學習測量系統**: [07-measurement-system.md](07-measurement-system.md)
- **後端實現**: [03-backend-structure.md](03-backend-structure.md)
