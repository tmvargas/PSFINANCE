import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base

INSTANCE_PATH = Path(os.getenv("PSFINANCE_INSTANCE_PATH", "instance"))
INSTANCE_PATH.mkdir(parents=True, exist_ok=True)

DATABASE_URL = (
    os.getenv("PSFINANCE_STAGING_DATABASE_URL")
    or os.getenv("PSFINANCE_DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or f"sqlite:///{INSTANCE_PATH / 'financeiro.db'}"
)

DATABASE_URL_SOURCE = next(
    (
        name
        for name in (
            "PSFINANCE_STAGING_DATABASE_URL",
            "PSFINANCE_DATABASE_URL",
            "DATABASE_URL",
        )
        if os.getenv(name)
    ),
    "sqlite_fallback",
)


def _positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


def engine_options(database_url: str) -> dict:
    options = {
        "echo": os.getenv("PSFINANCE_SQL_ECHO", "false").lower() == "true",
        "future": True,
        "pool_pre_ping": True,
    }
    if database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
        connect_timeout = _positive_int_env("PSFINANCE_DB_CONNECT_TIMEOUT", 5)
        statement_timeout = _positive_int_env("PSFINANCE_DB_STATEMENT_TIMEOUT_MS", 10000)
        lock_timeout = _positive_int_env("PSFINANCE_DB_LOCK_TIMEOUT_MS", 3000)
        options.update(
            {
                "pool_recycle": _positive_int_env("PSFINANCE_DB_POOL_RECYCLE_SECONDS", 300),
                "pool_timeout": _positive_int_env("PSFINANCE_DB_POOL_TIMEOUT_SECONDS", 5),
                "connect_args": {
                    "connect_timeout": connect_timeout,
                    "options": (
                        f"-c statement_timeout={statement_timeout} "
                        f"-c lock_timeout={lock_timeout}"
                    ),
                },
            }
        )
    return options


engine = create_engine(DATABASE_URL, **engine_options(DATABASE_URL))

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(engine)


def database_metadata():
    return {
        "db_dialect": engine.dialect.name,
        "database_url_source": DATABASE_URL_SOURCE,
    }
