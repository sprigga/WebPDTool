# 10 - 開發指南

## 開發環境快速開始

### 前置條件

```bash
# 檢查版本
python --version          # 3.11+
node --version           # 16+
npm --version            # 8+
docker --version         # 20.10+
git --version            # 2.20+
```

### 5 分鐘快速啟動

```bash
# 1. 獲取程式碼
git clone https://github.com/company/webpdtool.git
cd webpdtool

# 2. 啟動容器 (Docker 推薦)
docker-compose up -d

# 3. 訪問應用
# 前端：http://localhost:9080
# 後端 API: http://localhost:9100
# Swagger 文件：http://localhost:9100/docs

# 4. 預設憑證
# 使用者名稱：admin
# 密碼：admin123
```

### 本地開發 (無 Docker)

```bash
# ===== 後端 =====
cd backend

# 虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依賴
pip install -e ".[dev]"

# 環境變數
export DATABASE_URL=mysql+pymysql://pdtool:pdtool123@localhost:33306/webpdtool
export SECRET_KEY=dev-secret-key
export REDIS_URL=redis://localhost:6379/0

# 執行伺服器
uvicorn app.main:app --reload --host 0.0.0.0 --port 9100

# ===== 前端 =====
cd frontend

# 依賴
npm install

# 開發伺服器 (Vite 熱更新)
npm run dev

# 訪問：http://localhost:5173
```

## 程式碼風格指南

### Python 後端

#### 匯入順序

```python
# 標準庫
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# 第三方庫
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator

# 本地應用
from app.core.database import AsyncSession, get_db
from app.core.exceptions import MeasurementExecutionError
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.test_engine import TestEngine

# 空行分隔各組
```

#### 型別提示 (強制)

```python
# ✅ 正確
async def create_test_session(
    db: AsyncSession,
    station_id: int,
    user_id: int,
    run_all_test: bool = False
) -> TestSession:
    """Create a new test session."""
    session = TestSession(
        station_id=station_id,
        user_id=user_id,
        run_all_test=run_all_test
    )
    db.add(session)
    await db.commit()
    return session

# ❌ 錯誤 (缺少型別)
async def create_test_session(db, station_id, user_id, run_all_test=False):
    # ...
```

#### 函式命名和結構

```python
# ✅ 正確
class TestEngineService:
    """Orchestrates test execution."""

    async def execute_test_session(
        self,
        session_id: int,
        measurements: List[Measurement]
    ) -> TestSessionResult:
        """
        Execute all measurements in a test session.

        Args:
            session_id: The test session ID
            measurements: List of measurements to execute

        Returns:
            TestSessionResult with final status and errors

        Raises:
            TestSessionNotFoundError: If session doesn't exist
            MeasurementExecutionError: If execution fails
        """
        # 實現...

    async def _validate_session(self, session_id: int) -> TestSession:
        """驗證會話存在且有效 (私有方法)"""
        # 實現...
```

#### 錯誤處理

```python
# ✅ 正確 - 使用 HTTPException
from fastapi import HTTPException, status

@router.get("/test-sessions/{session_id}")
async def get_test_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
) -> TestSessionResponse:
    session = await db.get(TestSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test session not found"
        )
    return TestSessionResponse.from_orm(session)

# ✅ 正確 - 使用自定義異常
from app.core.exceptions import MeasurementExecutionError

try:
    result = await measurement.execute(params)
except Exception as e:
    raise MeasurementExecutionError(
        measurement_type=measurement.type,
        error_message=str(e)
    )
```

#### Async/Await 模式

```python
# ✅ 非同步資料庫操作 (SQLAlchemy 2.0)
async def get_test_plans(
    db: AsyncSession,
    station_id: int
) -> List[TestPlan]:
    result = await db.execute(
        select(TestPlan).filter_by(station_id=station_id)
    )
    return result.scalars().all()

# ✅ 非同步服務呼叫
async def process_test_session(
    session_id: int,
    service: TestEngineService
) -> Dict[str, Any]:
    result = await service.execute_test_session(session_id)
    return result.to_dict()

# ❌ 錯誤 - 在 async 函式中使用同步操作
async def bad_example(db: Session):
    # 直接同步呼叫
    result = db.query(TestPlan).all()  # ❌ 錯誤!

    # 正確方式
    result = await db.execute(select(TestPlan))
    items = result.scalars().all()
```

