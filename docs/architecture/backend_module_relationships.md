# Backend Module Relationships - Detailed UML

This document provides detailed UML diagrams showing the relationships between all backend modules.

---

## 1. Module Dependency Graph

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
graph TB
    subgraph Entry["Entry Points"]
        Main["main.py"]
        Dep["dependencies.py"]
    end

    subgraph API["API Layer (app/api/)"]
        AuthAPI["auth.py"]
        ProjectsAPI["projects.py"]
        StationsAPI["stations.py"]
        TestplanAPI["testplan/"]
        TestsAPI["tests.py"]
        MeasurementsAPI["measurements.py"]
        ResultsAPI["results/"]
    end

    subgraph Core["Core Layer (app/core/)"]
        Database["database.py"]
        Security["security.py"]
        Logging["logging.py"]
        Helpers["api_helpers.py"]
        Exceptions["exceptions.py"]
        Constants["constants.py"]
    end

    subgraph Schemas["Schemas Layer (app/schemas/)"]
        UserSchema["user.py"]
        ProjectSchema["project.py"]
        StationSchema["station.py"]
        TestplanSchema["testplan.py"]
        SessionSchema["test_session.py"]
        ResultSchema["test_result.py"]
        MeasurementSchema["measurement.py"]
    end

    subgraph Models["Models Layer (app/models/)"]
        UserModel["user.py"]
        ProjectModel["project.py"]
        StationModel["station.py"]
        TestplanModel["test_plan.py"]
        SessionModel["test_session.py"]
        ResultModel["test_result.py"]
        SfcLogModel["sfc_log.py"]
    end

    subgraph Services["Service Layer (app/services/)"]
        TestEngine["test_engine.py"]
        MeasurementService["measurement_service.py"]
        TestPlanService["test_plan_service.py"]
        InstrumentManager["instrument_manager.py"]
        InstrumentConnection["instrument_connection.py"]
        ReportService["report_service.py"]
        AuthService["auth.py"]
    end

    subgraph Measurements["Measurement Layer (app/measurements/)"]
        Base["base.py"]
        Registry["registry.py"]
        Implementations["implementations.py"]
    end

    subgraph Utils["Utils Layer (app/utils/)"]
        CSVParser["csv_parser.py"]
    end

    subgraph Instruments["Instrument Drivers (app/services/instruments/)"]
        BaseDriver["base.py"]
        COMPort["comport_command.py"]
        Console["console_command.py"]
        Drivers["23 drivers"]
    end

    subgraph DUTComms["DUT Communications (app/services/dut_comms/)"]
        RelayController["relay_controller.py"]
        ChassisController["chassis_controller.py"]
        ChassisProtocol["ltl_chassis_fixt_comms/"]
    end

    %% Entry to API
    Main --> AuthAPI
    Main --> ProjectsAPI
    Main --> StationsAPI
    Main --> TestplanAPI
    Main --> TestsAPI
    Main --> MeasurementsAPI
    Main --> ResultsAPI
    Dep --> AuthAPI
    Dep --> Security

    %% API to Core
    AuthAPI --> Security
    AuthAPI --> Database
    TestsAPI --> Database
    MeasurementsAPI --> Database
    ResultsAPI --> Database

    %% API to Services
    TestsAPI --> TestEngine
    MeasurementsAPI --> InstrumentManager
    TestplanAPI --> TestPlanService
    ResultsAPI --> Database

    %% Services to Core
    TestEngine --> Database
    MeasurementService --> Database
    TestPlanService --> Database
    AuthService --> Database
    InstrumentManager --> Logging

    %% Services to Measurements
    MeasurementService --> Base
    MeasurementService --> Registry
    MeasurementService --> Implementations

    %% Services to Instruments
    InstrumentManager --> InstrumentConnection
    MeasurementService --> InstrumentManager

    %% Measurements Base
    Implementations --> Base
    Registry --> Base

    %% TestPlan to Utils
    TestPlanService --> CSVParser

    %% Instruments
    InstrumentConnection --> BaseDriver
    Drivers --> BaseDriver
    Drivers --> COMPort
    Drivers --> Console

    %% DUT Comms
    ChassisController --> ChassisProtocol
    RelayController --> COMPort

    %% API to Schemas
    AuthAPI --> UserSchema
    ProjectsAPI --> ProjectSchema
    StationsAPI --> StationSchema
    TestplanAPI --> TestplanSchema
    TestsAPI --> SessionSchema
    TestsAPI --> ResultSchema
    MeasurementsAPI --> MeasurementSchema

    %% Schemas to Models (validation mapping)
    UserSchema -.-> UserModel
    ProjectSchema -.-> ProjectModel
    StationSchema -.-> StationModel
    TestplanSchema -.-> TestplanModel
    SessionSchema -.-> SessionModel
    ResultSchema -.-> ResultModel

    %% Services to Models
    TestEngine --> SessionModel
    TestEngine --> ResultModel
    MeasurementService --> TestplanModel
    TestPlanService --> TestplanModel
    AuthService --> UserModel
    InstrumentManager --> SessionModel

    %% Styles
    style Entry fill:#E3F2FD
    style API fill:#FFF3E0
    style Core fill:#F3E5F5
    style Services fill:#E8F5E9
    style Measurements fill:#FCE4EC
    style Instruments fill:#E0F2F1
    style DUTComms fill:#E0F2F1
