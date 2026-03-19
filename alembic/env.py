from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import asyncio

from src.core.config import settings
from src.db.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

target_metadata = Base.metadata

# --- async run migrations ---
def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        url=settings.database_url,
        poolclass=pool.NullPool,
    )

    async def do_run_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(context.run_migrations)

    asyncio.run(do_run_migrations())

run_migrations_online()
