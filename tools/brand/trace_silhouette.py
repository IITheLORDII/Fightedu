import sys, numpy as np, potrace
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
a = np.array(Image.open(src).convert("RGBA"))[:, :, 3]
mask = a > 110
ys, xs = np.nonzero(mask)
y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
mask = mask[y0:y1 + 1, x0:x1 + 1]
# delikleri doldur (göz gibi küçük boşluklar): dışarıdan erişilemeyen boş pikseller dolu sayılır
from collections import deque
h, w = mask.shape
outside = np.zeros_like(mask)
q = deque([(0, 0)])
pad = np.pad(mask, 1)
outside = np.zeros_like(pad)
q = deque([(0, 0)]); outside[0, 0] = True
H, W = pad.shape
while q:
    y, x = q.popleft()
    for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
        ny, nx = y+dy, x+dx
        if 0 <= ny < H and 0 <= nx < W and not outside[ny, nx] and not pad[ny, nx]:
            outside[ny, nx] = True; q.append((ny, nx))
filled = ~outside[1:-1, 1:-1]
bmp = potrace.Bitmap(~filled)
path = bmp.trace(turdsize=20, alphamax=1.1, opticurve=True, opttolerance=0.4)
parts = []
for curve in path:
    s = curve.start_point
    d = [f"M{s.x:.1f},{s.y:.1f}"]
    for seg in curve.segments:
        if seg.is_corner:
            d.append(f"L{seg.c.x:.1f},{seg.c.y:.1f}L{seg.end_point.x:.1f},{seg.end_point.y:.1f}")
        else:
            d.append(f"C{seg.c1.x:.1f},{seg.c1.y:.1f} {seg.c2.x:.1f},{seg.c2.y:.1f} {seg.end_point.x:.1f},{seg.end_point.y:.1f}")
    d.append("Z")
    parts.append("".join(d))
open(out, "w").write(f'{w} {h}\n' + "".join(parts))
print(w, h, len(parts), sum(len(p) for p in parts))