```

---

## 2. API to Service Mapping Diagram

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
flowchart LR
    subgraph API_Endpoints["API Endpoints"]
        A1["POST /api/auth/login"]
        A2["POST /api/auth/logout"]
        A3["GET /api/projects"]
        A4["POST /api/projects"]
        A5["PUT /api/projects/{id}"]
        A6["DELETE /api/projects/{id}"]
        A7["GET /api/stations"]
        A8["POST /api/stations"]
        A9["GET /api/testplan/stations/{id}/testplan"]
        A10["POST /api/testplan/upload"]
        A11["POST /api/tests/sessions/start"]
        A12["GET /api/tests/sessions/{id}/status"]
        A13["POST /api/tests/sessions/{id}/stop"]
        A14["GET /api/measurements/instruments"]
        A15["POST /api/measurements/instruments/connect"]
        A16["GET /api/results/sessions"]
        A17["GET /api/results/summary"]
        A18["GET /api/results/export/csv/{id}"]
    end

    subgraph Services["Services"]
        S1["AuthService"]
        S2["ProjectService (implicit)"]
        S3["StationService (implicit)"]
        S4["TestPlanService"]
        S5["TestEngine"]
        S6["MeasurementService"]
        S7["InstrumentManager"]
        S8["ReportService"]
    end

    A1 --> S1
    A2 --> S1
    A3 --> S2
    A4 --> S2
    A5 --> S2
    A6 --> S2
    A7 --> S3
    A8 --> S3
    A9 --> S4
    A10 --> S4
    A11 --> S5
    A12 --> S5
    A13 --> S5
    A14 --> S7
    A15 --> S7
    A16 --> S8
    A17 --> S8
    A18 --> S8

    S5 --> S6
    S6 --> S7

    style API_Endpoints fill:#FFF3E0
    style Services fill:#E8F5E9
```

---

## 3. Schema to Model Mapping

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
classDiagram
    class UserSchema {
        <<Pydantic>>
        +UserCreate
        +UserLogin
        +UserResponse
    }

    class UserModel {
        <<SQLAlchemy>>
        +id: int
        +username: str
        +hashed_password: str
        +role: Enum
        +is_active: bool
    }

    class ProjectSchema {
        <<Pydantic>>
        +ProjectCreate
        +ProjectUpdate
        +ProjectResponse
    }

    class ProjectModel {
        <<SQLAlchemy>>
        +id: int
        +project_code: str
        +project_name: str
        +description: str
        +is_active: bool
    }

    class StationSchema {
        <<Pydantic>>
        +StationCreate
        +StationUpdate
        +StationResponse
    }

    class StationModel {
        <<SQLAlchemy>>
        +id: int
        +project_id: int
        +station_code: str
        +station_name: str
        +ip_address: str
        +is_active: bool
    }

    class TestPlanSchema {
        <<Pydantic>>
        +TestPlanCreate
        +TestPlanUpdate
        +TestPlanCSVRow
    }

    class TestPlanModel {
        <<SQLAlchemy>>
        +id: int
        +station_id: int
        +project_id: int
        +item_no: int
        +item_name: str
        +test_type: str
        +parameters: JSON
        +limit_type: str
        +value_type: str
    }

    class TestSessionSchema {
        <<Pydantic>>
        +TestSessionCreate
        +TestSessionResponse
    }

    class TestSessionModel {
        <<SQLAlchemy>>
        +id: int
        +serial_number: str
        +station_id: int
        +user_id: int
        +status: Enum
        +final_result: Enum
        +start_time: datetime
        +end_time: datetime
    }

    class TestResultSchema {
        <<Pydantic>>
        +TestResultCreate
        +TestResultResponse
    }

    class TestResultModel {
        <<SQLAlchemy>>
        +id: bigint
        +test_session_id: int
        +test_plan_id: int
        +measured_value: decimal
        +result: Enum
        +error_message: str
        +execution_duration_ms: int
    }

    UserSchema ..> UserModel : validates
    ProjectSchema ..> ProjectModel : validates
    StationSchema ..> StationModel : validates
    TestPlanSchema ..> TestPlanModel : validates
    TestSessionSchema ..> TestSessionModel : validates
    TestResultSchema ..> TestResultModel : validates
