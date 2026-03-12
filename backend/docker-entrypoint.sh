#!/bin/bash
# =============================================================================
# WebPDTool Backend Docker Entrypoint
# =============================================================================
# This script runs Alembic migrations before starting the FastAPI application.
# It is designed to be safe for both initial deployments and subsequent updates.
#
# Environment Variables:
#   SKIP_MIGRATIONS    - Set to "true" to skip migration runs (default: false)
#   MIGRATION_TIMEOUT  - Maximum time to wait for DB connection (default: 60s)
#   ALEMBIC_ARGS       - Additional arguments to pass to alembic (default: "")
# =============================================================================

set -e  # Exit on error (but we handle migration failures gracefully)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration from environment variables
SKIP_MIGRATIONS="${SKIP_MIGRATIONS:-false}"
MIGRATION_TIMEOUT="${MIGRATION_TIMEOUT:-60}"
ALEMBIC_ARGS="${ALEMBIC_ARGS:-}"

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Function: Wait for database to be ready
# =============================================================================
wait_for_db() {
    local host="${DB_HOST:-db}"
    local port="${DB_PORT:-3306}"
    local timeout=$MIGRATION_TIMEOUT
    local count=0

    log_info "Waiting for database at ${host}:${port} to be ready..."

    while [ $count -lt $timeout ]; do
        if python -c "
import sys
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('${host}', ${port}))
    s.close()
    sys.exit(0)
except:
    sys.exit(1)
" 2>/dev/null; then
            log_info "Database is ready!"
            return 0
        fi
        count=$((count + 1))
        if [ $((count % 5)) -eq 0 ]; then
            log_warn "Still waiting for database... (${count}/${timeout}s)"
        fi
        sleep 1
    done

    log_error "Database connection timeout after ${timeout}s"
    return 1
}

# =============================================================================
# Function: Run Alembic migrations
# =============================================================================
run_migrations() {
    if [ "$SKIP_MIGRATIONS" = "true" ]; then
        log_warn "SKIP_MIGRATIONS=true, skipping database migrations"
        return 0
    fi

    log_info "Starting Alembic database migrations..."

    # Check current migration version
    log_info "Checking current migration version..."
    if ! uv run alembic current 2>/dev/null; then
        log_warn "No migration version found (first time setup)"
    fi

    # Show migration history for debugging
    log_info "Migration history:"
    uv run alembic history 2>&1 | head -n 5 || true

    # Run the migration
    log_info "Running 'alembic upgrade head'..."
    if uv run alembic upgrade head ${ALEMBIC_ARGS}; then
        log_info "✅ Migrations completed successfully!"

        # Show final version
        log_info "Current migration version:"
        uv run alembic current
    else
        log_error "❌ Migration failed!"
        log_error "The application will still start, but database schema may be incomplete."
        log_error "Check the migration logs above for details."
        log_error "You can also run migrations manually later:"
        log_error "  docker-compose exec backend uv run alembic upgrade head"
        # Don't exit - let the application start anyway
    fi
}

# =============================================================================
# Main execution
# =============================================================================
main() {
    log_info "=========================================="
    log_info "WebPDTool Backend Entrypoint"
    log_info "=========================================="

    # Wait for database
    if ! wait_for_db; then
        log_error "Failed to connect to database, but will attempt to start application..."
    fi

    # Run migrations
    run_migrations

    # Start the application
    log_info "Starting FastAPI application..."
    log_info "=========================================="

    # Execute the CMD passed to the container
    exec "$@"
}

# Run main function
main "$@"
