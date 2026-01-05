#!/usr/bin/env python3
"""測試計畫資料匯入腳本
從 PDTool4/testPlan 目錄下的 CSV 檔案匯入測試計畫資料到資料庫
"""
import sys
import os
from pathlib import Path
import csv
import json

# 新增專案路徑到 Python 路徑
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.project import Project
from app.models.station import Station
from app.models.testplan import TestPlan


def get_or_create_project(db: Session, project_code: str, project_name: str) -> Project:
    """取得或建立專案"""
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        project = Project(
            project_code=project_code,
            project_name=project_name,
            description=f"自動匯入: {project_name}"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        print(f"  ✓ 建立新專案: {project_code} - {project_name}")
    else:
        print(f"  • 使用現有專案: {project_code} - {project_name}")
    return project


def get_or_create_station(db: Session, project_id: int, station_code: str,
                         test_plan_path: str) -> Station:
    """取得或建立站點"""
    station = db.query(Station).filter(
        Station.project_id == project_id,
        Station.station_code == station_code
    ).first()

    station_name = f"{station_code} 測試站"

    if not station:
        station = Station(
            station_code=station_code,
            station_name=station_name,
            project_id=project_id,
            test_plan_path=test_plan_path,
            is_active=True
        )
        db.add(station)
        db.commit()
        db.refresh(station)
        print(f"    ✓ 建立新站點: {station_code}")
    else:
        print(f"    • 使用現有站點: {station_code}")
    return station


def parse_csv_row(row: dict, row_index: int) -> dict:
    """解析 CSV 行資料"""
    # 處理空值
    def safe_str(value):
        return value.strip() if value and value.strip() else None

    # 處理數值
    def safe_float(value):
        if not value or not value.strip():
            return None
        try:
            return float(value.strip())
        except ValueError:
            return None

    # 處理整數
    def safe_int(value):
        if not value or not value.strip():
            return None
        try:
            return int(value.strip())
        except ValueError:
            return None

    return {
        'item_name': safe_str(row.get('ID')),
        'item_key': safe_str(row.get('ItemKey')),
        'value_type': safe_str(row.get('ValueType')),
        'limit_type': safe_str(row.get('LimitType')),
        'eq_limit': safe_str(row.get('EqLimit')),
        'lower_limit': safe_float(row.get('LL')),
        'upper_limit': safe_float(row.get('UL')),
        'pass_or_fail': safe_str(row.get('PassOrFail')),
        'measure_value': safe_str(row.get('measureValue')),
        'execute_name': safe_str(row.get('ExecuteName')),
        'case_type': safe_str(row.get('case')),
        'command': safe_str(row.get('Command')),
        'timeout': safe_int(row.get('Timeout')),
        'use_result': safe_str(row.get('UseResult')),
        'wait_msec': safe_int(row.get('WaitmSec'))
    }


def import_csv_to_db(csv_file_path: str, project_code: str = None,
                     station_code: str = None, test_plan_name: str = None):
    """匯入單個 CSV 檔案到資料庫"""
    db = SessionLocal()

    try:
        csv_path = Path(csv_file_path)
        if not csv_path.exists():
            print(f"✗ 檔案不存在: {csv_file_path}")
            return False

        print(f"\n處理檔案: {csv_path.name}")

        # 從路徑解析專案和站點資訊
        # 路徑格式: PDTool4/testPlan/{Customer}/{Project}/{Station}_testPlan.csv
        # 或: PDTool4/testPlan/Other/{Category}/{File}_testPlan.csv

        if not project_code:
            # 自動從路徑解析
            relative_parts = csv_path.relative_to(Path(csv_file_path).parent.parent.parent.parent).parts
            if len(relative_parts) >= 3:
                project_code = relative_parts[2]  # Customer 或類別名稱

        if not station_code:
            # 從檔名提取站點代碼
            # 例如: XCU_ControlBoard_CANLIN_testPlan.csv -> XCU_ControlBoard_CANLIN
            station_code = csv_path.stem.replace('_testPlan', '')

        if not test_plan_name:
            test_plan_name = csv_path.stem

        # 建立或取得專案
        project = get_or_create_project(db, project_code, f"{project_code} 專案")

        # 建立或取得站點
        # 原有程式碼: test_plan_path=str(csv_path.relative_to('/home/ubuntu/WebPDTool'))
        # 修改: 支援容器環境路徑
        try:
            test_plan_path = str(csv_path.relative_to('/home/ubuntu/WebPDTool'))
        except ValueError:
            # 容器環境中使用絕對路徑
            test_plan_path = str(csv_path)

        station = get_or_create_station(
            db,
            project_id=project.id,
            station_code=station_code,
            test_plan_path=test_plan_path
        )

        # 讀取 CSV 檔案
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            if not rows:
                print(f"  ✗ CSV 檔案沒有資料列")
                return False

            # 刪除該站點現有的測試計畫 (避免重複)
            # db.query(TestPlan).filter(TestPlan.station_id == station.id).delete()
            # db.commit()

            success_count = 0
            skip_count = 0

            for idx, row in enumerate(rows, start=1):
                try:
                    # 解析資料
                    data = parse_csv_row(row, idx)

                    # 檢查必要欄位
                    if not data['item_name']:
                        print(f"    ⚠ 第 {idx} 列: 缺少 ID，跳過")
                        skip_count += 1
                        continue

                    # 判斷測試類型
                    if data['execute_name'] == 'CommandTest':
                        test_type = 'command'
                    elif data['execute_name'] == 'SFCtest':
                        test_type = 'sfc'
                    elif data['execute_name'] == 'Other':
                        test_type = 'other'
                    elif data['execute_name'] == 'URL':
                        test_type = 'url'
                    else:
                        test_type = 'general'

                    # 建立測試計畫項目
                    test_plan = TestPlan(
                        project_id=project.id,
                        station_id=station.id,
                        test_plan_name=test_plan_name,
                        item_no=idx,
                        item_name=data['item_name'],
                        test_type=test_type,
                        parameters={
                            'item_key': data['item_key'],
                            'value_type': data['value_type'],
                            'limit_type': data['limit_type'],
                            'eq_limit': data['eq_limit'],
                            'pass_or_fail': data['pass_or_fail'],
                            'measure_value': data['measure_value']
                        },
                        lower_limit=data['lower_limit'],
                        upper_limit=data['upper_limit'],
                        unit=None,
                        enabled=True,
                        sequence_order=idx,
                        # 新增欄位
                        item_key=data['item_key'],
                        value_type=data['value_type'],
                        limit_type=data['limit_type'],
                        eq_limit=data['eq_limit'],
                        pass_or_fail=data['pass_or_fail'],
                        measure_value=data['measure_value'],
                        execute_name=data['execute_name'],
                        case_type=data['case_type'],
                        command=data['command'],
                        timeout=data['timeout'],
                        use_result=data['use_result'],
                        wait_msec=data['wait_msec']
                    )

                    db.add(test_plan)
                    success_count += 1

                    if success_count % 10 == 0:
                        db.commit()
                        print(f"    已處理 {success_count} 筆資料...")

                except Exception as e:
                    print(f"    ✗ 第 {idx} 列匯入失敗: {str(e)}")
                    skip_count += 1
                    continue

            # 最後提交
            db.commit()

            print(f"\n  ✓ 匯入完成:")
            print(f"    成功: {success_count} 筆")
            print(f"    跳過: {skip_count} 筆")
            print(f"    站點: {station.station_code} (ID: {station.id})")
            print(f"    專案: {project.project_code} (ID: {project.id})")

            return True

    except Exception as e:
        db.rollback()
        print(f"✗ 匯入失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


    # 預設匯入範例檔案
    # 原有程式碼: example_file = "/home/ubuntu/WebPDTool/PDTool4/testPlan/Other/selfTest/UseResult_testPlan.csv"
    example_file = "/app/testplans/UseResult_testPlan.csv"
    print(f"匯入範例檔案: {example_file}\n")
    import_csv_to_db(example_file)


def import_all_csv_files(base_dir: str = "/app/testplans"):
    """匯入所有 CSV 測試計畫檔案"""
    base_path = Path(base_dir)

    if not base_path.exists():
        print(f"✗ 目錄不存在: {base_dir}")
        return

    # 找出所有 CSV 檔案
    csv_files = list(base_path.rglob("*_testPlan.csv"))

    print(f"找到 {len(csv_files)} 個測試計畫檔案\n")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    for csv_file in csv_files:
        if import_csv_to_db(str(csv_file)):
            success_count += 1
        else:
            fail_count += 1

    print("\n" + "=" * 60)
    print(f"\n匯入統計:")
    print(f"  成功: {success_count} 個檔案")
    print(f"  失敗: {fail_count} 個檔案")
    print(f"  總計: {len(csv_files)} 個檔案")


def main():
    """主程式"""
    import argparse

    parser = argparse.ArgumentParser(description='匯入測試計畫 CSV 資料到資料庫')
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='指定單個 CSV 檔案路徑'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='匯入所有測試計畫 CSV 檔案'
    )
    parser.add_argument(
        '--project', '-p',
        type=str,
        help='指定專案代碼'
    )
    parser.add_argument(
        '--station', '-s',
        type=str,
        help='指定站點代碼'
    )
    parser.add_argument(
        '--name', '-n',
        type=str,
        help='指定測試計畫名稱'
    )

    args = parser.parse_args()

    if args.file:
        # 匯入單個檔案
        import_csv_to_db(
            args.file,
            project_code=args.project,
            station_code=args.station,
            test_plan_name=args.name
        )
    elif args.all:
        # 匯入所有檔案
        import_all_csv_files()
    else:
        # 預設匯入範例檔案
        example_file = "/home/ubuntu/WebPDTool/PDTool4/testPlan/Other/selfTest/UseResult_testPlan.csv"
        print(f"匯入範例檔案: {example_file}\n")
        import_csv_to_db(example_file)


if __name__ == "__main__":
    main()
