"""Hacimli (dolgulu) figür çizimi ve spora göre kıyafetler.

Her uzuv kendi parent'lı katmanında, yerel koordinatta (0,0) eklemden (0,-L) uca doğru
"yukarı" uzanacak şekilde çizilir; katmanın rotasyonu uzvu yönlendirir. Gövde/baş için
yerel +x figürün baktığı (ön) taraftır.
Yalnızca lottie-android'in desteklediği öğeler kullanılır (gr, sh, el, rc, fl, st, tr).
"""
from rig import (FOREARM, HEAD_R, NECK, SHIN, SHOULDER_DROP, THIGH, TORSO, UPPER_ARM,
                 animated, group_transform, rgba, shade, static, transform)

K = 0.5523  # dairesel yay için bezier katsayısı

SKIN = "#D9A27A"
LINE = "#4E342E"
HAIR = "#2B1D16"
WHITE_LINE = "#90A4AE"

# cover_*: uzvun eklemden itibaren ne kadarının (0..1) giysiyle kaplı olduğu
OUTFITS = {
    "boxing": dict(top=None, shorts="#B71C1C", band="#FAFAFA", thigh_cover=0.5, arm_cover=0,
                   gloves="#D32F2F", shoes="#212121", boot=0.22, shin_guard=None, belt=None),
    "kickboxing": dict(top=None, shorts="#0D47A1", band="#FFC107", thigh_cover=0.42, arm_cover=0,
                       gloves="#1565C0", shoes=None, boot=0, shin_guard="#E3F2FD", belt=None),
    "wrestling": dict(top="#2E7D32", shorts="#2E7D32", band=None, thigh_cover=0.38, arm_cover=0,
                      gloves=None, shoes="#1B5E20", boot=0.3, shin_guard=None, belt=None),
    "taekwondo": dict(top="#FAFAFA", shorts="#FAFAFA", band=None, thigh_cover=1.0, arm_cover=1.0,
                      forearm_cover=0.82, shin_cover=0.88, gloves=None, shoes=None, boot=0,
                      shin_guard=None, belt="#212121"),
    "general": dict(top="#546E7A", shorts="#263238", band=None, thigh_cover=0.45, arm_cover=0.45,
                    gloves=None, shoes="#ECEFF1", boot=0.08, shin_guard=None, belt=None),
}

# Rakip / antrenman partneri (renkler sporcudan ayrışsın)
PARTNER_OUTFITS = {
    "boxing": dict(OUTFITS["boxing"], shorts="#37474F", band="#90A4AE", gloves="#455A64", shoes="#37474F"),
    "kickboxing": dict(OUTFITS["kickboxing"], shorts="#424242", band="#BDBDBD", gloves="#546E7A",
                       shin_guard="#CFD8DC"),
    "wrestling": dict(OUTFITS["wrestling"], top="#C62828", shorts="#C62828", shoes="#7F0000"),
    "taekwondo": dict(OUTFITS["taekwondo"], hogu="#1E88E5"),
    "general": OUTFITS["general"],
}


# --------------------------------------------------------------------------
# Şekil yardımcıları
# --------------------------------------------------------------------------
def path(vertices, ins, outs, closed=True):
    return {"ty": "sh", "ks": static({"i": [list(p) for p in ins], "o": [list(p) for p in outs],
                                      "v": [list(p) for p in vertices], "c": closed})}


def smooth_path(points, closed=True, tension=1.0):
    """Catmull-Rom ile noktalardan geçen yumuşak bezier yol."""
    n = len(points)
    ins, outs = [], []
    for i in range(n):
        if closed:
            p0, p2 = points[(i - 1) % n], points[(i + 1) % n]
        else:
            p0, p2 = points[max(i - 1, 0)], points[min(i + 1, n - 1)]
        tx, ty = (p2[0] - p0[0]) / 6 * tension, (p2[1] - p0[1]) / 6 * tension
        ins.append((-tx, -ty))
        outs.append((tx, ty))
    return path(points, ins, outs, closed)


