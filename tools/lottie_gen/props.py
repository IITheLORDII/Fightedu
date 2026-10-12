"""Sahne nesneleri: zemin, gölge, kum torbası, darbe efekti ve vuruş tespiti."""
from body import ellipse, fill, group, rect, smooth_path, stroke
from rig import GROUND, H, W, animated, group_transform, shade, static, transform, world_points

STRIKE_POINTS = ["ffist", "bfist", "ftoe", "fheel", "btoe", "bheel", "fknee", "bknee"]


def floor_layers(lb, color="#DCE2E6"):
    floor = lb.add("floor", 4, transform(static([0, 0, 0]), static(0)), [
        group("line", [smooth_path([(0, GROUND + 1), (W, GROUND + 1)], closed=False)], line="#B0BEC5", line_w=2),
        group("floor", [rect(W / 2, (GROUND + H) / 2 + 1, W, H - GROUND + 2)], color),
    ])
    return floor


def shadow_layer(lb, hip_track, width=150):
    track = [(f, [v[0], GROUND + 2, 0]) for f, v in hip_track]
    return lb.add("shadow", 4, transform(animated(track, 3, linear=True), static(0)), [
        {"ty": "gr", "nm": "shadow", "it": [ellipse(0, 0, width, 11), fill("#000000", 13), group_transform()]},
    ])


# --------------------------------------------------------------------------
# Vuruş tespiti
# --------------------------------------------------------------------------
def reach_profile(keys, base_x, dur, direction=1):
    """Her kare için en ileri uç noktası: [(frame, x*direction, (x, y), isim)]."""
    out = []
    for f in range(dur + 1):
        pts = world_points(keys, base_x, f)
        name = max(STRIKE_POINTS, key=lambda n: pts[n][0] * direction)
        out.append((f, pts[name][0] * direction, pts[name], name))
    return out


HIT_PAD = {"bknee": 11, "fknee": 11, "bankle": 8, "fankle": 8}


def explicit_hits(keys, base_x, hits, direction=1):
    """[(kare, nokta)] -> [(kare, erişim, (x, y), nokta)]."""
    out = []
    for f, name in hits:
        x, y = world_points(keys, base_x, f)[name]
        x += HIT_PAD.get(name, 0) * direction
        out.append((f, x * direction, (x, y), name))
    return out


def find_hits(profile, window=24):
    """Erişimin, maksimuma yakın yerel tepe noktaları = darbe anları."""
    rmax = max(r for _, r, _, _ in profile)
    hits = []
    for i in range(1, len(profile) - 1):
        f, r, pt, name = profile[i]
        # tepeye ilk ulaşılan kare (bekleme/plato varsa başlangıcı)
        if r >= rmax - window and r > profile[i - 1][1] + 0.05 and r >= profile[i + 1][1] - 0.3:
            if hits and f - hits[-1][0] < 6:
                continue
            hits.append((f, r, pt, name))
    return hits


# --------------------------------------------------------------------------
# Kum torbası
# --------------------------------------------------------------------------
def bag_layers(lb, x_left, hits, dur, long_bag=False):
    width = 58
    cx = x_left + width / 2
    pivot_y = 16
    body_top = 58
    body_h = (GROUND - 20 - body_top) if long_bag else 205
    leather = "#263238" if long_bag else "#7B1E1E"

    # sallanma: darbe yönü sağa -> saat yönünün tersi (negatif açı)
    rot = [(0, [0])]
    for i, (f, *_rest) in enumerate(hits):
        nxt = hits[i + 1][0] if i + 1 < len(hits) else dur
        amp = 3 if long_bag else 5
        seq = [(f, [0]), (f + 7, [-amp]), (f + 15, [amp * 0.4]), (f + 23, [0])]
        rot += [kf for kf in seq if kf[0] < nxt and kf[0] < dur]
    rot.append((dur, [0]))
    rot = sorted({f: v for f, v in rot}.items())

    bracket = lb.add("bag_bracket", 4, transform(static([cx, pivot_y, 0]), static(0)), [
        group("bracket", [rect(0, -6, 46, 8, 2)], "#546E7A"),
        group("hook", [ellipse(0, 0, 8, 8)], "#78909C"),
    ])
    rel_top = body_top - pivot_y
    bag = lb.add("bag", 4, transform(static([cx, pivot_y, 0]), animated(rot, 1)), [
        group("logo", [ellipse(0, rel_top + body_h * 0.42, 26, 26)], "#FFFFFF", opacity=18),
        group("hl", [rect(-15, rel_top + body_h / 2, 9, body_h - 26, 4)], "#FFFFFF", opacity=14),
        group("band_bottom", [rect(0, rel_top + body_h - 16, width, 7)], shade(leather, 0.7)),
        group("band_top", [rect(0, rel_top + 16, width, 7)], shade(leather, 0.7)),
        group("body", [rect(0, rel_top + body_h / 2, width, body_h, 16)], leather, shade(leather, 0.5), 2),
        group("chains", [
            smooth_path([(0, 0), (-width / 2 + 4, rel_top + 2)], closed=False),
            smooth_path([(0, 0), (width / 2 - 4, rel_top + 2)], closed=False),
            smooth_path([(0, 0), (0, rel_top)], closed=False),
        ], line="#90A4AE", line_w=2.5),
    ])
    return [bag, bracket]


def impact_layers(lb, hits, dur):
    """Temas noktasında kısa süreli darbe yıldızı."""
    inds = []
    for i, (f, _r, (x, y), _n) in enumerate(hits):
        start = max(f - 1, 0)
        end = min(f + 6, dur)
        op = [(0, [0]), (start, [0]), (f, [100]), (end, [0]), (dur, [0])]
        op = sorted({k: v for k, v in op}.items())
        sc = [(0, [40, 40, 100]), (f, [40, 40, 100]), (end, [150, 150, 100]), (dur, [150, 150, 100])]
        sc = sorted({k: v for k, v in sc}.items())
        star = {"ty": "sr", "sy": 1, "d": 1, "pt": static(8), "p": static([0, 0]), "r": static(0),
                "ir": static(6), "is": static(0), "or": static(17), "os": static(0)}
        inds.append(lb.add(f"impact_{i}", 4,
                           transform(static([x, y, 0]), static(0), s=animated(sc, 3, linear=True),
                                     o=animated(op, 1, linear=True)),
                           [{"ty": "gr", "nm": "star", "it": [star, stroke("#FF6F00", 2), fill("#FFD54F"),
                                                             group_transform()]}]))
    return inds

