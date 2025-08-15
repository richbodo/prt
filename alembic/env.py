from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import event

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prt.models import Base
from prt.config import load_config, is_database_encrypted, get_encryption_key
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    """Get the database URL, handling encryption if needed."""
    try:
        prt_config = load_config()
        if is_database_encrypted(prt_config):
            # For encrypted databases, we need to handle the connection differently
            return prt_config.get('db_path', 'prt_data/prt.db')
        else:
            # Use the URL from alembic.ini for unencrypted databases
            return config.get_main_option("sqlalchemy.url")
    except Exception:
        # Fallback to alembic.ini URL
        return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
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
    try:
        prt_config = load_config()
        is_encrypted = is_database_encrypted(prt_config)
    except Exception:
        is_encrypted = False
    
    if is_encrypted:
        # Handle encrypted database
        db_path = prt_config.get('db_path', 'prt_data/prt.db')
        encryption_key = get_encryption_key()
        
        # Create engine configuration for encrypted database
        engine_config = {
            'sqlalchemy.url': f"sqlite:///{db_path}",
            'sqlalchemy.echo': 'false',
            'sqlalchemy.connect_args': '{"check_same_thread": false, "timeout": 30.0}'
        }
        
        connectable = engine_from_config(
            engine_config,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        
        # Set up encryption on connection
        @event.listens_for(connectable, "connect")
        def set_sqlcipher_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            # Set the encryption key
            cursor.execute(f"PRAGMA key = '{encryption_key}'")
            # Set SQLCipher compatibility mode (version 3)
            cursor.execute("PRAGMA cipher_compatibility = 3")
            # Set page size for better performance
            cursor.execute("PRAGMA page_size = 4096")
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()
    else:
        # Handle unencrypted database
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