def capsule(y0, y1, r0, r1, x=0.0):
    """y0'dan y1'e (y1 < y0, yukarı) konik kapsül: y0'da r0, y1'de r1 yarıçap."""
    v = [(x + r0, y0), (x + r1, y1), (x, y1 - r1), (x - r1, y1), (x - r0, y0), (x, y0 + r0)]
    outs = [(0, 0), (0, -K * r1), (-K * r1, 0), (0, 0), (0, K * r0), (K * r0, 0)]
    ins = [(0, K * r0), (0, 0), (K * r1, 0), (0, -K * r1), (0, 0), (-K * r0, 0)]
    return path(v, ins, outs)


def ellipse(cx, cy, w, h):
    return {"ty": "el", "p": static([cx, cy]), "s": static([w, h]), "d": 1}


def rect(cx, cy, w, h, r=0):
    return {"ty": "rc", "p": static([cx, cy]), "s": static([w, h]), "r": static(r), "d": 1}


def fill(color, opacity=100):
    return {"ty": "fl", "c": static(rgba(color)), "o": static(opacity), "r": 1}


def stroke(color, width, opacity=100):
    return {"ty": "st", "c": static(rgba(color)), "o": static(opacity), "w": static(width), "lc": 2, "lj": 2}


def group(name, shapes, fill_color=None, line=None, line_w=2.0, opacity=100):
    """line: kontur rengi (None = konturs)."""
    items = list(shapes)
    if line:
        items.append(stroke(line, line_w))
    if fill_color:
        items.append(fill(fill_color, opacity))
    items.append(group_transform())
    return {"ty": "gr", "nm": name, "it": items}


def outline_for(color):
    """Açık renkli giysilerde gri, diğerlerinde koyu kontur."""
    h = color.lstrip("#")
    lum = sum(int(h[i:i + 2], 16) for i in (0, 2, 4)) / 3
    return WHITE_LINE if lum > 200 else shade(color, 0.45)


# --------------------------------------------------------------------------
# Vücut parçaları (katman içi şekil listeleri; listede önce gelen üstte çizilir)
# --------------------------------------------------------------------------
def limb_shapes(length, r0, r1, skin, cover_color=None, cover=0.0, cover_from=0.0, cover_pad=1.2,
                extra=None):
    """Uzuv: ten kapsülü + (varsa) giysi kaplaması + vurgu."""
    shapes = []
    if extra:
        shapes += extra
    if cover_color and cover > 0:
        a, b = cover_from, min(cover, 1.0)
        ra = r0 + (r1 - r0) * a + cover_pad
        rb = r0 + (r1 - r0) * b + cover_pad
        shapes.append(group("cover", [capsule(-length * a, -length * b, ra, rb)],
                            cover_color, outline_for(cover_color), 1.6))
    # vurgu (ışık): ön kenar boyunca ince açık şerit
    shapes.append(group("hl", [capsule(-length * 0.15, -length * 0.85, r0 * 0.28, r1 * 0.28, x=r0 * 0.38)],
                        shade(skin, 1.22), opacity=55))
    shapes.append(group("skin", [capsule(0, -length, r0, r1)], skin, shade(skin, 0.55), 1.6))
    return shapes


def torso_shapes(o, skin, partner=False):
    shapes = []
    # Göğüs koruyucu (tekvando partneri)
    if o.get("hogu"):
        shapes.append(group("hogu", [smooth_path([(19, -30), (21, -60), (17, -78), (-14, -80),
                                                  (-17, -55), (-14, -28)])],
                            o["hogu"], "#FFFFFF", 2.5))
    if o.get("belt"):
        shapes.append(group("belt_tail", [rect(13, -10, 5, 18, 2)], o["belt"]))
        shapes.append(group("belt", [rect(-1, -21, 34, 7, 2)], o["belt"]))
    if o.get("band"):
        shapes.append(group("band", [rect(-1, -22, 31, 6, 2)], o["band"], shade(o["band"], 0.6), 1.0))
    # Şort / pantolon bel kısmı
    shorts = o.get("shorts")
    if shorts:
        shapes.append(group("shorts", [smooth_path([(12, 7), (15, -9), (14, -23), (-15, -23),
                                                    (-18, -8), (-14, 7)])],
                            shorts, outline_for(shorts), 1.6))
    body_pts = [(11, 2), (13, -20), (15, -46), (19, -64), (17, -80), (9, -91),
                (-6, -92), (-15, -84), (-17, -62), (-13, -38), (-16, -14), (-13, 3)]
    top = o.get("top")
    if top:
        if o.get("belt"):  # dobok yakası
            shapes.append(group("collar", [smooth_path([(9, -90), (14, -78), (4, -62), (1, -64), (8, -78)],
                                                       tension=0.6)], shade(top, 0.82)))
        shapes.append(group("top", [smooth_path(body_pts)], top, outline_for(top), 1.8))
    else:
        # çıplak gövde: göğüs ve karın hatları
        shapes.append(group("pec", [smooth_path([(4, -67), (12, -60), (19, -63)], closed=False)],
                            line=shade(skin, 0.68), line_w=1.6))
        shapes.append(group("abs", [smooth_path([(9, -48), (12, -35), (11, -24)], closed=False)],
                            line=shade(skin, 0.75), line_w=1.4))
        shapes.append(group("skin", [smooth_path(body_pts)], skin, shade(skin, 0.55), 1.8))
    return shapes