```

---

## 4. Measurement Type Hierarchy

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
classDiagram
    class BaseMeasurement {
        <<Abstract>>
        #item_no: str
        #item_name: str
        #test_type: str
        #lower_limit: float
        #upper_limit: float
        #limit_type: str
        #value_type: str
        #unit: str
        +async prepare(params) None
        +async execute(params) MeasurementResult
        +async cleanup() None
        +validate_result() Tuple[bool, str]
    }

    class PowerSetMeasurement {
        +async prepare()
        +async execute()
        +async cleanup()
        -_set_voltage()
        -_set_current()
    }

    class PowerReadMeasurement {
        +async prepare()
        +async execute()
        +async cleanup()
        -_read_voltage()
        -_read_current()
    }

    class CommandTestMeasurement {
        +async prepare()
        +async execute()
        +async cleanup()
        -_send_command()
        -_parse_response()
    }

    class SFCtestMeasurement {
        +async prepare()
        +async execute()
        +async cleanup()
        -_call_sfc_service()
        -_parse_sfc_response()
    }

    class GetSNMeasurement {
        +async prepare()
        +async execute()
        +async cleanup()
        -_read_serial_number()
    }

    class OPJudgeMeasurement {
        +async prepare()
        +async execute()
        +async cleanup()
        -_prompt_operator()
    }

    class OtherMeasurement {
        +async prepare()
        +async execute()
        +async cleanup()
    }

    class MeasurementResult {
        <<Dataclass>>
        +success: bool
        +value: Any
        +error_message: Optional[str]
        +execution_duration_ms: int
    }

    BaseMeasurement <|-- PowerSetMeasurement
    BaseMeasurement <|-- PowerReadMeasurement
    BaseMeasurement <|-- CommandTestMeasurement
    BaseMeasurement <|-- SFCtestMeasurement
    BaseMeasurement <|-- GetSNMeasurement
    BaseMeasurement <|-- OPJudgeMeasurement
    BaseMeasurement <|-- OtherMeasurement
    BaseMeasurement --> MeasurementResult
```

---

## 5. Instrument Driver Hierarchy

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
classDiagram
    class BaseInstrumentDriver {
        <<Abstract>>
        #instrument_id: str
        #connection: Any
        #config: Dict
        +async initialize() None
        +async reset() None
        +async read_value() Any
        +async write_command() None
        +disconnect() None
    }

    class DigitalMultimeter {
        <<Category>>
    }

    class PowerSupply {
        <<Category>>
    }

    class FunctionGenerator {
        <<Category>>
    }

    class Oscilloscope {
        <<Category>>
    }

    class RFInstrument {
        <<Category>>
    }

    %% Digital Multimeters
    class Keithley2303 {
        +model: str = "2303"
        +async read_voltage()
        +async read_current()
    }

    class Keithley2306 {
        +model: str = "2306"
        +async read_voltage()
        +async read_current()
    }

    class Keithley2015 {
        +model: str = "2015"
        +async read_voltage()
        +async read_current()
    }

    %% DAQ Devices
    class DAQ6510 {
        +model: str = "DAQ6510"
        +async scan_channels()
    }

    class DAQ973A {
        +model: str = "DAQ973A"
        +async scan_channels()
    }

    %% Power Supplies
    class PSW3072 {
        +model: str = "PSW3072"
        +async set_voltage()
        +async set_current()
    }

    %% RF Instruments
    class CMW100 {
        +model: str = "CMW100"
        +async set_rf_power()
        +async measure_rf()
    }

    class APS7050 {
        +model: str = "APS7050"
        +async generate_signal()
    }

    BaseInstrumentDriver <|-- DigitalMultimeter
    BaseInstrumentDriver <|-- PowerSupply
    BaseInstrumentDriver <|-- FunctionGenerator
    BaseInstrumentDriver <|-- Oscilloscope
    BaseInstrumentDriver <|-- RFInstrument

    DigitalMultimeter <|-- Keithley2303
    DigitalMultimeter <|-- Keithley2306
    DigitalMultimeter <|-- Keithley2015
    DigitalMultimeter <|-- DAQ6510
    DigitalMultimeter <|-- DAQ973A

    PowerSupply <|-- PSW3072

    RFInstrument <|-- CMW100
    RFInstrument <|-- APS7050
