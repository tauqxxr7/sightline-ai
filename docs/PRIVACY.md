# Privacy

Visual Assist and Screen Lens keep selected images in browser memory until Analyze sends PNG/JPEG bytes to the Python process at 127.0.0.1. Images are decoded/inferred in memory. Screen Lens reads the clipboard only after Import clipboard image or the user's paste action. It does not poll the clipboard, capture the screen or request camera access.

Privacy Shield performs manual blur, pixelation or solid fill entirely in browser memory. It does not send images or regions to the server. Export creates a fresh flattened PNG from the redacted canvas, with no original EXIF payload. Unselected pixels remain visible. Automatic face/text/email/phone/QR detection is unavailable. Blur/pixelation can preserve recognizable information; use solid fill to replace selected content and review the whole output.

No telemetry or external inference service is configured. Dependencies and model acquisition require network during explicit setup; sample loading and inference use the loopback server. No universal claim is made about OS/browser behavior. Clearing a view releases references, not secure memory erasure.

Detection JSON and redacted PNG downloads are explicit. Benchmark runs intentionally persist environment/model/input hashes and timings under benchmarks/results/. They use the bundled public image and do not persist image pixels, detection results or user filenames. Environment reports include CPU identity and software versions, not serial numbers.

QNN verification writes temporary ORT profiles and removes them after parsing. Summaries retain counts and a hash. Browser/OS caches, paging, crash dumps and third-party runtime behavior are outside the application's guarantees. Review exported files before sharing them.
