"""Local CPU development host with bounded image requests and allowlisted assets."""

import argparse
import json
import logging
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from app.benchmarking.runner import RESULTS, run_benchmark, save_report, validate_counts
from app.core.errors import SightLineError
from app.inference.engine import CPUEngine
from app.inference.preprocess import MAX_BYTES
from app.inference.selection import QNNEngine
from app.system.status import runtime_status

ROOT = Path(__file__).resolve().parents[2]
ASSETS = {
    "/": ("ui/index.html", "text/html; charset=utf-8"),
    "/styles/tokens.css": ("ui/styles/tokens.css", "text/css; charset=utf-8"),
    "/styles/app.css": ("ui/styles/app.css", "text/css; charset=utf-8"),
    "/app.js": ("ui/app.js", "text/javascript; charset=utf-8"),
    "/pages/visual.js": ("ui/pages/visual.js", "text/javascript; charset=utf-8"),
    "/pages/privacy.js": ("ui/pages/privacy.js", "text/javascript; charset=utf-8"),
    "/lib/privacy.js": ("ui/lib/privacy.js", "text/javascript; charset=utf-8"),
    "/lib/clipboard.js": ("ui/lib/clipboard.js", "text/javascript; charset=utf-8"),
    "/pages/performance.js": ("ui/pages/performance.js", "text/javascript; charset=utf-8"),
    "/lib/view.js": ("ui/lib/view.js", "text/javascript; charset=utf-8"),
    "/lib/files.js": ("ui/lib/files.js", "text/javascript; charset=utf-8"),
    "/lib/results.js": ("ui/lib/results.js", "text/javascript; charset=utf-8"),
    "/samples/astronaut.png": ("assets/samples/astronaut.png", "image/png"),
}
LOG = logging.getLogger("sightline")
ENGINE = CPUEngine()
ENGINES: dict[str, CPUEngine | QNNEngine] = {
    "cpu": ENGINE,
    "qnn": QNNEngine(),
    "qnn-strict": QNNEngine(strict=True),
}
DEFAULT_MODE = "cpu"
LAST_MODE = "cpu"
ANALYSIS_GATE = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    server: ThreadingHTTPServer
    server_version = "SightLineDev/0.4"
    sys_version = ""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, format: str, *args: object) -> None:
        # Deliberately omit user-controlled URLs, filenames and request payloads.
        return

    def respond(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; script-src 'self'; style-src 'self'; "
            "img-src 'self' blob:; connect-src 'self'; font-src 'self'; "
            "base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
        )
        try:
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionError, OSError):
            LOG.info('{"event":"client_disconnected"}')

    def allowed_request(self) -> bool:
        expected_host = f"127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host") != expected_host:
            self.respond(403, b"Host not allowed", "text/plain")
            return False
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{expected_host}":
            self.respond(403, b"Origin not allowed", "text/plain")
            return False
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            self.respond(403, b"Cross-site request denied", "text/plain")
            return False
        return True

    def do_GET(self) -> None:
        if not self.allowed_request():
            return
        path = urlsplit(self.path).path
        if path == "/api/status":
            mode = LAST_MODE
            data = runtime_status(
                "CPUExecutionProvider" if mode == "cpu" else "QNNExecutionProvider",
                mode == "qnn-strict",
            )
            model = ENGINES[mode].snapshot()
            data["model"] = model
            observed = model.get("provider_state") or model.get("last_successful_runtime")
            if isinstance(observed, dict):
                current = data["provider"]
                assert isinstance(current, dict)
                data["provider"] = {**current, **observed}
            self.respond(200, json.dumps(data).encode(), "application/json")
            return
        match = re.fullmatch(r"/api/benchmarks/([0-9a-f]{32})\.(json|csv)", path)
        if match:
            filename = f"{match[1]}.{match[2]}"
            try:
                artifact = RESULTS / filename
                if (
                    artifact.resolve().parent != RESULTS.resolve()
                    or artifact.stat().st_size > 5_000_000
                ):
                    raise OSError()
                body = artifact.read_bytes()
            except OSError:
                self.respond(404, b"Benchmark not found", "text/plain")
                return
            self.respond(200, body, "application/json" if match[2] == "json" else "text/csv")
            return
        asset = ASSETS.get(path)
        if asset is None:
            self.respond(404, b"Not found", "text/plain")
            return
        filename, content_type = asset
        try:
            body = (ROOT / filename).read_bytes()
        except OSError:
            LOG.error('{"event":"asset_read_failed"}')
            self.respond(503, b"Application asset unavailable", "text/plain")
            return
        self.respond(200, body, content_type)

    def do_POST(self) -> None:
        global LAST_MODE
        self.close_connection = True
        if not self.allowed_request():
            return
        if urlsplit(self.path).path == "/api/benchmark":
            self.benchmark_request()
            return
        if urlsplit(self.path).path != "/api/analyze":
            self.respond(405, b"Unsupported operation", "text/plain")
            return
        # Custom header prevents simple cross-origin form/image requests.
        if self.headers.get("X-SightLine-Request") != "1":
            self.error_json(SightLineError("request_header", "Missing local request header.", 403))
            return
        if not ANALYSIS_GATE.acquire(blocking=False):
            self.error_json(
                SightLineError("busy", "An analysis is already running. Try again shortly.", 409)
            )
            return
        try:
            mode = self.headers.get("X-SightLine-Provider", DEFAULT_MODE)
            if mode not in ENGINES:
                raise SightLineError(
                    "provider_policy", "Choose CPU, QNN fallback, or strict QNN.", 400
                )
            lengths = self.headers.get_all("Content-Length", [])
            if (
                self.headers.get("Transfer-Encoding")
                or len(lengths) != 1
                or not lengths[0].isdigit()
            ):
                raise SightLineError("request_length", "Provide one valid Content-Length.", 411)
            length = int(lengths[0])
            if not 0 < length <= MAX_BYTES:
                raise SightLineError(
                    "image_size", "Choose a nonempty image no larger than 10 MB.", 413
                )
            mime = self.headers.get("Content-Type", "")
            if mime not in ("image/png", "image/jpeg"):
                raise SightLineError("image_type", "Only PNG and JPEG images are supported.", 415)
            try:
                content = self.rfile.read(length)
            except OSError as exc:
                raise SightLineError(
                    "request_timeout", "Image transfer timed out. Please retry.", 408
                ) from exc
            if len(content) != length:
                raise SightLineError("request_incomplete", "Image transfer was incomplete.", 400)
            LAST_MODE = mode
            result = ENGINES[mode].analyze(content, mime)
            self.respond(200, json.dumps(result, allow_nan=False).encode(), "application/json")
        except SightLineError as exc:
            self.error_json(exc)
        except Exception:
            LOG.error('{"event":"analysis_request_failed"}')
            self.error_json(
                SightLineError("internal_error", "Analysis could not finish. Please retry.", 500)
            )
        finally:
            ANALYSIS_GATE.release()

    def benchmark_request(self) -> None:
        if self.headers.get("X-SightLine-Request") != "1":
            self.error_json(SightLineError("request_header", "Missing local request header.", 403))
            return
        if not ANALYSIS_GATE.acquire(blocking=False):
            self.error_json(SightLineError("busy", "Local analysis or benchmark is running.", 409))
            return
        try:
            lengths = self.headers.get_all("Content-Length", [])
            if (
                self.headers.get("Transfer-Encoding")
                or len(lengths) != 1
                or not lengths[0].isdigit()
            ):
                raise SightLineError("request_length", "Provide one valid Content-Length.", 411)
            length = int(lengths[0])
            if not 0 < length <= 256:
                raise SightLineError(
                    "request_size", "Benchmark options exceed the request limit.", 413
                )
            if self.headers.get("Content-Type") != "application/json":
                raise SightLineError("request_type", "Benchmark options require JSON.", 415)
            content = self.rfile.read(length)
            if len(content) != length:
                raise SightLineError("request_incomplete", "Incomplete benchmark request.", 400)
            try:
                options = json.loads(content)
            except (ValueError, UnicodeError) as exc:
                raise SightLineError("request_json", "Invalid benchmark JSON.", 400) from exc
            if not isinstance(options, dict) or set(options) != {"samples", "warmups"}:
                raise SightLineError("benchmark_options", "Provide samples and warmups only.", 400)
            samples, warmups = validate_counts(options["samples"], options["warmups"])
            report = run_benchmark(samples, warmups)
            artifacts = save_report(report, RESULTS)
            response = {"report": report, "artifacts": artifacts}
            self.respond(200, json.dumps(response, allow_nan=False).encode(), "application/json")
        except SightLineError as exc:
            self.error_json(exc)
        except Exception:
            LOG.error('{"event":"benchmark_failed"}')
            self.error_json(SightLineError("benchmark_failed", "Benchmark could not finish.", 503))
        finally:
            ANALYSIS_GATE.release()

    def error_json(self, error: SightLineError) -> None:
        data = {"error": {"code": error.code, "message": str(error)}}
        self.respond(error.status, json.dumps(data).encode(), "application/json")


def main() -> None:
    global DEFAULT_MODE, LAST_MODE
    parser = argparse.ArgumentParser(description="SightLine local development shell")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--provider", choices=("cpu", "qnn", "qnn-strict"), default="cpu")
    parser.add_argument("--qnn-model", type=Path)
    parser.add_argument("--qnn-sha256")
    parser.add_argument("--qnn-backend", type=Path)
    args = parser.parse_args()
    DEFAULT_MODE = LAST_MODE = args.provider
    for mode in ("qnn", "qnn-strict"):
        ENGINES[mode] = QNNEngine(
            mode == "qnn-strict", args.qnn_model, args.qnn_sha256, args.qnn_backend
        )
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    LOG.info(json.dumps({"event": "server_started", "port": server.server_port}))
    print(f"SightLine AI: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
