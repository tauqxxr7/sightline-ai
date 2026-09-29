// Pure validation and drawing coordinates, shared by the UI and Node tests.
export function validateResult(result, width, height) {
  if (result?.schema_version !== 1 || result.image?.width !== width ||
      result.image?.height !== height ||
      !(result.runtime?.active === "CPUExecutionProvider" ||
        (result.runtime?.active === "QNNExecutionProvider" && result.runtime?.npu_verified === true)) ||
      !Array.isArray(result.detections) || result.detections.length > 100) {
    throw new Error("The analysis response does not match this image or verified session.");
  }
  for (const detection of result.detections) {
    const box = detection.box;
    if (typeof detection.label !== "string" || detection.label.length > 80 ||
        !Number.isInteger(detection.class_id) || detection.class_id < 0 || detection.class_id > 79 ||
        !Number.isFinite(detection.confidence) || detection.confidence < 0 || detection.confidence > 1 ||
        !Array.isArray(box) || box.length !== 4 || !box.every(Number.isFinite) ||
        box[0] < 0 || box[1] < 0 || box[2] > width || box[3] > height ||
        box[2] <= box[0] || box[3] <= box[1]) {
      throw new Error("The analysis returned invalid object coordinates.");
    }
  }
  for (const key of ["preprocessing", "inference", "postprocessing", "total_pipeline"]) {
    if (!Number.isFinite(result.timings_ms?.[key]) || result.timings_ms[key] < 0) {
      throw new Error("The analysis returned invalid timing metadata.");
    }
  }
  if (result.timings_ms.initialization !== null &&
      (!Number.isFinite(result.timings_ms.initialization) || result.timings_ms.initialization < 0)) {
    throw new Error("The analysis returned invalid initialization timing.");
  }
  return result;
}

export function boxRectangle(box) {
  return {x: box[0], y: box[1], width: box[2] - box[0], height: box[3] - box[1]};
}

export function drawDetections(context, detections) {
  context.lineWidth = Math.max(2, context.canvas.width / 300);
  const fontSize = Math.max(14, context.canvas.width / 35);
  context.font = `600 ${fontSize}px sans-serif`;
  detections.forEach((detection, index) => {
    const {x, y, width, height} = boxRectangle(detection.box);
    context.strokeStyle = "#70d5f5";
    context.strokeRect(x, y, width, height);
    const label = `${index + 1}. ${detection.label} ${Math.round(detection.confidence * 100)}%`;
    const labelY = Math.max(fontSize + 6, y);
    context.fillStyle = "#08202b";
    context.fillRect(x, labelY - fontSize - 5, context.measureText(label).width + 12, fontSize + 9);
    context.fillStyle = "#eff4fa";
    context.fillText(label, x + 6, labelY);
  });
}

// A deterministic inventory of model output, not a generated scene description.
export function objectSummary(detections) {
  if (!detections.length) return "No objects met the model threshold. Objects may still be present.";
  const counts = new Map();
  for (const item of detections) counts.set(item.label, (counts.get(item.label) ?? 0) + 1);
  return [...counts].map(([label, count]) => `${label}: ${count}`).join(" · ");
}
