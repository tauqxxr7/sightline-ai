"""Fail-closed HTP execution. Availability and session registration are not proof."""

import hashlib
import importlib
import json
import tempfile
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
from numpy.typing import NDArray

from app.core.errors import SightLineError
from app.inference.model import INPUT_SHAPE, OUTPUT_SHAPE
from app.system.hardware import hardware_report

QNN = "QNNExecutionProvider"
UNVERIFIED = "QNN/NPU not verified on this device"


def profile_evidence(events: object) -> dict[str, object]:
    """Require actual QNN kernel events and reject CPU, unknown or mixed execution."""
    if not isinstance(events, list):
        raise SightLineError("qnn_profile", "Execution profile is unavailable or malformed.", 503)
    counts: dict[str, int] = {}
    for event in events:
        if not isinstance(event, dict) or event.get("cat") != "Node":
            continue
        args = event.get("args", {})
        provider = args.get("provider") if isinstance(args, dict) else None
        if provider is None and not str(event.get("name", "")).endswith("_kernel_time"):
            continue  # ORT fence events have no provider and do not represent kernels.
        key = str(provider or "unknown")
        counts[key] = counts.get(key, 0) + 1
    if not counts.get(QNN) or any(provider != QNN for provider in counts):
        raise SightLineError(
            "qnn_assignment", "Profile does not prove exclusive QNN execution.", 503
        )
    return {"kernel_event_counts": counts, "cpu_kernel_events": 0, "exclusive_qnn": True}