### Vue 3 前端

#### 元件結構

```vue
<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useDemoApi } from '@/api/demo'
import ComponentName from '@/components/ComponentName.vue'

// 匯入完成

// ===== 狀態
const store = useAuthStore()
const { fetchData } = useDemoApi()

const count = ref(0)
const inputValue = ref('')

// ===== 計算屬性
const doubleCount = computed(() => count.value * 2)
const isLoading = computed(() => store.loading)

// ===== 方法
const increment = () => {
  count.value++
}

const handleSubmit = async () => {
  const result = await fetchData(inputValue.value)
  // 處理結果
}

// ===== 生命週期和監聽
watch(
  () => store.currentProject,
  (newProject) => {
    if (newProject) {
      // 處理變化
    }
  }
)
</script>

<template>
  <div class="page-container">
    <h1>元件標題</h1>

    <div class="content">
      <p>Count: {{ count }}</p>
      <p>Double: {{ doubleCount }}</p>

      <el-button @click="increment">增加</el-button>
    </div>
  </div>
</template>

<style scoped>
.page-container {
  padding: 20px;
}

.content {
  margin-top: 20px;
}
</style>
```

#### API 呼叫模式

```javascript
// frontend/src/api/demo.js
import { client } from './client'

export const useDemoApi = () => {
  // 獲取列表
  const getList = async (params = {}) => {
    try {
      const response = await client.get('/api/demo', { params })
      return response.data
    } catch (error) {
      console.error('Failed to fetch list:', error)
      throw error
    }
  }

  // 獲取單個
  const getById = async (id) => {
    const response = await client.get(`/api/demo/${id}`)
    return response.data
  }

  // 建立
  const create = async (data) => {
    const response = await client.post('/api/demo', data)
    return response.data
  }

  // 更新
  const update = async (id, data) => {
    const response = await client.put(`/api/demo/${id}`, data)
    return response.data
  }

  // 刪除
  const delete_ = async (id) => {
    await client.delete(`/api/demo/${id}`)
  }

  return {
    getList,
    getById,
    create,
    update,
    delete_
  }
}
```

#### 狀態管理 (Pinia)

```javascript
// frontend/src/stores/demo.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useDemoApi } from '@/api/demo'

export const useDemoStore = defineStore('demo', () => {
  const { getList, create, update, delete_ } = useDemoApi()

  // 狀態
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)
  const selectedId = ref(null)

  // 計算屬性
  const selectedItem = computed(() => {
    return items.value.find(item => item.id === selectedId.value)
  })

  const itemCount = computed(() => items.value.length)

  // 操作
  const fetchItems = async () => {
    loading.value = true
    error.value = null
    try {
      items.value = await getList()
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  const addItem = async (data) => {
    const newItem = await create(data)
    items.value.push(newItem)
    return newItem
  }

  const updateItem = async (id, data) => {
    const updated = await update(id, data)
    const index = items.value.findIndex(item => item.id === id)
    if (index !== -1) {
      items.value[index] = updated
    }
  }

  const removeItem = async (id) => {
    await delete_(id)
    items.value = items.value.filter(item => item.id !== id)
  }

  const selectItem = (id) => {
    selectedId.value = id
  }

  return {
    items,
    loading,
    error,
    selectedId,
    selectedItem,
    itemCount,
    fetchItems,
    addItem,
    updateItem,
    removeItem,
    selectItem
  }
})
```

## 常見開發任務

### 新增新的測量型別

#### 1. 建立測量實現

