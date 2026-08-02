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

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("PSFINANCE_SQL_ECHO", "false").lower() == "true",
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(engine)


def database_metadata():
    return {
        "db_dialect": engine.dialect.name,
        "database_url_source": DATABASE_URL_SOURCE,
    }
