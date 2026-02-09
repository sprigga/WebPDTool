#!/usr/bin/env python3
"""
驗證 test_plans 表遷移是否成功
檢查所有必要的欄位是否存在並符合 ORM 模型定義
"""
import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text, inspect
from app.core.database import SessionLocal, engine
from app.models.testplan import TestPlan

def verify_migration():
    """驗證遷移結果"""
    print("=" * 70)
    print("Test Plans Table Migration Verification")
    print("=" * 70)

    db = SessionLocal()
    inspector = inspect(engine)

    try:
        # 取得實際表結構
        columns = inspector.get_columns('test_plans')
        column_names = {col['name'] for col in columns}

        # 取得 ORM 模型預期的欄位
        expected_columns = {col.name for col in TestPlan.__table__.columns}

        print(f"\n✓ 實際欄位數: {len(column_names)}")
        print(f"✓ 預期欄位數: {len(expected_columns)}")

        # 檢查缺少的欄位
        missing = expected_columns - column_names
        if missing:
            print(f"\n✗ 缺少欄位: {missing}")
            return False
        else:
            print(f"\n✓ 所有必要欄位都存在")

        # 檢查多餘的欄位
        extra = column_names - expected_columns
        if extra:
            print(f"\n⚠ 多餘欄位: {extra}")

        # 驗證關鍵欄位
        print("\n檢查關鍵欄位:")
        critical_fields = ['project_id', 'station_id', 'test_plan_name', 'item_key',
                          'value_type', 'limit_type', 'command', 'timeout', 'wait_msec']

        for field in critical_fields:
            if field in column_names:
                print(f"  ✓ {field}")
            else:
                print(f"  ✗ {field} - MISSING!")
                return False

        # 檢查外鍵約束
        print("\n檢查外鍵約束:")
        fks = inspector.get_foreign_keys('test_plans')
        fk_columns = {fk['constrained_columns'][0] for fk in fks}

        if 'project_id' in fk_columns:
            print("  ✓ project_id foreign key")
        else:
            print("  ⚠ project_id foreign key not found (可能需要手動添加)")

        if 'station_id' in fk_columns:
            print("  ✓ station_id foreign key")
        else:
            print("  ✗ station_id foreign key - MISSING!")

        # 檢查索引
        print("\n檢查索引:")
        indexes = inspector.get_indexes('test_plans')
        print(f"  ✓ 找到 {len(indexes)} 個索引")
        for idx in indexes:
            print(f"    - {idx['name']}: {idx['column_names']}")

        # 檢查資料
        print("\n檢查資料:")
        result = db.execute(text("SELECT COUNT(*) as count FROM test_plans"))
        total_records = result.fetchone()[0]
        print(f"  ✓ 總記錄數: {total_records}")

        if total_records > 0:
            result = db.execute(text("""
                SELECT
                    COUNT(DISTINCT project_id) as projects,
                    COUNT(DISTINCT station_id) as stations,
                    COUNT(DISTINCT test_plan_name) as test_plans,
                    COUNT(*) as total_items
                FROM test_plans
            """))
            stats = result.fetchone()
            print(f"  ✓ 專案數: {stats[0]}")
            print(f"  ✓ 工站數: {stats[1]}")
            print(f"  ✓ 測試計畫數: {stats[2]}")
            print(f"  ✓ 測試項目數: {stats[3]}")

        print("\n" + "=" * 70)
        print("✅ Migration verification PASSED!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n✗ 驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = verify_migration()
    sys.exit(0 if success else 1)
