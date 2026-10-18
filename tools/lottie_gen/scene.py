"""Bir hareketi (3B pozlar) Lottie JSON'a dönüştüren sahne derleyicisi.

- Her kare için iskelet çözülür, figür kameraya göre 2B yollara çevrilir.
- Gövde parçası grupları her karede derinliğe göre sıralanır; sıra değiştiği anlarda
  Lottie'de aynı grup 'precomp' örnekleriyle farklı katman sıralarında gösterilir.
- Animasyonlu yollar, doğrusal enterpolasyonla hata payı içinde kalacak en az keyframe'e indirilir.
"""
import math

from camera import Camera, ellipse, polygon, smooth
from figure import FigureRenderer, shade
from mathx import add, dot, lerp, madd, mul, sub, unit
from skeleton import Base, Skeleton, Track

FPS = 30
W, H = 500, 400
TOL = 0.8             # keyframe azaltma hata payı (px)
SPEED_TOL = 0.12      # hız başına ek hata payı (px / (px/kare))
ACCENTS = {"boxing": "#D32F2F", "kickboxing": "#1565C0", "wrestling": "#2E7D32",
           "taekwondo": "#6A1B9A", "general": "#EF6C00"}
FLOORS = {"boxing": "#E2DED6", "kickboxing": "#DCE0E3", "wrestling": "#EDCB5C",
          "taekwondo": "#C7D5EA", "general": "#DCE0E3"}
HIT_PAD = {"hand": 6.0, "ankle": 4.0, "ball": 3.2, "heel": 4.0, "knee": 6.0, "toe": 2.4, "shin": 5.0}


# --------------------------------------------------------------------------
# Lottie yardımcıları
# --------------------------------------------------------------------------
def rgba(h):
    h = h.lstrip("#")
    return [round(int(h[i:i + 2], 16) / 255, 4) for i in (0, 2, 4)] + [1]


def static(v):
    return {"a": 0, "k": v}


def tr(opacity=None):
    return {"ty": "tr", "p": static([0, 0]), "a": static([0, 0]), "s": static([100, 100]),
            "r": static(0), "o": opacity or static(100)}


def layer_ks(opacity=None, pos=None, scale=None):
    return {"o": opacity or static(100), "r": static(0), "p": pos or static([0, 0, 0]),
            "a": static([0, 0, 0]), "s": scale or static([100, 100, 100])}


def r1(x):
    v = round(x, 1)
    return 0 if v == 0 else (int(v) if v == int(v) else v)


def flat(path):
    out = []
    for key in ("v", "i", "o"):
        for x, y in path[key]:
            out.append(x)
            out.append(y)
    return out


def r0(x):
    return int(round(x))


def unflat(vals, n, closed):
    pts = [(vals[2 * k], vals[2 * k + 1]) for k in range(3 * n)]
    return {"v": [[r1(x), r1(y)] for x, y in pts[:n]],
            "i": [[r0(x), r0(y)] for x, y in pts[n:2 * n]],
            "o": [[r0(x), r0(y)] for x, y in pts[2 * n:]], "c": closed}


def reduce_keys(series, tol=TOL):
    """Douglas–Peucker (zamanda): doğrusal enterpolasyonla tol içinde kalan en az kare."""
    n = len(series)
    keep = {0, n - 1}
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        va, vb = series[a], series[b]
        worst, wi = -1.0, None
        for k in range(a + 1, b):
            t = (k - a) / (b - a)
            vk = series[k]
            err = 0.0
            for i in range(len(vk)):
                e = abs(vk[i] - (va[i] + (vb[i] - va[i]) * t))
                if e > err:
                    err = e
            if err > worst:
                worst, wi = err, k
        if worst > tol:
            keep.add(wi)
            stack.append((a, wi))
            stack.append((wi, b))
    return sorted(keep)


def animated_scalar(values, tol=0.5, hold=False):
    """values: kare başına sayı (ya da liste)."""
    vals = [v if isinstance(v, (list, tuple)) else [v] for v in values]
    if all(max(abs(a - b) for a, b in zip(vals[0], v)) < 1e-6 for v in vals):
        v0 = [r1(x) for x in vals[0]]
        return static(v0 if len(v0) > 1 else v0[0])
    if hold:
        kfs = []
        prev = None
        for t, v in enumerate(vals):
            if v != prev:
                kfs.append({"t": t, "s": [r1(x) for x in v], "h": 1})
                prev = v
        return {"a": 1, "k": kfs}
    keys = reduce_keys(vals, tol)
    kfs = []
    for idx, k in enumerate(keys):
        kf = {"t": k, "s": [r1(x) for x in vals[k]]}
        if idx < len(keys) - 1:
            kf["i"] = {"x": [1], "y": [1]}
            kf["o"] = {"x": [0], "y": [0]}
        kfs.append(kf)
    return {"a": 1, "k": kfs}


DETAIL_ITEMS = ("eye", "brow", "mouth", "ear", "pec", "abs", "cuff", "lapel", "logo", "highlight", "band", "sole")


