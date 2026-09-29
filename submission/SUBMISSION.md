# SightLine AI
## Private Visual Intelligence for Snapdragon-Powered PCs

SightLine AI brings image understanding, manual privacy redaction, screenshot analysis and honest runtime reporting into one local application. Core inference runs in a local Python process through ONNX Runtime; the browser UI uses the shared SightLine design system.

Repository: https://github.com/tauqxxr7/sightline-ai

## Demonstrated capabilities

- **Visual Assist:** real YOLOX-Nano object detection, bounding boxes, confidence, object inventory and JSON export.
- **Privacy Shield:** user-selected regions, solid/blur/pixelate transformations, preview and PNG export. Automatic sensitive-content detection is unavailable.
- **Screen Lens:** PNG/JPEG screenshot import and explicit clipboard image import, followed by local analysis.
- **Performance Lab:** actual CPU measurements, cold/warm separation, raw samples and JSON/CSV export. No fabricated FPS or memory values.

## Run and demonstrate

From the repository root on Windows with Python and Node installed:

```powershell
./scripts/setup.ps1
./.venv/Scripts/python.exe -m app.core.server
```

Open http://127.0.0.1:8765/#visual. Setup requires network access to install dependencies and acquire the checksum-pinned model. Model weights are excluded from source control. Use the public sample at `assets/samples/astronaut.png`. Follow [the demo script](DEMO_SCRIPT.md).

## Evidence and boundaries

Screenshots in [assets](assets) were captured from working workflows using the public NASA sample during Phase 4. They are evidence from those runs, not newly measured benchmark results. Final automated results and current environment/provider reports are in [verification](verification).

Verified hardware is Intel AMD64 Windows, not Snapdragon. QNN is unavailable on this machine. Strict QNN verification must fail closed here; the normal QNN policy preserves real CPU fallback. NPU execution has not been verified and no NPU performance claim is made.

This submission is a loopback development application. Native Windows packaging, OCR, automatic privacy detection, Camera Assist, Qualcomm AI Hub jobs, accuracy evaluation and Snapdragon hardware validation are not complete. No recorded demo video is included. Blur and pixelation do not guarantee irreversible concealment; inspect exports before sharing.

## Licensing

Original code: MIT (repository LICENSE). YOLOX: Apache-2.0 (models/YOLOX-LICENSE.txt). The NASA Eileen Collins sample is public domain; provenance is recorded in assets/samples/README.md at the repository root. Screenshots show that public sample. No personal input images are included.
