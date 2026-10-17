"""3B insan figürünü kamera açısından 2B çizim öğelerine (Lottie yolları) dönüştürür.

Figür, derinliğe göre sıralanan gruplardan oluşur: gövde+baş, her kolun üst ve alt kısmı,
her bacak. Her grup içinde öğeler sabit sıradadır (ilk öğe en üstte). Bir öğe birden çok
yoldan oluşabilir; bunlar tek dolguyla birleşir (dikişsiz kas hatları) ve dış konturu çizilir.
"""
import math

from camera import ellipse, polygon, smooth
from mathx import cross, dot, length, lerp, madd, mul, reject, sub, unit
from skeleton import CHEST_UP, HEAD_R

# --------------------------------------------------------------------------
# Renkler ve kıyafetler
# --------------------------------------------------------------------------
SKIN_TONES = {"fighter": "#C68A62", "partner": "#8B5A3C"}
HAIR_COLORS = {"fighter": "#2A1B12", "partner": "#141010"}

OUTFITS = {
    "boxing": dict(shorts="#B71C1C", trim="#F5F5F5", gloves="#D32F2F", shoes="#1F1F1F", boot=0.36),
    "kickboxing": dict(shorts="#0D47A1", trim="#FFC107", gloves="#1565C0", guard="#ECEFF1"),
    "wrestling": dict(singlet="#2E7D32", shoes="#1B5E20", boot=0.3, trim="#A5D6A7"),
    "taekwondo": dict(dobok="#F7F7F7", belt="#1E1E1E"),
    "general": dict(tee="#546E7A", shorts="#263238", shoes="#ECEFF1", boot=0.06, trim="#90A4AE"),
}
PARTNER_OUTFITS = {
    "boxing": dict(OUTFITS["boxing"], shorts="#37474F", trim="#B0BEC5", gloves="#455A64", shoes="#37474F"),
    "kickboxing": dict(OUTFITS["kickboxing"], shorts="#424242", trim="#BDBDBD", gloves="#546E7A", guard="#CFD8DC"),
    "wrestling": dict(OUTFITS["wrestling"], singlet="#C62828", shoes="#7F0000", trim="#EF9A9A"),
    "taekwondo": dict(OUTFITS["taekwondo"], hogu="#1E88E5"),
    "general": OUTFITS["general"],
}


def hex_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def shade(color, f):
    rgb = hex_rgb(color)
    if f <= 1:
        rgb = [c * f for c in rgb]
    else:
        rgb = [c + (255 - c) * (f - 1) for c in rgb]
    return "#%02X%02X%02X" % tuple(int(max(0, min(255, round(c)))) for c in rgb)


def outline_of(color):
    rgb = hex_rgb(color)
    lum = 0.3 * rgb[0] + 0.59 * rgb[1] + 0.11 * rgb[2]
    return shade(color, 0.62) if lum > 215 else shade(color, 0.5)


# --------------------------------------------------------------------------
# 3B ilkel -> 2B
# --------------------------------------------------------------------------
class Proj:
    def __init__(self, cam):
        self.cam = cam

    def p(self, pt):
        return self.cam.project(pt)

    def vec(self, v):
        x, y = self.cam.raw(v)
        return (x * self.cam.scale, y * self.cam.scale)

    def r(self, r):
        return r * self.cam.scale

    def capsule(self, a, ra, b, rb):
        """Konik kapsül ilkel öğesi (Lottie'de dönüşüm animasyonuyla çizilir)."""
        return ("cap", self.p(a), self.r(ra), self.p(b), self.r(rb))

    def sphere(self, c, r):
        return ("circ", self.p(c), self.r(r))

    def disc(self, c, n, r):
        """Normali n olan 3B daire (göz, kulak vb.) -> elips."""
        a = unit(cross(n, (0.0, 1.0, 0.0)), (0.0, 0.0, 1.0))
        b = cross(n, a)
        return ("path", ellipse(self.p(c), self.vec(mul(a, r)), self.vec(mul(b, r))))

    def disc2(self, c, a, b):
        return ("path", ellipse(self.p(c), self.vec(a), self.vec(b)))

    def line(self, pts, closed=False):
        return ("path", smooth([self.p(q) for q in pts], closed=closed))


