import os
import time
import urllib.error
import urllib.request

from flask import Flask, jsonify, render_template_string


app = Flask(__name__)
STARTED_AT = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
STAGING_BASE_PATH = os.getenv("PSFINANCE_STAGING_BASE_PATH", "/staging/psfinance")


def app_metadata():
    return {
        "app": os.getenv("APP_NAME", "PSFINANCE"),
        "environment": os.getenv("APP_ENV", "staging"),
        "branch": os.getenv("GIT_BRANCH", "unknown"),
        "commit": os.getenv("GIT_COMMIT", "unknown"),
        "base_path": STAGING_BASE_PATH,
        "started_at": STARTED_AT,
    }


INDEX_TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PSFINANCE - Homologacao</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Arial, Helvetica, sans-serif;
      color: #20262e;
      background: #f4f6f8;
    }

    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
    }

    main {
      width: min(760px, calc(100% - 32px));
      padding: 32px;
      border: 1px solid #d9e0e8;
      border-radius: 8px;
      background: #ffffff;
      box-shadow: 0 12px 36px rgba(24, 35, 48, 0.08);
    }

    h1 {
      margin: 0 0 8px;
      font-size: 32px;
      line-height: 1.15;
    }

    p {
      margin: 0 0 20px;
      line-height: 1.5;
      color: #4a5563;
    }

    dl {
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: 10px 18px;
      margin: 0;
    }

    dt {
      font-weight: 700;
      color: #2f3a45;
    }

    dd {
      margin: 0;
      overflow-wrap: anywhere;
    }
  </style>
</head>
<body>
  <main>
    <h1>PSFINANCE</h1>
    <p>Ambiente de homologacao ativo.</p>
    <dl>
      <dt>Status</dt>
      <dd>ok</dd>
      <dt>Ambiente</dt>
      <dd>{{ metadata.environment }}</dd>
      <dt>Branch</dt>
      <dd>{{ metadata.branch }}</dd>
      <dt>Commit</dt>
      <dd>{{ metadata.commit }}</dd>
      <dt>Base</dt>
      <dd>{{ metadata.base_path }}</dd>
    </dl>
  </main>
</body>
</html>"""


@app.get(STAGING_BASE_PATH)
@app.get(f"{STAGING_BASE_PATH}/")
@app.get("/")
def index():
    return render_template_string(INDEX_TEMPLATE, metadata=app_metadata())


@app.get(f"{STAGING_BASE_PATH}/health")
@app.get("/health")
def health():
    return jsonify({**app_metadata(), "status": "healthy"})


@app.get(f"{STAGING_BASE_PATH}/gate")
@app.get("/gate")
def gate():
    target_url = os.getenv("PSFINANCE_STAGING_HEALTH_URL")
    result = {**app_metadata(), "status": "healthy", "checks": {}}

    if target_url:
        try:
            with urllib.request.urlopen(target_url, timeout=5) as response:
                result["checks"]["psfinance_staging"] = {
                    "url": target_url,
                    "http_status": response.status,
                    "ok": 200 <= response.status < 300,
                }
        except (urllib.error.URLError, TimeoutError) as exc:
            result["status"] = "unhealthy"
            result["checks"]["psfinance_staging"] = {
                "url": target_url,
                "ok": False,
                "error": exc.__class__.__name__,
            }

    http_status = 200 if result["status"] == "healthy" else 503
    return jsonify(result), http_status


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(host="127.0.0.1", port=port)
