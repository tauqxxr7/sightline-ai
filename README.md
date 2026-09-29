# SightLine AI

### Private Visual Intelligence for Snapdragon-Powered PCs

SightLine AI is a local-first visual intelligence application designed for Snapdragon-powered Windows PCs. It helps users analyze images, screenshots and clipboard images while minimizing unnecessary cloud exposure.

Four connected workflows provide structured object results, manual privacy redaction, screenshot analysis and transparent runtime measurements. Python and ONNX Runtime power local computer vision, with an optional Qualcomm QNN/HTP verification path and a preserved CPU fallback. Shared SightLine design tokens, keyboard controls, visible states and structured text results support accessible interaction.

**Current scope:** object detection and manual region redaction work. Automatic sensitive-content detection, OCR, document conversion and Camera Assist are unavailable. The UI is a browser-based Windows development application, not a native installer.

[Repository](https://github.com/tauqxxr7/sightline-ai) | **Core technologies:** Python, ONNX Runtime, local computer vision, Windows hardware inspection, QNN/HTP provider architecture.

Local visual intelligence for Windows. **CPU inference works. QNN/NPU execution is unverified on this Intel AMD64 machine.**

## Implemented

- Real YOLOX-Nano model loading, image preprocessing, inference, decoding and bounding-box rendering.
- Native Windows architecture and processor identity inspection, ORT version and provider enumeration.
- CPU, QNN with CPU fallback, and strict QNN policies with explicit requested/active/fallback fields.
- Conservative HTP verification: strict session configuration, confirmed backend and exclusive QNN execution profile required before any NPU claim.
- Visual Assist: real boxes, confidence, object inventory, overlays and JSON export.
- Privacy Shield: manual regions, blur/pixelate/solid effects, before/after preview and PNG export.
- Screen Lens: screenshot files, explicit clipboard reading and Ctrl+V image paste.
- Performance Lab: bounded CPU benchmarks with cold/warm separation, raw samples and JSON/CSV artifacts.
- Machine-readable reports and automated CPU, provider, HTTP and UI contract tests.

## Run

Python 3.12 and Node 24 were used for local verification. Setup downloads dependencies and a checksum-pinned official model; inference runs locally.

```powershell
./scripts/setup.ps1
./.venv/Scripts/python.exe -m app.core.server
```

Open http://127.0.0.1:8765/#visual. Choose the public-domain sample, select an execution policy and analyze. The sample produces a person detection on CPU. Model weights are ignored by Git and must be acquired during setup.

## Verify

```powershell
./.venv/Scripts/python.exe -m scripts.verify_environment --provider qnn --output docs/evidence/environment-phase3.json
./.venv/Scripts/python.exe -m scripts.verify_qnn --output docs/evidence/qnn-strict.json
./.venv/Scripts/python.exe -m scripts.verify_qnn --allow-cpu-fallback --output docs/evidence/qnn-fallback.json
./.venv/Scripts/python.exe -m pytest -q
./.venv/Scripts/python.exe -m ruff check .
./.venv/Scripts/python.exe -m ruff format --check .
./.venv/Scripts/python.exe -m mypy
npm test
npm run check
```

Strict verification exits 2 if evidence is missing; that is the expected result here. In child-process-restricted environments run `node --test --test-isolation=none tests/*.test.js`.

[Phase 4 evidence](docs/PHASE_4_REPORT.md) | [Benchmark methodology](docs/BENCHMARKS.md) | [Phase 2 evidence](docs/PHASE_2_REPORT.md) · [Phase 3 evidence](docs/PHASE_3_REPORT.md) · [QNN setup and limits](docs/QNN_VERIFICATION.md) · [Environment JSON](docs/evidence/environment-phase3.json)

## Limits and privacy

This is a loopback development application, not a packaged native Windows release. OCR, automatic sensitive-content detection, camera capture, accuracy evaluation and sustained thermal/battery benchmarks remain unfinished. No AI Hub job has run. Input images pass from the browser to the local Python process in memory; no external inference service or telemetry is configured. See [Privacy](docs/PRIVACY.md), [Security](docs/SECURITY.md), [model details](models/MODEL_CARD.md) and [limitations](docs/LIMITATIONS.md).

MIT for original SightLine code. YOLOX retains its Apache-2.0 license. NASA sample attribution is in assets/samples/README.md.

## Submission

See [submission package](submission/SUBMISSION.md) and [final verification](submission/verification/results.json).
