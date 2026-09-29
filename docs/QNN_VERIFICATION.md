# QNN verification

The CPU environment is preserved. This machine has Intel i5-1135G7 hardware, AMD64 Windows/Python and ORT 1.30.0 without QNN EP. No Snapdragon/NPU execution or speedup has been measured.

## Target setup

Use a separate virtual environment on a supported Snapdragon Windows ARM64 machine with native ARM64 Python and a compatible official `onnxruntime-qnn` package. Do not install competing ORT distributions into the CPU environment. Package/Python/QNN driver compatibility must be checked on the target; this repository does not claim the CPU dependency lock is an ARM64 QNN lock.

Supply a trusted QNN-compatible, separately validated model, its lowercase SHA-256 and the runtime's QnnHtp.dll. The artifact must retain float32 input [1,3,416,416], BGR 0..255 preprocessing, raw float32 output [1,3549,85] and COCO class ordering. Matching dimensions do not establish accuracy: quantization needs representative calibration and CPU/QNN accuracy comparison. No QNN artifact has been generated or validated here.

```powershell
python -m scripts.verify_qnn --model C:/models/yolox-qdq.onnx --sha256 YOUR_SHA256 --backend C:/runtime/QnnHtp.dll --output qnn-verification.json
python -m app.core.server --qnn-model C:/models/yolox-qdq.onnx --qnn-sha256 YOUR_SHA256 --qnn-backend C:/runtime/QnnHtp.dll
```

Select strict QNN in Visual Assist. The CLI defaults to strict; `--allow-cpu-fallback` explicitly allows the original CPU engine when verification fails.

## Evidence rule

Require QNN EP availability, native ARM64 process/OS, pinned model bytes, confirmed HTP backend options, disabled CPU EP fallback, disabled Python runtime fallback, successful inference, valid output, and ORT Node kernel events exclusively assigned to QNN. Empty, unknown, mixed or CPU profiles fail closed. Provider enumeration or registration alone never establishes execution. Sessions whose provider options/profile cannot confirm these facts remain unverified, even if the device might be capable.

ORT profiles are temporary and removed after parsing; the report retains counts and SHA-256. This is profiled cold execution, not a performance benchmark. It establishes runtime evidence for the given run, not independent hardware attestation. Synthetic test sessions validate policy only.

Official reference: [ONNX Runtime QNN EP documentation](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html), consulted 2026-09-28. The documented HTP backend and `session.disable_cpu_ep_fallback` setting underpin this implementation.
