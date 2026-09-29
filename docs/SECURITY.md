# Security review

The development host binds only to 127.0.0.1. Exact Host, same-origin and fetch-site checks mitigate cross-site requests and DNS rebinding. Static assets use an allowlist. CSP restricts scripts and connections to self; responses are no-store. No CORS permission is granted.

POST /api/analyze requires a custom header, one bounded Content-Length, PNG/JPEG MIME and a supported provider policy. Transfer encoding is rejected. One analysis at a time is allowed. Server image probing enforces 10 MB, 24 MP and 16000-pixel side limits before full decode, rejects malformed/truncated/mismatched/animated inputs, and handles EXIF orientation. Browser validation provides feedback but is not the trust boundary.

Model acquisition verifies fixed size and SHA-256; verified bytes are passed to the runtime. QNN paths and hashes come from local CLI configuration, never browser input. Only trusted models and vendor runtime DLLs should be configured: these are native-code/parser trust boundaries. Exceptions returned to HTTP clients are sanitized. Images, filenames and tensors are not logged.

Residual risks: Python's threaded HTTP server is a development host, not a hardened distribution. Browser image decoding allocates before dimension validation; timeouts do not terminate native inference already running. The loopback endpoint is not authenticated against other local processes. No penetration test, dependency vulnerability audit or native package signing has been completed. Unit tests exercise request limits and origin protections; they are not a security certification.

## Phase 4 review

Clipboard input uses the same image checks as file import. Clipboard read requires an explicit action; pasted text/HTML is never inserted as markup. Privacy effects operate on bounded pixel crops, with no server upload. Flattened PNG export uses generated names and contains the redacted canvas rather than original bytes. Rendering errors disable export before transformations begin.

Benchmark POST requires the local custom header, JSON MIME, at most 256 bytes and integer counts in fixed ranges. It accepts no model, image, command or output paths. Only generated 32-hex IDs with json/csv suffixes are served from the fixed result directory, with resolved-path and size checks. Outputs contain metadata/timings only. Benchmarks and inference share a lock. Request validation, concurrency, real artifact roundtrips and traversal rejection are tested.

No new third-party dependencies were introduced in Phase 4. The runtime remains a development host; request-rate hardening, native-call isolation and a dependency vulnerability audit are not claimed complete.
