"""Hardware detection fixtures never imply verified acceleration."""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.system import hardware


@pytest.mark.parametrize(
    "name,qualcomm,snapdragon",
    [
        ("Snapdragon X Elite Qualcomm", "detected", "detected"),
        ("Qualcomm processor", "detected", "unverified"),
        ("GenuineIntel", "not_detected", "not_detected"),
        ("ARM Processor", "unverified", "unverified"),
        ("Intel Qualcomm", "unverified", "unverified"),
    ],
)
def test_registry_identity_is_conservative(monkeypatch, name, qualcomm, snapdragon):
    fake = SimpleNamespace(
        HKEY_LOCAL_MACHINE=0,
        KEY_READ=1,
        KEY_WOW64_64KEY=2,
        OpenKey=MagicMock(),
        QueryValueEx=lambda key, field: (name, 1),
    )
    monkeypatch.setitem(sys.modules, "winreg", fake)
    monkeypatch.setattr(hardware.platform, "system", lambda: "Windows")
    result = hardware.processor_identity()
    assert result["qualcomm"] == qualcomm
    assert result["snapdragon"] == snapdragon


def test_native_probe_missing_does_not_guess(monkeypatch):
    monkeypatch.setattr(hardware.platform, "system", lambda: "Windows")
    monkeypatch.setattr(hardware.ctypes, "WinDLL", MagicMock(side_effect=OSError), raising=False)
    assert hardware.native_windows_architecture()["value"] is None


def test_emulated_process_native_architecture(monkeypatch):
    monkeypatch.setattr(hardware.platform, "system", lambda: "Windows")

    def probe(handle, process, native):
        process._obj.value = 0x8664
        native._obj.value = 0xAA64
        return 1

    kernel = SimpleNamespace(
        GetCurrentProcess=MagicMock(return_value=123), IsWow64Process2=MagicMock(side_effect=probe)
    )
    monkeypatch.setattr(hardware.ctypes, "WinDLL", lambda *a, **k: kernel, raising=False)
    result = hardware.native_windows_architecture()
    assert result["value"] == "ARM64"
    assert result["emulated"] is True