def ease_eval(oy, iy, u):
    """x kontrol noktaları 1/3 ve 2/3 olan kübik bezier easing: zaman doğrusal, değer kübik."""
    v = 1.0 - u
    return 3 * v * v * u * round(oy, 2) + 3 * v * u * u * round(iy, 2) + u * u * u


def fit_eased(series, tol, slopes=None):
    """Çok boyutlu seri (kare başına liste) için en az keyframe + segment easing'i.

    Her segmentte değer = a + (b - a) * E(u); E, uç noktalardaki eğimlerden (Hermite) türetilir.
    Döner: [(kare, (oy, iy))]  (son keyframe için easing None)."""
    n = len(series)
    dims = len(series[0])
    if slopes is None:
        slopes = []
        for k in range(n):
            km = k - 1 if k > 0 else n - 2
            kp = k + 1 if k < n - 1 else 1
            slopes.append([(series[kp][d] - series[km][d]) / 2.0 for d in range(dims)])

    def seg_ease(a, b):
        # en çok değişen boyutun eğimlerinden easing
        best, dmax = 0, -1.0
        for d in range(dims):
            delta = abs(series[b][d] - series[a][d])
            if delta > dmax:
                best, dmax = d, delta
        delta = series[b][best] - series[a][best]
        if abs(delta) < 1e-6:
            return (0.0, 1.0)
        h = b - a
        s0 = slopes[a][best] * h / delta
        s1 = slopes[b][best] * h / delta
        s0 = max(-1.5, min(4.5, s0))
        s1 = max(-1.5, min(4.5, s1))
        return (s0 / 3.0, 1.0 - s1 / 3.0)

    # hızlı hareket eden karelerde (hareket bulanıklığı) daha büyük hata payı
    allow = [tol + SPEED_TOL * max(abs(x) for x in slopes[k]) for k in range(n)]

    def seg_err(a, b):
        oy, iy = seg_ease(a, b)
        worst, wi = 0.0, None
        va, vb = series[a], series[b]
        for k in range(a + 1, b):
            e = ease_eval(oy, iy, (k - a) / (b - a))
            vk = series[k]
            for d in range(dims):
                err = abs(vk[d] - (va[d] + (vb[d] - va[d]) * e)) / allow[k]
                if err > worst:
                    worst, wi = err, k
        return worst, wi

    keep = {0, n - 1}
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        worst, wi = seg_err(a, b)
        if worst > 1.0:
            keep.add(wi)
            stack.append((a, wi))
            stack.append((wi, b))
    keys = sorted(keep)
    out = []
    for idx, k in enumerate(keys):
        out.append((k, seg_ease(k, keys[idx + 1]) if idx < len(keys) - 1 else None))
    return out


def static_of(v):
    """Tek boyutlu özelliklerin sabit değeri sayı olmalı (liste değil)."""
    if isinstance(v, list) and len(v) == 1:
        return static(v[0])
    return static(v)


def prop(series, tol, fmt, scale=None, array_ease=True):
    """series: kare başına liste. fmt: liste -> Lottie 's' değeri. scale: hata ölçeği (boyut başına)."""
    if all(max(abs(a - b) for a, b in zip(series[0], v)) < 1e-6 for v in series):
        return static_of(fmt(series[0]))
    sc = scale or [1.0] * len(series[0])
    scaled = [[v[d] * sc[d] for d in range(len(v))] for v in series]
    keys = fit_eased(scaled, tol)
    if len(keys) == 2 and all(max(abs(a - b) for a, b in zip(scaled[0], v)) < tol * 0.5 for v in scaled):
        return static_of(fmt(series[0]))
    kfs = []
    for k, ease in keys:
        kf = {"t": k, "s": fmt(series[k])}
        if ease is not None:
            oy, iy = round(ease[0], 2), round(ease[1], 2)
            if array_ease:
                kf["o"] = {"x": [0.33], "y": [oy]}
                kf["i"] = {"x": [0.67], "y": [iy]}
            else:
                kf["o"] = {"x": 0.33, "y": oy}
                kf["i"] = {"x": 0.67, "y": iy}
        kfs.append(kf)
    return {"a": 1, "k": kfs}


def pos2(xs, ys, tol):
    """2B konum (x ve y aynı keyframe/easing ile)."""
    return prop([[x, y] for x, y in zip(xs, ys)], tol, lambda v: [r1(v[0]), r1(v[1])], array_ease=False)


def tr_full(p=None, r=None, s=None):
    return {"ty": "tr", "p": p or static([0, 0]), "a": static([0, 0]), "s": s or static([100, 100]),
            "r": r or static(0), "o": static(100)}


def cap_series(series):
    """('cap', A, ra, B, rb) kareleri -> (ax, ay, açı°, L) (açı sürekli)."""
    out = []
    prev = None
    for _t, a, _ra, b, _rb in series:
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        th = math.degrees(math.atan2(dy, dx)) if L > 0.3 else (prev[2] if prev else 0.0)
        if prev is not None:
            while th - prev[2] > 180:
                th -= 360
            while th - prev[2] < -180:
                th += 360
        cur = (a[0], a[1], th, L)
        out.append(cur)
        prev = cur
    return out


