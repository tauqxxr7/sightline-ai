# Current limitations

- The four Phase 4 workflows are implemented for their documented scope: object detection, manual redaction, screenshot/clipboard import and measured CPU benchmarking.
- OCR, automatic sensitive-region detection, scene captioning, screen capture, document conversion and Camera Assist are not implemented. Camera access remains blocked.
- Actual device is Intel i5-1135G7 with AMD64 Windows/Python; QNN EP absent. No NPU execution or speedup claim. Real Snapdragon/QNN model/runtime validation remains pending.
- The object model can miss objects or produce false positives. Its confidence is not calibrated; one fixture is not a dataset accuracy evaluation.
- Privacy Shield supports PNG/JPEG up to 10 MB and 6 MP, with up to 50 manual regions. Blur/pixelation are visual obscuring effects, not guarantees of removal. Unselected content remains visible. Solid fill replaces the selected pixels in the exported PNG.
- Clipboard support depends on browser permissions. File import remains available when clipboard read is denied. No clipboard polling or automatic analysis occurs.
- Benchmarks repeat one public image in a fresh CPU session. OS cache, thermals and concurrent work are uncontrolled. Memory and video FPS are not measured. QNN comparisons remain unavailable.
- Development loopback host, one inference/benchmark at a time, no native installer or process authentication. Browser cancellation does not terminate a native runtime call.
- Native packaging, comprehensive security/accessibility review, accuracy evaluation and thermal/battery testing are future work. Not submission-ready.