```

---

## 6. Test Plan Service Class Diagram

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "fontSize": "16px",
    "fontFamily": "Arial, Helvetica, sans-serif",
    "primaryTextColor": "#333333",
    "lineColor": "#555555",
    "primaryColor": "#f0f0f0"
  },
  "flowchart": {
    "padding": 20,
    "nodeSpacing": 60,
    "rankSpacing": 80,
    "curve": "basis",
    "diagramPadding": 30
  }
}}%%
classDiagram
    class TestPlanService {
        <<Service>>
        +async create_test_plan()
        +async get_test_plan()
        +async update_test_plan()
        +async delete_test_plan()
        +async get_station_testplan()
        +validate_unique_id()
        +async bulk_create()
    }

    class TestPlanMap {
        <<Container>>
        -_test_points: Dict
        +add_test_point()
        +get_test_point()
        +remove_test_point()
        +all_executed()
        +count_executed()
        +all_pass()
    }

    class TestPoint {
        <<Entity>>
        +unique_id: str
        +item_no: int
        +item_name: str
        +test_type: str
        +limit_type: LimitType
        +value_type: ValueType
        +lower_limit: float
        +upper_limit: float
        +eq_limit: str
        +enabled: bool
        +executed: bool
        +passed: bool
    }

    class LimitType {
        <<Abstract>>
        +check() bool
        +get_error_message() str
    }

    class LowerLimitType {
        +check(value, limit) bool
    }

    class UpperLimitType {
        +check(value, limit) bool
    }

    class BothLimitType {
        +check(value, lower, upper) bool
    }

    class EqualityLimitType {
        +check(value, expected) bool
    }

    class InequalityLimitType {
        +check(value, expected) bool
    }

    class PartialLimitType {
        +check(value, substring) bool
    }

    class NoneLimitType {
        +check() bool
    }

    class ValueType {
        <<Abstract>>
        +cast() Any
    }

    class StringValueType {
        +cast(value) str
    }

    class IntegerValueType {
        +cast(value) int
    }

    class FloatValueType {
        +cast(value) float
    }

    TestPlanService --> TestPlanMap : uses
    TestPlanMap --> TestPoint : contains
    TestPoint --> LimitType : has
    TestPoint --> ValueType : has

    LimitType <|-- LowerLimitType
    LimitType <|-- UpperLimitType
    LimitType <|-- BothLimitType
    LimitType <|-- EqualityLimitType
    LimitType <|-- InequalityLimitType
    LimitType <|-- PartialLimitType
    LimitType <|-- NoneLimitType

    ValueType <|-- StringValueType
    ValueType <|-- IntegerValueType
    ValueType <|-- FloatValueType
```

---

`★ Insight ─────────────────────────────────────`
1. **Schema-to-Model separation** ensures clean validation layer (Pydantic) before database persistence (SQLAlchemy), preventing invalid data from reaching the database
2. **Limit/Value Type polymorphism** allows PDTool4's 7 limit types and 3 value types to be extended without modifying validation logic
3. **TestPlanMap** implements a dictionary-like container that tracks execution state (executed, passed) for runAllTest mode error collection
`─────────────────────────────────────────────────`
