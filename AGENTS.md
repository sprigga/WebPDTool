# AGENTS.md

This file guides agentic coding agents working in this repository. WebPDTool is a Vue 3 + FastAPI testing system refactored from PDTool4, with complete measurement abstraction supporting 7 limit types and 3 value types.

## Build/Lint/Test Commands

### Backend (Python 3.11+)

```bash
cd backend

# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 9100

# Install dependencies
pip install -e .
# OR using uv (recommended)
uv pip install -e .

# Run all tests
pytest

# Run single test file
pytest tests/test_api/test_auth.py

# Run single test function
pytest tests/test_api/test_auth.py::test_login_success

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app tests/

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Frontend (Vue 3)

```bash
cd frontend

# Development server
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Install dependencies
npm install
```

### Docker (Primary Development Environment)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Stop services
docker-compose down

# Execute commands in containers
docker-compose exec backend pytest
docker-compose exec backend alembic upgrade head
```

## Code Style Guidelines

### Backend (Python)

**Imports**: Order: standard library → third-party → local app imports. Use `from typing import Dict, Any, List, Optional, Union, Tuple`. Use `from sqlalchemy.orm import Session` (not `from sqlalchemy import`). Blank line between import groups.

**Type Hints**: Required for all function parameters and return values. Use `Dict[str, Any]` for JSON bodies, `Optional[Type]` for nullable fields, `List[Type]` for arrays.

**Naming Conventions**: Classes: PascalCase (e.g., `BaseMeasurement`, `TestEngine`). Functions/Variables: snake_case (e.g., `execute_measurement`, `user_id`). Constants: UPPER_SNAKE_CASE (e.g., `MEASUREMENT_REGISTRY`). Private methods: leading underscore.

**Error Handling**: Use FastAPI `HTTPException` for API errors. Use custom exceptions from `app.core.exceptions` (e.g., `MeasurementExecutionError`). Include status codes and descriptive detail messages.

**Async/Await Pattern**: All database operations must be async with SQLAlchemy 2.0. Use `async def` for endpoint handlers and service methods. Use `await db.execute()` for queries.

**Docstrings**: Use triple-quoted strings at module/function/class level. Brief one-line description for simple functions.

**Measurement Abstraction**: All measurements inherit from `BaseMeasurement` in `app/measurements/base.py`. Implement `prepare()`, `execute()`, `cleanup()` async methods. Register in `MEASUREMENT_REGISTRY` via `app/measurements/registry.py`. Return `MeasurementResult` dataclass. Support 7 limit types: lower, upper, both, equality, inequality, partial, none. Support 3 value types: string, integer, float.

**Database Models**: Use SQLAlchemy ORM models in `app/models/`. Use Pydantic schemas in `app/schemas/` for validation. Enum classes for role/status fields. Index columns used in queries.

**API Routes**: Use `APIRouter` for modular routing. Use `response_model` for output validation. Use `Depends()` for dependency injection. Prefix routes with `/api`.

### Frontend (Vue 3)

**Imports**: Use named imports for components (e.g., `import { ElButton } from 'element-plus'`). Use default import for Pinia stores (e.g., `import { useAuthStore } from '@/stores/auth'`). Use `@` alias for src directory.

**Component Structure**: Use `<script setup>` for Composition API. Define reactive state with `ref()` and `computed()`. Export functions/methods explicitly.

**Naming Conventions**: Components: PascalCase (e.g., `ProjectStationSelector.vue`). Functions/Variables: camelCase (e.g., `handleLogin`, `userName`). Constants: UPPER_SNAKE_CASE (e.g., `API_BASE_URL`). CSS classes: kebab-case.

**API Calls**: Use centralized API clients in `frontend/src/api/`. Handle errors via Axios interceptor in `client.js`. Use async/await for asynchronous operations.

**State Management**: Use Pinia stores in `frontend/src/stores/`. Use `defineStore` with setup function syntax. Persist tokens to localStorage.

**Element Plus**: Use Element Plus components for UI consistency. Follow existing patterns in `TestMain.vue` for test-related interfaces.

## Architecture Notes

**Backend Architecture**: API Layer: `app/api/*.py` - FastAPI routes organized by domain. Service Layer: `app/services/*.py` - Business logic (TestEngine, InstrumentManager). Measurement Layer: `app/measurements/*.py` - Abstract measurement system. Models: `app/models/*.py` - SQLAlchemy ORM. Schemas: `app/schemas/*.py` - Pydantic validation.

**Frontend Architecture**: Views: `frontend/src/views/*.vue` - Page components. Components: `frontend/src/components/*.vue` - Reusable components. API: `frontend/src/api/*.js` - Axios API clients. Stores: `frontend/src/stores/*.js` - Pinia state management.

**Critical Patterns**: runAllTest Mode: Continue execution after failures, collect error summary. PDTool4 Compatibility: Measurement validation logic in `app/measurements/base.py`. Singleton Pattern: InstrumentManager ensures single connection pool. Async Test Execution: All test operations use asyncio.

## Important Constraints
- NO comments unless explicitly requested
- NO emojis unless explicitly requested
- Use existing libraries only (check `package.json` and `pyproject.toml`)
- Follow existing code patterns in each file
- Backend uses SQLAlchemy 2.0 async (NOT sync patterns)
- Frontend uses Vue 3 Composition API (NOT Options API)
