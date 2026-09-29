export const MAX_BYTES = 10 * 1024 * 1024;
export const MAX_PIXELS = 24_000_000;

export function validateHeader(bytes, size, mime, name) {
  if (size === 0) throw new Error("This image is empty.");
  if (size > MAX_BYTES) throw new Error("This file exceeds the 10 MB size limit.");
  const png = [137, 80, 78, 71, 13, 10, 26, 10].every((v, i) => bytes[i] === v);
  const jpeg = bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255;
  const extension = name.toLowerCase().split(".").pop();
  const valid = (png && extension === "png" && mime === "image/png") ||
    (jpeg && ["jpg", "jpeg"].includes(extension) && mime === "image/jpeg");
  if (!valid) throw new Error("Choose a PNG or JPEG with matching file type and contents.");
  return png ? "image/png" : "image/jpeg";
}

export function validateDimensions(width, height) {
  if (!Number.isInteger(width) || !Number.isInteger(height) || width < 1 || height < 1 ||
      width * height > MAX_PIXELS || Math.max(width, height) > 16000) {
    throw new Error("Image dimensions are invalid or exceed the 24 megapixel limit.");
  }
}
