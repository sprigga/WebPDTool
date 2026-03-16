from logging.config import fileConfig
import sys
import os

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import database configuration and models
# Modified: Use ASYNC_DATABASE_URL instead of DATABASE_URL (async-only migration)
from app.core.database import Base, ASYNC_DATABASE_URL

# For backwards compatibility with existing code
DATABASE_URL = ASYNC_DATABASE_URL
from app.models.user import User
from app.models.project import Project
from app.models.station import Station
from app.models.testplan import TestPlan
from app.models.test_result import TestResult
from app.models.test_session import TestSession
from app.models.sfc_log import SFCLog
from app.models.instrument import Instrument  # Added for instruments table support

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

def _resolve_alembic_database_url() -> str:
    """
    Resolve database URL for Alembic migrations.
    Converts asyncmy to pymysql for synchronous migration engine.
    """
    env_database_url = os.getenv("ALEMBIC_DATABASE_URL") or os.getenv("DATABASE_URL")
    if env_database_url:
        url = env_database_url
    else:
        url = DATABASE_URL

    # Convert mysql+asyncmy:// to mysql+pymysql:// for sync migrations
    # Alembic's run_migrations_online() uses a synchronous engine
    if url.startswith("mysql+asyncmy://"):
        return url.replace("mysql+asyncmy://", "mysql+pymysql://")
    return url


config.set_main_option("sqlalchemy.url", _resolve_alembic_database_url())

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# 使用我們的 Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
