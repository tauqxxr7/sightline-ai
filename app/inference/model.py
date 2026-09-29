"""Pinned artifact contract; no network access in the inference path."""

import hashlib
from pathlib import Path

from app.core.errors import SightLineError

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models/weights/yolox_nano.onnx"
MODEL_SHA256 = "c789161ed43c8269fcd4e67c67eeeb4e80c622da2eb296a20bc6007bd18a0b7d"
MODEL_BYTES = 3659407
MODEL_URL = (
    "https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_nano.onnx"
)
MODEL_VERSION = "0.1.1rc0"
INPUT_SHAPE = (1, 3, 416, 416)
OUTPUT_SHAPE = (1, 3549, 85)


def verified_model_bytes(path: Path = MODEL_PATH) -> bytes:
    try:
        if path.stat().st_size != MODEL_BYTES:
            raise SightLineError(
                "model_integrity",
                "Model checksum/size mismatch. Run python -m scripts.setup_models.",
                503,
            )
        content = path.read_bytes()
    except OSError as exc:
        raise SightLineError(
            "model_missing",
            "Model is missing or unreadable. Run python -m scripts.setup_models.",
            503,
        ) from exc
    if hashlib.sha256(content).hexdigest() != MODEL_SHA256:
        raise SightLineError(
            "model_integrity", "Model checksum mismatch. Run python -m scripts.setup_models.", 503
        )
    return content
