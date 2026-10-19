"""lottie_gen iskelet çözümünü (cm, X ileri / Y yukarı / Z sağ) MakeHuman iskeletine aktarır.

- Gövde: kalça, göğüs ve baş çerçevelerinin dönüşü; göğüs dönüşü üç omur kemiğine paylaştırılır.
- Kol ve bacaklar: MakeHuman omuz/kalça ekleminden bizim el/bilek hedeflerine iki kemikli IK;
  dirsek/diz menteşe ekseni hem duruşta hem pozda aynı tutularak kemik burulması doğru kalır.
- Ayaklar: bizim ayak çerçevesi; parmaklar yere basarken düz kalır.
- Parmaklar: karakter ayarına göre yumruk.

lottie_gen/skeleton.py ölçüleri configure_skeleton() ile MakeHuman gövdesine eşitlenir; böylece
IK hedefleri (yere basan ayaklar, torbaya/partnere değen yumruklar) bu gövdede birebir tutar.
"""
import math

import numpy as np
from mathutils import Matrix, Quaternion, Vector

AXIS_MAP = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]])  # (X, Y, Z)_biz -> Blender


def B(p):
    """Bizim nokta (cm) -> Blender (m)."""
    return AXIS_MAP @ np.asarray(p, dtype=float) / 100.0


def Bv(v):
    return AXIS_MAP @ np.asarray(v, dtype=float)


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


