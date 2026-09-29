# AI Hub preparation
No AI Hub jobs have been submitted and no Qualcomm profile evidence exists here.

1. Select/license source weights and pin hashes/revision.
2. Export a fixed-shape model and validate against reference outputs.
3. Authenticate in a separate optional build environment; upload/compile for a named Snapdragon target.
4. Profile and retain genuine job identifiers, device/runtime metadata and raw output.
5. Validate accuracy/output regression with actual inputs and measurements.
6. Download the optimized artifact; record license/hash and deploy locally.
7. Verify QNN HTP execution on the actual Windows target. Remote profiles are not local benchmarks.

AI Hub is an external network operation. Use public or explicitly approved model/input artifacts; never silently upload user screenshots. It is optional and absent from the core application runtime. Store real evidence under `benchmarks/ai_hub/` without credentials or private data.

Strict verification plan: request HTP with a pinned runtime's supported `backend_type=htp` or `QnnHtp.dll` option, set `session.disable_cpu_ep_fallback=1`, prohibit CPU retries and execute a known test input. Retain assignment/profile evidence, validated output and backend/version metadata. QNN enumeration alone does not prove HTP execution. Verify options and Python/wheel compatibility against the actual pinned runtime.

References checked 2026-09-27: [QNN EP documentation](https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html), [Qualcomm models](https://github.com/qualcomm/ai-hub-models), [Yolo-X listing](https://aihub.qualcomm.com/compute/models/yolox).
