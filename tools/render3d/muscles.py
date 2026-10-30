"""Anatomik kas hacimleri: gövde ağının dinlenme şekline her kası ayrı bir kabarıklık olarak yontar.

Uzuv kasları kemik çerçevesinde tanımlanır: kemik boyunca konum t (0 = baş, 1 = uç) ve kemik ekseni
etrafında açı (0 = vücudun önü, +90 = dış yan, 180 = arka). Gövde kasları dinlenme koordinatında
elipsoidlerdir. Pozitif yükseklik kas karnı (kabarık), negatif yükseklik kaslar arası oluktur; köşe,
o kemiğe olan deri ağırlığı oranında ve yüzey normali yönünde itilir.
"""
import numpy as np

GAIN = 1.8  # tüm kas yükseklikleri için ortak çarpan

# (kemik, t merkezi, t yarı boyu, açı merkezi, açı yarı genişliği, yükseklik mm)
LIMB = [
    # deltoid: ön, yan ve arka baş -> yuvarlak omuz kapağı; altta kola kaynaşır
    ("upperarm", 0.10, 0.30, 0, 60, 6.0),
    ("upperarm", 0.12, 0.32, 90, 55, 7.5),
    ("upperarm", 0.10, 0.30, 180, 60, 5.5),
    ("upperarm", 0.47, 0.08, 90, 40, -2.0),   # deltoid tutunma çukuru
    # biseps (ön) ve triseps (arka): ayrı karınlar, aralarında iç/dış oluk
    ("upperarm", 0.60, 0.30, -5, 60, 7.0),
    ("upperarm", 0.55, 0.32, 175, 70, 6.0),
    ("upperarm", 0.38, 0.18, 150, 30, 2.5),   # triseps uzun/dış baş kabarıklığı
    ("upperarm", 0.62, 0.30, 90, 16, -3.0),   # dış oluk (biseps-triseps)
    ("upperarm", 0.62, 0.30, -95, 16, -2.5),  # iç oluk
    # önkol: brakioradyalis (dış-ön), fleksörler (iç), ekstansörler (arka-dış); bileğe doğru incelir
    ("lowerarm", 0.22, 0.22, 45, 45, 6.0),
    ("lowerarm", 0.25, 0.25, -60, 55, 4.5),
    ("lowerarm", 0.25, 0.25, 140, 50, 4.0),
    # uyluk: rectus femoris (ön), vastus lateralis (dış), vastus medialis (iç, dizin üstünde damla)
    ("thigh", 0.50, 0.38, 0, 45, 6.0),
    ("thigh", 0.48, 0.38, 75, 45, 7.0),
    ("thigh", 0.80, 0.14, -55, 40, 7.5),
    ("thigh", 0.50, 0.35, 120, 12, -2.5),     # IT bandı oluğu (kuadriseps-hamstring)
    ("thigh", 0.45, 0.38, 180, 60, 4.5),      # hamstringler
    ("thigh", 0.50, 0.30, -100, 14, -2.0),    # iç oluk (adduktor)
    # baldır: gastroknemius iç ve dış başı (iç baş daha aşağı iner), tibialis anterior
    ("calf", 0.25, 0.22, -150, 40, 7.0),
    ("calf", 0.22, 0.18, 150, 35, 5.5),
    ("calf", 0.20, 0.20, 180, 10, -2.0),      # iki baş arası
    ("calf", 0.35, 0.30, 25, 30, 3.0),
]


def _window(x, half):
    """|x| < half içinde cos² penceresi (kenarda 0, merkezde 1)."""
    u = np.clip(np.abs(x) / half, 0.0, 1.0)
    return np.cos(u * np.pi / 2) ** 2


def vertex_normals(verts, faces):
    n = np.zeros_like(verts)
    for f in faces:
        p = verts[f]
        fn = np.cross(p[1] - p[0], p[2] - p[0])
        if len(f) == 4:
            fn = fn + np.cross(p[2] - p[0], p[3] - p[0])
        n[f] += fn
    return n / np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]


