"""Bounded CPU benchmarks, with fresh-session cold and separate warm samples."""

import csv
import hashlib
import io
import json
import logging
import math
import statistics
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from app.core.errors import SightLineError
from app.inference.engine import CPUEngine
from app.inference.model import ROOT
from app.system.status import runtime_status

RESULTS = ROOT / "benchmarks/results"
STAGES = ("preprocessing", "inference", "postprocessing", "total_pipeline")
LOG = logging.getLogger("sightline")


def summarize(values: list[float]) -> dict[str, float | int]:
    if not values or any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Expected nonempty, finite, nonnegative measurements")
    ordered = sorted(values)
    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "p95": ordered[math.ceil(0.95 * len(ordered)) - 1],
        "stdev": statistics.pstdev(values),
        "min": ordered[0],
        "max": ordered[-1],
    }


def validate_counts(samples: object, warmups: object) -> tuple[int, int]:
    if type(samples) is not int or not 3 <= samples <= 30:
        raise SightLineError("benchmark_samples", "Choose 3 to 30 measured samples.", 400)
    if type(warmups) is not int or not 1 <= warmups <= 5:
        raise SightLineError("benchmark_warmups", "Choose 1 to 5 warmup runs.", 400)
    return samples, warmups


def run_benchmark(samples: int = 10, warmups: int = 2) -> dict[str, Any]:
    samples, warmups = validate_counts(samples, warmups)
    environment = runtime_status("CPUExecutionProvider")
    content = (ROOT / "assets/samples/astronaut.png").read_bytes()
    engine = CPUEngine()  # Fresh session, independent of prior UI analyses.
    started = perf_counter()
    cold = engine.analyze(content, "image/png")
    records: list[dict[str, Any]] = []
    for phase, count in (("warmup", warmups), ("measured", samples)):
        for index in range(count):
            if perf_counter() - started > 120:
                raise SightLineError(
                    "benchmark_timeout", "Benchmark exceeded its time budget.", 503
                )
            result = engine.analyze(content, "image/png")
            runtime = result["runtime"]
            timings = result["timings_ms"]
            if not isinstance(runtime, dict) or runtime.get("active") != "CPUExecutionProvider":
                raise SightLineError("benchmark_provider", "Unexpected execution provider.", 503)
            if not isinstance(timings, dict) or result.get("run_kind") != "warm":
                raise SightLineError("benchmark_session", "Warm session was not preserved.", 503)
            records.append({"phase": phase, "index": index + 1, "timings_ms": timings})
    measured = [row for row in records if row["phase"] == "measured"]
    summary = {
        stage: summarize([float(row["timings_ms"][stage]) for row in measured]) for stage in STAGES
    }
    report = {
        "schema_version": 1,
        "kind": "measured_cpu_benchmark",
        "id": uuid4().hex,
        "observed_at": datetime.now(UTC).isoformat(),
        "environment": environment,
        "model": cold["model"],
        "runtime": cold["runtime"],
        "input": {
            "fixture": "NASA astronaut PNG",
            "sha256": hashlib.sha256(content).hexdigest(),
            "dimensions": cold["image"],
        },
        "configuration": {
            "samples": samples,
            "warmups": warmups,
            "intra_op_threads": 2,
            "inter_op_threads": 1,
            "percentile_method": "nearest rank",
            "stdev_method": "population",
        },
        "cold": {
            "timings_ms": cold["timings_ms"],
            "scope": "Fresh ORT session; not process/OS cold",
        },
        "runs": records,
        "summary_ms": summary,
        "memory_bytes": None,
        "memory_note": "Not measured; Python heap is not process/native memory",
        "fps": None,
        "fps_note": "Static-image benchmark; no video FPS measured",
        "elapsed_ms": (perf_counter() - started) * 1000,
        "limitations": [
            "CPU baseline only; no QNN comparison",
            "One repeated image, not accuracy evaluation",
            "UI rendering and HTTP transfer excluded",
            "OS cache and thermal state uncontrolled",
        ],
    }
    LOG.info('{"event":"benchmark_completed","provider":"CPUExecutionProvider"}')
    return report


def csv_text(report: dict[str, Any]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["phase", "index", "initialization_ms", *[f"{s}_ms" for s in STAGES]])
    rows = [
        {"phase": "cold", "index": 1, "timings_ms": report["cold"]["timings_ms"]},
        *report["runs"],
    ]
    for row in rows:
        timings = row["timings_ms"]
        writer.writerow(
            [
                row["phase"],
                row["index"],
                timings.get("initialization"),
                *[timings[s] for s in STAGES],
            ]
        )
    return output.getvalue()


def save_report(report: dict[str, Any], directory: Path = RESULTS) -> dict[str, str]:
    # Names are generated locally, never accepted from an HTTP caller.
    identifier = str(report["id"])
    if len(identifier) != 32 or any(c not in "0123456789abcdef" for c in identifier):
        raise ValueError("Invalid benchmark identifier")
    directory.mkdir(parents=True, exist_ok=True)
    names = {"json": f"{identifier}.json", "csv": f"{identifier}.csv"}
    json_body = json.dumps(report, indent=2, allow_nan=False) + "\n"
    csv_body = csv_text(report)
    created: list[Path] = []
    try:
        for kind, body in (("json", json_body), ("csv", csv_body)):
            path = directory / names[kind]
            with path.open("x", encoding="utf-8", newline="") as output:
                created.append(path)
                output.write(body)
    except OSError as exc:
        for path in created:
            path.unlink(missing_ok=True)
        raise SightLineError(
            "benchmark_save", "Benchmark artifacts could not be saved.", 503
        ) from exc
    return names
