# Phase 4 demo

After setup and model acquisition, launch the loopback server.

1. Visual Assist: select the public-domain sample and Analyze locally. Inspect actual person detection, object inventory and provider/timings; toggle overlays and export JSON.
2. Privacy Shield: select an image, enter a manual region using coordinates or drag. Compare solid/pixelate/blur effects, remove or undo selections, export the redacted PNG and inspect it before sharing. Automatic detection is unavailable.
3. Screen Lens: copy a PNG/JPEG image and click Import clipboard image or press Ctrl+V. Analyze explicitly. If permission is denied, use screenshot file import.
4. Performance Lab: choose warmups/sample count, run the CPU benchmark, inspect measured statistics and export JSON/CSV. Explain that cold means a fresh session and no video FPS/memory/QNN comparison is measured.
5. Show strict QNN failure and CPU fallback in Visual Assist if needed. On this Intel device NPU execution remains unverified.

Camera Assist stays unimplemented. Do not present OCR, automatic privacy detection or native packaging as available. Network-disconnection testing is separate; no claim of an observed Wi-Fi-off run is made here.
