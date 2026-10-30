"""Anatomik yontu haritası: kasları ayrı karınlar ve aralarındaki oluklar olarak deriye işler.

Bir heykeltıraşın yüksek çözünürlüklü yontusunun yerini tutar. Her kas (deltoidin üç başı, pektoral,
karın dilimleri, serratus dişleri, oblik, latissimus, biseps/triseps, önkol grupları, kuadriseps,
baldır...) dinlenme pozunda tanımlı bir yükseklik alanıdır: + kas karnı, - kaslar arası oluk.
Alan ikiye bölünür: yumuşatılmış kısmı (kas kütleleri) temel ağın köşelerine işlenir, böylece giysiler
ve kumaş çarpışma vekili aynı hacmi taşır; kalan ince ayrıntı (oluklar, kas sınırları) gövdenin UV
düzlemine 2048² kayan noktalı bir görüntü olarak pişirilir ve render'da Subsurf'ten sonra gelen
Displace modifier'ıyla uygulanır (gövde UV'sini taşıyan giysilere de). Ayrıntı iskeletle birlikte
deforme olur; maske/ağırlık düzeni temel ağda kalır.

Koordinatlar Blender düzenindedir (metre, Z yukarı, karakter -Y'ye bakar, +X sol taraf). Gövde
özellikleri simetriktir ve |x| üzerinde tanımlanır. Uzuv özellikleri kemik çerçevesindedir:
t kemik boyunca (0 baş, 1 uç), açı 0 = ön, +90 = dış yan, 180 = arka, -90 = iç yan.
"""
import hashlib
import os

import numpy as np

SIZE = 2048
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "anatomy")
MM = 1e-3

ARM_BONES = ("upperarm", "upperarm_twist", "lowerarm", "lowerarm_twist", "hand", "thumb_01", "thumb_02",
             "thumb_03", "index_01", "index_02", "index_03", "middle_01", "middle_02", "middle_03",
             "ring_01", "ring_02", "ring_03", "pinky_01", "pinky_02", "pinky_03")
LEG_BONES = ("thigh", "thigh_twist", "calf", "foot", "ball")


# --------------------------------------------------------------------------------
# Şekil yardımcıları
# --------------------------------------------------------------------------------
def ss(e0, e1, x):
    """Yumuşak basamak; e0 > e1 ise tersine döner."""
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def dome(d, p=0.6):
    """Normalize uzaklık d (0 merkez, 1 kenar) -> yuvarlak kas karnı."""
    return np.clip(1.0 - d * d, 0.0, None) ** p


def superd(a, b, n=2.8):
    return (np.abs(a) ** n + np.abs(b) ** n) ** (1.0 / n)


def gauss(d, w):
    return np.exp(-(d / w) ** 2)


def polyline(P, pts):
    """P'nin (n, d) kırık çizgiye uzaklığı ve çizgi boyunca 0..1 konumu."""
    pts = np.asarray(pts, dtype=np.float64)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    acc = np.concatenate([[0.0], np.cumsum(seg)]) / max(seg.sum(), 1e-9)
    best = np.full(len(P), np.inf)
    pos = np.zeros(len(P))
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        ab = b - a
        t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0.0, 1.0)
        d = np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
        m = d < best
        best[m] = d[m]
        pos[m] = acc[i] + t[m] * (acc[i + 1] - acc[i])
    return best, pos


def ellipsoid(P, c, axes, radii):
    """Eksenleri (3x3, satırlar) ve yarıçaplarıyla elipsoid normalize uzaklığı."""
    q = (P - c) @ np.asarray(axes).T / np.asarray(radii)
    return np.sqrt((q * q).sum(axis=1))


def _unit(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v)


