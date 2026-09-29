# YOLOX-Nano CPU model card

Official Megvii YOLOX 0.1.1rc0 ONNX release; Apache-2.0. SHA-256 c789161ed43c8269fcd4e67c67eeeb4e80c622da2eb296a20bc6007bd18a0b7d, 3659407 bytes. Source URL in manifest.json. Weights acquired explicitly, not committed.

Input: float32 [1,3,416,416], BGR 0..255, OpenCV linear resize with aspect preservation, top-left placement and padding 114. No normalization. The release asset matches preprocessing at upstream revision 6ddff4824372906469a7fae2dc3206c7aa4bbaee; the old release-tag normalization does not match this asset.

Output: float32 [1,3549,85], raw stride 8/16/32 predictions with 80 COCO classes. Objectness times class score; threshold 0.30; class-agnostic NMS IoU 0.45; boxes mapped/clipped to source pixels, maximum 100 detections.

Tests compare preprocessing and decoding against attributed upstream reference functions. The NASA astronaut fixture produces a person at approximately 0.926 confidence on this CPU. This is a smoke test, not an accuracy evaluation. Scores are not calibrated probabilities; false positives, missed objects, domain shift and small-object limitations apply. No identity recognition or safety-critical use is supported.

QNN model quantization/calibration and cross-provider accuracy validation remain pending. Dimensions alone are insufficient to certify compatibility.
