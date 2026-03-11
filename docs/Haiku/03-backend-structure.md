# 03 - 後端結構

## 目錄結構概覽

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 應用入口
│   ├── config.py               # 配置管理
│   ├── dependencies.py         # 依賴注入定義
│   │
│   ├── api/                    # API 層 (9+ 路由)
│   │   ├── __init__.py
│   │   ├── auth.py             # JWT 認證
│   │   ├── users.py            # 使用者 CRUD
│   │   ├── projects.py         # 專案管理
│   │   ├── stations.py         # 工站管理
│   │   ├── testplans.py        # 測試計劃
│   │   ├── tests.py            # 測試執行
│   │   ├── measurements.py     # 測量控制
│   │   ├── dut_control.py      # 裝置控制
│   │   └── results/            # 結果子路由 (7 個)
│   │       ├── sessions.py
│   │       ├── measurements.py
│   │       ├── summary.py
│   │       ├── export.py
│   │       ├── cleanup.py
│   │       ├── reports.py
│   │       └── analysis.py
│   │
│   ├── services/               # Service 層 (業務邏輯)
│   │   ├── __init__.py
│   │   ├── test_engine.py      # 測試編排 (核心)
│   │   ├── measurement_service.py # 測量執行 (關鍵)
│   │   ├── instrument_manager.py  # 硬體管理 (Singleton)
│   │   ├── test_plan_service.py   # 計劃操作
│   │   ├── report_service.py      # 報表生成
│   │   ├── auth.py                # 認證服務
│   │   ├── dut_comms/             # 裝置通訊
│   │   └── instruments/           # 硬體驅動
│   │       ├── base.py
│   │       └── implementations/
│   │
│   ├── measurements/           # 測量抽象層 (核心)
│   │   ├── __init__.py
│   │   ├── base.py             # BaseMeasurement (抽象)
│   │   ├── registry.py         # 測量註冊表
│   │   └── implementations.py  # 20+ 測量實現
│   │
│   ├── models/                 # ORM 模型 (7 表)
│   │   ├── __init__.py
│   │   ├── user.py             # User 表 + UserRole 列舉
│   │   ├── project.py          # Project 表
│   │   ├── station.py          # Station 表
│   │   ├── testplan.py         # TestPlan 表 (複雜)
│   │   ├── test_session.py     # TestSession 表 + enums
│   │   ├── test_result.py      # TestResult 表
│   │   └── sfc_log.py          # SFCLog 表
│   │
│   ├── schemas/                # Pydantic 驗證
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── station.py
│   │   ├── testplan.py
│   │   ├── test_session.py
│   │   ├── test_result.py
│   │   └── common.py
│   │
│   ├── core/                   # 核心模組
│   │   ├── __init__.py
│   │   ├── database.py         # SQLAlchemy setup
│   │   ├── security.py         # JWT + Password
│   │   ├── logging_v2.py       # 增強日誌系統 (新)
│   │   ├── exceptions.py       # 自定義異常
│   │   ├── constants.py        # 常量定義
│   │   ├── instrument_config.py # 硬體配置
│   │   └── api_helpers.py      # API 輔助函式
│   │
│   ├── utils/                  # 工具函式
│   │   ├── __init__.py
│   │   ├── csv_parser.py       # CSV 匯入解析
│   │   └── validators.py       # 驗證邏輯
│   │
│   └── config/                 # 配置目錄
│       └── (配置檔案)
│
├── alembic/                    # 資料庫遷移
│   ├── versions/
│   └── env.py
│
├── tests/                      # 測試目錄
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_measurements/
│
├── pyproject.toml              # 專案配置 + 依賴
├── alembic.ini                 # Alembic 配置
├── Dockerfile                  # Docker 構建
└── .env                        # 環境變數
```

## API 層詳解

### 模組分佈

| 模組 | 路由字首 | 功能 | 端點數 |
|------|---------|------|--------|
| `auth.py` | `/api/auth` | JWT 認證 | 3 |
| `users.py` | `/api/users` | 使用者 CRUD | 6 |
| `projects.py` | `/api/projects` | 專案管理 | 4 |
| `stations.py` | `/api/stations` | 工站管理 | 4 |
| `testplans.py` | `/api/testplans` | 測試計劃 | 5 |
| `tests.py` | `/api/tests` | 測試執行 | 5 |
| `measurements.py` | `/api/measurements` | 測量控制 | 3 |
| `dut_control.py` | `/api/dut` | 裝置控制 | 3 |
| `results/` | `/api/tests/results` | 結果分析 | 10+ |

### 設計模式

```python
# FastAPI APIRouter 模式
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/items", tags=["items"])

@router.get("/")
async def list_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """獲取列表 - 帶分頁和過濾"""
    return await service.get_items(db, current_user)

