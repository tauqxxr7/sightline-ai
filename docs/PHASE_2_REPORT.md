# Phase 2 CPU gate — 2026-09-28

The official 3,659,407-byte YOLOX-Nano ONNX artifact loads in ONNX Runtime 1.30.0 on this Windows AMD64/Intel machine. SHA-256 is pinned in models/manifest.json. No QNN code was added until the following checks passed.

- Preprocessing exactly matches reference revision `6ddff4824372906469a7fae2dc3206c7aa4bbaee` on square and nonsquare images: BGR, OpenCV bilinear resize, top-left pad 114, NCHW float32, no normalization.
- Raw-head decoding and NMS match the pinned reference on actual output.
- Real CPU inference on the public-domain astronaut sample detects a person with approximately 0.926 confidence; this is not an accuracy score.
- Browser sample → local POST → CPU inference → drawn box and accessible object list verified. Browser recorded no warnings/errors.
- `python -m pytest -q --tb=short`: **48 passed in 11.00s**.
- `node --test --test-isolation=none tests/ui.test.js`: **6 passed**.
- `python -m ruff check .`: passed. `ruff format --check .`: 23 files already formatted.
- `python -m mypy`: no issues in 16 source files. JS syntax checks passed.

The old release-tag RGB normalization did not match the published artifact; the current pinned official reference did. This was corrected before integration. A large-input test originally generated an oversized pytest case ID; explicit short IDs corrected test setup. The final suite passed.

Single-run browser observations were initialization 72.06 ms, preprocessing 62.72 ms, inference 20.05 ms, postprocessing 6.67 ms and total local pipeline 162.71 ms. These are one observed run, not a benchmark or device comparison. Raw repeated benchmarking is deferred.

The provided GitHub repository was empty. The original user-supplied build prompt was restored verbatim as MASTER_BUILD_PROMPT.md and origin set to tauqxxr7/sightline-ai. No remote changes were published.
