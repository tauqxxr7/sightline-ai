You are the principal engineer, AI/edge-ML architect, Windows application architect,
product designer, security engineer, QA lead, and technical documentation lead for
a hackathon-grade project called SightLine AI.

You are working directly inside the Git repository.

PROJECT:
SightLine AI
Tagline: "Private Visual Intelligence. Powered Locally by Snapdragon."

MISSION:
Build a polished, evidence-driven, production-oriented Windows AI application
designed for Snapdragon-powered PCs.

SightLine AI accepts screenshots, images, documents, and optionally camera input
and performs useful visual intelligence locally.

The project's central differentiator is:

LOCAL AI + SNAPDRAGON NPU + PRIVACY + ACCESSIBILITY + TRANSPARENT BENCHMARKING.

This is NOT:
- a generic chatbot
- a cloud wrapper
- an AWS project
- an OpenAI/Gemini API wrapper
- a fake NPU demo
- a collection of disconnected AI features

AWS MUST NOT BE USED.

No mandatory cloud inference may exist in the core application.

==================================================
0. NON-NEGOTIABLE ENGINEERING INTEGRITY
==================================================

Never fabricate:

- Snapdragon hardware detection
- NPU execution
- QNN availability
- benchmark numbers
- latency
- FPS
- memory consumption
- model accuracy
- Qualcomm AI Hub results
- test results
- privacy guarantees
- offline capability
- model compatibility

Measured values must come from real measurements.

If NPU/QNN cannot be verified on the current machine, report:

"QNN/NPU not verified on this device"

and fall back gracefully.

Never display "NPU ACTIVE" simply because the application requested QNN.

The runtime must distinguish:

REQUESTED PROVIDER
AVAILABLE PROVIDER
ACTIVE PROVIDER
FALLBACK STATE

Where technically possible, provide strict verification mode that fails rather
than silently falling back from QNN/NPU to CPU.

Keep generated benchmark artifacts separate from sample/demo artifacts.

==================================================
1. PRODUCT VISION
==================================================

SightLine AI transforms a Snapdragon-powered Windows PC into a private,
offline-capable visual intelligence workstation.

Primary workflows:

1. Screen Lens
2. Visual Assist
3. Camera Assist
4. Privacy Shield
5. Performance Lab

Core experience:

INPUT
  ↓
LOCAL PREPROCESSING
  ↓
AI INFERENCE
  ↓
ONNX RUNTIME
  ↓
QNN EXECUTION PROVIDER
  ↓
SNAPDRAGON NPU / HTP
  ↓
POSTPROCESSING
  ↓
STRUCTURED ACCESSIBLE RESULT

CPU fallback must exist for development/testing.

==================================================
2. PRIMARY USE CASE
==================================================

SightLine should help a user understand visual information without requiring
the image to be uploaded to a cloud AI service.

Inputs:

- PNG
- JPG/JPEG
- screenshots
- clipboard images
- camera frames where practical
- supported document/image conversions where practical

Outputs:

- detected objects/regions
- extracted text where OCR is available
- confidence information
- structured visual summary
- sensitive-region detection/redaction
- inference metadata

==================================================
3. CORE FEATURES
==================================================

A. VISUAL ASSIST

Allow drag-and-drop or file selection.

Perform:
- validation
- preprocessing
- local inference
- object/region detection
- OCR if available
- structured output

Show:
- input preview
- detected regions
- labels
- confidence
- extracted text
- inference metadata

B. SCREEN LENS

Allow:
- screenshot import
- clipboard image
- optional screen capture if safely implementable

Analyze locally.

Provide structured visual information.

C. CAMERA ASSIST

If camera APIs are available:

camera
→ frame sampler
→ change detection / throttling
→ preprocessing
→ inference
→ confidence filtering
→ visual overlay

Do NOT perform wasteful inference on every frame.

Provide configurable sampling.

Camera failure must not break the application.

D. PRIVACY SHIELD

Provide a local privacy pipeline.

