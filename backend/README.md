# WebPDTool Backend

FastAPI-based backend for WebPDTool application.

## Setup

1. Install dependencies using uv:
```bash
cd backend
uv sync
```

2. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
```

3. Update database configuration in `.env`

4. Run the application:
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once the application is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Directory Structure

```
backend/
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Core functionality
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   ├── measurements/  # Test measurement modules
│   └── utils/         # Utility functions
├── alembic/           # Database migrations
├── tests/             # Tests
└── pyproject.toml     # Project dependencies
```
