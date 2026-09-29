export async function readClipboardImage(clipboard) {
  if (!clipboard?.read) throw new Error("Clipboard reading is unavailable in this browser. Paste an image with Ctrl+V or import a screenshot file.");
  let items;
  try { items = await clipboard.read(); }
  catch { throw new Error("Clipboard access was denied or unavailable. Paste an image with Ctrl+V or import a screenshot file."); }
  for (const item of items) {
    const type = ["image/png","image/jpeg"].find(type => item.types.includes(type));
    if (type) return clipboardFile(await item.getType(type), type);
  }
  throw new Error("The clipboard contains no PNG or JPEG image. Copy an image, then try again.");
}
export function clipboardFile(blob, type = blob.type) {
  if (!["image/png","image/jpeg"].includes(type)) throw new Error("Clipboard image must be PNG or JPEG.");
  return new File([blob], type === "image/png" ? "clipboard.png" : "clipboard.jpg", {type});
}