Detect supported sensitive visual information such as:
- faces, if supported by selected model
- text regions
- email-like strings
- phone-like strings
- QR codes if supported
- user-selected regions

Allow:
- blur
- pixelate
- solid redaction

Display:

Sensitive regions detected: N
Processing: Local
Network required for this operation: No

Do not claim detection categories that are not actually implemented.

E. PERFORMANCE LAB

Create a dedicated performance page.

Display real runtime information:

Hardware
Architecture
Model
Model version
Execution Provider requested
Execution Provider available
Execution Provider active
Backend
Precision
Inference latency
Warm inference latency
Cold initialization time where measured
FPS where meaningful
Memory where reliably measurable
Fallback status

Provide benchmark runner.

Save benchmark artifacts to:

benchmarks/results/

Prefer machine-readable JSON plus CSV where useful.

Never hardcode performance values.

==================================================
4. SNAPDRAGON / QUALCOMM ARCHITECTURE
==================================================

Primary inference architecture:

ONNX model
→ ONNX Runtime
→ QNN Execution Provider
→ HTP backend
→ Snapdragon NPU

Implement provider abstraction.

Suggested structure:

InferenceProvider
├── QNNProvider
└── CPUProvider

Provider selection:

1. inspect system
2. inspect ONNX Runtime providers
3. attempt QNN initialization
4. validate execution
5. record actual state
6. fall back to CPU if permitted
7. expose result transparently to UI

Support Windows ARM64 as primary target.

Where appropriate use onnxruntime-qnn.

Do not assume QNN exists.

Implement:

scripts/verify_environment.py
scripts/verify_qnn.py
scripts/benchmark.py

verify_qnn should produce human-readable and JSON results.

Research/document how strict CPU fallback disabling can be used where supported
to strengthen NPU verification.

==================================================
5. QUALCOMM AI HUB
==================================================

Prepare the project for Qualcomm AI Hub workflows.

Do NOT invent AI Hub job results.

Create:

docs/QUALCOMM_AI_HUB.md

Explain:

source model
→ upload/compile
→ target Snapdragon device
→ profile
→ validate
→ download optimized artifact
→ deploy locally

Provide scripts/configuration where reasonable.

Store real profile evidence only when it exists.

Create:

benchmarks/ai_hub/

with README explaining how real profile artifacts should be stored.

Clearly label placeholders/examples as examples.

==================================================
6. MODEL STRATEGY
==================================================

Choose small, credible models suitable for edge inference.

Priorities:

1. Qualcomm AI Hub compatibility
2. QNN compatibility
3. Windows ARM64 deployment
4. fast inference
5. permissive/documented licensing
6. useful visual output

Avoid unnecessarily large generative models.

Start with ONE reliable visual model.

Only add additional models when the previous pipeline is stable.

Maintain:

models/manifest.json

For every model record:

- name
- purpose
- source
- version
- format
- input shape
- precision
- license
- runtime
- expected provider
- checksum if distributable
- notes

Never commit huge model files when inappropriate.

Provide download/setup scripts where licensing permits.

==================================================
7. ARCHITECTURE
==================================================

Use clean modular boundaries.

Target structure:

sightline-ai/
│
├── app/
│   ├── core/
│   ├── inference/
│   ├── capture/
│   ├── privacy/
│   ├── accessibility/
│   ├── benchmarking/
│   └── system/
│
├── ui/
│   ├── components/
│   ├── pages/
│   ├── layouts/
│   ├── hooks/
│   ├── lib/
│   └── styles/
│
├── models/
│   ├── manifest.json
│   └── README.md
│
├── scripts/
│   ├── setup.ps1
│   ├── verify_environment.py
│   ├── verify_qnn.py
│   └── benchmark.py
│
├── benchmarks/
│   ├── results/
│   ├── ai_hub/
│   └── README.md
│
├── tests/
│
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── QUALCOMM_AI_HUB.md
│   ├── MODEL_CARD.md
│   ├── BENCHMARKS.md
│   ├── PRIVACY.md
│   ├── SECURITY.md
│   ├── ACCESSIBILITY.md
│   ├── LIMITATIONS.md
│   ├── DEMO_SCRIPT.md
│   └── JUDGING_EVIDENCE.md
│
├── .github/workflows/
│
├── AGENTS.md
├── README.md
├── LICENSE
└── .gitignore

