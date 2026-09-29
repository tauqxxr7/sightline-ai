"""Run a real CPU benchmark and save JSON/CSV evidence."""

import argparse
import json

from app.benchmarking.runner import RESULTS, run_benchmark, save_report
from app.core.errors import SightLineError


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--warmups", type=int, default=2)
    args = parser.parse_args()
    try:
        report = run_benchmark(args.samples, args.warmups)
        names = save_report(report)
    except SightLineError as exc:
        parser.exit(2, f"{exc}\n")
    print(
        json.dumps(
            {
                "artifacts": {key: str(RESULTS / value) for key, value in names.items()},
                "inference_ms": report["summary_ms"]["inference"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
