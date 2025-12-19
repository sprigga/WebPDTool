"""Test Plan model"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, DECIMAL, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class TestPlan(Base):
    """Test plan item model"""
    __tablename__ = "test_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 新增 project_id 欄位以區分測試計畫所屬專案
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, comment="所屬專案ID")
    station_id = Column(Integer, ForeignKey('stations.id', ondelete='CASCADE'), nullable=False)
    # 新增 test_plan_name 欄位以區分不同測試計劃
    test_plan_name = Column(String(100), nullable=True, comment="測試計劃名稱")

    # Original fields (保留原有欄位)
    item_no = Column(Integer, nullable=False)
    item_name = Column(String(100), nullable=False)
    test_type = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=True)
    lower_limit = Column(DECIMAL(15, 6), nullable=True)
    upper_limit = Column(DECIMAL(15, 6), nullable=True)
    unit = Column(String(20), nullable=True)
    enabled = Column(Boolean, default=True)
    sequence_order = Column(Integer, nullable=False)

    # New fields from CSV (新增欄位對應 CSV)
    item_key = Column(String(50), nullable=True, comment="ItemKey - 項目鍵值")
    value_type = Column(String(50), nullable=True, comment="ValueType - 數值類型")
    limit_type = Column(String(50), nullable=True, comment="LimitType - 限制類型")
    eq_limit = Column(String(100), nullable=True, comment="EqLimit - 等於限制")
    pass_or_fail = Column(String(20), nullable=True, comment="PassOrFail - 通過或失敗")
    measure_value = Column(String(100), nullable=True, comment="measureValue - 測量值")
    execute_name = Column(String(100), nullable=True, comment="ExecuteName - 執行名稱")
    case_type = Column(String(50), nullable=True, comment="case - 案例類型")
    command = Column(String(500), nullable=True, comment="Command - 命令")
    timeout = Column(Integer, nullable=True, comment="Timeout - 超時時間(毫秒)")
    use_result = Column(String(100), nullable=True, comment="UseResult - 使用結果")
    wait_msec = Column(Integer, nullable=True, comment="WaitmSec - 等待毫秒")

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    # 修正: 使用字串引用避免循環導入問題
    # project = relationship("Project")  # 原有程式碼: 新增 project 關聯
    station = relationship("Station")

    def __repr__(self):
        return f"<TestPlan {self.item_name}>"