Adapt this structure intelligently to the chosen implementation stack.

Do not create architecture for architecture's sake.

==================================================
8. UI / DESIGN SYSTEM
==================================================

Build a premium modern desktop AI interface.

The reference design philosophy is:

- modern
- minimal
- highly systematic
- strong visual hierarchy
- reusable components
- consistent spacing
- restrained use of accent colors
- professional AI tooling aesthetic

Do NOT make the application look like:
- Streamlit
- an admin template
- a generic Bootstrap dashboard
- a hackathon prototype
- a clone of another company's copyrighted interface

Create an ORIGINAL design system inspired by professional developer/AI tools.

DESIGN DIRECTION:

Dark-first desktop experience.

Suggested visual language:

Background:
near-black / graphite

Surfaces:
subtle elevated dark panels

Primary text:
near-white

Secondary text:
muted neutral

Accent:
electric blue / cyan family

Success:
accessible green

Warning:
accessible amber

Error:
accessible red

Use actual design tokens rather than scattered values.

Create tokens for:

- colors
- typography
- spacing
- radius
- shadows
- borders
- motion
- breakpoints

Typography:
clean technical sans-serif.

Use monospaced typography selectively for:
- model names
- latency
- execution providers
- hardware information
- logs

Avoid excessive gradients.

Avoid glassmorphism everywhere.

Avoid huge empty hero areas.

Avoid excessive rounded cards.

Avoid emoji as primary UI icons.

Use a coherent icon library.

==================================================
9. APPLICATION SHELL
==================================================

Desktop layout:

LEFT SIDEBAR

SightLine logo/name

WORKSPACE
- Overview
- Visual Assist
- Screen Lens
- Camera Assist
- Privacy Shield

SYSTEM
- Performance Lab
- Models
- Settings

BOTTOM
- Hardware status
- Version

TOP BAR

Current page
Offline/online indicator
Provider status
NPU status
Settings/help where appropriate

==================================================
10. OVERVIEW PAGE
==================================================

Create a strong landing dashboard.

Hero:

SightLine AI
Private Visual Intelligence
Powered Locally by Snapdragon

Primary action:
Analyze Visual

Secondary:
Open Screen Lens

Status cards:

SNAPDRAGON
detected / unavailable

NPU
verified / unavailable / unverified

EXECUTION PROVIDER
QNN / CPU

PRIVACY
Local Core Pipeline

Recent analysis section.

System readiness panel.

Do not show fake statistics.

==================================================
11. VISUAL ASSIST PAGE
==================================================

Large upload zone.

After analysis use split layout:

LEFT:
image with bounding boxes/regions

RIGHT:
structured analysis

Sections:

Objects
Text
Important regions
Privacy findings

Bottom inference strip:

MODEL
PROVIDER
COMPUTE
LATENCY
NETWORK

==================================================
12. PERFORMANCE LAB UI
==================================================

This page is crucial.

Header:
Snapdragon Performance Lab

System card:
CPU
architecture
Snapdragon status
NPU
runtime

Runtime card:
ONNX Runtime version
QNN availability
backend
model

Benchmark card:
Run Benchmark

Results:
cold start
warm inference
median
p95
FPS where relevant
memory where available

Comparison charts may only use measured values.

If comparison data is unavailable, explain that rather than fabricating it.

Allow exporting benchmark JSON.

==================================================
13. PRIVACY SHIELD UI
==================================================

Before/after interface.

LEFT:
original

RIGHT:
redacted

Controls:
Blur
Pixelate
Solid

List detected categories.

Display:

PROCESSING LOCATION
This Device

NETWORK
Not Required

Only make these claims for the local operation.

