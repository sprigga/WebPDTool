"""
Enhanced Logging System (Refactored from Polish StdStreamsCaptureHandler)

This module provides:
1. Session-scoped logging (isolate logs per test session)
2. Structured logging with context (request_id, session_id, user_id)
3. Redis-backed real-time log streaming
4. File-based long-term archival

Design Changes from Polish:
- ❌ Removed: Global stdout capture (not suitable for async web environment)
- ✅ Added: Context-aware structured logging
- ✅ Added: Redis integration for real-time log streaming
- ✅ Added: Async-safe logging handlers
"""
import logging
import sys
import time
import contextvars
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from logging.handlers import RotatingFileHandler
import json
import traceback

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


# Context variables for request/session tracking
request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('request_id', default=None)
session_id_var: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar('session_id', default=None)
user_id_var: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar('user_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    Structured JSON formatter for logs
    Adds context variables to every log record
    """

    def format(self, record: logging.LogRecord) -> str:
        # Build structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context variables
        if request_id := request_id_var.get():
            log_entry["request_id"] = request_id
        if session_id := session_id_var.get():
            log_entry["session_id"] = session_id
        if user_id := user_id_var.get():
            log_entry["user_id"] = user_id

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_entry["extra"] = record.extra_data

        return json.dumps(log_entry, ensure_ascii=False)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for console output
    Similar to Polish's VERBOSE_LOG_FORMAT_STRING
    """

    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(levelname)-8s - [%(name)s:%(lineno)d:%(funcName)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def format(self, record: logging.LogRecord) -> str:
        # Add context info if available
        context_parts = []
        if request_id := request_id_var.get():
            context_parts.append(f"req={request_id[:8]}")
        if session_id := session_id_var.get():
            context_parts.append(f"session={session_id}")
        if user_id := user_id_var.get():
            context_parts.append(f"user={user_id}")

        if context_parts:
            record.message = f"[{', '.join(context_parts)}] {record.getMessage()}"

        return super().format(record)


class RedisLogHandler(logging.Handler):
    """
    Redis-backed handler for real-time log streaming

    Stores logs in Redis with TTL for real-time monitoring
    Not for long-term storage - use file handlers for that
    """

    def __init__(self, redis_client: Optional['aioredis.Redis'] = None, ttl_seconds: int = 3600):
        super().__init__()
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds
        self.buffer: List[Dict[str, Any]] = []
        self.last_flush = time.time()
        self.flush_interval = 1.0  # Flush every 1 second

    def emit(self, record: logging.LogRecord):
        """Buffer log record for async flushing"""
        try:
            # Format the record as structured JSON
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            # Add context
            if request_id := request_id_var.get():
                log_entry["request_id"] = request_id
            if session_id := session_id_var.get():
                log_entry["session_id"] = session_id
            if user_id := user_id_var.get():
                log_entry["user_id"] = user_id

            self.buffer.append(log_entry)

            # Auto-flush if interval exceeded
            if time.time() - self.last_flush > self.flush_interval:
                # Note: This is sync flush - should be called from async context
                # In production, use async background task to flush
                pass

        except Exception as e:
            self.handleError(record)

    async def flush_to_redis(self):
        """Async flush buffered logs to Redis"""
        if not self.redis_client or not self.buffer:
            return

        try:
            # Group logs by session_id
            session_logs: Dict[int, List[Dict]] = {}
            global_logs: List[Dict] = []

            for log_entry in self.buffer:
                if session_id := log_entry.get("session_id"):
                    if session_id not in session_logs:
                        session_logs[session_id] = []
                    session_logs[session_id].append(log_entry)
                else:
                    global_logs.append(log_entry)

            # Store session logs
            for session_id, logs in session_logs.items():
                key = f"logs:session:{session_id}"
                for log in logs:
                    await self.redis_client.rpush(key, json.dumps(log, ensure_ascii=False))
                await self.redis_client.expire(key, self.ttl_seconds)

            # Store global logs
            if global_logs:
                key = "logs:global"
                for log in global_logs:
                    await self.redis_client.rpush(key, json.dumps(log, ensure_ascii=False))
                await self.redis_client.expire(key, self.ttl_seconds)

            self.buffer.clear()
            self.last_flush = time.time()

        except Exception as e:
            print(f"Failed to flush logs to Redis: {e}", file=sys.stderr)


class SessionLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter for session-scoped logging
    Automatically adds session context to all log records
    """

    def __init__(self, logger: logging.Logger, session_id: int):
        super().__init__(logger, {"session_id": session_id})
        self.session_id = session_id

    def process(self, msg: str, kwargs: Any) -> tuple:
        # Set session context
        session_id_var.set(self.session_id)
        return msg, kwargs


class LoggingManager:
    """
    Centralized logging manager
    Replaces Polish's init_project_logger/deinit_project_logger
    """

    def __init__(self):
        self.redis_client: Optional['aioredis.Redis'] = None
        self.redis_handler: Optional[RedisLogHandler] = None
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.session_loggers: Dict[int, logging.Logger] = {}

    def setup_logging(
        self,
        log_level: str = "INFO",
        enable_redis: bool = False,
        redis_url: Optional[str] = None,
        enable_json_logs: bool = False
    ):
        """
        Initialize logging system

        Args:
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_redis: Enable Redis log streaming
            redis_url: Redis connection URL
            enable_json_logs: Use structured JSON logs for files
        """
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))

        # Clear existing handlers
        root_logger.handlers.clear()

        # Console handler (human-readable)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(HumanReadableFormatter())
        root_logger.addHandler(console_handler)

        # File handler (rotating)
        file_formatter = StructuredFormatter() if enable_json_logs else HumanReadableFormatter()
        file_handler = RotatingFileHandler(
            self.log_dir / "webpdtool.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Error file handler (errors only)
        error_handler = RotatingFileHandler(
            self.log_dir / "errors.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

        # Redis handler (if enabled)
        if enable_redis and REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = aioredis.from_url(redis_url, decode_responses=False)
                self.redis_handler = RedisLogHandler(self.redis_client, ttl_seconds=3600)
                self.redis_handler.setLevel(logging.INFO)
                root_logger.addHandler(self.redis_handler)
                logging.info("Redis log streaming enabled")
            except Exception as e:
                logging.warning(f"Failed to enable Redis logging: {e}")

    def get_session_logger(self, session_id: int) -> logging.Logger:
        """
        Get or create session-scoped logger

        Args:
            session_id: Test session ID

        Returns:
            Logger instance with session context
        """
        if session_id in self.session_loggers:
            return self.session_loggers[session_id]

        # Create session-specific logger
        logger = logging.getLogger(f"session.{session_id}")

        # Add session-specific file handler
        session_log_file = self.log_dir / f"session_{session_id}.log"
        session_handler = logging.FileHandler(session_log_file)
        session_handler.setLevel(logging.DEBUG)
        session_handler.setFormatter(HumanReadableFormatter())
        logger.addHandler(session_handler)

        # Wrap in adapter for automatic context
        adapter = SessionLoggerAdapter(logger, session_id)
        self.session_loggers[session_id] = adapter

        return adapter

    async def flush_redis_logs(self):
        """Flush buffered logs to Redis"""
        if self.redis_handler:
            await self.redis_handler.flush_to_redis()

    async def get_session_logs(self, session_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve logs for a specific session from Redis

        Args:
            session_id: Test session ID
            limit: Maximum number of logs to retrieve

        Returns:
            List of log entries
        """
        if not self.redis_client:
            return []

        try:
            key = f"logs:session:{session_id}"
            logs_bytes = await self.redis_client.lrange(key, -limit, -1)
            logs = [json.loads(log_bytes) for log_bytes in logs_bytes]
            return logs
        except Exception as e:
            logging.error(f"Failed to retrieve logs from Redis: {e}")
            return []

    async def cleanup(self):
        """Cleanup resources"""
        if self.redis_client:
            await self.redis_client.close()


# Global logging manager instance
logging_manager = LoggingManager()


def set_request_context(request_id: str, user_id: Optional[int] = None):
    """Set context variables for current request"""
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)


def set_session_context(session_id: int):
    """Set session context variable"""
    session_id_var.set(session_id)


def clear_context():
    """Clear all context variables"""
    request_id_var.set(None)
    session_id_var.set(None)
    user_id_var.set(None)


# Convenience function for backward compatibility
def get_logger(name: str) -> logging.Logger:
    """Get logger instance (backward compatible with Polish)"""
    return logging.getLogger(name)
