"""3B iskelet: vücut ölçüleri, poz parametreleri, ters kinematik (IK).

Bir poz; kalça (pelvis) konumu/yönü, göğsün kalçaya göre dönüşü, başın bakışı, ellerin ve
ayakların hedef konumlarıyla tanımlanır. Dirsek ve dizler iki kemikli IK ile hesaplanır.
Tüm ölçüler santimetre; koordinatlar sporcunun kendi "taban" çerçevesindedir
(X ileri, Y yukarı, Z sağ) ve sahnede taban konumu/yönüyle dünyaya taşınır.
"""
import math

from mathx import (WORLD, add, cross, dir_in_frame, in_frame, length, lerp, madd, periodic_pchip,
                   reject, rotate_frame, smoothstep, sub, to_frame, unit, yaw_frame)

# --------------------------------------------------------------------------
# Vücut ölçüleri (~178 cm atletik yetişkin)
# --------------------------------------------------------------------------
HIP_HALF = 9.0        # pelvis merkezi -> kalça eklemi (yana)
HIP_DOWN = 3.0        # kalça eklemleri pelvis merkezinin biraz altında
CHEST_UP = 17.0       # pelvis merkezi -> göğüs dönme noktası (bel üstü)
SHOULDER_UP = 27.5    # göğüs noktası -> omuz eklemleri
SHOULDER_HALF = 17.5
SHOULDER_BACK = 1.5
NECK_UP = 31.5        # göğüs noktası -> boyun kökü
NECK_LEN = 8.5
HEAD_R = 10.3         # kafatası yarıçapı
HEAD_UP = 9.5         # boyun üstü -> kafa merkezi
HEAD_FWD = 1.2
UPPER_ARM = 29.0
FOREARM = 25.5
HAND = 7.0            # bilek -> yumruk merkezi
THIGH = 44.0
SHIN = 43.0
ANKLE_H = 7.8         # düz basan ayakta bilek yüksekliği
FOOT_BALL = 13.5      # bilek -> ayak tabanı ön (top) noktası (ileri)
FOOT_BALL_DOWN = 4.8
BALL_R = 3.0
PLANTED_MAX_Y = 14.0  # bileği bu yükseklikten alçak ayak "yere basıyor" sayılır

STAND_Y = 97.0        # ayakta pelvis merkezi yüksekliği

# --------------------------------------------------------------------------
# Poz parametreleri (hepsi sayısal; keyframe'ler arasında enterpolasyon yapılır)
# --------------------------------------------------------------------------
VEC_KEYS = {
    "lh": 3, "rh": 3,        # el hedefi – göğüs çerçevesinde (ileri, yukarı, sağ)
    "lhw": 3, "rhw": 3,      # el hedefi – taban (dünya) çerçevesinde
    "le": 3, "re": 3,        # dirsek yön ipucu (göğüs çerçevesinde)
    "lfa": 3, "rfa": 3,      # ayak bileği hedefi (taban çerçevesi)
    "lfk": 3, "rfk": 3,      # diz yön ipucu (taban çerçevesi)
}
SCALAR_KEYS = [
    "x", "y", "z", "yaw", "pitch", "roll",      # pelvis
    "cyaw", "cpitch", "croll",                  # göğüs (kalçaya göre)
    "look", "hyaw", "hpitch", "hroll", "chin",  # baş
    "lhk", "rhk",                               # 0 = el göğüs çerçevesinde, 1 = dünyada
    "lfy", "lfp", "rfy", "rfp",                 # ayak yönü (yaw) ve eğimi (pitch, + = parmak aşağı)
    "lfr", "rfr",                               # ayak bileği dönüşü (roll, + = taban içe döner)
    "lsup", "rsup",                             # önkol supinasyonu (derece, + = avuç yukarı döner)
    "autoy",                                    # 1 = basan ayaklar için kalçayı otomatik indir
]


