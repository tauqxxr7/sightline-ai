"""Safe decode and pinned YOLOX reference preprocessing for the released ONNX artifact."""

import io
import warnings
from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.errors import SightLineError

MAX_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 24_000_000
MAX_SIDE = 16000


@dataclass(frozen=True)
class PreparedImage:
    tensor: NDArray[np.float32]
    width: int
    height: int
    ratio: float


def decode_image(content: bytes, mime: str) -> NDArray[np.uint8]:
    if not content or len(content) > MAX_BYTES:
        raise SightLineError("image_size", "Choose a nonempty image no larger than 10 MB.", 413)
    expected = {"image/png": "PNG", "image/jpeg": "JPEG"}.get(mime)
    if expected is None:
        raise SightLineError("image_type", "Only PNG and JPEG images are supported.", 415)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as probe:
                width, height = probe.size
                if probe.format != expected:
                    raise SightLineError(
                        "image_type", "Image contents do not match the declared type.", 415
                    )
                if width * height > MAX_PIXELS or max(width, height) > MAX_SIDE:
                    raise SightLineError(
                        "image_dimensions", "Image exceeds 24 megapixels or 16000 pixels per side."
                    )
                if getattr(probe, "n_frames", 1) != 1:
                    raise SightLineError(
                        "image_frames", "Choose a single-frame image; animated PNG is unsupported."
                    )
                probe.verify()
            with Image.open(io.BytesIO(content)) as source:
                normalized = ImageOps.exif_transpose(source)
                rgba = normalized.convert("RGBA")
                background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                rgb = Image.alpha_composite(background, rgba).convert("RGB")
                return np.ascontiguousarray(np.asarray(rgb, dtype=np.uint8)[:, :, ::-1])
    except SightLineError:
        raise
    except (
        OSError,
        ValueError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise SightLineError(
            "image_decode", "This image is damaged or cannot be decoded safely."
        ) from exc


def preprocess(bgr: NDArray[np.uint8]) -> PreparedImage:
    if bgr.ndim != 3 or bgr.shape[2] != 3 or bgr.dtype != np.uint8:
        raise SightLineError("image_shape", "Decoded image must have three 8-bit channels.")
    height, width = bgr.shape[:2]
    if not width or not height:
        raise SightLineError("image_dimensions", "Image dimensions must be positive.")
    ratio = min(416 / height, 416 / width)
    resized_width, resized_height = int(width * ratio), int(height * ratio)
    if min(resized_width, resized_height) < 1:
        raise SightLineError(
            "image_aspect", "Image is too narrow for this model. Crop it before analysis."
        )
    # Matching source revision 6ddff482: bilinear resize, top-left pad 114,
    # BGR values 0..255 with NO normalization, then contiguous NCHW float32.
    # The older release tag's normalized RGB code does not match this artifact.
    padded = np.full((416, 416, 3), 114, dtype=np.uint8)
    padded[:resized_height, :resized_width] = cv2.resize(
        bgr, (resized_width, resized_height), interpolation=cv2.INTER_LINEAR
    ).astype(np.uint8)
    tensor = np.ascontiguousarray(padded.transpose(2, 0, 1)[None], dtype=np.float32)
    return PreparedImage(tensor, width, height, ratio)
