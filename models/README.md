# Model registry

Run `python -m scripts.setup_models` after installing requirements-cpu.txt. This explicitly downloads the official YOLOX-Nano ONNX release, checks byte count and SHA-256 and saves it under ignored models/weights. Runtime inference never downloads models.

The exact URL, checksum, tensor contract, preprocessing and thresholds are recorded in manifest.json. Source license is YOLOX-LICENSE.txt (Apache-2.0). QNN uses a separately supplied artifact and never overwrites this CPU model. See ../docs/QNN_VERIFICATION.md.