def planted(x, z, yaw=0.0, heel=0.0):
    """Yere basan ayak: top noktası (x, z)'de, yaw derece, topuk 'heel' derece kalkık."""
    fy = math.radians(yaw)
    p = math.radians(heel)
    fd0 = (math.cos(fy), 0.0, math.sin(fy))
    up = (0.0, 1.0, 0.0)
    # topuk kalkarken ayak, top noktası etrafında döner
    fd = madd((0, 0, 0), (fd0, math.cos(p)), (up, -math.sin(p)))
    fu = madd((0, 0, 0), (up, math.cos(p)), (fd0, math.sin(p)))
    ball = (x, BALL_R, z)
    ankle = madd(ball, (fd, -FOOT_BALL), (fu, FOOT_BALL_DOWN))
    knee = (math.cos(fy), 0.12, math.sin(fy))
    return {"a": ankle, "yaw": yaw, "pitch": heel, "knee": knee}


def air(ankle, yaw=0.0, pitch=0.0, knee=None, roll=0.0):
    """Havadaki ayak: bilek konumu, ayak yönü (yaw), eğimi (pitch + = parmak ucu aşağı),
    bilek dönüşü (roll + = taban içe, örn. dönen tekmede ayak üstü hedefe bakar)."""
    if knee is None:
        fy = math.radians(yaw)
        knee = (math.cos(fy), 0.3, math.sin(fy))
    return {"a": tuple(ankle), "yaw": yaw, "pitch": pitch, "knee": tuple(knee), "roll": roll}


BASE_POSE = {
    "x": 0.0, "y": STAND_Y, "z": 0.0, "yaw": 0.0, "pitch": 0.0, "roll": 0.0,
    "cyaw": 0.0, "cpitch": 0.0, "croll": 0.0,
    "look": 1.0, "hyaw": 0.0, "hpitch": 0.0, "hroll": 0.0, "chin": 0.0,
    "lh": (2.0, -33.0, -21.0), "rh": (2.0, -33.0, 21.0), "lhk": 0.0, "rhk": 0.0,
    "le": (-1.0, -0.2, -0.3), "re": (-1.0, -0.2, 0.3),
    "lf": planted(2.0, -11.0, -6.0), "rf": planted(2.0, 11.0, 6.0),
    "autoy": 1.0,
}


def merge(base, **kw):
    d = dict(base)
    d.update(kw)
    return d


# --------------------------------------------------------------------------
# Çerçeveler
# --------------------------------------------------------------------------
class Base:
    """Bir figürün sahnedeki taban konumu ve yönü."""

    def __init__(self, x=0.0, z=0.0, yaw=0.0):
        self.x, self.z, self.yaw = x, z, yaw
        self.frame = yaw_frame(yaw)
        self.origin = (x, 0.0, z)

    def point(self, p):
        return in_frame(self.frame, self.origin, *p)

    def vector(self, v):
        return dir_in_frame(self.frame, *v)

    def local_point(self, w):
        return to_frame(self.frame, sub(w, self.origin))


def frames_for(p, base):
    """Pelvis ve göğüs çerçevelerini ve pelvis merkezini döndürür (dünya)."""
    pel_local = rotate_frame(WORLD, p["yaw"], p["pitch"], p["roll"])
    pelvis = tuple(base.vector(v) for v in pel_local)
    chest = rotate_frame(pelvis, p["cyaw"], p["cpitch"], p["croll"])
    origin = base.point((p["x"], p["y"], p["z"]))
    return pelvis, chest, origin


def chest_origin(pelvis, origin):
    return madd(origin, (pelvis[1], CHEST_UP))


# --------------------------------------------------------------------------
# Keyframe normalizasyonu ve enterpolasyon
# --------------------------------------------------------------------------
def normalize_key(pose, base):
    """Yazar pozunu tam sayısal vektöre çevirir; ellerin hem göğüs hem dünya koordinatını
    doldurur (enterpolasyonun iki çerçeve arasında yumuşak geçmesi için)."""
    p = dict(BASE_POSE)
    p.update(pose)
    pelvis, chest, origin = frames_for(p, base)
    c0 = chest_origin(pelvis, origin)
    out = {k: float(p[k]) for k in SCALAR_KEYS if k in p and not isinstance(p[k], (tuple, dict))}
    for side in ("l", "r"):
        has_c = side + "h" in pose
        has_w = side + "hw" in pose
        if has_w and not has_c:
            hw = tuple(pose[side + "hw"])
            hc = to_frame(chest, sub(base.point(hw), c0))
        elif has_w and has_c:
            hw = tuple(pose[side + "hw"])
            hc = tuple(pose[side + "h"])
        else:
            hc = tuple(p[side + "h"])
            hw = base.local_point(in_frame(chest, c0, *hc))
        out[side + "hk"] = float(pose.get(side + "hk", 1.0 if (has_w and not has_c) else 0.0))
        out[side + "h"] = hc
        out[side + "hw"] = hw
        out[side + "e"] = tuple(p[side + "e"])
        foot = p[side + "f"]
        out[side + "fa"] = tuple(foot["a"])
        out[side + "fk"] = tuple(foot["knee"])
        out[side + "fy"] = float(foot["yaw"])
        out[side + "fp"] = float(foot["pitch"])
        out[side + "fr"] = float(foot.get("roll", 0.0))
    for k in SCALAR_KEYS:
        out.setdefault(k, float(BASE_POSE.get(k, 0.0)))
    return out