@router.post("/")
async def create_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """建立新項 - 帶權限檢查"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="權限不足")
    return await service.create_item(db, item)
```

## Service 層詳解

### TestEngine (測試編排核心)

**檔案:** `app/services/test_engine.py` (500+ 行)

**責任:**
- 管理 test session 生命週期
- 迭代執行 test items
- 追蹤執行時間
- 實現 runAllTest 邏輯

**關鍵方法:**

```python
class TestEngine:
    async def start_test_session(
        session_id: int,
        serial_number: str,
        station_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """啟動測試 session"""

    async def execute_test_item(
        test_plan_id: int,
        params: Dict[str, Any]
    ) -> MeasurementResult:
        """執行單個 test item"""

    async def pause_test_session(session_id: int):
        """暫停執行"""

    async def abort_test_session(session_id: int):
        """中止執行"""
```

### MeasurementService (測量執行關鍵)

**檔案:** `app/services/measurement_service.py` (81KB, 最重要!)

**責任:**
- 橋接 TestEngine 和測量實現
- 引數驗證和準備
- 呼叫 3 階段生命週期
- 實現驗證邏輯
- runAllTest 錯誤收集

**關鍵方法:**

```python
class MeasurementService:
    async def execute_measurement(
        test_plan: TestPlan,
        params: Dict[str, Any]
    ) -> Tuple[bool, MeasurementResult]:
        """執行單次測量"""

    async def validate_measurement(
        result: MeasurementResult,
        test_plan: TestPlan
    ) -> Tuple[bool, str]:
        """驗證測量結果 [PDTool4 邏輯](../07-measurement-system.md)"""
```

### InstrumentManager (硬體管理 Singleton)

**檔案:** `app/services/instrument_manager.py`

**責任:**
- 單例模式確保單一連線池
- 管理硬體連線
- 命令佇列執行
- 狀態追蹤 (IDLE/BUSY/ERROR)

**關鍵方法:**

```python
class InstrumentManager:
    """Singleton: 全域性只有一個例項"""

    async def connect(instrument_id: str, config: Dict):
        """建立連線"""

    async def send_command(instrument_id: str, command: str) -> str:
        """傳送命令獲取響應"""

    async def get_status(instrument_id: str) -> str:
        """獲取狀態"""
```

### 其他核心 Service

**TestPlanService**
- `import_test_plan()` - CSV 匯入
- `get_test_plan()` - 獲取計劃
- `validate_test_plan()` - 驗證有效性

**ReportService**
- `generate_summary_report()` - 生成摘要
- `calculate_statistics()` - 統計分析
- `export_data()` - 匯出資料

**AuthService**
- `authenticate_user()` - 使用者認證
- `create_access_token()` - 生成 JWT
- `verify_password()` - 密碼驗證

## 測量抽象層詳解

### BaseMeasurement (抽象基類)

**檔案:** `app/measurements/base.py` (400+ 行)

```python
class BaseMeasurement(ABC):
    """所有測量的基類"""

    async def prepare(self, params: Dict[str, Any]) -> None:
        """階段 1: 配置硬體和引數"""
        raise NotImplementedError

    async def execute(self, params: Dict[str, Any]) -> MeasurementResult:
        """階段 2: 執行測量和收集資料"""
        raise NotImplementedError

    async def cleanup(self) -> None:
        """階段 3: 重置狀態和釋放資源"""
        raise NotImplementedError

    def validate_result(
        self,
        measured_value: Any,
        lower_limit: Optional[Any],
        upper_limit: Optional[Any],
        limit_type: str = 'both',
        value_type: str = 'float'
    ) -> Tuple[bool, str]:
        """PDTool4 驗證邏輯"""
        # 支援 7 種 limit_type
        # 支援 3 種 value_type
```

### MeasurementResult (資料類)

```python
@dataclass
class MeasurementResult:
    """測量結果統一格式"""
    value: Optional[Union[str, int, float]]
    unit: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
```

### 測量註冊表

**檔案:** `app/measurements/registry.py`

```python
# 20+ 測量型別註冊
MEASUREMENT_REGISTRY = {
    'PowerRead': PowerReadMeasurement,
    'PowerSet': PowerSetMeasurement,
    'CommandTest': CommandTestMeasurement,
    'SFCtest': SFCMeasurement,
    'getSN': GetSNMeasurement,
    'OPjudge': OPJudgeMeasurement,
    'Other': OtherMeasurement,
    # ... 13+ 更多型別
}

def get_measurement_class(test_type: str) -> Type[BaseMeasurement]:
    """執行時獲取測量類"""
    return MEASUREMENT_REGISTRY.get(test_type, OtherMeasurement)
```

### 實現示例：PowerReadMeasurement

```python
class PowerReadMeasurement(BaseMeasurement):
    """讀取電源功率的測量"""

    async def prepare(self, params: Dict[str, Any]) -> None:
        # 解析引數
        channel = params.get('channel', 1)
        range_val = params.get('range', 'AUTO')

        # 配置硬體
        await self.instrument.select_channel(channel)
        await self.instrument.set_range(range_val)

    async def execute(self, params: Dict[str, Any]) -> MeasurementResult:
        try:
            # 讀取功率
            reading = await self.instrument.read_power()

            return MeasurementResult(
                value=reading,
                unit='W',
                success=True,
                timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            return MeasurementResult(
                value=None,
                success=False,
                error=str(e)
            )

    async def cleanup(self) -> None:
        # 重置狀態
        await self.instrument.reset()
```

## ORM 資料模型

### 7 個核心表

```python
# 1. User (認證)
class User(Base):
    id: int          # PK
    username: str    # UNIQUE
    password_hash: str
    role: UserRole   # ENUM(ADMIN,ENGINEER,OPERATOR)
    full_name: str
    email: str
    is_active: bool
    created_at, updated_at

# 2. Project (專案)
class Project(Base):
    id: int
    project_code: str        # UNIQUE
    project_name: str
    description: str
    is_active: bool
    created_at, updated_at

# 3. Station (工站)
class Station(Base):
    id: int
    station_code: str
    station_name: str
    project_id: int (FK)
    test_plan_path: str
    is_active: bool
    created_at, updated_at

# 4. TestPlan (測試計劃 - 從 CSV 匯入)
class TestPlan(Base):
    id: int
    project_id, station_id: int (FK)
    item_no, item_name: str
    test_type: str
    upper_limit, lower_limit: Optional[float]
    expected_value: Optional[str]
    limit_type: str       # 7 種
    value_type: str       # 3 種
    parameters: JSON      # 儲存 JSON 引數

# 5. TestSession (測試會話 - 執行追蹤)
class TestSession(Base):
    id: int
    user_id, station_id: int (FK)
    serial_number: str
    start_time, end_time: datetime
    status: SessionStatus  # PENDING/RUNNING/COMPLETED/FAILED/ABORTED
    final_result: Result   # PASS/FAIL/ABORT
    run_all_test: bool
    error_message: str

# 6. TestResult (個別結果)
class TestResult(Base):
    id: int
    test_plan_id, test_session_id: int (FK)
    item_no, item_name: str
    measured_value: str
    lower_limit, upper_limit: Optional[float]
    limit_type, value_type: str
    validation_result: ItemResult  # PASS/FAIL/ERROR
    error_message: str
    execution_time_ms: float

# 7. SFCLog (製造整合)
class SFCLog(Base):
    id: int
    session_id: int (FK)
    log_data: JSON
    timestamp: datetime
```

## 配置管理

**檔案:** `app/config.py`

```python
class Settings(BaseSettings):
    """應用配置 (從.env 讀取)"""

    # 資料庫
    DB_HOST: str = "db"
    DB_PORT: int = 3306
    DB_USER: str = "pdtool"
    DATABASE_ECHO: bool = False

    # 安全
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 小時

    # 日誌
    LOG_LEVEL: str = "INFO"
    REDIS_ENABLED: bool = True
    REDIS_URL: str = "redis://redis:6379/0"

    # 應用
    APP_NAME: str = "WebPDTool"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
```

## 核心模組

### database.py (SQLAlchemy 設定)
```python
# 非同步資料庫引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DATABASE_ECHO,
)

# 非同步會話工廠
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """依賴注入提供 async session"""
    async with AsyncSessionLocal() as session:
        yield session
```

### security.py (JWT 和密碼)
```python
# JWT token 生成
def create_access_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

# 密碼哈希和驗證 (bcrypt)
def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.verify(plain, hashed)
```

### logging_v2.py (增強日誌)
```python
# Redis 支援的日誌流
class LoggingManager:
    def setup_logging(
        self,
        log_level: str,
        enable_redis: bool = False,
        enable_json_logs: bool = False
    ):
        """配置日誌系統"""
        # 設定 formatters
        # 配置 handlers
        # 可選 Redis 流
```

## 依賴注入系統

**檔案:** `app/dependencies.py`

```python
async def get_db() -> AsyncSession:
    """提供資料庫會話"""
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """提供當前認證使用者"""
    payload = jwt.decode(token, ...)
    user_id = payload.get("sub")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401)
    return user
```

## 關鍵檔案大小

| 檔案 | 行數 | 說明 |
|------|------|------|
| measurement_service.py | 2000+ | 測量執行邏輯 |
| test_engine.py | 500+ | 測試編排 |
| base.py (measurement) | 400+ | 基類和驗證 |
| implementations.py | 1500+ | 20+ 測量實現 |
| main.py | 100+ | FastAPI 入口 |
| models/* | 800+ | 7 個 ORM 模型 |
| api/* | 1200+ | 所有路由 |

## 下一步

- **瞭解測量系統**: [07-measurement-system.md](07-measurement-system.md)
- **學習 API 端點**: [06-api-endpoints.md](06-api-endpoints.md)
- **瞭解前端**: [04-frontend-structure.md](04-frontend-structure.md)
