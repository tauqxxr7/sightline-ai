# Phase 0 repository audit — 2026-09-27

## 1. Repository audit
The supplied directory contained only empty `outputs/` and `work/` directories. Recursive file enumeration found no source, tests, dependencies, models or CI. Both `git status --short` and `git rev-parse --show-toplevel` reported no Git repository. No repository URL was supplied. The new foundation lives under `outputs/sightline-ai`; no remote is configured. This audit covers the supplied workspace, not unrelated repositories elsewhere on the machine.

Observed tools: Python 3.12.2, Node 24.14.0, Git 2.53.0.windows.1, pytest 8.3.2 and Ruff 0.15.12. Python reports Windows 11 / AMD64 and Intel64 Family 6 Model 140 Stepping 1, GenuineIntel. The CIM processor query was denied. Platform information is not hardware certification. ONNX Runtime is absent and no model is installed. **QNN/NPU not verified on this device.**

## 2. Proposed architecture
Python owns validation, model lifecycle, inference, provider evidence and benchmarks. A local HTML/CSS/ES-module interface provides an accessible desktop layout without frontend runtime dependencies. Phase 1 uses a read-only loopback development host. Native Windows packaging and constrained WebView2 IPC are later milestones. See [architecture](ARCHITECTURE.md).

## 3. Implementation plan
1. Shell, design tokens, environment inspection, provider policy, tests and CI.
2. Pin and acquire one YOLOX-Nano artifact; verify preprocessing/decoder and real CPU inference.
3. Add QNN sessions, explicit HTP configuration, strict fallback disabling and hardware execution evidence.
4. Add real Visual Assist results, clipboard import, manual redaction and benchmarks; camera last.
5. Harden decoding, resource limits, logging, accessibility and Windows packaging.
6. Run optional AI Hub compile/profile/validation and retain real artifacts.
7. Capture final demo evidence and assess every submission gate.

## 4. Dependency plan
Phase 1 runtime: Python standard library and browser APIs. No cloud SDK, CDN or secrets. Developer pins: pytest 8.3.2, Ruff 0.15.12 and mypy 1.15.0; Node 24 for built-in tests.

Phase 2 candidates: Pillow, NumPy and ONNX Runtime CPU. Pin only after checking wheel support for the selected architecture/Python combination. Phase 3 uses a separate ARM64 environment with onnxruntime-qnn; do not combine CPU and QNN distributions. AI Hub SDK/export/quantization belong in an optional build environment, outside core inference. Native packaging needs a validated ARM64 build matrix.

## 5. Model recommendation
Use YOLOX-Nano as the proposed first CPU detector. Upstream documents ONNX export and Apache-2.0 code licensing. Qualcomm AI Hub lists Yolo-X, but this does not establish compatibility of a Nano export. Pin weights, source revision, preprocessing, labels, decoder, precision and SHA-256 before deployment. The manifest deliberately leaves version/hash unset. Review the exact weights license before acquisition/distribution.

Sources checked 2026-09-27: [YOLOX](https://github.com/Megvii-BaseDetection/YOLOX), [Qualcomm Yolo-X](https://aihub.qualcomm.com/compute/models/yolox), [QNN EP](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html).

## 6. Risks/blockers
- No original repository/remote: new local foundation; no remote changes.
- No Snapdragon validation hardware identified: NPU execution cannot be established here.
- No runtime/model: no inference, latency, accuracy or offline inference claims.
- ARM64 wheels, HTP DLLs, quantization and operator coverage need a tested matrix.
- Browser dimensions are checked after decode; hostile-image resource hardening remains.
- Native installer, clean-machine setup and assistive-technology review remain unverified.

## 7. Exact Phase 1 changes
Create typed provider planning, observed environment status, read-only local host, eight-page UI, original SVG icon set, design tokens, validated memory-only image preview, environment CLI, setup script, model manifest, meaningful tests, CI, permanent AGENTS rules and phase documentation. No synthetic inference or benchmark results.
