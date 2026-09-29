export function regionBounds(x, y, width, height, imageWidth, imageHeight) {
  if (![x,y,width,height,imageWidth,imageHeight].every(Number.isInteger) ||
      x < 0 || y < 0 || width < 1 || height < 1 || x + width > imageWidth || y + height > imageHeight) {
    throw new Error("Enter whole-pixel coordinates fully inside the image with positive width and height.");
  }
  return {x,y,width,height};
}

export function dragBounds(start, end, width, height) {
  const clamp = (n, max) => Math.max(0, Math.min(max, Math.round(n)));
  const x = clamp(Math.min(start.x,end.x),width), y = clamp(Math.min(start.y,end.y),height);
  return regionBounds(x,y,clamp(Math.max(start.x,end.x),width)-x,
    clamp(Math.max(start.y,end.y),height)-y,width,height);
}

// Operates only on the selected crop. Opaque output; never mutates source pixels.
export function transformPixels(source, width, height, mode) {
  if (!Number.isInteger(width) || !Number.isInteger(height) || width < 1 || height < 1 ||
      width * height > 6000000 || source.length !== width * height * 4 ||
      !["solid","pixelate","blur"].includes(mode)) throw new Error("Invalid redaction region.");
  let data = new Uint8ClampedArray(source);
  if (mode === "solid") {
    for (let i=0; i<data.length; i+=4) { data[i]=data[i+1]=data[i+2]=0; data[i+3]=255; }
    return data;
  }
  if (mode === "pixelate") {
    const block = 16;
    for (let y=0; y<height; y+=block) for (let x=0; x<width; x+=block) {
      const right=Math.min(width,x+block), bottom=Math.min(height,y+block), sums=[0,0,0];
      for (let yy=y; yy<bottom; yy++) for (let xx=x; xx<right; xx++) {
        const i=(yy*width+xx)*4; for (let c=0;c<3;c++) sums[c]+=data[i+c];
      }
      const count=(right-x)*(bottom-y);
      for (let yy=y; yy<bottom; yy++) for (let xx=x; xx<right; xx++) {
        const i=(yy*width+xx)*4;
        for (let c=0;c<3;c++) data[i+c]=Math.round(sums[c]/count);
        data[i+3]=255;
      }
    }
    return data;
  }
  // Three separable box passes approximate a blur. Clamped crop edges prevent bleed.
  const radius=12, span=radius*2+1;
  for (let pass=0;pass<3;pass++) for (const horizontal of [true,false]) {
    const next=new Uint8ClampedArray(data.length);
    const lines=horizontal?height:width, length=horizontal?width:height;
    const index=(line,pos) => (horizontal ? line*width+pos : pos*width+line)*4;
    for (let line=0;line<lines;line++) {
      const sums=[0,0,0];
      for(let k=-radius;k<=radius;k++) {
        const i=index(line,Math.max(0,Math.min(length-1,k)));
        for(let c=0;c<3;c++) sums[c]+=data[i+c];
      }
      for(let pos=0;pos<length;pos++) {
        const i=index(line,pos);
        for(let c=0;c<3;c++) next[i+c]=Math.round(sums[c]/span);
        next[i+3]=255;
        const remove=index(line,Math.max(0,pos-radius));
        const add=index(line,Math.min(length-1,pos+radius+1));
        for(let c=0;c<3;c++) sums[c]+=data[add+c]-data[remove+c];
      }
    }
    data=next;
  }
  return data;
}
