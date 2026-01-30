"""FastAPI application entry point"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
import asyncio
import uuid

# ✅ Refactored: Use new logging system instead of app.core.logging
# from app.core.logging import logger  # ❌ Old logging
from app.core.logging_v2 import logging_manager, set_request_context, clear_context, get_logger

# Initialize logger
logger = get_logger(__name__)

# Import all models to ensure SQLAlchemy knows about them
from app.models.user import User
from app.models.project import Project
from app.models.station import Station
from app.models.testplan import TestPlan
from app.models.test_session import TestSession
from app.models.test_result import TestResult
from app.models.sfc_log import SFCLog

# ✅ Added: Initialize logging system before creating app
logging_manager.setup_logging(
    log_level=settings.LOG_LEVEL,
    enable_redis=settings.REDIS_ENABLED,
    redis_url=settings.REDIS_URL,
    enable_json_logs=settings.ENABLE_JSON_LOGS
)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ Added: Logging middleware for request context tracking
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    Add request context to all logs within this request
    Automatically tracks: request_id, user_id, session_id
    """
    # Generate unique request ID
    request_id = str(uuid.uuid4())

    # Extract user_id if available (set by auth middleware)
    user_id = getattr(request.state, 'user_id', None)

    # Set context for this request
    set_request_context(request_id, user_id)

    # Process request
    response = await call_next(request)

    # Clear context after request completes
    clear_context()

    # Add request ID to response headers for debugging
    response.headers["X-Request-ID"] = request_id

    return response


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # ✅ Added: Start Redis log flusher if Redis is enabled
    if settings.REDIS_ENABLED:
        async def flush_logs_periodically():
            """Background task to flush buffered logs to Redis"""
            while True:
                try:
                    await logging_manager.flush_redis_logs()
                except Exception as e:
                    logger.error(f"Failed to flush logs to Redis: {e}")
                await asyncio.sleep(1)  # Flush every second

        # Start background task
        asyncio.create_task(flush_logs_periodically())
        logger.info("Redis log streaming enabled - background flusher started")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info(f"Shutting down {settings.APP_NAME}")

    # ✅ Added: Cleanup logging resources
    await logging_manager.cleanup()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Import and include routers
# Original single-file routers backed up as .backup
# New modular routers are used instead
from app.api import auth, projects, stations, tests, measurements, dut_control
from app.api.testplan import router as testplans_router
from app.api.results import router as measurement_results_router

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(stations.router, prefix="/api", tags=["Stations"])
app.include_router(testplans_router, prefix="/api", tags=["Test Plans"])
app.include_router(tests.router, prefix="/api/tests", tags=["Test Execution"])
app.include_router(measurements.router, prefix="/api/measurements", tags=["Measurements"])
app.include_router(measurement_results_router, prefix="/api/measurement-results", tags=["Measurement Results"])
app.include_router(dut_control.router, prefix="/api", tags=["DUT Control"])

# Additional routers will be added in later phases
# from app.api import results, sfc, modbus, config
# ...
