"""Ortografik kamera ve 2B bezier yol (Lottie 'sh') oluşturucuları.

Kamera, sahneyi yatayda 'az' (derece) ve dikeyde 'el' (derece) açısından görür:
az = 0 → tam yandan (sporcunun sağ tarafından, sporcu ekranda sağa bakar);
az > 0 → kamera sporcunun önüne doğru döner (göğüs daha çok görünür).
"""
import math

from mathx import cross, dot, unit

K = 0.5523


class Camera:
    def __init__(self, az=20.0, el=7.0):
        a, e = math.radians(az), math.radians(el)
        # sahneden kameraya doğru birim vektör
        self.v = (math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e))
        self.right = unit(cross((0.0, 1.0, 0.0), self.v))
        self.up = cross(self.v, self.right)
        self.scale = 1.4
        self.ox = 250.0
        self.oy = 200.0

    def raw(self, p):
        return (dot(p, self.right), -dot(p, self.up))

    def depth(self, p):
        """Büyük = kameraya yakın."""
        return dot(p, self.v)

    def project(self, p):
        x, y = self.raw(p)
        return (x * self.scale + self.ox, y * self.scale + self.oy)

    def radius(self, r):
        return r * self.scale

    def fit(self, raw_pts, width, height, margin=18.0, bottom=30.0, max_scale=1.6):
        xs = [p[0] for p in raw_pts]
        ys = [p[1] for p in raw_pts]
        bw = max(xs) - min(xs)
        bh = max(ys) - min(ys)
        s = min(max_scale, (width - 2 * margin) / max(bw, 1.0), (height - margin - bottom) / max(bh, 1.0))
        self.scale = s
        self.ox = width / 2 - s * (min(xs) + max(xs)) / 2
        self.oy = (height - bottom) - s * max(ys)


# --------------------------------------------------------------------------
# 2B yollar: {"v": [(x,y)...], "i": [...], "o": [...], "c": bool}
# Kapalı yolların hepsi aynı yöne çevrilir (orient); böylece aynı dolguyu paylaşan yollar
# (birleşim) 'nonzero' kuralıyla boşluksuz birleşir.
# --------------------------------------------------------------------------
def ellipse(c, a, b):
    """Merkez c, eşlenik yarı eksen vektörleri a ve b olan elips (4 köşe)."""
    vs, ins, outs = [], [], []
    for k in range(4):
        t = -k * math.pi / 2
        ct, st = math.cos(t), math.sin(t)
        p = (c[0] + a[0] * ct + b[0] * st, c[1] + a[1] * ct + b[1] * st)
        dv = (-a[0] * st + b[0] * ct, -a[1] * st + b[1] * ct)
        # azalan parametre yönünde ilerliyoruz -> teğet işareti ters
        vs.append(p)
        outs.append((-dv[0] * K, -dv[1] * K))
        ins.append((dv[0] * K, dv[1] * K))
    path = {"v": vs, "i": ins, "o": outs, "c": True}
    return orient(path)


def signed_area(vs):
    s = 0.0
    n = len(vs)
    for k in range(n):
        x0, y0 = vs[k]
        x1, y1 = vs[(k + 1) % n]
        s += x0 * y1 - x1 * y0
    return s / 2.0


def reverse(path):
    vs = list(reversed(path["v"]))
    ins = list(reversed(path["o"]))
    outs = list(reversed(path["i"]))
    return {"v": vs, "i": ins, "o": outs, "c": path["c"]}


def orient(path):
    """Kapalı yolu standart yöne çevir (pozitif alan = ekranda saat yönü; Lottie 'el' ile aynı).
    Aynı dolguyu paylaşan yolların aynı yönde olması, birleşimde boşluk oluşmamasını sağlar."""
    if path["c"] and signed_area(path["v"]) < 0:
        return reverse(path)
    return path


def smooth(points, closed=True, tension=1.0):
    n = len(points)
    ins, outs = [], []
    for k in range(n):
        if closed:
            p0, p2 = points[(k - 1) % n], points[(k + 1) % n]
        else:
            p0, p2 = points[max(k - 1, 0)], points[min(k + 1, n - 1)]
        tx = (p2[0] - p0[0]) / 6.0 * tension
        ty = (p2[1] - p0[1]) / 6.0 * tension
        ins.append((-tx, -ty))
        outs.append((tx, ty))
    path = {"v": list(points), "i": ins, "o": outs, "c": closed}
    return orient(path) if closed else path


def polygon(points):
    z = [(0.0, 0.0)] * len(points)
    return orient({"v": list(points), "i": list(z), "o": list(z), "c": True})