def flatten(key):
    vals = [key[k] for k in SCALAR_KEYS]
    for k, n in VEC_KEYS.items():
        vals.extend(key[k])
    return vals


def unflatten(vals):
    out = {}
    i = 0
    for k in SCALAR_KEYS:
        out[k] = vals[i]
        i += 1
    for k, n in VEC_KEYS.items():
        out[k] = tuple(vals[i:i + n])
        i += n
    return out


def mirror_pose(pose):
    """Pozu sporcunun kendi sağ-sol eksenine göre aynala (ortodoks <-> solak)."""
    out = {}
    neg = {"z", "yaw", "roll", "cyaw", "croll", "hyaw", "hroll"}
    swap = {"lh": "rh", "rh": "lh", "lhw": "rhw", "rhw": "lhw", "le": "re", "re": "le",
            "lhk": "rhk", "rhk": "lhk", "lf": "rf", "rf": "lf", "lsup": "rsup", "rsup": "lsup"}
    for k, v in pose.items():
        nk = swap.get(k, k)
        if k in neg:
            v = -v
        elif k in ("lh", "rh", "lhw", "rhw", "le", "re"):
            v = (v[0], v[1], -v[2])
        elif k in ("lf", "rf"):
            v = {"a": (v["a"][0], v["a"][1], -v["a"][2]), "yaw": -v["yaw"], "pitch": v["pitch"],
                 "knee": (v["knee"][0], v["knee"][1], -v["knee"][2]), "roll": v.get("roll", 0.0)}
        out[nk] = v
    return out


class Track:
    """Keyframe listesinden her kare için poz üretir (döngüsel)."""

    def __init__(self, keys, dur, base, mirror=False):
        if keys[0][0] != 0:
            raise ValueError("ilk keyframe 0 olmalı")
        if mirror:
            keys = [(t, mirror_pose(merge(BASE_POSE, **p))) for t, p in keys]
        keys = [(t, normalize_key(p, base)) for t, p in keys if t < dur]
        self.times = [t for t, _ in keys]
        flat = [flatten(k) for _, k in keys]
        self.funcs = [periodic_pchip(self.times, [row[i] for row in flat], dur) for i in range(len(flat[0]))]
        self.dur = dur

    def at(self, t):
        return unflatten([f(t) for f in self.funcs])


# --------------------------------------------------------------------------
# IK ve iskelet değerlendirmesi
# --------------------------------------------------------------------------
def ik2(root, target, l1, l2, pole):
    d = sub(target, root)
    dist = length(d)
    dirv = unit(d, (0.0, -1.0, 0.0))
    dist_c = min(max(dist, abs(l1 - l2) + 0.5), l1 + l2 - 0.05)
    end = madd(root, (dirv, dist_c))
    a = (l1 * l1 + dist_c * dist_c - l2 * l2) / (2 * l1 * dist_c)
    a = max(-1.0, min(1.0, a))
    pv = reject(pole, dirv)
    if length(pv) < 1e-6:
        pv = reject((0.0, 1.0, 0.0), dirv)
        if length(pv) < 1e-6:
            pv = reject((1.0, 0.0, 0.0), dirv)
    pv = unit(pv)
    mid = madd(root, (dirv, l1 * a), (pv, l1 * math.sqrt(max(0.0, 1 - a * a))))
    return mid, end