def cap_lottie(name, series, tol):
    ra, rb = series[0][2], series[0][4]
    vals = cap_series(series)
    xs = [v[0] for v in vals]
    ys = [v[1] for v in vals]
    ths = [[v[2]] for v in vals]
    Ls = [[v[3]] for v in vals]
    lmax = max(v[3] for v in vals) + rb
    rot = prop(ths, tol, lambda v: [r1(v[0])], scale=[math.radians(1) * max(lmax, 1.0)])
    trap = {"v": [[0, r1(-ra)], [1, r1(-rb)], [1, r1(rb)], [0, r1(ra)]],
            "i": [[0, 0]] * 4, "o": [[0, 0]] * 4, "c": True}
    return {"ty": "gr", "nm": name, "it": [
        {"ty": "el", "nm": "a", "p": static([0, 0]), "s": static([r1(2 * ra), r1(2 * ra)]), "d": 1},
        {"ty": "el", "nm": "b", "p": prop(Ls, tol, lambda v: [r1(v[0]), 0], array_ease=False),
         "s": static([r1(2 * rb), r1(2 * rb)]), "d": 1},
        {"ty": "gr", "nm": "side", "it": [
            {"ty": "sh", "ks": static(trap)},
            tr_full(s=prop(Ls, tol, lambda v: [r1(max(v[0], 0.01) * 100), 100], array_ease=False))]},
        tr_full(p=pos2(xs, ys, tol), r=rot),
    ]}


def circ_lottie(name, series, tol):
    r = series[0][2]
    xs = [c[0] for _t, c, _r in series]
    ys = [c[1] for _t, c, _r in series]
    return {"ty": "gr", "nm": name, "it": [
        {"ty": "el", "nm": "c", "p": static([0, 0]), "s": static([r1(2 * r), r1(2 * r)]), "d": 1},
        tr_full(p=pos2(xs, ys, tol))]}


def animated_path(paths, tol=TOL):
    n = len(paths[0]["v"])
    closed = paths[0]["c"]
    for p in paths:
        if len(p["v"]) != n:
            raise ValueError("yol köşe sayısı kareler arasında değişti")
    series = [flat(p) for p in paths]
    return prop(series, tol, lambda v: [unflat(v, n, closed)], array_ease=False)


def item_to_lottie(name, frames):
    """frames: kare başına öğe sözlüğü (aynı yapı). Lottie 'gr' döner."""
    first = frames[0]
    vis = [f["visible"] for f in frames]
    nprims = len(first["prims"])
    series = [[f["prims"][k] for f in frames] for k in range(nprims)]
    # görünmez karelerde veriyi komşu görünür kareden kopyala (gereksiz keyframe olmasın)
    if any(vis) and not all(vis):
        filled = []
        last = None
        for t, v in enumerate(vis):
            if v:
                last = t
            filled.append(last)
        nxt = None
        for t in range(len(vis) - 1, -1, -1):
            if vis[t]:
                nxt = t
            if filled[t] is None:
                filled[t] = nxt
        for k in range(nprims):
            series[k] = [series[k][filled[t]] for t in range(len(vis))]
    tol = 1.1 if name.startswith(DETAIL_ITEMS) else TOL
    it = []
    for k in range(nprims):
        kind = series[k][0][0]
        if kind == "cap":
            it.append(cap_lottie(f"c{k}", series[k], tol))
        elif kind == "circ":
            it.append(circ_lottie(f"s{k}", series[k], tol))
        else:
            it.append({"ty": "sh", "nm": f"p{k}", "ks": animated_path([pr[1] for pr in series[k]], tol)})
    if first["kind"] == "line":
        it.append({"ty": "st", "nm": "line", "c": static(rgba(first["line"])), "o": static(100),
                   "w": static(r1(first["width"])), "lc": 2, "lj": 2, "ml": 4})
    else:
        it.append({"ty": "fl", "nm": "fill", "c": static(rgba(first["fill"])), "o": static(100), "r": 1})
        if first["line"] and first["width"] > 0:
            it.append({"ty": "st", "nm": "outline", "c": static(rgba(first["line"])), "o": static(100),
                       "w": static(r1(first["width"])), "lc": 2, "lj": 2, "ml": 4})
    op = animated_scalar([100 if v else 0 for v in vis], hold=True)
    it.append(tr(op))
    return {"ty": "gr", "nm": name, "np": nprims, "it": it}


def items_bbox(items):
    xs, ys = [], []
    for it in items:
        if not it.get("visible", True):
            continue
        for pr in it["prims"]:
            if pr[0] == "cap":
                _k, a, ra, b, rb = pr
                xs += [a[0] - ra, a[0] + ra, b[0] - rb, b[0] + rb]
                ys += [a[1] - ra, a[1] + ra, b[1] - rb, b[1] + rb]
            elif pr[0] == "circ":
                _k, c, r = pr
                xs += [c[0] - r, c[0] + r]
                ys += [c[1] - r, c[1] + r]
            else:
                for x, y in pr[1]["v"]:
                    xs.append(x)
                    ys.append(y)
    if not xs:
        return (0.0, 0.0, -1.0, -1.0)
    return (min(xs), min(ys), max(xs), max(ys))


def boxes_overlap(a, b, pad=2.0):
    return not (a[2] + pad < b[0] or b[2] + pad < a[0] or a[3] + pad < b[1] or b[3] + pad < a[1])


