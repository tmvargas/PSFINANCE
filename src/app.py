import os
import time
import urllib.error
import urllib.request

from flask import Flask, jsonify


app = Flask(__name__)
STARTED_AT = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def app_metadata():
    return {
        "app": os.getenv("APP_NAME", "PSFINANCE"),
        "environment": os.getenv("APP_ENV", "staging"),
        "branch": os.getenv("GIT_BRANCH", "unknown"),
        "commit": os.getenv("GIT_COMMIT", "unknown"),
        "started_at": STARTED_AT,
    }


@app.get("/")
def index():
    return jsonify({**app_metadata(), "status": "ok"})


@app.get("/health")
def health():
    return jsonify({**app_metadata(), "status": "healthy"})


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
