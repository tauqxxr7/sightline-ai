# Architecture

Browser file/sample -> bounded loopback POST -> decode/EXIF/alpha handling -> 416x416 BGR tensor -> explicit provider engine -> raw YOLOX decode and NMS -> JSON -> canvas boxes and accessible text list.

`CPUEngine` loads checksum-pinned model bytes into a CPU-only ORT session and reuses the session. `QNNEngine` wraps an independent CPU engine. It attempts `QNNProvider`, requiring native ARM64, trusted HTP DLL/model, strict fallback settings and an exclusive QNN profile. Strict mode fails with no active provider; normal QNN mode records the reason and runs the original CPU pipeline.

System inspection reports native OS architecture separately from process architecture, registry identity separately from runtime capabilities, and planned providers separately from successful execution. No provider availability alone enables an NPU label.

The browser holds current image/result state in memory. The server holds model sessions and provider metadata, not image history. Explicit exports serialize results/environment. QNN profiling is temporary. Configuration paths are CLI-only; HTTP accepts only CPU/QNN/strict policy choices.

This remains a loopback development application. Native packaging and further visual workflows are future phases.

## Phase 4 additions

Privacy Shield is a browser-only transformation module with a 6 MP limit, bounded manual regions and flattened PNG export. It has no upload endpoint. Screen Lens shares Visual Assist validation and inference; clipboard reads require an explicit action. Performance Lab calls a bounded loopback benchmark endpoint using a fresh CPUEngine, writes metadata-only JSON/CSV and serves artifacts through a restricted generated-ID route. Benchmarking and image inference share a concurrency guard. Shared UI view helpers and the existing CSS tokens govern the feature pages.
