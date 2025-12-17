"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.logging import logger

# Import all models to ensure SQLAlchemy knows about them
from app.models.user import User
from app.models.project import Project
from app.models.station import Station
from app.models.testplan import TestPlan
from app.models.test_session import TestSession
from app.models.test_result import TestResult
from app.models.sfc_log import SFCLog

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


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info(f"Shutting down {settings.APP_NAME}")


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
from app.api import auth, projects, stations, testplans, tests, measurements, measurement_results

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(stations.router, prefix="/api", tags=["Stations"])
app.include_router(testplans.router, prefix="/api", tags=["Test Plans"])
app.include_router(tests.router, prefix="/api/tests", tags=["Test Execution"])
app.include_router(measurements.router, prefix="/api/measurements", tags=["Measurements"])
app.include_router(measurement_results.router, prefix="/api/measurement-results", tags=["Measurement Results"])

# Additional routers will be added in later phases
# from app.api import results, sfc, modbus, config
# ...