def shape_layer(name, shapes, dur, ind=1, ks=None):
    return {"ddd": 0, "ind": ind, "ty": 4, "nm": name, "sr": 1, "ks": ks or layer_ks(), "ao": 0,
            "shapes": shapes, "ip": 0, "op": dur, "st": 0, "bm": 0}


# --------------------------------------------------------------------------
# Sahne
# --------------------------------------------------------------------------
class Move:
    def __init__(self, sport, dur, fig, cam=None, target=None, opp=None, opp_dist=None, hits=(),
                 trails=None, fighter_bias=25.0, look=None, opp_mirror=True, rope=None):
        self.sport = sport
        self.dur = dur
        self.fig = fig
        self.cam = dict(az=20.0, el=7.0)
        self.cam.update(cam or {})
        self.target = target
        self.opp = opp
        self.opp_dist = opp_dist
        self.hits = list(hits)
        self.trails = trails
        self.fighter_bias = fighter_bias
        self.look = look
        self.opp_mirror = opp_mirror
        self.rope = rope          # ip atlama: ipin ayak altından geçtiği kare


def point_pad(name):
    for k, v in HIT_PAD.items():
        if name.endswith(k):
            return v
    return 3.0


class SceneBuilder:
    def __init__(self, move_id, mv):
        self.id = move_id
        self.mv = mv
        self.dur = mv.dur
        self.accent = ACCENTS[mv.sport]

    # -- iskeletler ------------------------------------------------------------
    def solve(self):
        mv, dur = self.mv, self.dur
        fbase = Base(0.0, 0.0, 0.0)
        ftrack = Track(mv.fig, dur, fbase)
        fparams = [ftrack.at(t) for t in range(dur + 1)]
        # bakış hedefi olmadan ön çözüm (hedef/partner yerleşimi için)
        ahead = (400.0, 155.0, 0.0)
        pre = [Skeleton(p, fbase, ahead) for p in fparams]

        self.bag = None
        self.partner = None
        self.hit_pts = []
        for f, name in mv.hits:
            self.hit_pts.append((f, name, pre[f].point(name)))
        direction = -1 if mv.target == "partner_left" else 1
        if mv.target in ("bag", "long_bag"):
            radius = 17.0
            centers, pushes = [], []
            for f, n, pt in self.hit_pts:
                reach = point_pad(n) + radius - 1.5
                if n.endswith("shin"):
                    # yandan savrulan kaval: torba, kavalın savrulma yönündeki yanında durur
                    sk = pre[f]
                    d = sub(sk.j[n[0] + "ankle"], sk.j[n[0] + "knee"])
                    h = unit((d[0], 0.0, d[2]))
                    side = 1.0 if n[0] == "r" else -1.0
                    nrm = (h[2] * side, 0.0, -h[0] * side)
                    centers.append(madd(pt, (nrm, reach)))
                    pushes.append(nrm)
                else:
                    centers.append((pt[0] + reach, pt[1], pt[2]))
                    pushes.append((1.0, 0.0, 0.0))
            # en kısa uzanan vuruş torbaya değsin; yan konum ortalama
            self.bag = {"x": min(c[0] for c in centers), "z": sum(c[2] for c in centers) / len(centers),
                        "r": radius, "long": mv.target == "long_bag", "centers": centers,
                        "pushes": pushes}
        recoil = [0.0] * (dur + 1)
        pbase = None
        if mv.target in ("partner", "partner_left"):
            if mv.opp_dist is None:
                cx = [pt[0] + direction * point_pad(n) for _f, n, pt in self.hit_pts]
                contact = min(cx) if direction == 1 else max(cx)
                px = contact + direction * 13.0
                for f, _n, _p in self.hit_pts:
                    for t in range(dur + 1):
                        dt = t - f
                        if 0 <= dt <= 14:
                            recoil[t] += 8.0 * math.sin(math.pi * min(1.0, dt / 14.0)) * (1 - dt / 20)
            else:
                px = direction * mv.opp_dist
            pyaw = 180.0 if direction == 1 else 0.0
            pbase = Base(px, 0.0, pyaw)
            ptrack = Track(mv.opp or [(0, {})], dur, pbase, mirror=mv.opp_mirror)
            pparams = [ptrack.at(t) for t in range(dur + 1)]
        self.recoil = recoil

        fsk, psk = [], []
        for t in range(dur + 1):
            if pbase is not None:
                rb = Base(pbase.x + direction * recoil[t], 0.0, pbase.yaw)
                p_pre = Skeleton(pparams[t], rb, pre[t].point("head"))
                fs = Skeleton(fparams[t], fbase, p_pre.point("head"))
                ps = Skeleton(pparams[t], rb, fs.point("head"))
                psk.append(ps)
            else:
                target = ahead
                if self.bag:
                    target = (self.bag["x"], 150.0, self.bag["z"])
                if mv.look is not None:
                    target = mv.look
                fs = Skeleton(fparams[t], fbase, target)
            fsk.append(fs)
        self.fsk, self.psk = fsk, psk

    # -- kamera ----------------------------------------------------------------
    def setup_camera(self):
        cam = Camera(self.mv.cam["az"], self.mv.cam["el"])
        pts = []
        for sks in (self.fsk, self.psk):
            for sk in sks:
                for name in ("head",):
                    c = sk.point(name)
                    for d in ((0, 13, 0), (0, -12, 0), (12, 0, 0), (-12, 0, 0), (0, 0, 12), (0, 0, -12)):
                        pts.append(cam.raw(add(c, d)))
                for q in sk.j.values():
                    if isinstance(q, tuple) and len(q) == 3 and isinstance(q[0], float):
                        for d in ((0, 8, 0), (0, -8, 0), (8, 0, 0), (-8, 0, 0), (0, 0, 8), (0, 0, -8)):
                            pts.append(cam.raw(add(q, d)))
        if self.bag:
            b = self.bag
            for y in (12.0, 238.0):
                for dz in (-b["r"], b["r"]):
                    for dx in (-b["r"], b["r"] + 12):
                        pts.append(cam.raw((b["x"] + dx, y, b["z"] + dz)))
        # zemin noktaları
        for sks in (self.fsk, self.psk):
            for sk in sks[:1]:
                pts.append(cam.raw((sk.origin[0], 0.0, sk.origin[2])))
        cam.fit(pts, W, H, margin=16.0, bottom=24.0, max_scale=1.55)
        self.cam = cam

    # -- render ----------------------------------------------------------------
    def build(self):
        self.solve()
        self.setup_camera()
        cam, dur = self.cam, self.dur
        fr = FigureRenderer(self.mv.sport, "fighter")
        pr = FigureRenderer(self.mv.sport, "partner") if self.psk else None
        group_frames = {}      # anahtar -> [kare başına öğe listesi]
        depth_frames = []      # kare başına {anahtar: derinlik}
        boxes = {}             # anahtar -> [kare başına 2B kutu]
        for t in range(dur + 1):
            depths = {}
            for prefix, renderer, sks, bias in (("fig", fr, self.fsk, self.mv.fighter_bias),
                                                ("opp", pr, self.psk, 0.0)):
                if renderer is None:
                    continue
                groups = renderer.build(sks[t], cam)
                for gname, (items, depth) in groups.items():
                    key = f"{prefix}_{gname}"
                    group_frames.setdefault(key, []).append(items)
                    depths[key] = depth + bias
                    boxes.setdefault(key, []).append(items_bbox(items))
            if self.mv.rope is not None:
                ritems, rdepth = self.rope_items(t)
                group_frames.setdefault("fig_rope", []).append(ritems)
                depths["fig_rope"] = rdepth + self.mv.fighter_bias
                boxes.setdefault("fig_rope", []).append(items_bbox(ritems))
            if self.bag:
                key = "bag"
                bitems = self.bag_items(t)
                group_frames.setdefault(key, []).append(bitems)
                depths[key] = -1e6
                boxes.setdefault(key, []).append(items_bbox(bitems))
            depth_frames.append(depths)
        self.group_frames = group_frames
        self.depth_frames = depth_frames
        self.boxes = boxes
        return self.to_lottie()

    # -- ip ----------------------------------------------------------------------
    def rope_items(self, t):
        """İp: iki el arasında, gövdenin etrafında dönen eğri (yan düzlemde daire)."""
        sk = self.fsk[t]
        cam = self.cam
        lh, rh = sk.j["lhand"], sk.j["rhand"]
        # rope=k: k. karede ip ayakların altında
        ph = 2 * math.pi * (t - self.mv.rope) / self.dur
        cx = (lh[0] + rh[0]) / 2.0
        cy = (lh[1] + rh[1]) / 2.0 + 10.0
        R = max(10.0, cy + 4.0)
        apex = (cx + 0.55 * R * math.sin(ph), cy - R * math.cos(ph), (lh[2] + rh[2]) / 2.0)
        mid_l = lerp(lh, apex, 0.6)
        mid_r = lerp(rh, apex, 0.6)
        mid_l = (mid_l[0], mid_l[1], lh[2] * 0.9 + apex[2] * 0.1 - 4.0)
        mid_r = (mid_r[0], mid_r[1], rh[2] * 0.9 + apex[2] * 0.1 + 4.0)
        pts = [cam.project(q) for q in (lh, mid_l, apex, mid_r, rh)]
        item = {"name": "rope", "prims": [("path", smooth(pts, closed=False))], "fill": None,
                "line": "#37474F", "width": 1.8, "visible": True, "kind": "line"}
        depth = cam.depth(apex) - cam.depth(sk.origin)
        return [item], cam.depth(sk.origin) + (12.0 if depth > 0 else -12.0)

    # -- kum torbası ------------------------------------------------------------
    def bag_swing(self, t):
        """Torbanın sallanması: (açı derece, yatay itme yönü) – her darbe kendi yönünde iter."""
        sx = sz = 0.0
        for k, (f, _n, _p) in enumerate(self.hit_pts):
            push = self.bag["pushes"][k]
            for cyc in (0, -self.dur):
                dt = t - (f + cyc)
                if dt >= 0:
                    a = 7.0 * math.exp(-dt / 11.0) * math.sin(dt / 4.2)
                    sx += a * push[0]
                    sz += a * push[2]
        k = 0.55 if self.bag["long"] else 1.0
        ang = math.hypot(sx, sz)
        return ang * k, ((sx / ang, 0.0, sz / ang) if ang > 1e-9 else (1.0, 0.0, 0.0))

    def bag_angle(self, t):
        """2B önizleme (yandan görünüm) için ileri yöndeki bileşen."""
        ang, d = self.bag_swing(t)
        return ang * d[0]

    def bag_items(self, t):
        b = self.bag
        cam = self.cam
        a = math.radians(self.bag_angle(t))
        pivot = (b["x"], 236.0, b["z"])
        d = (math.sin(a), -math.cos(a), 0.0)
        e1 = (0.0, 0.0, 1.0)
        e2 = (math.cos(a), math.sin(a), 0.0)
        chain = 36.0 if not b["long"] else 26.0
        length = 118.0 if not b["long"] else 188.0
        r = b["r"]
        top = madd(pivot, (d, chain))
        bot = madd(top, (d, length))

        def proj(p):
            return cam.project(p)

        def vec(v):
            x, y = cam.raw(v)
            return (x * cam.scale, y * cam.scale)

        a1, a2 = vec(mul(e1, r)), vec(mul(e2, r))
        tc, bc = proj(top), proj(bot)
        ax = unit((bc[0] - tc[0], bc[1] - tc[1], 0.0))
        n2 = (-ax[1], ax[0])

        def extremes(c):
            pa = a1[0] * n2[0] + a1[1] * n2[1]
            pb = a2[0] * n2[0] + a2[1] * n2[1]
            th = math.atan2(pb, pa)
            ex = (a1[0] * math.cos(th) + a2[0] * math.sin(th), a1[1] * math.cos(th) + a2[1] * math.sin(th))
            return (c[0] + ex[0], c[1] + ex[1]), (c[0] - ex[0], c[1] - ex[1])

        t1, t2 = extremes(tc)
        b1, b2 = extremes(bc)
        leather = "#263238" if b["long"] else "#7B1E1E"
        body = [ellipse(tc, a1, a2), polygon([t1, b1, b2, t2]), ellipse(bc, a1, a2)]

        def ring(y_frac, width):
            c0 = madd(top, (d, length * y_frac))
            c1 = madd(top, (d, length * y_frac + width))
            th0 = math.atan2(dot(e2, cam.v), dot(e1, cam.v))
            rows = []
            for c in (c0, c1):
                pts = []
                for k in range(6):
                    th = th0 - math.pi / 2 + math.pi * k / 5
                    pts.append(proj(madd(c, (e1, r * math.cos(th) * 1.01), (e2, r * math.sin(th) * 1.01))))
                rows.append(pts)
            return polygon(rows[0] + list(reversed(rows[1])))

        nv = unit(sub(cam.v, mul(d, dot(cam.v, d))))
        logo_c = madd(top, (d, length * 0.42), (nv, r * 1.01))
        la = vec(mul(unit((nv[2], 0.0, -nv[0])) if abs(nv[0]) + abs(nv[2]) > 1e-6 else (1, 0, 0), 6.0))
        lb = vec(mul(d, 6.0))
        hl_c = madd(top, (d, length * 0.5), (unit(add(nv, (-0.6, 0.0, 0.0))), r * 0.7))
        pts_chain = [proj(madd(top, (e1, r * 0.9))), proj(pivot), proj(madd(top, (e1, -r * 0.9)))]
        items = [
            {"name": "logo", "prims": [ellipse(proj(logo_c), la, lb)], "fill": shade(leather, 1.35),
             "line": None, "width": 0, "visible": True, "kind": "fill"},
            {"name": "band_bottom", "prims": [ring(0.86, 6.0)], "fill": shade(leather, 0.62),
             "line": None, "width": 0, "visible": True, "kind": "fill"},
            {"name": "band_top", "prims": [ring(0.08, 6.0)], "fill": shade(leather, 0.62),
             "line": None, "width": 0, "visible": True, "kind": "fill"},
            {"name": "highlight", "prims": [ellipse(proj(hl_c), vec(mul(e1, 2.2)), vec(mul(d, length * 0.36)))],
             "fill": shade(leather, 1.18), "line": None, "width": 0, "visible": True, "kind": "fill"},
            {"name": "body", "prims": body, "fill": leather, "line": shade(leather, 0.5), "width": 3.0,
             "visible": True, "kind": "fill"},
            {"name": "chain", "prims": [smooth(pts_chain, closed=False, tension=0.0)], "fill": None,
             "line": "#90A4AE", "width": 2.4, "visible": True, "kind": "line"},
        ]
        for it in items:
            it["prims"] = [("path", p) if isinstance(p, dict) else p for p in it["prims"]]
        return items

    # -- zemin ve gölgeler -------------------------------------------------------
    def floor_layers(self, dur):
        """Zemin: ekranda yatay bir bant (ortografik kamerada zemin ufuksuz olduğundan)."""
        cam = self.cam
        ys = []
        for sks in (self.fsk, self.psk):
            for sk in sks:
                for s in ("l", "r"):
                    ys.append(cam.project((sk.j[s + "ball"][0], 0.0, sk.j[s + "ball"][2]))[1])
                ys.append(cam.project((sk.origin[0], 0.0, sk.origin[2]))[1])
        top = max(40.0, min(ys) - 34.0 * cam.scale)
        shapes = []
        band = polygon([(-10.0, top), (W + 10.0, top), (W + 10.0, H + 10.0), (-10.0, H + 10.0)])
        line = polygon([(-10.0, top - 1.5), (W + 10.0, top - 1.5), (W + 10.0, top + 1.5), (-10.0, top + 1.5)])
        shapes.append({"ty": "gr", "nm": "edge", "it": [
            {"ty": "sh", "ks": static(self._path_json(line))},
            {"ty": "fl", "c": static(rgba(shade(FLOORS[self.mv.sport], 0.9))), "o": static(100), "r": 1}, tr()]})
        shapes.append({"ty": "gr", "nm": "floor", "it": [
            {"ty": "sh", "ks": static(self._path_json(band))},
            {"ty": "fl", "c": static(rgba(FLOORS[self.mv.sport])), "o": static(100), "r": 1}, tr()]})
        return [shape_layer("floor", shapes, dur, ind=1)]

    def _path_json(self, p):
        n = len(p["v"])
        return unflat(flat(p), n, p["c"])

    def shadow_shapes(self):
        cam, dur = self.cam, self.dur
        shapes = []
        for prefix, sks in (("fig", self.fsk), ("opp", self.psk)):
            if not sks:
                continue
            body, feet = [], {"l": [], "r": []}
            for sk in sks:
                o = sk.origin
                body.append(self._ellipse_path((o[0], 0.0, o[2]), 34.0, 22.0))
                for s in ("l", "r"):
                    c = lerp(sk.j[s + "heel"], sk.j[s + "ball"], 0.5)
                    hgt = max(0.0, min(sk.j[s + "heel"][1], sk.j[s + "ball"][1]) - 0.5)
                    op = max(0.0, 1.0 - hgt / 30.0)
                    feet[s].append((self._ellipse_path((c[0], 0.0, c[2]), 13.0, 7.0), op))
            shapes.append({"ty": "gr", "nm": prefix + "_shadow", "it": [
                {"ty": "sh", "ks": animated_path(body, 0.6)},
                {"ty": "fl", "c": static(rgba("#000000")), "o": static(9), "r": 1}, tr()]})
            for s in ("l", "r"):
                paths = [p for p, _o in feet[s]]
                ops = [round(o * 100) for _p, o in feet[s]]
                shapes.append({"ty": "gr", "nm": f"{prefix}_{s}foot_shadow", "it": [
                    {"ty": "sh", "ks": animated_path(paths, 0.6)},
                    {"ty": "fl", "c": static(rgba("#000000")), "o": static(18), "r": 1},
                    tr(animated_scalar(ops, tol=3))]})
        return shapes

    def _ellipse_path(self, c, rx, rz):
        cam = self.cam
        a = cam.raw((rx, 0.0, 0.0))
        b = cam.raw((0.0, 0.0, rz))
        return ellipse(cam.project(c), (a[0] * cam.scale, a[1] * cam.scale), (b[0] * cam.scale, b[1] * cam.scale))

    # -- efektler -------------------------------------------------------------
    def effect_layers(self, ind0):
        cam, dur = self.cam, self.dur
        layers = []
        ind = ind0
        trails = self.mv.trails
        if trails is None:
            trails = [(n, max(0, f - 8), f) for f, n, _p in self.hit_pts]
        for k, (name, t0, t1) in enumerate(trails):
            pts = []
            for t in range(t0, t1 + 1):
                sk = self.fsk[t]
                pts.append(cam.project(sk.point(name)))
            if len(pts) < 3:
                continue
            path = smooth(pts, closed=False)
            end = min(dur, t1 + 7)
            ks_e = [{"t": t0, "s": [0], "i": {"x": [0.4], "y": [1]}, "o": {"x": [0.6], "y": [0]}}, {"t": t1, "s": [100]}]
            ks_s = [{"t": t0, "s": [0], "i": {"x": [0.4], "y": [1]}, "o": {"x": [0.6], "y": [0]}},
                    {"t": t1, "s": [35], "i": {"x": [0.4], "y": [1]}, "o": {"x": [0.6], "y": [0]}},
                    {"t": end, "s": [100]}]
            shapes = []
            for w, opac in ((11, 22), (4, 55)):
                shapes.append({"ty": "gr", "nm": f"trail{w}", "it": [
                    {"ty": "sh", "ks": static(self._path_json(path))},
                    {"ty": "tm", "s": {"a": 1, "k": ks_s}, "e": {"a": 1, "k": ks_e}, "o": static(0), "m": 1},
                    {"ty": "st", "c": static(rgba(self.accent)), "o": static(opac), "w": static(w), "lc": 2, "lj": 2},
                    tr()]})
            lay = shape_layer(f"trail_{k}", shapes, dur, ind=ind)
            lay["ip"], lay["op"] = t0, end + 1
            layers.append(lay)
            ind += 1
        for k, (f, name, _p) in enumerate(self.hit_pts):
            sk = self.fsk[f]
            x, y = cam.project(sk.point(name))
            start, end = max(f - 1, 0), min(f + 7, dur)
            op = animated_scalar([0 if (t < f or t > end) else max(0, 100 - (t - f) * 14) for t in range(dur + 1)],
                                 tol=2)
            sc = animated_scalar([[40 + min(t - f, 7) * 16] * 2 + [100] if t >= f else [40, 40, 100]
                                  for t in range(dur + 1)], tol=1)
            star = {"ty": "sr", "sy": 1, "d": 1, "pt": static(8), "p": static([0, 0]), "r": static(0),
                    "ir": static(6), "is": static(0), "or": static(16), "os": static(0)}
            lay = shape_layer(f"impact_{k}", [{"ty": "gr", "nm": "star", "it": [
                star, {"ty": "st", "c": static(rgba("#FF6F00")), "o": static(100), "w": static(2), "lc": 2, "lj": 2},
                {"ty": "fl", "c": static(rgba("#FFD54F")), "o": static(100), "r": 1}, tr()]}],
                dur, ind=ind, ks=layer_ks(opacity=op, pos=static([r1(x), r1(y), 0]), scale=sc))
            lay["ip"], lay["op"] = start, end + 1
            layers.append(lay)
            ind += 1
        return layers

    # -- derinlik sırası -----------------------------------------------------------
    def orders(self):
        """Her kare için çizim sırası (alttan üste). Yalnızca ekranda örtüşen grup çiftleri
        derinliğe göre sıralanır; diğerleri önceki karedeki sırasını korur (daha az katman)."""
        keys = list(self.group_frames.keys())
        d0 = self.depth_frames[0]
        prev = sorted(keys, key=lambda k: d0[k])
        rel = {}            # (a, b) -> a b'nin altında mı (histerezisli)
        margin = 2.5
        result = []
        for t in range(self.dur):
            d = self.depth_frames[t]
            bx = {k: self.boxes[k][t] for k in keys}
            below = {k: set() for k in keys}     # k'nin altında olması gerekenler
            for i, a in enumerate(keys):
                for b in keys[i + 1:]:
                    if not boxes_overlap(bx[a], bx[b]):
                        continue
                    key = (a, b)
                    if d[a] + margin < d[b]:
                        rel[key] = True          # a altta
                    elif d[b] + margin < d[a]:
                        rel[key] = False
                    elif key not in rel:
                        rel[key] = d[a] <= d[b]
                    if rel[key]:
                        below[b].add(a)
                    else:
                        below[a].add(b)
            order = []
            placed = set()
            remaining = list(prev)
            while remaining:
                pick = None
                for k in remaining:
                    if below[k] <= placed:
                        pick = k
                        break
                if pick is None:   # döngü: en uzaktakini koy
                    pick = min(remaining, key=lambda k: d[k])
                order.append(pick)
                placed.add(pick)
                remaining.remove(pick)
            prev = order
            result.append(tuple(order))
        return result

    def to_lottie(self):
        dur = self.dur
        assets = []
        for key, frames in self.group_frames.items():
            n_items = len(frames[0])
            shapes = []
            for i in range(n_items):
                name = frames[0][i]["name"]
                shapes.append(item_to_lottie(name, [fr[i] for fr in frames]))
            assets.append({"id": key, "nm": key, "fr": FPS,
                           "layers": [shape_layer(key, shapes, dur, ind=1)]})
        orders = self.orders()
        segments = []
        start = 0
        for t in range(1, dur + 1):
            if t == dur or orders[t] != orders[start]:
                segments.append((start, t, orders[start]))
                start = t
        layers = []
        ind = 1
        layers += self.effect_layers(ind)
        ind += len(layers)
        for s0, s1, order in segments:
            for key in reversed(order):    # üstteki önce
                layers.append({"ddd": 0, "ind": ind, "ty": 0, "nm": key, "refId": key, "sr": 1, "ks": layer_ks(),
                               "ao": 0, "w": W, "h": H, "ip": s0, "op": s1, "st": 0, "bm": 0})
                ind += 1
        shadow = shape_layer("shadows", self.shadow_shapes(), dur, ind=ind)
        ind += 1
        layers.append(shadow)
        for lay in self.floor_layers(dur):
            lay["ind"] = ind
            ind += 1
            layers.append(lay)
        return {"v": "5.7.4", "fr": FPS, "ip": 0, "op": dur, "w": W, "h": H, "nm": self.id, "ddd": 0,
                "assets": assets, "layers": layers, "markers": []}


def _strip(o, depth=0):
    if isinstance(o, dict):
        is_layer = "ty" in o and isinstance(o.get("ty"), int)
        is_asset = "refId" in o or ("id" in o and "layers" in o)
        out = {}
        for k, v in o.items():
            if k in ("nm", "np") and not is_layer and not is_asset and depth > 0:
                continue
            out[k] = _strip(v, depth + 1)
        return out
    if isinstance(o, list):
        return [_strip(v, depth + 1) for v in o]
    return o


def build_move(move_id, mv):
    return _strip(SceneBuilder(move_id, mv).build())