# --------------------------------------------------------------------------------
# Anatomi
# --------------------------------------------------------------------------------
class Anatomy:
    def __init__(self, base, verts, rig, k):
        self.k = k
        self.rig = rig
        bone = lambda n: (np.asarray(rig.bones[n]["head"], float), np.asarray(rig.bones[n]["tail"], float))
        self.bone = bone
        self.sh = bone("upperarm_l")[0]
        self.hip = bone("thigh_l")[0]
        self.neck = bone("neck_01")[0]
        self.nip_z = self.sh[2] - 0.165 * k
        body = base.groups["body"]
        bv = verts[body]
        arm_w = np.zeros(len(verts))
        for b in ARM_BONES:
            for s in ("l", "r"):
                for vi, w in rig.skin_weights.get(f"{b}_{s}", []):
                    arm_w[int(vi)] += w
        keep = arm_w[body] < 0.3
        self.torso = bv[keep]
        # göbek: ön orta hatta en çukur nokta
        m = (np.abs(self.torso[:, 0]) < 0.005 * k) & (np.abs(self.torso[:, 2] - (self.hip[2] + 0.12 * k)) < 0.05 * k) \
            & (self.torso[:, 1] < self.sh[1])
        c = self.torso[m]
        self.navel = c[np.argmax(c[:, 1])] if len(c) else np.array([0.0, -0.1 * k, self.hip[2] + 0.12 * k])

    # -- yüzey çapaları ------------------------------------------------------------
    def front(self, x, z, back=False, tol=0.008):
        k = self.k
        t = self.torso
        m = (np.abs(t[:, 0] - x) < tol * k) & (np.abs(t[:, 2] - z) < tol * k)
        if not m.any():
            return np.array([x, 0.0, z])
        y = t[m, 1].max() if back else t[m, 1].min()
        return np.array([x, y, z])

    def around(self, z, az, tol=0.008):
        """z yüksekliğindeki gövde kesitinde azimut açısındaki (0 = ön, 90 = sol yan, 180 = arka) yüzey noktası."""
        k = self.k
        t = self.torso
        sec = t[(np.abs(t[:, 2] - z) < tol * k) & (np.abs(t[:, 0]) < 0.25 * k)]
        cy = 0.5 * (sec[:, 1].min() + sec[:, 1].max())
        a = np.degrees(np.arctan2(sec[:, 0], -(sec[:, 1] - cy)))
        d = np.abs((a - az + 180.0) % 360.0 - 180.0)
        return sec[np.argmin(d)]

    # -- alan ----------------------------------------------------------------------
    def height(self, P, N, W):
        """P, N: (n, 3) dinlenme konumu/normali; W: kemik adı -> (n,) deri ağırlığı. Döner: (n,) metre."""
        k = self.k
        h = np.zeros(len(P))
        arm = sum(W.get(f"{b}_{s}", 0.0) for b in ARM_BONES for s in ("l", "r"))
        torso_m = np.clip(1.0 - arm, 0.0, 1.0)
        # gövde: sol yarıda tanımlı; sağ yarı aynalanmış noktalarla aynı fonksiyondan gelir. İki katkı toplanır
        # (|x| ile aynalamak orta hatta kırışık çizgi bırakırdı); orta hattaki özellikler yarım ağırlıklıdır
        flip = np.array([-1.0, 1.0, 1.0])
        sel = np.nonzero(torso_m > 0.02)[0]
        if len(sel):
            h[sel] += torso_m[sel] * (self._torso(P[sel], N[sel]) + self._torso(P[sel] * flip, N[sel] * flip))
        for s, sgn in (("l", 1.0), ("r", -1.0)):
            ua = W.get(f"upperarm_{s}", 0.0) + W.get(f"upperarm_twist_{s}", 0.0) + W.get(f"clavicle_{s}", 0.0)
            la = W.get(f"lowerarm_{s}", 0.0) + W.get(f"lowerarm_twist_{s}", 0.0) + W.get(f"hand_{s}", 0.0)
            th = W.get(f"thigh_{s}", 0.0) + W.get(f"thigh_twist_{s}", 0.0)
            ca = W.get(f"calf_{s}", 0.0)
            side = ss(-0.01 * k, 0.01 * k, P[:, 0] * sgn)
            h += self._limb(P, N, side * ss(0.02, 0.3, ua + la), f"upperarm_{s}", sgn, self._upperarm, rmax=0.13)
            h += self._limb(P, N, side * ss(0.02, 0.3, la + ua), f"lowerarm_{s}", sgn, self._forearm)
            h += self._limb(P, N, side * ss(0.02, 0.3, th + 0.5 * ca), f"thigh_{s}", sgn, self._thigh, rmax=0.17)
            h += self._limb(P, N, side * ss(0.02, 0.3, ca + 0.5 * th), f"calf_{s}", sgn, self._calf, rmax=0.12)
        return h

    # -- gövde ---------------------------------------------------------------------
    def _torso(self, P, N):
        k = self.k
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        front = ss(-0.1, -0.45, N[:, 1])
        back = ss(0.1, 0.45, N[:, 1])
        h = np.zeros(len(P))
        nz = self.nip_z

        # pektoral: alt kenarı keskin (üstü kalın kas plakası), köprücük kemiğine doğru incelir
        xs = np.array([0.0, 0.02, 0.05, 0.08, 0.11, 0.14, 0.165, 0.19]) * k
        zL = nz + np.interp(x, xs, np.array([-0.032, -0.035, -0.037, -0.034, -0.025, -0.008, 0.014, 0.042]) * k)
        zU = nz + np.interp(x, xs, np.array([0.196, 0.196, 0.193, 0.190, 0.187, 0.183, 0.178, 0.170]) * k)
        xo = np.interp(z, nz + np.array([0.06, 0.12, 0.17, 0.20]) * k, np.array([0.188, 0.178, 0.160, 0.150]) * k)
        inner = ss(0.0, 0.032 * k, x)
        outer = 1.0 - ss(xo - 0.026 * k, xo + 0.004 * k, x)
        # dolgun göğüs: alt-orta kısım en kalın, köprücük kemiğine doğru yuvarlanarak incelir
        pec = ss(zL - 0.002 * k, zL + 0.02 * k, z) * (1.0 - 0.7 * ss(zL + 0.06 * k, zU, z) ** 1.5)
        pec *= inner * outer * (0.85 + 0.15 * ss(0.02 * k, 0.09 * k, x)) * front
        h += 16.0 * MM * k * pec
        # pektoral altı gölge oluğu ve sternum
        # deltopektoral oluk ve köprücük altı çukuru
        dp = gauss(x - xo, 0.010 * k) * ss(nz + 0.06 * k, nz + 0.09 * k, z) * ss(zU + 0.01 * k, zU - 0.01 * k, z)
        h -= 1.5 * MM * k * dp * front
        h -= 3.0 * MM * k * dome(ellipsoid(P, self.front(0.155 * k, nz + 0.175 * k), np.eye(3),
                                           (0.014 * k, 0.03 * k, 0.012 * k)), 1.0) * front

        # rectus abdominis: dört sıra yastık, linea alba ve linea semilunaris olukları
        top = nz - 0.042 * k
        rows = [top, nz - 0.088 * k, nz - 0.132 * k, self.navel[2] - 0.010 * k, self.hip[2] + 0.028 * k]
        xw = np.interp(z, [rows[-1], top], [0.046 * k, 0.068 * k])
        x0 = 0.0055 * k
        for i, H in enumerate((5.5, 5.5, 5.0, 3.2)):
            z1, z0 = rows[i], rows[i + 1]
            gap = 0.002 * k
            zc, rz = 0.5 * (z1 + z0), 0.5 * (z1 - z0) - gap
            cx, rx = 0.5 * (x0 + xw), 0.5 * (xw - x0)
            d = superd((x - cx) / rx, (z - zc) / rz, 2.8 if i < 3 else 2.2)
            h += H * MM * k * dome(d, 1.6) * front
        alba = gauss(x, 0.006 * k) * ss(rows[-1] + 0.02 * k, self.navel[2], z) * ss(top + 0.015 * k, top - 0.005 * k, z)
        h -= 0.6 * MM * k * alba * front
        semi = gauss(x - (xw + 0.004 * k), 0.011 * k) * ss(rows[-1], rows[-1] + 0.03 * k, z) * ss(top + 0.02 * k, top, z)
        h -= 1.5 * MM * k * semi * front
        # göbek
        h -= 2.5 * MM * k * dome(ellipsoid(P, self.navel, np.eye(3), (0.008 * k, 0.02 * k, 0.011 * k)), 1.0)
        # alt karın: sarkık değil, düz
        h -= 2.0 * MM * k * dome(ellipsoid(P, self.front(0.0, self.hip[2] + 0.05 * k), np.eye(3),
                                           (0.075 * k, 0.05 * k, 0.05 * k)), 1.0) * front

        # dış oblik (bel yanı) ve altında kasık V çizgisi (inguinal) + kalça kemiği sırtı
        fl = self.around(self.hip[2] + 0.11 * k, 72.0)
        ax = np.eye(3)
        h += 4.5 * MM * k * dome(ellipsoid(P, fl, ax, (0.04 * k, 0.05 * k, 0.065 * k)), 1.2)
        crest = [self.around(self.hip[2] + 0.07 * k, 105.0), self.around(self.hip[2] + 0.05 * k, 75.0),
                 self.front(0.105 * k, self.hip[2] + 0.035 * k), self.front(0.07 * k, self.hip[2] - 0.0 * k),
                 self.front(0.035 * k, self.hip[2] - 0.03 * k)]
        d, s = polyline(P, crest)
        h -= 2.5 * MM * k * gauss(d, 0.011 * k) * (0.6 + 0.4 * ss(0.0, 0.4, s)) * ss(1.0, 0.85, s)

        # serratus anterior: kaburga yanında çapraz dişler
        for j in range(4):
            c = self.around(nz - (0.005 + 0.027 * j) * k, 58.0 + 4.0 * j)
            nrm = _unit([1.0, -0.35, 0.0])
            along = _unit(np.cross(nrm, [1.0, 0.0, 0.0]) + np.array([0.0, -0.75, -0.55]))
            along = _unit(along - nrm * (along @ nrm))
            across = np.cross(nrm, along)
            dd = ellipsoid(P, c, np.stack([along, across, nrm]), (0.024 * k, 0.0075 * k, 0.03 * k))
            h += 3.5 * MM * k * dome(dd, 1.2) * ss(0.15, 0.45, N[:, 0])

        # latissimus dorsi: koltuk altından bele geniş kanat
        lat = self.around(nz - 0.03 * k, 118.0)
        h += 5.5 * MM * k * dome(ellipsoid(P, lat, np.eye(3), (0.06 * k, 0.07 * k, 0.12 * k)), 1.2)

        # sırt: omurga oluğu, erector spinae sütunları, trapez, kürek kemiği kasları, kalça
        h -= 1.5 * MM * k * gauss(x, 0.010 * k) * ss(self.hip[2] + 0.02 * k, self.hip[2] + 0.06 * k, z) \
            * ss(self.neck[2] - 0.04 * k, self.neck[2] - 0.12 * k, z) * (1.0 - 0.5 * ss(nz - 0.05 * k, nz + 0.1 * k, z)) * back
        er = self.front(0.028 * k, self.hip[2] + 0.12 * k, back=True)
        h += 7.0 * MM * k * dome(ellipsoid(P, er, np.eye(3), (0.026 * k, 0.04 * k, 0.13 * k)), 1.5) * back
        sc = self.front(0.095 * k, nz + 0.07 * k, back=True)
        h += 5.0 * MM * k * dome(ellipsoid(P, sc, np.eye(3), (0.05 * k, 0.05 * k, 0.055 * k)), 2.0) * back
        tr = self.front(0.035 * k, nz + 0.10 * k, back=True)
        h += 3.0 * MM * k * dome(ellipsoid(P, tr, np.eye(3), (0.06 * k, 0.04 * k, 0.12 * k)), 1.2) * back
        gl = self.front(0.085 * k, self.hip[2] - 0.05 * k, back=True)
        h += 7.0 * MM * k * dome(ellipsoid(P, gl, np.eye(3), (0.075 * k, 0.06 * k, 0.085 * k)), 1.2) * back
        h -= 4.0 * MM * k * dome(ellipsoid(P, self.around(self.hip[2] - 0.03 * k, 112.0), np.eye(3),
                                           (0.02 * k, 0.03 * k, 0.035 * k)), 1.0)

        # boyun: sternokleidomastoid kordonları, sternum çentiği, köprücük kemiği ve üstündeki çukur
        nb = self.neck
        mast = np.array([0.052 * k, nb[1] + 0.035 * k, nb[2] + 0.10 * k])
        stern = self.front(0.016 * k, nb[2] - 0.055 * k)
        mid = 0.5 * (mast + stern) + np.array([0.004 * k, -0.012 * k, 0.0])
        d, s = polyline(P, [mast, mid, stern])
        neck_zone = ss(nb[2] - 0.075 * k, nb[2] - 0.05 * k, z)
        h += 6.0 * MM * k * gauss(d, 0.012 * k) * ss(0.0, 0.15, s) * neck_zone
        h -= 1.75 * MM * k * dome(ellipsoid(P, self.front(0.0, nb[2] - 0.045 * k), np.eye(3),
                                           (0.012 * k, 0.03 * k, 0.012 * k)), 1.0)
        clav = [self.front(0.02 * k, nb[2] - 0.072 * k), self.front(0.08 * k, nb[2] - 0.075 * k),
                self.front(0.14 * k, nb[2] - 0.072 * k), self.front(0.185 * k, nb[2] - 0.08 * k)]
        d, _ = polyline(P, clav)
        h += 2.0 * MM * k * gauss(d, 0.009 * k)
        d, _ = polyline(P, [c + np.array([0.0, 0.006 * k, 0.022 * k]) for c in clav[:3]])
        h -= 2.0 * MM * k * gauss(d, 0.013 * k) * ss(0.2, 0.5, N[:, 2])
        # üst trapez: boyun yanından omuza inen kalın eğim (boyna yakın yüksek), akromiyonda çukur;
        # böylece omuz düz bir raf değil, trapezden deltoide yuvarlanan bir hat olur
        # boyun yanından omuza ~30° inen bir eğim düzlemine kadar doldur (trapez kütlesi): yukarı bakan
        # omuz yüzeyi düzlemle arasındaki boşluk kadar kabarır; omuz başına doğru boşluk sıfıra iner
        zp = nb[2] + 0.048 * k - 0.62 * np.maximum(x - 0.04 * k, 0.0)
        gap = np.clip(zp - z, 0.0, 0.03 * k)
        wy = ss(nb[1] - 0.05 * k, nb[1] - 0.005 * k, y)
        h += gap * np.clip(N[:, 2], 0.0, 1.0) * wy * ss(0.035 * k, 0.06 * k, x) * ss(nb[2] - 0.09 * k, nb[2] - 0.05 * k, z)
        acr = np.array([0.205 * k, self.sh[1] + 0.005 * k, self.sh[2] + 0.045 * k])
        h -= 3.5 * MM * k * dome(ellipsoid(P, acr, np.eye(3), (0.04 * k, 0.05 * k, 0.035 * k)), 1.5)
        return h

    # -- uzuvlar -------------------------------------------------------------------
    def _limb(self, P, N, member, bone, sgn, fn, rmax=0.11):
        idx = np.nonzero(member > 1e-3)[0]
        out = np.zeros(len(P))
        if not len(idx):
            return out
        hd, tl = self.bone(bone)
        ax = tl - hd
        L2 = ax @ ax
        a = ax / np.sqrt(L2)
        fwd, lat = self._frame(bone, a, sgn)
        v = P[idx] - hd
        t = (v @ ax) / L2
        rad = v - np.outer(v @ a, a)
        r = np.linalg.norm(rad, axis=1)
        ang = np.degrees(np.arctan2(rad @ lat, rad @ fwd))
        outward = ss(0.0, 0.35, ((rad / np.maximum(r, 1e-9)[:, None]) * N[idx]).sum(axis=1))
        hh = fn(t, ang, r) * outward * ss(rmax * self.k, 0.8 * rmax * self.k, r) * member[idx]
        out[idx] = hh
        return out

    def _frame(self, bone, a, sgn):
        if bone.startswith("lowerarm"):
            # önkol: 0 = başparmak (radius) tarafı, +90 = avuç (fleksörler), -90 = el sırtı (ekstansörler)
            s = bone[-1]
            hd, tl = self.bone(bone)
            th = np.asarray(self.rig.bones[f"thumb_01_{s}"]["head"], float) - tl
            rdir = _unit(th - a * (th @ a))
            med = np.array([-sgn, 0.0, 0.0])
            vol = med - a * (med @ a) - rdir * (med @ rdir)
            return rdir, _unit(vol)
        fwd0 = np.array([0.0, -1.0, 0.0])
        fwd = _unit(fwd0 - a * (fwd0 @ a))
        lat = np.cross(a, fwd)
        if lat[0] * sgn < 0:
            lat = -lat
        return fwd, _unit(lat)

    @staticmethod
    def _belly(t, ang, tc, th, ac, ah, n=2.6, p=1.3):
        da = (ang - ac + 180.0) % 360.0 - 180.0
        return dome(superd((t - tc) / th, da / ah, n), p)

    def _upperarm(self, t, ang, r):
        k = self.k
        h = np.zeros(len(t))
        # deltoid: ön, yan, arka baş; aşağıda kola V şeklinde tutunur
        for ac, ah0, H in ((24.0, 46.0, 14.0), (90.0, 44.0, 18.0), (156.0, 46.0, 12.0)):
            ah = ah0 * (1.0 - 0.45 * ss(0.12, 0.50, t))
            ac_t = ac + (90.0 - ac) * ss(0.15, 0.48, t)
            da = (ang - ac_t + 180.0) % 360.0 - 180.0
            rise = ss(-0.10, 0.12, t)
            fall = 1.0 - ss(0.24, 0.50, t)
            h += H * MM * k * rise * fall * dome(np.abs(da) / ah, 1.2)
        # biseps, brakialis, triseps (dış ve uzun baş) ve tendon plakası
        h += 14.0 * MM * k * self._belly(t, ang, 0.62, 0.32, -6.0, 60.0)
        h += 3.0 * MM * k * self._belly(t, ang, 0.74, 0.15, 72.0, 22.0)
        h += 8.0 * MM * k * self._belly(t, ang, 0.44, 0.24, 135.0, 34.0)
        h += 12.0 * MM * k * self._belly(t, ang, 0.44, 0.30, -165.0, 46.0)
        h -= 1.5 * MM * k * self._belly(t, ang, 0.84, 0.12, 180.0, 30.0, p=1.0)
        # dış ve iç oluk (biseps-triseps), deltoid alt sınırı
        h -= 1.2 * MM * k * gauss(((ang - 92.0 + 180.0) % 360.0 - 180.0), 14.0) * ss(0.58, 0.68, t) * ss(0.95, 0.85, t)
        h -= 1.5 * MM * k * gauss(((ang + 95.0 + 180.0) % 360.0 - 180.0), 14.0) * ss(0.25, 0.35, t) * ss(0.95, 0.85, t)
        return h

    def _forearm(self, t, ang, r):
        k = self.k
        h = np.zeros(len(t))
        h += 10.0 * MM * k * self._belly(t, ang, 0.18, 0.28, 5.0, 42.0)     # brakioradyalis
        h += 7.0 * MM * k * self._belly(t, ang, 0.24, 0.30, -45.0, 32.0)    # ekstansör karpi radyalis
        h += 4.5 * MM * k * self._belly(t, ang, 0.30, 0.30, -95.0, 35.0)    # ekstansör digitorum
        h += 9.0 * MM * k * self._belly(t, ang, 0.22, 0.32, 95.0, 58.0)     # fleksörler
        h -= 1.2 * MM * k * gauss(((ang + 150.0 + 180.0) % 360.0 - 180.0), 14.0) * ss(0.1, 0.2, t) * ss(0.95, 0.8, t)
        h -= 0.8 * MM * k * gauss(((ang - 45.0 + 180.0) % 360.0 - 180.0), 12.0) * ss(0.1, 0.2, t) * ss(0.6, 0.45, t)
        return h

    def _thigh(self, t, ang, r):
        k = self.k
        h = np.zeros(len(t))
        h += 9.0 * MM * k * self._belly(t, ang, 0.52, 0.34, 78.0, 40.0)     # vastus lateralis
        h += 7.5 * MM * k * self._belly(t, ang, 0.46, 0.36, 8.0, 28.0)      # rectus femoris
        h += 10.0 * MM * k * self._belly(t, ang, 0.80, 0.15, -48.0, 36.0)   # vastus medialis (damla)
        h -= 1.2 * MM * k * gauss(((ang - 42.0 + 180.0) % 360.0 - 180.0), 12.0) * ss(0.3, 0.45, t) * ss(0.9, 0.8, t)
        h -= 1.0 * MM * k * gauss(((ang + 22.0 + 180.0) % 360.0 - 180.0), 12.0) * ss(0.5, 0.62, t) * ss(0.95, 0.85, t)
        h += 4.0 * MM * k * self._belly(t, ang, 0.30, 0.25, -100.0, 40.0)   # adduktorlar
        h += 5.0 * MM * k * self._belly(t, ang, 0.50, 0.32, 160.0, 30.0)    # biseps femoris
        h += 5.0 * MM * k * self._belly(t, ang, 0.50, 0.32, -155.0, 32.0)   # semitendinozus
        h -= 1.2 * MM * k * gauss(((ang - 115.0 + 180.0) % 360.0 - 180.0), 14.0) * ss(0.25, 0.4, t) * ss(0.95, 0.85, t)
        # sartorius oluğu: uyluk önünde dıştan içe çapraz
        sart = -70.0 + 120.0 * (1.0 - t)
        h -= 1.0 * MM * k * gauss(((ang - sart + 180.0) % 360.0 - 180.0), 12.0) * ss(0.15, 0.3, t) * ss(0.85, 0.72, t)
        # diz kapağı ve çevresindeki çukurlar
        h += 3.0 * MM * k * self._belly(t, ang, 0.99, 0.05, 0.0, 30.0)
        h -= 2.0 * MM * k * self._belly(t, ang, 0.98, 0.06, 45.0, 14.0, p=1.0)
        h -= 2.0 * MM * k * self._belly(t, ang, 0.98, 0.06, -45.0, 14.0, p=1.0)
        return h

    def _calf(self, t, ang, r):
        k = self.k
        h = np.zeros(len(t))
        h += 9.0 * MM * k * self._belly(t, ang, 0.26, 0.20, -148.0, 38.0)   # gastroknemius iç baş
        h += 7.0 * MM * k * self._belly(t, ang, 0.22, 0.17, 150.0, 34.0)    # gastroknemius dış baş
        h -= 1.5 * MM * k * gauss(((ang - 180.0 + 180.0) % 360.0 - 180.0), 12.0) * ss(0.04, 0.1, t) * ss(0.4, 0.3, t)
        h += 4.0 * MM * k * self._belly(t, ang, 0.52, 0.18, 112.0, 26.0)    # soleus dış
        h += 4.0 * MM * k * self._belly(t, ang, 0.52, 0.18, -112.0, 26.0)   # soleus iç
        h += 4.0 * MM * k * self._belly(t, ang, 0.32, 0.28, 38.0, 22.0)     # tibialis anterior
        h += 1.5 * MM * k * self._belly(t, ang, 0.80, 0.16, 180.0, 12.0)    # aşil tendonu
        h -= 2.0 * MM * k * self._belly(t, ang, 0.82, 0.14, 150.0, 18.0, p=1.0)
        h -= 2.0 * MM * k * self._belly(t, ang, 0.82, 0.14, -150.0, 18.0, p=1.0)
        return h