class Skeleton:
    """Bir karedeki tüm eklem noktaları ve çerçeveler (dünya koordinatı)."""

    def __init__(self, p, base, look_target=None):
        self.p = p
        pelvis, chest, origin = frames_for(p, base)

        # basan ayaklara ulaşmak için kalçayı otomatik indir
        feet = {s: base.point(p[s + "fa"]) for s in ("l", "r")}
        if p["autoy"] > 0.5:
            drop = 0.0
            reach = THIGH + SHIN - 0.6
            for s, sgn in (("l", -1), ("r", 1)):
                if p[s + "fa"][1] > PLANTED_MAX_Y:
                    continue
                hj = madd(origin, (pelvis[2], sgn * HIP_HALF), (pelvis[1], -HIP_DOWN))
                d = sub(feet[s], hj)
                h2 = d[0] * d[0] + d[2] * d[2]
                if h2 < reach * reach:
                    need = -math.sqrt(reach * reach - h2) - d[1]
                    drop = max(drop, need)
            origin = (origin[0], origin[1] - drop, origin[2])

        self.pelvis, self.chest, self.origin = pelvis, chest, origin
        c0 = chest_origin(pelvis, origin)
        self.c0 = c0
        f, u, r = chest
        self.neck_base = madd(c0, (u, NECK_UP), (f, -SHOULDER_BACK))

        # baş: hedefe bakış
        yaw, pitch = p["hyaw"], p["hpitch"] + p["chin"]
        if look_target is not None and p["look"] > 0.001:
            eye = madd(self.neck_base, (u, 20.0))
            d = unit(sub(look_target, eye))
            df, du, dr = to_frame(chest, d)
            ay = math.degrees(math.atan2(dr, df))
            ap = -math.degrees(math.atan2(du, math.hypot(df, dr)))
            ay = max(-75.0, min(75.0, ay))
            ap = max(-40.0, min(45.0, ap))
            yaw += p["look"] * ay
            pitch += p["look"] * ap
        self.head = rotate_frame(chest, yaw, pitch, p["hroll"])
        hf, hu, hr = self.head
        neck_dir = unit(add(u, hu))
        self.neck_top = madd(self.neck_base, (neck_dir, NECK_LEN))
        self.head_c = madd(self.neck_top, (hu, HEAD_UP), (hf, HEAD_FWD))

        self.j = {}
        for s, sgn in (("l", -1), ("r", 1)):
            sh = madd(c0, (u, SHOULDER_UP), (r, sgn * SHOULDER_HALF), (f, -SHOULDER_BACK))
            tc = in_frame(chest, c0, *p[s + "h"])
            tw = base.point(p[s + "hw"])
            target = lerp(tc, tw, max(0.0, min(1.0, p[s + "hk"])))
            pole = dir_in_frame(chest, *p[s + "e"])
            elbow, hand = ik2(sh, target, UPPER_ARM, FOREARM + HAND, pole)
            fdir = unit(sub(hand, elbow))
            wrist = madd(elbow, (fdir, FOREARM))
            self.j[s + "shoulder"] = sh
            self.j[s + "elbow"] = elbow
            self.j[s + "wrist"] = wrist
            self.j[s + "hand"] = hand

            hip = madd(origin, (pelvis[2], sgn * HIP_HALF), (pelvis[1], -HIP_DOWN))
            kpole = base.vector(p[s + "fk"])
            knee, ankle = ik2(hip, feet[s], THIGH, SHIN, kpole)
            self.j[s + "hip"] = hip
            self.j[s + "knee"] = knee
            self.j[s + "ankle"] = ankle

            # ayak çerçevesi
            fy = math.radians(p[s + "fy"])
            fp = math.radians(p[s + "fp"])
            fd_l = (math.cos(fy) * math.cos(fp), -math.sin(fp), math.sin(fy) * math.cos(fp))
            fr_l = (-math.sin(fy), 0.0, math.cos(fy))
            fd = base.vector(fd_l)
            frr = base.vector(fr_l)
            fu = cross(frr, fd)
            fr_ang = math.radians(p[s + "fr"]) * (1.0 if s == "r" else -1.0)
            if fr_ang:
                # taban içe: sağ ayakta üst yüz dışa (+Z) döner
                fu, frr = madd((0, 0, 0), (fu, math.cos(fr_ang)), (frr, math.sin(fr_ang))), \
                    madd((0, 0, 0), (frr, math.cos(fr_ang)), (fu, -math.sin(fr_ang)))
            flat = base.vector((math.cos(fy), 0.0, math.sin(fy)))
            airness = smoothstep(10.0, 22.0, ankle[1])
            toe_dir = unit(lerp(flat, fd, airness))
            self.j[s + "foot"] = (fd, fu, frr, toe_dir)
            ball = madd(ankle, (fd, FOOT_BALL), (fu, -FOOT_BALL_DOWN))
            self.j[s + "ball"] = ball
            self.j[s + "toe"] = madd(ball, (toe_dir, 6.0))
            self.j[s + "heel"] = madd(ankle, (fd, -5.5), (fu, -5.0))
        self.j["head"] = self.head_c

    def point(self, name):
        if name == "head":
            return self.head_c
        if name == "chest":
            return madd(self.c0, (self.chest[1], 14.0), (self.chest[0], 10.0))
        if name == "pelvis":
            return self.origin
        if name.endswith("shin"):
            # tekmede vuran yüzey: kaval kemiğinin alt yarısı
            return lerp(self.j[name[0] + "knee"], self.j[name[0] + "ankle"], 0.6)
        return self.j[name]


