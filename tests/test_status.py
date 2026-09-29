from types import SimpleNamespace
from unittest.mock import patch

from app.system.status import runtime_status


def test_runtime_missing_is_reported():
    with patch("app.system.status.importlib.import_module", side_effect=ImportError):
        result = runtime_status()
    assert result["runtime_version"] is None
    assert result["provider"]["available"] == ()
    assert result["provider"]["active"] is None
    assert result["measurements"] is None


def test_broken_runtime_does_not_expose_exception():
    with patch(
        "app.system.status.importlib.import_module", side_effect=RuntimeError("secret-path")
    ):
        result = runtime_status()
    assert "secret-path" not in str(result)
    assert result["runtime_error"] is not None


def test_provider_enumeration_never_certifies_hardware():
    fake = SimpleNamespace(
        __version__="test-fixture", get_available_providers=lambda: ["QNNExecutionProvider"]
    )
    with patch("app.system.status.importlib.import_module", return_value=fake):
        result = runtime_status()
    assert result["provider"]["selected"] is None
    assert result["provider"]["active"] is None
    assert result["provider"]["npu_verified"] is False