==================================================
14. ACCESSIBILITY
==================================================

Accessibility is a first-class requirement.

Implement:

- keyboard navigation
- visible focus states
- semantic HTML where applicable
- ARIA labels where required
- sufficient contrast
- scalable typography
- no color-only status communication
- reduced motion support
- screen-reader-friendly controls
- descriptive labels
- meaningful empty/error states

Document accessibility in docs/ACCESSIBILITY.md.

==================================================
15. SECURITY
==================================================

Perform a security review.

Requirements:

- no secrets in frontend
- no secrets committed
- .env files ignored
- secure environment variable handling
- strict file validation
- file size limits
- MIME/type checks
- safe filenames
- sanitize user-controlled strings
- prevent path traversal
- prevent unsafe file handling
- safe temporary-file lifecycle
- dependency review
- avoid command injection
- avoid arbitrary shell execution
- avoid unsafe deserialization

If a backend API exists:
- validate every request
- use schemas
- set request limits
- safe error handling
- appropriate CORS policy
- no stack traces exposed in production

Authentication is NOT required merely for appearance.

If the app stores no accounts/user cloud data, document why authentication is
outside MVP scope.

==================================================
16. PRIVACY
==================================================

The project must be privacy-evidence-first.

Document:

- what remains local
- whether telemetry exists
- what is persisted
- what is temporary
- network requirements
- model downloads
- optional external operations

Do not claim:
"Nothing ever leaves your computer"
unless technically proven for all functionality.

Prefer:
"Core visual inference runs locally."

==================================================
17. TESTING
==================================================

Create meaningful tests.

Test:

- file validation
- unsupported file rejection
- preprocessing
- postprocessing
- inference abstraction
- provider selection
- QNN unavailable behavior
- CPU fallback
- strict provider mode
- privacy transformations
- benchmark calculations
- system detection
- malformed input
- large input
- missing model
- corrupted model
- camera unavailable
- error states

Do not create meaningless tests just to inflate the count.

All test results reported in documentation must come from actual test runs.

==================================================
18. OBSERVABILITY
==================================================

Use structured local logging.

Never log:
- raw sensitive image data
- secrets
- API keys
- credentials

Log useful technical events:

provider initialization
model loading
fallback events
inference failures
benchmark runs

Provide debug mode separately.

==================================================
19. DOCUMENTATION
==================================================

README must be exceptional.

Recommended structure:

# SightLine AI

tagline

demo media

badges

What is SightLine?
Why this matters
Why Snapdragon?
Features
Architecture
Snapdragon / QNN integration
Qualcomm AI Hub workflow
Models
Performance
Privacy
Accessibility
Installation
Running locally
Testing
Benchmarks
Security
Limitations
Roadmap
License

A judge should understand the project's Snapdragon differentiation in under
60 seconds.

Create architecture diagrams using Mermaid where useful.

==================================================
20. JUDGING EVIDENCE
==================================================

Create:

docs/JUDGING_EVIDENCE.md

Map evidence to:

1. Technical Implementation
2. Application Use Case & Innovation
3. Deployment & Accessibility
4. Presentation & Documentation

For every claim provide:
- implementation path
- test/evidence
- screenshot/artifact if available
- limitation

Never write unsupported marketing claims.

==================================================
21. DEMO MODE
==================================================

Create deterministic demo assets that do not depend on network access.

Include safe sample images where licensing permits.

Demo should work offline after setup/model acquisition.

Create docs/DEMO_SCRIPT.md.

Ideal demonstration:

1. Disconnect Wi-Fi.
2. Launch SightLine.
3. Show hardware/runtime status.
4. Import image/screenshot.
5. Run local visual analysis.
6. Show bounding boxes/text.
7. Open Privacy Shield.
8. Redact sensitive region.
9. Open Performance Lab.
10. Show real provider and benchmark evidence.
11. Explain Snapdragon NPU architecture.

==================================================
22. PERFORMANCE ENGINEERING
==================================================

Measure before optimizing.

Implement warmup.