class QNNProvider:
    def __init__(
        self,
        model_path: Path | None = None,
        sha256: str | None = None,
        backend_path: Path | None = None,
    ) -> None:
        self.model_path, self.sha256, self.backend_path = model_path, sha256, backend_path

    def run(
        self, tensor: NDArray[np.float32]
    ) -> tuple[NDArray[np.float32], dict[str, object], dict[str, float]]:
        try:
            ort = importlib.import_module("onnxruntime")
        except Exception as exc:
            raise SightLineError(
                "runtime_missing", "ONNX Runtime could not be imported.", 503
            ) from exc
        try:
            available = list(ort.get_available_providers())
        except Exception as exc:
            raise SightLineError("runtime_unavailable", "Provider query failed.", 503) from exc
        if QNN not in available:
            raise SightLineError("qnn_unavailable", "QNN Execution Provider was not detected.", 503)
        hardware = hardware_report()
        native = hardware["native_architecture"]
        if (
            hardware["system"] != "Windows"
            or not isinstance(native, dict)
            or native.get("value") != "ARM64"
            or str(hardware["process_architecture"]).upper() not in ("ARM64", "AARCH64")
        ):
            raise SightLineError(
                "qnn_platform", "HTP verification requires native Windows ARM64 Python.", 503
            )
        if self.model_path is None or self.sha256 is None:
            raise SightLineError(
                "qnn_model_missing",
                "Configure a validated QNN model and SHA-256; CPU FP32 remains available.",
                503,
            )
        if len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256):
            raise SightLineError(
                "qnn_model_hash", "A lowercase SHA-256 is required for the QNN artifact.", 503
            )
        backend = self.backend_path
        if backend is None:
            package = Path(str(ort.__file__)).resolve().parent
            backend = next(
                (p for p in (package / "capi/QnnHtp.dll", package / "QnnHtp.dll") if p.is_file()),
                None,
            )
        if backend is None or not backend.is_file() or backend.name.lower() != "qnnhtp.dll":
            raise SightLineError(
                "qnn_backend", "A trusted QnnHtp.dll from the QNN runtime is required.", 503
            )
        try:
            if self.model_path.stat().st_size > 256 * 1024 * 1024:
                raise SightLineError(
                    "qnn_model_size", "QNN model exceeds the supported size limit.", 503
                )
            content = self.model_path.read_bytes()
        except OSError as exc:
            raise SightLineError(
                "qnn_model_missing", "QNN artifact is missing or unreadable.", 503
            ) from exc
        if hashlib.sha256(content).hexdigest() != self.sha256:
            raise SightLineError(
                "qnn_model_hash", "QNN artifact checksum does not match configuration.", 503
            )
        if (
            tensor.shape != INPUT_SHAPE
            or tensor.dtype != np.float32
            or not np.isfinite(tensor).all()
        ):
            raise SightLineError(
                "qnn_input", "QNN input does not match the validated image contract."
            )
        started = perf_counter()
        with tempfile.TemporaryDirectory(prefix="sightline-qnn-") as directory:
            session: Any = None
            ended = False
            try:
                options = ort.SessionOptions()
                options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
                if options.get_session_config_entry("session.disable_cpu_ep_fallback") != "1":
                    raise SightLineError(
                        "qnn_strict_unsupported",
                        "Runtime cannot enforce strict CPU fallback disabling.",
                        503,
                    )
                options.enable_profiling = True
                options.profile_file_prefix = str(Path(directory) / "execution")
                options.log_severity_level = 3
                session = ort.InferenceSession(
                    content,
                    sess_options=options,
                    providers=[QNN],
                    provider_options=[{"backend_path": str(backend.resolve())}],
                )
                session.disable_fallback()
                registered = session.get_providers()
                if (
                    not registered
                    or registered[0] != QNN
                    or any(p not in (QNN, "CPUExecutionProvider") for p in registered)
                ):
                    raise SightLineError(
                        "qnn_session_fallback", "Session construction fell back from QNN.", 503
                    )
                applied = session.get_provider_options().get(QNN, {})
                if Path(applied.get("backend_path", "")).resolve() != backend.resolve():
                    raise SightLineError(
                        "qnn_backend_unconfirmed",
                        "Session did not confirm the requested HTP backend.",
                        503,
                    )
                inputs, outputs = session.get_inputs(), session.get_outputs()
                if (
                    len(inputs) != 1
                    or inputs[0].type != "tensor(float)"
                    or tuple(inputs[0].shape) != INPUT_SHAPE
                    or len(outputs) != 1
                    or outputs[0].type != "tensor(float)"
                    or tuple(outputs[0].shape) != OUTPUT_SHAPE
                ):
                    raise SightLineError(
                        "qnn_contract", "QNN artifact does not match the YOLOX I/O contract.", 503
                    )
                initialization = (perf_counter() - started) * 1000
                inference_start = perf_counter()
                raw = session.run(None, {inputs[0].name: tensor})[0]
                inference = (perf_counter() - inference_start) * 1000
                profile = Path(session.end_profiling())
                ended = True
                if (
                    not profile.resolve().is_relative_to(Path(directory).resolve())
                    or profile.stat().st_size > 64 * 1024 * 1024
                ):
                    raise SightLineError(
                        "qnn_profile", "Unexpected execution profile location or size.", 503
                    )
                profile_bytes = profile.read_bytes()
                evidence = profile_evidence(json.loads(profile_bytes))
                if (
                    raw.shape != OUTPUT_SHAPE
                    or raw.dtype != np.float32
                    or not np.isfinite(raw).all()
                ):
                    raise SightLineError("qnn_output", "QNN output validation failed.", 503)
                evidence.update(
                    profile_sha256=hashlib.sha256(profile_bytes).hexdigest(),
                    strict_cpu_fallback_disabled=True,
                    runtime_fallback_disabled=True,
                    backend="QnnHtp.dll",
                    model_sha256=self.sha256,
                )
                runtime = {
                    "requested": QNN,
                    "available": available,
                    "active": QNN,
                    "backend": "HTP",
                    "fallback": "none",
                    "npu": "Verified QNN HTP execution for this run",
                    "npu_verified": True,
                    "version": str(ort.__version__),
                    "evidence": evidence,
                }
                return (
                    np.asarray(raw, dtype=np.float32),
                    runtime,
                    {"initialization": initialization, "inference": inference},
                )
            except SightLineError:
                raise
            except Exception as exc:
                raise SightLineError(
                    "qnn_verification_failed",
                    "QNN/HTP initialization, execution or evidence validation failed.",
                    503,
                ) from exc
            finally:
                if session is not None and not ended:
                    try:
                        session.end_profiling()
                    except Exception:
                        pass
                session = None