def ellipse_extreme(c2, a2, b2, n2):
    pa = a2[0] * n2[0] + a2[1] * n2[1]
    pb = b2[0] * n2[0] + b2[1] * n2[1]
    t = math.atan2(pb, pa)
    e = (a2[0] * math.cos(t) + b2[0] * math.sin(t), a2[1] * math.cos(t) + b2[1] * math.sin(t))
    return (c2[0] + e[0], c2[1] + e[1]), (c2[0] - e[0], c2[1] - e[1]), t


# Gövde kesitleri: (yükseklik, göğüs ağırlığı, yarı genişlik, yarı derinlik, öne kayma)
TORSO_SECTIONS = [
    (-10.0, 0.0, 12.8, 9.6, -1.6),
    (-3.0, 0.0, 15.8, 11.4, -1.2),
    (5.0, 0.1, 15.2, 10.8, -0.2),
    (12.0, 0.35, 14.0, 10.1, 0.5),
    (20.0, 0.75, 15.0, 10.8, 1.0),
    (29.0, 1.0, 16.6, 11.8, 1.6),
    (37.0, 1.0, 17.4, 11.3, 1.2),
    (43.0, 1.0, 15.8, 9.6, 0.1),
    (47.5, 1.0, 8.6, 6.8, -0.9),
]


def torso_section(sk, h, w, a, b, fo, inflate=0.0):
    pf, pu, pr = sk.pelvis
    cf, cu, cr = sk.chest
    pp = madd(sk.origin, (pu, h), (pf, fo))
    pc = madd(sk.c0, (cu, h - CHEST_UP), (cf, fo))
    center = lerp(pp, pc, w)
    ax = mul(unit(lerp(pr, cr, w)), a + inflate)
    bx = mul(unit(lerp(pf, cf, w)), b + inflate)
    up = unit(lerp(pu, cu, w))
    return center, ax, bx, up


