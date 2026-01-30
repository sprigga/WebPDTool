#!/usr/bin/env python3
"""
測試 Redis Logging 功能

這個腳本用於測試 logging 系統是否正常寫入資料到 Redis。

使用方式:
    # 啟用 Redis 並執行測試
    REDIS_ENABLED=true python scripts/test_redis_logging.py

    或者先啟動 Redis 後執行:
    docker run -d --name redis-test -p 6379:6379 redis:7-alpine
    uv run python scripts/test_redis_logging.py
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加專案路徑到 Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import redis.asyncio as aioredis
import json


async def test_redis_logging():
    """測試 Redis logging 功能"""

    print("=" * 60)
    print("Redis Logging 測試")
    print("=" * 60)

    # 讀取配置
    from app.config import settings
    from app.core.logging_v2 import (
        logging_manager,
        set_session_context,
        get_logger,
        clear_context
    )

    # 檢查 Redis 是否啟用
    if not settings.REDIS_ENABLED:
        print(f"\n⚠️  Redis 未啟用!")
        print(f"當前設定: REDIS_ENABLED={settings.REDIS_ENABLED}")
        print(f"\n請在 .env 檔案中設定: REDIS_ENABLED=true")
        print(f"或在執行時設定環境變數:")
        print(f"  REDIS_ENABLED=true uv run python scripts/test_redis_logging.py")
        return False

    print(f"\n📋 設定資訊:")
    print(f"  REDIS_URL: {settings.REDIS_URL}")
    print(f"  REDIS_LOG_TTL: {settings.REDIS_LOG_TTL} 秒")

    # 1. 測試 Redis 連線
    print(f"\n1️⃣  測試 Redis 連線...")
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        print(f"   ✅ Redis 連線成功!")
    except Exception as e:
        print(f"   ❌ Redis 連線失敗: {e}")
        print(f"\n💡 請確認 Redis 服務正在運行:")
        print(f"   Docker: docker run -d --name redis-test -p 6379:6379 redis:7-alpine")
        print(f"   本地: redis-server")
        return False
    finally:
        await redis_client.close()

    # 2. 初始化 logging 系統 (啟用 Redis)
    print(f"\n2️⃣  初始化 logging 系統...")
    logging_manager.setup_logging(
        log_level="INFO",
        enable_redis=True,
        redis_url=settings.REDIS_URL,
        enable_json_logs=False
    )
    print(f"   ✅ Logging 系統初始化完成")

    # 3. 建立測試用 logger
    print(f"\n3️⃣  產生測試日誌...")
    logger = get_logger("test")

    # 設定 session context
    test_session_id = 99999
    set_session_context(test_session_id)

    # 產生各種層級的日誌
    logger.debug("這是 DEBUG 日誌 (不應該出現在 Redis)")
    logger.info("這是 INFO 日誌")
    logger.warning("這是 WARNING 日誌")
    logger.error("這是 ERROR 日誌")

    # 4. Flush 日誌到 Redis
    print(f"\n4️⃣  將日誌 flush 到 Redis...")
    await logging_manager.flush_redis_logs()
    print(f"   ✅ 日誌已 flush")

    # 5. 從 Redis 讀取日誌驗證
    print(f"\n5️⃣  從 Redis 讀取日誌驗證...")
    logs = await logging_manager.get_session_logs(test_session_id, limit=10)

    if not logs:
        print(f"   ❌ 沒有讀取到任何日誌!")
        return False

    print(f"   ✅ 讀取到 {len(logs)} 筆日誌:")
    print()
    print("   " + "-" * 55)
    for i, log in enumerate(logs, 1):
        level = log.get("level", "UNKNOWN")
        message = log.get("message", "")
        timestamp = log.get("timestamp", "")
        print(f"   [{i}] {timestamp} | {level:7} | {message}")
    print("   " + "-" * 55)

    # 6. 直接連接 Redis 驗證資料
    print(f"\n6️⃣  直接從 Redis 驗證...")
    redis_client = aioredis.from_url(settings.REDIS_URL)

    # 檢查 session logs
    session_key = f"logs:session:{test_session_id}"
    session_count = await redis_client.llen(session_key)
    print(f"   Session key: {session_key}")
    print(f"   Session logs count: {session_count}")

    # 檢查 global logs
    global_key = "logs:global"
    global_count = await redis_client.llen(global_key)
    print(f"   Global key: {global_key}")
    print(f"   Global logs count: {global_count}")

    # 檢查 TTL
    ttl = await redis_client.ttl(session_key)
    print(f"   Session key TTL: {ttl} 秒")

    # 清理測試資料
    print(f"\n7️⃣  清理測試資料...")
    await redis_client.delete(session_key)
    print(f"   ✅ 測試資料已清理")

    await redis_client.close()
    await logging_manager.cleanup()

    print(f"\n" + "=" * 60)
    print(f"✅ Redis Logging 測試通過!")
    print(f"=" * 60)

    return True


async def test_redis_with_cli():
    """使用 redis-cli 驗證 (如果可用)"""
    import subprocess

    print(f"\n💡 使用 redis-cli 手動驗證指令:")
    print(f"   redis-cli LRANGE logs:session:99999 0 -1")
    print(f"   redis-cli LRANGE logs:global 0 -1")
    print(f"   redis-cli TTL logs:session:99999")
    print(f"   redis-cli KEYS logs:*")


if __name__ == "__main__":
    try:
        result = asyncio.run(test_redis_logging())
        if result:
            asyncio.run(test_redis_with_cli())
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n\n⚠️  測試中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
