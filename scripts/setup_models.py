"""Explicit model download with pinned size/hash and atomic installation."""

import hashlib
import tempfile
import urllib.request
from pathlib import Path

from app.inference.model import (
    MODEL_BYTES,
    MODEL_PATH,
    MODEL_SHA256,
    MODEL_URL,
    verified_model_bytes,
)


def install_model() -> Path:
    if MODEL_PATH.exists():
        verified_model_bytes()
        return MODEL_PATH
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        request = urllib.request.Request(MODEL_URL, headers={"User-Agent": "SightLine-setup/0.2"})
        with urllib.request.urlopen(request, timeout=60) as response:
            if not response.url.startswith("https://"):
                raise ValueError("Model download must use HTTPS")
            content = response.read(MODEL_BYTES + 1)
        if len(content) != MODEL_BYTES or hashlib.sha256(content).hexdigest() != MODEL_SHA256:
            raise ValueError("Downloaded model failed its pinned size/SHA-256 check")
        with tempfile.NamedTemporaryFile(
            dir=MODEL_PATH.parent, suffix=".part", delete=False
        ) as file:
            temporary = Path(file.name)
            file.write(content)
        temporary.replace(MODEL_PATH)
        return MODEL_PATH
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> None:
    try:
        print(f"Verified YOLOX-Nano: {install_model()}")
    except Exception:
        raise SystemExit(
            "Model setup failed. Check connectivity or remove the corrupt weights file and retry."
        ) from None


if __name__ == "__main__":
    main()
