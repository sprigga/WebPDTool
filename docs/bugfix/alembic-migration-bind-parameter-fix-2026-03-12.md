# Alembic Migration Bind Parameter Fix

**Date:** 2026-03-12
**Status:** Fixed
**Severity:** High - Blocks deployment

## Issue Description

The Alembic migration `20260312_add_instruments_table.py` was failing during the Docker container startup with the following error:

```
sqlalchemy.exc.InvalidRequestError: A value is required for bind parameter '5000'
[SQL: INSERT INTO instruments ... VALUES ..., '{"address":"TCPIP0::192.168.1.10::inst0::INSTR","timeout"%(5000)s}', ...]
```

The migration was trying to seed the `instruments` table with default instrument configurations, but SQLAlchemy was misinterpreting the JSON string `"timeout":5000` as a bind parameter.

## Root Cause Analysis

### The Problem

1. **SQLAlchemy's `text()` parameter parsing**: SQLAlchemy uses `:param` syntax for bind parameters in SQL statements
2. **MySQL dialect conversion**: The MySQL driver (using `pyformat` style) converts `:param` to `%(param)s`
3. **JSON string collision**: The JSON string `{"address":"TCPIP0::192.168.1.10::inst0::INSTR","timeout":5000}` contains `:5000` (colon followed by number)
4. **False positive**: SQLAlchemy interpreted `:5000` as a bind parameter named "5000"

### Why `sa.text()` Didn't Help

The initial fix attempt used `sa.text()` with the following comment:
```python
# 注意：必須用 sa.text() 包裝，避免 SQLAlchemy 把 JSON 中的 ":5000" 誤解為
# bind parameter "%(5000)s"，導致 InvalidRequestError。
op.execute(sa.text("""..."""))
```

However, `sa.text()` still goes through SQLAlchemy's parameter parser - it's designed to enable parameter binding, not disable it.

### Why Plain `op.execute()` Also Failed

```python
op.execute("""INSERT INTO ... VALUES ('...', '{"timeout":5000}', ...)""")
```

Even without `sa.text()`, `op.execute()` internally processes the SQL through SQLAlchemy's engine, which still parses for bind parameters.

## Solution

### Bypass SQLAlchemy's Parameter Parsing

The solution is to use the raw DBAPI connection's cursor, which executes SQL directly without any parameter parsing:

```python
from sqlalchemy.engine import Connection

def upgrade() -> None:
    # ... table creation code ...

    # Seed default instruments using raw DBAPI connection
    # to bypass SQLAlchemy's parameter parsing
    conn = op.get_bind()
    if isinstance(conn, Connection):
        # SQLAlchemy Connection - use the raw DBAPI connection
        dbapi_conn = conn.connection
        cursor = dbapi_conn.cursor()
    else:
        # Already a DBAPI connection
        cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO instruments (instrument_id, instrument_type, name, conn_type, conn_params, enabled, description)
        VALUES
          ('DAQ973A_1', 'DAQ973A', 'Keysight DAQ973A #1',
           'VISA', '{"address":"TCPIP0::192.168.1.10::inst0::INSTR","timeout":5000}',
           0, 'Keysight DAQ973A data acquisition system'),

          ('MODEL2303_1', 'MODEL2303', 'Keysight 2303 Power Supply #1',
           'VISA', '{"address":"TCPIP0::192.168.1.11::inst0::INSTR","timeout":5000}',
           0, 'Keysight 2303 power supply'),

          ('console_1', 'console', 'Console Command (default)',
           'LOCAL', '{"address":"local://console"}',
           1, 'Virtual instrument for OS subprocess command execution'),

          ('comport_1', 'comport', 'COM Port Command (default)',
           'LOCAL', '{"address":"local://comport"}',
           1, 'Virtual instrument for serial port command execution'),

          ('tcpip_1', 'tcpip', 'TCP/IP Command (default)',
           'LOCAL', '{"address":"local://tcpip"}',
           1, 'Virtual instrument for TCP/IP socket command execution')
        ON DUPLICATE KEY UPDATE
          name        = VALUES(name),
          conn_type   = VALUES(conn_type),
          conn_params = VALUES(conn_params),
          description = VALUES(description)
    """)
    cursor.close()
```