```python
# backend/app/measurements/implementations.py

class NewMeasurementType(BaseMeasurement):
    """實現新的測量型別"""

    type = 'NewType'

    async def prepare(self, params: Dict[str, Any]) -> None:
        """準備階段 - 初始化硬體連線等"""
        logger.info(f"Preparing {self.type}: {params}")
        # 驗證引數
        if 'device_id' not in params:
            raise ValueError("device_id is required")
        # 連線裝置
        self.device = await self.instrument_manager.connect(
            params['device_id']
        )

    async def execute(self, params: Dict[str, Any]) -> MeasurementResult:
        """執行階段 - 進行實際測量"""
        try:
            measured_value = await self.device.measure(
                duration=params.get('duration', 1000)
            )

            # 獲取限制值和型別
            limit_type = params.get('limit_type', 'both')
            value_type = params.get('value_type', 'float')
            lower_limit = params.get('lower_limit')
            upper_limit = params.get('upper_limit')

            # 驗證結果
            validation_ok, error_msg = self.validate_result(
                measured_value,
                lower_limit,
                upper_limit,
                limit_type,
                value_type
            )

            return MeasurementResult(
                value=str(measured_value),
                unit=params.get('unit', 'V'),
                success=validation_ok,
                error_message=error_msg,
                measured_value=measured_value,
                timestamp=datetime.now()
            )
        except Exception as e:
            raise MeasurementExecutionError(
                measurement_type=self.type,
                error_message=str(e)
            )

    async def cleanup(self) -> None:
        """清理階段 - 斷開連線、釋放資源"""
        if self.device:
            await self.device.disconnect()
            logger.info(f"Cleaned up {self.type}")
```

#### 2. 註冊測量型別

```python
# backend/app/measurements/registry.py

from app.measurements.implementations import NewMeasurementType

MEASUREMENT_REGISTRY = {
    'NewType': NewMeasurementType,
    # ... 其他型別
}
```

#### 3. 在測試計劃中使用

```csv
項次，品名規格，upper_limit,lower_limit,limit_type,value_type,test_type,parameters
1，測量專案 1,10,0,both,float,NewType,{"device_id": "DEV001", "duration": 1000}
```

### 新增新的 API 端點

#### 1. 建立路由

```python
# backend/app/api/demo.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.demo import DemoCreate, DemoResponse
from app.services.demo_service import DemoService

router = APIRouter(prefix="/api/demo", tags=["demo"])

@router.get("", response_model=list[DemoResponse])
async def list_demos(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """獲取示例列表"""
    service = DemoService(db)
    return await service.get_demos(skip, limit)

@router.get("/{demo_id}", response_model=DemoResponse)
async def get_demo(
    demo_id: int,
    db: AsyncSession = Depends(get_db)
):
    """獲取單個示例"""
    service = DemoService(db)
    demo = await service.get_demo(demo_id)
    if not demo:
        raise HTTPException(status_code=404, detail="Demo not found")
    return demo

@router.post("", response_model=DemoResponse)
async def create_demo(
    item: DemoCreate,
    db: AsyncSession = Depends(get_db)
):
    """建立新示例"""
    service = DemoService(db)
    return await service.create_demo(item)

@router.put("/{demo_id}", response_model=DemoResponse)
async def update_demo(
    demo_id: int,
    item: DemoCreate,
    db: AsyncSession = Depends(get_db)
):
    """更新示例"""
    service = DemoService(db)
    return await service.update_demo(demo_id, item)

@router.delete("/{demo_id}")
async def delete_demo(
    demo_id: int,
    db: AsyncSession = Depends(get_db)
):
    """刪除示例"""
    service = DemoService(db)
    await service.delete_demo(demo_id)
    return {"status": "deleted"}
```

#### 2. 註冊路由

```python
# backend/app/main.py

from app.api import demo

app = FastAPI()

# 註冊路由
app.include_router(demo.router)
```

### 新增新的前端頁面

#### 1. 建立頁面元件

```vue
<!-- frontend/src/views/DemoPage.vue -->
<script setup>
import { onMounted } from 'vue'
import { useDemoStore } from '@/stores/demo'
import DemoTable from '@/components/DemoTable.vue'
import DemoForm from '@/components/DemoForm.vue'

const store = useDemoStore()

onMounted(async () => {
  await store.fetchItems()
})

const handleAdd = async (data) => {
  await store.addItem(data)
  store.fetchItems()
}

const handleDelete = async (id) => {
  if (confirm('確認刪除？')) {
    await store.removeItem(id)
  }
}
</script>

<template>
  <div class="demo-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Demo 管理</span>
          <el-button type="primary" @click="store.showFormDialog = true">
            新增
          </el-button>
        </div>
      </template>

      <div class="content">
        <DemoTable
          v-if="!store.loading"
          :data="store.items"
          @delete="handleDelete"
        />
        <el-skeleton v-else :rows="5" />
      </div>
    </el-card>

    <DemoForm
      v-if="store.showFormDialog"
      :visible="store.showFormDialog"
      @add="handleAdd"
      @close="store.showFormDialog = false"
    />
  </div>
</template>

<style scoped>
.demo-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

#### 2. 更新路由

```javascript
// frontend/src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import DemoPage from '@/views/DemoPage.vue'