# --------------------------------------------------------------------------
# Yazım yardımcıları
# --------------------------------------------------------------------------
_ORIGIN_BASE = Base(0.0, 0.0, 0.0)


def solve_point(pose, name):
    """Pozdaki bir noktanın taban koordinatı (bakış hedefi olmadan çözülür)."""
    sk = Skeleton(normalize_key(pose, _ORIGIN_BASE), _ORIGIN_BASE, None)
    return sk.point(name)


def hand_at(pose, side, offset, ref="shoulder"):
    """El hedefini, aynı pozdaki omuz (ya da başka nokta) + offset olarak dünyada sabitle."""
    base_pt = solve_point(pose, side + ref) if ref in ("shoulder", "hip", "elbow") else solve_point(pose, ref)
    target = (base_pt[0] + offset[0], base_pt[1] + offset[1], base_pt[2] + offset[2])
    return merge(pose, **{side + "hw": target, side + "hk": 1.0})


def _rot_xz(x, z, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return x * c - z * s, x * s + z * c


def turn(pose, deg, about=(0.0, 0.0)):
    """Pozu dikey eksen etrafında döndür (deg + = sağa). Ayaklar ve dünya el hedefleri de döner."""
    p = merge(BASE_POSE, **pose)
    ax, az = about
    out = dict(p)
    x, z = _rot_xz(p["x"] - ax, p["z"] - az, deg)
    out["x"], out["z"] = x + ax, z + az
    out["yaw"] = p["yaw"] + deg
    for s in ("l", "r"):
        f = p[s + "f"]
        a = f["a"]
        fx, fz = _rot_xz(a[0] - ax, a[2] - az, deg)
        kx, kz = _rot_xz(f["knee"][0], f["knee"][2], deg)
        out[s + "f"] = {"a": (fx + ax, a[1], fz + az), "yaw": f["yaw"] + deg, "pitch": f["pitch"],
                        "knee": (kx, f["knee"][1], kz)}
        if s + "hw" in pose:
            w = pose[s + "hw"]
            wx, wz = _rot_xz(w[0] - ax, w[2] - az, deg)
            out[s + "hw"] = (wx + ax, w[1], wz + az)
    return out


def shift(pose, dx=0.0, dz=0.0):
    """Pozu (pelvis, ayaklar, dünya el hedefleri) yatayda kaydır."""
    p = merge(BASE_POSE, **pose)
    out = dict(p)
    out["x"], out["z"] = p["x"] + dx, p["z"] + dz
    for s in ("l", "r"):
        f = p[s + "f"]
        a = f["a"]
        out[s + "f"] = dict(f, a=(a[0] + dx, a[1], a[2] + dz))
        if s + "hw" in pose:
            w = pose[s + "hw"]
            out[s + "hw"] = (w[0] + dx, w[1], w[2] + dz)
    return out
