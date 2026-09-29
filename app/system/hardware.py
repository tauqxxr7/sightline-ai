"""Observe Windows native architecture and processor identity without shell commands."""

import ctypes
import platform
from typing import Any


def native_windows_architecture() -> dict[str, object]:
    if platform.system() != "Windows":
        return {"value": None, "source": None, "error": "Not Windows"}
    try:
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        probe = kernel.IsWow64Process2
        probe.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ushort),
            ctypes.POINTER(ctypes.c_ushort),
        ]
        probe.restype = ctypes.c_int
        process, native = ctypes.c_ushort(), ctypes.c_ushort()
        if not probe(kernel.GetCurrentProcess(), ctypes.byref(process), ctypes.byref(native)):
            raise OSError("IsWow64Process2 failed")
        names = {0xAA64: "ARM64", 0x8664: "AMD64", 0x014C: "x86"}
        return {
            "value": names.get(native.value, f"unknown_0x{native.value:04x}"),
            "source": "Windows IsWow64Process2",
            "emulated": process.value != 0,
            "error": None,
        }
    except (OSError, AttributeError):
        return {
            "value": None,
            "source": "Windows IsWow64Process2",
            "error": "Native architecture query unavailable",
        }


def processor_identity() -> dict[str, object]:
    values: dict[str, str] = {}
    error = None
    if platform.system() == "Windows":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
            ) as key:
                for name in ("ProcessorNameString", "Identifier", "VendorIdentifier"):
                    try:
                        value: Any = winreg.QueryValueEx(key, name)[0]
                        if isinstance(value, str):
                            values[name] = value.strip()
                    except OSError:
                        pass
        except (ImportError, OSError):
            error = "Processor registry query unavailable"
    else:
        error = "Windows processor registry not applicable"
    text = " ".join(values.values()).lower()
    qualcomm = "qualcomm" in text or "snapdragon" in text
    other = any(name in text for name in ("genuineintel", "authenticamd", "intel", "amd ryzen"))
    state = (
        "detected"
        if qualcomm and not other
        else "not_detected"
        if other and not qualcomm
        else "unverified"
    )
    return {
        "qualcomm": state,
        "snapdragon": (
            "detected"
            if "snapdragon" in text and not other
            else "not_detected"
            if state == "not_detected"
            else "unverified"
        ),
        "source": "Windows processor registry" if values else None,
        "values": values,
        "error": error,
        "note": "CPU identity only; not evidence of NPU execution",
    }


def hardware_report() -> dict[str, object]:
    return {
        "system": platform.system(),
        "os_version": platform.version(),
        "process_architecture": platform.machine(),
        "process_bits": ctypes.sizeof(ctypes.c_void_p) * 8,
        "native_architecture": native_windows_architecture(),
        "processor": processor_identity(),
    }
