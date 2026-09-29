"""Provider safety tests. Synthetic profiles are not hardware evidence."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from app.core.errors import SightLineError
from app.inference.qnn import QNN, QNNProvider, profile_evidence
from app.inference.selection import QNNEngine

SAMPLE = Path(__file__).resolve().parents[1] / "assets/samples/astronaut.png"


def event(provider):
    return {"cat": "Node", "name": "test_kernel_time", "args": {"provider": provider}}


@pytest.mark.parametrize(
    "events",
    [
        None,
        [],
        [event("CPUExecutionProvider")],
        [event(QNN), event("CPUExecutionProvider")],
        [event(QNN), event(None)],
    ],
)
def test_incomplete_or_mixed_profiles_never_verify(events):
    with pytest.raises(SightLineError):
        profile_evidence(events)


def test_synthetic_qnn_profile_contract():
    evidence = profile_evidence([event(QNN), {"cat": "Node", "name": "fence"}])
    assert evidence["exclusive_qnn"] is True
    assert evidence["kernel_event_counts"] == {QNN: 1}


def test_strict_failure_does_not_call_cpu():
    engine = QNNEngine(strict=True)
    with patch.object(
        engine.qnn, "run", side_effect=SightLineError("qnn_unavailable", "Unavailable", 503)
    ):
        with patch.object(engine.cpu, "analyze", side_effect=AssertionError("CPU forbidden")):
            with pytest.raises(SightLineError, match="Strict mode forbids"):
                engine.analyze(SAMPLE.read_bytes(), "image/png")
    assert engine.runtime["active"] is None
    assert engine.runtime["fallback"] == "forbidden"
    assert engine.runtime["npu_verified"] is False


def test_qnn_failure_runs_real_cpu_fallback():
    engine = QNNEngine()
    with patch.object(
        engine.qnn, "run", side_effect=SightLineError("qnn_unavailable", "Unavailable", 503)
    ):
        result = engine.analyze(SAMPLE.read_bytes(), "image/png")
    assert result["runtime"]["requested"] == QNN
    assert result["runtime"]["active"] == "CPUExecutionProvider"
    assert result["runtime"]["fallback"] == "cpu"
    assert result["runtime"]["npu_verified"] is False
    assert any(d["label"] == "person" and d["confidence"] > 0.8 for d in result["detections"])


def test_broken_provider_query_is_safe():
    fake = SimpleNamespace(
        get_available_providers=lambda: (_ for _ in ()).throw(RuntimeError("secret"))
    )
    with patch("app.inference.qnn.importlib.import_module", return_value=fake):
        with pytest.raises(SightLineError, match="Provider query failed"):
            QNNProvider().run(np.zeros((1, 3, 416, 416), dtype=np.float32))


def test_provider_registration_on_wrong_architecture_is_not_execution():
    fake = SimpleNamespace(get_available_providers=lambda: [QNN])
    hardware = {
        "system": "Windows",
        "native_architecture": {"value": "AMD64"},
        "process_architecture": "AMD64",
    }
    with (
        patch("app.inference.qnn.hardware_report", return_value=hardware),
        patch("app.inference.qnn.importlib.import_module", return_value=fake),
    ):
        with pytest.raises(SightLineError, match="ARM64"):
            QNNProvider().run(np.zeros((1, 3, 416, 416), dtype=np.float32))


def test_synthetic_session_enforces_flags_and_rejects_cpu(tmp_path):
    import hashlib
    import json

    model = tmp_path / "test.onnx"
    model.write_bytes(b"synthetic model; not real hardware evidence")
    backend = tmp_path / "QnnHtp.dll"
    backend.write_bytes(b"synthetic backend")

    class Options:
        def add_session_config_entry(self, key, value):
            self.config = {key: value}

        def get_session_config_entry(self, key):
            return self.config[key]

    class Session:
        providers = [QNN]
        kernel = QNN

        def __init__(self, content, sess_options, providers, provider_options):
            self.options = sess_options
            assert sess_options.config == {"session.disable_cpu_ep_fallback": "1"}
            assert sess_options.enable_profiling
            assert providers == [QNN]
            assert provider_options == [{"backend_path": str(backend.resolve())}]
            self.disabled = False

        def disable_fallback(self):
            self.disabled = True

        def get_providers(self):
            return self.providers

        def get_provider_options(self):
            return {QNN: {"backend_path": str(backend)}}

        def get_inputs(self):
            return [SimpleNamespace(type="tensor(float)", shape=[1, 3, 416, 416], name="images")]

        def get_outputs(self):
            return [SimpleNamespace(type="tensor(float)", shape=[1, 3549, 85])]

        def run(self, names, feeds):
            assert self.disabled
            return [np.zeros((1, 3549, 85), dtype=np.float32)]

        def end_profiling(self):
            path = Path(self.options.profile_file_prefix + ".json")
            path.write_text(json.dumps([event(self.kernel)]))
            return str(path)

    fake = SimpleNamespace(
        get_available_providers=lambda: [QNN],
        SessionOptions=Options,
        InferenceSession=Session,
        __version__="synthetic-test",
    )
    hardware = {
        "system": "Windows",
        "native_architecture": {"value": "ARM64"},
        "process_architecture": "ARM64",
    }
    provider = QNNProvider(model, hashlib.sha256(model.read_bytes()).hexdigest(), backend)
    with (
        patch("app.inference.qnn.hardware_report", return_value=hardware),
        patch("app.inference.qnn.importlib.import_module", return_value=fake),
    ):
        _, runtime, _ = provider.run(np.zeros((1, 3, 416, 416), dtype=np.float32))
        assert runtime["npu_verified"] is True  # Synthetic contract only.
        Session.kernel = "CPUExecutionProvider"
        with pytest.raises(SightLineError, match="exclusive QNN"):
            provider.run(np.zeros((1, 3, 416, 416), dtype=np.float32))
        Session.providers = ["CPUExecutionProvider"]
        with pytest.raises(SightLineError, match="fell back"):
            provider.run(np.zeros((1, 3, 416, 416), dtype=np.float32))
