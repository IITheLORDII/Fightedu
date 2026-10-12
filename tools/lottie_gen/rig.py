"""İskelet (rig) kinematiği ve Lottie yardımcıları.

Açı kuralı (derece, mutlak/dünya koordinatı):
    0 = yukarı, 90 = ileri (sağ, figürün baktığı yön), 180 = aşağı, 270 = geri.
Poz anahtarları:
    t        : gövde (kalça -> boyun)
    fua, ffa : ön kol üst / ön kol alt (ön = izleyiciye yakın taraf)
    bua, bfa : arka kol üst / alt
    fth, fsh : ön uyluk / ön baldır
    bth, bsh : arka uyluk / baldır
    dx       : kalçanın yatay kayması (px)
    lift     : yerden yükseklik (zıplama) (px)
Figür her karede en alçak noktası zemine değecek şekilde otomatik yerleştirilir.
"""
import math

FPS = 30
W, H = 500, 400
GROUND = 372

TORSO, NECK, HEAD_R = 92, 8, 17
UPPER_ARM, FOREARM = 50, 48
THIGH, SHIN = 64, 62
SHOULDER_DROP = 7      # omuz eklemi boyun noktasının biraz altında
SOLE = 10              # ayak bileğinden tabana
TOE = 24               # ayak bileğinden parmak ucuna
HEEL = 6               # ayak bileğinden topuğun arkasına
FIST_R = 8             # yumruk/eldiven yarıçapı (uç noktası için)
KNEE_R = 10

POSE_KEYS = ["t", "fua", "ffa", "bua", "bfa", "fth", "fsh", "bth", "bsh", "dx", "lift"]


def P(base, **kw):
    d = dict(base)
    d.update(kw)
    return d


def vec(angle_deg, length):
    a = math.radians(angle_deg)
    return math.sin(a) * length, -math.cos(a) * length


def add(p, q):
    return p[0] + q[0], p[1] + q[1]


def joints(pose, glove_r=FIST_R):
    """Kalça (0,0) iken eklem ve uç noktaları (ekran koordinatı, y aşağı)."""
    hip = (0.0, 0.0)
    neck = vec(pose["t"], TORSO)
    shoulder = vec(pose["t"], TORSO - SHOULDER_DROP)
    head_c = add(neck, vec(pose["t"], NECK + HEAD_R))
    pts = {"hip": hip, "neck": neck, "head": head_c}
    for side in ("f", "b"):
        elbow = add(shoulder, vec(pose[side + "ua"], UPPER_ARM))
        hand = add(elbow, vec(pose[side + "fa"], FOREARM))
        fist = add(hand, vec(pose[side + "fa"], glove_r))
        knee = add(hip, vec(pose[side + "th"], THIGH))
        ankle = add(knee, vec(pose[side + "sh"], SHIN))
        sh = pose[side + "sh"]
        sole_c = add(ankle, vec(sh, SOLE))
        toe = add(sole_c, vec(sh - 90, TOE))
        heel = add(sole_c, vec(sh + 90, HEEL))
        pts.update({
            side + "elbow": elbow, side + "hand": hand, side + "fist": fist,
            side + "knee": knee, side + "ankle": ankle, side + "toe": toe, side + "heel": heel,
        })
    return pts


def lowest_y(pose):
    pts = joints(pose)
    ys = [pts["head"][1] + HEAD_R]
    for s in ("f", "b"):
        ys += [pts[s + "toe"][1], pts[s + "heel"][1], pts[s + "knee"][1] + KNEE_R,
               pts[s + "fist"][1], pts[s + "elbow"][1] + 7]
    ys.append(pts["hip"][1] + 14)
    return max(ys)


def hip_position(pose, base_x):
    return [round(base_x + pose["dx"], 1), round(GROUND - lowest_y(pose) - pose["lift"], 1)]


def bezier_ease(u, x1=0.42, y1=0.0, x2=0.58, y2=1.0):
    """Lottie'nin uyguladığı cubic-bezier easing (EASE_OUT/EASE_IN ile aynı)."""
    def coord(s, a, b):
        return 3 * a * s * (1 - s) ** 2 + 3 * b * s * s * (1 - s) + s ** 3
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if coord(mid, x1, x2) < u:
            lo = mid
        else:
            hi = mid
    return coord((lo + hi) / 2, y1, y2)


