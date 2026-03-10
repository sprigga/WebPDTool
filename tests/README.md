# WebPDTool Testing Guide

This guide explains how to run and write tests for WebPDTool using pytest.

## Prerequisites

```bash
# Install test dependencies (using uv as specified in CLAUDE.md)
cd backend
uv pip install -e ".[dev]"

# Or install manually
uv pip install pytest pytest-asyncio pytest-cov httpx
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_measurements_refactoring.py

# Run specific test class
pytest tests/test_measurements_refactoring.py::TestLowerLimitValidation

# Run specific test method
pytest tests/test_measurements_refactoring.py::TestLowerLimitValidation::test_lower_limit_validation

# Run with coverage report
pytest --cov=app --cov-report=html

# Run and stop on first failure
pytest -x

# Run failed tests only
pytest --lf

# Enter debug mode on failure
pytest --pdb
```

### Using Markers

```bash
# Run only fast tests
pytest -m "fast"

# Run only unit tests
pytest -m "unit"

# Run only integration tests
pytest -m "integration"

# Run only simulation mode tests (no hardware required)
pytest -m "simulation"

# Skip slow tests
pytest -m "not slow"

# Run only specific instrument tests
pytest -m "instrument_34970a"
pytest -m "instrument_model2306"

# Run multiple markers
pytest -m "simulation and not slow"
pytest -m "unit or integration"

# Run hardware tests (requires physical hardware)
pytest -m "hardware" --run-hardware
```

### Output Options

```bash
# Show print statements (useful for debugging)
pytest -s

# Show extra test summary info
pytest -ra

# Show local variables in tracebacks
pytest -l

# Shorter traceback format
pytest --tb=short

# Very short traceback (only assertion error)
pytest --tb=line

# No traceback (just summary)
pytest --tb=no
```

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── README.md                      # This file
├── test_measurements_refactoring.py  # Measurement validation tests
├── test_instruments_pytest_style.py   # Instrument driver tests (new)
├── test_instruments/              # Instrument-specific tests
│   ├── test_cmw100.py            # CMW100 driver tests
│   ├── test_mt8872a.py           # MT8872A driver tests
│   └── ...
└── test_services/                 # Service layer tests
    └── ...
```

## Writing Tests

### Basic Test Function

```python
import pytest

def test_addition():
    result = 2 + 2
    assert result == 4
```

### Async Test

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result is not None
```

### Using Fixtures

```python
# Using built-in fixture from conftest.py
async def test_with_instrument(instrument_executor):
    result = await instrument_executor.execute_instrument_command(
        instrument_id="34970A_1",
        params={'Item': 'OPEN', 'Channel': '01'},
        simulation=True
    )
    assert result is not None
```

### Parameterized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("foo", "FOO"),
    ("bar", "BAR"),
])
def test_uppercase(input, expected):
    assert input.upper() == expected
```

### Grouping Tests in Classes

```python
@pytest.mark.instruments
@pytest.mark.simulation
class Test34970ADriver:
    """Tests for 34970A driver"""

    async def test_open_channels(self, instrument_executor):
        # Test implementation
        pass

    async def test_close_channels(self, instrument_executor):
        # Test implementation
        pass
```

## Markers Reference

### Execution Speed
- `slow`: Marks tests as slow (>1 second)
- `fast`: Marks tests as fast (<1 second)

### Test Type
- `unit`: Unit tests (fast, isolated, no external deps)
- `integration`: Integration tests (uses external services)
- `e2e`: End-to-end tests (full system testing)

### Hardware Requirements
- `hardware`: Requires physical hardware
- `simulation`: Runs in simulation mode (no hardware)

### Instrument-Specific
- `instrument_34970a`: 34970A Data Acquisition tests
- `instrument_model2306`: MODEL2306 Power Supply tests
- `instrument_it6723c`: IT6723C Power Supply tests
- `instrument_2260b`: 2260B Power Supply tests
- `instrument_cmw100`: CMW100 RF Analyzer tests
- `instrument_mt8872a`: MT8872A Network Tester tests

### Component-Specific
- `measurements`: Measurement layer tests
- `instruments`: Instrument driver tests
- `api`: API endpoint tests
- `services`: Service layer tests

## Common Fixtures

### `instrument_executor`
```python
async def test_example(instrument_executor):
    """Get the global instrument executor instance"""
    await instrument_executor.execute_instrument_command(...)
```

### `db_session`
```python
async def test_database(db_session):
    """Get a test database session (in-memory SQLite)"""
    user = User(name="Test")
    db_session.add(user)
    await db_session.commit()
```

### `async_client`
```python
async def test_api(async_client):
    """Get an async HTTP client for FastAPI testing"""
    response = await async_client.get("/api/users")
    assert response.status_code == 200
```

### `sim_connection`
```python
def test_driver(sim_connection):
    """Get a mock simulation connection"""
    driver = Driver34970A(sim_connection)
    assert driver.simulation_mode is True
```

## Migration from Old Test Style

### Before (manual async main)
```python
async def test_34970a():
    print("Testing 34970A...")
    try:
        result = await executor.execute_instrument_command(...)
        print(f"✓ Result: {result}")
    except Exception as e:
        print(f"✗ Failed: {e}")

async def main():
    await test_34970a()
    await test_model2306()

if __name__ == "__main__":
    asyncio.run(main())
```

### After (pytest style)
```python
@pytest.mark.instruments
@pytest.mark.simulation
@pytest.mark.asyncio
class Test34970ADriver:
    async def test_open_channels(self, instrument_executor):
        result = await instrument_executor.execute_instrument_command(
            instrument_id="34970A_1",
            params={'Item': 'OPEN', 'Channel': '01'},
            simulation=True
        )
        assert result is not None
```

## Best Practices

1. **Use descriptive test names**: `test_invalid_channel_raises_error` not `test_1`

2. **Arrange-Act-Assert pattern**:
```python
def test_user_creation(db_session):
    # Arrange: Set up test data
    user_data = {"name": "Test", "email": "test@example.com"}

    # Act: Execute the function being tested
    user = create_user(user_data)

    # Assert: Verify the result
    assert user.name == "Test"
    assert user.id is not None
```

3. **Use fixtures for setup**: Don't duplicate setup code

4. **Test one thing per test**: Each test should verify one behavior

5. **Use markers appropriately**: Mark slow tests so they can be skipped during quick development

6. **Avoid brittle tests**: Don't test implementation details, test behavior

## CI/CD Integration

```yaml
# .github/workflows/tests.yml example
- name: Run tests
  run: |
    pytest -m "not slow and not hardware" --cov=app --cov-report=xml

- name: Run slow tests
  run: pytest -m "slow" --cov=app
  if: github.event_name == 'schedule'  # Run nightly
```

## Troubleshooting

### Import errors
```bash
# Make sure you're running from the project root
cd /home/ubuntu/python_code/WebPDTool
pytest
```

### Async tests not running
```bash
# Make sure pytest-asyncio is installed
uv pip install pytest-asyncio

# Use the async marker
@pytest.mark.asyncio
async def test_something():
    ...
```

### Database tests failing
```bash
# Ensure aiosqlite is installed
uv pip install aiosqlite
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [pytest markers](https://docs.pytest.org/en/stable/mark.html)
