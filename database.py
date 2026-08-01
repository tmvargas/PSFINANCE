import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base

INSTANCE_PATH = Path(os.getenv("PSFINANCE_INSTANCE_PATH", "instance"))
INSTANCE_PATH.mkdir(parents=True, exist_ok=True)

DATABASE_URL = (
    os.getenv("PSFINANCE_DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or f"sqlite:///{INSTANCE_PATH / 'financeiro.db'}"
)

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("PSFINANCE_SQL_ECHO", "false").lower() == "true",
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(engine)
