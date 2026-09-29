"""Read runtime facts without starting inference or claiming NPU execution."""

import importlib
import platform
import sys
from datetime import UTC, datetime

from app.inference.providers import ProviderName, ProviderUnavailable, plan_provider
from app.system.hardware import hardware_report


def runtime_status(
    requested: ProviderName = "CPUExecutionProvider", strict: bool = False
) -> dict[str, object]:
    providers: tuple[str, ...] = ()
    version: str | None = None
    runtime_error: str | None = None
    try:
        runtime = importlib.import_module("onnxruntime")
        providers = tuple(str(item) for item in runtime.get_available_providers())
        version = str(runtime.__version__)
    except ImportError:
        runtime_error = "ONNX Runtime is not installed or could not be imported."
    except Exception:
        runtime_error = "ONNX Runtime inspection failed. No provider is verified."
    hardware = hardware_report()
    try:
        plan = plan_provider(providers, requested=requested, strict=strict).to_dict()
    except ProviderUnavailable:
        plan = {
            "requested": requested,
            "available": providers,
            "selected": None,
            "active": None,
            "fallback": "forbidden",
            "backend": None,
            "npu": "QNN/NPU not verified on this device",
        }
    processor = hardware["processor"]
    assert isinstance(processor, dict)
    return {
        "schema_version": 1,
        "observed_at": datetime.now(UTC).isoformat(),
        "system": platform.system(),
        "architecture": platform.machine(),
        "processor": platform.processor() or "Unavailable",
        "processor_source": "Python platform API; not a hardware certification",
        "snapdragon": processor["snapdragon"],
        "hardware": hardware,
        "python": {"version": platform.python_version(), "implementation": sys.implementation.name},
        "runtime_version": version,
        "runtime_error": runtime_error,
        "qnn_ep_available": "QNNExecutionProvider" in providers,
        "provider": {**plan, "strict": strict, "npu_verified": False},
        "model": None,
        "measurements": None,
        "phase": "Phase 4 local visual workflows",
    }