# --------------------------------------------------------------------------------
# UV'ye pişirme
# --------------------------------------------------------------------------------
def _normals(verts, faces):
    n = np.zeros_like(verts)
    for f in faces:
        p = verts[f]
        fn = np.cross(p[1] - p[0], p[2] - p[0])
        if len(f) == 4:
            fn = fn + np.cross(p[2] - p[0], p[3] - p[0])
        n[f] += fn
    return n / np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]


def _rasterize(base, fids, size):
    """UV üçgenlerini doku hücrelerine böl: (piksel indeksi, 3 köşe, 3 barisentrik)."""
    pix, tri, bar = [], [], []
    uvs = base.uvs * size - 0.5
    for f in fids:
        vi, ti = base.faces[f], base.face_uvs[f]
        for a, b, c in ((0, 1, 2), (0, 2, 3))[: len(vi) - 2]:
            A, B, C = uvs[ti[a]], uvs[ti[b]], uvs[ti[c]]
            lo = np.floor(np.minimum(np.minimum(A, B), C)).astype(int)
            hi = np.ceil(np.maximum(np.maximum(A, B), C)).astype(int)
            lo = np.clip(lo, 0, size - 1)
            hi = np.clip(hi, 0, size - 1)
            xs, ys = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
            px, py = xs.ravel().astype(float), ys.ravel().astype(float)
            den = (B[1] - C[1]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[1] - C[1])
            if abs(den) < 1e-12:
                continue
            l0 = ((B[1] - C[1]) * (px - C[0]) + (C[0] - B[0]) * (py - C[1])) / den
            l1 = ((C[1] - A[1]) * (px - C[0]) + (A[0] - C[0]) * (py - C[1])) / den
            l2 = 1.0 - l0 - l1
            m = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
            if not m.any():
                continue
            pix.append((ys.ravel()[m] * size + xs.ravel()[m]).astype(np.int64))
            tri.append(np.tile([vi[a], vi[b], vi[c]], (int(m.sum()), 1)))
            bar.append(np.stack([l0[m], l1[m], l2[m]], axis=1))
    return np.concatenate(pix), np.concatenate(tri), np.concatenate(bar)


