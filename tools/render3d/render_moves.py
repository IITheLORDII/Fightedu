#!/usr/bin/env python3
"""FightEdu gerçekçi hareket videoları: MakeHuman gövdesi + Blender Cycles.

Hareketlerin kendisi (anahtar pozlar, hedefler, partner, darbe kareleri) tools/lottie_gen/moves.py'den
gelir; bu betik aynı iskelet çözümünü gerçekçi 3B sporcuya aktarır, stüdyo ışığında render eder ve
her hareket için döngüsel bir MP4 ile küçük bir kapak resmi (WebP) üretir.

Kullanım (bpy kurulu Python 3.13 ile):
  python render_moves.py --out ../../app/src/main/assets/video [--only box_jab ...] [--preview 0,12]
"""
import argparse
import math
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "lottie_gen"))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Quaternion, Vector  # noqa: E402

import outfits  # noqa: E402
import retarget  # noqa: E402
import studio  # noqa: E402
from character import ATHLETE, Character  # noqa: E402
from shading import srgb  # noqa: E402

WIDTH, HEIGHT = 640, 512
ROPE_POINTS = 13
LEG_HITS = ("shin", "ball", "knee", "heel", "toe", "ankle")
KICK_IMPULSE = 0.05  # tekme darbesinde torbanın açısal hızı (radyan/kare): ~6° savrulma

FIGHTER_SHAPE = ATHLETE
PARTNER_SHAPE = dict(ATHLETE, muscle=0.92, weight=0.40, height=0.52,
                     race=dict(african=0.55, asian=0.05, caucasian=0.40))

STYLE = {
    "boxing": dict(floor="#CFCBC4", wall="#ECEDEF",
                   fighter=dict(shorts_color="#1F4FC8", trim="#F4F4F4", gloves="#C8102E", boots="#111111"),
                   partner=dict(shorts_color="#A3161B", trim="#151515", gloves="#151515", boots="#F0F0F0",
                                socks="#151515")),
    "kickboxing": dict(floor="#C6CBD2", wall="#ECEDEF",
                       fighter=dict(shorts_color="#151515", trim="#D9A21B", gloves="#1F4FC8"),
                       partner=dict(shorts_color="#A3161B", trim="#F2F2F2", gloves="#A3161B")),
    "wrestling": dict(floor="#D9BE55", wall="#ECEDEF",
                      fighter=dict(singlet="#1F3FA8", trim="#F2F2F2", shoes="#151515"),
                      partner=dict(singlet="#B3191F", trim="#F2F2F2", shoes="#B3191F")),
    "taekwondo": dict(floor="#9FB6D8", wall="#ECEDEF",
                      fighter=dict(belt="#111111"),
                      partner=dict(belt="#111111", hogu="#C62828")),
    "general": dict(floor="#CFCBC4", wall="#ECEDEF", fighter=dict(), partner=dict()),
}
HANDS = {  # parmak bükülmesi (derece): (01, 02, 03), başparmak
    "boxing": ((70, 95, 65), (15, 35, 40)),
    "kickboxing": ((70, 95, 65), (15, 35, 40)),
    "taekwondo": ((78, 100, 70), (25, 45, 55)),
    "wrestling": ((25, 35, 25), (10, 15, 15)),
    "general": ((12, 18, 12), (5, 8, 8)),
}


def our_dir(v):
    return retarget.Bv(v)


