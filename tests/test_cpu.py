import io
import socket
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from app.core.errors import SightLineError
from app.inference.engine import CPUEngine
from app.inference.model import MODEL_BYTES, MODEL_PATH, MODEL_SHA256, verified_model_bytes
from app.inference.postprocess import decode_head, nms, postprocess
from app.inference.preprocess import MAX_BYTES, decode_image, preprocess
from tests.reference.yolox_contract import demo_postprocess, multiclass_nms_class_agnostic, preproc

SAMPLE = Path(__file__).resolve().parents[1] / "assets/samples/astronaut.png"


def image_bytes(mode="RGB", size=(100, 50), color=None, fmt="PNG"):
    output = io.BytesIO()
    Image.new(mode, size, color).save(output, format=fmt)
    return output.getvalue()


@pytest.mark.parametrize("size", [(73, 151), (151, 73), (416, 416)])
def test_preprocessing_matches_pinned_upstream(size):
    bgr = np.random.default_rng(7).integers(0, 256, (*size, 3), dtype=np.uint8)
    actual = preprocess(bgr)
    expected, ratio = preproc(bgr, (416, 416))
    np.testing.assert_array_equal(actual.tensor[0], expected)
    assert actual.ratio == ratio
    assert actual.tensor.shape == (1, 3, 416, 416)
    assert actual.tensor.dtype == np.float32
    assert actual.tensor.flags.c_contiguous


def test_channel_order_padding_and_no_normalization():
    prepared = preprocess(decode_image(image_bytes(color=(255, 0, 0)), "image/png"))
    np.testing.assert_array_equal(prepared.tensor[0, :, 0, 0], [0, 0, 255])
    np.testing.assert_array_equal(prepared.tensor[0, :, 415, 415], [114, 114, 114])


@pytest.mark.parametrize(
    "content,mime",
    [
        (b"", "image/png"),
        (b"invalid", "image/png"),
        (b"GIF89a", "image/gif"),
        (b"x" * (MAX_BYTES + 1), "image/png"),
    ],
    ids=["empty", "malformed", "unsupported", "oversized"],
)
def test_bad_input_rejected(content, mime):
    with pytest.raises(SightLineError):
        decode_image(content, mime)


def test_mime_mismatch_and_truncated_image():
    content = image_bytes()
    with pytest.raises(SightLineError):
        decode_image(content, "image/jpeg")
    with pytest.raises(SightLineError):
        decode_image(content[:30], "image/png")


def test_pixel_limit_before_loading(monkeypatch):
    content = image_bytes(size=(5000, 5000))
    with pytest.raises(SightLineError, match="24 megapixels"):
        decode_image(content, "image/png")


def test_alpha_composited_and_grayscale_supported():
    rgba = decode_image(image_bytes("RGBA", color=(0, 0, 0, 0)), "image/png")
    assert np.all(rgba == 255)
    gray = decode_image(image_bytes("L", color=50), "image/png")
    assert gray.shape == (50, 100, 3)


def test_exif_orientation():
    output = io.BytesIO()
    img = Image.new("RGB", (60, 30), "red")
    exif = Image.Exif()
    exif[274] = 6
    img.save(output, format="JPEG", exif=exif)
    assert decode_image(output.getvalue(), "image/jpeg").shape == (60, 30, 3)


def test_extreme_aspect_rejected():
    with pytest.raises(SightLineError):
        preprocess(np.zeros((1, 2000, 3), dtype=np.uint8))


def test_decoder_reference_and_does_not_mutate():
    raw = np.random.default_rng(8).random((1, 3549, 85), dtype=np.float32)
    unchanged = raw.copy()
    np.testing.assert_allclose(
        decode_head(raw), demo_postprocess(raw.copy(), (416, 416))[0], rtol=1e-6
    )
    np.testing.assert_array_equal(raw, unchanged)


def test_nms_and_empty_output():
    boxes = np.array([[0, 0, 20, 20], [1, 1, 21, 21], [90, 90, 99, 99]], dtype=np.float32)
    assert nms(boxes, np.array([0.9, 0.8, 0.7], dtype=np.float32), 0.45) == [0, 2]
    assert postprocess(np.zeros((1, 3549, 85), dtype=np.float32), 512, 512, 416 / 512) == []


@pytest.mark.parametrize(
    "bad",
    [np.zeros((1, 4, 85), dtype=np.float32), np.full((1, 3549, 85), np.nan, dtype=np.float32)],
)
def test_invalid_model_output_rejected(bad):
    with pytest.raises(SightLineError):
        decode_head(bad)


def test_missing_and_corrupt_artifact(tmp_path):
    with pytest.raises(SightLineError, match="missing"):
        verified_model_bytes(tmp_path / "missing.onnx")
    bad = tmp_path / "bad.onnx"
    bad.write_bytes(b"x" * MODEL_BYTES)
    with pytest.raises(SightLineError, match="checksum"):
        verified_model_bytes(bad)


def test_real_model_load_output_and_warm_reuse_without_network():
    engine = CPUEngine()
    assert engine.snapshot()["last_successful_runtime"] is None
    with patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")):
        first = engine.analyze(SAMPLE.read_bytes(), "image/png")
        second = engine.analyze(SAMPLE.read_bytes(), "image/png")
    assert first["model"]["sha256"] == MODEL_SHA256
    assert first["runtime"]["active"] == "CPUExecutionProvider"
    assert first["run_kind"] == "cold" and second["run_kind"] == "warm"
    assert first["timings_ms"]["initialization"] > 0
    assert second["timings_ms"]["initialization"] is None
    assert first["detections"] == second["detections"]
    person = next(d for d in first["detections"] if d["label"] == "person")
    assert person["confidence"] > 0.8
    assert all(0 <= value <= 512 for value in person["box"])
    assert first["timings_ms"]["inference"] > 0


def test_real_decoder_matches_upstream_reference():
    import onnxruntime as ort

    prepared = preprocess(decode_image(SAMPLE.read_bytes(), "image/png"))
    session = ort.InferenceSession(str(MODEL_PATH), providers=["CPUExecutionProvider"])
    raw = session.run(None, {"images": prepared.tensor})[0]
    prediction = demo_postprocess(raw.copy(), (416, 416))[0]
    box = prediction[:, :4]
    boxes = (
        np.concatenate([box[:, :2] - box[:, 2:] / 2, box[:, :2] + box[:, 2:] / 2], axis=1)
        / prepared.ratio
    )
    ref = multiclass_nms_class_agnostic(boxes, prediction[:, 4:5] * prediction[:, 5:], 0.45, 0.3)
    actual = postprocess(raw, 512, 512, prepared.ratio)
    assert len(actual) == len(ref)
    for actual_row, expected in zip(actual, ref, strict=True):
        np.testing.assert_allclose(actual_row.box, np.clip(expected[:4], 0, 512), atol=1e-3)
        assert actual_row.confidence == pytest.approx(expected[4])
        assert actual_row.class_id == int(expected[5])


def test_engine_missing_model_is_actionable(tmp_path):
    engine = CPUEngine(tmp_path / "missing.onnx")
    with pytest.raises(SightLineError, match="setup_models"):
        engine.analyze(SAMPLE.read_bytes(), "image/png")
    assert engine.snapshot()["last_successful_runtime"] is None