def head_shapes(skin, hair=HAIR):
    cy = -(NECK + HEAD_R)
    cx = 3
    r = HEAD_R
    return [
        group("eye", [ellipse(cx + r * 0.62, cy - 2, 3.2, 3.6)], "#212121"),
        group("brow", [smooth_path([(cx + r * 0.38, cy - 7), (cx + r * 0.85, cy - 6.5)], closed=False)],
              line=hair, line_w=2.0),
        group("ear", [ellipse(cx - 2, cy + 1, 6, 9)], shade(skin, 0.88), shade(skin, 0.55), 1.2),
        group("hair", [smooth_path([(cx - r + 1, cy + 4), (cx - r * 0.85, cy - r * 0.55), (cx - r * 0.2, cy - r - 2),
                                    (cx + r * 0.55, cy - r * 0.92), (cx + r * 0.88, cy - r * 0.45),
                                    (cx + r * 0.3, cy - r * 0.62), (cx - r * 0.35, cy - r * 0.35),
                                    (cx - r * 0.6, cy + 0.2 * r)])], hair),
        group("nose", [smooth_path([(cx + r * 0.9, cy - 3), (cx + r * 0.9 + 5, cy + 4), (cx + r * 0.9, cy + 5)],
                                   tension=0.4)], skin, shade(skin, 0.55), 1.2),
        group("jaw", [ellipse(cx + 7, cy + 9, 15, 11)], skin),
        group("head", [ellipse(cx, cy, r * 1.9, r * 2.15)], skin, shade(skin, 0.55), 1.8),
        group("neck", [capsule(4, -NECK - 6, 6.5, 6.5, x=1)], shade(skin, 0.9), shade(skin, 0.55), 1.4),
    ]


def hand_shapes(o, skin, glove=None):
    if glove:
        return [
            group("glove_hl", [ellipse(-4, -12, 6, 10)], "#FFFFFF", opacity=35),
            group("thumb", [ellipse(8, -5, 8, 13)], glove, shade(glove, 0.5), 1.4),
            group("glove", [ellipse(0, -8, 23, 27)], glove, shade(glove, 0.5), 1.8),
            group("lace", [rect(0, 4, 13, 2.5)], "#FAFAFA", opacity=85),
            group("cuff", [rect(0, 4, 17, 11, 3)], shade(glove, 0.85), shade(glove, 0.5), 1.4),
        ]
    return [
        group("knuckle", [smooth_path([(-5, -9), (0, -11), (5, -9)], closed=False)],
              line=shade(skin, 0.6), line_w=1.2),
        group("fist", [ellipse(0, -5, 15, 16)], skin, shade(skin, 0.55), 1.6),
    ]


FOOT_PTS = [(6, 3), (7.5, -5), (4, -10.5), (-19, -10.5), (-24.5, -7.5), (-21, -3.5), (-11, -0.5), (-4, 4)]


def foot_shapes(o, skin):
    shoe = o.get("shoes")
    if shoe:
        return [
            group("sole", [smooth_path([(5, -9), (-21, -9), (-23, -11.5), (4, -12)], tension=0.5)],
                  "#FAFAFA" if shoe not in ("#ECEFF1",) else "#90A4AE"),
            group("shoe", [smooth_path([(7, 4), (8.5, -5), (5, -11), (-19, -11), (-25.5, -7.5), (-21, -2.5),
                                        (-11, 1), (-5, 6)])], shoe, outline_for(shoe), 1.6),
        ]
    return [group("foot", [smooth_path(FOOT_PTS)], skin, shade(skin, 0.55), 1.6)]


