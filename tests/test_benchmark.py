"""Real CPU benchmark evidence and deterministic statistical contracts."""

import csv
import io
import json

import pytest

from app.benchmarking.runner import csv_text, run_benchmark, save_report, summarize, validate_counts
from app.core.errors import SightLineError


def test_summary_nearest_rank_excludes_no_values_implicitly():
    values = [float(i) for i in range(1, 21)]
    result = summarize(values)
    assert result["median"] == 10.5
    assert result["p95"] == 19
    assert result["mean"] == 10.5
    assert result["count"] == 20
    assert result["stdev"] == pytest.approx(5.766281297)


@pytest.mark.parametrize("values", [[], [float("nan")], [float("inf")], [-1]])
def test_invalid_measurements_rejected(values):
    with pytest.raises(ValueError):
        summarize(values)


@pytest.mark.parametrize("samples,warmups", [(True, 1), (2, 1), (31, 1), (3, 0), (3, 6), (3, 1.5)])
def test_benchmark_request_limits(samples, warmups):
    with pytest.raises(SightLineError):
        validate_counts(samples, warmups)


def test_real_cpu_benchmark_artifacts_and_warmup_separation(tmp_path):
    report = run_benchmark(3, 1)
    assert report["runtime"]["active"] == "CPUExecutionProvider"
    assert report["runtime"]["npu_verified"] is False
    assert report["cold"]["timings_ms"]["initialization"] > 0
    assert len(report["runs"]) == 4
    measured = [
        row["timings_ms"]["inference"] for row in report["runs"] if row["phase"] == "measured"
    ]
    assert report["summary_ms"]["inference"] == summarize(measured)
    assert all(row["timings_ms"]["initialization"] is None for row in report["runs"])
    assert report["fps"] is None and report["memory_bytes"] is None
    assert "detections" not in json.dumps(report)
    names = save_report(report, tmp_path)
    assert json.loads((tmp_path / names["json"]).read_text()) == json.loads(json.dumps(report))
    rows = list(csv.DictReader(io.StringIO(csv_text(report))))
    assert [r["phase"] for r in rows] == ["cold", "warmup", "measured", "measured", "measured"]
    assert float(rows[2]["inference_ms"]) == measured[0]
    with pytest.raises(SightLineError, match="saved"):
        save_report(report, tmp_path)
    assert json.loads((tmp_path / names["json"]).read_text()) == json.loads(json.dumps(report))


def test_benchmark_failure_never_returns_measurements(monkeypatch):
    from app.benchmarking import runner

    def fail(*args):
        raise SightLineError("missing", "Model unavailable", 503)

    monkeypatch.setattr(runner.CPUEngine, "analyze", fail)
    with pytest.raises(SightLineError):
        run_benchmark(3, 1)
