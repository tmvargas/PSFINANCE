#!/usr/bin/env python3
"""Migra dados do SQLite operacional do PSFINANCE para PostgreSQL staging."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Numeric
from sqlalchemy import create_engine, delete, func, insert, select
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from models import Base  # noqa: E402


TABLE_ORDER = [
    "documento",
    "plano_de_contas",
    "credor",
    "conta",
    "titulo",
    "titulo_anexo",
    "baixa",
    "movimentacao_conta",
]

SEQUENCE_TABLES = {
    "documento": "id_doc",
    "plano_de_contas": "id_plano",
    "credor": "id_credor",
    "conta": "id_conta",
    "titulo": "id_titulo",
    "titulo_anexo": "id_anexo",
    "baixa": "id_baixa",
    "movimentacao_conta": "id_movimentacao",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copia dados do SQLite do PSFINANCE para um PostgreSQL vazio de staging."
    )
    parser.add_argument(
        "--sqlite-url",
        default=os.getenv(
            "PSFINANCE_SQLITE_DATABASE_URL",
            f"sqlite:///{ROOT / 'instance' / 'financeiro.db'}",
        ),
        help="URL SQLAlchemy de origem SQLite.",
    )
    parser.add_argument(
        "--postgres-url",
        default=os.getenv("PSFINANCE_STAGING_DATABASE_URL") or os.getenv("PSFINANCE_DATABASE_URL"),
        help="URL SQLAlchemy de destino PostgreSQL staging.",
    )
    parser.add_argument(
        "--truncate-target",
        action="store_true",
        help="Limpa as tabelas de destino antes de copiar. Use somente apos backup validado.",
    )
    return parser.parse_args()


def make_engine(url: str) -> Engine:
    return create_engine(url, future=True, pool_pre_ping=True)


def assert_urls(sqlite_url: str | None, postgres_url: str | None) -> None:
    if not sqlite_url:
        raise SystemExit("Informe --sqlite-url ou PSFINANCE_SQLITE_DATABASE_URL.")
    if not postgres_url:
        raise SystemExit("Informe --postgres-url ou PSFINANCE_STAGING_DATABASE_URL.")
    if not sqlite_url.startswith("sqlite:///"):
        raise SystemExit("A origem deve ser SQLite.")
    if not postgres_url.startswith(
        ("postgresql://", "postgresql+psycopg2://", "postgresql+psycopg://")
    ):
        raise SystemExit("O destino deve ser PostgreSQL.")


def normalize_value(value: Any, column: Any) -> Any:
    if value is None:
        if column.name in {"created_at", "updated_at"}:
            return datetime.now(timezone.utc).replace(tzinfo=None)
        if column.name in {"deleted", "conciliado"}:
            return False
        return None

    if isinstance(column.type, Boolean):
        return bool(value)
    if isinstance(column.type, DateTime) and isinstance(value, str):
        raw = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(raw)
        return parsed.replace(tzinfo=None)
    if isinstance(column.type, Date) and not isinstance(column.type, DateTime) and isinstance(value, str):
        return date.fromisoformat(value.split(" ")[0])
    if isinstance(column.type, Numeric) and not isinstance(value, Decimal):
        return Decimal(str(value))
    return value


def fetch_rows(source: Engine, table_name: str) -> list[dict[str, Any]]:
    table = Base.metadata.tables[table_name]
    with source.connect() as conn:
        rows = conn.execute(select(table)).mappings().all()
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {column.name: normalize_value(row.get(column.name), column) for column in table.columns}
        )
    return normalized


def assert_target_empty(target: Engine) -> None:
    with target.connect() as conn:
        non_empty = []
        for table_name in TABLE_ORDER:
            table = Base.metadata.tables[table_name]
            count = conn.execute(select(func.count()).select_from(table)).scalar_one()
            if count:
                non_empty.append(f"{table_name}={count}")
    if non_empty:
        raise SystemExit(
            "Destino PostgreSQL nao esta vazio. Execute backup e use --truncate-target se a substituicao for autorizada: "
            + ", ".join(non_empty)
        )


def reset_sequences(target: Engine) -> None:
    with target.begin() as conn:
        for table_name, pk_column in SEQUENCE_TABLES.items():
            conn.exec_driver_sql(
                "SELECT setval(pg_get_serial_sequence(%s, %s), "
                f"COALESCE((SELECT MAX({pk_column}) FROM {table_name}), 1), "
                f"COALESCE((SELECT MAX({pk_column}) FROM {table_name}), 0) > 0)",
                (table_name, pk_column),
            )


def migrate(sqlite_url: str, postgres_url: str, truncate_target: bool) -> None:
    source = make_engine(sqlite_url)
    target = make_engine(postgres_url)

    Base.metadata.create_all(target)
    if truncate_target:
        with target.begin() as conn:
            for table_name in reversed(TABLE_ORDER):
                conn.execute(delete(Base.metadata.tables[table_name]))
    else:
        assert_target_empty(target)

    copied: dict[str, int] = {}
    with target.begin() as conn:
        for table_name in TABLE_ORDER:
            table = Base.metadata.tables[table_name]
            rows = fetch_rows(source, table_name)
            if rows:
                conn.execute(insert(table), rows)
            copied[table_name] = len(rows)

    reset_sequences(target)

    print("Migracao concluida para PostgreSQL staging.")
    for table_name in TABLE_ORDER:
        print(f"{table_name}: {copied[table_name]}")


def main() -> None:
    args = parse_args()
    assert_urls(args.sqlite_url, args.postgres_url)
    migrate(args.sqlite_url, args.postgres_url, args.truncate_target)


if __name__ == "__main__":
    main()
