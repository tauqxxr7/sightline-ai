import http.client
import json
import threading
from http.server import ThreadingHTTPServer

import pytest

from app.core.server import Handler


@pytest.fixture
def server():
    instance = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    yield instance
    instance.shutdown()
    instance.server_close()
    thread.join(timeout=2)


def request(server, path="/", method="GET", headers=None, body=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
    connection.request(method, path, headers=headers or {}, body=body)
    response = connection.getresponse()
    result = response.status, dict(response.getheaders()), response.read()
    connection.close()
    return result


def test_shell_served_with_security_headers(server):
    status, headers, body = request(server)
    assert status == 200
    assert b"SightLine" in body
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert headers["Cache-Control"] == "no-store"
    assert "Access-Control-Allow-Origin" not in headers


@pytest.mark.parametrize(
    "path",
    ["/../AGENTS.md", "/%2e%2e/.env", "/models/manifest.json", "/app/core/server.py", "/unknown"],
)
def test_only_allowlisted_assets_are_readable(server, path):
    assert request(server, path)[0] == 404


def test_cross_origin_denied(server):
    assert request(server, "/api/status", headers={"Origin": "https://example.com"})[0] == 403


def test_dns_rebinding_host_denied(server):
    assert request(server, headers={"Host": "attacker.example"})[0] == 403


def test_cross_site_denied(server):
    assert request(server, headers={"Sec-Fetch-Site": "cross-site"})[0] == 403


def test_no_upload_endpoint(server):
    assert request(server, "/api/upload", method="POST")[0] == 405


def test_status_schema_and_absence_of_measurements(server):
    code, _, data = request(server, "/api/status")
    parsed = json.loads(data)
    assert code == 200
    assert parsed["schema_version"] == 1
    assert parsed["provider"]["active"] in (None, "CPUExecutionProvider")
    assert parsed["measurements"] is None


def test_real_analysis_http(server):
    from pathlib import Path

    content = (Path(__file__).resolve().parents[1] / "assets/samples/astronaut.png").read_bytes()
    status, _, body = request(
        server,
        "/api/analyze",
        "POST",
        {"X-SightLine-Request": "1", "Content-Type": "image/png"},
        content,
    )
    data = json.loads(body)
    assert status == 200
    assert data["runtime"]["active"] == "CPUExecutionProvider"
    assert any(d["label"] == "person" for d in data["detections"])


@pytest.mark.parametrize(
    "headers,body,expected",
    [
        ({"Content-Type": "image/png"}, b"fake", 403),
        ({"X-SightLine-Request": "1", "Content-Type": "text/plain"}, b"fake", 415),
        ({"X-SightLine-Request": "1", "Content-Type": "image/png"}, b"fake", 422),
        (
            {"X-SightLine-Request": "1", "Content-Type": "image/png", "Content-Length": "10485761"},
            None,
            413,
        ),
        (
            {"X-SightLine-Request": "1", "Content-Type": "image/png", "Content-Length": "-1"},
            None,
            411,
        ),
        (
            {
                "X-SightLine-Request": "1",
                "Content-Type": "image/png",
                "Origin": "https://evil.invalid",
            },
            b"fake",
            403,
        ),
    ],
)
def test_analysis_validation(server, headers, body, expected):
    status, _, response = request(server, "/api/analyze", "POST", headers, body)
    assert status == expected
    assert b"Traceback" not in response


@pytest.mark.parametrize("mode,expected", [("qnn", 200), ("qnn-strict", 503), ("bogus", 400)])
def test_http_provider_policy(server, monkeypatch, mode, expected):
    from pathlib import Path

    from app.core import server as module
    from app.core.errors import SightLineError
    from app.inference.selection import QNNEngine

    engine = QNNEngine(strict=mode == "qnn-strict")

    def unavailable(tensor):
        raise SightLineError("qnn_unavailable", "Unavailable in fixture", 503)

    monkeypatch.setattr(engine.qnn, "run", unavailable)
    if mode != "bogus":
        monkeypatch.setitem(module.ENGINES, mode, engine)
    monkeypatch.setattr(module, "LAST_MODE", "cpu")
    content = (Path(__file__).resolve().parents[1] / "assets/samples/astronaut.png").read_bytes()
    if mode == "bogus":
        content = b"invalid-policy-fixture"
    status, _, body = request(
        server,
        "/api/analyze",
        "POST",
        {"X-SightLine-Request": "1", "X-SightLine-Provider": mode, "Content-Type": "image/png"},
        content,
    )
    assert status == expected
    data = json.loads(body)
    if mode == "qnn":
        assert data["runtime"]["active"] == "CPUExecutionProvider"
        assert data["runtime"]["fallback"] == "cpu"
    elif mode == "qnn-strict":
        _, _, report = request(server, "/api/status")
        provider = json.loads(report)["provider"]
        assert provider["active"] is None
        assert provider["fallback"] == "forbidden"
        assert provider["npu_verified"] is False


@pytest.mark.parametrize(
    "body,status",
    [
        (b'{"samples":2,"warmups":1}', 400),
        (b'{"samples":true,"warmups":1}', 400),
        (b'{"samples":3,"warmups":1,"path":"../secret"}', 400),
        (b"[]", 400),
        (b"broken", 400),
        (b"x" * 257, 413),
    ],
)
def test_benchmark_validation(server, body, status):
    assert (
        request(
            server,
            "/api/benchmark",
            "POST",
            {"Content-Type": "application/json", "X-SightLine-Request": "1"},
            body,
        )[0]
        == status
    )


def test_real_benchmark_http_and_saved_artifacts(server, monkeypatch, tmp_path):
    from app.core import server as module

    monkeypatch.setattr(module, "RESULTS", tmp_path)
    code, _, body = request(
        server,
        "/api/benchmark",
        "POST",
        {"Content-Type": "application/json", "X-SightLine-Request": "1"},
        b'{"samples":3,"warmups":1}',
    )
    assert code == 200
    data = json.loads(body)
    assert data["report"]["summary_ms"]["inference"]["count"] == 3
    for filename in data["artifacts"].values():
        code, _, saved = request(server, "/api/benchmarks/" + filename)
        assert code == 200
        assert saved == (tmp_path / filename).read_bytes()
    assert request(server, "/api/benchmarks/../README.md")[0] == 404


def test_benchmark_and_analysis_share_concurrency_guard(server):
    from app.core import server as module

    with module.ANALYSIS_GATE:
        assert (
            request(
                server,
                "/api/benchmark",
                "POST",
                {"Content-Type": "application/json", "X-SightLine-Request": "1"},
                b"{}",
            )[0]
            == 409
        )
