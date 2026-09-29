# Product requirements and status

SightLine provides local visual analysis with explicit execution evidence. CPU fallback is retained; NPU labels require verified execution.

| Workflow | Phase 4 implementation | Explicitly outside current scope |
|---|---|---|
| Visual Assist | Import/drop, real boxes/confidence, inventory, overlays, JSON | OCR, captions, automatic privacy findings |
| Privacy Shield | Manual coordinate/drag regions, blur/pixelate/solid, before/after, PNG | Automatic sensitive-content detection |
| Screen Lens | Screenshot files, explicit clipboard read/paste, local detection | Screen capture, OCR |
| Performance Lab | Real CPU cold/warm timings, statistics, JSON/CSV | QNN comparison, memory, video FPS |
| Camera Assist | Unavailable page; no camera implementation | All camera capture/sampling |

Implemented and tested in the user's requested order. Hardware verification, native packaging and later hardening remain separate work. No accounts or mandatory cloud inference.