# MakeHuman duruşunda gövde çerçevesi: ileri -Y, yukarı +Z, sağ -X (sütunlar)
REST_FRAME = np.array([[0.0, 0.0, -1.0], [-1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


def frame_rot(frame):
    """Bizim (f, u, r) çerçevesinin MakeHuman duruşuna göre dönüşü (3x3, Blender)."""
    f, u, r = (Bv(x) for x in frame)
    R1 = np.stack([f, u, r], axis=1)
    return R1 @ REST_FRAME.T


def basis_from(y, n):
    """y ekseni ve ona dik yaklaşık n ile ortonormal taban (sütunlar: y, n, y x n)."""
    y = unit(y)
    n = unit(n - y * np.dot(n, y))
    return np.stack([y, n, np.cross(y, n)], axis=1)


def quat_from(R):
    return Matrix(R.tolist()).to_quaternion()


def slerp_rot(Ra, Rb, t):
    qa, qb = quat_from(Ra), quat_from(Rb)
    return np.array(qa.slerp(qb, t).to_matrix())


def axis_angle(axis, ang):
    return np.array(Matrix.Rotation(ang, 3, Vector(unit(axis).tolist())))


def ik2(root, target, l1, l2, pole):
    d = target - root
    dist = np.linalg.norm(d)
    dirv = unit(d)
    dist_c = min(max(dist, abs(l1 - l2) + 0.005), l1 + l2 - 0.0005)
    a = (l1 * l1 + dist_c * dist_c - l2 * l2) / (2 * l1 * dist_c)
    a = max(-1.0, min(1.0, a))
    pv = pole - dirv * np.dot(pole, dirv)
    if np.linalg.norm(pv) < 1e-6:
        pv = np.array([0.0, 0.0, 1.0]) - dirv * dirv[2]
    pv = unit(pv)
    mid = root + dirv * (l1 * a) + pv * (l1 * math.sqrt(max(0.0, 1 - a * a)))
    end = root + dirv * dist_c
    return mid, end, pv


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# --------------------------------------------------------------------------------
# lottie_gen iskelet ölçülerini MakeHuman gövdesine eşitle
# --------------------------------------------------------------------------------
def body_dims(ch):
    """Character (rest, metre) -> skeleton.py sabitleri (cm)."""
    bones = ch.rig.bones
    P = lambda n, e="head": np.asarray(bones[n][e]) * 100.0  # noqa: E731
    hip = P("thigh_l")
    hip_r = P("thigh_r")
    hip_mid = (hip + hip_r) / 2
    HIP_DOWN = 3.0
    CHEST_UP = 17.0
    pelvis_c = hip_mid + np.array([0.0, 0.0, HIP_DOWN])
    c0 = pelvis_c + np.array([0.0, 0.0, CHEST_UP])
    sh = P("upperarm_l")
    neck = P("neck_01")
    head0 = P("head")
    head_top = P("head", "tail")
    wrist = P("hand_l")
    knuckle = P("middle_01_l")
    ankle = P("foot_l")
    ball = P("ball_l")
    d = dict(
        HIP_HALF=abs(hip[0]),
        HIP_DOWN=HIP_DOWN,
        CHEST_UP=CHEST_UP,
        SHOULDER_UP=sh[2] - c0[2],
        SHOULDER_HALF=abs(sh[0]),
        SHOULDER_BACK=sh[1] - c0[1],
        NECK_UP=neck[2] - c0[2],
        NECK_LEN=np.linalg.norm(head0 - neck),
        HEAD_UP=0.42 * np.linalg.norm(head_top - head0),
        HEAD_FWD=1.5,
        HEAD_R=0.5 * np.linalg.norm(head_top - head0) * 1.1,
        UPPER_ARM=np.linalg.norm(P("upperarm_l", "tail") - sh),
        FOREARM=np.linalg.norm(wrist - P("lowerarm_l")),
        HAND=0.8 * np.linalg.norm(knuckle - wrist) + 1.0,
        THIGH=np.linalg.norm(P("thigh_l", "tail") - hip),
        SHIN=np.linalg.norm(ankle - P("calf_l")),
        ANKLE_H=ankle[2],
        FOOT_BALL=-(ball[1] - ankle[1]),
        FOOT_BALL_DOWN=ankle[2] - ball[2],
        BALL_R=ball[2],
    )
    d["STAND_Y"] = pelvis_c[2] - 0.8
    return {k: float(v) for k, v in d.items()}


def configure_skeleton(dims):
    """skeleton.py ölçülerini değiştir. moves.py bu çağrıdan SONRA içe aktarılmalı (pozlar içe
    aktarılırken çözülür)."""
    import skeleton
    for k, v in dims.items():
        setattr(skeleton, k, v)
    skeleton.BASE_POSE["y"] = dims["STAND_Y"]
    # BASE_POSE ayakları modül yüklenirken eski ölçülerle hesaplanmıştı
    skeleton.BASE_POSE["lf"] = skeleton.planted(2.0, -11.0, -6.0)
    skeleton.BASE_POSE["rf"] = skeleton.planted(2.0, 11.0, 6.0)


# --------------------------------------------------------------------------------
# Poz aktarımı
# --------------------------------------------------------------------------------
FINGERS = ("index", "middle", "ring", "pinky")


class Poser:
    def __init__(self, ch, fist=(70.0, 95.0, 65.0), thumb=(15.0, 35.0, 40.0), pronate=80.0):
        self.ch = ch
        self.arm = ch.arm_ob.data
        self.rest = {b.name: np.array(b.matrix_local) for b in self.arm.bones}
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in self.arm.bones}
        self.order = [n for n in ch.rig.order]
        self.fist = fist
        self.thumb = thumb
        self.pronate = math.radians(pronate)
        R = self.rest
        h = lambda n: R[n][:3, 3]  # noqa: E731
        tail = lambda n: np.asarray(ch.rig.bones[n]["tail"])  # noqa: E731
        self.len = {n: float(np.linalg.norm(tail(n) - h(n))) for n in R}
        # dinlenmedeki menteşe eksenleri (dirsek, diz)
        self.hinge0 = {}
        for s in ("l", "r"):
            for up, lo in (("upperarm", "lowerarm"), ("thigh", "calf")):
                a = tail(f"{up}_{s}") - h(f"{up}_{s}")
                b = tail(f"{lo}_{s}") - h(f"{lo}_{s}")
                self.hinge0[f"{up}_{s}"] = unit(np.cross(a, b))
        # parmak bükülme eksenleri (bone yerel)
        self.curl = {}
        self.palm0, self.hand_y0 = {}, {}
        self.flat = {"l": False, "r": False}
        for s in ("l", "r"):
            lateral = unit(h(f"index_01_{s}") - h(f"pinky_01_{s}"))
            for fng in FINGERS + ("thumb",):
                d1 = tail(f"{fng}_01_{s}") - h(f"{fng}_01_{s}")
                d2 = tail(f"{fng}_02_{s}") - h(f"{fng}_02_{s}")
                ax = np.cross(d1, d2)
                if fng != "thumb":
                    # yanal eksen; işareti duruştaki hafif kıvrılmadan
                    sgn = 1.0 if np.dot(ax, lateral) >= 0 else -1.0
                    ax = lateral * sgn if np.linalg.norm(ax) < 1e-4 else unit(ax)
                else:
                    ax = unit(ax) if np.linalg.norm(ax) > 1e-6 else lateral
                for j in ("01", "02", "03"):
                    bn = f"{fng}_{j}_{s}"
                    self.curl[bn] = R[bn][:3, :3].T @ ax
                if fng == "middle":
                    # parmak ucu bükülünce ax x d yönüne gider: avuç içi normali
                    dh = unit(tail(f"hand_{s}") - h(f"hand_{s}"))
                    self.palm0[s] = unit(np.cross(ax, dh))
                    self.hand_y0[s] = dh

    def _rest_rot(self, n):
        return self.rest[n][:3, :3]

    def pose(self, sk, recoil=None):
        """sk: lottie_gen Skeleton (tek kare). Kemiklerin poz matrislerini uygular."""
        R = self.rest
        world = {}

        def head_from_parent(n):
            p = self.parent[n]
            if p is None:
                return R[n][:3, 3]
            rel = np.linalg.inv(R[p]) @ R[n]
            return (world[p] @ rel)[:3, 3]

        def setw(n, rot, head=None):
            M = np.eye(4)
            M[:3, :3] = rot
            M[:3, 3] = head_from_parent(n) if head is None else head
            world[n] = M

        Qp = frame_rot(sk.pelvis)
        Qc = frame_rot(sk.chest)
        Qh = frame_rot(sk.head)
        # kalça: MakeHuman kalça eklemleri ortası = bizim kalça eklemleri ortası
        hip_mid_rest = (R["thigh_l"][:3, 3] + R["thigh_r"][:3, 3]) / 2
        hip_mid = (B(sk.j["lhip"]) + B(sk.j["rhip"])) / 2
        world["Root"] = R["Root"].copy()
        pel_head = hip_mid + Qp @ (R["pelvis"][:3, 3] - hip_mid_rest)
        setw("pelvis", Qp @ self._rest_rot("pelvis"), pel_head)
        for n, t in (("spine_01", 0.25), ("spine_02", 0.55), ("spine_03", 1.0)):
            setw(n, slerp_rot(Qp, Qc, t) @ self._rest_rot(n))
        for s in ("l", "r"):
            setw(f"clavicle_{s}", Qc @ self._rest_rot(f"clavicle_{s}"))
        setw("neck_01", slerp_rot(Qc, Qh, 0.45) @ self._rest_rot("neck_01"))
        setw("head", Qh @ self._rest_rot("head"))

        for s, side in (("l", 1.0), ("r", -1.0)):
            self._limb(sk, world, s, "upperarm", "lowerarm", head_from_parent, setw, Qc,
                       target=B(sk.j[s + "hand"]), pole_pt=B(sk.j[s + "elbow"]),
                       l2_extra=self._hand_len(), side=side)
            self._limb(sk, world, s, "thigh", "calf", head_from_parent, setw, Qp,
                       target=B(sk.j[s + "ankle"]), pole_pt=B(sk.j[s + "knee"]), l2_extra=0.0, side=side)
            # ayak
            fd, fu, fr, toe = sk.j[s + "foot"]
            Qf = frame_rot((fd, fu, fr))
            setw(f"foot_{s}", Qf @ self._rest_rot(f"foot_{s}"))
            td = unit(Bv(toe))
            up = Bv(fu)
            Qt = basis_from(td, up) @ basis_from(np.array([0.0, -1.0, 0.0]), np.array([0.0, 0.0, 1.0])).T
            setw(f"ball_{s}", Qt @ self._rest_rot(f"ball_{s}"))
            # parmaklar: önce el ile aynı göreli duruş
            for fng in FINGERS + ("thumb",):
                for j in ("01", "02", "03"):
                    bn = f"{fng}_{j}_{s}"
                    p = self.parent[bn]
                    rel = np.linalg.inv(R[p]) @ R[bn]
                    world[bn] = world[p] @ rel
        self._apply(world)

    def _hand_len(self):
        return self.ch.dims["HAND"] / 100.0

    def _limb(self, sk, world, s, up, lo, head_from_parent, setw, Qparent, target, pole_pt, l2_extra, side):
        R = self.rest
        nu, nl = f"{up}_{s}", f"{lo}_{s}"
        root = head_from_parent(nu)
        l1 = self.len[nu]
        l2 = self.len[nl] + l2_extra
        flat = None
        if up == "upperarm":
            self.flat[s] = bool(target[2] < 0.10)
            if self.flat[s]:
                # yere dayanan el: avuç yere düz, bilek avuç merkezinin gerisinde ve üstünde
                fwd = Bv(sk.chest[0]).copy()
                fwd[2] = 0.0
                fwd = unit(fwd) if np.linalg.norm(fwd) > 1e-3 else np.array([1.0, 0.0, 0.0])
                flat = fwd
                target = np.array([target[0], target[1], 0.0]) - fwd * 0.045 + np.array([0.0, 0.0, 0.035])
                l2 = self.len[nl]
        pole = pole_pt - (root + target) / 2
        mid, end, pv = ik2(root, target, l1, l2, pole)
        dirv = unit(end - root)
        n = unit(np.cross(pv, dirv))
        a = mid - root
        b = end - mid
        n0 = self.hinge0[nu]
        y0u = R[nu][:3, :3] @ np.array([0.0, 1.0, 0.0])
        y0l = R[nl][:3, :3] @ np.array([0.0, 1.0, 0.0])
        Ru = basis_from(a, n) @ basis_from(y0u, n0).T
        Rl = basis_from(b, n) @ basis_from(y0l, n0).T
        if up == "upperarm":
            # uzanan yumrukta önkol/bilek içe döner (pronasyon)
            ext = np.linalg.norm(target - root) / (self.len[nu] + self.len[nl] + l2_extra)
            ang = 0.0 if flat is not None else side * self.pronate * smoothstep(0.82, 0.99, ext)
            # pozda istenen ek önkol dönüşü (supinasyon: avuç yukarı; pronasyonun tersi)
            ang -= side * math.radians(sk.p.get(s + "sup", 0.0))
            Rl = axis_angle(b, 0.45 * ang) @ Rl
        setw(nu, Ru @ R[nu][:3, :3], root)
        setw(nl, Rl @ R[nl][:3, :3])
        if up == "upperarm":
            # el: önkol ile aynı göreli duruş + kalan pronasyon
            rel = np.linalg.inv(R[nl]) @ R[f"hand_{s}"]
            M = world[nl] @ rel
            M[:3, :3] = axis_angle(b, 0.55 * ang) @ M[:3, :3]
            if flat is not None:
                Rh = basis_from(flat, np.array([0.0, 0.0, -1.0])) @ basis_from(self.hand_y0[s], self.palm0[s]).T
                M[:3, :3] = Rh @ R[f"hand_{s}"][:3, :3]
            world[f"hand_{s}"] = M

    def _apply(self, world):
        ob = self.ch.arm_ob
        R = self.rest
        for n in self.order:
            pb = ob.pose.bones[n]
            p = self.parent[n]
            if p is None:
                basis = np.linalg.inv(R[n]) @ world[n]
            else:
                basis = np.linalg.inv(R[n]) @ R[p] @ np.linalg.inv(world[p]) @ world[n]
            M = Matrix(basis.tolist())
            loc, rot, _sc = M.decompose()
            if n.split("_")[0] in FINGERS + ("thumb",):
                ang = self._finger_angle(n)
                rot = rot @ Quaternion(Vector(self.curl[n].tolist()), math.radians(ang))
            pb.location = loc
            pb.rotation_quaternion = rot
            pb.scale = (1.0, 1.0, 1.0)

    def _finger_angle(self, n):
        fng, j, s = n.split("_")
        k = int(j) - 1
        if self.flat.get(s):
            return (10.0, 6.0, 4.0)[k] if fng == "thumb" else (4.0, 6.0, 4.0)[k]
        return self.thumb[k] if fng == "thumb" else self.fist[k]
