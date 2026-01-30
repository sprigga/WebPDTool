# 日誌系統遷移實戰指南

**日期:** 2026-01-30
**目標:** 將 WebPDTool 現有日誌系統遷移到增強版日誌系統

---

## 快速開始

### 步驟 1: 安裝依賴

```bash
cd backend
uv add redis  # 可選，如需 Redis 支援
```

### 步驟 2: 更新環境變數

```bash
# backend/.env
LOG_LEVEL=INFO
ENABLE_JSON_LOGS=false
REDIS_ENABLED=false  # 階段一先設為 false
REDIS_URL=redis://localhost:6379/0
REDIS_LOG_TTL=3600
```

### 步驟 3: 更新 main.py

```python
# backend/app/main.py
from app.core.logging_v2 import logging_manager, set_request_context, clear_context
from app.core.config import settings
import uuid

# 初始化日誌系統 (在創建 app 之前)
logging_manager.setup_logging(
    log_level=settings.LOG_LEVEL,
    enable_redis=settings.REDIS_ENABLED,
    redis_url=settings.REDIS_URL,
    enable_json_logs=settings.ENABLE_JSON_LOGS
)

app = FastAPI(...)

# 添加日誌中間件
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # 生成請求 ID
    request_id = str(uuid.uuid4())

    # 設置上下文
    user_id = getattr(request.state, 'user_id', None)
    set_request_context(request_id, user_id)

    # 處理請求
    response = await call_next(request)

    # 清理上下文
    clear_context()

    return response

# 定期刷新日誌到 Redis (如果啟用)
if settings.REDIS_ENABLED:
    @app.on_event("startup")
    async def start_log_flusher():
        async def flush_logs():
            while True:
                await logging_manager.flush_redis_logs()
                await asyncio.sleep(1)

        asyncio.create_task(flush_logs())
```

### 步驟 4: 更新 test_engine.py

```python
# backend/app/services/test_engine.py
from app.core.logging_v2 import logging_manager, set_session_context

class TestEngine:
    async def _execute_test_session(self, session_id: int, station_id: int, db: Session):
        # ✅ 獲取會話專屬 logger
        session_logger = logging_manager.get_session_logger(session_id)
        set_session_context(session_id)

        try:
            # 會話開始
            session_logger.info("Test session started", extra={"extra_data": {
                "station_id": station_id,
                "serial_number": serial_number
            }})

            # 執行測試項目
            for idx, test_plan_item in enumerate(test_plan_items):
                session_logger.info(
                    f"Executing item {idx + 1}/{total}",
                    extra={"extra_data": {
                        "item_no": test_plan_item.item_no,
                        "item_name": test_plan_item.item_name,
                        "test_type": test_plan_item.test_type
                    }}
                )

                result = await self._execute_measurement(...)

                session_logger.info(
                    f"Item {idx + 1} result: {result.result}",
                    extra={"extra_data": {
                        "measured_value": str(result.measured_value),
                        "is_valid": result.is_valid
                    }}
                )

            # 會話完成
            session_logger.info("Test session completed", extra={"extra_data": {
                "total": total,
                "pass": pass_count,
                "fail": fail_count,
                "final_result": final_result
            }})

        except Exception as e:
            session_logger.error(f"Test session failed: {e}", exc_info=True)
            raise
```

### 步驟 5: 測試驗證

```bash
# 1. 基本功能測試
cd backend
uv run python scripts/test_logging_v2.py

# 2. 整合測試
uv run python scripts/demo_logging_integration.py

# 3. 檢查日誌文件
ls -lh logs/
cat logs/session_100.log
```

---

## 代碼遷移模式

### 模式 1: 基本日誌記錄

**舊代碼:**
```python
# ❌ 使用舊的 logging.py
from app.core.logging import logger

logger.info("Test started")
```

**新代碼:**
```python
# ✅ 使用新的 logging_v2.py
from app.core.logging_v2 import get_logger

logger = get_logger(__name__)
logger.info("Test started")
```

---

### 模式 2: 會話級別日誌

**舊代碼:**
```python
# ❌ 所有日誌混在一起
logger = logging.getLogger(__name__)
logger.info(f"Session {session_id} started")
```

**新代碼:**
```python
# ✅ 會話專屬 logger
from app.core.logging_v2 import logging_manager, set_session_context

session_logger = logging_manager.get_session_logger(session_id)
set_session_context(session_id)
session_logger.info("Session started")  # 自動記錄到 logs/session_{id}.log
```

---

### 模式 3: 結構化日誌

**舊代碼:**
```python
# ❌ 純文本日誌
logger.info(f"Test item: {item_no}, result: {result}, value: {value}")
```