Benchmark multiple runs.

Report:
- sample count
- warmup count
- median
- mean if useful
- p95
- standard deviation where useful

Do not benchmark UI rendering and call it inference latency.

Separate:
model load
preprocessing
inference
postprocessing
total pipeline

==================================================
23. ERROR EXPERIENCE
==================================================

Errors must be useful.

Examples:

"QNN Execution Provider was not detected. SightLine is using CPU fallback."

"Model could not be loaded. Run scripts/setup_models.py."

"Camera access was denied."

"This file exceeds the configured size limit."

Never silently fail.

==================================================
24. DEVELOPMENT QUALITY
==================================================

Use:
- typing
- linting
- formatting
- modular code
- schemas
- docstrings where useful
- dependency pinning
- clean Git ignore rules

Configure CI for operations that can run on generic GitHub runners.

Do not make CI require Snapdragon hardware.

Separate hardware-specific tests with markers.

==================================================
25. AGENTS.md
==================================================

Create/update AGENTS.md with permanent engineering rules:

- no fabricated evidence
- no AWS
- local-first architecture
- QNN preferred
- CPU fallback
- tests required
- docs updated with architectural changes
- security checks required
- no secrets
- accessibility required
- benchmark claims must be reproducible
- preserve design-system consistency

==================================================
26. BUILD ORDER
==================================================

Do NOT attempt everything simultaneously.

PHASE 0 — REPOSITORY AUDIT
Inspect existing repository.
Report current state.
Do not destroy useful existing work.

PHASE 1 — SCAFFOLD
Create architecture.
Create design system.
Create application shell.
Create test infrastructure.

PHASE 2 — CPU VERTICAL SLICE
Get ONE visual model working end-to-end on CPU:

input
→ preprocessing
→ model
→ postprocessing
→ UI

PHASE 3 — QNN
Implement:
provider detection
QNN initialization
strict mode
fallback
verification

PHASE 4 — PRODUCT FEATURES
Build:
Visual Assist
Screen Lens
Privacy Shield
Performance Lab

Only then add Camera Assist.

PHASE 5 — HARDENING
security
accessibility
error handling
tests
logging

PHASE 6 — QUALCOMM OPTIMIZATION
AI Hub preparation
QNN optimization
real profiling
benchmarking

PHASE 7 — SUBMISSION POLISH
README
screenshots
architecture
demo script
judging evidence
limitations

==================================================
27. DEFINITION OF DONE
==================================================

SightLine is submission-ready only when:

[ ] clean install documented
[ ] application launches
[ ] one visual model works end-to-end
[ ] CPU fallback works
[ ] QNN status is truthfully represented
[ ] NPU execution is verified or explicitly marked unverified
[ ] Visual Assist works
[ ] Privacy Shield works
[ ] Performance Lab uses real measurements
[ ] UI is coherent and responsive
[ ] keyboard navigation works
[ ] errors are handled
[ ] tests pass
[ ] lint passes
[ ] repository contains no secrets
[ ] model licenses documented
[ ] architecture documented
[ ] benchmark methodology documented
[ ] limitations documented
[ ] README complete
[ ] demo script complete
[ ] judging evidence complete

==================================================
28. CURRENT TASK
==================================================

Begin with PHASE 0.

Inspect the entire repository first.

Then produce:

1. repository audit
2. proposed architecture
3. implementation plan
4. dependency plan
5. model recommendation
6. risks/blockers
7. exact Phase 1 changes

After the audit, begin Phase 1 implementation.

Work autonomously through straightforward implementation decisions.

Do not ask me questions unless:
- credentials are genuinely required
- hardware information is required
- a destructive action is required
- model licensing requires a decision
- there are two materially incompatible architectural paths

After every phase:

1. run relevant tests
2. run lint/type checks
3. inspect git diff
4. fix regressions
5. update documentation
6. report exactly what changed
7. report commands executed
8. report actual test results
9. identify remaining blockers
10. propose the next phase

Do not claim completion without verification.

Begin.