const routes = [
  {
    path: '/demo',
    component: DemoPage,
    meta: { requiresAuth: true, title: 'Demo 管理' }
  },
  // ... 其他路由
]

const router = createRouter({
  history: createWebHistory(),
  routes
})
```

## 測試和 CI/CD

### 單元測試 (pytest)

```python
# backend/tests/test_api/test_demo.py

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app
from app.models.demo import Demo

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_list_demos(client):
    """測試獲取列表"""
    response = await client.get("/api/demo")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_demo(client):
    """測試建立"""
    data = {"name": "Test", "description": "Test demo"}
    response = await client.post("/api/demo", json=data)
    assert response.status_code == 200
    assert response.json()["name"] == "Test"

@pytest.mark.asyncio
async def test_demo_not_found(client):
    """測試不存在的資源"""
    response = await client.get("/api/demo/99999")
    assert response.status_code == 404
```

### 執行測試

```bash
# 後端測試
cd backend

# 執行所有測試
pytest

# 執行特定檔案
pytest tests/test_api/test_demo.py

# 執行特定測試
pytest tests/test_api/test_demo.py::test_list_demos

# 帶覆蓋率
pytest --cov=app tests/

# 顯示詳細日誌
pytest -vv --tb=short
```

### 前端測試 (Vitest)

```javascript
// frontend/__tests__/stores/demo.test.js

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDemoStore } from '@/stores/demo'

describe('DemoStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with empty items', () => {
    const store = useDemoStore()
    expect(store.items).toEqual([])
    expect(store.loading).toBe(false)
  })

  it('adds items correctly', async () => {
    const store = useDemoStore()
    const newItem = { id: 1, name: 'Test' }

    // Mock API call
    vi.mock('@/api/demo', () => ({
      useDemoApi: () => ({
        create: vi.fn().mockResolvedValue(newItem)
      })
    }))

    await store.addItem({ name: 'Test' })
    expect(store.itemCount).toBe(1)
  })
})
```

## 常用命令參考

### 後端命令

```bash
cd backend

# 開發
uvicorn app.main:app --reload

# 生成遷移
alembic revision --autogenerate -m "add users table"

# 應用遷移
alembic upgrade head

# 回滾遷移
alembic downgrade -1

# 檢查程式碼風格
flake8 app tests

# 格式化程式碼
black app tests

# 型別檢查
mypy app

# 安全檢查
bandit -r app
```

### 前端命令

```bash
cd frontend

# 開發伺服器
npm run dev

# 構建
npm run build

# 預覽構建
npm run preview

# ESLint 檢查
npm run lint

# ESLint 修復
npm run lint -- --fix

# 型別檢查
npm run type-check
```

### Docker 命令

```bash
# 啟動
docker-compose up -d

# 停止
docker-compose down

# 檢視日誌
docker-compose logs -f backend

# 執行命令
docker-compose exec backend pytest
docker-compose exec backend alembic upgrade head

# 重新構建
docker-compose build --no-cache

# 刪除所有資料
docker-compose down -v
```

## 故障排查

### 常見錯誤

**ImportError: cannot import name**
```bash
# 解決
cd backend
pip install -e .
# 或
python -m pip install --no-cache-dir -e .
```

**Database connection refused**
```bash
# 檢查服務
docker-compose ps

# 重啟資料庫
docker-compose restart db

# 檢查連線字串
echo $DATABASE_URL
```

**npm ERR! code ERESOLVE**
```bash
# 解決
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

**Vue component not updating**
```javascript
// 確保使用 reactive 或 ref
const state = reactive({ count: 0 })

// 或
const count = ref(0)
```

## 部署指南

參考 [09-deployment-devops.md](09-deployment-devops.md) 獲取完整部署說明。

## 相關文件

- **架構**: [02-architecture.md](02-architecture.md)
- **API**: [06-api-endpoints.md](06-api-endpoints.md)
- **安全**: [08-authentication-security.md](08-authentication-security.md)
- **部署**: [09-deployment-devops.md](09-deployment-devops.md)
