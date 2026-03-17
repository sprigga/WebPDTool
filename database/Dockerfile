# Database Dockerfile for WebPDTool
# Builds a self-contained MySQL image with schema and seed data pre-loaded.
# This image is an alternative to volume-mounting SQL files at runtime.
#
# Usage (standalone):
#   docker build -t webpdtool-db ./database
#   docker run -d -p 33306:3306 \
#     -e MYSQL_ROOT_PASSWORD=rootpassword \
#     -e MYSQL_DATABASE=webpdtool \
#     -e MYSQL_USER=pdtool \
#     -e MYSQL_PASSWORD=pdtool123 \
#     webpdtool-db
#
# Usage (docker-compose):
#   Replace `image: mysql:8.0` with `build: ./database` in docker-compose.yml.

FROM mysql:8.0

# ── Timezone ────────────────────────────────────────────────────────────────
ENV TZ=Asia/Taipei

# ── MySQL tuning configuration ───────────────────────────────────────────────
# Placed in /etc/mysql/conf.d/ so it is loaded after the default my.cnf.
COPY my.cnf /etc/mysql/conf.d/webpdtool.cnf

# ── Initialization scripts ───────────────────────────────────────────────────
# Files in /docker-entrypoint-initdb.d/ are executed in alphabetical order
# only when the data directory is empty (i.e., on the very first container start).
# Execution order: 01-schema → 02-seed_data → 03-seed_instruments → 04-migrations
COPY schema.sql              /docker-entrypoint-initdb.d/01-schema.sql
COPY seed_data.sql           /docker-entrypoint-initdb.d/02-seed_data.sql
COPY seed_instruments.sql    /docker-entrypoint-initdb.d/03-seed_instruments.sql
COPY migrations/add_instruments_table.sql  /docker-entrypoint-initdb.d/04-migration-add_instruments_table.sql
COPY migrations/add_switch_mode_column.sql /docker-entrypoint-initdb.d/05-migration-add_switch_mode_column.sql

# ── Expose standard MySQL port ───────────────────────────────────────────────
EXPOSE 3306