class FigureRenderer:
    """Bir figürün (sporcu ya da partner) her karede çizim öğelerini üretir."""

    def __init__(self, sport, role="fighter"):
        self.role = role
        self.outfit = (OUTFITS if role == "fighter" else PARTNER_OUTFITS)[sport]
        self.skin = SKIN_TONES[role]
        self.hair = HAIR_COLORS[role]
        self.far_side = None   # "l" ya da "r": kameradan uzak taraf (koyu tonlanır)

    # -- yardımcılar -------------------------------------------------------
    def tone(self, color, group):
        if self.far_side and group.startswith(self.far_side):
            return shade(color, 0.84)
        return color

    def item(self, name, paths, fill=None, line=None, width=3.0, visible=True, kind="fill", group=""):
        fill_c = self.tone(fill, group) if fill else None
        line_c = self.tone(line, group) if line else (outline_of(fill_c) if fill_c else None)
        prims = [p if isinstance(p, tuple) else ("path", p) for p in paths]
        return {"name": name, "prims": prims, "fill": fill_c, "line": line_c, "width": width,
                "visible": visible, "kind": kind}

    # -- ana fonksiyon -------------------------------------------------------
    def build(self, sk, cam):
        P = Proj(cam)
        if self.far_side is None:
            self.far_side = "l" if dot(sk.pelvis[2], cam.v) > 0 else "r"
        groups = {}
        groups["torso"] = (self.torso_items(sk, P, cam), self.depth(cam, [sk.origin, sk.c0, sk.neck_base]))
        for s in ("l", "r"):
            j = sk.j
            groups[s + "arm_up"] = (self.upper_arm_items(sk, P, s),
                                    self.depth(cam, [j[s + "shoulder"], j[s + "elbow"]]))
            groups[s + "arm_lo"] = (self.lower_arm_items(sk, P, s),
                                    self.depth(cam, [j[s + "elbow"], j[s + "hand"]]) + 0.5)
            groups[s + "leg"] = (self.leg_items(sk, P, s),
                                 self.depth(cam, [j[s + "hip"], j[s + "knee"], j[s + "ankle"]]))
        return groups

    @staticmethod
    def depth(cam, pts):
        return sum(cam.depth(q) for q in pts) / len(pts)

    # -- gövde ve baş ----------------------------------------------------------
    def torso_outline(self, sk, P, sections, inflate=0.0, top_cap=3.0, bottom_cap=4.5):
        if len(sections) > 7:
            keep = [0, 1, 3, 5, 6, 7] + list(range(8, len(sections)))
            sections = [sections[i] for i in keep]
        cs = [torso_section(sk, *s, inflate=inflate) for s in sections]
        c2 = [P.p(c) for c, _, _, _ in cs]
        ax = (c2[-1][0] - c2[0][0], c2[-1][1] - c2[0][1])
        n = math.hypot(*ax) or 1.0
        ax = (ax[0] / n, ax[1] / n)
        n2 = (-ax[1], ax[0])
        right, left = [], []
        for (c, a, b, _u), cc in zip(cs, c2):
            e1, e2, _t = ellipse_extreme(cc, P.vec(a), P.vec(b), n2)
            right.append(e1)
            left.append(e2)
        top = P.p(madd(cs[-1][0], (cs[-1][3], top_cap)))
        bottom = P.p(madd(cs[0][0], (cs[0][3], -bottom_cap)))
        pts = [bottom] + right + [top] + list(reversed(left))
        return smooth(pts, tension=0.9)

    def band(self, sk, P, cam, h0, h1, inflate=0.6, n=5):
        """Belde görünür (kameraya bakan) yarım halka şerit."""
        rows = []
        for h in (h1, h0):
            sec = min(TORSO_SECTIONS, key=lambda s: abs(s[0] - h))
            c, a, b, _u = torso_section(sk, h, sec[1], sec[2], sec[3], sec[4], inflate)
            # görünür yarı: normal·v > 0
            t0 = math.atan2(dot(unit(b), cam.v), dot(unit(a), cam.v))
            pts = []
            for k in range(n):
                t = t0 - math.pi / 2 + math.pi * k / (n - 1)
                pts.append(P.p(madd(c, (a, math.cos(t)), (b, math.sin(t)))))
            rows.append(pts)
        return polygon(rows[0] + list(reversed(rows[1])))

    def surface_point(self, sk, h, ang, out=0.3):
        """Gövde yüzeyinde nokta: ang=90 ön orta, 0 sağ yan, 180 sol yan."""
        sec = min(TORSO_SECTIONS, key=lambda s: abs(s[0] - h))
        c, a, b, _u = torso_section(sk, h, sec[1], sec[2] + out, sec[3] + out, sec[4])
        t = math.radians(ang)
        return madd(c, (a, math.cos(t)), (b, math.sin(t)))

    def front_visible(self, sk, cam, h):
        sec = min(TORSO_SECTIONS, key=lambda s: abs(s[0] - h))
        _c, _a, b, _u = torso_section(sk, h, *sec[1:])
        return dot(unit(b), cam.v)

    def torso_items(self, sk, P, cam):
        o = self.outfit
        items = []
        items += self.head_items(sk, P, cam)
        skin = self.skin
        front = self.front_visible(sk, cam, 29.0)
        belly = self.front_visible(sk, cam, 14.0)
        full = TORSO_SECTIONS
        if o.get("dobok"):
            d = o["dobok"]
            lap = [self.surface_point(sk, 44, 62, 0.6), self.surface_point(sk, 33, 82, 0.6),
                   self.surface_point(sk, 22, 100, 0.6), self.surface_point(sk, 15, 112, 0.6)]
            items.append(self.item("lapel", [P.line(lap)], line=shade(d, 0.72), width=1.6, kind="line",
                                   visible=front > 0.05))
            items.append(self.item("belt_knot", [P.capsule(self.surface_point(sk, 12, 92, 1.4), 1.6,
                                                           self.surface_point(sk, 2, 98, 1.6), 1.2)],
                                   fill=o["belt"], visible=belly > 0.1))
            items.append(self.item("belt", [self.band(sk, P, cam, 10.0, 15.0, 1.3)], fill=o["belt"]))
            if o.get("hogu"):
                hp = [self.surface_point(sk, h, a, 1.6) for h, a in
                      ((40, 25), (40, 155), (27, 165), (16, 150), (16, 30), (27, 15))]
                items.append(self.item("hogu", [smooth([P.p(q) for q in hp])], fill=o["hogu"], line="#FFFFFF",
                                       width=3.0, visible=front > -0.2))
            items.append(self.item("dobok", [self.torso_outline(sk, P, full[:-1], inflate=1.6, top_cap=4.0)], fill=d))
        elif o.get("singlet"):
            items.append(self.item("singlet_trim", [self.band(sk, P, cam, 4.0, 7.0, 0.9)], fill=o["trim"]))
            items.append(self.item("singlet", [self.torso_outline(sk, P, full[:-2], inflate=0.7, top_cap=0.5)],
                                   fill=o["singlet"]))
            items.append(self.item("skin", [self.torso_outline(sk, P, full)], fill=skin))
        else:
            if o.get("tee"):
                items.append(self.item("tee", [self.torso_outline(sk, P, full[:-1], inflate=1.0, top_cap=2.5)],
                                       fill=o["tee"]))
            if o.get("shorts"):
                items.append(self.item("waistband", [self.band(sk, P, cam, 9.0, 13.0, 1.6)],
                                       fill=o.get("trim", shade(o["shorts"], 0.8))))
                items.append(self.item("shorts", [self.torso_outline(sk, P, full[:4], inflate=1.4, top_cap=0.5)],
                                       fill=o["shorts"]))
            if not o.get("tee"):
                pec_r = [self.surface_point(sk, 27.5, 92), self.surface_point(sk, 26.5, 70),
                         self.surface_point(sk, 29.5, 45)]
                pec_l = [self.surface_point(sk, 27.5, 88), self.surface_point(sk, 26.5, 110),
                         self.surface_point(sk, 29.5, 135)]
                abs_l = [self.surface_point(sk, 23, 90), self.surface_point(sk, 16, 90),
                         self.surface_point(sk, 10, 90)]
                ln = shade(skin, 0.74)
                items.append(self.item("pec_r", [P.line(pec_r)], line=ln, width=1.5, kind="line",
                                       visible=front > 0.15))
                items.append(self.item("pec_l", [P.line(pec_l)], line=ln, width=1.5, kind="line",
                                       visible=front > 0.15))
                items.append(self.item("abs", [P.line(abs_l)], line=ln, width=1.3, kind="line",
                                       visible=belly > 0.25))
                items.append(self.item("skin", [self.torso_outline(sk, P, full)], fill=skin))
        return items

    def head_items(self, sk, P, cam):
        hf, hu, hr = sk.head
        c = sk.head_c
        R = HEAD_R
        skin = self.skin
        items = []
        v = cam.v
        facing = dot(hf, v)
        # yüz detayları
        for side, sgn in (("r", 1), ("l", -1)):
            n_eye = unit(madd((0, 0, 0), (hf, 0.80), (hu, 0.12), (hr, 0.40 * sgn)))
            e = madd(c, (n_eye, R - 0.1))
            vis = dot(n_eye, v) > 0.08
            items.append(self.item("eye_" + side, [P.disc(e, n_eye, 0.95)], fill="#1B1210", line="#1B1210",
                                   width=0.6, visible=vis))
            b0 = madd(c, (unit(madd((0, 0, 0), (hf, 0.80), (hu, 0.34), (hr, 0.16 * sgn))), R + 0.3))
            b1 = madd(c, (unit(madd((0, 0, 0), (hf, 0.62), (hu, 0.36), (hr, 0.62 * sgn))), R + 0.3))
            items.append(self.item("brow_" + side, [P.line([b0, b1])], line=self.hair, width=2.0, kind="line",
                                   visible=dot(unit(sub(b0, c)), v) > 0.05 or dot(unit(sub(b1, c)), v) > 0.05))
        m0 = madd(c, (hf, 8.4), (hu, -6.8), (hr, 2.0))
        m1 = madd(c, (hf, 8.4), (hu, -6.8), (hr, -2.0))
        items.append(self.item("mouth", [P.line([m0, madd(c, (hf, 8.9), (hu, -7.0)), m1])], line="#6D3B2A",
                               width=1.3, kind="line", visible=facing > -0.15))
        for side, sgn in (("r", 1), ("l", -1)):
            n_ear = mul(hr, sgn)
            ec = madd(c, (hr, sgn * (R - 0.6)), (hf, -1.2), (hu, -1.5))
            vis = dot(n_ear, v) > 0.12
            items.append(self.item("ear_" + side, [P.disc2(ec, mul(hu, 3.1), mul(hf, 2.0))],
                                   fill=shade(skin, 0.93), visible=vis, width=1.8))
        hair = self.hair_path(P, cam, madd(c, (hu, 0.4)), R + 0.7, unit(madd((0, 0, 0), (hu, 0.82), (hf, -0.5))),
                              math.radians(70), K=6)
        items.append(self.item("hair", [hair[0]], fill=self.hair, visible=hair[1], width=1.6))
        head = [
            P.sphere(madd(c, (hu, 0.4)), R),
            P.capsule(madd(c, (hf, 3.2), (hu, -3.6)), 7.4, madd(c, (hf, 6.0), (hu, -8.9)), 3.5),
            P.capsule(madd(c, (hf, 9.3), (hu, -0.8)), 1.35, madd(c, (hf, 11.4), (hu, -3.6)), 1.25),
            P.capsule(sk.neck_base, 6.2, madd(sk.neck_top, (hu, 1.5)), 5.5),
        ]
        items.append(self.item("head", head, fill=skin))
        return items

    def hair_path(self, P, cam, c, R, h, beta, K=8):
        """Saç: başın küre kapağının görünen kısmı. (yol, görünür) döner."""
        v = cam.v
        sr, su = cam.right, cam.up
        cb, sb = math.cos(beta), math.sin(beta)
        hv = dot(h, v)
        e1 = reject(v, h)
        if length(e1) < 1e-6:
            e1 = reject(sr, h)
        e1 = unit(e1)
        e2 = cross(h, e1)
        A = cb * hv
        B = sb * dot(e1, v)

        def cap_pt(t):
            n = madd((0, 0, 0), (h, cb), (e1, sb * math.cos(t)), (e2, sb * math.sin(t)))
            return n

        def proj(n):
            return P.p(madd(c, (n, R)))

        if B < 1e-6 or -A / B <= -1.0:
            if hv > 0:
                pts = [proj(cap_pt(2 * math.pi * k / (2 * K))) for k in range(2 * K)]
                return smooth(pts), True
            return smooth([P.p(c)] * (2 * K)), False
        if -A / B >= 1.0:
            return smooth([P.p(c)] * (2 * K)), False
        g = math.acos(-A / B)
        cap = [cap_pt(-g + 2 * g * k / K) for k in range(K + 1)]
        s0 = math.atan2(dot(cap[0], su), dot(cap[0], sr))
        s1 = math.atan2(dot(cap[-1], su), dot(cap[-1], sr))
        # silüet yayı: s1'den s0'a, kapak içinden geçen yön
        d = (s0 - s1) % (2 * math.pi)
        mid = s1 + d / 2
        mvec = madd((0, 0, 0), (sr, math.cos(mid)), (su, math.sin(mid)))
        if dot(mvec, h) < cb:
            d = d - 2 * math.pi
        sil = []
        for k in range(1, K):
            s = s1 + d * k / K
            sil.append(madd((0, 0, 0), (sr, math.cos(s)), (su, math.sin(s))))
        pts = [proj(n) for n in cap] + [proj(n) for n in sil]
        return smooth(pts, tension=0.8), True

    # -- kollar ---------------------------------------------------------------
    def bend_dir(self, a, b, c, fallback):
        """a-b-c zincirinde b'deki bükülmenin iç tarafı (a-b eksenine dik)."""
        axis = unit(sub(b, a))
        d = reject(sub(c, b), axis)
        if length(d) < 0.8:
            d = reject(fallback, axis)
        return unit(d, fallback)

    def upper_arm_items(self, sk, P, s):
        o = self.outfit
        g = s + "arm_up"
        j = sk.j
        S, E, H = j[s + "shoulder"], j[s + "elbow"], j[s + "hand"]
        bd = self.bend_dir(S, E, H, sk.chest[0])
        items = []
        sleeve = o.get("dobok") or o.get("tee")
        delt = madd(S, (sk.chest[1], -0.6))
        if sleeve:
            cover = 1.0 if o.get("dobok") else 0.48
            infl = 1.6 if o.get("dobok") else 1.1
            end = lerp(S, E, cover)
            items.append(self.item("sleeve", [P.sphere(delt, 6.3 + infl),
                                              P.capsule(S, 5.5 + infl, end, 4.2 + infl + (1 - cover) * 1.0)],
                                   fill=sleeve, group=g))
        items.append(self.item("skin", [
            P.sphere(delt, 6.2),
            P.capsule(S, 5.4, E, 4.0),
            P.capsule(madd(lerp(S, E, 0.25), (bd, 0.9)), 4.8, madd(lerp(S, E, 0.66), (bd, 0.8)), 4.3),
        ], fill=self.skin, group=g))
        return items

    def lower_arm_items(self, sk, P, s):
        o = self.outfit
        g = s + "arm_lo"
        j = sk.j
        S, E, Wr, H = j[s + "shoulder"], j[s + "elbow"], j[s + "wrist"], j[s + "hand"]
        fd = unit(sub(H, E))
        side = unit(reject(sk.chest[1], fd), (0.0, 1.0, 0.0))
        items = []
        glove = o.get("gloves")
        if glove:
            lace_a = madd(Wr, (fd, 2.2), (side, 4.6))
            lace_b = madd(Wr, (fd, 2.2), (side, -4.6))
            items.append(self.item("cuff_line", [P.line([lace_a, lace_b])], line="#FAFAFA", width=1.6,
                                   kind="line", group=g))
            items.append(self.item("glove", [
                P.capsule(madd(Wr, (fd, -1.0)), 4.6, madd(H, (fd, 1.0)), 6.6),
                P.sphere(madd(H, (side, 4.2), (fd, -1.5)), 2.7),
            ], fill=glove, group=g))
        else:
            items.append(self.item("fist", [
                P.capsule(Wr, 2.9, H, 4.0),
                P.sphere(madd(H, (side, 2.4), (fd, -0.8)), 1.9),
            ], fill=self.skin, group=g))
        if o.get("dobok"):
            end = lerp(E, Wr, 0.86)
            items.append(self.item("sleeve", [P.sphere(E, 5.6), P.capsule(E, 5.6, end, 4.8)],
                                   fill=o["dobok"], group=g))
        items.append(self.item("skin", [
            P.capsule(madd(E, (fd, -0.6)), 4.2, Wr, 2.8),
            P.capsule(lerp(E, Wr, 0.05), 4.6, lerp(E, Wr, 0.5), 3.6),
        ], fill=self.skin, group=g))
        return items

    # -- bacaklar ---------------------------------------------------------------
    def leg_items(self, sk, P, s):
        o = self.outfit
        g = s + "leg"
        j = sk.j
        Hj, K, A = j[s + "hip"], j[s + "knee"], j[s + "ankle"]
        fd, fu, fr, td = j[s + "foot"]
        ball = j[s + "ball"]
        # bükülmenin iç tarafı baldırın gittiği yön (arka); uyluğun ön yüzü bunun tersi
        fwd = mul(self.bend_dir(Hj, K, A, mul(fd, -1.0)), -1.0)
        sf = unit(reject(td, unit(sub(A, K))), fd)  # baldır ön yüzü (parmak yönü)
        items = []

        heel = madd(A, (fd, -4.4), (fu, -4.4))
        foot = [
            P.capsule(madd(A, (fu, 0.3)), 3.6, heel, 3.4),
            P.capsule(heel, 3.4, madd(ball, (fu, 0.3)), 3.0),
            P.capsule(madd(A, (fd, 0.6)), 3.4, madd(ball, (fu, 0.9)), 2.8),
            P.capsule(ball, 3.0, madd(ball, (td, 5.4), (fu, 0.3)), 2.2),
        ]
        shoe = o.get("shoes")
        if shoe:
            sole = [P.capsule(madd(heel, (fu, -2.6)), 1.3, madd(ball, (td, 4.6), (fu, -2.4)), 1.1)]
            items.append(self.item("sole", sole, fill="#9E9E9E" if shoe != "#ECEFF1" else "#78909C",
                                   width=0, group=g))
            big = [
                P.capsule(madd(A, (fu, 0.3)), 4.4, heel, 4.1),
                P.capsule(heel, 4.1, madd(ball, (fu, 0.4)), 3.7),
                P.capsule(madd(A, (fd, 0.6)), 4.1, madd(ball, (fu, 1.0)), 3.5),
                P.capsule(ball, 3.7, madd(ball, (td, 5.6), (fu, 0.4)), 2.8),
            ]
            items.append(self.item("shoe", big, fill=shoe, group=g))
            if o.get("boot"):
                items.append(self.item("boot", [P.capsule(lerp(K, A, 1 - o["boot"]), 4.6, A, 4.4)],
                                       fill=shoe, group=g))
        else:
            if o.get("guard"):
                items.append(self.item("instep", [P.capsule(madd(A, (fd, 2.0), (fu, 0.8)), 4.0,
                                                            madd(ball, (fu, 1.2)), 3.3)],
                                       fill=o["guard"], group=g))
            items.append(self.item("foot", foot, fill=self.skin, group=g))
        if o.get("guard"):
            items.append(self.item("shin_guard", [P.capsule(madd(lerp(K, A, 0.06), (sf, 0.8)), 6.1,
                                                            madd(lerp(K, A, 0.9), (sf, 0.4)), 4.5)],
                                   fill=o["guard"], group=g))
        if o.get("dobok"):
            items.append(self.item("pants", [
                P.capsule(Hj, 10.4, K, 7.8), P.sphere(K, 7.2),
                P.capsule(K, 7.4, lerp(K, A, 0.88), 6.4)], fill=o["dobok"], group=g))
        elif o.get("singlet"):
            items.append(self.item("singlet_leg", [P.capsule(Hj, 9.4, lerp(Hj, K, 0.36), 8.6)],
                                   fill=o["singlet"], group=g))
        elif o.get("shorts"):
            items.append(self.item("shorts_leg", [P.capsule(Hj, 10.0, lerp(Hj, K, 0.5), 8.6)],
                                   fill=o["shorts"], group=g))
        items.append(self.item("skin", [
            P.capsule(Hj, 8.4, madd(K, (fwd, 0.3)), 5.4),
            P.capsule(madd(lerp(Hj, K, 0.2), (fwd, 1.5)), 7.4, madd(lerp(Hj, K, 0.72), (fwd, 1.4)), 5.8),
            P.capsule(K, 5.1, A, 3.4),
            P.capsule(madd(lerp(K, A, 0.1), (sf, -2.0)), 5.2, madd(lerp(K, A, 0.55), (sf, -0.6)), 3.8),
        ], fill=self.skin, group=g))
        return items
