# WebPDTool Measurement Codebase 詳細說明

## 目錄
1. [架構概觀](#1-架構概觀)
2. [核心模組說明](#2-核心模組說明)
3. [資料模型層](#3-資料模型層)
4. [測量類型與支援儀器](#4-測量類型與支援儀器)
5. [程式碼關聯圖](#5-程式碼關聯圖)
6. [實際用途總結](#6-實際用途總結)
7. [PDTool4 與 WebPDTool 測量架構對比分析](#7-pdtool4-與-webpdtool-測量架構對比分析)
8. [PDTool4 與 WebPDTool 架構對應總結](#8-pdtool4-與-webpdtool-架構對應總結)
9. [PDTool4 test_point 模組與 WebPDTool 對應分析](#9-pdtool4-test_point-模組與-webpdtool-對應分析)

---

## 1. 架構概觀

Measurement 系統採用多層架構設計，基於 PDTool4 的測量架構實作：

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (measurements.py)               │
│                    RESTful API Endpoints                     │
├─────────────────────────────────────────────────────────────┤
│                   Service Layer (measurement_service.py)     │
│              Measurement Dispatch & Execution Logic          │
├─────────────────────────────────────────────────────────────┤
│           Test Engine (test_engine.py)                       │
│         Test Orchestration & State Management                │
├─────────────────────────────────────────────────────────────┤
│     Measurement Base (base.py) + Implementations (impl.py)   │
│         Abstract Base Classes & Concrete Implementations     │
├─────────────────────────────────────────────────────────────┤
│    Instrument Manager (instrument_manager.py)                │
│           Connection Pool & Resource Management              │
├─────────────────────────────────────────────────────────────┤
│              Data Layer (models: test_session, test_result)  │
│              Database Models & Persistence                   │
└─────────────────────────────────────────────────────────────┘
```

### 檔案結構

```
backend/app/
├── api/
│   └── measurements.py          # API 端點層
├── services/
│   ├── measurement_service.py   # 測量服務層
│   ├── instrument_manager.py    # 儀器管理器
│   └── test_engine.py           # 測試執行引擎
├── measurements/
│   ├── base.py                  # 測量基類
│   ├── implementations.py       # 具體測量實作
│   └── __init__.py
├── models/
│   ├── test_session.py          # 測試會話模型
│   ├── test_result.py           # 測試結果模型
│   └── testplan.py              # 測試計畫模型
└── dependencies.py              # 依賴注入 (身份驗證)
```

---

## 2. 核心模組說明

### 2.1 API 層 - `app/api/measurements.py`

**檔案位置**: `backend/app/api/measurements.py`

#### 主要功能
- 提供 RESTful API 端點供前端呼叫
- 處理單一測量和批次測量執行請求
- 提供測量參數驗證和儀器狀態查詢

#### 關聯性
- 依賴 `measurement_service` 執行實際測量
- 透過 `get_current_active_user` 進行身份驗證
- 使用 `TestSessionModel` 驗證測試會話存在性

#### 主要端點

| HTTP 方法 | 端點 | 功能 | 關聯方法 |
|-----------|------|------|----------|
| POST | `/execute` | 執行單一測量 | `measurement_service.execute_single_measurement()` |
| POST | `/batch-execute` | 執行批次測量 (背景) | `measurement_service.execute_batch_measurements()` |
| GET | `/types` | 取得測量類型列表 | 靜態定義 |
| GET | `/instruments` | 取得儀器狀態 | `measurement_service.get_instrument_status()` |
| POST | `/instruments/{id}/reset` | 重置特定儀器 | `measurement_service.reset_instrument()` |
| GET | `/session/{id}/results` | 取得會話測量結果 | `measurement_service.get_session_results()` |
| POST | `/validate-params` | 驗證測量參數 | `measurement_service.validate_params()` |
| GET | `/instruments/available` | 取得可用儀器列表 | 靜態定義 |
| GET | `/measurement-templates` | 取得測量範本 | 靜態定義 |
| POST | `/execute-with-dependencies` | 執行有相依性的測量 | `execute_measurement()` |

#### 請求/回應模型

**MeasurementRequest** (單一測量請求)
```python
{
    "measurement_type": str,   # PowerSet, PowerRead, CommandTest, etc.
    "test_point_id": str,
    "switch_mode": str,        # DAQ973A, MODEL2303, comport, etc.
    "test_params": Dict[str, Any],
    "run_all_test": bool = False
}
```

**MeasurementResponse** (測量回應)
```python
{
    "test_point_id": str,
    "measurement_type": str,
    "result": str,             # PASS, FAIL, ERROR
    "measured_value": Optional[float],
    "error_message": Optional[str],
    "test_time": datetime,
    "execution_duration_ms": Optional[int]
}
```

**BatchMeasurementRequest** (批次測量請求)
```python
{
    "session_id": int,
    "measurements": List[MeasurementRequest],
    "stop_on_fail": bool = True
}
```

---

### 2.2 測量服務層 - `app/services/measurement_service.py`

**檔案位置**: `backend/app/services/measurement_service.py`

#### 主要功能
- 實作 PDTool4 風格的測量派送機制
- 管理測量執行生命週期
- 處理儀器命令執行 (透過 subprocess 呼叫外部 Python 腳本)

#### 核心類別: `MeasurementService`

```python
class MeasurementService:
    def __init__(self):
        # 測量派送表 (類似 PDTool4 的 switch case)
        self.measurement_dispatch = {
            'PowerSet': self._execute_power_set,
            'PowerRead': self._execute_power_read,
            'CommandTest': self._execute_command_test,
            'SFCtest': self._execute_sfc_test,
            'getSN': self._execute_get_sn,
            'OPjudge': self._execute_op_judge,
            'Other': self._execute_other,
            'Final': self._execute_final
        }

        # 儀器重置對應表
        self.instrument_reset_map = {
            'DAQ973A': 'DAQ973A_test.py',
            'MODEL2303': '2303_test.py',
            # ... 更多對應
        }

        # 活躍測試會話追蹤
        self.active_sessions: Dict[int, Dict] = {}
```

#### 測量派送表 (Measurement Dispatch)

| 測量類型 | 對應方法 | PDTool4 原始檔案 | 功能說明 |
|----------|----------|------------------|----------|
| PowerSet | `_execute_power_set()` | PowerSetMeasurement.py | 電源電壓/電流設定 |
| PowerRead | `_execute_power_read()` | PowerReadMeasurement.py | 電壓/電流讀取 |
| CommandTest | `_execute_command_test()` | CommandTestMeasurement.py | 序列/網路命令測試 |
| SFCtest | `_execute_sfc_test()` | SFC_GONOGOMeasurement.py | SFC 整合測試 |
| getSN | `_execute_get_sn()` | getSNMeasurement.py | 序號取得 (SN/IMEI/MAC) |
| OPjudge | `_execute_op_judge()` | OPjudgeMeasurement.py | 操作者判斷確認 |
| Other | `_execute_other()` | OtherMeasurement.py | 自訂測量 |
| Final | `_execute_final()` | FinalMeasurement.py | 最終清理 |

#### 儀器重置對應表

```python
self.instrument_reset_map = {
    'DAQ973A': 'DAQ973A_test.py',
    'MODEL2303': '2303_test.py',
    'MODEL2306': '2306_test.py',
    'IT6723C': 'IT6723C.py',
    'PSW3072': 'PSW3072.py',
    '2260B': '2260B.py',
    'APS7050': 'APS7050.py',
    '34970A': '34970A.py',
    'KEITHLEY2015': 'Keithley2015.py',
    'DAQ6510': 'DAQ6510.py',
    'MDO34': 'MDO34.py',
    'MT8872A_INF': 'MT8872A_INF.py'
}
```

#### 關鍵方法說明

| 方法 | 說明 | 回傳值 |
|------|------|--------|
| `execute_single_measurement()` | 執行單一測量，包含參數驗證和派送 | `MeasurementResult` |
| `execute_batch_measurements()` | 執行批次測量 (背景)，支援 stop_on_fail | `None` (背景執行) |
| `_execute_power_set()` | 執行電源設定測量 | `MeasurementResult` |
| `_execute_power_read()` | 執行電源讀取測量 | `MeasurementResult` |
| `_execute_command_test()` | 執行命令測試，支援關鍵字提取 | `MeasurementResult` |
| `_execute_sfc_test()` | 執行 SFC 整合測試 | `MeasurementResult` |
| `_execute_instrument_command()` | 透過 subprocess 執行外部儀器腳本 | `str` (命令輸出) |
| `_process_keyword_extraction()` | 從命令回應中提取指定值 | `str` (提取的值) |
| `_cleanup_used_instruments()` | 測試完成後重置儀器 | `None` |
| `validate_params()` | 根據測量類型和 switch_mode 驗證參數 | `Dict` (驗證結果) |
| `get_instrument_status()` | 取得所有儀器狀態 | `List[Dict]` |
| `reset_instrument()` | 重置特定儀器 | `Dict` (狀態) |
| `get_session_results()` | 取得會話測量結果 | `List[Dict]` |
| `_save_measurement_result()` | 儲存測量結果至資料庫 | `None` |

#### 命令執行機制

```python
async def _execute_instrument_command(
    self,
    script_path: str,      # e.g., './src/lowsheen_lib/DAQ973A_test.py'
    test_point_id: str,
    test_params: Dict[str, Any]
) -> str:
    """透過 subprocess 執行儀器命令"""
    result = subprocess.run(
        ['python', script_path, test_point_id, str(test_params)],
        capture_output=True,
        text=True,
        timeout=30
    )
    return result.stdout.strip()
```

#### 關鍵字提取處理

```python
def _process_keyword_extraction(self, response: str, test_params: Dict) -> str:
    """
    從命令回應中提取指定值

    參數:
    - response: 命令執行回應
    - test_params: 包含 keyWord, spiltCount, splitLength

    範例:
    - response: "Version: 1.2.3\nDate: 2024-01-01"
    - keyWord: "Version"
    - spiltCount: 1 (從第1個字元開始，1-based)
    - splitLength: 5 (取5個字元)
    - 回傳: " 1.2."
    """
```

#### 實際用途
- 做為 API 層和底層測量實作之間的中介層
- 實作 PDTool4 的 CSV 驅動測試執行邏輯
- 管理測試會話狀態 (`active_sessions`)
- 處理測量結果儲存至資料庫

---

### 2.3 測量基類 - `app/measurements/base.py`

**檔案位置**: `backend/app/measurements/base.py`

#### `MeasurementResult` - 測量結果資料結構

```python
class MeasurementResult:
    """測量結果資料結構"""

    def __init__(
        self,
        item_no: int,                      # 項目編號
        item_name: str,                    # 項目名稱
        result: str,                       # PASS/FAIL/SKIP/ERROR
        measured_value: Optional[Decimal] = None,  # 測量值
        lower_limit: Optional[Decimal] = None,     # 規格下限
        upper_limit: Optional[Decimal] = None,     # 規格上限
        unit: Optional[str] = None,        # 單位
        error_message: Optional[str] = None,       # 錯誤訊息
        execution_duration_ms: Optional[int] = None  # 執行時間 (毫秒)
    ):
        self.test_time = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
```

#### `BaseMeasurement` - 抽象測量基類

```python
class BaseMeasurement(ABC):
    """抽象測量基類，所有測量實作都應繼承此類"""

    def __init__(self, test_plan_item: Dict, config: Dict):
        """初始化測量"""
        self.item_no = test_plan_item.get("item_no")
        self.item_name = test_plan_item.get("item_name")
        self.lower_limit = test_plan_item.get("lower_limit")
        self.upper_limit = test_plan_item.get("upper_limit")
        self.unit = test_plan_item.get("unit")
        self.test_command = test_plan_item.get("test_command")
        self.test_params = test_plan_item.get("test_params", {})

    @abstractmethod
    async def execute(self) -> MeasurementResult:
        """子類必須實作的測量執行方法"""
        pass

    def validate_result(self, measured_value: Decimal) -> str:
        """驗證測量值是否符合規格"""
        if self.lower_limit and measured_value < self.lower_limit:
            return "FAIL"
        if self.upper_limit and measured_value > self.upper_limit:
            return "FAIL"
        return "PASS"

    def create_result(self, result: str, ...) -> MeasurementResult:
        """建立測量結果物件"""
        pass

    async def setup(self):
        """測量前設定 (可選)"""
        pass

    async def teardown(self):
        """測量後清理 (可選)"""
        pass
```

#### 關聯性
- 被 `implementations.py` 中的具體測量類別繼承
- 被 `test_engine.py` 用於執行測量

---

### 2.4 測量實作類別 - `app/measurements/implementations.py`

**檔案位置**: `backend/app/measurements/implementations.py`

#### 實作類別列表

| 類別 | 繼承 | 對應 PDTool4 | 用途 |
|------|------|-------------|------|
| `DummyMeasurement` | `BaseMeasurement` | - | 測試用，回傳隨機值 (80% PASS率) |
| `CommandTestMeasurement` | `BaseMeasurement` | CommandTestMeasurement.py | 序列埠/網路命令測試 |
| `PowerReadMeasurement` | `BaseMeasurement` | PowerReadMeasurement.py | 電壓/電流讀取 |
| `PowerSetMeasurement` | `BaseMeasurement` | PowerSetMeasurement.py | 電源電壓/電流設定 |
| `SFCMeasurement` | `BaseMeasurement` | SFC_GONOGOMeasurement.py | SFC 系統整合測試 |
| `GetSNMeasurement` | `BaseMeasurement` | getSNMeasurement.py | 序號取得 (SN/IMEI/MAC) |
| `OPJudgeMeasurement` | `BaseMeasurement` | OPjudgeMeasurement.py | 操作者判斷確認 |

#### 測量註冊表 (MEASUREMENT_REGISTRY)

```python
MEASUREMENT_REGISTRY = {
    "DUMMY": DummyMeasurement,
    "COMMAND_TEST": CommandTestMeasurement,
    "POWER_READ": PowerReadMeasurement,
    "POWER_SET": PowerSetMeasurement,
    "SFC_TEST": SFCMeasurement,
    "GET_SN": GetSNMeasurement,
    "OP_JUDGE": OPJudgeMeasurement,
    "OTHER": DummyMeasurement,
    "FINAL": DummyMeasurement,
}
```

#### 工廠函式

```python
def get_measurement_class(test_command: str) -> Optional[type]:
    """
    將 PDTool4 風格的命令名稱對應到註冊表中的類別

    對應關係:
    - "SFCtest"      -> "SFC_TEST"     -> SFCMeasurement
    - "getSN"        -> "GET_SN"       -> GetSNMeasurement
    - "OPjudge"      -> "OP_JUDGE"     -> OPJudgeMeasurement
    - "Other"        -> "OTHER"        -> DummyMeasurement
    - "Final"        -> "FINAL"        -> DummyMeasurement
    - "CommandTest"  -> "COMMAND_TEST" -> CommandTestMeasurement
    - "PowerRead"    -> "POWER_READ"   -> PowerReadMeasurement
    - "PowerSet"     -> "POWER_SET"    -> PowerSetMeasurement
    """
```

---

### 2.5 儀器管理器 - `app/services/instrument_manager.py`

**檔案位置**: `backend/app/services/instrument_manager.py`

#### `InstrumentConnection` - 儀器連線基類

```python
class InstrumentConnection:
    """儀器連線基類"""

    def __init__(self, instrument_id: str, config: Dict[str, Any]):
        self.instrument_id = instrument_id
        self.config = config
        self.is_connected = False

    async def connect(self):
        """連線儀器"""
        pass

    async def disconnect(self):
        """斷開連線"""
        pass

    async def send_command(self, command: str) -> str:
        """發送命令到儀器並取得回應"""
        raise NotImplementedError("Subclass must implement send_command")
```

#### `InstrumentManager` - 單例儀器管理器

```python
class InstrumentManager:
    """
    單例儀器管理器

    特點:
    - 使用單例模式確保只有一個管理器實例
    - 使用 asyncio.Lock 保證執行緒安全
    - 實作連線池機制以重用儀器連線
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        """實作單例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        self.instruments: Dict[str, InstrumentConnection] = {}
        self.usage_count: Dict[str, int] = defaultdict(int)

    async def get_instrument(
        self,
        instrument_id: str,
        instrument_type: str,
        config: Dict[str, Any]
    ) -> InstrumentConnection:
        """取得或建立儀器連線 (連線池機制)"""
        async with self._lock:
            if instrument_id not in self.instruments:
                instrument = self._create_instrument(instrument_id, instrument_type, config)
                await instrument.connect()
                self.instruments[instrument_id] = instrument

            self.usage_count[instrument_id] += 1
            return self.instruments[instrument_id]

    async def release_instrument(self, instrument_id: str):
        """釋放儀器 (減少使用計數，不實際斷線)"""
        async with self._lock:
            if instrument_id in self.usage_count:
                self.usage_count[instrument_id] -= 1

    async def reset_instrument(self, instrument_id: str):
        """重置特定儀器 (斷線後重新連線)"""
        pass

    def get_status(self) -> Dict[str, Any]:
        """取得所有儀器狀態"""
        return {
            "instruments": {
                inst_id: {
                    "connected": inst.is_connected,
                    "usage_count": self.usage_count.get(inst_id, 0),
                    "type": inst.__class__.__name__
                }
                for inst_id, inst in self.instruments.items()
            },
            "total_instruments": len(self.instruments)
        }
```

#### 設計模式
- **單例模式**: 確保全域只有一個管理器實例
- **連線池**: 重用儀器連線，減少連線開銷
- **執行緒安全**: 使用 asyncio.Lock 保護共享資源

---

### 2.6 測試執行引擎 - `app/services/test_engine.py`

**檔案位置**: `backend/app/services/test_engine.py`

#### `TestExecutionState` - 測試執行狀態

```python
class TestExecutionState:
    """追蹤測試執行狀態"""

    def __init__(self, session_id: int):
        self.session_id = session_id
        self.status = "IDLE"           # IDLE, RUNNING, PAUSED, COMPLETED, ABORTED
        self.current_item_index = 0
        self.results: List[MeasurementResult] = []
        self.start_time: Optional[datetime] = None
        self.error: Optional[str] = None
        self.should_stop = False
```

#### `TestEngine` - 測試執行引擎

```python
class TestEngine:
    """
    測試執行引擎

    功能:
    - 管理多個測試會話的並行執行
    - 協調測試流程和結果收集
    - 處理測試中止和錯誤恢復
    """

    def __init__(self):
        self.active_tests: Dict[int, TestExecutionState] = {}
        self._lock = asyncio.Lock()

    async def start_test_session(
        self,
        session_id: int,
        serial_number: str,
        station_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        啟動測試會話 (在背景執行)

        流程:
        1. 驗證測試會話不存在
        2. 建立 TestExecutionState 並設為 RUNNING
        3. 在背景執行 _execute_test_session()
        """

    async def _execute_test_session(self, session_id, station_id, db):
        """
        執行測試會話主流程 (背景)

        流程:
        1. 載入測試計畫項目
        2. 依序執行每個測量
        3. 檢查 should_stop 標誌
        4. 儲存測量結果至資料庫
        5. 完成後更新會話狀態
        """

    async def _execute_measurement(...) -> MeasurementResult:
        """
        執行單一測量

        流程:
        1. 取得測量類別 (透過 get_measurement_class)
        2. 建立 measurement 實例
        3. 呼叫 setup(), execute(), teardown()
        4. 計算執行時間
        """

    async def stop_test_session(self, session_id: int):
        """設定 should_stop=True 以中止測試"""

    def get_test_status(self, session_id: int) -> Optional[Dict]:
        """取得測試會話狀態"""
```

#### 執行流程圖

```
start_test_session()
        │
        ▼
建立 TestExecutionState (status=RUNNING)
        │
        ▼
在背景執行 _execute_test_session()
        │
        ▼
┌───────────────────────────────┐
│  載入測試計畫項目              │
└─────────────┬─────────────────┘
              ▼
┌───────────────────────────────┐
│  依序執行每個測量              │
│  - 檢查 should_stop           │
│  - 呼叫 _execute_measurement() │
└─────────────┬─────────────────┘
              ▼
┌───────────────────────────────┐
│  儲存測量結果至資料庫          │
└─────────────┬─────────────────┘
              ▼
┌───────────────────────────────┐
│  更新會話狀態 (COMPLETED/ABORT)│
└───────────────────────────────┘
```

---

## 3. 資料模型層

### 3.1 TestSession (`app/models/test_session.py`)

```python
class TestSession(Base):
    """測試會話模型"""
    __tablename__ = "test_sessions"

    # 主鍵
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 測試資訊
    serial_number = Column(String(100), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 時間戳記
    start_time = Column(TIMESTAMP, server_default=func.now())
    end_time = Column(TIMESTAMP, nullable=True)

    # 測試結果統計
    final_result = Column(Enum(TestResult), nullable=True)  # PASS/FAIL/ABORT
    total_items = Column(Integer, nullable=True)
    pass_items = Column(Integer, nullable=True)
    fail_items = Column(Integer, nullable=True)
    test_duration_seconds = Column(Integer, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())

    # 關聯
    station = relationship("Station", back_populates="test_sessions")
    user = relationship("User")
    test_results = relationship("TestResult", back_populates="session", cascade="all, delete-orphan")
    sfc_logs = relationship("SFCLog", back_populates="session", cascade="all, delete-orphan")
```

### 3.2 TestResult (`app/models/test_result.py`)

```python
class TestResult(Base):
    """測試結果模型"""
    __tablename__ = "test_results"

    # 主鍵
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 外鍵
    session_id = Column(Integer, ForeignKey("test_sessions.id", ondelete="CASCADE"), nullable=False)
    test_plan_id = Column(Integer, ForeignKey("test_plans.id"), nullable=False)

    # 測試項目資訊
    item_no = Column(Integer, nullable=False)
    item_name = Column(String(100), nullable=False)

    # 測量值與規格
    measured_value = Column(DECIMAL(15, 6), nullable=True)
    lower_limit = Column(DECIMAL(15, 6), nullable=True)
    upper_limit = Column(DECIMAL(15, 6), nullable=True)
    unit = Column(String(20), nullable=True)

    # 測試結果
    result = Column(Enum(ItemResult), nullable=False, index=True)  # PASS/FAIL/SKIP/ERROR
    error_message = Column(Text, nullable=True)

    # 時間戳記
    test_time = Column(TIMESTAMP, server_default=func.now(), index=True)
    execution_duration_ms = Column(Integer, nullable=True)

    # 關聯
    session = relationship("TestSession", back_populates="test_results")
    test_plan = relationship("TestPlan")
```

### 3.3 ItemResult 列舉

```python
class ItemResult(str, enum.Enum):
    """測試項目結果列舉"""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"
```

---

## 4. 測量類型與支援儀器

### 4.1 測量類型對照表

| 測量類型 | 說明 | 支援 Switch Mode | 必要參數範例 |
|----------|------|------------------|-------------|
| **PowerSet** | 電源電壓/電流設定 | DAQ973A, MODEL2303, MODEL2306, IT6723C, PSW3072, 2260B, APS7050, 34970A, KEITHLEY2015 | Instrument, Channel, Item, Volt, Curr |
| **PowerRead** | 電壓/電流讀取 | DAQ973A, 34970A, 2015, 6510, APS7050, MDO34, MT8870A_INF, KEITHLEY2015 | Instrument, Channel, Item, Type |
| **CommandTest** | 序列/網路命令測試 | comport, tcpip, console, android_adb, PEAK | Port/Baud/Host, Command, keyWord, EqLimit |
| **SFCtest** | SFC 整合測試 | webStep1_2, URLStep1_2, skip | Mode |
| **getSN** | 序號取得 | SN, IMEI, MAC | Type, serial_number |
| **OPjudge** | 操作者判斷 | YorN, confirm | Type, operator_judgment |

### 4.2 PowerSet 參數範例

**DAQ973A**
```python
{
    "Instrument": "daq973a_1",
    "Channel": "101",
    "Item": "volt",      # volt 或 curr
    "Volt": "5.0",
    "Curr": "1.0"
}
```

**MODEL2303**
```python
{
    "Instrument": "model2303_1",
    "SetVolt": "5.0",
    "SetCurr": "2.0",
    "OVP": "6.0",        # optional
    "OCP": "2.5"         # optional
}
```

### 4.3 PowerRead 參數範例

**DAQ973A**
```python
{
    "Instrument": "daq973a_1",
    "Channel": "101",
    "Item": "volt",      # volt 或 curr
    "Type": "DC",        # DC 或 AC
    "Range": "10",       # optional
    "NPLC": "1"          # optional
}
```

**34970A**
```python
{
    "Instrument": "34970a_1",
    "Channel": "101",
    "Item": "volt"
}
```

### 4.4 CommandTest 參數範例

**comport**
```python
{
    "Port": "COM4",
    "Baud": "9600",
    "Command": "AT+VERSION",
    "keyWord": "VERSION",     # optional (關鍵字提取)
    "spiltCount": "1",        # optional (從第1字元開始)
    "splitLength": "10"       # optional (取10字元)
}
```

**tcpip**
```python
{
    "Host": "192.168.1.100",
    "Port": "5025",
    "Command": "*IDN?",
    "Timeout": "5"            # optional
}
```

**EqLimit 模式**
```python
{
    "Port": "COM4",
    "Baud": "9600",
    "Command": "TEST_STATUS",
    "EqLimit": "PASS"         # 檢查回應中是否包含 "PASS"
}
```

### 4.5 支援儀器列表

#### 電源供應器
| 儀器 ID | 描述 | 對應腳本 |
|---------|------|---------|
| DAQ973A | Keysight DAQ973A | DAQ973A_test.py |
| MODEL2303 | Keysight Model 2303 | 2303_test.py |
| MODEL2306 | Keysight Model 2306 | 2306_test.py |
| IT6723C | ITECH IT6723C | IT6723C.py |
| PSW3072 | Rigol PSW3072 | PSW3072.py |
| 2260B | Keysight 2260B | 2260B.py |
| APS7050 | Agilent APS7050 | APS7050.py |

#### 多用電錶
| 儀器 ID | 描述 | 對應腳本 |
|---------|------|---------|
| 34970A | Keysight 34970A | 34970A.py |
| DAQ6510 | Keysight DAQ6510 | DAQ6510.py |
| KEITHLEY2015 | Keithley 2015 Multimeter | Keithley2015.py |

#### 通訊介面
| 介面 ID | 描述 | 對應腳本 |
|---------|------|---------|
| comport | Serial Port Communication | ComPortCommand.py |
| tcpip | TCP/IP Communication | TCPIPCommand.py |
| console | Console Command Execution | ConSoleCommand.py |
| android_adb | Android ADB Communication | AndroidAdbCommand.py |
| PEAK | PEAK CAN Interface | PEAK_API/PEAK.py |

#### RF 分析儀
| 儀器 ID | 描述 | 對應腳本 |
|---------|------|---------|
| MDO34 | Tektronix MDO34 | MDO34.py |
| MT8870A_INF | Anritsu MT8870A | RF_tool/MT8872A_INF.py |

---

## 5. 程式碼關聯圖

### 5.1 整體架構關聯

```
Frontend Request (HTTP)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  API Layer: api/measurements.py                             │
│  - authenticate user (dependencies.py)                      │
│  - validate request                                         │
│  - parse request to MeasurementRequest                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Service Layer: services/measurement_service.py             │
│  - measurement_service (singleton)                          │
│  - dispatch by measurement_type                             │
│  - execute via subprocess or direct implementation          │
│  - manage active_sessions                                   │
└─────────┬───────────────────────────────────┬────────────────┘
          │                                   │
          ▼                                   ▼
┌──────────────────────┐         ┌──────────────────────────┐
│ Test Engine          │         │ Instrument Manager       │
│ (test_engine.py)     │         │ (instrument_manager.py)  │
│ - orchestrate tests  │         │ - connection pool        │
│ - track state        │         │ - manage resources       │
└──────────┬───────────┘         └──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│  Measurements: measurements/                                │
│  - base.py (BaseMeasurement, MeasurementResult)            │
│  - implementations.py (concrete measurement classes)        │
│  - execute() method implementation                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  External Scripts: ./src/lowsheen_lib/                      │
│  - DAQ973A_test.py                                         │
│  - 2303_test.py                                             │
│  - ComPortCommand.py                                        │
│  - ...                                                     │
│  (executed via subprocess)                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Data Layer: models/                                       │
│  - TestSession (test_sessions table)                       │
│  - TestResult (test_results table)                         │
│  - SQLAlchemy ORM                                          │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 模組間依賴關係

```
┌─────────────────────────────────────────────────────────────┐
│                        api/measurements.py                  │
│  Depends on:                                                │
│  - app.dependencies (get_current_active_user)               │
│  - app.services.measurement_service (measurement_service)   │
│  - app.models.test_session (TestSession)                    │
│  - app.core.database (get_db)                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    services/measurement_service.py          │
│  Depends on:                                                │
│  - app.measurements.base (BaseMeasurement, MeasurementResult)│
│  - app.measurements.implementations (get_measurement_class) │
│  - app.models.test_session (TestSession)                    │
│  - app.models.test_result (TestResult)                      │
│  - app.services.instrument_manager (instrument_manager)     │
│  - subprocess (for external script execution)               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       measurements/base.py                  │
│  Depends on:                                                │
│  - abc (ABC, abstractmethod)                               │
│  - decimal (Decimal)                                       │
│  - datetime (datetime)                                     │
│  - logging                                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  measurements/implementations.py            │
│  Depends on:                                                │
│  - app.measurements.base (BaseMeasurement, MeasurementResult)│
│  - asyncio, random (for simulation)                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   services/instrument_manager.py            │
│  Depends on:                                                │
│  - asyncio, logging, collections                           │
│  - (no app dependencies)                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        services/test_engine.py              │
│  Depends on:                                                │
│  - app.models.test_session (TestSession)                    │
│  - app.models.test_result (TestResult)                      │
│  - app.models.testplan (TestPlan)                           │
│  - app.models.station (Station)                            │
│  - app.measurements.base (BaseMeasurement, MeasurementResult)│
│  - app.measurements.implementations (get_measurement_class) │
│  - app.services.instrument_manager (instrument_manager)     │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 呼叫流程圖

#### 單一測量執行流程

```
Client POST /execute
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  measurements.py: execute_measurement()                     │
│  1. Get current_user from dependencies                      │
│  2. Call measurement_service.execute_single_measurement()  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  measurement_service.py: execute_single_measurement()       │
│  1. validate_params()                                      │
│  2. Get executor from measurement_dispatch                 │
│  3. Call executor (e.g., _execute_power_set)              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  measurement_service.py: _execute_power_set()              │
│  1. Validate required parameters                           │
│  2. Map switch_mode to script_file                         │
│  3. Call _execute_instrument_command()                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  measurement_service.py: _execute_instrument_command()     │
│  subprocess.run(['python', script_path, ...])              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  External Script: ./src/lowsheen_lib/DAQ973A_test.py       │
│  (Actual instrument communication)                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Parse output and create MeasurementResult                  │
│  Return to API layer                                       │
└─────────────────────────────────────────────────────────────┘
```

#### 批次測量執行流程

```
Client POST /batch-execute
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  measurements.py: execute_batch_measurements()             │
│  1. Validate session exists                                │
│  2. Add background task to execution queue                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  measurement_service.py: execute_batch_measurements()      │
│  (Background execution)                                     │
│  1. Initialize active_sessions[session_id]                 │
│  2. Loop through measurements                              │
│  3. For each measurement:                                  │
│     - Check should_stop                                   │
│     - Execute measurement                                 │
│     - Store result in session_data                        │
│     - Save to database                                    │
│     - Check stop_on_fail                                  │
│  4. Cleanup instruments                                   │
│  5. Update session status                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. 實際用途總結

### 6.1 單一測量執行

**用途**: 執行單一測量並立即取得結果

**流程**:
```
API → measurement_service.execute_single_measurement()
    → 派送至對應執行方法
    → 執行外部腳本 或 內部實作
    → 回傳 MeasurementResult
```

**API 端點**: `POST /measurements/execute`

**請求範例**:
```json
{
    "measurement_type": "PowerRead",
    "test_point_id": "TP001",
    "switch_mode": "DAQ973A",
    "test_params": {
        "Instrument": "daq973a_1",
        "Channel": "101",
        "Item": "volt",
        "Type": "DC"
    }
}
```

---

### 6.2 批次測量執行

**用途**: 執行多個測量 (測試會話)，在背景執行，支援失敗停止

**流程**:
```
API → measurement_service.execute_batch_measurements() (背景)
    → 循序執行測量
    → 儲存結果至資料庫
    → 清理儀器
```

**API 端點**: `POST /measurements/batch-execute`

**請求範例**:
```json
{
    "session_id": 123,
    "measurements": [
        {
            "measurement_type": "PowerSet",
            "test_point_id": "TP001",
            "switch_mode": "DAQ973A",
            "test_params": {...}
        },
        {
            "measurement_type": "PowerRead",
            "test_point_id": "TP002",
            "switch_mode": "DAQ973A",
            "test_params": {...}
        }
    ],
    "stop_on_fail": true
}
```

---

### 6.3 測試會話執行

**用途**: 完整的測試會話管理，包含測試計畫載入、測試執行、結果收集

**流程**:
```
test_engine.start_test_session()
    → 載入測試計畫
    → 在背景執行 _execute_test_session()
    → 依序執行測量
    → 更新會話狀態
```

**API 端點**: (需在 TestSession API 中實作)

---

### 6.4 儀器管理

**用途**: 管理儀器連線，實作連線池機制

**流程**:
```
instrument_manager.get_instrument()
    → 建立或重用連線
    → 增加使用計數
    → 回傳 InstrumentConnection

instrument_manager.release_instrument()
    → 減少使用計數
    → (保留連線供後續使用)

instrument_manager.reset_instrument()
    → 斷線並重連
```

**API 端點**:
- `GET /measurements/instruments` - 取得儀器狀態
- `POST /measurements/instruments/{id}/reset` - 重置儀器

---

### 6.5 參數驗證

**用途**: 驗證測量參數是否符合規範

**流程**:
```
API → measurement_service.validate_params()
    → 根據測量類型和 switch_mode 檢查
    → 回傳缺失參數列表
```

**API 端點**: `POST /measurements/validate-params`

**請求範例**:
```json
{
    "measurement_type": "PowerRead",
    "switch_mode": "DAQ973A",
    "test_params": {
        "Instrument": "daq973a_1",
        "Channel": "101"
    }
}
```

**回應範例**:
```json
{
    "valid": false,
    "missing_params": ["Item", "Type"],
    "invalid_params": [],
    "suggestions": []
}
```

---

### 6.6 測量結果查詢

**用途**: 查詢測試會話的所有測量結果

**流程**:
```
API → measurement_service.get_session_results()
    → 從 active_sessions 或資料庫查詢
    → 回傳結果列表
```

**API 端點**: `GET /measurements/session/{session_id}/results`

---

## 附錄: 參考資料

### 相關檔案
- [PDTool4_Measurement_Module_Analysis.md](./PDTool4_Measurement_Module_Analysis.md) - PDTool4 測量模組分析
- [architecture_workflow.md](./architecture_workflow.md) - 系統架構說明
- [configuration_setup.md](./configuration_setup.md) - 配置設定說明

---

## 7. PDTool4 與 WebPDTool 測量架構對比分析

### 7.1 架構對應關係

| PDTool4 (`polish/measurement/`) | WebPDTool (`backend/app/`) | 說明 |
|--------------------------------|----------------------------|------|
| `measurement.py` (核心基類) | `measurements/base.py` | 測量抽象基類 |
| - | `measurements/implementations.py` | 具體測量實作類別 |
| `Measurement` 類別 | `BaseMeasurement` 類別 | 測量基類 |
| `MeasurementList` 類別 | `services/test_engine.py` | 測試執行引擎 |
| `MeasurementList.run_measurements()` | `TestEngine._execute_test_session()` | 執行測試流程 |
| `DepsResolver` | `services/measurement_service.py` | 相依性解析與派送 |
| `Job` 類別 | - | 任務執行 (WebPDTool 未實作) |

### 7.2 核心類別對比

#### 7.2.1 `Measurement` (PDTool4) vs `BaseMeasurement` (WebPDTool)

| 特性 | PDTool4 `Measurement` | WebPDTool `BaseMeasurement` |
|------|----------------------|------------------------------|
| 繼承 | `DepsResolver` | `ABC` |
| 測試點管理 | `test_point_uids`, `test_points` (Canister) | `item_no`, `item_name` (字典) |
| 初始化參數 | `meas_assets` (包含 test_point_map) | `test_plan_item`, `config` |
| 執行方法 | `run()` → `setup()`, `measure()`, `teardown()` | `execute()` → `setup()`, `execute()`, `teardown()` |
| 測試點驗證 | `check_test_points()` (自動檢查) | `validate_result()` (手動呼叫) |
| 回傳值 | None (結果存入 test_point) | `MeasurementResult` 物件 |
| 時間記錄 | 自動記錄到 `result.txt` | `execution_duration_ms` 欄位 |

#### PDTool4 Measurement 核心結構
```python
# PDTool4/polish/measurement/measurement.py
class Measurement(DepsResolver):
    test_point_uids = tuple()  # 測試點 ID 列表

    def __init__(self, meas_assets):
        self.test_points = Canister()
        # 從 test_point_map 載入測試點

    def run(self):
        tick = time.time()
        try:
            self.setup()
            self.measure()
            self.check_test_points()  # 自動驗證所有測試點已被饋入
        finally:
            self.teardown()
            # 記錄執行時間到 result.txt

    def setup(self):
        pass

    def measure(self):
        raise MeaurementImplementationError()

    def teardown(self):
        pass
```

#### WebPDTool BaseMeasurement 核心結構
```python
# backend/app/measurements/base.py
class BaseMeasurement(ABC):
    def __init__(self, test_plan_item: Dict, config: Dict):
        self.item_no = test_plan_item.get("item_no")
        self.item_name = test_plan_item.get("item_name")
        self.lower_limit = test_plan_item.get("lower_limit")
        self.upper_limit = test_plan_item.get("upper_limit")
        # ...

    @abstractmethod
    async def execute(self) -> MeasurementResult:
        """子類必須實作"""
        pass

    def validate_result(self, measured_value: Decimal) -> str:
        """驗證結果是否符合規格"""
        if self.lower_limit and measured_value < self.lower_limit:
            return "FAIL"
        # ...
        return "PASS"

    def create_result(...) -> MeasurementResult:
        """建立測量結果物件"""
```

### 7.3 執行流程對比

#### PDTool4 測量執行流程
```
MeasurementList.run_measurements()
        │
        ▼
get_ordered_measurments()  # 解析相依性並排序
        │
        ▼
for meas in ordered_measurements:
    meas.run()
        │
        ▼
    ┌──────────────────────────┐
    │  setup()                │
    ├──────────────────────────┤
    │  measure()              │  ← 實際測量邏輯
    │  (子類實作)             │     饋入資料到 test_points
    ├──────────────────────────┤
    │  check_test_points()    │  ← 自動檢查所有測試點
    │  (驗證完成度)           │
    ├──────────────────────────┤
    │  teardown()             │
    └──────────────────────────┘
        │
        ▼
    寫入 result.txt
```

#### WebPDTool 測量執行流程
```
TestEngine._execute_test_session()
        │
        ▼
載入測試計畫項目
        │
        ▼
for test_plan_item in items:
    measurement_class = get_measurement_class(test_command)
    measurement = measurement_class(test_plan_item, config)
        │
        ▼
    ┌──────────────────────────┐
    │  await setup()          │
    ├──────────────────────────┤
    │  await execute()        │  ← 實際測量邏輯
    │  (子類實作)             │     回傳 MeasurementResult
    ├──────────────────────────┤
    │  validate_result()      │  ← 手動驗證結果
    │  (可選)                 │
    ├──────────────────────────┤
    │  await teardown()       │
    └──────────────────────────┘
        │
        ▼
    儲存到資料庫 (TestResult)
```

### 7.4 測試點管理機制對比

| 特性 | PDTool4 | WebPDTool |
|------|---------|-----------|
| 測試點容器 | `Canister` (自定義容器) | 字典 (`test_plan_item`) |
| 測試點 ID | `test_point_uids` (tuple) | `item_no`, `item_name` |
| 資料饋入 | 直接寫入 `test_points[uid]` | 回傳 `MeasurementResult` |
| 完成度檢查 | 自動 `check_test_points()` | 無自動檢查 |
| 規格上下限 | 在 `TestPoint` 中定義 | 在 `test_plan_item` 中定義 |

#### PDTool4 測試點饋入範例
```python
# PDTool4 測量實作
class VoltageMeasurement(Measurement):
    test_point_uids = (('voltage_test', 'tp_001'),)

    def measure(self):
        voltage = self.instrument.read_voltage()
        # 饋入資料到測試點
        self.test_points['voltage_test'].feed(voltage)
        # check_test_points() 會自動檢查是否所有測試點都被饋入
```

#### WebPDTool 測量實作範例
```python
# WebPDTool 測量實作
class PowerReadMeasurement(BaseMeasurement):
    async def execute(self) -> MeasurementResult:
        voltage = self.instrument.read_voltage()
        # 驗證並回傳結果
        result_status = self.validate_result(voltage)
        return self.create_result(
            result=result_status,
            measured_value=voltage
        )
```

### 7.5 相依性管理對比

| 特性 | PDTool4 | WebPDTool |
|------|---------|-----------|
| 相依性解析 | `DepsResolver` 基類 | `measurement_service.py` 派送表 |
| 相依性定義 | `define_deps()` classmethod | `measurement_dispatch` 字典 |
| 排序機制 | `get_ordered_measurings()` | 無 (依測試計畫順序) |
| 去重機制 | `sort_measurements()` 自動去重 | 無 |

#### PDTool4 相依性定義
```python
# PDTool4
class TestMeasurement(Measurement):
    @classmethod
    def define_deps(cls):
        cls.deps = (PowerSetupMeasurement,)  # 相依於 PowerSetup

# 執行時自動解析並排序
ordered = get_ordered_measurings([TestMeasurement])
# 結果: [PowerSetupMeasurement, TestMeasurement]
```

#### WebPDTool 派送機制
```python
# backend/app/services/measurement_service.py
class MeasurementService:
    def __init__(self):
        self.measurement_dispatch = {
            'PowerSet': self._execute_power_set,
            'PowerRead': self._execute_power_read,
            'CommandTest': self._execute_command_test,
            # ...
        }
```

### 7.6 主要差異總結

#### 架構差異
1. **測試點模型**:
   - PDTool4: 使用 `Canister` 容器和 `TestPoint` 物件
   - WebPDTool: 使用字典和 `MeasurementResult` 物件

2. **執行模式**:
   - PDTool4: 同步執行 (`run()`)
   - WebPDTool: 非同步執行 (`async execute()`)

3. **結果儲存**:
   - PDTool4: 寫入 `result.txt` 檔案
   - WebPDTool: 儲存到資料庫 (`test_results` 表)

4. **相依性管理**:
   - PDTool4: 類別層級相依性定義
   - WebPDTool: 服務層派送表

#### 設計理念差異
| 面向 | PDTool4 | WebPDTool |
|------|---------|-----------|
| 目標 | 桌面應用/本地測試 | Web API 服務 |
| 資料儲存 | 檔案系統 | 資料庫 (MySQL) |
| 並行模型 | 同步/多執行緒 | 非同步/asyncio |
| 擴展性 | 單機 | 分散式/多工站 |
| 用戶介面 | 桌面 GUI | Web Frontend + API |

### 7.7 程式碼對應映射

```python
# PDTool4 polish/measurement/measurement.py
┌─────────────────────────────────────────────────────────────────┐
│ class Measurement(DepsResolver)                                 │
│   ├── test_point_uids (tuple)                                  │  → item_no, item_name
│   ├── test_points (Canister)                                   │  → MeasurementResult
│   ├── __init__(meas_assets)                                    │  → __init__(test_plan_item, config)
│   ├── run()                                                    │  → execute()
│   ├── setup()                                                  │  → setup()
│   ├── measure()                                                │  → execute() 主體
│   ├── teardown()                                               │  → teardown()
│   └── check_test_points()                                      │  → validate_result()
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ class MeasurementList                                           │
│   ├── _measurements (list)                                     │  → TestEngine.active_tests
│   ├── add(measurements)                                        │  → start_test_session()
│   └── run_measurements()                                       │  → _execute_test_session()
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ class Job(Measurement)                                          │
│   ├── run()                                                    │  → (未對應)
│   └── job()                                                    │  → (未對應)
└─────────────────────────────────────────────────────────────────┘
```

```python
# WebPDTool backend/app/measurements/
┌─────────────────────────────────────────────────────────────────┐
│ class BaseMeasurement(ABC)                                     │
│   ├── item_no, item_name                                       │  ← test_point_uids
│   ├── lower_limit, upper_limit                                 │  ← TestPoint limits
│   ├── __init__(test_plan_item, config)                         │  ← __init__(meas_assets)
│   ├── execute() → MeasurementResult                            │  ← run() → check_test_points()
│   ├── setup()                                                  │  ← setup()
│   ├── teardown()                                               │  ← teardown()
│   ├── validate_result(measured_value)                          │  ← TestPoint validation
│   └── create_result(...)                                       │  ← test_points.feed()
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ class TestEngine                                                │
│   ├── active_tests (Dict)                                      │  ← MeasurementList._measurements
│   ├── start_test_session()                                     │  ← run_measurements()
│   ├── _execute_test_session()                                  │  ← run_measurements() 主體
│   └── _execute_measurement()                                   │  ← meas.run()
└─────────────────────────────────────────────────────────────────┘
```

### 7.8 實作建議

若要將 PDTool4 的測量邏輯遷移到 WebPDTool:

1. **測試點轉換**:
   ```python
   # PDTool4
   self.test_points['voltage_test'].feed(voltage)

   # WebPDTool
   return self.create_result(
       result="PASS",
       measured_value=voltage
   )
   ```

2. **測量類別註冊**:
   ```python
   # 將 PDTool4 的 Measurement 子類轉換為
   # BaseMeasurement 子類並註冊到 MEASUREMENT_REGISTRY
   ```

3. **相依性處理**:
   ```python
   # PDTool4 的 define_deps() 轉換為
   # 測試計畫中的執行順序定義
   ```

### 7.9 檔案位置對應

| PDTool4 | WebPDTool | 說明 |
|---------|-----------|------|
| `polish/measurement/measurement.py` | `app/measurements/base.py` | 測量基類 |
| - | `app/measurements/implementations.py` | 測量實作 |
| `polish/measurement/measurement.py` (MeasurementList) | `app/services/test_engine.py` | 測試執行 |
| - | `app/services/measurement_service.py` | 測量派送 |
| - | `app/services/instrument_manager.py` | 儀器管理 |

---

## 8. PDTool4 與 WebPDTool 架構對應總結 {#8-pdtool4-與-webpdtool-架構對應總結}

**PDTool4 的 `polish/measurement/` 模組主要對應 WebPDTool 的 `app/measurements/` 目錄**:

1. **`measurement.py` (PDTool4)** → **`base.py` + `implementations.py` (WebPDTool)**
   - `Measurement` 類別 → `BaseMeasurement` 類別
   - 測試點管理機制 → `MeasurementResult` 資料結構

2. **`MeasurementList` 類別 (PDTool4)** → **`test_engine.py` (WebPDTool)**
   - 測試執行協調
   - 測試狀態管理

3. **`DepsResolver` (PDTool4)** → **`measurement_service.py` (WebPDTool)**
   - 測量派送機制
   - 參數驗證

WebPDTool 在此基礎上增加了:
- RESTful API 層 (`api/measurements.py`)
- 資料庫持久化 (SQLAlchemy ORM)
- 非同步執行支援
- Web 介面整合

---

## 9. PDTool4 test_point 模組與 WebPDTool 對應分析

### 9.1 模組概觀

PDTool4 的 `polish/test_point/` 模組主要負責**測試點 (TestPoint) 的定義、管理和規格驗證**。這是 PDTool4 測試架構中的核心資料結構，用於定義每個測試項目的規格限制條件。

**PDTool4 test_point 檔案結構:**
```
PDTool4/polish/test_point/
├── __init__.py
├── test_point.py              # TestPoint 類別定義 (核心)
├── test_point_map.py          # TestPointMap 管理器
└── test_point_runAllTest.py   # 支援 runAllTest 功能的版本
```

**WebPDTool 對應位置:**
```
backend/app/
├── models/
│   └── testplan.py            # TestPlan ORM 模型 (相當於 TestPoint)
├── schemas/
│   └── testplan.py            # TestPlanCreate/Update/Response schemas
└── measurements/
    └── base.py                # MeasurementResult 類別
```

### 9.2 核心類別對應關係

#### 9.2.1 TestPoint (PDTool4) vs TestPlan (WebPDTool)

| 特性 | PDTool4 `TestPoint` | WebPDTool `TestPlan` | 說明 |
|------|---------------------|---------------------|------|
| **檔案位置** | `polish/test_point/test_point.py` | `app/models/testplan.py` | 核心資料模型 |
| **識別碼** | `name` (unique_id) | `item_no`, `item_name` | 項目識別 |
| **鍵值** | `ItemKey` | `item_key` | 項目鍵值 (test_point_runAllTest.py 專用) |
| **數值類型** | `value_type` | `value_type` | 數值類型 (string/integer/float) |
| **限制類型** | `limit_type` | `limit_type` | 限制類型 (lower/upper/both/equality/...) |
| **相等限制** | `equality_limit` | `eq_limit` | 相等限制值 |
| **下限** | `lower_limit` | `lower_limit` | 規格下限 |
| **上限** | `upper_limit` | `upper_limit` | 規格上限 |
| **單位** | `unit` | `unit` | 測量單位 |
| **執行狀態** | `executed`, `passed` | `enabled` | 執行狀態 |
| **測量值** | `value` | `measure_value` | 測量結果值 |

#### 9.2.2 限制類型 (LimitType) 對應

**PDTool4 test_point.py:**
```python
# PDTool4 的限制類型定義
class LOWER_LIMIT_TYPE(LimitType): pass
class UPPER_LIMIT_TYPE(LimitType): pass
class BOTH_LIMIT_TYPE(LimitType): pass
class NONE_LIMIT_TYPE(LimitType): pass
class EQUALITY_LIMIT_TYPE(LimitType): pass
class PARTIAL_LIMIT_TYPE(LimitType): pass      # test_point_runAllTest.py 專用
class INEQUALITY_LIMIT_TYPE(LimitType): pass   # test_point_runAllTest.py 專用

LIMIT_TYPE_MAP = {
    'lower': LOWER_LIMIT_TYPE,
    'upper': UPPER_LIMIT_TYPE,
    'both': BOTH_LIMIT_TYPE,
    'equality': EQUALITY_LIMIT_TYPE,
    'partial': PARTIAL_LIMIT_TYPE,             # test_point_runAllTest.py
    'inequality': INEQUALITY_LIMIT_TYPE,       # test_point_runAllTest.py
    'none': NONE_LIMIT_TYPE,
}
```

**WebPDTool testplan.py:**
```python
# WebPDTool 將限制類型儲存為字串
class TestPlan(Base):
    limit_type = Column(String(50), nullable=True)  # 字串形式儲存
    # 支援的值: 'lower', 'upper', 'both', 'equality', 'partial', 'inequality', 'none'
```

#### 9.2.3 數值類型 (ValueType) 對應

**PDTool4:**
```python
class STRING_VALUE_TYPE(ValueType):
    @staticmethod
    def cast_call(in_obj): return str(in_obj)

class INTEGER_VALUE_TYPE(ValueType):
    @staticmethod
    def cast_call(in_obj): return int(in_obj, 0)

class FLOAT_VALUE_TYPE(ValueType):
    @staticmethod
    def cast_call(in_obj): return float(in_obj)

VALUE_TYPE_MAP = {
    'string': STRING_VALUE_TYPE,
    'integer': INTEGER_VALUE_TYPE,
    'float': FLOAT_VALUE_TYPE,
}
```

**WebPDTool:**
```python
class TestPlan(Base):
    value_type = Column(String(50), nullable=True)  # 字串形式儲存
    # 支援的值: 'string', 'integer', 'float'
```

### 9.3 TestPoint 類別詳細分析

#### 9.3.1 PDTool4 TestPoint 初始化

**test_point.py (原始版本):**
```python
class TestPoint(object):
    def __init__(self,
                 name,              # 測試點名稱 (unique_id)
                 unit,              # 單位
                 value_type,        # 數值類型
                 limit_type,        # 限制類型
                 equality_limit=None,   # 相等限制
                 lower_limit=None,      # 下限
                 upper_limit=None,      # 上限
                 ):
        self.executed = False
        self.passed = None
        self.value = None
        self.name = name
        self.unique_id = name
        self.unit = unit
        self.value_type = VALUE_TYPE_MAP[value_type.strip()]
        self.limit_type = LIMIT_TYPE_MAP[limit_type.strip()]
        # ... 處理限制值
```

**test_point_runAllTest.py (runAllTest 版本):**
```python
class TestPoint(object):
    def __init__(self,
                 name,              # 測試點名稱 (unique_id)
                 ItemKey,           # 項目鍵值 (新增)
                 # unit,             # 單位 (移除)
                 value_type,        # 數值類型
                 limit_type,        # 限制類型
                 equality_limit=None,   # 相等限制
                 lower_limit=None,      # 下限
                 upper_limit=None,      # 上限
                 ):
        self.executed = False
        self.passed = None
        self.value = None
        self.ItemKey = ItemKey        # 新增 ItemKey 屬性
        self.name = name
        self.unique_id = name
        # self.unit = unit            # 移除 unit
        # ... 其他初始化
```

#### 9.3.2 WebPDTool TestPlan 模型

```python
class TestPlan(Base):
    __tablename__ = "test_plans"

    # 核心識別欄位
    id = Column(Integer, primary_key=True)
    item_no = Column(Integer, nullable=False)       # 相當於 TestPoint.name (編號)
    item_name = Column(String(100), nullable=False)  # 相當於 TestPoint.name (名稱)
    item_key = Column(String(50), nullable=True)    # 相當於 TestPoint.ItemKey

    # 規格限制欄位
    value_type = Column(String(50), nullable=True)  # 相當於 TestPoint.value_type
    limit_type = Column(String(50), nullable=True)  # 相當於 TestPoint.limit_type
    lower_limit = Column(DECIMAL(15, 6), nullable=True)  # 相當於 TestPoint.lower_limit
    upper_limit = Column(DECIMAL(15, 6), nullable=True)  # 相當於 TestPoint.upper_limit
    eq_limit = Column(String(100), nullable=True)   # 相當於 TestPoint.equality_limit
    unit = Column(String(20), nullable=True)        # 相當於 TestPoint.unit

    # 測試相關欄位
    test_type = Column(String(50), nullable=False)  # 測試類型
    parameters = Column(JSON, nullable=True)        # 測試參數
    enabled = Column(Boolean, default=True)         # 相當於 TestPoint.executed 狀態
    sequence_order = Column(Integer, nullable=False)

    # CSV 專屬欄位
    pass_or_fail = Column(String(20), nullable=True)    # PassOrFail
    measure_value = Column(String(100), nullable=True)  # measureValue
    execute_name = Column(String(100), nullable=True)   # ExecuteName
    case_type = Column(String(50), nullable=True)       # case
    command = Column(String(500), nullable=True)        # Command
    timeout = Column(Integer, nullable=True)            # Timeout
    use_result = Column(String(100), nullable=True)     # UseResult
    wait_msec = Column(Integer, nullable=True)          # WaitmSec
```

### 9.4 TestPointMap 與 WebPDTool 的測試計畫管理

#### 9.4.1 PDTool4 TestPointMap

**檔案位置**: `polish/test_point/test_point_map.py`

```python
class TestPointMap(object):
    """測試點映射管理器 - 管理多個 TestPoint 物件"""

    def __init__(self):
        self._map = {}  # {unique_id: TestPoint}

    def add_test_point(self, test_point):
        """新增測試點，檢查 unique_id 唯一性"""
        unique_id = test_point.unique_id
        if unique_id in self._map:
            raise TestPointUniqueIdViolation(...)
        self._map[unique_id] = test_point

    def get_test_point(self, unique_id):
        """取得測試點"""
        return self._map.get(unique_id)

    def __getitem__(self, unique_id):
        """支援 dict 風格存取"""
        if unique_id in self._map:
            return self._map[unique_id]
        return None

    def all_executed(self):
        """檢查所有測試點是否已執行"""
        return all((tp.executed for tp in self._map.values()))

    def count_executed(self):
        """計算已執行的測試點數量"""
        n_exec = 0
        for n, tp in enumerate(self._map.values()):
            if tp.executed:
                n_exec += 1
        return n_exec, n+1

    def count_skipped(self):
        """計算跳過的測試點數量"""
        c, n = self.count_executed()
        return n - c

    def all_pass(self):
        """檢查所有測試點是否通過"""
        return all((tp.passed for tp in self._map.values()))

    def all_executed_all_pass(self):
        """檢查是否全部執行且通過"""
        return self.all_pass() and self.all_executed()

    def get_fail_uid(self):
        """取得失敗的測試點 UID"""
        for tp in self._map.values():
            if tp.passed == False:
                return tp.unique_id
        return None

def new_test_point_map(limits_table):
    """從 CSV 表格建立 TestPointMap"""
    test_point_map = TestPointMap()
    for row in limits_table:
        # ... 解析 CSV 並建立 TestPoint
        test_point = TestPoint(*row)
        test_point_map.add_test_point(test_point)
    return test_point_map
```

#### 9.4.2 WebPDTool 的測試計畫管理

WebPDTool 使用 SQLAlchemy ORM 進行測試計畫管理，功能分佈在多個檔案:

**Model 層 (app/models/testplan.py):**
```python
class TestPlan(Base):
    """資料庫 ORM 模型，對應 test_plans 表"""
    # 定義資料表結構
    # 提供 relationship 關聯
```

**Schema 層 (app/schemas/testplan.py):**
```python
class TestPlanBase(BaseModel):
    """基礎 Schema"""
    item_no: int
    item_name: str
    test_type: str
    lower_limit: Optional[float]
    upper_limit: Optional[float]
    # ... 其他欄位

class TestPlanCreate(TestPlanBase):
    """建立 Schema"""
    project_id: int
    station_id: int

class TestPlanUpdate(BaseModel):
    """更新 Schema"""
    # 所有欄位皆為 Optional

class TestPlan(TestPlanBase):
    """回應 Schema"""
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
```

**API 層 (使用 SQLAlchemy 查詢):**
```python
# 相當於 TestPointMap 的操作:
def get_test_plans(project_id: int, station_id: int, db: Session):
    """取得測試計畫列表 - 相當於 TestPointMap"""
    return db.query(TestPlan).filter(
        TestPlan.project_id == project_id,
        TestPlan.station_id == station_id
    ).order_by(TestPlan.sequence_order).all()

def get_test_plan_by_id(test_plan_id: int, db: Session):
    """取得單一測試計畫 - 相當於 get_test_point()"""
    return db.query(TestPlan).filter(TestPlan.id == test_plan_id).first()
```

### 9.5 TestPoint 執行與驗證邏輯對應

#### 9.5.1 PDTool4 TestPoint.execute()

**test_point.py (原始版本):**
```python
def execute(self, value, raiseOnFail = RAISE_ON_FAIL):
    """執行測試點驗證"""
    try:
        pass_fail = self._execute(value, raiseOnFail)
        self.passed = pass_fail
        self.executed = True
        return pass_fail
    except TestPointLimitFailure:
        self.passed = False
        self.executed = True
        raise
    finally:
        self.logger.info(str(self))
        # 寫入 result.txt
        f = open(FILE_NAME, 'a')
        f.write(str(self.passed) + ',' + str(self.value) +'\n')
        f.close()

def _execute(self, value, raiseOnFail):
    """內部驗證邏輯"""
    if self.limit_type is NONE_LIMIT_TYPE:
        return True
    if self.limit_type is EQUALITY_LIMIT_TYPE:
        result = bool(str(value) == self.equality_limit)
        if raiseOnFail and result == False:
            raise TestPointEqualityLimitFailure(...)
        return result
    if self.limit_type is LOWER_LIMIT_TYPE:
        lower_result = bool(float(value) >= float(self.lower_limit))
        if raiseOnFail and lower_result == False:
            raise TestPointLowerLimitFailure(...)
        return lower_result
    if self.limit_type is UPPER_LIMIT_TYPE:
        upper_result = bool(float(self.upper_limit) >= float(value))
        if raiseOnFail and upper_result == False:
            raise TestPointUpperLimitFailure(...)
        return upper_result
    if self.limit_type is BOTH_LIMIT_TYPE:
        return upper_result and lower_result
```

**test_point_runAllTest.py (runAllTest 版本 - 支援 PARTIAL_LIMIT_TYPE):**
```python
def execute(self, value, runAllTest, raiseOnFail = RAISE_ON_FAIL):
    """支援 runAllTest 模式的執行"""
    try:
        if value == "No instrument found":
            self.value = value
            self.passed = False
            self.executed = True
            raise
        if "Error: " in value:
            self.value = value
            self.passed = False
            self.executed = True
            raise
        else:
            pass_fail = self._execute(value, runAllTest, raiseOnFail)
            self.passed = pass_fail
            self.executed = True
            return pass_fail
    # ... 異常處理

def _execute(self, value, runAllTest, raiseOnFail):
    """支援 PARTIAL_LIMIT_TYPE 的驗證"""
    # ... 相同於 test_point.py

    if self.limit_type is PARTIAL_LIMIT_TYPE:
        result = str(self.equality_limit) in str(value)  # 檢查是否包含
        if runAllTest == "ON":
            try:
                result = str(self.equality_limit) in str(value)
                if raiseOnFail and not result:
                    print("Partial_limit : "+str(self.equality_limit))
                    raise TestPointEqualityLimitFailure(...)
            except TestPointEqualityLimitFailure as e:
                print(str(e))
                return result
        else:
            if raiseOnFail and not result:
                print("Partial_limit : "+str(self.equality_limit))
                print(...)
                raise TestPointEqualityLimitFailure
        return result

    # INEQUALITY_LIMIT_TYPE (不相等限制)
    if self.limit_type is INEQUALITY_LIMIT_TYPE:
        result = bool(value != self.equality_limit)
        # ... 類似處理
```

#### 9.5.2 WebPDTool 的規格驗證邏輯

WebPDTool 的規格驗證邏輯分佈在兩個層級:

**1. measurements/base.py - BaseMeasurement.validate_result()**
```python
class BaseMeasurement(ABC):
    def __init__(self, test_plan_item: Dict, config: Dict):
        self.lower_limit = test_plan_item.get("lower_limit")
        self.upper_limit = test_plan_item.get("upper_limit")
        # ...

    def validate_result(self, measured_value: Decimal) -> str:
        """驗證測量值是否符合規格 - 相當於 TestPoint._execute()"""
        if self.lower_limit and measured_value < self.lower_limit:
            return "FAIL"
        if self.upper_limit and measured_value > self.upper_limit:
            return "FAIL"
        return "PASS"
```

**2. MeasurementResult 結構**
```python
class MeasurementResult:
    def __init__(self,
                 item_no: int,
                 item_name: str,
                 result: str,                    # PASS/FAIL/SKIP/ERROR
                 measured_value: Optional[Decimal] = None,
                 lower_limit: Optional[Decimal] = None,
                 upper_limit: Optional[Decimal] = None,
                 unit: Optional[str] = None,
                 error_message: Optional[str] = None,
                 execution_duration_ms: Optional[int] = None):
        self.test_time = datetime.utcnow()
        # ...
```

### 9.6 Canister 容器類別

#### 9.6.1 PDTool4 Canister

```python
class Canister(dict):
    """可動態添加屬性的字典容器"""
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: %s" % name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: %s" % name)
```

**用途**:
- 在 `TestPoint.__init__()` 中用於儲存配置:
  ```python
  self.cfg = Canister()
  self.cfg.test_atlas = TEST_ATLAS
  ```
- 作為動態屬性容器

#### 9.6.2 WebPDTool 的對應

WebPDTool 使用 Python 原生字典和 Pydantic BaseModel:

```python
# 使用 Pydantic Schema
class TestPlanBase(BaseModel):
    # 欄位定義與驗證
    pass

# 使用原生字典
test_plan_item: Dict[str, Any] = {
    "item_no": 1,
    "item_name": "Test1",
    # ...
}
```

### 9.7 欄位對應總結表

| PDTool4 TestPoint | WebPDTool TestPlan | 說明 |
|-------------------|-------------------|------|
| `name` / `unique_id` | `item_no`, `item_name` | 測試點識別 |
| `ItemKey` (runAllTest) | `item_key` | 項目鍵值 |
| `unit` | `unit` | 測量單位 |
| `value_type` | `value_type` | 數值類型 |
| `limit_type` | `limit_type` | 限制類型 |
| `equality_limit` | `eq_limit` | 相等限制 |
| `lower_limit` | `lower_limit` | 規格下限 |
| `upper_limit` | `upper_limit` | 規格上限 |
| `executed` | `enabled` | 執行狀態 |
| `passed` | `pass_or_fail` | 通過狀態 |
| `value` | `measure_value` | 測量值 |
| `cfg` (Canister) | `parameters` (JSON) | 參數配置 |

### 9.8 主要差異總結

#### 架構差異

| 面向 | PDTool4 | WebPDTool |
|------|---------|-----------|
| **資料儲存** | 記憶體物件 (TestPoint) | 資料庫 (SQLAlchemy ORM) |
| **限制類型** | 類別 (Type classes) | 字串 (String) |
| **數值轉換** | cast_call 方法 | 自動轉換 (Decimal) |
| **驗證邏輯** | TestPoint._execute() | BaseMeasurement.validate_result() |
| **結果輸出** | result.txt 檔案 | 資料庫 test_results 表 |
| **容器機制** | Canister (自定義) | Dict / BaseModel |
| **狀態追蹤** | executed, passed | enabled + TestResult.result |

#### 功能差異

**PDTool4 獨有:**
- `PARTIAL_LIMIT_TYPE`: 檢查字串是否包含子字串 (test_point_runAllTest.py)
- `INEQUALITY_LIMIT_TYPE`: 檢查不相等 (test_point_runAllTest.py)
- `re_execute()`: 重新執行測試點
- `runAllTest` 模式: 支援錯誤繼續執行
- SFC 整合 (註解掉的功能)

**WebPDTool 獨有:**
- 資料庫持久化
- RESTful API 介面
- 多專案/工站支援
- CSV 上傳/下載功能
- 批次操作 (刪除/重排序)
- 前端整合

### 9.9 test_point_runAllTest.py 與 test_point.py 的差異

| 特性 | test_point.py | test_point_runAllTest.py |
|------|---------------|-------------------------|
| **ItemKey 參數** | 無 | 有 (取代 unit) |
| **PARTIAL_LIMIT_TYPE** | 無 | 有 (支援子字串匹配) |
| **INEQUALITY_LIMIT_TYPE** | 無 | 有 (支援不相等檢查) |
| **execute() 參數** | `execute(value, raiseOnFail)` | `execute(value, runAllTest, raiseOnFail)` |
| **錯誤處理** | 立即拋出異常 | 支援 runAllTest 模式 (錯誤繼續) |
| **Instrument 錯誤檢查** | 無 | 有 ("No instrument found", "Error:") |

### 9.10 檔案對應關係

| PDTool4 檔案 | WebPDTool 檔案 | 對應關係 |
|-------------|---------------|----------|
| `polish/test_point/test_point.py` | `app/models/testplan.py` | TestPoint → TestPlan 模型 |
| | `app/schemas/testplan.py` | TestPlanCreate/Update/Response |
| | `app/measurements/base.py` | MeasurementResult |
| `polish/test_point/test_point_map.py` | `app/api/testplan.py` (假設存在) | TestPointMap → API CRUD |
| | `app/services/test_plan_service.py` (假設存在) | 業務邏輯層 |
| `polish/test_point/test_point_runAllTest.py` | 同上 | runAllTest 功能由 API 批次執行實作 |

---

### 更新記錄
- 2024-12-23: 初始版本，完整分析 Measurement Codebase
- 2024-12-23: 新增 PDTool4 與 WebPDTool 測量架構對比分析 (第7-8章)
- 2024-12-23: 新增 PDTool4 test_point 模組與 WebPDTool 對應分析 (第9章)