def pose_at(keys, frame):
    """Anahtar pozlar arasında (Lottie ile aynı easing'le) ara poz."""
    for (f0, p0), (f1, p1) in zip(keys, keys[1:]):
        if f0 <= frame <= f1:
            e = bezier_ease((frame - f0) / (f1 - f0)) if f1 > f0 else 1.0
            return {k: p0[k] + (p1[k] - p0[k]) * e for k in POSE_KEYS}
    return dict(keys[-1][1])


def dense_hip_track(keys, base_x, step=2):
    """Kalça konumu: ara pozları zemine oturtur (geçişlerde ayak zemine girmez)."""
    out = []
    end = keys[-1][0]
    f = 0
    while f < end:
        out.append((f, hip_position(pose_at(keys, f), base_x) + [0]))
        f += step
    out.append((end, hip_position(keys[-1][1], base_x) + [0]))
    return out


def world_points(keys, base_x, frame):
    """Belirli karede tüm noktaların dünya koordinatı (rakip/torba yerleşimi için)."""
    pose = pose_at(keys, frame)
    hx, hy = hip_position(pose, base_x)
    return {k: (hx + x, hy + y) for k, (x, y) in joints(pose).items()}


# --------------------------------------------------------------------------
# Lottie yardımcıları
# --------------------------------------------------------------------------
EASE_OUT = {"x": [0.42], "y": [0]}
EASE_IN = {"x": [0.58], "y": [1]}
LINEAR_OUT = {"x": [0], "y": [0]}
LINEAR_IN = {"x": [1], "y": [1]}


def rgba(hex_color):
    h = hex_color.lstrip("#")
    return [round(int(h[i:i + 2], 16) / 255, 4) for i in (0, 2, 4)] + [1]


def shade(hex_color, factor):
    """factor < 1 koyulaştırır, > 1 açar."""
    h = hex_color.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    if factor <= 1:
        rgb = [int(c * factor) for c in rgb]
    else:
        rgb = [int(c + (255 - c) * (factor - 1)) for c in rgb]
    return "#%02X%02X%02X" % tuple(max(0, min(255, c)) for c in rgb)


def static(v):
    return {"a": 0, "k": v}


def animated(frames_values, dims, linear=False):
    """frames_values: [(frame, [değerler])] -> Lottie animasyonlu özellik."""
    uniq = []
    for f, v in frames_values:
        if uniq and uniq[-1][0] == f:
            uniq[-1] = (f, v)
        else:
            uniq.append((f, v))
    if all(v == uniq[0][1] for _, v in uniq):
        val = uniq[0][1]
        return {"a": 0, "k": val if dims > 1 else val[0]}
    kfs = []
    for i, (f, v) in enumerate(uniq):
        kf = {"t": f, "s": v}
        if i < len(uniq) - 1:
            kf["o"] = LINEAR_OUT if linear else EASE_OUT
            kf["i"] = LINEAR_IN if linear else EASE_IN
        kfs.append(kf)
    return {"a": 1, "k": kfs}


def transform(p, r, s=None, o=None):
    return {
        "o": o or static(100),
        "r": r,
        "p": p,
        "a": static([0, 0, 0]),
        "s": s or static([100, 100, 100]),
    }


def group_transform():
    return {"ty": "tr", "p": static([0, 0]), "a": static([0, 0]), "s": static([100, 100]),
            "r": static(0), "o": static(100), "sk": static(0), "sa": static(0), "nm": "Transform"}


class LayerBuilder:
    def __init__(self, dur):
        self.dur = dur
        self.layers = []
        self.next_ind = 1

    def add(self, name, ty, ks, shapes=None, parent=None):
        ind = self.next_ind
        self.next_ind += 1
        layer = {"ddd": 0, "ind": ind, "ty": ty, "nm": name, "sr": 1, "ks": ks, "ao": 0,
                 "ip": 0, "op": self.dur, "st": 0, "bm": 0}
        if parent is not None:
            layer["parent"] = parent
        if shapes is not None:
            layer["shapes"] = shapes
        self.layers.append(layer)
        return ind

    def by_ind(self, ind):
        return next(layer for layer in self.layers if layer["ind"] == ind)