**新代碼:**
```python
# ✅ 結構化日誌
logger.info("Test item completed", extra={"extra_data": {
    "item_no": item_no,
    "result": result,
    "measured_value": value,
    "test_type": "CommandTest"
}})
```

---

### 模式 4: 錯誤日誌

**舊代碼:**
```python
# ❌ 簡單錯誤記錄
try:
    result = execute_test()
except Exception as e:
    logger.error(f"Test failed: {e}")
```

**新代碼:**
```python
# ✅ 完整異常追蹤
try:
    result = execute_test()
except Exception as e:
    logger.error("Test execution failed", exc_info=True, extra={"extra_data": {
        "test_item": item_no,
        "error_type": type(e).__name__
    }})
```

---

### 模式 5: 請求上下文追蹤

**新功能（舊系統無此功能）:**

```python
# ✅ 在 API 端點自動獲取請求上下文
from app.core.logging_v2 import get_logger

logger = get_logger(__name__)

@router.post("/tests/sessions/start")
async def start_test_session(...):
    # 請求上下文已由中間件設置
    logger.info("Starting test session")
    # 日誌自動包含: request_id, user_id
```

---

## Redis 整合（可選）

### 啟用 Redis

1. **啟動 Redis 服務:**
   ```bash
   docker-compose up -d redis
   ```

2. **更新環境變數:**
   ```bash
   # backend/.env
   REDIS_ENABLED=true
   REDIS_URL=redis://redis:6379/0
   ```

3. **驗證 Redis 連接:**
   ```bash
   docker-compose exec redis redis-cli ping
   # 應該返回: PONG
   ```

### 前端 API 整合

**添加即時日誌查詢端點:**

```python
# backend/app/api/tests.py
from app.core.logging_v2 import logging_manager

@router.get("/sessions/{session_id}/logs")
async def get_session_logs(
    session_id: int,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取測試會話即時日誌"""
    # 驗證權限
    session = db.query(TestSessionModel).filter_by(id=session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 從 Redis 獲取日誌
    logs = await logging_manager.get_session_logs(session_id, limit)

    return {"logs": logs, "count": len(logs)}
```

**前端實時日誌顯示:**

```vue
<!-- frontend/src/views/TestMain.vue -->
<template>
  <el-card class="log-panel">
    <template #header>
      <div class="log-header">
        <span>測試執行日誌</span>
        <el-switch v-model="autoScroll" active-text="自動滾動" />
      </div>
    </template>
    <el-scrollbar ref="scrollbarRef" height="400px">
      <div v-for="log in logs" :key="log.timestamp" class="log-entry">
        <span class="log-time">{{ formatTime(log.timestamp) }}</span>
        <el-tag :type="getLogTypeTag(log.level)" size="small">
          {{ log.level }}
        </el-tag>
        <span class="log-message">{{ log.message }}</span>
      </div>
    </el-scrollbar>
  </el-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { api } from '@/api/client'

const logs = ref([])
const autoScroll = ref(true)
const scrollbarRef = ref(null)
let logInterval = null

const fetchLogs = async () => {
  if (!currentSessionId.value) return

  try {
    const response = await api.get(
      `/api/tests/sessions/${currentSessionId.value}/logs?limit=50`
    )
    logs.value = response.data.logs

    // 自動滾動到底部
    if (autoScroll.value && scrollbarRef.value) {
      scrollbarRef.value.setScrollTop(scrollbarRef.value.wrapRef.scrollHeight)
    }
  } catch (error) {
    console.error('Failed to fetch logs:', error)
  }
}

const getLogTypeTag = (level) => {
  const tagMap = {
    'DEBUG': '',
    'INFO': 'success',
    'WARNING': 'warning',
    'ERROR': 'danger'
  }
  return tagMap[level] || ''
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('zh-TW')
}

onMounted(() => {
  logInterval = setInterval(fetchLogs, 1000)  // 每秒輪詢
})

onUnmounted(() => {
  if (logInterval) clearInterval(logInterval)
})
</script>

<style scoped>
.log-panel {
  margin-top: 20px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-entry {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  padding: 4px 8px;
  border-bottom: 1px solid #f0f0f0;
}

.log-time {
  color: #909399;
  margin-right: 8px;
}

.log-message {
  margin-left: 8px;
}
</style>
```

---

## 性能優化建議

### 1. 日誌級別調整

```python
# 生產環境
LOG_LEVEL=WARNING  # 只記錄警告和錯誤

# 開發環境
LOG_LEVEL=DEBUG  # 記錄所有日誌

# 測試環境
LOG_LEVEL=INFO  # 記錄一般信息
```

### 2. 日誌輪轉配置

