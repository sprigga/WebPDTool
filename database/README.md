# WebPDTool Database

MySQL database schema and seed data for WebPDTool.

## Setup

### Option 1: Using Docker (Recommended)

If MySQL is running in a Docker container, use `docker exec` to execute the import commands:

1. Create database and tables:
```bash
docker exec webpdtool-db mysql -u root -prootpassword < /home/ubuntu/WebPDTool/database/schema.sql
```

2. (Optional) Load seed data for development:
```bash
docker exec webpdtool-db mysql -u root -prootpassword < /home/ubuntu/WebPDTool/database/seed_data.sql
```

3. (Optional) Verify the tables were created:
```bash
docker exec webpdtool-db mysql -u root -prootpassword -e "USE webpdtool; SHOW TABLES;"
```

**Note**: Replace `webpdtool-db` with your actual container name if different. The password `rootpassword` comes from the `MYSQL_ROOT_PASSWORD` environment variable in `.env`.

### Option 2: Using Local MySQL

If MySQL 8.0+ is installed and running locally:

1. Create database and tables:
```bash
mysql -u root -p < schema.sql
```

2. (Optional) Load seed data for development:
```bash
mysql -u root -p < seed_data.sql
```

When prompted, enter your MySQL root password.

## Default Users

After loading seed data, the following users are available:

| Username | Password | Role | Description |
|----------|----------|------|-------------|
| admin | admin123 | admin | System administrator |
| engineer1 | admin123 | engineer | Test engineer |
| operator1 | admin123 | operator | Test operator |

**Note**: Please change these passwords in production!

## Database Schema

The database consists of the following tables:

- **users**: User accounts and authentication
- **projects**: Test projects
- **stations**: Test stations within projects
- **test_plans**: Test plan configurations
- **test_sessions**: Test execution sessions
- **test_results**: Individual test results
- **configurations**: System configuration
- **sfc_logs**: SFC communication logs
- **modbus_logs**: Modbus communication logs

## Migrations

Database migrations will be managed using Alembic (in the backend directory).