# --------------------------------------------------------------------------
# Figür kurulumu
# --------------------------------------------------------------------------
def build_figure(lb, keys, base_x, outfit, hip_track, parent=None, name="fig"):
    """Figürün katmanlarını ekler; çizim sırasına göre (üstten alta) katman ind listesi döner.

    keys      : [(frame, pose)] – tam pozlar
    hip_track : [(frame, [x, y, 0])] kalça konumları (parent'ın yerel koordinatında)
    """
    o = outfit
    skin = SKIN
    back_skin = shade(SKIN, 0.82)

    def track(fn):
        return animated([(f, [fn(p)]) for f, p in keys], 1)

    def rel(a, b):
        return lambda p: p[a] - (p[b] if b else 0)

    hip = lb.add(f"{name}_hip", 3, transform(animated(hip_track, 3, linear=True), static(0)), parent=parent)
    torso = lb.add(f"{name}_torso", 4, transform(static([0, 0, 0]), track(rel("t", None))),
                   torso_shapes(o, skin), parent=hip)
    head = lb.add(f"{name}_head", 4, transform(static([0, -TORSO, 0]), static(0)), head_shapes(skin), parent=torso)

    def side_layers(prefix, skin_c, dark):
        sh = (lambda c: shade(c, 0.84)) if dark else (lambda c: c)
        top = o.get("top")
        arm_cover_color = sh(top) if top and o.get("arm_cover") else None
        sy = -(TORSO - SHOULDER_DROP)
        ua = lb.add(f"{name}_{prefix}_upper_arm", 4,
                    transform(static([0, sy, 0]), track(rel(prefix + "ua", "t"))),
                    limb_shapes(UPPER_ARM, 9.5, 7, skin_c, arm_cover_color, o.get("arm_cover", 0)), parent=torso)
        fa = lb.add(f"{name}_{prefix}_forearm", 4,
                    transform(static([0, -UPPER_ARM, 0]), track(rel(prefix + "fa", prefix + "ua"))),
                    limb_shapes(FOREARM, 7.5, 5.5, skin_c, arm_cover_color if o.get("forearm_cover") else None,
                                o.get("forearm_cover", 0)), parent=ua)
        glove = sh(o["gloves"]) if o.get("gloves") else None
        hand = lb.add(f"{name}_{prefix}_hand", 4, transform(static([0, -FOREARM, 0]), static(0)),
                      hand_shapes(o, skin_c, glove), parent=fa)
        shorts = o.get("shorts")
        th = lb.add(f"{name}_{prefix}_thigh", 4,
                    transform(static([0, 0, 0]), track(rel(prefix + "th", None))),
                    limb_shapes(THIGH, 12.5, 8.5, skin_c, sh(shorts) if shorts else None, o.get("thigh_cover", 0),
                                cover_pad=2.0), parent=hip)
        shin_cover_color, cover, cover_from = None, 0.0, 0.0
        if o.get("shin_cover"):
            shin_cover_color, cover = sh(shorts), o["shin_cover"]
        elif o.get("shin_guard"):
            shin_cover_color, cover, cover_from = sh(o["shin_guard"]), 0.9, 0.12
        elif o.get("shoes") and o.get("boot"):
            shin_cover_color, cover, cover_from = sh(o["shoes"]), 1.0, 1.0 - o["boot"]
        shn = lb.add(f"{name}_{prefix}_shin", 4,
                     transform(static([0, -THIGH, 0]), track(rel(prefix + "sh", prefix + "th"))),
                     limb_shapes(SHIN, 8.5, 5.5, skin_c, shin_cover_color, cover, cover_from), parent=th)
        foot_o = dict(o, shoes=sh(o["shoes"]) if o.get("shoes") else None)
        foot = lb.add(f"{name}_{prefix}_foot", 4, transform(static([0, -SHIN, 0]), static(0)),
                      foot_shapes(foot_o, skin_c), parent=shn)
        return dict(ua=ua, fa=fa, hand=hand, th=th, sh=shn, foot=foot)

    f = side_layers("f", skin, False)
    b = side_layers("b", back_skin, True)
    order = [f["hand"], f["fa"], f["ua"], head, torso, f["foot"], f["sh"], f["th"],
             b["foot"], b["sh"], b["th"], b["hand"], b["fa"], b["ua"], hip]
    return order