```python
# backend/app/core/logging_v2.py
file_handler = RotatingFileHandler(
    self.log_dir / "webpdtool.log",
    maxBytes=10 * 1024 * 1024,  # 10MB per file
    backupCount=10               # Keep 10 backup files
)
```

### 3. Redis 記憶體管理

```yaml
# docker-compose.yml
redis:
  command: >
    redis-server
    --maxmemory 256mb           # 限制記憶體使用
    --maxmemory-policy allkeys-lru  # LRU 淘汰策略
```

### 4. 會話日誌清理

```bash
# scripts/cleanup_logs.sh
#!/bin/bash
# 刪除 7 天前的會話日誌
find /app/logs -name "session_*.log" -mtime +7 -delete

# Crontab 配置
0 3 * * * /app/scripts/cleanup_logs.sh  # 每天凌晨 3 點執行
```

---

## 故障排查

### 問題 1: Redis 連接失敗

**症狀:**
```
Error 111 connecting to localhost:6379. Connect call failed ('127.0.0.1', 6379).
```

**解決方案:**
```bash
# 檢查 Redis 是否運行
docker-compose ps redis

# 啟動 Redis
docker-compose up -d redis

# 檢查連接
docker-compose exec redis redis-cli ping
```

---

### 問題 2: 日誌文件權限錯誤

**症狀:**
```
PermissionError: [Errno 13] Permission denied: '/app/logs/session_100.log'
```

**解決方案:**
```bash
# 修正權限
chmod -R 755 logs/
chown -R $(whoami) logs/
```

---

### 問題 3: 日誌不顯示上下文

**症狀:**
日誌中缺少 `request_id`, `session_id` 等上下文資訊。

**解決方案:**
確保在使用 logger 前設置上下文：

```python
# ✓ 正確
from app.core.logging_v2 import set_session_context

set_session_context(session_id)
logger.info("Test started")  # 會包含 session_id

# ✗ 錯誤
logger.info("Test started")  # 缺少 session_id
```

---

## 完整測試清單

### ✅ 功能測試

- [ ] 基本日誌記錄（INFO, WARNING, ERROR）
- [ ] 會話級別日誌隔離
- [ ] 上下文追蹤（request_id, session_id, user_id）
- [ ] 結構化日誌（extra_data）
- [ ] 異常追蹤（exc_info=True）
- [ ] 並發日誌安全

### ✅ Redis 整合測試（可選）

- [ ] Redis 連接正常
- [ ] 日誌寫入 Redis
- [ ] 日誌從 Redis 讀取
- [ ] TTL 自動過期
- [ ] 批量刷新性能

### ✅ 性能測試

- [ ] 1000 條/秒日誌寫入無阻塞
- [ ] 日誌文件輪轉正常
- [ ] Redis 記憶體使用 < 256MB
- [ ] 會話日誌清理正常

### ✅ 整合測試

- [ ] main.py 中間件正常
- [ ] test_engine.py 會話日誌正常
- [ ] API 日誌查詢正常
- [ ] 前端即時日誌顯示正常

---

## 遷移時間表

### 第 1 天：基礎整合（無 Redis）

- ✅ 安裝依賴
- ✅ 更新 main.py
- ✅ 更新 test_engine.py
- ✅ 基本測試驗證

### 第 2 天：Redis 整合

- ⏳ 啟動 Redis 服務
- ⏳ 配置環境變數
- ⏳ 添加日誌查詢 API
- ⏳ Redis 測試驗證

### 第 3 天：前端整合

- ⏳ 實現即時日誌面板
- ⏳ 測試輪詢/WebSocket
- ⏳ UI/UX 優化

### 第 4 天：測試和部署

- ⏳ 完整測試流程
- ⏳ 性能測試
- ⏳ 生產環境部署

---

## 回滾計劃

如果遷移遇到問題，可以快速回滾：

```python
# backend/app/main.py
# 註釋新日誌系統
# from app.core.logging_v2 import logging_manager
# logging_manager.setup_logging(...)

# 恢復舊日誌系統
from app.core.logging import logger
```

---

## 總結

### 關鍵改進

1. **會話隔離** - 每個測試會話獨立日誌文件
2. **上下文追蹤** - 自動注入 request_id, session_id, user_id
3. **結構化日誌** - JSON 格式，方便查詢和分析
4. **實時監控** - Redis 支援即時日誌流
5. **異步安全** - 無全域鎖，支援高並發

### 後續優化

- [ ] Elasticsearch 整合（大規模日誌搜尋）
- [ ] Grafana 整合（日誌視覺化）
- [ ] OpenTelemetry 整合（分散式追蹤）
- [ ] 日誌壓縮和歸檔自動化

---

**文檔版本:** 1.0
**最後更新:** 2026-01-30