def sculpt(base, verts, rig, k=1.0):
    """verts (tüm temel ağ, metre) üzerinde gövde köşelerini kas hacimleriyle yerinde değiştirir."""
    body = base.groups["body"]
    faces = [f for f, g in zip(base.faces, base.face_groups) if g == "body"]
    normals = vertex_normals(verts, faces)
    disp = np.zeros(len(verts))
    w_of = {b: dict((int(vi), w) for vi, w in pairs) for b, pairs in rig.weights.items()}
    fwd0 = np.array([0.0, -1.0, 0.0])
    for bone, tc, th, ac, ah, h in LIMB:
        for s, sx in (("l", 1.0), ("r", -1.0)):
            b = rig.bones[f"{bone}_{s}"]
            hd, tl = np.asarray(b["head"]), np.asarray(b["tail"])
            ax = tl - hd
            L2 = ax @ ax
            a = ax / np.sqrt(L2)
            fwd = fwd0 - a * (fwd0 @ a)
            fwd /= np.linalg.norm(fwd)
            lat = np.cross(a, fwd)
            if lat[0] * sx < 0:
                lat = -lat
            wmap = w_of.get(f"{bone}_{s}", {})
            idx = np.array([vi for vi in wmap if vi in body_set(base)], dtype=np.int64)
            if not len(idx):
                continue
            v = verts[idx] - hd
            t = (v @ ax) / L2
            rad = v - np.outer(v @ a, a)
            ang = np.degrees(np.arctan2(rad @ lat, rad @ fwd))
            da = (ang - ac + 180.0) % 360.0 - 180.0
            w = np.array([wmap[int(i)] for i in idx])
            disp[idx] += h * GAIN * 1e-3 * k * _window(t - tc, th) * _window(da, ah) * w
    for c, r, h in torso_muscles(verts, base, rig, k):
        q = (verts[body] - c) / r
        d2 = (q * q).sum(axis=1)
        disp[body] += h * GAIN * 1e-3 * k * np.clip(1.0 - d2, 0.0, 1.0) ** 2
    # komşu ortalamasıyla yumuşat: kas sınırları keskin basamak olmasın
    nb = _neighbors(len(verts), faces)
    for _ in range(3):
        avg = np.array([disp[n].mean() if len(n) else disp[i] for i, n in enumerate(nb)])
        disp = 0.5 * disp + 0.5 * avg
    verts[body] += normals[body] * disp[body][:, None]
    return verts


_BODY = {}


def body_set(base):
    key = id(base)
    if key not in _BODY:
        _BODY[key] = set(int(i) for i in base.groups["body"])
    return _BODY[key]


def _neighbors(n, faces):
    nb = [set() for _ in range(n)]
    for f in faces:
        for x, y in zip(f, f[1:] + f[:1]):
            nb[x].add(y)
            nb[y].add(x)
    return [np.array(sorted(s), dtype=np.int64) for s in nb]


def torso_muscles(verts, base, rig, k):
    """Gövde kasları: (merkez yüzeyde, yarıçaplar, yükseklik mm)."""
    body = verts[base.groups["body"]]
    torso = body[np.abs(body[:, 0]) < 0.2 * k]

    def surf(x, z, back=False, tol=0.008):
        m = (np.abs(torso[:, 0] - x) < tol * k) & (np.abs(torso[:, 2] - z) < tol * k)
        if not m.any():
            return None
        return torso[m, 1].max() if back else torso[m, 1].min()

    sh = np.asarray(rig.bones["upperarm_l"]["head"])
    neck = np.asarray(rig.bones["neck_01"]["head"])
    hip_z = float(np.asarray(rig.bones["thigh_l"]["head"])[2])
    nip_z = sh[2] - 0.165 * k
    out = []

    def add(x, z, r, h, back=False, sym=True):
        for sx in ((1, -1) if sym and abs(x) > 1e-6 else (1,)):
            y = surf(sx * x, z, back)
            if y is not None:
                out.append((np.array([sx * x, y, z]), np.array(r) * k, h))

    # pektoral: göğüs kası kütlesi, alt kenarı keskin (kütle yukarıda), sternumda oluk
    add(0.07 * k, nip_z + 0.04 * k, (0.075, 0.05, 0.06), 7.0)
    add(0.075 * k, nip_z - 0.035 * k, (0.07, 0.04, 0.012), -3.0)
    add(0.0, nip_z + 0.02 * k, (0.008, 0.05, 0.07), -3.0)
    # trapez: boyundan omuza eğim, sırtta kürek kemikleri arasına
    add(0.06 * k, neck[2] - 0.03 * k, (0.06, 0.06, 0.04), 6.0, back=True)
    add(0.04 * k, sh[2] - 0.08 * k, (0.05, 0.05, 0.08), 3.5, back=True)
    # latissimus: koltuk altından bele kanat
    add(0.12 * k, nip_z - 0.05 * k, (0.05, 0.08, 0.10), 5.0, back=True)
    # omurga oluğu (erector spinae iki yanda kabarık)
    add(0.0, nip_z - 0.08 * k, (0.008, 0.05, 0.2), -3.0, back=True)
    add(0.025 * k, hip_z + 0.10 * k, (0.02, 0.05, 0.12), 3.0, back=True)
    # rectus abdominis: 3 sıra dilim + alt karın; dilim araları ve linea alba oluk
    top, bot = nip_z - 0.075 * k, hip_z + 0.035 * k
    span = top - bot
    for f in (0.10, 0.30, 0.50):
        add(0.03 * k, top - f * span, (0.024, 0.04, 0.026), 3.5)
    add(0.028 * k, top - 0.80 * span, (0.026, 0.04, 0.05), 2.0)
    add(0.0, top - 0.33 * span, (0.006, 0.04, 0.13), -2.5)
    for f in (0.20, 0.40):
        add(0.03 * k, top - f * span, (0.03, 0.04, 0.006), -2.0)
    # oblik ve serratus
    add(0.10 * k, top - 0.45 * span, (0.03, 0.05, 0.07), 2.5)
    for j in range(3):
        add(0.125 * k, nip_z - (0.03 + 0.03 * j) * k, (0.014, 0.05, 0.009), 2.0)
    # kalça kası (gluteus) arkada
    add(0.08 * k, hip_z - 0.02 * k, (0.08, 0.08, 0.08), 4.0, back=True)
    return out
