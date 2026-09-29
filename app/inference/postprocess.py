"""Decode raw YOLOX heads, confidence filter, NMS and original-image coordinates."""

from dataclasses import asdict, dataclass

import numpy as np
from numpy.typing import NDArray

from app.core.errors import SightLineError
from app.inference.labels import COCO_CLASSES
from app.inference.model import OUTPUT_SHAPE


@dataclass(frozen=True)
class Detection:
    label: str
    class_id: int
    confidence: float
    box: tuple[float, float, float, float]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def decode_head(output: NDArray[np.float32]) -> NDArray[np.float32]:
    if output.shape != OUTPUT_SHAPE or not np.isfinite(output).all():
        raise SightLineError("model_output", "Model returned an invalid output tensor.", 503)
    predictions = output.copy()[0]
    offset = 0
    for stride in (8, 16, 32):
        size = 416 // stride
        x, y = np.meshgrid(np.arange(size), np.arange(size))
        grid = np.stack((x, y), axis=-1).reshape(-1, 2)
        count = size * size
        values = predictions[offset : offset + count]
        values[:, :2] = (values[:, :2] + grid) * stride
        with np.errstate(over="ignore", invalid="ignore"):
            values[:, 2:4] = np.exp(values[:, 2:4]) * stride
        offset += count
    if (
        not np.isfinite(predictions).all()
        or np.any(predictions[:, 4:] < 0)
        or np.any(predictions[:, 4:] > 1)
    ):
        raise SightLineError(
            "model_output", "Model output values are outside the supported contract.", 503
        )
    return np.asarray(predictions, dtype=np.float32)


def nms(boxes: NDArray[np.float32], scores: NDArray[np.float32], threshold: float) -> list[int]:
    """Class-agnostic NMS, matching the pinned reference's inclusive pixel IoU."""
    order = scores.argsort(kind="stable")[::-1]
    keep: list[int] = []
    while order.size:
        i = int(order[0])
        keep.append(i)
        other = order[1:]
        top_left = np.maximum(boxes[i, :2], boxes[other, :2])
        bottom_right = np.minimum(boxes[i, 2:], boxes[other, 2:])
        intersection = np.prod(np.maximum(0, bottom_right - top_left + 1), axis=1)
        area = np.prod(np.maximum(0, boxes[:, 2:] - boxes[:, :2] + 1), axis=1)
        union = area[i] + area[other] - intersection
        iou = intersection / np.maximum(union, np.finfo(np.float32).eps)
        order = other[iou <= threshold]
    return keep


def postprocess(
    output: NDArray[np.float32],
    width: int,
    height: int,
    ratio: float,
    confidence: float = 0.3,
    iou: float = 0.45,
) -> list[Detection]:
    if (
        not 0 < confidence <= 1
        or not 0 < iou <= 1
        or not np.isfinite(ratio)
        or ratio <= 0
        or min(width, height) <= 0
    ):
        raise ValueError("Invalid postprocessing parameters")
    predictions = decode_head(output)
    scores = predictions[:, 4:5] * predictions[:, 5:]
    classes = scores.argmax(axis=1)
    best = scores[np.arange(len(scores)), classes]
    mask = best > confidence
    raw = predictions[mask, :4]
    classes, best = classes[mask], best[mask]
    boxes = (
        np.concatenate((raw[:, :2] - raw[:, 2:] / 2, raw[:, :2] + raw[:, 2:] / 2), axis=1) / ratio
    )
    result = []
    for i in nms(np.asarray(boxes, dtype=np.float32), best, iou)[:100]:
        x1, y1, x2, y2 = boxes[i]
        box = (
            float(np.clip(x1, 0, width)),
            float(np.clip(y1, 0, height)),
            float(np.clip(x2, 0, width)),
            float(np.clip(y2, 0, height)),
        )
        if box[2] <= box[0] or box[3] <= box[1]:
            continue
        cls = int(classes[i])
        result.append(Detection(COCO_CLASSES[cls], cls, float(best[i]), box))
    return result
