"""Try a real verification run; strict failures return exit 2 and a JSON report."""

import argparse
import json
from pathlib import Path

from app.core.errors import SightLineError
from app.inference.model import ROOT
from app.inference.selection import QNNEngine
from app.system.status import runtime_status


def verify(
    strict: bool = True,
    model: Path | None = None,
    sha256: str | None = None,
    backend: Path | None = None,
) -> dict[str, object]:
    report = runtime_status("QNNExecutionProvider", strict)
    engine = QNNEngine(strict, model, sha256, backend)
    try:
        result = engine.analyze((ROOT / "assets/samples/astronaut.png").read_bytes(), "image/png")
        report["result"] = result
        report["provider"] = result["runtime"]
        runtime = result["runtime"]
        assert isinstance(runtime, dict)
        report["verification"] = "verified" if runtime.get("npu_verified") else "cpu_fallback"
    except SightLineError as exc:
        state = engine.snapshot()["provider_state"]
        current = report["provider"]
        assert isinstance(current, dict)
        report["provider"] = {**current, **(state if isinstance(state, dict) else {})}
        report["verification"] = "failed"
        report["error"] = {"code": exc.code, "message": str(exc)}
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Strict QNN/HTP verification with actual model execution"
    )
    parser.add_argument("--allow-cpu-fallback", action="store_true")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--sha256")
    parser.add_argument("--backend", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/evidence/qnn-verification.json")
    args = parser.parse_args()
    report = verify(not args.allow_cpu_fallback, args.model, args.sha256, args.backend)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    provider = report["provider"]
    assert isinstance(provider, dict)
    print(f"Verification: {report['verification']}")
    print(f"Requested: {provider.get('requested')} | Active: {provider.get('active')}")
    print(provider.get("npu"))
    print(f"JSON report: {args.output}")
    if report["verification"] == "failed":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
