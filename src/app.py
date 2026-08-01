import os
import secrets
import time
import urllib.error
import urllib.request
from pathlib import Path

from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

from database import init_db
from financeiro import bp_financeiro


STARTED_AT = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
REPO_ROOT = Path(__file__).resolve().parent.parent
STAGING_BASE_PATH = os.getenv("PSFINANCE_STAGING_BASE_PATH", "/staging/psfinance").rstrip("/")


class PrefixMiddleware:
    def __init__(self, app, prefix):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if self.prefix and path.startswith(self.prefix):
            environ["SCRIPT_NAME"] = self.prefix
            environ["PATH_INFO"] = path[len(self.prefix):] or "/"
        return self.app(environ, start_response)


app = Flask(
    __name__,
    template_folder=str(REPO_ROOT / "templates"),
    instance_path=os.getenv("PSFINANCE_INSTANCE_PATH", str(REPO_ROOT / "instance")),
)
app.wsgi_app = ProxyFix(PrefixMiddleware(app.wsgi_app, STAGING_BASE_PATH), x_for=1, x_proto=1, x_host=1)
app.secret_key = os.getenv("PSFINANCE_SECRET_KEY") or os.getenv("SECRET_KEY") or secrets.token_hex(32)
app.config["UPLOAD_TITULOS_FOLDER"] = os.getenv(
    "PSFINANCE_UPLOAD_TITULOS_FOLDER",
    str(Path(app.instance_path) / "uploads" / "titulos"),
)
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("PSFINANCE_MAX_CONTENT_LENGTH", str(20 * 1024 * 1024)))
Path(app.config["UPLOAD_TITULOS_FOLDER"]).mkdir(parents=True, exist_ok=True)

init_db()
app.register_blueprint(bp_financeiro, url_prefix="/financeiro")


def app_metadata():
    return {
        "app": os.getenv("APP_NAME", "PSFINANCE"),
        "environment": os.getenv("APP_ENV", "staging"),
        "branch": os.getenv("GIT_BRANCH", "unknown"),
        "commit": os.getenv("GIT_COMMIT", "unknown"),
        "base_path": STAGING_BASE_PATH,
        "started_at": STARTED_AT,
    }


@app.get(STAGING_BASE_PATH)
@app.get(f"{STAGING_BASE_PATH}/")
@app.get("/")
def index():
    return app.view_functions["financeiro.dashboard_financeiro"]()


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
