"""Report observed runtime facts; performs no model inference."""

import argparse
import json
from pathlib import Path

from app.system.status import runtime_status


def main() -> None:
    parser = argparse.ArgumentParser(description="Observe environment without executing a model")
    parser.add_argument("--provider", choices=("cpu", "qnn"), default="qnn")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = runtime_status(
        "CPUExecutionProvider" if args.provider == "cpu" else "QNNExecutionProvider", args.strict
    )
    text = json.dumps(data, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