class MoveRenderer:
    def __init__(self, move_id, mv, samples=10):
        self.id = move_id
        self.mv = mv
        self.samples = samples

    # -- sahne --------------------------------------------------------------------
    def build(self):
        import scene as lscene
        mv = self.mv
        style = STYLE[mv.sport]
        studio.reset_scene()
        studio.setup_render(WIDTH, HEIGHT, samples=self.samples)
        studio.world(strength=0.16)
        fist, thumb = HANDS[mv.sport]
        self.fig = Character("fig", shape=FIGHTER_SHAPE)
        bm = outfits.BodyMap(self.fig)
        outfits.KITS[mv.sport](self.fig, bm, **style["fighter"])
        self.fig.dims = retarget.body_dims(self.fig)
        retarget.configure_skeleton(self.fig.dims)
        self.fposer = retarget.Poser(self.fig, fist=fist, thumb=thumb)

        sb = lscene.SceneBuilder(self.id, mv)
        sb.solve()
        self.sb = sb
        self.opp = None
        if sb.psk:
            self.opp = Character("opp", shape=PARTNER_SHAPE, skin="#7B4B33", hair="#0E0A08", iris="#24160E")
            obm = outfits.BodyMap(self.opp)
            outfits.KITS[mv.sport](self.opp, obm, **style["partner"])
            self.opp.dims = retarget.body_dims(self.opp)
            self.oposer = retarget.Poser(self.opp, fist=fist, thumb=thumb)
        self.bag_report = None
        if sb.bag:
            self._bag_contacts()
        self.bag = self._bag() if sb.bag else None
        self.rope = self._rope() if mv.rope is not None else None
        self._camera_and_lights(style)

    def _bag_dims(self):
        """(askı noktası, zincir, boy, yarıçap) – Blender metresi."""
        b = self.sb.bag
        chain = (26.0 if b["long"] else 36.0) / 100.0
        length = (188.0 if b["long"] else 118.0) / 100.0
        return retarget.B((b["x"], 236.0, b["z"])), chain, length, b["r"] / 100.0

    def _swing(self, t):
        """Darbelerin zamana bağlı sallanması: yatay eğim vektörü (radyan, alt uç bu yöne gider)."""
        ang, push = self.sb.bag_swing(t)
        return math.radians(ang) * retarget.Bv(push)[:2]

    def _bag_depth(self, P, tilt):
        """Noktaların eğik torba silindirine girme derinliği (m, > 0 içeride)."""
        pivot, chain, length, r = self._bag_dims()
        ang = float(np.linalg.norm(tilt))
        L = P - pivot
        if ang > 1e-9:
            d = np.array([tilt[0], tilt[1], 0.0]) / ang
            R = np.array(Quaternion(Vector(np.cross(d, (0.0, 0.0, 1.0)).tolist()), ang).to_matrix())
            L = L @ R  # torba yerel ekseni (satır vektörü: R^T p)
        inside = (L[:, 2] < -chain) & (L[:, 2] > -chain - length)
        return np.where(inside, r - np.hypot(L[:, 0], L[:, 1]), -1.0)

    def _bag_contacts(self, margin=0.002, max_tilt=0.6):
        """Vuruşun devamında uzuv torbanın içinden geçmesin: her karede dövüşçü ağlarını torbaya karşı sına,
        giren köşeler kalmayacak kadar torbayı itme yönünde ek eğ. Temas bitince torba sönümlü bir yayla
        geri gelir (iki tur hesaplanır, döngü dikişsiz). Yalnızca tekmeli hareketlerde itme çok büyükse torba
        o kadar geriye yerleştirilir (ağır torba fazla savrulmasın)."""
        sb, dur = self.sb, self.mv.dur
        obs = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("fig_")
               and not any(m.type == "CLOTH" for m in o.modifiers)]
        frames = []
        for t in range(dur):
            self.fposer.pose(sb.fsk[t])
            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()
            pts = []
            for ob in obs:
                ev = ob.evaluated_get(dg)
                me = ev.to_mesh()
                co = np.empty(len(me.vertices) * 3)
                me.vertices.foreach_get("co", co)
                mw = np.array(ev.matrix_world)
                ev.to_mesh_clear()
                pts.append(co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3])
            frames.append(np.concatenate(pts))
        pushes = []
        for p in sb.bag["pushes"]:
            v = retarget.Bv(p)[:2]
            pushes.append(v / max(np.linalg.norm(v), 1e-9))
        hits = [f for f, _n, _p in sb.hit_pts]
        legs_only = all(n.endswith(LEG_HITS) for _f, n, _p in sb.hit_pts)
        shifted = 0.0
        for _attempt in range(3):
            pivot, chain, length, r = self._bag_dims()
            need, dirs, worst = [], [], (0.0, 0.0, 0)
            for t, P in enumerate(frames):
                P = P[np.hypot(P[:, 0] - pivot[0], P[:, 1] - pivot[1]) < r + 0.4]
                k = min(range(len(hits)), key=lambda i: min(abs(t - hits[i]), dur - abs(t - hits[i])))
                n = pushes[k]
                base = self._swing(t)
                d = self._bag_depth(P, base) if len(P) else np.full(1, -1.0)
                e = 0.0
                if d.max() > -margin:
                    if self._bag_depth(P, base + max_tilt * n).max() > -margin:
                        e = max_tilt
                    else:
                        lo, hi = 0.0, max_tilt
                        for _ in range(18):
                            mid = (lo + hi) / 2
                            if self._bag_depth(P, base + mid * n).max() > -margin:
                                lo = mid
                            else:
                                hi = mid
                        e = hi
                    lever = pivot[2] - float(np.mean(P[d > -margin][:, 2]))
                    if e * lever > worst[0]:
                        worst = (e * lever, e, t)
                need.append(e)
                dirs.append(n)
            k_w = worst[2]
            if legs_only and worst[0] > 0.10:
                # torbayı itme yönünde geri al: kalan temas ~6 cm itmeyle çözülsün
                s = worst[0] - 0.06
                n = dirs[k_w]
                sb.bag["x"] += s * n[0] * 100.0
                sb.bag["z"] -= s * n[1] * 100.0  # Blender y = -biz z
                shifted += s
                continue
            break
        # temas varken bacakla birlikte it, bırakınca kritik sönümlü yayla dön; tekme torbayı belirgin
        # savurur (darbe karesinde itme yönünde hız), yumruklar yalnızca eski hafif sallanmayla kalır
        kicks = {f: pushes[k] for k, (f, n, _p) in enumerate(sb.hit_pts) if n.endswith(LEG_HITS)}
        w = 2.0 * math.pi / 36.0
        val = vel = 0.0
        n_cur = dirs[0]
        tilt = []
        for lap in range(2):
            for t in range(dur):
                if need[t] > 0.0:
                    n_cur = dirs[t]
                if t in kicks:
                    n_cur = kicks[t]
                    vel += KICK_IMPULSE
                prev = val
                vel += -w * w * val - 2.0 * w * vel
                val += vel
                if val <= need[t]:
                    vel = max(need[t] - prev, 0.0)
                    val = need[t]
                val = max(val, 0.0)
                if lap == 1:
                    tilt.append(self._swing(t) + val * n_cur)
        self.bag_tilt = tilt
        self.bag_report = dict(push_cm=round(float(worst[0]) * 100.0, 1), tilt_deg=round(math.degrees(worst[1]), 1),
                               frame=worst[2], shifted_cm=round(shifted * 100.0, 1))

    def _bag(self):
        b = self.sb.bag
        long_bag = b["long"]
        pivot, chain, length, r = self._bag_dims()
        root = bpy.data.objects.new("bag_pivot", None)
        bpy.context.scene.collection.objects.link(root)
        root.location = Vector(pivot.tolist())
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r, depth=length,
                                            location=(0.0, 0.0, -chain - length / 2))
        body = bpy.context.active_object
        body.name = "bag"
        bev = body.modifiers.new("Bevel", "BEVEL")
        bev.width = 0.025
        bev.segments = 4
        for p in body.data.polygons:
            p.use_smooth = True
        body.modifiers.new("WN", "WEIGHTED_NORMAL")
        leather = outfits.leather("bag_leather", "#2B1C18" if not long_bag else "#1B1B1F", roughness=0.42,
                                  coat=0.25)
        body.data.materials.append(leather)
        band = outfits.leather("bag_band", "#B71C1C", roughness=0.5, coat=0.1)
        body.data.materials.append(band)
        for p in body.data.polygons:
            z = p.center.z + chain + length / 2
            if abs(z - length * 0.12) < 0.03 or abs(z - length * 0.88) < 0.03:
                p.material_index = 1
        body.parent = root
        # askı kayışları ve zincir
        metal = outfits.leather("bag_chain", "#8E9AA3", roughness=0.25, coat=0.0)
        metal.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
        for k in range(4):
            a = math.radians(45 + 90 * k)
            p0 = Vector((math.cos(a) * r * 0.85, math.sin(a) * r * 0.85, -chain))
            p1 = Vector((0.0, 0.0, -chain * 0.45))
            self._rod(f"strap{k}", p0, p1, 0.005, metal, root)
        self._rod("chain", Vector((0, 0, -chain * 0.45)), Vector((0, 0, 0.6)), 0.006, metal, root)
        return root

    def _rod(self, name, p0, p1, radius, mat, parent):
        d = p1 - p0
        bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=radius, depth=d.length, location=(p0 + p1) / 2)
        ob = bpy.context.active_object
        ob.name = name
        ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        ob.data.materials.append(mat)
        ob.parent = parent
        return ob

    def _rope(self):
        cu = bpy.data.curves.new("rope", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.0042
        cu.bevel_resolution = 3
        sp = cu.splines.new("NURBS")
        sp.points.add(ROPE_POINTS - 1)
        sp.use_endpoint_u = True
        sp.order_u = 4
        ob = bpy.data.objects.new("rope", cu)
        bpy.context.scene.collection.objects.link(ob)
        cu.materials.append(outfits.leather("rope_mat", "#263238", roughness=0.5, coat=0.0))
        handle = outfits.leather("rope_handle", "#C62828", roughness=0.45, coat=0.2)
        self.handles = []
        for s in "lr":
            bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.014, depth=0.13)
            h = bpy.context.active_object
            h.name = f"rope_handle_{s}"
            h.data.materials.append(handle)
            self.handles.append(h)
        return ob

    def _update_rope(self, t):
        """İp, iki el arasındaki eksen etrafında dönen bir yay: rope karesinde ayakların altında."""
        sk = self.sb.fsk[t]
        lh, rh = retarget.B(sk.j["lhand"]), retarget.B(sk.j["rhand"])
        axis = unit(rh - lh)
        down = np.array([0.0, 0.0, -1.0])
        down = unit(down - axis * (down @ axis))
        fwd = np.cross(axis, down)
        fwd *= 1.0 if fwd @ retarget.Bv(sk.pelvis[0]) > 0 else -1.0
        ph = 2 * math.pi * (t - self.mv.rope) / self.mv.dur
        mid = (lh + rh) / 2
        R = mid[2] - 0.01  # en altta zeminin ~1 cm üstünden, havadaki ayakların altından geçsin
        # ileri atlama: ip ayak altından geçtikten sonra arkadan yukarı çıkar, baş üstünden öne iner
        radial = down * math.cos(ph) - fwd * math.sin(ph) * 0.85
        pts = []
        for k in range(ROPE_POINTS):
            u = k / (ROPE_POINTS - 1)
            bulge = math.sin(math.pi * u) ** 0.7
            p = lh + (rh - lh) * u + radial * R * bulge
            pts.append(p)
        sp = self.rope.data.splines[0]
        for p, q in zip(sp.points, pts):
            p.co = (q[0], q[1], q[2], 1.0)
        # sapları el içinde, ipin çıkış yönünde tut
        for h, hand in zip(self.handles, (lh, rh)):
            h.location = Vector(hand.tolist())
            h.rotation_euler = Vector((radial + down * 0.3).tolist()).to_track_quat("Z", "Y").to_euler()

    def _camera_and_lights(self, style):
        mv = self.mv
        az, el = math.radians(mv.cam["az"]), math.radians(mv.cam["el"] + 4.0)
        v = unit(retarget.Bv((math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el))))
        pts, pads = [], []
        for sks in (self.sb.fsk, self.sb.psk):
            for sk in sks:
                for name, q in sk.j.items():
                    if isinstance(q, tuple) and len(q) == 3 and isinstance(q[0], float):
                        pts.append(retarget.B(q))
                        pads.append(0.07)  # eklem merkezi -> vücut/eldiven yüzeyi
                        if name.endswith("hand") and q[1] < 10.0:
                            # yere dayanan elin parmakları ileri uzanır
                            fwd_h = retarget.Bv(sk.chest[0]) * np.array([1.0, 1.0, 0.0])
                            pts.append(retarget.B(q) + unit(fwd_h) * 0.15)
                            pads.append(0.04)
                c = retarget.B(sk.point("head"))
                pts.append(c)
                pads.append(0.14)  # kafa (saç dahil)
        if self.sb.bag:
            b = self.sb.bag
            for y in (40.0 if not b["long"] else 22.0, 200.0):
                for dz in (-b["r"], b["r"]):
                    pts.append(retarget.B((b["x"] + b["r"], y, b["z"] + dz)))
                    pads.append(0.02)
        pts = np.array(pts)
        pads = np.array(pads)
        # zemin: en alçak noktanın altı da kadrajda kalsın
        floor_pts = pts.copy()
        floor_pts[:, 2] = 0.0
        pts = np.vstack([pts, floor_pts])
        pads = np.concatenate([pads, np.full(len(floor_pts), 0.02)])
        lens = 55.0
        aspect = WIDTH / HEIGHT
        tx = math.tan(math.atan(18.0 / lens)) * 0.88
        ty = tx / aspect * 0.92 / 0.88
        up_w = np.array([0.0, 0.0, 1.0])
        fwd = -v
        right = unit(np.cross(fwd, up_w))
        up = np.cross(right, fwd)
        center = (pts.min(axis=0) + pts.max(axis=0)) / 2
        for _ in range(3):
            q = pts - center
            x, y, z = q @ right, q @ up, q @ v
            D = max(np.max(z + (np.abs(x) + pads) / tx), np.max(z + (np.abs(y) + pads) / ty))
            # yatay/dikey ortalama düzeltmesi (perspektifte)
            dz_ = D - z
            cx_ = (np.max((x + pads) / dz_) + np.min((x - pads) / dz_)) / 2
            cy_ = (np.max((y + pads) / dz_) + np.min((y - pads) / dz_)) / 2
            center = center + right * cx_ * D * 0.9 + up * cy_ * D * 0.9
        cam_loc = center + v * D
        studio.camera(tuple(cam_loc), tuple(center), lens=lens)
        # ışıklar kameraya göre: sağ-önden ana ışık, soldan dolgu, arkadan kenar
        c = center
        key = unit(right * 0.75 + v * 0.65 + up_w * 0.7)
        fill = unit(-right * 0.95 + v * 0.45 + up_w * 0.15)
        rim = unit(-v * 0.9 + up_w * 0.55 - right * 0.35)
        studio.area_light("key", tuple(c + key * 4.2), tuple(c), 1150.0, 1.8, (1.0, 0.96, 0.92))
        studio.area_light("fill", tuple(c + fill * 4.5), tuple(c), 170.0, 3.0, (0.92, 0.96, 1.0))
        studio.area_light("rim", tuple(c + rim * 3.6), tuple(c + np.array([0, 0, 0.3])), 700.0, 1.4)
        # fon: kameranın tersine dönük sonsuz fon
        bd = studio.backdrop(floor_color=style["floor"], wall_color=style["wall"])
        h = -v.copy()
        h[2] = 0.0
        h = unit(h)
        bd.rotation_euler = (0.0, 0.0, math.atan2(-h[0], h[1]))
        bd.location = (center[0], center[1], 0.0)

    # -- kareler ------------------------------------------------------------------
    def pose(self, t):
        sb = self.sb
        self.fposer.pose(sb.fsk[t])
        if self.opp is not None:
            self.oposer.pose(sb.psk[t])
        if self.bag is not None:
            tilt = self.bag_tilt[t]
            ang = float(np.linalg.norm(tilt))
            d = np.array([tilt[0], tilt[1], 0.0]) / ang if ang > 1e-9 else np.array([1.0, 0.0, 0.0])
            # alt uç eğim yönüne gitsin: eksen = yön x yukarı
            axis = np.cross(d, np.array([0.0, 0.0, 1.0]))
            self.bag.rotation_mode = "QUATERNION"
            self.bag.rotation_quaternion = Quaternion(Vector(axis.tolist()), ang)
        if self.rope is not None:
            self._update_rope(t)

    def render(self, frame_dir, frames=None):
        os.makedirs(frame_dir, exist_ok=True)
        sc = bpy.context.scene
        frames = range(self.mv.dur) if frames is None else frames
        todo = [t for t in frames if not os.path.exists(os.path.join(frame_dir, f"{t:04d}.png"))]
        if not todo:
            return
        sim = bool(self.fig.cloth or (self.opp is not None and self.opp.cloth))
        if sim:
            # kumaş sırayla simüle edilir: dinlenme duruşundan ilk poza geçiş, bir ısınma turu (döngünün
            # başı ile sonu aynı kumaş durumuna otursun), render ikinci turda
            f = self._preroll()
            for t in range(self.mv.dur):
                self.pose(t)
                sc.frame_set(f)
                f += 1
            steps = range(max(todo) + 1)
        else:
            steps = todo
        for t in steps:
            self.pose(t)
            if sim:
                sc.frame_set(f)
                f += 1
            if t not in todo:
                continue
            path = os.path.join(frame_dir, f"{t:04d}.png")
            sc.render.filepath = path + ".tmp.png"
            bpy.ops.render.render(write_still=True)
            os.replace(path + ".tmp.png", path)

    def _preroll(self, n=24):
        """Kumaş simülasyonu dinlenme duruşunda (giysinin dikildiği şekil) başlar, ilk poza yumuşakça geçer."""
        sc = bpy.context.scene
        self.pose(0)
        target = []
        for ch in (self.fig, self.opp):
            if ch is None:
                continue
            for pb in ch.arm_ob.pose.bones:
                target.append((pb, pb.location.copy(), pb.rotation_quaternion.copy()))
        f = 1
        for k in range(n):
            u = k / (n - 1)
            u = u * u * (3.0 - 2.0 * u)
            for pb, loc, rot in target:
                pb.location = loc * u
                pb.rotation_quaternion = Quaternion().slerp(rot, u)
            sc.frame_set(f)
            f += 1
        return f

    def poster_frame(self):
        if self.mv.poster is not None:
            return self.mv.poster
        if self.mv.hits:
            return min(self.mv.dur - 1, self.mv.hits[0][0])
        return int(self.mv.dur * 0.3)


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def encode(frame_dir, mp4, poster_src, poster, fps=30):
    os.makedirs(os.path.dirname(mp4), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i",
                    os.path.join(frame_dir, "%04d.png"), "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                    "-profile:v", "main", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", mp4], check=True)
    os.makedirs(os.path.dirname(poster), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", poster_src, "-vf", "scale=320:-1",
                    "-c:v", "libwebp", "-quality", "86", poster], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.normpath(os.path.join(HERE, "..", "..", "app", "src", "main", "assets")))
    ap.add_argument("--frames", default=os.path.join(HERE, "build", "frames"))
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--preview", help="yalnızca bu kareleri render et (virgüllü), video üretme")
    ap.add_argument("--samples", type=int, default=10)
    ap.add_argument("--draft", action="store_true", help="düşük çözünürlükte her 4. kare + temas sayfası")
    ap.add_argument("--bag-report", action="store_true", help="render etmeden torba temas itmelerini yazdır")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    # iskelet ölçülerini gövdeye eşitle, sonra hareketleri yükle (pozlar yüklenirken çözülür)
    studio.reset_scene()
    retarget.configure_skeleton(retarget.body_dims(Character("probe", shape=FIGHTER_SHAPE)))
    from generate import MOVES
    ids = args.only or sorted(MOVES)
    global WIDTH, HEIGHT
    if args.draft:
        WIDTH, HEIGHT = 320, 256
        args.samples = 6
    for mid in ids:
        t0 = time.time()
        if args.bag_report and MOVES[mid].target not in ("bag", "long_bag"):
            continue
        r = MoveRenderer(mid, MOVES[mid], samples=args.samples)
        r.build()
        if args.bag_report:
            print(f"{mid}: {r.bag_report}", flush=True)
            continue
        fdir = os.path.join(args.frames, mid)
        if args.draft:
            frames = list(range(0, MOVES[mid].dur, 4))
            r.render(fdir, frames)
            sheet = os.path.join(args.frames, f"{mid}_sheet.jpg")
            cols = 6
            rows = (len(frames) + cols - 1) // cols
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-pattern_type", "glob", "-i",
                            os.path.join(fdir, "*.png"), "-vf", f"tile={cols}x{rows}", "-frames:v", "1",
                            "-q:v", "4", sheet], check=True)
        elif args.preview:
            r.render(fdir, [int(x) for x in args.preview.split(",")])
        else:
            r.render(fdir)
            encode(fdir, os.path.join(args.out, "video", f"{mid}.mp4"),
                   os.path.join(fdir, f"{r.poster_frame():04d}.png"), os.path.join(args.out, "poster", f"{mid}.webp"))
        print(f"{mid}: {time.time() - t0:.0f} sn", flush=True)


if __name__ == "__main__":
    main()
