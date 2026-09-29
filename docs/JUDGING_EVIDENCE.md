# Judging evidence

| Criterion | Implementation | Actual evidence | Limit |
|---|---|---|---|
| Technical implementation | app/inference, app/benchmarking, app/system | CPU reference tests; 90 Python + 19 JS tests; actual benchmark JSON/CSV | QNN hardware unverified |
| Useful visual workflows | ui/pages/visual.js, privacy.js, performance.js | Phase 4 screenshots; clipboard inference; redacted PNG pixel verification | OCR and automatic privacy detection unavailable |
| Deployment/accessibility | Loopback Windows host; shared CSS tokens; keyboard controls | Local browser flow and compact-width checks; coordinate-based redaction | No native installer or accessibility certification |
| Presentation/documentation | README, phase reports, benchmark/privacy/security methodology | Explicit provider and fallback metadata, source model/license and raw measurements | Not submission-ready |

[Phase 4 report](PHASE_4_REPORT.md) contains per-feature gates and actual observations. [Phase 2](PHASE_2_REPORT.md) and [Phase 3](PHASE_3_REPORT.md) are historical evidence. The selected genuine benchmark is [JSON](../benchmarks/results/cb70fbe2ed474154929a5d7a2cb1233f.json) / [CSV](../benchmarks/results/cb70fbe2ed474154929a5d7a2cb1233f.csv). Synthetic policy tests are never presented as NPU evidence. No AI Hub job or remote CI run has been performed.
