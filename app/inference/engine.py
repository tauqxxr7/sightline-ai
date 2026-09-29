"""One serialized CPU session; execution metadata requires a successful real run."""

import importlib
import logging
import threading
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np

from app.core.errors import SightLineError
from app.inference.model import (
    INPUT_SHAPE,
    MODEL_PATH,
    MODEL_SHA256,
    MODEL_VERSION,
    OUTPUT_SHAPE,
    verified_model_bytes,
)
from app.inference.postprocess import postprocess
from app.inference.preprocess import decode_image, preprocess

LOG = logging.getLogger("sightline")


class CPUEngine:
    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        self.model_path = model_path
        self._session: Any = None
        self._lock = threading.Lock()
        self._last_runtime: dict[str, object] | None = None
        self._initialization_ms: float | None = None
        self._runtime_version: str | None = None

    def snapshot(self) -> dict[str, object]:
        return {
            "installed": self.model_path.is_file(),
            "loaded": self._session is not None,
            "name": "YOLOX-Nano",
            "version": MODEL_VERSION,
            "sha256": MODEL_SHA256,
            "precision": "FP32",
            "last_successful_runtime": self._last_runtime,
        }

    def _load(self) -> bool:
        if self._session is not None:
            return False
        started = perf_counter()
        content = verified_model_bytes(self.model_path)
        try:
            ort = importlib.import_module("onnxruntime")
            if "CPUExecutionProvider" not in ort.get_available_providers():
                raise SightLineError(
                    "cpu_unavailable", "CPU Execution Provider is unavailable.", 503
                )
            options = ort.SessionOptions()
            options.intra_op_num_threads = 2
            options.inter_op_num_threads = 1
            options.log_severity_level = 3
            session = ort.InferenceSession(
                content, sess_options=options, providers=["CPUExecutionProvider"]
            )
            session.disable_fallback()
            if session.get_providers() != ["CPUExecutionProvider"]:
                raise SightLineError(
                    "provider_mismatch", "Required CPU provider was not selected.", 503
                )
            inputs, outputs = session.get_inputs(), session.get_outputs()
            if (
                len(inputs) != 1
                or inputs[0].name != "images"
                or tuple(inputs[0].shape) != INPUT_SHAPE
                or inputs[0].type != "tensor(float)"
                or len(outputs) != 1
                or tuple(outputs[0].shape) != OUTPUT_SHAPE
            ):
                raise SightLineError(
                    "model_contract", "Model I/O contract does not match the pinned artifact.", 503
                )
            self._session = session
            self._runtime_version = str(ort.__version__)
            self._initialization_ms = (perf_counter() - started) * 1000
            LOG.info('{"event":"model_loaded","provider":"CPUExecutionProvider"}')
            return True
        except SightLineError:
            raise
        except ImportError as exc:
            raise SightLineError(
                "runtime_missing", "Install requirements-cpu.txt in the active environment.", 503
            ) from exc
        except Exception as exc:
            LOG.error('{"event":"model_load_failed"}')
            raise SightLineError(
                "model_load", "Model could not be loaded. Check runtime and model setup.", 503
            ) from exc

    def analyze(self, content: bytes, mime: str) -> dict[str, object]:
        if not self._lock.acquire(blocking=False):
            raise SightLineError(
                "busy", "An analysis is already running. Try again when it finishes.", 409
            )
        try:
            start = perf_counter()
            prepared = preprocess(decode_image(content, mime))
            preprocessing_ms = (perf_counter() - start) * 1000
            cold = self._load()
            inference_start = perf_counter()
            try:
                raw = self._session.run(None, {"images": prepared.tensor})[0]
            except Exception as exc:
                self._last_runtime = None
                self._session = None
                LOG.error('{"event":"inference_failed","provider":"CPUExecutionProvider"}')
                raise SightLineError(
                    "inference_failed", "CPU inference failed. Clear the image and try again.", 503
                ) from exc
            inference_ms = (perf_counter() - inference_start) * 1000
            post_start = perf_counter()
            if raw.dtype != np.float32:
                raise SightLineError("model_output", "Model output has an unsupported dtype.", 503)
            detections = postprocess(raw, prepared.width, prepared.height, prepared.ratio)
            postprocessing_ms = (perf_counter() - post_start) * 1000
            runtime: dict[str, object] = {
                "requested": "CPUExecutionProvider",
                "available": list(importlib.import_module("onnxruntime").get_available_providers()),
                "active": "CPUExecutionProvider",
                "backend": "CPU",
                "fallback": "not_requested",
                "npu": "QNN/NPU not verified on this device",
                "npu_verified": False,
                "version": self._runtime_version,
                "evidence": "Successful run in a CPU-only session with runtime fallback disabled",
            }
            self._last_runtime = runtime
            LOG.info('{"event":"inference_succeeded","provider":"CPUExecutionProvider"}')
            return {
                "schema_version": 1,
                "observed_at": datetime.now(UTC).isoformat(),
                "image": {"width": prepared.width, "height": prepared.height},
                "model": {
                    "name": "YOLOX-Nano",
                    "version": MODEL_VERSION,
                    "sha256": MODEL_SHA256,
                    "precision": "FP32",
                    "input_shape": list(INPUT_SHAPE),
                },
                "runtime": runtime,
                "detections": [item.to_dict() for item in detections],
                "thresholds": {"confidence": 0.3, "nms_iou": 0.45, "max_detections": 100},
                "timings_ms": {
                    "initialization": self._initialization_ms if cold else None,
                    "preprocessing": preprocessing_ms,
                    "inference": inference_ms,
                    "postprocessing": postprocessing_ms,
                    "total_pipeline": (perf_counter() - start) * 1000,
                },
                "run_kind": "cold" if cold else "warm",
                "network": "Loopback only; no external inference request",
                "unsupported": ["OCR", "redaction", "camera", "scene captioning"],
            }
        finally:
            self._lock.release()