def _dilate(img, valid, steps=24):
    img = img.copy()
    valid = valid.copy()
    for _ in range(steps):
        acc = np.zeros_like(img)
        cnt = np.zeros_like(img)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(np.roll(img * valid, dy, 0), dx, 1)
            sv = np.roll(np.roll(valid.astype(float), dy, 0), dx, 1)
            acc += sh
            cnt += sv
        grow = (~valid) & (cnt > 0)
        img[grow] = acc[grow] / cnt[grow]
        valid = valid | grow
    return img


def _neighbors(n, faces):
    nb = [set() for _ in range(n)]
    for f in faces:
        for x, y in zip(f, f[1:] + f[:1]):
            nb[x].add(y)
            nb[y].add(x)
    return [np.array(sorted(q), dtype=np.int64) for q in nb]


def sculpt(base, verts, rig, k, size=SIZE, cache_key="", smooth=8):
    """Yontuyu ikiye böl: büyük kas kütleleri (yumuşatılmış alan) temel ağın köşelerine işlenir – giysiler,
    çarpışma vekili ve deri aynı hacmi paylaşır; kalan ince ayrıntı (oluklar, kas sınırları) UV
    görüntüsünde kalır ve Displace ile uygulanır. Döner: (yontulmuş köşeler, (size, size) ayrıntı haritası)."""
    src = open(os.path.abspath(__file__), "rb").read()
    key = hashlib.sha1(src + cache_key.encode() + np.round(verts, 5).tobytes()
                       + f"{size}/{smooth}".encode()).hexdigest()[:16]
    path = os.path.join(CACHE, f"{key}.npz")
    if os.path.exists(path):
        d = np.load(path)
        return d["verts"], d["detail"]
    fids = base.faces_in("body")
    faces = [base.faces[f] for f in fids]
    body = np.unique(np.concatenate([np.asarray(f) for f in faces]))
    vn = _normals(verts, faces)
    Wv = {}
    for b, pairs in rig.skin_weights.items():
        w = np.zeros(len(verts))
        for vi, ww in pairs:
            w[int(vi)] = ww
        Wv[b] = w
    an = Anatomy(base, verts, rig, k)
    # köşelerde alan ve düşük frekanslı kısmı (kas kütleleri)
    hv = np.zeros(len(verts))
    hv[body] = an.height(verts[body], vn[body], {b: w[body] for b, w in Wv.items()})
    nb = _neighbors(len(verts), faces)
    low = hv.copy()
    for _ in range(smooth):
        avg = np.array([low[n].mean() if len(n) else low[i] for i, n in enumerate(nb)])
        low = 0.5 * low + 0.5 * avg
    # doku hücrelerinde tam alan eksi aradeğerlenmiş düşük kısım = ayrıntı
    pix, tri, bar = _rasterize(base, fids, size)
    P = (verts[tri] * bar[:, :, None]).sum(axis=1)
    N = (vn[tri] * bar[:, :, None]).sum(axis=1)
    N /= np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]
    W = {b: (w[tri] * bar).sum(axis=1) for b, w in Wv.items()}
    detail = an.height(P, N, W) - (low[tri] * bar).sum(axis=1)
    img = np.zeros(size * size)
    valid = np.zeros(size * size, dtype=bool)
    img[pix] = detail
    valid[pix] = True
    img = _dilate(img.reshape(size, size), valid.reshape(size, size)).astype(np.float32)
    out = verts.copy()
    out[body] += vn[body] * low[body][:, None]
    os.makedirs(CACHE, exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp.npz"
    np.savez(tmp, verts=out, detail=img)
    os.replace(tmp, path)  # paralel render süreçleri yarım dosya okumasın
    return out, img
