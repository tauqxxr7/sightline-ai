"""Optional verified QNN path with explicit fallback to the preserved CPU engine."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from app.core.errors import SightLineError
from app.inference.engine import CPUEngine
from app.inference.postprocess import postprocess
from app.inference.preprocess import decode_image, preprocess
from app.inference.qnn import QNN, UNVERIFIED, QNNProvider

LOG = logging.getLogger("sightline")


class QNNEngine:
    def __init__(
        self,
        strict: bool = False,
        model_path: Path | None = None,
        sha256: str | None = None,
        backend_path: Path | None = None,
    ) -> None:
        self.strict = strict
        self.cpu = CPUEngine()
        self.qnn = QNNProvider(model_path, sha256, backend_path)
        self.runtime: dict[str, object] | None = None

    def snapshot(self) -> dict[str, object]:
        # The registry view concerns the preserved CPU model; runtime is separate.
        return {
            **self.cpu.snapshot(),
            "last_successful_runtime": None,
            "provider_state": self.runtime,
            "qnn_artifact_configured": self.qnn.model_path is not None,
        }

    def analyze(self, content: bytes, mime: str) -> dict[str, object]:
        started = perf_counter()
        self.runtime = {
            "requested": QNN,
            "active": None,
            "backend": None,
            "fallback": "forbidden" if self.strict else "pending",
            "strict": self.strict,
            "npu_verified": False,
            "npu": UNVERIFIED,
        }
        prepared = preprocess(decode_image(content, mime))
        preprocessing = (perf_counter() - started) * 1000
        try:
            raw, runtime, timings = self.qnn.run(prepared.tensor)
            post_start = perf_counter()
            detections = postprocess(raw, prepared.width, prepared.height, prepared.ratio)
            postprocessing = (perf_counter() - post_start) * 1000
            runtime["strict"] = self.strict
            self.runtime = runtime
            return {
                "schema_version": 1,
                "observed_at": datetime.now(UTC).isoformat(),
                "image": {"width": prepared.width, "height": prepared.height},
                "model": {
                    "name": "YOLOX compatible QNN artifact",
                    "version": "user-pinned SHA256",
                    "sha256": self.qnn.sha256,
                    "precision": "artifact-specific; not inferred",
                },
                "runtime": runtime,
                "detections": [d.to_dict() for d in detections],
                "timings_ms": {
                    **timings,
                    "preprocessing": preprocessing,
                    "postprocessing": postprocessing,
                    "total_pipeline": (perf_counter() - started) * 1000,
                },
                "run_kind": "cold_profiled_verification",
                "network": "Loopback only; no external inference request",
            }
        except SightLineError as exc:
            self.runtime.update(fallback_reason=exc.code, message=str(exc))
            if self.strict:
                LOG.warning('{"event":"strict_qnn_failed","cpu_fallback":false}')
                raise SightLineError(
                    exc.code, f"{str(exc)} Strict mode forbids CPU fallback. {UNVERIFIED}", 503
                ) from exc
            LOG.warning('{"event":"qnn_cpu_fallback"}')
            try:
                result = self.cpu.analyze(content, mime)
            except SightLineError:
                self.runtime.update(fallback="failed", active=None)
                raise
            fallback_runtime = result["runtime"]
            assert isinstance(fallback_runtime, dict)
            fallback_runtime.update(
                requested=QNN,
                fallback="cpu",
                fallback_reason=exc.code,
                fallback_message=str(exc),
                strict=False,
                npu_verified=False,
            )
            self.runtime = fallback_runtime
            timings_out = result["timings_ms"]
            assert isinstance(timings_out, dict)
            timings_out["total_with_provider_attempt"] = (perf_counter() - started) * 1000
            return result
