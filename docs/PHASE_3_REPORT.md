# Phase 3 implementation and evidence

Recorded 2026-09-28. Phase 2's real CPU gate was completed before optional QNN integration; see PHASE_2_REPORT.md. This report records local observations, not remote CI or Snapdragon certification.

## Actual environment

Windows 10.0.26200; Intel Core i5-1135G7; native AMD64 and AMD64 process, not emulated, observed using IsWow64Process2. Registry identity reports Qualcomm/Snapdragon not detected. Python 3.12.2, ONNX Runtime 1.30.0. Available EPs: AzureExecutionProvider and CPUExecutionProvider. Azure is never selected by inference code. QNN EP is absent.

## Implemented

Native/process architecture and processor identity reporting; separate runtime availability, requested/selected/active provider and fallback fields; optional QNN policy around the preserved CPU engine; strict HTP verification requiring successful inference, disabled fallback and exclusive QNN kernel events; sanitized failure states; UI policy selection, real result rendering and JSON exports. Official runtime reference and target-machine instructions are in QNN_VERIFICATION.md.

## Actual runs

- environment-phase3.json: inspection only, active provider null, QNN requested, CPU fallback planned, NPU false.
- qnn-strict.json: verification failed, qnn_unavailable, active null, fallback forbidden, NPU false, CLI exit 2. No CPU inference permitted.
- qnn-fallback.json: QNN requested, CPUExecutionProvider active, fallback cpu with missing-QNN reason, NPU false, CLI exit 0. Real YOLOX model produced a person detection around 92.6% confidence on the NASA sample.
- Browser: selected QNN fallback, ran sample, inspected actual box/text/provider details. Strict QNN displayed an explicit error and cleared detections. Browser console error/warning query returned none. Screenshots: evidence/qnn-cpu-fallback.png and evidence/qnn-strict-ui.png.
- Timings in JSON are single observations, not benchmarks. No speedup is claimed.

## Quality gates

| Gate | Actual result |
|---|---|
| pytest -q | 69 passed in 13.10 seconds |
| Node tests, isolation disabled for restricted environment | 6 passed, 0 failed/skipped |
| Ruff check | Passed |
| Ruff format --check | 29 files already formatted |
| mypy | Passed, 20 source files |
| npm run check | Four JavaScript files passed syntax checks |
| pip check | No broken requirements |
| git diff --check | Passed; CRLF normalization notices only |

Tests include real CPU model execution, upstream preprocessing/decoder comparison, malformed/oversized input, HTTP origin and provider policies, registry/architecture fixtures, strict no-CPU behavior and actual CPU fallback. Synthetic QNN session/profile tests check the configuration, backend, successful proof contract and rejection of CPU/mixed/unknown/empty evidence. They are explicitly not real NPU evidence.

## Remaining hardware gate

No Qualcomm hardware, QNN runtime, validated QNN artifact or NPU run is available here. A supported native ARM64 environment, trusted QnnHtp.dll and separately calibrated/validated artifact are required. The wrapper intentionally rejects runtimes that cannot expose sufficient backend/profile evidence. No AI Hub job or remote CI run was performed. Native packaging, camera, OCR, redaction, accuracy evaluation and sustained benchmarks remain future work.
