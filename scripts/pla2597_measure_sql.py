import json
import os
import re
import time
from collections import Counter

from sqlalchemy import event, text

from database import engine


measurements = []


@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(_conn, _cursor, _statement, _parameters, context, _executemany):
    context._pla2597_started_at = time.perf_counter()


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(_conn, _cursor, statement, _parameters, context, _executemany):
    normalized = " ".join(statement.split())
    measurements.append({
        "elapsed_ms": round((time.perf_counter() - context._pla2597_started_at) * 1000, 3),
        "operation": normalized.split(" ", 1)[0].upper(),
        "tables": sorted(set(re.findall(r"(?:FROM|JOIN)\s+([a-zA-Z0-9_]+)", normalized, re.IGNORECASE))),
    })


with engine.connect() as connection:
    read_only = connection.execute(text("SHOW default_transaction_read_only")).scalar_one()

from src.app import app  # noqa: E402

measurements.clear()
started_at = time.perf_counter()
response = app.test_client().get(
    "/staging/psfinance/financeiro/extrato",
    query_string={
        "id_empresa": 1,
        "id_conta": 14,
        "data_ini": "2026-08-01",
        "data_fim": "2026-08-16",
    },
)
elapsed_ms = (time.perf_counter() - started_at) * 1000
table_groups = Counter(
    ",".join(item["tables"]) or "sem_tabela_identificada" for item in measurements
)
result = {
    "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "default_transaction_read_only": read_only,
    "http_status": response.status_code,
    "response_bytes": len(response.data),
    "route_elapsed_ms": round(elapsed_ms, 3),
    "sql_query_count": len(measurements),
    "sql_total_ms": round(sum(item["elapsed_ms"] for item in measurements), 3),
    "sql_max_ms": round(max((item["elapsed_ms"] for item in measurements), default=0), 3),
    "operations": dict(Counter(item["operation"] for item in measurements)),
    "query_groups": dict(table_groups),
    "queries": measurements,
}
output_path = os.environ.get("PLA2597_SQL_OUTPUT")
payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
if output_path:
    with open(output_path, "w", encoding="utf-8") as output:
        output.write(payload)
else:
    print(payload)