## Debugging Process

### 1. Initial Error Analysis

```
ERROR: A value is required for bind parameter '5000'
SQL: ... '{"timeout"%(5000)s}', ...
```

The `%(5000)s` format indicated MySQL's `pyformat` paramstyle was being used.

### 2. Verification Steps

```bash
# Check if the table already exists (manual SQL migration was run)
docker-compose exec db mysql -uroot -prootpassword webpdtool -e "SHOW TABLES LIKE 'instruments';"
# Result: Table exists

# Check current alembic version
docker-compose exec db mysql -uroot -prootpassword webpdtool -e "SELECT * FROM alembic_version;"
# Result: a8124fdea538 (previous version, not the new migration)

# Check instruments data
docker-compose exec db mysql -uroot -prootpassword webpdtool -e "SELECT * FROM instruments;"
# Result: 5 rows exist (from manual SQL migration)
```

### 3. File Content Verification

```bash
# Check the migration file in the container
docker-compose exec backend cat /app/alembic/versions/20260312_add_instruments_table.py | grep -A5 "5000"
```

The source file was correct with `"timeout":5000`, but the error still occurred.

### 4. Cache Clearing Attempt

```bash
# Clear Python bytecode cache
docker-compose exec backend find /app/alembic -name "*.pyc" -delete
docker-compose restart backend
```

This didn't help because the issue was in SQLAlchemy's parsing, not cached bytecode.

### 5. Final Solution Implementation

Changed from:
```python
op.execute(sa.text("""..."""))
```

To:
```python
conn = op.get_bind()
cursor = conn.connection.cursor()
cursor.execute("""...""")
cursor.close()
```

## Lessons Learned

### 1. SQLAlchemy Parameter Syntax

| Dialect | Paramstyle | Example |
|---------|------------|---------|
| PostgreSQL | `named` | `:param` |
| MySQL (mysqlconnector) | `format` | `%s` |
| MySQL (pymysql/aiomysql) | `pyformat` | `%(param)s` |

### 2. When to Use Raw DBAPI Connection

Use raw DBAPI cursor when:
- SQL contains JSON with colons followed by numbers
- SQL contains other strings that might be interpreted as parameters
- You need complete control over SQL execution

### 3. Migration Best Practices

1. **Test migrations locally first** before deploying
2. **Use `--sql` flag** to see generated SQL without executing:
   ```bash
   alembic upgrade head --sql
   ```
3. **Make migrations idempotent** using `ON DUPLICATE KEY UPDATE` (MySQL) or `ON CONFLICT` (PostgreSQL)
4. **Avoid complex JSON in migrations** - consider seeding data via separate scripts

## Related Files

- **Migration file**: `backend/alembic/versions/20260312_add_instruments_table.py`
- **Raw SQL reference**: `database/migrations/add_instruments_table.sql`
- **Instrument model**: `backend/app/models/instrument.py`
- **Docker entrypoint**: `backend/docker-entrypoint.sh`

## Verification

After the fix:

```bash
# Verify migration completed
docker-compose exec db mysql -uroot -prootpassword webpdtool -e "SELECT * FROM alembic_version;"
# Result: version_num = 20260312_add_instruments_table

# Verify instruments data
docker-compose exec db mysql -uroot -prootpassword webpdtool -e "SELECT COUNT(*) FROM instruments;"
# Result: 5

# Verify API endpoint
curl -s http://localhost:9100/api/instruments | python3 -m json.tool
# Result: Returns all 5 instruments with correct JSON structure
```

## References

- SQLAlchemy bind parameter documentation: https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.text
- Alembic `op.execute()` documentation: https://alembic.sqlalchemy.org/en/latest/ops.html#alembic.operations.Operations.execute
- MySQL JSON data type: https://dev.mysql.com/doc/refman/8.0/en/json.html
