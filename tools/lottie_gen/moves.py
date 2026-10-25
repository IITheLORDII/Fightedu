"""63 hareketin 3B poz tanımları.

Koordinatlar (cm, sporcunun taban çerçevesi): X ileri (hedefe), Y yukarı, Z sporcunun sağı.
Sporcu ortodoks duruşludur (sol ayak önde). Partner otomatik olarak aynalanır (solak),
böylece ikisinin de göğsü kameraya döner.

Poz anahtarları (skeleton.py):
  x,y,z,yaw,pitch,roll   pelvis   (yaw + = sağa dön, pitch + = öne eğil, roll + = sağa yatış)
  cyaw,cpitch,croll      göğüs (kalçaya göre)
  look, hyaw, hpitch     baş (look=1: hedefe bakar), chin: çene içeri (+)
  lh/rh                  el hedefi göğüs çerçevesinde (ileri, yukarı, sağ)
  lhw/rhw + lhk/rhk      el hedefi dünyada (hk=1)
  le/re                  dirsek yönü (göğüs çerçevesi)
  lf/rf                  ayak: planted(x, z, yaw, heel) ya da air(bilek, yaw, pitch, knee)
"""
from scene import Move
from skeleton import BASE_POSE, air, hand_at, merge, planted, shift, turn

P = merge

# ==========================================================================
# GENEL
# ==========================================================================
STAND = P(BASE_POSE, lf=planted(4, -14, -10), rf=planted(4, 14, 10),
          lh=(3, -32, -21), rh=(3, -32, 21))
STAND_WIDE = P(STAND, lf=planted(4, -17, -15), rf=planted(4, 17, 15))
CHAMBER_L = dict(lh=(-4, -9, -17), le=(-1, -0.2, -0.3))
CHAMBER_R = dict(rh=(-4, -9, 17), re=(-1, -0.2, 0.3))

import math  # noqa: E402

import skeleton as _sk  # noqa: E402  (canlı vücut ölçüleri: render3d bunları MakeHuman gövdesine eşitler)


def _g_lift(foot, lift):
    """Yere basan ayağı (planted) aynı açıyla 'lift' cm havaya kaldır."""
    a = foot["a"]
    return dict(foot, a=(a[0], a[1] + lift, a[2]))


def _g_shoulder(side):
    """Omuz eklemi göğüs çerçevesinde (ileri, yukarı, sağ)."""
    return (-_sk.SHOULDER_BACK, _sk.SHOULDER_UP, (-1.0 if side == "l" else 1.0) * _sk.SHOULDER_HALF)


def _g_hand_floor(pose, side, fwd, out=0.0, y=3.0):
    """Eli omzun 'fwd' cm önünde, 'out' cm dışında yere (avuç düz) koy."""
    s = _sk.solve_point(pose, side + "shoulder")
    sg = -1.0 if side == "l" else 1.0
    return P(pose, **{side + "hw": (s[0] + fwd, y, s[2] + sg * out), side + "hk": 1.0})


# -- yerinde koşu (yüksek diz): ön ayakla yumuşak iniş, dirsekler 90° önde-arkada sallanır ----------
_JOG_Y = (96.4, 95.2, 94.4, 94.4, 95.2, 96.4)   # destekteki ayağın fazına göre kalça yüksekliği


def _jog_foot(side, k):
    """k = ayak fazı (0..9): 0 ön ayakla iniş, 0-5 destek, 5 itiş, 6-9 salınım (7: diz kalça hizasında)."""
    z, yaw = (-12.0, -6.0) if side == "l" else (12.0, 6.0)
    heel = {0: 24, 1: 15, 2: 10, 3: 12, 4: 22, 5: 42}
    if k in heel:
        return planted(6, z, yaw, heel=heel[k])
    if k == 9:
        return _g_lift(planted(6, z, yaw, heel=26), 3.0)
    ax, ay, pitch = {6: (12, 30, 40), 7: (32, 44, 25), 8: (20, 32, 30)}[k]
    return air((ax, ay, z), yaw=yaw, pitch=pitch, knee=(1, 0.4, 0))


def _jog_key(i):
    kl, kr = (7 + i) % 10, (2 + i) % 10
    a = math.cos(2 * math.pi * i / 10)          # +1: sağ kol önde, sol diz yukarıda

    def arm(s):
        # dirsek ~90°: el omuz çevresinde yay çizer (arkada kalça yanı, önde göğüs hizası), gövdenin yanında
        w = (1 + (a if s == "r" else -a)) / 2       # 0 = arkada, 1 = önde
        sx, sy, _sz = _g_shoulder(s)
        ang, rad = math.radians(-89 + 72 * w), 40.0 + 1.5 * w
        return (sx + rad * math.cos(ang), sy + rad * math.sin(ang), (-1.0 if s == "l" else 1.0) * (25.0 - 7.0 * w))
    return P(STAND, y=_JOG_Y[min(kl, kr)], pitch=4, cpitch=2, yaw=2 * a, cyaw=-5 * a,
             lf=_jog_foot("l", kl), rf=_jog_foot("r", kr), lh=arm("l"), rh=arm("r"),
             le=(-1, -0.5, -0.15), re=(-1, -0.5, 0.15))


# -- kol çevirme: kollar yana açık (omuz hizası), iki el aynı fazda; küçükten büyüğe ileri, sonra geri --
def _arm_circle_keys(dur=64, revs=3.0, r0=5.0, r1=30.0, reach=64.0):
    half = dur // 2
    n = 400   # açısal hız ~ sqrt(s(1-s)): döngü başında ve yön değişiminde yavaşlar
    w = [math.sqrt((i + 0.5) / n * (1 - (i + 0.5) / n)) for i in range(n)]
    cum = [0.0]
    for v in w:
        cum.append(cum[-1] + v / sum(w))
    keys = []
    for t in range(dur):
        s = t / half if t <= half else (dur - t) / half      # ikinci yarı: aynı yol, ters yönde
        th = 2 * math.pi * revs * cum[int(round(s * n))]
        r = r0 + (r1 - r0) * s
        dx, dy = r * math.sin(th), r * math.cos(th)          # th = 0 tepede; artan th = ileri daire
        lat = math.sqrt(reach * reach - r * r)
        d = {}
        for side, sg in (("l", -1.0), ("r", 1.0)):
            sx, sy, sz = _g_shoulder(side)
            d[side + "h"] = (sx + dx, sy + dy, sz + sg * lat)
            d[side + "e"] = (-1.0, -0.2, 0.0)
        keys.append((t, P(STAND, **d)))
    return keys


# -- squat: ayaklar omuz genişliğinde, parmaklar ~15° dışa; kalça geriye, uyluk yere paralel ----------
SQ_FEET = dict(lf=planted(4, -23, -15), rf=planted(4, 23, 15))
SQ_TOP = P(STAND, **SQ_FEET, lh=(4, -32, -23), rh=(4, -32, 23))
SQ_MID = P(STAND, **SQ_FEET, x=-17, y=77, pitch=22, autoy=0, chin=-4, le=(-1, -0.3, -0.2), re=(-1, -0.3, 0.2))
SQ_MID = hand_at(hand_at(SQ_MID, "l", (46, -40, 4)), "r", (46, -40, -4))
SQ_LOW = P(STAND, **SQ_FEET, x=-28, y=52, pitch=40, cpitch=-4, autoy=0, chin=-8, le=(-1, -0.3, -0.2),
           re=(-1, -0.3, 0.2))
SQ_LOW = hand_at(hand_at(SQ_LOW, "l", (63, 0, 3)), "r", (63, 0, -3))


# -- ip atlama: eller kalçanın ~20 cm yanında, bileklerle küçük daireler; ip kare 10'da ayak altından geçer --
_ROPE = {0: (97.4, 12, 0.0), 2: (98.0, 16, 0.0), 4: (99.8, 26, 0.0), 6: (101.8, 38, 0.0), 8: (105.4, 36, 3.6),
         10: (107.2, 36, 5.5), 12: (105.4, 36, 3.6), 14: (101.8, 38, 0.0), 16: (99.8, 26, 0.0), 18: (98.0, 16, 0.0)}


def _rope_key(t, dur=20, rope=10):
    y, heel, lift = _ROPE[t]
    ph = 2 * math.pi * (t - rope) / dur
    cx, cy = -3.0 * math.sin(ph), -3.0 * math.cos(ph)
    feet = {}
    for s, z, yaw in (("l", -11.0, -5.0), ("r", 11.0, 5.0)):
        f = planted(6, z, yaw, heel=heel)
        feet[s + "f"] = _g_lift(f, lift) if lift else f
    return P(STAND, y=y, autoy=0, pitch=2, **feet,
             lhw=(18 + cx, y - 9 + cy, -37), rhw=(18 + cx, y - 9 + cy, 37), lhk=1, rhk=1,
             le=(-1, -0.5, 0.1), re=(-1, -0.5, -0.1))


# -- plank / şınav: baştan topuğa düz vücut, parmak uçlarında ---------------------------------------------
def _straight_body(sh_y, sh_x=None, ball_x=0.0, heel=75.0, cpitch=0.0, foot_z=10.0, hpitch=-16.0):
    """Omuz eklemi sh_y cm yükseklikte olacak şekilde kalça eğimi çözülür; bacaklar gövdenin devamı.
    sh_x verilirse ayaklar omuz o x'te olacak şekilde kaydırılır, yoksa top noktası ball_x'tedir."""
    L = _sk.THIGH + _sk.SHIN - 0.1
    h = math.radians(heel)
    ax = -_sk.FOOT_BALL * math.cos(h) + _sk.FOOT_BALL_DOWN * math.sin(h)
    ay = _sk.BALL_R + _sk.FOOT_BALL * math.sin(h) + _sk.FOOT_BALL_DOWN * math.cos(h)

    def solve(pitch):
        p, c = math.radians(pitch), math.radians(pitch + cpitch)
        ox, oy = ax + (L + _sk.HIP_DOWN) * math.sin(p), ay + (L + _sk.HIP_DOWN) * math.cos(p)
        sx = ox + _sk.CHEST_UP * math.sin(p) + _sk.SHOULDER_UP * math.sin(c) - _sk.SHOULDER_BACK * math.cos(c)
        sy = oy + _sk.CHEST_UP * math.cos(p) + _sk.SHOULDER_UP * math.cos(c) + _sk.SHOULDER_BACK * math.sin(c)
        return ox, oy, sx, sy

    lo, hi = 30.0, 100.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if solve(mid)[3] > sh_y:
            lo = mid
        else:
            hi = mid
    ox, oy, sx, _sy = solve(lo)
    bx = ball_x if sh_x is None else sh_x - sx
    return P(STAND, x=ox + bx, y=oy, pitch=lo, cpitch=cpitch, look=0, hpitch=hpitch, autoy=0,
             lf=dict(planted(bx, -foot_z, 0, heel=heel), knee=(0.2, -1, 0)),
             rf=dict(planted(bx, foot_z, 0, heel=heel), knee=(0.2, -1, 0)))


# şınav: üstte kollar düz, el bilekleri omuzların altında; altta göğüs yerden ~7 cm, dirsekler ~45°
_PU_ARM = _sk.UPPER_ARM + _sk.FOREARM
PU_UP = P(_straight_body(_PU_ARM + 2.0, heel=68), le=(-0.9, -0.9, -0.8), re=(-0.9, -0.9, 0.8))
PU_UP = _g_hand_floor(_g_hand_floor(PU_UP, "l", 6.0, 4.0), "r", 6.0, 4.0)
PU_DN = P(_straight_body(20.0, ball_x=0.0, heel=84), le=(-0.9, -0.9, -0.8),
          re=(-0.9, -0.9, 0.8), lhw=PU_UP["lhw"], rhw=PU_UP["rhw"], lhk=1, rhk=1)
# önkol plankı: önkollar yerde paralel, dirsekler omuzların altında
PLANK = P(_straight_body(_sk.UPPER_ARM + 5.5, heel=76), le=(0.7, -0.7, -0.2), re=(0.7, -0.7, 0.2))
PLANK = _g_hand_floor(_g_hand_floor(PLANK, "l", _sk.FOREARM + 4.5, -4.0), "r", _sk.FOREARM + 4.5, -4.0)

# -- mekik: sırt ve baş yerde (boyun nötr), eller çapraz omuzlarda; kalkışta çene içeride ------------------
_SIT_FEET = dict(lf=dict(planted(36, -14, -8), knee=(0.2, 1, -0.3)), rf=dict(planted(36, 14, 8), knee=(0.2, 1, 0.3)))
SIT_DOWN = P(STAND, **_SIT_FEET, y=10, pitch=-90, cpitch=-6, look=0, hpitch=10, autoy=0,
             lh=(10, 23, 14), rh=(19, 21, -14), le=(0.3, -0.9, 0.2), re=(0.3, -0.9, -0.2))
SIT_UP = P(SIT_DOWN, pitch=-57, cpitch=6, hpitch=18, chin=6)   # dirsekler uyluklara değmeden durur

# -- burpee ---------------------------------------------------------------------------------------------
_B_FEET = dict(lf=planted(4, -11, -5, heel=18), rf=planted(4, 11, 5, heel=18))
_B_HANDS = dict(lhw=(38, 3, -27), rhw=(38, 3, 27), lhk=1, rhk=1, le=(-0.5, -1, -0.4), re=(-0.5, -1, 0.4))
B_DOWN = P(STAND, **_B_FEET, x=-6, y=74, pitch=32, cpitch=6, look=0, hpitch=-14, lhw=(42, 42, -27), rhw=(42, 42, 27),
           lhk=1, rhk=1, le=(-0.5, -1, -0.4), re=(-0.5, -1, 0.4))
B_SQUAT = P(STAND, **_B_FEET, **_B_HANDS, x=-4, y=50, pitch=46, cpitch=8, look=0, hpitch=-16, autoy=1)
B_PLANK = P(_straight_body(_PU_ARM + 2.0, sh_x=38 - 4.5 - 1.5, heel=70, foot_z=12), **_B_HANDS)
B_KICK = P(STAND, **_B_HANDS, x=-6, y=62, pitch=66, cpitch=6, look=0, hpitch=-24, autoy=0,
           lf=air((-52, 22, -12), yaw=0, pitch=50, knee=(0.3, -1, 0)), rf=air((-52, 22, 12), yaw=0, pitch=50,
                                                                                knee=(0.3, -1, 0)))
B_RISE = P(STAND, **_B_FEET, x=-3, y=86, pitch=16, cpitch=2, look=1, le=(-1, -0.3, -0.3), re=(-1, -0.3, 0.3))
B_RISE = hand_at(hand_at(B_RISE, "l", (58, 14, -6)), "r", (58, 14, 6))
B_REACH = P(STAND, **_B_FEET, x=-1, y=94, pitch=6, le=(-1, 0, -0.4), re=(-1, 0, 0.4))
B_REACH = P(B_REACH, lf=_g_lift(B_REACH["lf"], 2.0), rf=_g_lift(B_REACH["rf"], 2.0), autoy=0)
B_REACH = hand_at(hand_at(B_REACH, "l", (40, 46, -12)), "r", (40, 46, 12))
B_AIR = P(STAND, y=118, autoy=0, pitch=-2,
          lf=air((1, 29, -12), yaw=-6, pitch=45), rf=air((1, 29, 12), yaw=6, pitch=45),
          lh=(_g_shoulder("l")[0] + 8, _g_shoulder("l")[1] + 60, _g_shoulder("l")[2] - 9),
          rh=(_g_shoulder("r")[0] + 8, _g_shoulder("r")[1] + 60, _g_shoulder("r")[2] + 9),
          le=(-1, 0, -0.4), re=(-1, 0, 0.4))
B_OPEN = P(STAND, y=108, autoy=0, pitch=2,
           lf=air((2, 18, -12), yaw=-6, pitch=35), rf=air((2, 18, 12), yaw=6, pitch=35),
           lh=(6, 40, -84), rh=(6, 40, 84), le=(-1, -0.2, 0), re=(-1, -0.2, 0))
B_LAND = P(STAND, x=0, y=88, pitch=12, cpitch=2, lf=planted(4, -13, -8), rf=planted(4, 13, 8),
           lh=(8, -18, -70), rh=(8, -18, 70), le=(-1, -0.4, 0), re=(-1, -0.4, 0))

# -- arka bacak esnetme: kalçadan katlan, eller bacakların ÖNÜNDEN bileklere doğru kayar --------------------
_HAM_FEET = dict(lf=planted(4, -10, -4), rf=planted(4, 10, 4))


def _ham(pitch, x, frac, cpitch=0.0, hpitch=0.0, look=0.0):
    """frac: elin bacak üzerindeki yeri (0 kalça, 1 diz, 2 bilek); el, bacağın ön yüzünün hemen önünde."""
    p = P(STAND, **_HAM_FEET, x=x, pitch=pitch, cpitch=cpitch, look=look, hpitch=hpitch,
          le=(-0.3, 0, -1), re=(-0.3, 0, 1))
    for s, sg in (("l", -1.0), ("r", 1.0)):
        hip, knee, ank = (_sk.solve_point(p, s + n) for n in ("hip", "knee", "ankle"))
        a, b, f = (hip, knee, frac) if frac <= 1 else (knee, ank, frac - 1)
        off = 12.5 - 3.5 * frac if frac <= 1 else 9.0 - 2.0 * (frac - 1)
        p[s + "hw"] = (a[0] + (b[0] - a[0]) * f + off, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f + sg)
        p[s + "hk"] = 1.0
    return p


QUAD_ST = P(STAND, lf=planted(4, -8, -4), rf=air((-18, 86, 10), yaw=180, pitch=-70, knee=(0.15, -1, 0)),
            rhw=(-20, 90, 17), rhk=1, re=(-1, -0.3, 0.6), lh=(30, 18, -22), le=(0, -1, -0.5), roll=-2)
SHOULDER_ST = P(STAND, lh=(16, 24, 38), le=(1, 0, 0), rh=(24, 22, 2), re=(0, -1, 0.6))

GENERAL = {
    "gen_jog": Move("general", 30, [(3 * i, _jog_key(i)) for i in range(10)], cam=dict(az=30)),
    "gen_arm_circles": Move("general", 64, _arm_circle_keys(), cam=dict(az=60, el=10)),
    "gen_squat": Move("general", 56, [(0, SQ_TOP), (12, SQ_MID), (24, SQ_LOW), (32, SQ_LOW), (44, SQ_MID)],
                      cam=dict(az=38)),
    "gen_jump_rope": Move("general", 20, [(t, _rope_key(t)) for t in range(0, 20, 2)], cam=dict(az=45), rope=10),
    "gen_pushup": Move("general", 50, [(0, PU_UP), (20, PU_DN), (28, PU_DN)], cam=dict(az=18, el=12)),
    "gen_plank": Move("general", 60, [(0, PLANK), (30, P(PLANK, y=PLANK["y"] + 1.0))], cam=dict(az=18, el=12)),
    "gen_situp": Move("general", 50, [(0, SIT_DOWN), (20, SIT_UP), (26, SIT_UP)], cam=dict(az=25, el=16)),
    "gen_stretch_hamstring": Move("general", 80, [
        (0, _ham(0, 0, 0.3, look=1)), (9, _ham(30, -4, 0.75, cpitch=4)), (18, _ham(58, -8, 1.1, cpitch=12)),
        (28, _ham(84, -12, 1.5, cpitch=26, hpitch=6)), (50, _ham(90, -13, 1.65, cpitch=30, hpitch=8)),
        (60, _ham(82, -12, 1.45, cpitch=24, hpitch=6)), (68, _ham(56, -8, 1.05, cpitch=10)),
        (74, _ham(28, -4, 0.7, cpitch=4))], cam=dict(az=25)),
    "gen_stretch_quad": Move("general", 60, [(0, QUAD_ST), (30, P(QUAD_ST, pitch=3))], cam=dict(az=20)),
    "gen_stretch_shoulder": Move("general", 60, [(0, SHOULDER_ST), (30, P(SHOULDER_ST, rh=(18, 24, 2)))],
                                 cam=dict(az=55)),
    "gen_burpee": Move("general", 64, [(0, STAND), (6, B_DOWN), (11, B_SQUAT), (16, B_KICK), (21, B_PLANK),
                                       (27, B_PLANK), (32, B_KICK), (37, B_SQUAT), (42, B_RISE), (45, B_REACH),
                                       (49, B_AIR), (52, B_OPEN), (56, B_LAND)], cam=dict(az=25, el=10)),
}

# ==========================================================================
# BOKS
# ==========================================================================
# Duruşta ayak uçları rakibe/torbaya bakar: ön ayak neredeyse düz, arka ayak ~30° açık (topuk hafif kalkık).
# Arka elle vuruşta (cross, arka kroşe/aparkat) arka ayak topun üstünde döner: topuk dışarı, parmaklar
# torbaya; ön elle kroşede ön ayak aynı şekilde içe döner.
BOX_LF_YAW, BOX_RF_YAW = 8.0, 30.0
BOX = P(BASE_POSE, y=90, z=2, yaw=38, pitch=5, cpitch=7, chin=10,
        lh=(24, 42, -15), rh=(14, 39, 7), le=(-0.1, -1, -0.45), re=(-0.25, -1, 0.4),
        lf=planted(26, -9, BOX_LF_YAW), rf=planted(-28, 15, BOX_RF_YAW, heel=20))
BOX_DIP = P(BOX, y=87, chin=12)
JAB = hand_at(P(BOX, yaw=44, cyaw=6, pitch=7, rf=planted(-28, 15, BOX_RF_YAW, heel=26), le=(0, -1, -0.2)),
              "l", (57, 6, 6))
# cross: kalça ve omuz tam döner, kol neredeyse düz; yumruk jab ile aynı uzaklığa (torbanın önüne) gider
CROSS = P(BOX, x=5, yaw=-4, cyaw=-12, pitch=11, rf=planted(-28, 15, 2, heel=50), lh=(18, 41, -9),
          re=(0, -1, 0.2), rhw=(81.5, 136, 4), rhk=1)
LHOOK_PREP = P(BOX, yaw=30, cyaw=-6)
LHOOK = hand_at(P(BOX, yaw=62, cyaw=14, pitch=6, lf=planted(26, -9, 62, heel=14), rh=(13, 40, 6),
                  le=(0.1, 0.35, -1)), "l", (38, 6, 26))
RHOOK = hand_at(P(BOX, yaw=-2, cyaw=-16, pitch=6, rf=planted(-28, 15, 0, heel=50), lh=(14, 43, -15),
                  re=(0.1, 0.35, 1)), "r", (38, 6, -26))
# arka kroşe yolu: yumruk önce dışarı-sağa açılır (dirsek omuz hizasında), sonra yatay yayla gelir; sol eldiven
# yanakta kalır, iki eldiven birbirine değmez
RHOOK_MID = hand_at(P(BOX, yaw=16, cyaw=-8, pitch=6, rf=planted(-28, 15, 14, heel=36), lh=(16, 43, -16),
                      re=(0, 0.15, 1)), "r", (32, 6, 8))
LUPPER_DIP = P(BOX, y=84, roll=-6, croll=-8, cpitch=10, lh=(22, 28, -14), le=(0, -1, -0.2))
LUPPER = hand_at(P(BOX, yaw=50, cyaw=8, pitch=2, cpitch=4, roll=4, lf=planted(26, -9, 40, heel=10),
                   le=(0, -1, -0.1)), "l", (38, 4, 14))
RUPPER_DIP = P(BOX, y=84, roll=6, croll=8, cpitch=10, rh=(16, 26, 8), re=(0, -1, 0.2))
RUPPER = hand_at(P(BOX, yaw=8, cyaw=-8, pitch=4, rf=planted(-28, 15, 6, heel=45), lh=(18, 41, -8),
                   re=(0, -1, 0.1)), "r", (38, 2, -14))
SLIP = P(BOX, y=84, z=8, roll=4, croll=18, cyaw=-8, cpitch=12)
ROLL_L = P(BOX, y=76, z=-6, pitch=14, cpitch=20, croll=-14)
ROLL_B = P(BOX, y=68, pitch=18, cpitch=26)
ROLL_R = P(BOX, y=80, z=8, pitch=10, cpitch=14, croll=14)
PARRY = P(BOX, rh=(30, 44, -12), re=(0, -1, 0.2))
# blok: eldiven şakakta, dirsek öne-aşağı (yana açılmaz), çene içeride
BLOCK = P(BOX, lh=(5, 50, -15), le=(1, -0.5, -0.15), chin=14)
# box_combo_123 kroşesi: dirsek ~90°, önkol yatay; yumruk torbanın sol-ön yüzüne yandan girer.
# Torba merkezi jab/cross/kroşe vuruşlarından (103, -4.8) çıkar.
C123_BAG = (103.0, -4.8)
LHOOK_C = P(BOX, x=17, z=-8, yaw=44, cyaw=10, pitch=6, lf=planted(43, -17, 52, heel=14),
            rf=planted(-11, 7, BOX_RF_YAW, heel=24), rh=(13, 40, 6), le=(0.1, 0.1, -1),
            lhw=(C123_BAG[0] - 17.7, 137, C123_BAG[1] - 14.8), lhk=1)
LHOOK_C_PREP = P(BOX, x=4, z=-3, yaw=26, cyaw=-6, lf=planted(32, -13, 16), lh=(20, 43, -18), le=(-0.3, -1, -0.8))


import skeleton as _skl  # noqa: E402  (ölçüler render sırasında ayarlanır; çağrı anında okunur)


def _parry_hook():
    """box_parry_block partner kroşesi (partnerin aynalanmadan önceki kendi çerçevesinde): yumruk,
    öğrencinin şakaktaki blok eldiveninin dış yüzüne gelir; partner yarım adım içeri girer."""
    g = _skl.solve_point(BLOCK, "lhand")
    tgt = (PARRY_DIST - g[0], g[1] + 1.0, g[2] - 11.0)
    return P(BOX, x=30, yaw=48, cyaw=10, pitch=6, lf=planted(56, -9, 52, heel=14),
             rf=planted(0, 15, BOX_RF_YAW, heel=24), rh=(13, 40, 6), le=(0.1, 0.6, -1), lhw=tgt, lhk=1)


PARRY_DIST = 118.0
PB_HOOK_PREP = P(BOX, x=16, yaw=30, cyaw=-6, lf=planted(42, -9, 18), rf=planted(-12, 15, BOX_RF_YAW, heel=24))
PB_HOOK = _parry_hook()


def box_feet(lx, rx, x):
    return P(BOX, x=x, lf=planted(lx, -9, BOX_LF_YAW), rf=planted(rx, 15, BOX_RF_YAW, heel=20))


BOXING = {
    "box_stance": Move("boxing", 60, [(0, BOX), (15, BOX_DIP), (30, BOX), (45, BOX_DIP)], cam=dict(az=28)),
    "box_footwork": Move("boxing", 64, [
        (0, box_feet(8, -44, -16)), (10, box_feet(34, -44, -5)), (20, box_feet(34, -18, 8)),
        (32, box_feet(34, -18, 8)), (42, box_feet(34, -44, -5)), (52, box_feet(8, -44, -16))],
        cam=dict(az=12)),
    "box_jab": Move("boxing", 36, [(0, BOX), (8, JAB), (13, JAB), (24, BOX)], cam=dict(az=16),
                    target="bag", hits=[(8, "lhand")]),
    "box_cross": Move("boxing", 40, [(0, BOX), (10, CROSS), (15, CROSS), (28, BOX)], cam=dict(az=16),
                      target="bag", hits=[(10, "rhand")]),
    "box_lead_hook": Move("boxing", 42, [(0, BOX), (5, LHOOK_PREP), (13, LHOOK), (18, LHOOK), (30, BOX)],
                          cam=dict(az=34, el=24), target="bag", hits=[(13, "lhand")]),
    "box_rear_hook": Move("boxing", 42, [(0, BOX), (7, RHOOK_MID), (13, RHOOK), (18, RHOOK), (30, BOX)],
                          cam=dict(az=34, el=24),
                          target="bag", hits=[(13, "rhand")]),
    "box_lead_uppercut": Move("boxing", 42, [(0, BOX), (6, LUPPER_DIP), (13, LUPPER), (18, LUPPER), (30, BOX)],
                              cam=dict(az=22), target="bag", hits=[(13, "lhand")]),
    "box_rear_uppercut": Move("boxing", 42, [(0, BOX), (6, RUPPER_DIP), (13, RUPPER), (18, RUPPER), (30, BOX)],
                              cam=dict(az=22), target="bag", hits=[(13, "rhand")]),
    "box_slip": Move("boxing", 44, [(0, BOX), (10, SLIP), (16, SLIP), (28, BOX)], cam=dict(az=42),
                     target="partner", opp_dist=116, opp=[(0, BOX), (10, JAB), (15, JAB), (26, BOX)],
                     trails=[("head", 0, 10)]),
    "box_roll": Move("boxing", 56, [(0, BOX), (10, ROLL_L), (18, ROLL_B), (27, ROLL_R), (40, BOX)],
                     cam=dict(az=42), target="partner", opp_dist=122,
                     opp=[(0, BOX), (8, LHOOK_PREP), (17, LHOOK), (22, LHOOK), (34, BOX)],
                     trails=[("head", 4, 28)]),
    "box_parry_block": Move("boxing", 48, [(0, BOX), (7, PARRY), (13, BOX), (24, BLOCK), (32, BLOCK), (40, BOX)],
                            cam=dict(az=38, el=16), target="partner", opp_dist=PARRY_DIST,
                            opp=[(0, BOX), (7, JAB), (12, BOX), (18, PB_HOOK_PREP), (24, PB_HOOK), (31, PB_HOOK),
                                 (40, BOX)]),
    "box_combo_12": Move("boxing", 48, [(0, BOX), (7, JAB), (12, P(BOX, yaw=30)), (19, CROSS), (24, CROSS),
                                        (36, BOX)], cam=dict(az=16), target="bag",
                         hits=[(7, "lhand"), (19, "rhand")]),
    "box_combo_123": Move("boxing", 62, [(0, BOX), (7, JAB), (12, P(BOX, yaw=30)), (19, CROSS), (24, CROSS),
                                         (27, LHOOK_C_PREP), (32, LHOOK_C), (37, LHOOK_C), (48, BOX)],
                          cam=dict(az=24, el=22),
                          target="bag", hits=[(7, "lhand"), (19, "rhand"), (32, "lhand")]),
    "box_shadow": Move("boxing", 120, [
        (0, BOX), (7, JAB), (13, BOX), (20, CROSS), (28, BOX), (38, SLIP), (46, BOX), (54, LHOOK_PREP),
        (60, LHOOK), (68, BOX), (76, ROLL_L), (82, ROLL_B), (88, ROLL_R), (98, BOX), (105, RUPPER), (112, BOX)],
        cam=dict(az=24)),
}

# ==========================================================================
# KİCK BOKS
# ==========================================================================
KB_LF_YAW, KB_RF_YAW = 6.0, 26.0
KB = P(BOX, y=92, yaw=33, pitch=3, cpitch=5, lf=planted(24, -7, KB_LF_YAW), rf=planted(-24, 13, KB_RF_YAW, heel=15),
       lh=(24, 43, -14), rh=(14, 40, 7))
KB_DIP = P(KB, y=89)
# Torba merkezi (102.5, ~2): jab ve cross yumrukları aynı noktaya (torbanın önü) gider.
KB_JAB = P(KB, yaw=40, cyaw=6, pitch=5, rf=planted(-24, 13, KB_RF_YAW, heel=22), le=(0, -1, -0.2),
           lhw=(81, 140, 0), lhk=1)
KB_CROSS = P(KB, x=6, yaw=-4, cyaw=-14, pitch=8, rf=planted(-24, 13, 2, heel=48), lh=(18, 42, -9),
             re=(0, -1, 0.2), rhw=(81, 137, 4), rhk=1)
# Sol kroşe (kb_combo_jcm): dirsek ~90°, önkol yatay; yumruk torbanın sol-ön yüzüne yandan girer.
JCM_BAG = (102.5, -5.4)
KB_LHOOK_PREP = P(KB, x=4, z=-3, yaw=22, cyaw=-6, lf=planted(26, -15, 14), lh=(20, 44, -18), le=(-0.3, -1, -0.8))
KB_LHOOK = P(KB, x=12, z=-8, yaw=42, cyaw=10, pitch=6, lf=planted(24, -19, 52, heel=14),
             rf=planted(-14, 6, KB_RF_YAW, heel=20), rh=(13, 41, 6), le=(0.1, 0.1, -1),
             lhw=(JCM_BAG[0] - 17.7, 139, JCM_BAG[1] - 14.8), lhk=1)
TEEP_CH = P(KB, pitch=-4, lf=air((32, 52, -6), yaw=10, pitch=-15, knee=(1, 0.6, 0)), rf=planted(-24, 13, KB_RF_YAW, heel=8))
TEEP = P(KB, x=4, pitch=-14, cpitch=0, lf=air((80, 94, -4), yaw=0, pitch=-55, knee=(1, 0.3, 0)),
         rf=planted(-24, 13, KB_RF_YAW, heel=6))

# --- yuvarlak tekme (Muay Thai roundhouse) ---------------------------------------------
# Bacak, kalça ekleminden yön + diz bükümü ile yerleştirilir (kalça konumu pozdan çözülür;
# ölçüler render sırasında MakeHuman gövdesine ayarlandığı için çağrı anında okunur).
import math as _math  # noqa: E402

import skeleton as _skl  # noqa: E402


def _kdir(a, e):
    """Yatay açı a (+X'ten +Z'ye doğru) ve yükseliş e (derece) ile birim vektör."""
    a, e = _math.radians(a), _math.radians(e)
    return (_math.cos(a) * _math.cos(e), _math.sin(e), _math.sin(a) * _math.cos(e))


def _vlin(*terms):
    out = [0.0, 0.0, 0.0]
    for v, k in terms:
        for i in range(3):
            out[i] += v[i] * k
    return tuple(out)


def _vunit(v):
    n = _math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def kick_leg(pose, side, a, e, bend, pole, hook=25.0, roll=0.0):
    """Havadaki bacak: uyluk yönü (a, e), diz bükümü 'bend' derece; diz kapağı 'pole' yönüne
    bakar, baldır ters yöne bükülür. Ayak baldır doğrultusunda, 'hook' derece diz kapağı
    tarafına kıvrık (gergin ayak bileği)."""
    probe = P(pose, **{side + "f": air((0.0, 60.0, 30.0 if side == "r" else -30.0))})
    hip = _skl.solve_point(probe, side + "hip")
    td = _kdir(a, e)
    pl = _vunit(_vlin((pole, 1.0), (td, -sum(p * t for p, t in zip(pole, td)))))
    b = _math.radians(bend)
    sd = _vlin((td, _math.cos(b)), (pl, -_math.sin(b)))
    knee = _vlin((hip, 1.0), (td, _skl.THIGH))
    ank = _vlin((knee, 1.0), (sd, _skl.SHIN))
    h = _math.radians(hook)
    fd = _vunit(_vlin((sd, _math.cos(h)), (pl, _math.sin(h))))
    fy = _math.degrees(_math.atan2(fd[2], fd[0]))
    fp = -_math.degrees(_math.asin(max(-1.0, min(1.0, fd[1]))))
    return P(pose, **{side + "f": air(ank, yaw=fy, pitch=fp, knee=pole, roll=roll)})


def _sweep(a, up=0.35):
    """Sağ bacağın savrulma yönü (diz kapağı buraya bakar): -Z'ye doğru, biraz yukarı."""
    r = _math.radians(a)
    return (_math.sin(r), up, -_math.cos(r))


def rk_leg(pose, a, e, bend, up=0.35, hook=25.0, roll=-55.0):
    # dönen tekmede ayak bileği içe döner: ayak üstü ve kaval hedefe bakar
    return kick_leg(pose, "r", a, e, bend, _sweep(a, up), hook, roll)


def leg_off(pose, side, off, pole, fy, fp):
    """Havadaki bacak: bilek = kalça eklemi + off; diz 'pole' yönüne bakar."""
    probe = P(pose, **{side + "f": air((0.0, 60.0, 30.0 if side == "r" else -30.0))})
    hip = _skl.solve_point(probe, side + "hip")
    return P(pose, **{side + "f": air(_vlin((hip, 1.0), (off, 1.0)), yaw=fy, pitch=fp, knee=pole)})


def rk_aim(pose, a, bend, y, up=0.35):
    """Uyluk yükselişini (e), kaval vuruş noktası (diz->bilek %60) 'y' yüksekliğinde olacak şekilde
    seç; (e, poz) döndürür."""
    best = None
    for e10 in range(-450, 701, 5):
        p = rk_leg(pose, a, e10 / 10.0, bend, up)
        d = abs(_skl.solve_point(p, "rshin")[1] - y)
        if best is None or d < best[0]:
            best = (d, e10 / 10.0, p)
    return best[1], best[2]


# Yükseklik başına: kalça yatışı (roll), göğüs karşı dönüşü, hedef kaval yüksekliği, kalça yüksekliği
RK_H = {"low": dict(roll=-14, cyaw=38, croll=6, y=64, bend=24, yp=96),
        "mid": dict(roll=-25, cyaw=42, croll=8, y=112, bend=22, yp=102),
        "high": dict(roll=-40, cyaw=46, croll=14, y=154, bend=18, yp=104)}
RK_GUARD = dict(lh=(23, 46, 8), le=(-0.2, -1, -0.6), chin=12)


def _shin_bag(pose):
    """Sahnenin 'rshin' vuruşu için torbayı koyacağı merkez (x, z)."""
    knee, ank = _skl.solve_point(pose, "rknee"), _skl.solve_point(pose, "rankle")
    sh = _skl.solve_point(pose, "rshin")
    h = _vunit((ank[0] - knee[0], 0.0, ank[2] - knee[2]))
    return sh[0] + h[2] * 20.5, sh[2] - h[0] * 20.5


def rk_seq(t, height, step=(32, -24), pel=(34, -14), bag=None, bend=None, sup=-150, x0=(0.0, 2.0), shin=None,
           follow=True):
    """Sağ arka bacakla yuvarlak tekme; vuruş t karesinde. Ön ayak dışa açık adım alır, ayak
    topunda topuk hedefe dönecek kadar döner; kalça devrilir, gövde karşı yana yatar, sol el
    çenede, sağ kol aşağı-geriye savrulur. Bacak hemen hemen düz, arkadan-yandan yatay bir yayla
    gelir ve aynı yoldan geri döner (öne kalkan diz/chamber yok). x0: tekmeden önceki kalça (x, z).
    bag=(x, z) verilirse tekme o torba merkezine, shin=(x, y, z) verilirse kaval vuruş noktası oraya
    oturacak şekilde (adım/kalça birlikte) kaydırılır. follow=False: vuruştan sonra bacak ileri gitmez,
    hafifçe geri seker (kavala çarpıp duran tekme)."""
    hp = dict(RK_H[height])
    if bend is not None:
        hp["bend"] = bend
    if shin is not None:
        hp["y"] = shin[1]
    if bag is not None or shin is not None:
        probe = _rk_build(t, hp, step, pel, sup, x0, follow)[4][1]
        if bag is not None:
            bx, bz = _shin_bag(probe)
            dx, dz = bag[0] - bx, bag[1] - bz
        else:
            q = _skl.solve_point(probe, "rshin")
            dx, dz = shin[0] - q[0], shin[2] - q[2]
        step, pel = (step[0] + dx, step[1] + dz), (pel[0] + dx, pel[1] + dz)
    return _rk_build(t, hp, step, pel, sup, x0, follow)


def _rk_build(t, hp, step, pel, sup, x0, follow=True):
    sx, sz = step
    px, pz = pel
    lerp = lambda u: (x0[0] + u * (px - x0[0]), x0[1] + u * (pz - x0[1]))  # noqa: E731
    k = (hp["y"] - 60) / 94.0          # 0 = alçak, 1 = yüksek

    def body(u, yaw, sup_yaw, heel, rh, re, roll_k, cy_k):
        x, z = lerp(u)
        return P(KB, x=x, z=z, y=hp["yp"], yaw=yaw, pitch=-4 * roll_k, roll=hp["roll"] * roll_k,
                 cyaw=hp["cyaw"] * cy_k, croll=hp["croll"] * roll_k, lf=planted(sx, sz, sup_yaw, heel=heel),
                 rh=rh, re=re, **RK_GUARD)

    sp = lambda u: 15 + (sup - 15) * u  # noqa: E731  destek ayağının topunda dönüşü
    x1, z1 = lerp(0.25)
    stp = P(KB, x=x1, z=z1, yaw=18, pitch=2, lf=planted(sx, sz, -35), rf=planted(-24, 13, KB_RF_YAW, heel=40),
            lh=(22, 45, -8))
    hit_base = body(1.0, -82, sup, 25, (-26, -16, 34), (-1, -0.2, 0.5), 1.0, 1.0)
    eh, hit = rk_aim(hit_base, 8, hp["bend"], hp["y"])
    e0 = -58 + 16 * k
    arc = lambda a: e0 + (eh - e0) * ((110 - a) / 102.0) ** 0.8  # noqa: E731  yay boyunca yükseliş
    sw1 = rk_leg(body(0.55, -15, sp(0.6), 16, (28, 12, 22), (-0.3, -1, 0.6), 0.2, 0.3), 110, e0, 12, up=0.6,
                 hook=35)
    sw2 = rk_leg(body(0.75, -38, sp(0.73), 20, (16, -4, 30), (-0.6, -0.6, 0.6), 0.45, 0.6), 78, arc(78), 8, up=0.5)
    sw3 = rk_leg(body(0.92, -62, sp(0.88), 23, (-6, -14, 34), (-1, -0.3, 0.6), 0.75, 0.85), 44, arc(44), 10)
    if follow:
        hold = rk_aim(P(hit_base, yaw=-86, roll=hp["roll"] - 2), 2, hp["bend"], hp["y"] - 3)[1]
    else:
        hold = rk_aim(P(hit_base, yaw=-79), 14, hp["bend"] + 4, hp["y"])[1]
    ret1 = rk_leg(body(0.9, -58, sp(0.85), 22, (-2, -10, 32), (-1, -0.3, 0.6), 0.7, 0.8), 46, arc(46) - 4, 14)
    ret2 = rk_leg(body(0.7, -30, sp(0.66), 18, (26, 2, 24), (-0.5, -1, 0.6), 0.35, 0.5), 88, arc(88) - 6, 18,
                  up=0.6)
    x5, z5 = lerp(0.3)
    land = P(KB, x=x5, z=z5, yaw=22, pitch=2, lf=planted(sx, sz, -30), rf=planted(-18, 15, KB_RF_YAW + 4, heel=38))
    return [(t - 12, stp), (t - 8, sw1), (t - 5, sw2), (t - 2, sw3), (t, hit), (t + 4, hold), (t + 8, ret1),
            (t + 12, ret2), (t + 16, land)]


CLINCH = P(KB, x=7, y=94, lf=planted(31, -7, KB_LF_YAW), lhw=(52, 150, -8), rhw=(52, 150, 12), lhk=1, rhk=1,
           le=(-0.2, -1, -0.9), re=(-0.2, -1, 0.9))
# Düz diz: kalça öne itilir, gövde hafif geride, destek ayağının ucunda yükselir; eller boyun tutar gibi
# aşağı-içe çeker; diz göbek hizasına (uyluk yatayın üstünde) sürülür.
KNEE = kick_leg(P(CLINCH, x=20, y=100, yaw=10, pitch=-12, cpitch=10, chin=14, lhw=(56.5, 124, -4.7),
                  rhw=(56.5, 124, 15.3), le=(-0.2, -1, -0.5), re=(-0.2, -1, 0.5),
                  lf=planted(34, -7, 10, heel=32)), "r", -12, 30, 128, (-0.5, 0.85, 0), hook=-10)
# Check: ön diz yukarı ve hafif dışa, kaval tekmeye dönük, ayak ucu aşağıda; sol dirsek dize iner.
CHECK = kick_leg(P(KB, x=-4, y=94, yaw=28, pitch=8, cpitch=14, roll=3, croll=-10, chin=14,
                   rf=planted(-26, 13, KB_RF_YAW, heel=12), lh=(13, 40, -15), le=(0.4, -0.8, -0.45)),
                 "l", -24, 8, 100, (0, 1, 0), hook=0)
CHECK = P(CHECK, lf=dict(CHECK["lf"], yaw=-25, pitch=62))


def _check_shin():
    """Partnerin yuvarlak alçak tekmesi (kendi çerçevesinde, aynasız) için kaval vuruş noktası:
    öğrencinin kaldırdığı kavalın dış yüzü, diz altı."""
    knee, ank = _skl.solve_point(CHECK, "lknee"), _skl.solve_point(CHECK, "lankle")
    c = _vlin((knee, 0.7), (ank, 0.3))
    return KB_CHECK_DIST - c[0], c[1], -(c[2] - 12.0)


KB_CHECK_DIST = 136.0


def kb_feet(lx, rx, x):
    return P(KB, x=x, lf=planted(lx, -7, KB_LF_YAW), rf=planted(rx, 13, KB_RF_YAW, heel=15))


KICKBOXING = {
    "kb_stance": Move("kickboxing", 60, [(0, KB), (15, KB_DIP), (30, KB), (45, KB_DIP)], cam=dict(az=28)),
    "kb_footwork": Move("kickboxing", 64, [
        (0, kb_feet(12, -36, -12)), (10, kb_feet(28, -36, -4)), (20, kb_feet(28, -20, 4)),
        (32, P(kb_feet(28, -20, 4), yaw=60, lf=planted(28, -7, 50))), (44, kb_feet(28, -36, -4)),
        (54, kb_feet(12, -36, -12))], cam=dict(az=14)),
    "kb_jab_cross": Move("kickboxing", 48, [(0, KB), (7, KB_JAB), (12, P(KB, yaw=26)), (19, KB_CROSS),
                                            (24, KB_CROSS), (36, KB)], cam=dict(az=16), target="long_bag",
                         hits=[(7, "lhand"), (19, "rhand")]),
    "kb_teep": Move("kickboxing", 46, [(0, KB), (10, TEEP_CH), (17, TEEP), (22, TEEP), (29, TEEP_CH), (38, KB)],
                    cam=dict(az=10), target="long_bag", hits=[(17, "lball")]),
    "kb_low_kick": Move("kickboxing", 48, [(0, KB), *rk_seq(18, "low"), (40, KB)], cam=dict(az=-18, el=24),
                        target="long_bag", hits=[(18, "rshin")]),
    "kb_middle_kick": Move("kickboxing", 50, [(0, KB), *rk_seq(19, "mid"), (42, KB)], cam=dict(az=-18, el=24),
                           target="long_bag", hits=[(19, "rshin")]),
    "kb_high_kick": Move("kickboxing", 52, [(0, KB), *rk_seq(20, "high"), (44, KB)], cam=dict(az=-18, el=24),
                         target="long_bag", hits=[(20, "rshin")]),
    "kb_knee": Move("kickboxing", 42, [(0, KB), (6, CLINCH), (12, KNEE), (18, KNEE), (28, CLINCH), (36, KB)],
                    cam=dict(az=12), target="long_bag", hits=[(12, "rknee")]),
    "kb_check": Move("kickboxing", 42, [(0, KB), (10, CHECK), (22, CHECK), (32, KB)], cam=dict(az=170, el=14),
                     target="partner", opp_dist=KB_CHECK_DIST, opp_mirror=False,
                     opp=[(0, KB), *rk_seq(16, "low", step=(40, -24), shin=_check_shin(), bend=30, sup=-140,
                                           follow=False), (38, KB)], poster=17),
    "kb_combo_jcl": Move("kickboxing", 66, [(0, KB), (7, KB_JAB), (12, P(KB, yaw=26)), (19, KB_CROSS),
                                            *rk_seq(35, "low", step=(40, -24), bag=(102.5, 2.0), bend=30, sup=-140,
                                                    x0=(4, 2)), (56, KB)], cam=dict(az=-10, el=22), target="long_bag",
                         hits=[(7, "lhand"), (19, "rhand"), (35, "rshin")]),
    "kb_combo_jcm": Move("kickboxing", 82, [(0, KB), (7, KB_JAB), (12, P(KB, yaw=26)), (19, KB_CROSS),
                                            (25, KB_LHOOK_PREP), (31, KB_LHOOK),
                                            *rk_seq(48, "mid", step=(40, -24), bag=JCM_BAG, bend=26, x0=(10, -6)),
                                            (70, KB)], cam=dict(az=26, el=28), target="long_bag",
                         hits=[(7, "lhand"), (19, "rhand"), (31, "lhand"), (48, "rshin")]),
    "kb_shadow": Move("kickboxing", 120, [
        (0, KB), (7, KB_JAB), (13, KB), (20, KB_CROSS), (28, KB), (36, TEEP_CH), (42, TEEP), (48, TEEP_CH),
        (56, KB), (62, CLINCH), (68, KNEE), (74, CLINCH), (80, KB), *rk_seq(97, "mid")],
        cam=dict(az=18)),
}

# ==========================================================================
# GÜREŞ
# ==========================================================================
import skeleton as _wsk  # noqa: E402  (güreş yardımcıları: kalçanın otomatik inişini de hesaba katan çözüm)


def wr_solve(pose):
    return _wsk.Skeleton(_wsk.normalize_key(pose, _wsk._ORIGIN_BASE), _wsk._ORIGIN_BASE, None)


def wr_hands(pose, lw=None, rw=None):
    """Elleri taban çerçevesindeki noktalara koy ama göğüs çerçevesinde sakla (gövde kayınca eller de kayar)."""
    sk = wr_solve(pose)
    out = dict(pose)
    f, u, r = sk.chest
    for s, w in (("l", lw), ("r", rw)):
        if w is not None:
            v = (w[0] - sk.c0[0], w[1] - sk.c0[1], w[2] - sk.c0[2])
            out[s + "h"] = tuple(v[0] * a[0] + v[1] * a[1] + v[2] * a[2] for a in (f, u, r))
            out[s + "hk"] = 0.0
            out.pop(s + "hw", None)
    return out


def ow(px, w):
    """Sahne noktası -> partnerin yazım çerçevesi (partner px'te, bize dönük ve aynalı: x -> px - x)."""
    return (px - w[0], w[1], w[2])


def wr_pt(pose, name, px=None):
    """Pozdaki bir eklemin sahne konumu (px verilirse partner pozu olarak)."""
    sk = wr_solve(pose)
    p = sk.point(name) if name in ("head", "chest", "pelvis") else sk.j[name]
    return p if px is None else (px - p[0], p[1], p[2])


def knee_down(x, z, side_sign):
    """Dizi mindere inmiş bacak: bilek arkada, parmak uçları minderde."""
    return air((x, 15, z), yaw=0, pitch=65, knee=(0.6, -1, 0.08 * side_sign))


def wr_world_hands(pose, lw, rw, le=None, re=None):
    d = dict(lhw=lw, rhw=rw, lhk=1, rhk=1)
    if le:
        d["le"] = le
    if re:
        d["re"] = re
    return P(pose, **d)


def wr_pole(pose, d):
    """Dünya yönündeki dirsek ipucunu pozun göğüs çerçevesine çevir."""
    f, u, r = wr_solve(pose).chest
    return tuple(d[0] * a[0] + d[1] * a[1] + d[2] * a[2] for a in (f, u, r))

def wr_head_back(pose, out=11.0, up=3.0):
    """Öğrenci başının arkası/üstü (partner eli için)."""
    sk = wr_solve(pose)
    f, u, r = sk.chest
    return tuple(sk.head_c[i] - f[i] * out + u[i] * up for i in range(3))

def wr_back(pose, side, out=15.0, inward=6.0, up=2.0):
    """Öğrenci pozunda kürek kemiği üstünde (sırt yüzeyinde) bir nokta."""
    sk = wr_solve(pose)
    f, u, r = sk.chest
    sh = sk.j[side + "shoulder"]
    sg = -1.0 if side == "l" else 1.0
    return tuple(sh[i] - f[i] * out + u[i] * up - r[i] * sg * inward for i in range(3))

def wr_off(p, dx=0.0, dy=0.0, dz=0.0):
    return (p[0] + dx, p[1] + dy, p[2] + dz)

def wr_nape(pose, px=None, out=10.0):
    """Ense (boynun arkası) – collar tie eli için."""
    sk = wr_solve(pose)
    f = sk.chest[0]
    p = tuple((sk.neck_base[i] + sk.neck_top[i]) / 2 - f[i] * out for i in range(3))
    return p if px is None else (px - p[0], p[1], p[2])

def wr_triceps(pose, side, px=None, out=10.0):
    """Dirseğin hemen üstü, kolun arkası (triseps tutuşu)."""
    sk = wr_solve(pose)
    sh, el = sk.j[side + "shoulder"], sk.j[side + "elbow"]
    p = tuple(el[i] + (sh[i] - el[i]) * 0.25 - sk.chest[0][i] * out for i in range(3))
    return p if px is None else (px - p[0], p[1], p[2])


# -- nötr duruş: gövde ~40° önde, eller göğsün ~25 cm önünde, dirsekler kaburgalara yakın
WR = wr_hands(P(BASE_POSE, y=72, yaw=22, pitch=30, cpitch=10, chin=2,
                lf=planted(26, -15, 12), rf=planted(-26, 20, 30),
                le=(-0.3, -1, -0.15), re=(-0.3, -1, 0.15)), lw=(54, 82, -2), rw=(46, 80, 24))
WR_STEP = wr_hands(P(WR, x=4, lf=planted(32, -15, 12)), lw=(62, 86, -2), rw=(50, 82, 24))
WR_LOOK = (320.0, 112.0, 20.0)   # partnersiz hareketlerde bakış: karşıdaki hayali rakibin göğsü
WR_LEVEL = P(WR, y=56, pitch=32, cpitch=8)
# partnerin nötr duruşu (biraz daha dik; eller öğrencininkilerle çakışmasın diye biraz alçak)
WR_OPP = wr_hands(P(WR, y=76, pitch=26), lw=(50, 78, -4), rw=(44, 76, 22))


# --------------------------------------------------------------------------
# Çift dal (double leg): partner 140 cm'de
# --------------------------------------------------------------------------
DL_PX = 140
DL_STEP = wr_world_hands(P(WR, x=50, y=54, z=6, yaw=28, pitch=36, cpitch=8, autoy=0,
                           lf=planted(64, -4, 10), rf=planted(-22, 24, 30, heel=55)),
                         (104, 60, -8), (100, 58, 34), le=(-0.4, -0.6, -1), re=(-0.4, -0.6, 1))
# temas: ön diz minderde, baş partnerin kalçasının dışında, omuz karın hizasında, eller dizlerin arkasında
_DL_SHOT = P(WR, x=94, y=52, z=10, yaw=30, roll=4, pitch=36, cpitch=8, autoy=0,
             lf=planted(60, -2, 10, heel=70), rf=planted(10, 26, 30, heel=65),
             lhw=(142, 50, -24), rhw=(152, 46, 28), lhk=1, rhk=1)
DL_SHOT = P(_DL_SHOT, le=wr_pole(_DL_SHOT, (-0.4, -0.3, -1)), re=wr_pole(_DL_SHOT, (-0.3, -0.4, 1)))
DL_GRIP = P(DL_SHOT, x=96, lhw=(139, 50, -24), rhw=(148, 47, 29))
# arka ayak öne, yanlara basar; ön diz kalkar, kalça yükselir ve açıyla sürer
_DL_UP = P(WR, x=104, y=62, z=12, yaw=26, roll=4, pitch=40, cpitch=8, autoy=0,
           lf=planted(66, -2, 10, heel=25), rf=planted(90, 26, 30, heel=20),
           lhw=(140, 52, -22), rhw=(150, 50, 30), lhk=1, rhk=1)
DL_UP = P(_DL_UP, le=wr_pole(_DL_UP, (-0.4, -0.3, -1)), re=wr_pole(_DL_UP, (-0.3, -0.4, 1)))
_DL_DRIVE = P(WR, x=118, y=62, z=10, yaw=18, pitch=34, cpitch=6, autoy=0, chin=-8,
              lf=planted(108, -12, 0, heel=30), rf=planted(90, 14, 20, heel=40),
              lhw=(162, 50, -40), rhw=(162, 50, 42), lhk=1, rhk=1)
DL_DRIVE = P(_DL_DRIVE, le=wr_pole(_DL_DRIVE, (-0.3, -0.3, -1)), re=wr_pole(_DL_DRIVE, (-0.3, -0.3, 1)))
# bitiş: partnerin bacakları arasında dizler minderde, göğüs kalçasının üstünde, eller kalçasını bastırır
_DL_TOP = P(WR, x=136, y=49, z=0, yaw=0, pitch=58, cpitch=10, autoy=0, chin=-6,
            lf=knee_down(94, -13, -1), rf=knee_down(94, 13, 1),
            lhw=(184, 31, -22), rhw=(184, 31, 22), lhk=1, rhk=1)
DL_TOP = P(_DL_TOP, le=wr_pole(_DL_TOP, (-0.2, 0.3, -1)), re=wr_pole(_DL_TOP, (-0.2, 0.3, 1)))
DL_TOP_UP = P(DL_TOP, pitch=38, cpitch=6, lhw=(158, 74, -26), rhw=(158, 74, 26))
DL_RISE = P(WR, x=96, lf=planted(122, -15, 12), rf=planted(70, 20, 30))
DL_BACK1 = P(WR, x=70, y=66, lf=planted(122, -15, 12), rf=planted(26, 20, 30))
DL_BACK2 = P(WR, x=48, lf=planted(74, -15, 12), rf=planted(26, 20, 30))
DL_BACK3 = P(WR, x=20, y=68, lf=planted(74, -15, 12), rf=planted(-26, 20, 30))

# partner (yazım çerçevesinde; ow() sahne noktasını çevirir)
OPP_DL_REACT = P(WR_OPP, x=-3, y=86, pitch=12, cpitch=4, lf=planted(10, -15, 8), rf=planted(-20, 16, 22),
                 lhw=ow(DL_PX, (110, 102, -28)), rhw=ow(DL_PX, (106, 106, 38)), lhk=1, rhk=1)
_OPP_DL_HIT = P(WR_OPP, x=-6, y=93, pitch=4, cpitch=4, lf=planted(0, -15, 6), rf=planted(-20, 16, 20),
                lhw=ow(DL_PX, wr_back(DL_SHOT, "l")), rhw=ow(DL_PX, wr_head_back(DL_SHOT, 14)), lhk=1, rhk=1)
OPP_DL_HIT = P(_OPP_DL_HIT, le=wr_pole(_OPP_DL_HIT, (0.2, -1, -0.6)), re=wr_pole(_OPP_DL_HIT, (0, 0.3, 1)))
# dizler bükülür, kalça düşer
_OPP_DL_BUCKLE = P(WR_OPP, x=-14, y=76, pitch=-6, cpitch=0, lf=planted(2, -15, 6), rf=planted(-18, 16, 20),
                   lhw=ow(DL_PX, wr_back(DL_UP, "l")), rhw=ow(DL_PX, wr_head_back(DL_UP, 14)), lhk=1, rhk=1)
OPP_DL_BUCKLE = P(_OPP_DL_BUCKLE, le=wr_pole(_OPP_DL_BUCKLE, (0.2, -1, -0.6)),
                  re=wr_pole(_OPP_DL_BUCKLE, (0, 0.3, 1)))
# geriye düşerken: bacaklar öğrencinin kollarında (dizler kolların dışında), kollar minderi karşılamaya uzanır
OPP_DL_FALL = P(BASE_POSE, x=-46, y=49, pitch=-46, cpitch=-8, autoy=0, look=0, hpitch=-30,
                lf=air(ow(DL_PX, (150, 23, -41)), yaw=-20, pitch=50, knee=(1, 0.5, -0.6)),
                rf=air(ow(DL_PX, (150, 23, 41)), yaw=20, pitch=50, knee=(1, 0.5, 0.6)),
                lhw=ow(DL_PX, (196, 118, -54)), rhw=ow(DL_PX, (190, 122, 56)), lhk=1, rhk=1,
                le=(-0.4, -0.2, -1), re=(-0.4, -0.2, 1))
# sırt ve kalça minderde, dizler açık
OPP_DL_DOWN = P(BASE_POSE, x=-46, y=13, pitch=-84, cpitch=-4, autoy=0, look=0, hpitch=-20,
                lf=air((8, 9, -36), yaw=-30, pitch=-10, knee=(0.3, 1, -0.6)),
                rf=air((8, 9, 36), yaw=30, pitch=-10, knee=(0.3, 1, 0.6)),
                lhw=(-60, 4, -50), rhw=(-60, 4, 50), lhk=1, rhk=1, le=(0, -1, -1), re=(0, -1, 1))
# kalkış: oturur, eller arkada; teknik kalkış (bir el ve bir diz minderde); duruş; öne adım
OPP_DL_SIT = P(BASE_POSE, x=-46, y=14, pitch=-38, cpitch=8, autoy=0, look=0, hpitch=10,
               lf=planted(-4, -24, -35), rf=planted(-4, 24, 35),
               lhw=(-80, 4, -24), rhw=(-80, 4, 24), lhk=1, rhk=1, le=(-1, -0.2, -0.3), re=(-1, -0.2, 0.3))
OPP_DL_ROLL = P(BASE_POSE, x=-54, y=36, pitch=4, cpitch=6, autoy=0, look=1,
                lf=air((-58, 14, -26), yaw=-60, pitch=20, knee=(0.2, -0.2, -1)), rf=planted(-26, 20, 10),
                lhw=(-66, 4, -30), lhk=1, rh=(24, 18, 10), le=(-0.2, -1, -0.3), re=(-0.3, -1, 0.3))
OPP_DL_TECH = P(BASE_POSE, x=-60, y=50, pitch=30, cpitch=8, autoy=0, look=1,
                lf=knee_down(-108, -12, -1), rf=planted(-28, 20, 10),
                lhw=(-58, 4, -30), lhk=1, rh=(24, 18, 10), le=(-0.2, -1, -0.3), re=(-0.3, -1, 0.3))
OPP_DL_CROUCH = P(WR_OPP, x=-50, lf=planted(-24, -15, 12), rf=planted(-76, 20, 30))
OPP_DL_STEP = P(WR_OPP, x=-22, lf=planted(4, -15, 12), rf=planted(-76, 20, 30))

# --------------------------------------------------------------------------
# Tek dal (single leg): partnerin öndeki bacağı; baş kalçanın iç tarafında
# --------------------------------------------------------------------------
SL_PX = 140
SL_STEP = wr_world_hands(P(WR, x=42, y=54, z=0, yaw=14, pitch=38, cpitch=8, autoy=0,
                           lf=planted(56, -6, 10), rf=planted(-24, 22, 30, heel=55)),
                         (98, 58, -16), (96, 60, 2), le=(-0.4, -0.6, -1), re=(-0.4, -0.6, 1))
_SL_SHOT = P(WR, x=70, y=45, z=-2, yaw=8, pitch=40, cpitch=6, autoy=0,
             lf=planted(46, -2, 10, heel=70), rf=planted(-2, 22, 30, heel=65),
             lhw=(124, 46, -18), rhw=(124, 50, -3), lhk=1, rhk=1)
SL_SHOT = P(_SL_SHOT, le=wr_pole(_SL_SHOT, (-0.3, -0.4, -1)), re=wr_pole(_SL_SHOT, (-0.5, -0.6, 0.4)))
SL_GRIP = P(SL_SHOT, x=72, lhw=(122, 48, -18), rhw=(122, 52, -3))
# ayağa kalkar, bacağı göğsüne/kalçasına kaldırır; partnerin bileği dizlerinin önünde
SL_RISING = wr_world_hands(P(WR, x=74, y=62, z=-2, yaw=10, pitch=40, cpitch=6, autoy=0,
                             lf=planted(76, -30, 0, heel=30), rf=planted(22, 18, 30, heel=40)),
                           (120, 56, -20), (120, 60, -4), le=(-0.4, -0.6, -1), re=(-0.4, -0.6, 1))
_SL_LIFT = P(WR, x=84, y=84, z=-4, yaw=10, pitch=14, cpitch=4, croll=6, autoy=0, chin=4,
             lf=planted(106, -36, 0), rf=planted(54, 16, 30, heel=20),
             lhw=(116, 76, -20), rhw=(116, 80, -6), lhk=1, rhk=1)
SL_LIFT = P(_SL_LIFT, le=wr_pole(_SL_LIFT, (-0.3, -0.4, -1)), re=wr_pole(_SL_LIFT, (-0.3, -0.6, 1)))
# arka ayak geri-yana adım, ~45° dönüş; bacak yana ve aşağı çekilir
_SL_PIVOT = P(WR, x=80, y=80, z=4, yaw=48, pitch=18, cpitch=4, autoy=0, chin=4,
              lf=planted(106, -30, 30), rf=planted(40, 44, 70, heel=20),
              lhw=(116, 70, 0), rhw=(112, 76, 14), lhk=1, rhk=1)
SL_PIVOT = P(_SL_PIVOT, le=wr_pole(_SL_PIVOT, (-0.3, -0.5, -1)), re=wr_pole(_SL_PIVOT, (-0.3, -0.6, 1)))
_SL_HOLD = P(WR, x=86, y=78, z=8, yaw=40, pitch=22, cpitch=6, autoy=0, chin=0,
             lf=planted(108, -26, 30), rf=planted(48, 42, 70, heel=20),
             lhw=(124, 66, 4), rhw=(124, 72, 14), lhk=1, rhk=1)
SL_HOLD = P(_SL_HOLD, le=wr_pole(_SL_HOLD, (-0.3, -0.5, -1)), re=wr_pole(_SL_HOLD, (-0.3, -0.6, 1)))
SL_RELEASE = P(WR, x=82, lf=planted(108, -15, 12), rf=planted(56, 20, 30))
SL_BACK1 = P(WR, x=56, y=66, lf=planted(108, -15, 12), rf=planted(10, 20, 30))
SL_BACK2 = P(WR, x=34, lf=planted(60, -15, 12), rf=planted(10, 20, 30))
SL_BACK3 = P(WR, x=10, y=68, lf=planted(60, -15, 12), rf=planted(-26, 20, 30))

OPP_SL_REACT = P(WR_OPP, x=-3, y=84, pitch=14, cpitch=4, lf=planted(24, -15, 10), rf=planted(-24, 17, 26),
                 lhw=ow(SL_PX, (110, 102, -28)), rhw=ow(SL_PX, (106, 106, 36)), lhk=1, rhk=1)
_OPP_SL_HIT = P(WR_OPP, x=-4, y=86, pitch=8, cpitch=4, lf=planted(22, -15, 10), rf=planted(-24, 17, 26),
                lhw=ow(SL_PX, wr_back(SL_SHOT, "l")), rhw=ow(SL_PX, wr_back(SL_SHOT, "r")), lhk=1, rhk=1)
OPP_SL_HIT = P(_OPP_SL_HIT, le=wr_pole(_OPP_SL_HIT, (0.2, -1, -0.6)), re=wr_pole(_OPP_SL_HIT, (0.2, -1, 0.6)))
_OPP_SL_UP = P(OPP_SL_HIT, x=-10, y=90, pitch=-6, cpitch=-2,
               lhw=ow(SL_PX, wr_back(SL_RISING, "l")), rhw=ow(SL_PX, wr_back(SL_RISING, "r", out=6, inward=0, up=10)))
OPP_SL_UP = P(_OPP_SL_UP, le=wr_pole(_OPP_SL_UP, (0.2, -1, -0.6)), re=wr_pole(_OPP_SL_UP, (0, 0.3, 1)))
# bacağı havada, arka ayağında sekiyor
_OPP_SL_LIFTED = P(WR_OPP, x=-16, y=90, pitch=-8, cpitch=-4, chin=4,
                   lf=air(ow(SL_PX, (108, 44, -6)), yaw=0, pitch=50, knee=(1, 0.3, 0)),
                   rf=planted(-34, 16, 26, heel=20),
                   lhw=ow(SL_PX, (118, 118, -44)), rhw=ow(SL_PX, wr_back(SL_LIFT, "r", out=6, inward=0, up=10)),
                   lhk=1, rhk=1)
OPP_SL_LIFTED = P(_OPP_SL_LIFTED, le=wr_pole(_OPP_SL_LIFTED, (0, 0, -1)), re=wr_pole(_OPP_SL_LIFTED, (0, 0.3, 1)))
OPP_SL_HOP = P(BASE_POSE, x=-24, y=84, pitch=-20, cpitch=-6, autoy=0, chin=6,
               lf=air(ow(SL_PX, (110, 52, 6)), yaw=-30, pitch=40, knee=(1, 0.5, 0.3)),
               rf=air((-34, 16, 22), yaw=10, pitch=30, knee=(1, 0.3, 0.1)),
               lhw=ow(SL_PX, (150, 120, -56)), rhw=ow(SL_PX, (176, 126, 52)), lhk=1, rhk=1,
               le=(-0.3, 0, -1), re=(-0.3, 0, 1))
# sırtüstü düştü; öndeki bacağı hâlâ öğrencinin elinde
OPP_SL_DOWN = P(BASE_POSE, x=-44, y=13, z=-6, pitch=-84, cpitch=-4, autoy=0, look=0, hpitch=-20,
                lf=air(ow(SL_PX, (126, 62, 8)), yaw=-20, pitch=30, knee=(0.6, 1, 0)),
                rf=planted(-6, 22, 20),
                lhw=(-60, 4, -50), rhw=(-60, 4, 50), lhk=1, rhk=1, le=(0, -1, -1), re=(0, -1, 1))

# --------------------------------------------------------------------------
# Sprawl: partner alçaktan dalar; öğrenci bacaklarını geri atıp kalçasını partnerin başına/omzuna,
# göğsünü sırtına bırakır
# --------------------------------------------------------------------------
SP_PX = 150
_SPRAWL = P(BASE_POSE, x=14, y=52, z=-8, pitch=74, cpitch=4, autoy=0, look=0, hpitch=-30,
            lf=planted(-68, -36, -10, heel=75), rf=planted(-68, 28, 10, heel=75),
            lhw=(28, 42, -16), rhw=(16, 52, 26), lhk=1, rhk=1)
WR_SPRAWL = P(_SPRAWL, le=wr_pole(_SPRAWL, (0.3, 0.3, -1)), re=wr_pole(_SPRAWL, (0, 0.5, 1)))
WR_SPRAWL_HOLD = P(WR_SPRAWL, y=51, x=12)
_SPRAWL_HALF = P(WR, x=4, y=58, z=-6, yaw=4, pitch=52, cpitch=6, autoy=0,
                 lf=planted(-16, -26, 0, heel=50), rf=planted(-48, 26, 10, heel=60),
                 lhw=(38, 66, -10), rhw=(30, 78, 22), lhk=1, rhk=1)
WR_SPRAWL_HALF = P(_SPRAWL_HALF, le=wr_pole(_SPRAWL_HALF, (0, -0.3, -1)), re=wr_pole(_SPRAWL_HALF, (0, -0.3, 1)))
# kalça kalkar, ayaklar altına gelir (kollar önde, partneri iter)
_SPRAWL_UP = P(WR, x=-14, y=64, pitch=40, cpitch=6, autoy=0,
               lf=planted(-10, -20, 0, heel=30), rf=planted(-46, 24, 20, heel=40),
               lhw=(46, 50, -16), rhw=(40, 56, 24), lhk=1, rhk=1)
WR_SPRAWL_UP = P(_SPRAWL_UP, le=wr_pole(_SPRAWL_UP, (0, -0.3, -1)), re=wr_pole(_SPRAWL_UP, (0, -0.3, 1)))

OPP_SP_LEVEL = P(WR_OPP, x=6, y=56, pitch=40, cpitch=8, lf=planted(40, -15, 12), rf=planted(-26, 20, 30))
OPP_SP_DIVE = wr_world_hands(P(WR_OPP, x=SP_PX - 104, y=46, z=10, yaw=18, pitch=62, cpitch=8, autoy=0, chin=-14,
                               lf=planted(SP_PX - 92, -13, 10, heel=20), rf=planted(SP_PX - 170, 20, 24, heel=55)),
                             ow(SP_PX, (34, 40, -24)), ow(SP_PX, (32, 42, 32)), le=(0, -0.5, -1), re=(0, -0.5, 1))
# dalış: baş öğrencinin kalçasına (kameraya yakın taraf), kollar dizlere uzanır
_OPP_SP_SHOT = P(WR_OPP, x=SP_PX - 74, y=44, z=6, yaw=18, pitch=72, cpitch=8, autoy=0, chin=-16,
                 lf=planted(SP_PX - 100, -12, 10, heel=50), rf=planted(SP_PX - 156, 20, 20, heel=65),
                 lhw=ow(SP_PX, (14, 22, -30)), rhw=ow(SP_PX, (12, 24, 38)), lhk=1, rhk=1)
OPP_SP_SHOT = P(_OPP_SP_SHOT, le=wr_pole(_OPP_SP_SHOT, (0, -0.4, -1)), re=wr_pole(_OPP_SP_SHOT, (0, -0.4, 1)))
# ezildi: dizler minderde, göğüs yere yakın, baş öğrencinin kalçasının yanında
_OPP_SP_FLAT = P(BASE_POSE, x=SP_PX - 82, y=47, yaw=20, pitch=98, cpitch=6, autoy=0, look=0, hpitch=-40, chin=-10,
                 lf=knee_down(32, -14, -1), rf=knee_down(28, 16, 1),
                 lhw=ow(SP_PX, (-16, 6, -34)), rhw=ow(SP_PX, (-12, 6, 44)), lhk=1, rhk=1)
OPP_SP_FLAT = P(_OPP_SP_FLAT, le=wr_pole(_OPP_SP_FLAT, (0, 0.3, -1)), re=wr_pole(_OPP_SP_FLAT, (0, 0.3, 1)))
OPP_SP_FLAT2 = P(OPP_SP_FLAT, y=46, pitch=100)
# dizlerinin üstünde doğrulur, sonra geri çekilip ayağa kalkar
OPP_SP_BACK = P(OPP_SP_FLAT, x=SP_PX - 100, y=48, pitch=92, yaw=10, lf=knee_down(14, -14, -1),
                rf=knee_down(10, 16, 1), lhw=ow(SP_PX, (40, 5, -30)), rhw=ow(SP_PX, (44, 5, 36)))
OPP_SP_KNEES = P(BASE_POSE, x=SP_PX - 120, y=54, pitch=30, cpitch=6, autoy=0,
                 lf=knee_down(-8, -14, -1), rf=planted(SP_PX - 132, 18, 10),
                 lh=(30, 10, -16), rh=(30, 10, 16), le=(-0.3, -1, -0.3), re=(-0.3, -1, 0.3))


# --------------------------------------------------------------------------
# El mücadelesi (hand fight): bilek kontrolü, ense bağlantısı (collar tie), dirsek kontrolü;
# partner karşılık verir
# --------------------------------------------------------------------------
HF_PX = 124


# 1) öğrencinin sol eli partnerin sağ bileğini tutup aşağı-dışa çeker;
#    partnerin sol eli öğrencinin sağ bileğine uzanır
_OPP_HF_WRIST = P(WR_OPP, x=-2, lhw=ow(HF_PX, (60, 70, -22)), rhw=ow(HF_PX, (56, 88, 28)), lhk=1, rhk=1)
OPP_HF_WRIST = P(_OPP_HF_WRIST, le=wr_pole(_OPP_HF_WRIST, (-0.3, -1, -0.4)), re=wr_pole(_OPP_HF_WRIST, (-0.3, -1, 0.4)))
_HF_WRIST = P(WR, yaw=16, cyaw=-4, lhw=wr_off(wr_pt(OPP_HF_WRIST, "lwrist", HF_PX), -2, 4, 0),
              rhw=(44, 84, 26), lhk=1, rhk=1)
HF_WRIST = P(_HF_WRIST, le=wr_pole(_HF_WRIST, (-0.4, -1, -0.3)), re=wr_pole(_HF_WRIST, (-0.4, -1, 0.3)))
# 2) sağ el ensede (collar tie), başı aşağı çeker; sol el bileği tutmaya devam eder; partner sol eliyle pazıyı iter
_OPP_HF_TIED = P(WR_OPP, x=4, y=72, yaw=-6, pitch=50, cpitch=10, look=0, hpitch=6, chin=0,
                 lhw=ow(HF_PX, (56, 64, -24)), lhk=1)
_HF_TIE = P(WR, x=6, y=78, yaw=18, pitch=14, cpitch=6, chin=4,
            lhw=wr_off(wr_pt(_OPP_HF_TIED, "lwrist", HF_PX), -2, 4, 0),
            rhw=wr_off(wr_nape(_OPP_HF_TIED, HF_PX), 0, 0, 6), lhk=1, rhk=1)
HF_TIE = P(_HF_TIE, le=wr_pole(_HF_TIE, (-0.4, -1, -0.3)), re=wr_pole(_HF_TIE, (0, -0.3, 1)))
_OPP_HF_TIED = P(_OPP_HF_TIED, rhw=ow(HF_PX, wr_off(wr_pt(HF_TIE, "relbow"), -4, -4, 6)), rhk=1)
OPP_HF_TIED = P(_OPP_HF_TIED, le=wr_pole(_OPP_HF_TIED, (-0.3, -1, -0.4)), re=wr_pole(_OPP_HF_TIED, (0, -1, 0.6)))
# başı biraz daha aşağı çeker
_OPP_HF_TIED2 = P(OPP_HF_TIED, y=70, pitch=54, x=10)
_HF_TIE2 = P(HF_TIE, x=4, pitch=16, lhw=wr_off(wr_pt(_OPP_HF_TIED2, "lwrist", HF_PX), -2, 4, 0),
             rhw=wr_off(wr_nape(_OPP_HF_TIED2, HF_PX), 0, 0, 6))
HF_TIE2 = P(_HF_TIE2, le=wr_pole(_HF_TIE2, (-0.4, -1, -0.3)), re=wr_pole(_HF_TIE2, (0, -0.3, 1)))
_OPP_HF_TIED2 = P(_OPP_HF_TIED2, rhw=ow(HF_PX, wr_off(wr_pt(HF_TIE2, "relbow"), -4, -4, 6)))
OPP_HF_TIED2 = P(_OPP_HF_TIED2, le=wr_pole(_OPP_HF_TIED2, (-0.3, -1, -0.4)), re=wr_pole(_OPP_HF_TIED2, (0, -1, 0.6)))
# ense bağlantısı bırakılırken partner başını geri-aşağıdan çeker; el omzuna/kola kayar
OPP_HF_OUT = P(OPP_HF_TIED2, x=-2, y=74, pitch=40, yaw=0, look=1, hpitch=0, chin=2,
               lhw=ow(HF_PX, (58, 72, -22)), rhw=ow(HF_PX, (60, 92, 30)))
_HF_SLIDE = P(HF_TIE2, x=2, pitch=24, rhw=wr_off(wr_pt(OPP_HF_OUT, "relbow", HF_PX), 0, 8, 7),
              lhw=wr_off(wr_pt(OPP_HF_OUT, "lwrist", HF_PX), -2, 4, 0))
HF_SLIDE = P(_HF_SLIDE, re=wr_pole(_HF_SLIDE, (-0.3, -1, 0.5)))
# 3) partner doğrulur; öğrencinin sağ eli enseden dirseğe kayar ve dirseği yukarı-içeri iter
OPP_HF_ELB = wr_hands(P(WR_OPP, x=2, y=76, yaw=14, pitch=30, cpitch=8), lw=(60, 84, -8), rw=(62, 92, 18))
_HF_ELB = P(WR, x=4, yaw=18, pitch=26, rhw=wr_off(wr_pt(OPP_HF_ELB, "relbow", HF_PX), -4, -5, 4), rhk=1)
HF_ELB = P(_HF_ELB, re=wr_pole(_HF_ELB, (-0.3, -1, 0.5)))
# 4) partner karşılık verir: sol eliyle öğrencinin sağ bileğini yakalar; öğrenci elini içeri çevirip kurtarır
HF_CLEAR = wr_hands(P(WR, x=0, yaw=24), lw=(58, 90, 2), rw=(50, 76, 18))
_OPP_HF_GRAB = P(WR_OPP, x=0, rhw=ow(HF_PX, wr_off(wr_pt(HF_CLEAR, "rwrist"), 3, 4, 2)), rhk=1)
OPP_HF_GRAB = P(_OPP_HF_GRAB, re=wr_pole(_OPP_HF_GRAB, (-0.3, -1, 0.4)))

# --------------------------------------------------------------------------
# Snap down: ense + triseps; baş öğrencinin yanında mindere çekilir, arka ayak geri adım
# --------------------------------------------------------------------------
SN_PX = 124


_OPP_SN_TIED = P(WR_OPP, x=4, y=72, yaw=-6, pitch=50, cpitch=10, look=0, hpitch=6, chin=0)
_SN_REACH = P(WR, x=4, y=78, yaw=18, pitch=15, cpitch=6, chin=4,
              rhw=wr_off(wr_nape(_OPP_SN_TIED, SN_PX), 0, 0, 6), lhw=wr_triceps(_OPP_SN_TIED, "l", SN_PX), lhk=1, rhk=1)
SN_REACH = P(_SN_REACH, le=wr_pole(_SN_REACH, (-0.3, -1, -0.5)), re=wr_pole(_SN_REACH, (0, -0.3, 1)))
_OPP_SN_TIED = P(_OPP_SN_TIED, rhw=ow(SN_PX, wr_off(wr_pt(SN_REACH, "relbow"), -4, -4, 6)), rhk=1)
OPP_SN_TIED = P(_OPP_SN_TIED, re=wr_pole(_OPP_SN_TIED, (0, -1, 0.6)))
# çekiş: partnerin başı öğrencinin ön ayağının önünde mindere iner, elleri mindere dayanır
_OPP_SN_DOWN = P(BASE_POSE, x=SN_PX - 120, y=74, z=8, yaw=8, pitch=96, cpitch=14, autoy=0, look=0, hpitch=-10,
                 lf=planted(SN_PX - 104, -14, 0, heel=20), rf=planted(SN_PX - 154, 18, 20, heel=40),
                 lhw=ow(SN_PX, (58, 4, -14)), rhw=ow(SN_PX, (54, 4, 44)), lhk=1, rhk=1)
OPP_SN_DOWN = P(_OPP_SN_DOWN, le=wr_pole(_OPP_SN_DOWN, (-0.3, -0.2, -1)), re=wr_pole(_OPP_SN_DOWN, (-0.3, -0.2, 1)))
_SN_SNAP = P(WR, x=-4, y=66, z=-2, yaw=18, pitch=38, cpitch=8, autoy=0,
             lf=planted(22, -15, 12), rf=planted(-60, 20, 30, heel=20),
             rhw=wr_off(wr_nape(OPP_SN_DOWN, SN_PX), 0, 2, 4), lhw=wr_triceps(OPP_SN_DOWN, "l", SN_PX), lhk=1, rhk=1)
SN_SNAP = P(_SN_SNAP, le=wr_pole(_SN_SNAP, (-0.3, -1, -0.5)), re=wr_pole(_SN_SNAP, (-0.2, -0.3, 1)))
# bırakış: eller gardına döner, partner başını geri çekip doğrulur
OPP_SN_OUT = P(OPP_SN_DOWN, x=SN_PX - 140, y=72, pitch=84, lf=planted(SN_PX - 116, -14, 0, heel=20),
               rf=planted(SN_PX - 166, 18, 20, heel=40), lhw=ow(SN_PX, (74, 14, -16)), rhw=ow(SN_PX, (72, 16, 40)))
SN_RELEASE = P(WR, x=-8, y=68, pitch=34, lf=planted(20, -15, 12), rf=planted(-58, 20, 30, heel=20))
OPP_SN_UP = P(WR_OPP, x=-10, y=72, pitch=34, cpitch=10, lf=planted(12, -15, 12), rf=planted(-40, 20, 30))
SN_BACK = P(WR, x=-10, lf=planted(16, -15, 12), rf=planted(-44, 20, 30))

# --------------------------------------------------------------------------
# Penetrasyon adımı: ön ayak ~60 cm öne, ön diz mindere, kalça ileri; sonra arka bacak gelir
# --------------------------------------------------------------------------
PEN_PX = 172
WR_OPP_SQUARE = P(WR_OPP, x=-22, y=86, pitch=10, cpitch=4, lf=planted(-10, -20, 8), rf=planted(-24, 20, 16))
PEN_STEP = wr_world_hands(P(WR, x=58, y=56, z=6, yaw=26, pitch=36, cpitch=8, autoy=0,
                            lf=planted(86, -6, 10), rf=planted(-22, 24, 30, heel=55)),
                          (110, 62, -10), (104, 60, 32), le=(-0.4, -0.6, -1), re=(-0.4, -0.6, 1))
_PEN_KNEE = P(WR, x=124, y=50, z=10, yaw=30, roll=4, pitch=34, cpitch=8, autoy=0,
              lf=planted(86, -6, 10, heel=72), rf=planted(40, 26, 30, heel=65),
              lhw=(144, 40, -28), rhw=(158, 42, 38), lhk=1, rhk=1)
WR_PEN = P(_PEN_KNEE, le=wr_pole(_PEN_KNEE, (-0.3, -0.5, -1)), re=wr_pole(_PEN_KNEE, (-0.3, -0.5, 1)))
WR_PEN_DRIVE = P(WR_PEN, x=127, rf=planted(46, 26, 30, heel=65))
# arka bacak öne gelir, ön diz kalkar
_PEN_TRAIL = P(WR, x=116, y=60, z=10, yaw=26, roll=2, pitch=36, cpitch=8, autoy=0,
               lf=planted(90, -6, 10, heel=40), rf=planted(80, 32, 30, heel=20),
               lhw=(138, 52, -24), rhw=(146, 54, 36), lhk=1, rhk=1)
WR_PEN_TRAIL = P(_PEN_TRAIL, le=wr_pole(_PEN_TRAIL, (-0.3, -0.5, -1)), re=wr_pole(_PEN_TRAIL, (-0.3, -0.5, 1)))
PEN_UP = P(WR, x=82, lf=planted(106, -15, 12), rf=planted(62, 20, 30))
PEN_B1 = P(WR, x=60, y=66, lf=planted(106, -15, 12), rf=planted(18, 20, 30))
PEN_B2 = P(WR, x=38, lf=planted(64, -15, 12), rf=planted(18, 20, 30))
PEN_B3 = P(WR, x=14, y=66, lf=planted(64, -15, 12), rf=planted(-26, 20, 30))

# --------------------------------------------------------------------------
# Yer: dört ayak (referee pozisyonu altı), sit-out, stand-up
# --------------------------------------------------------------------------
QUAD = P(BASE_POSE, y=54, pitch=86, cpitch=0, look=0, hpitch=-40, autoy=0,
         lhw=(46, 4, -16), rhw=(46, 4, 16), lhk=1, rhk=1, le=(-0.2, -1, -0.3), re=(-0.2, -1, 0.3),
         lf=air((-40, 7, -13), yaw=180, pitch=0, knee=(0, -1, 0)),
         rf=air((-40, 7, 13), yaw=180, pitch=0, knee=(0, -1, 0)))
# sağ ayak sağ elin dışına basar (dizi yukarıda), eller minderde
SO_STEP = P(QUAD, x=-2, y=56, pitch=72, rf=planted(-4, 36, 20))
# sol ele yüklenir, sağ el kalkar; sol bacak gövdenin altına çekilir, kalça dönmeye başlar
SO_POST = P(BASE_POSE, x=-2, y=46, z=0, yaw=26, pitch=34, cpitch=6, autoy=0, look=0, hpitch=-16,
            lf=air((6, 11, -2), yaw=40, pitch=10, knee=(0.3, -1, 0.4)), rf=planted(-4, 36, 20),
            lhw=(40, 4, -16), lhk=1, rh=(26, 6, 16), le=(-0.2, -1, -0.5), re=(-0.4, -1, 0.3))
# sol bacak sağ dizin altından kameraya doğru fırlar, kalça düşer ve döner
SO_KICK = P(BASE_POSE, x=-2, y=26, z=2, yaw=66, pitch=8, cpitch=8, autoy=0, look=0, hpitch=-4,
            lf=air((26, 10, 64), yaw=80, pitch=-20, knee=(0.7, 0.1, 0.7)), rf=planted(-6, 42, 50),
            lhw=(30, 4, -24), lhk=1, rh=(28, 12, 14), le=(-0.4, -1, -0.5), re=(-0.3, -1, 0.3))
# oturdu: kalça ~80° döndü (kameraya dönük), sol bacak uzanmış, sağ diz yukarıda, sol el arkada minderde
_SO_SIT = P(BASE_POSE, x=-4, y=15, z=6, yaw=80, pitch=-24, cpitch=10, autoy=0, look=0, hpitch=6,
            lf=air((14, 8, 76), yaw=80, pitch=-30, knee=(0, 1, 0.2)), rf=planted(-14, 58, 85),
            lhw=(-18, 4, -22), lhk=1, le=(-1, -0.3, -0.3))
SO_SIT = P(_SO_SIT, rhw=wr_off(wr_pt(_SO_SIT, "rknee"), -2, 7, 0), rhk=1, re=wr_pole(_SO_SIT, (-1, -0.4, 0)))
SO_SIT2 = P(SO_SIT, pitch=-18)
# kalça sol el ve sağ ayak üstünde kalkar (sol bacak düz, dizi yukarıda), sonra sol diz altına girer
SO_TURN = P(BASE_POSE, x=-4, y=38, z=6, yaw=70, pitch=10, cpitch=6, autoy=0, look=0, hpitch=-6,
            lf=air((6, 9, 52), yaw=80, pitch=-20, knee=(0.2, 1, 0.3)), rf=planted(-8, 46, 60),
            lhw=(-10, 4, -24), lhk=1, rh=(26, 4, 10), rhk=0, le=(-1, -0.3, -0.3), re=(-0.4, -1, 0.5))
# kalça kalkar ve geri döner (hip heist): sol el minderde, sol diz altına girer, sonra dört ayak
SO_HEIST = P(BASE_POSE, x=-4, y=48, z=4, yaw=36, pitch=40, cpitch=6, autoy=0, look=0, hpitch=-20,
             lf=air((-30, 9, -6), yaw=200, pitch=0, knee=(0.6, -0.5, 0.2)), rf=planted(0, 40, 30),
             lhw=(36, 4, -18), rhw=(46, 4, 8), lhk=1, rhk=1, le=(-0.2, -1, -0.3), re=(-0.2, -1, 0.3))
# kalkış: sağ ayak öne basar, gövde dikleşir, eller beldeki kontrolü koparır; ayağa kalkar ve rakibe döner
SU_POST = P(SO_STEP, y=54, pitch=40, cpitch=4, hpitch=-10, lhk=0, rhk=0, lh=(20, 0, -16), rh=(22, 2, 16),
            le=(-0.4, -1, -0.4), re=(-0.4, -1, 0.4))
SU_KNEEL = P(BASE_POSE, x=-4, y=50, pitch=10, cpitch=4, autoy=0, look=0, hpitch=0,
             lf=knee_down(-44, -12, -1), rf=planted(8, 30, 15),
             lh=(14, -16, -18), rh=(16, -14, 18), le=(-0.6, -1, -0.5), re=(-0.6, -1, 0.5))
SU_RISE = P(BASE_POSE, x=-6, y=84, pitch=12, cpitch=4, look=0, hpitch=0,
            lf=planted(-36, -16, -10), rf=planted(10, 26, 15),
            lh=(16, -14, -18), rh=(18, -12, 18), le=(-0.6, -1, -0.5), re=(-0.6, -1, 0.5))
_SU_STANCE = P(WR, x=-8, lf=planted(-36, -16, -10), rf=planted(16, 24, 10), yaw=-12)
# arka (sol) ayak üzerinde dönüş: önce 90°, sonra 180° – rakibe yüz yüze
SU_TURN = turn(_SU_STANCE, 90, about=(-36, -16))
SU_FACE = turn(_SU_STANCE, 180, about=(-36, -16))
SU_FACE2 = P(SU_FACE, y=70)

# köprü: sırt, omuzlar ve başın arkası minderde; eller başın yanında minderde (destek)
BRIDGE_LIE = P(BASE_POSE, y=11, pitch=-92, look=0, hpitch=-26, autoy=0,
               lhw=(-80, 4, -20), rhw=(-80, 4, 20), lhk=1, rhk=1, le=(0.3, 1, -0.6), re=(0.3, 1, 0.6),
               lf=planted(50, -16, -8), rf=planted(50, 16, 8))
BRIDGE_UP = P(BRIDGE_LIE, x=-2, y=44, pitch=-116, hpitch=-62, lhw=(-70, 4, -20), rhw=(-70, 4, 20))

# gölge güreşi: el mücadelesi (uzan, bileği çek, ense, pummel), seviye, penetrasyon, sprawl (kalça minderde)
SH_REACH = wr_hands(P(WR, yaw=16, cyaw=-4), lw=(74, 92, -6), rw=(44, 84, 24))
SH_PULL = wr_hands(P(WR, yaw=18, cyaw=-2, y=70), lw=(52, 66, -24), rw=(70, 112, 12))
SH_TIE = wr_hands(P(WR, x=4, yaw=24, pitch=24, y=74), lw=(60, 96, -4), rw=(66, 104, 8))
SH_PUMMEL = wr_hands(P(WR, yaw=24), lw=(62, 104, 6), rw=(40, 76, 30))
SH_PEN = P(WR_PEN, x=94, lf=planted(60, -6, 10, heel=72), rf=planted(14, 26, 30, heel=65),
           lhw=(118, 40, -24), rhw=(126, 42, 30))
SH_PEN_STEP = P(PEN_STEP, x=40, lf=planted(64, -6, 10), lhw=(90, 62, -10), rhw=(84, 60, 32))
SH_PEN_TRAIL = P(WR_PEN_TRAIL, x=88, lf=planted(62, -6, 10, heel=40), rf=planted(52, 32, 30, heel=20),
                 lhw=(110, 52, -24), rhw=(118, 54, 36))
SH_UP = P(WR, x=62, lf=planted(88, -15, 12), rf=planted(36, 20, 30))
SH_BACK = P(WR, x=40, y=66, lf=planted(88, -15, 12), rf=planted(14, 20, 30))
# sprawl (partnersiz): kalça mindere iner, bacaklar geride ve açık, göğüs yukarıda, eller önde minderde
SH_SPRAWL_HALF = wr_world_hands(P(WR, x=6, y=50, z=-2, yaw=6, pitch=48, cpitch=4, autoy=0,
                                  lf=planted(-34, -28, -6, heel=55), rf=planted(-56, 28, 10, heel=65)),
                                (54, 30, -20), (52, 30, 22), le=(-0.3, -1, -0.4), re=(-0.3, -1, 0.4))
SH_SPRAWL = P(BASE_POSE, x=-12, y=17, z=-2, pitch=64, cpitch=-30, autoy=0, look=0, hpitch=-10,
              lf=planted(-104, -36, -10, heel=60), rf=planted(-104, 32, 10, heel=60),
              lhw=(42, 4, -24), rhw=(42, 4, 24), lhk=1, rhk=1, le=(-0.5, -1, -0.4), re=(-0.5, -1, 0.4))
SH_SPRAWL2 = P(SH_SPRAWL, y=18, cpitch=-34)
# kalkış: eller önde minderi iter, kalça kalkar, ayaklar altına gelir
SH_SPRAWL_UP = wr_world_hands(P(WR, x=-6, y=56, z=-2, yaw=8, pitch=52, cpitch=6, autoy=0,
                                lf=planted(-10, -22, 0, heel=30), rf=planted(-50, 24, 20, heel=45)),
                              (40, 34, -18), (40, 34, 20), le=(-0.3, -1, -0.4), re=(-0.3, -1, 0.4))

WRESTLING = {
    "wr_stance": Move("wrestling", 60, [(0, WR), (15, WR_STEP), (30, P(WR, y=70)), (45, WR_STEP)],
                      cam=dict(az=12), look=WR_LOOK),
    "wr_level_change": Move("wrestling", 40, [(0, WR), (14, WR_LEVEL), (20, WR_LEVEL), (32, WR)],
                            cam=dict(az=14), look=WR_LOOK),
    "wr_penetration": Move("wrestling", 76, [(0, WR), (9, WR_LEVEL), (17, PEN_STEP), (23, WR_PEN), (30, WR_PEN_DRIVE),
                                             (38, WR_PEN_TRAIL), (46, PEN_UP), (53, PEN_B1), (60, PEN_B2),
                                             (67, PEN_B3)],
                           cam=dict(az=16), target="partner", opp_dist=PEN_PX,
                           opp=[(0, WR_OPP_SQUARE), (38, P(WR_OPP_SQUARE, pitch=12))], trails=[("head", 9, 24)]),
    "wr_double_leg": Move("wrestling", 90, [(0, WR), (8, WR_LEVEL), (15, DL_STEP), (21, DL_SHOT), (27, DL_GRIP),
                                            (33, DL_UP), (39, DL_DRIVE), (45, DL_TOP), (53, DL_TOP), (57, DL_TOP_UP),
                                            (63, DL_RISE), (69, DL_BACK1), (76, DL_BACK2), (83, DL_BACK3)],
                          cam=dict(az=16), target="partner", opp_dist=DL_PX,
                          opp=[(0, WR_OPP), (9, WR_OPP), (15, OPP_DL_REACT), (21, OPP_DL_HIT), (27, OPP_DL_HIT),
                               (33, OPP_DL_BUCKLE), (39, OPP_DL_FALL), (45, OPP_DL_DOWN), (53, OPP_DL_DOWN),
                               (60, OPP_DL_SIT), (65, OPP_DL_ROLL), (70, OPP_DL_TECH), (76, OPP_DL_CROUCH),
                               (83, OPP_DL_STEP)],
                          trails=[("head", 8, 22)]),
    "wr_single_leg": Move("wrestling", 86, [(0, WR), (8, WR_LEVEL), (15, SL_STEP), (21, SL_SHOT), (27, SL_GRIP),
                                            (31, SL_RISING), (35, SL_LIFT), (42, SL_PIVOT), (48, SL_HOLD),
                                            (54, SL_HOLD), (60, SL_RELEASE), (66, SL_BACK1), (73, SL_BACK2),
                                            (80, SL_BACK3)],
                          cam=dict(az=18), target="partner", opp_dist=SL_PX,
                          opp=[(0, WR_OPP), (9, WR_OPP), (15, OPP_SL_REACT), (21, OPP_SL_HIT), (27, OPP_SL_HIT),
                               (31, OPP_SL_UP), (35, OPP_SL_LIFTED), (42, OPP_SL_HOP), (48, OPP_SL_DOWN),
                               (54, OPP_SL_DOWN), (59, OPP_DL_SIT), (64, OPP_DL_ROLL), (69, OPP_DL_TECH),
                               (75, OPP_DL_CROUCH), (81, OPP_DL_STEP)],
                          trails=[("head", 8, 22)]),
    "wr_sprawl": Move("wrestling", 54, [(0, WR), (4, WR), (8, WR_SPRAWL_HALF), (12, WR_SPRAWL), (24, WR_SPRAWL_HOLD),
                                        (30, P(WR_SPRAWL_HALF, x=-6)), (35, WR_SPRAWL_UP), (45, WR)],
                      cam=dict(az=18), target="partner", opp_dist=SP_PX,
                      opp=[(0, WR_OPP), (4, OPP_SP_LEVEL), (7, OPP_SP_DIVE), (9, OPP_SP_SHOT), (12, OPP_SP_FLAT),
                           (24, OPP_SP_FLAT2), (30, OPP_SP_BACK), (36, P(OPP_SP_BACK, x=SP_PX - 114, pitch=78)),
                           (42, OPP_SP_KNEES), (49, WR_OPP)]),
    "wr_bridge": Move("wrestling", 64, [(0, BRIDGE_LIE), (24, BRIDGE_UP), (38, BRIDGE_UP)], cam=dict(az=14, el=10)),
    "wr_hand_fight": Move("wrestling", 48, [(0, WR), (7, HF_WRIST), (15, HF_TIE), (22, HF_TIE2), (27, HF_SLIDE),
                                            (32, HF_ELB), (40, HF_CLEAR)],
                          cam=dict(az=16), target="partner", opp_dist=HF_PX,
                          opp=[(0, WR_OPP), (7, OPP_HF_WRIST), (15, OPP_HF_TIED), (22, OPP_HF_TIED2),
                               (27, OPP_HF_OUT), (32, OPP_HF_ELB), (40, OPP_HF_GRAB)]),
    "wr_snap_down": Move("wrestling", 48, [(0, WR), (8, SN_REACH), (15, SN_SNAP), (24, SN_SNAP), (29, SN_RELEASE),
                                           (37, SN_BACK)],
                         cam=dict(az=20), target="partner", opp_dist=SN_PX,
                         opp=[(0, WR_OPP), (8, OPP_SN_TIED), (13, OPP_SN_DOWN), (24, OPP_SN_DOWN), (30, OPP_SN_OUT),
                              (38, OPP_SN_UP)]),
    "wr_sit_out": Move("wrestling", 64, [(0, QUAD), (8, SO_STEP), (14, SO_POST), (20, SO_KICK), (26, SO_SIT),
                                         (36, SO_SIT2), (42, SO_TURN), (48, SO_HEIST), (56, QUAD)],
                       cam=dict(az=24, el=10)),
    "wr_stand_up": Move("wrestling", 76, [(0, QUAD), (9, SU_POST), (16, SU_KNEEL), (24, SU_RISE), (31, SU_TURN),
                                          (38, SU_FACE), (47, SU_FACE2), (54, SU_TURN), (61, SU_RISE), (67, SU_KNEEL),
                                          (72, SU_POST)],
                        cam=dict(az=22, el=8)),
    "wr_shadow": Move("wrestling", 120, [(0, WR), (6, SH_REACH), (11, SH_PULL), (17, SH_TIE), (23, SH_PUMMEL),
                                         (29, WR), (36, WR_LEVEL), (43, SH_PEN_STEP), (48, SH_PEN), (53, SH_PEN),
                                         (60, SH_PEN_TRAIL), (66, SH_UP), (72, SH_BACK), (78, P(WR, x=14)),
                                         (84, SH_SPRAWL_HALF), (89, SH_SPRAWL), (98, SH_SPRAWL2), (105, SH_SPRAWL_UP),
                                         (113, WR)],
                      cam=dict(az=16), look=WR_LOOK),
}

# ==========================================================================
# TEKVANDO
# ==========================================================================
from skeleton import mirror_pose as _tkd_mirror, solve_point as _tkd_solve  # noqa: E402

# Tekvandoya özel kol pozları (genel CHAMBER_* "eller belde" duruşu yerine): çekilen yumruk kuşağın
# yanında, dirsek dümdüz geride ve kaburgaya yakın.
TKD_HK_L = dict(lh=(12, -6, -19), le=(-1, -0.8, 0.2), lsup=95.0)
TKD_HK_R = dict(rh=(12, -6, 19), re=(-1, -0.8, -0.2), rsup=95.0)
# gard: yumruklar göğüs/çene önünde ~15-20 cm, dirsekler aşağıda
TKD_GUARD = dict(lh=(34, 20, -16), rh=(28, 34, 4), le=(-0.2, -1, -0.4), re=(-0.2, -1, 0.4))
TKD_G = P(BASE_POSE, y=94, yaw=52, pitch=2, cpitch=4, chin=6,
          lf=planted(24, -5, 26), rf=planted(-28, 12, 68, heel=24), **TKD_GUARD)
# partner: yüksek gard (göğüs koruyucu açık) / alçak gard (balta tekmesi için omuz açık)
TKD_OPP = P(TKD_G, lh=(30, 48, -10), rh=(26, 50, 6), le=(0.7, -1, -0.3), re=(0.7, -1, 0.3))
TKD_OPP_LOW = P(TKD_G, lh=(34, 2, -8), rh=(30, 10, 6), le=(-0.2, -1, -0.5), re=(-0.2, -1, 0.5))


def tkd_mirror(pose):
    """Sol-sağ aynalı poz (ön ayak/el yer değiştirir)."""
    return _tkd_mirror(P(BASE_POSE, **pose))


def tkd_opp(pose, back):
    """Partner pozunu kendi çerçevesinde 'back' cm geri kaydır (göğüs koruyucu yüzeyi vuruş noktasında kalsın)."""
    return shift(pose, dx=-back)


def tkd_leg(pose, side, direction, length, yaw=0.0, pitch=0.0, knee=None, roll=0.0):
    """Havadaki bacak: bilek, aynı pozdaki kalça ekleminden 'direction' yönünde 'length' cm ötede
    (86-87 cm ≈ düz bacak)."""
    hip = _tkd_solve(P(pose, **{side + "f": air((0, 60, 0))}), side + "hip")
    n = sum(c * c for c in direction) ** 0.5
    ank = tuple(h + c / n * length for h, c in zip(hip, direction))
    return P(pose, **{side + "f": air(ank, yaw=yaw, pitch=pitch, knee=knee, roll=roll)})


# --- duruşlar ---------------------------------------------------------------
READY = P(STAND, lf=planted(6, -14, -4), rf=planted(6, 14, 4), lh=(24, -8, -9), rh=(24, -8, 9),
          le=(-0.4, -1, -0.8), re=(-0.4, -1, 0.8), look=0)
# ap seogi: bir yürüyüş adımı, dizler neredeyse düz; ap kubi: uzun ve alçak, ön diz ayak ucunun üstünde
WALK = dict(y=95, lf=planted(34, -7, 0), rf=planted(-12, 9, 25), look=0)
WALK_R = dict(y=95, rf=planted(34, 7, 0), lf=planted(-12, -9, -25), look=0)
FRONT = dict(y=84, lf=planted(48, -10, 0), rf=planted(-40, 12, 25), look=0)
FRONT_R = dict(y=84, yaw=-6, rf=planted(48, 10, 0), lf=planted(-40, -12, -25), look=1)
# dwit kubi: L duruş; arka ayak 90°, ağırlığın ~%70'i derin bükülü arka bacakta, gövde yarı yana dönük
BACK = dict(x=-22, y=80, yaw=55, cyaw=8, lf=planted(52, -6, 0, heel=4), rf=planted(-24, 12, 90), look=1)

# --- kol teknikleri (göğüs çerçevesi) -----------------------------------------
LOW_BLOCK_L = dict(lh=(30, -44, -18), le=(0, -1, -1))
LOW_PREP_L = dict(lh=(10, 32, 14), le=(0, -1, -0.4), rh=(32, -26, 2), re=(0, -1, 0.3))
LOW_BLOCK_R = dict(rh=(30, -44, 18), re=(0, -1, 1))
LOW_PREP_R = dict(rh=(10, 32, -14), re=(0, -1, 0.4), lh=(32, -26, -2), le=(0, -1, -0.3))
MID_BLOCK_R = dict(rh=(40, 26, 3), re=(0, -1, 0.3))          # momtong an makgi: yumruk omuz hizası, orta hat
MID_PREP_R = dict(rh=(-4, 46, 30), re=(-0.3, -1, 1), lh=(34, 18, 2), le=(0, -1, -0.3))
OUT_BLOCK_L = dict(lh=(32, 36, -16), le=(0.2, -1, -0.2))     # momtong bakkat makgi (dwit kubi)
HIGH_BLOCK_L = dict(lh=(25, 72, 6), le=(0.3, 0.8, -1))       # alnın bir yumruk üstünde ve önünde
HIGH_PREP_L = dict(lh=(22, -10, 14), le=(0, -1, -0.3), rh=(32, 36, -2), re=(0, -1, 0.3))

AP_SEOGI = P(STAND, **WALK, **LOW_BLOCK_L, **TKD_HK_R)
AP_SEOGI_PREP = P(P(STAND, **WALK, **LOW_PREP_L), lf=planted(20, -10, 0))
AP_KUBI = P(STAND, **FRONT, **LOW_BLOCK_L, **TKD_HK_R)
AP_KUBI_PREP = P(P(STAND, **FRONT, **LOW_PREP_L), y=90, lf=planted(30, -12, 0))
DWIT_KUBI = hand_at(P(STAND, **BACK, le=(0.2, -1, -0.3), **TKD_HK_R), "l", (30, 0, 8))
DWIT_KUBI_PREP = P(P(STAND, **BACK), y=90, x=-10, lf=planted(26, -8, 0), lh=(16, 8, 18), le=(0, -1, 0.3),
                   rh=(34, 16, -4), re=(0, -1, 0.3))
PUNCH_BASE = P(P(STAND, **FRONT), x=4, rf=planted(-36, 12, 25), **TKD_HK_L, **TKD_HK_R)
PUNCH_L = hand_at(P(PUNCH_BASE, yaw=10, cyaw=8), "l", (60, -8, 16))
PUNCH_R = hand_at(P(PUNCH_BASE, yaw=-4, cyaw=-10), "r", (60, -8, -16))
WALK_PUNCH_R = hand_at(P(STAND, **WALK_R, cyaw=-8, **TKD_HK_L), "r", (60, -10, -16))
WALK_PUNCH_L = hand_at(P(STAND, **WALK, cyaw=8, **TKD_HK_R), "l", (60, -10, 16))

# --- tekmeler -----------------------------------------------------------------
TKD_KNEE_R = P(TKD_G, x=6, yaw=30, lf=planted(24, -5, 20, heel=14),
               rf=air((30, 64, 10), yaw=10, pitch=10, knee=(1, 0.6, 0)), lh=(32, 30, -6), rh=(26, 38, 8))
AP_CHAGI = tkd_leg(P(TKD_G, x=10, yaw=24, pitch=-10, cpitch=8, lf=planted(24, -5, 16, heel=18),
                     lh=(32, 30, -6), rh=(26, 38, 8)), "r", (80, 16, 2), 85, yaw=0, pitch=-35, knee=(1, 0.3, 0))
# dollyo: destek ayağı ~150° döner, kalça devrilir (yaw ~-86, roll < 0), bacak düz; ayak üstü/kaval
# göğüs koruyucunun kameraya bakan yüzüne değer
DOLLYO_CH = P(TKD_G, x=12, yaw=0, roll=-10, cyaw=20, lf=planted(22, -5, -40, heel=25),
              rf=air((22, 72, 38), yaw=-20, pitch=55, knee=(1, 0.6, -0.2)), lh=(32, 36, -4), rh=(22, 30, 14))
DOLLYO_BODY = P(TKD_G, x=26, y=101, yaw=-86, pitch=0, roll=-28, cyaw=30, croll=10,
                lf=planted(20, -6, -150, heel=20), lh=(30, 40, -2), rhw=(0, 110, 24), rhk=1, re=(-0.5, -1, 0.6))
DOLLYO = tkd_leg(DOLLYO_BODY, "r", (80, 15, 23), 86.5, yaw=-8, pitch=20, knee=(0.1, 1, -0.4), roll=-60)
DOLLYO_BACK = P(DOLLYO_CH, x=18, yaw=-50, roll=-18, cyaw=30, lf=planted(20, -6, -110, heel=22),
                rf=air((40, 88, 30), yaw=-40, pitch=55, knee=(1, 0.6, -0.4)))
# yeop: ön (sol) bacakla; destek ayağının topuğu hedefe döner, gövde kicken uzağa yatar, bacak düz,
# topuk önde ve ayak tabanı hedefe bakar
YEOP_CH = P(TKD_G, x=-8, yaw=84, roll=8, cyaw=-6, rf=planted(-22, 10, 150, heel=10),
            lf=air((0, 80, 0), yaw=150, pitch=60, knee=(0.4, 0.5, 1)), lh=(30, 30, -8), rh=(26, 40, 8))
YEOP_BODY = P(TKD_G, x=-10, y=99, yaw=92, roll=24, croll=-10, cyaw=-14, rf=planted(-22, 10, 172, heel=12),
              lh=(28, 32, -10), rh=(26, 42, 8))
YEOP = tkd_leg(YEOP_BODY, "l", (86, 16, -2), 86.5, yaw=180, pitch=75, knee=(0, -1, 0.35))
# dwi: sağa dönüp sırtı hedefe çevir, baş sağ omuzun üstünden hedefe bakar, topuk düz geriye
DWI_TURN = P(TKD_G, x=4, yaw=128, pitch=10, look=0, hyaw=55, lf=planted(24, -5, 140, heel=22),
             rf=planted(-24, 12, 112, heel=45), lh=(32, 28, -6), rh=(28, 36, 8))
DWI_BODY = P(TKD_G, x=10, y=98, yaw=194, pitch=20, cpitch=4, cyaw=24, look=0, hyaw=88, hpitch=8,
             lf=planted(24, -5, 200, heel=10), lh=(30, 28, -8), rh=(26, 36, 8))
DWI = tkd_leg(DWI_BODY, "r", (88, 14, 8), 86.5, yaw=180, pitch=78, knee=(0, -1, 0))
DWI_CH = tkd_leg(DWI_BODY, "r", (14, -36, 2), 40, yaw=180, pitch=70, knee=(-1, -0.4, 0))
# naeryo: düz bacak yukarı, topuk yay çizerek omuz/göğüs koruyucunun üstüne iner
NAERYO_BODY = P(TKD_G, x=8, y=97, yaw=18, pitch=-12, cpitch=6, lf=planted(24, -5, 22, heel=16),
                lh=(32, 30, -6), rh=(24, 40, 8))
NAERYO_UP = tkd_leg(P(NAERYO_BODY, pitch=-16), "r", (24, 86, 2), 86.5, yaw=0, pitch=-150, knee=(-0.95, 0.3, 0))
NAERYO_MID = tkd_leg(NAERYO_BODY, "r", (42, 75, -10), 86.5, yaw=0, pitch=-140, knee=(-0.87, 0.5, 0))
NAERYO_DOWN = tkd_leg(P(NAERYO_BODY, pitch=-6), "r", (66, 40, -12), 86.5, yaw=60, pitch=-40,
                      knee=(-0.64, 0.77, 0))
NAERYO_RISE = tkd_leg(P(NAERYO_BODY, pitch=-8), "r", (40, 60, 20), 80, yaw=0, pitch=-60, knee=(0.2, 1, 0.4))

# --- ayak oyunu ---------------------------------------------------------------
# yan duruş (gyeorugi seogi): kalça ~66° dönük, ayak uçlarında
TKD_FW = P(TKD_G, yaw=66, cyaw=-4, lf=planted(22, -4, 30, heel=10), rf=planted(-28, 10, 78, heel=26))


def tkd_hop(pose, h=4.5):
    """Ayak uçlarından hafif sekme: iki ayak da h cm havada, kalça h cm yukarıda."""
    pel = _tkd_solve(pose, "pelvis")
    feet = {}
    for s in ("l", "r"):
        f = pose[s + "f"]
        feet[s + "f"] = air((f["a"][0], f["a"][1] + h, f["a"][2]), yaw=f["yaw"], pitch=f["pitch"] + 6, knee=f["knee"])
    return P(pose, y=pel[1] + h, autoy=0, **feet)


TKD_FW_UP = tkd_hop(TKD_FW)
TKD_FW_S = tkd_mirror(TKD_FW)
TKD_FW_S_UP = tkd_mirror(TKD_FW_UP)
# switch: havada ayaklar yer değiştirir, gövde öne (rakibe) dönerek geçer
TKD_SWITCH = P(TKD_FW, y=100, yaw=0, cyaw=0, autoy=0, lf=air((-4, 11, -12), yaw=0, pitch=30, knee=(1, 0.3, 0)),
               rf=air((-2, 11, 12), yaw=0, pitch=30, knee=(1, 0.3, 0)), lh=(32, 26, -12), rh=(32, 30, 10))

# --- taegeuk 1 (öz): poz yerel çerçevede kurulur, formdaki yönüne çevrilip konumuna kaydırılır; adım atan ayak
# ara anahtarda havaya kalkar (ayaklar yerde kaymasın) ---------------------------------------------------------
TG_R = 105   # tüm formun yönü: ilk bölüm (sola dönüş) ve son bölüm kameraya 3/4 önden görünür


def _tg(pose, facing, x=0.0, z=0.0, **feet):
    """Yerel pozu formdaki yönüne (facing) çevir, (x, z)'ye kaydır; 'feet' ayakları form koordinatında
    (döndürmeden önce) değiştirir; sonra tüm form TG_R kadar döner."""
    p = shift(turn(pose, facing), dx=x, dz=z)
    if feet:
        p = P(p, **feet)
    return turn(p, TG_R)


def _tg_lift(x, z, facing, h=14):
    """Adım sırasında havadaki ayak (form koordinatı)."""
    c = {0: (1, 0.3, 0), 90: (0, 0.3, 1), -90: (0, 0.3, -1)}[facing]
    return air((x, h, z), yaw=facing, pitch=15, knee=c)


TG_AP_SEOGI_R = P(STAND, **WALK_R, **LOW_BLOCK_R, **TKD_HK_L)
TG_AP_SEOGI_R_PREP = P(STAND, **WALK_R, **LOW_PREP_R)
TG_KNEE = P(P(STAND, **WALK), lf=planted(34, -7, 0, heel=10),
            rf=air((10, 60, 8), yaw=0, pitch=20, knee=(1, 0.5, 0)), lh=(30, 20, -6), rh=(26, 26, 8),
            le=(-0.2, -1, -0.4), re=(-0.2, -1, 0.4))
TG_PUNCH_R = hand_at(P(STAND, **FRONT, yaw=-4, cyaw=-10, **TKD_HK_L), "r", (60, -8, -16))
TG_KICK = tkd_leg(P(TG_KNEE, pitch=-8, x=4), "r", (80, 36, 2), 85, yaw=0, pitch=-35, knee=(1, 0.3, 0))
TG_HIGH_KUBI = P(AP_KUBI, **HIGH_BLOCK_L, **TKD_HK_R)
TG_RET = P(READY, x=6)
TAEGEUK = [
    (0, _tg(READY, 0)),
    # 1) sola dön: ap seogi + arae makgi   2) adım: ap seogi + jireugi
    (6, _tg(AP_SEOGI_PREP, -90, 0, -4, lf=_tg_lift(0, -28, -90))),
    (12, _tg(AP_SEOGI, -90, 0, -8)), (20, _tg(AP_SEOGI, -90, 0, -8)),
    (26, _tg(P(AP_SEOGI, x=22), -90, 0, -8, rf=_tg_lift(3, -40, -90))),
    (32, _tg(WALK_PUNCH_R, -90, 0, -52)), (38, _tg(WALK_PUNCH_R, -90, 0, -52)),
    # 3) sağa 180° dön: ap seogi + arae makgi   4) adım: ap seogi + jireugi
    (46, _tg(TG_AP_SEOGI_R_PREP, 90, -10, -40, lf=planted(-9, -40, -25), rf=_tg_lift(-24, -36, 0))),
    (54, _tg(TG_AP_SEOGI_R, 90, -18, -28)), (60, _tg(TG_AP_SEOGI_R, 90, -18, -28)),
    (66, _tg(P(TG_AP_SEOGI_R, x=22), 90, -18, -28, lf=_tg_lift(-12, 6, 90))),
    (72, _tg(WALK_PUNCH_L, 90, -18, 16)), (78, _tg(WALK_PUNCH_L, 90, -18, 16)),
    # 5) sola dön: ap kubi + arae makgi   6) ters jireugi
    (84, _tg(AP_KUBI_PREP, 0, -33, 10, lf=planted(-11, 50, 60), rf=_tg_lift(-57, 10, 0))),
    (90, _tg(AP_KUBI_PREP, 0, -44, 3, rf=planted(-88, 12, 25), lf=_tg_lift(-6, 20, 0))),
    (96, _tg(AP_KUBI, 0, -48, 0)), (102, _tg(AP_KUBI, 0, -48, 0)),
    (110, _tg(TG_PUNCH_R, 0, -48, 0)), (115, _tg(TG_PUNCH_R, 0, -48, 0)),
    # olgul makgi
    (121, _tg(P(AP_KUBI, **HIGH_PREP_L), 0, -48, 0)), (127, _tg(TG_HIGH_KUBI, 0, -48, 0)),
    (132, _tg(TG_HIGH_KUBI, 0, -48, 0)),
    # ap chagi -> öne bas: ap seogi + jireugi (kihap) -> junbi
    (138, _tg(TG_KNEE, 0, -34, -3)), (143, _tg(TG_KICK, 0, -34, -3)), (148, _tg(P(TG_KNEE, x=8), 0, -34, -3)),
    (154, _tg(WALK_PUNCH_R, 0, 12, -1)), (160, _tg(WALK_PUNCH_R, 0, 12, -1)),
    (166, _tg(TG_RET, 0, 0, 0, lf=planted(2, -12, -4), rf=_tg_lift(26, 10, 0))),
]

# --- partner hareketleri (partnerin kendi çerçevesi; aynalanınca 'r' uzuvlar kameraya yakın tarafa gelir) ---
ARAE_D = 120
OPP_GUARD_MID = P(TKD_G, lh=(34, 24, -6), rh=(28, 34, 6))
OPP_KNEE = P(OPP_GUARD_MID, x=6, yaw=30, lf=planted(24, -5, 20, heel=14),
             rf=air((34, 68, 12), yaw=10, pitch=10, knee=(1, 0.6, 0)))
OPP_FRONT = P(OPP_GUARD_MID, x=10, yaw=24, pitch=-8, lf=planted(24, -5, 16, heel=18),
              rf=air((ARAE_D - 49, 78, 12), yaw=0, pitch=-25, knee=(1, 0.3, 0)))
OPP_FRONT_DOWN = P(OPP_FRONT, rf=air((ARAE_D - 47, 61, 25), yaw=12, pitch=-5, knee=(1, 0.4, 0.2)))
OPP_FRONT_OUT = P(OPP_FRONT, x=6, rf=air((ARAE_D - 50, 52, 31), yaw=16, pitch=5, knee=(1, 0.5, 0.3)))
ARAE_GUARD = P(STAND, **FRONT_R, lh=(32, 16, -4), rh=(28, 26, 8), le=(-0.2, -1, -0.5), re=(-0.2, -1, 0.5))
ARAE_PREP = P(ARAE_GUARD, **LOW_PREP_R)
ARAE_HIT = P(ARAE_GUARD, rh=(46, -6, 10), re=(0, -1, 0.8), lh=(20, -12, -16), le=(-0.6, -1, -0.3))
ARAE_END = P(ARAE_GUARD, **LOW_BLOCK_R, **TKD_HK_L)

MOM_D = 106
OPP_PUNCH = P(OPP_GUARD_MID, x=18, yaw=14, cyaw=10, lf=planted(46, -5, 20), rf=planted(-14, 12, 60, heel=30),
              lhw=(MOM_D - 26, 116, 9), lhk=1, le=(0, -1, 0.4))
OPP_PUNCH_IN = P(OPP_PUNCH, cyaw=14, lhw=(MOM_D - 28, 113, -8))
MOM_GUARD = ARAE_GUARD
MOM_PREP = P(MOM_GUARD, **MID_PREP_R)
MOM_HIT = P(MOM_GUARD, rh=(38, 32, 12), re=(0, -1, 0.6), lh=(26, 4, -14), le=(-0.6, -1, -0.3))
MOM_END = P(MOM_GUARD, **MID_BLOCK_R, **TKD_HK_L)

OLG_D = 108
OLG_GUARD = P(P(STAND, **FRONT), look=1, lh=(32, 16, -4), rh=(28, 26, 8), le=(-0.2, -1, -0.5), re=(-0.2, -1, 0.5))
OLG_PREP = P(OLG_GUARD, **HIGH_PREP_L)
OLG_END = P(OLG_GUARD, **HIGH_BLOCK_L, **TKD_HK_R)
OPP_HIGH = P(OPP_GUARD_MID, x=18, yaw=-8, cyaw=-12, lf=planted(46, -5, 20), rf=planted(-14, 12, 60, heel=30),
             rhw=(OLG_D - 26, 151, -4), rhk=1, re=(0, -1, 0.3))

TAEKWONDO = {
    "tkd_ap_seogi": Move("taekwondo", 64, [(0, READY), (9, AP_SEOGI_PREP), (18, AP_SEOGI), (44, AP_SEOGI),
                                           (56, READY)], cam=dict(az=38)),
    "tkd_ap_kubi": Move("taekwondo", 64, [(0, READY), (9, AP_KUBI_PREP), (18, AP_KUBI), (44, AP_KUBI),
                                          (56, READY)], cam=dict(az=38)),
    "tkd_dwit_kubi": Move("taekwondo", 64, [(0, READY), (9, DWIT_KUBI_PREP), (18, DWIT_KUBI), (44, DWIT_KUBI),
                                            (56, READY)], cam=dict(az=10)),
    "tkd_jireugi": Move("taekwondo", 44, [(0, PUNCH_R), (10, PUNCH_L), (20, PUNCH_L), (32, PUNCH_R)],
                        cam=dict(az=28), target="partner", opp=[(0, tkd_opp(TKD_OPP, 8))],
                        hits=[(10, "lhand"), (32, "rhand")]),
    "tkd_arae_makgi": Move("taekwondo", 50, [(0, ARAE_GUARD), (6, ARAE_PREP), (12, ARAE_HIT), (16, ARAE_END),
                                             (32, ARAE_END), (42, ARAE_GUARD)],
                           cam=dict(az=30), target="partner", opp_dist=ARAE_D,
                           opp=[(0, OPP_GUARD_MID), (6, OPP_KNEE), (12, OPP_FRONT), (15, OPP_FRONT_DOWN),
                                (18, OPP_FRONT_OUT), (26, OPP_KNEE), (36, OPP_GUARD_MID)]),
    "tkd_momtong_makgi": Move("taekwondo", 50, [(0, MOM_GUARD), (7, MOM_PREP), (13, MOM_HIT), (16, MOM_END),
                                                (32, MOM_END), (42, MOM_GUARD)],
                              cam=dict(az=30), target="partner", opp_dist=MOM_D,
                              opp=[(0, OPP_GUARD_MID), (6, OPP_GUARD_MID), (13, OPP_PUNCH), (16, OPP_PUNCH_IN),
                                   (24, OPP_PUNCH_IN), (34, OPP_GUARD_MID)]),
    "tkd_olgul_makgi": Move("taekwondo", 50, [(0, OLG_GUARD), (6, OLG_PREP), (13, OLG_END), (32, OLG_END),
                                              (42, OLG_GUARD)], cam=dict(az=30),
                            target="partner", opp_dist=OLG_D,
                            opp=[(0, OPP_GUARD_MID), (13, OPP_HIGH), (22, OPP_HIGH), (34, OPP_GUARD_MID)]),
    "tkd_ap_chagi": Move("taekwondo", 44, [(0, TKD_G), (9, TKD_KNEE_R), (15, AP_CHAGI), (19, AP_CHAGI),
                                           (25, TKD_KNEE_R), (34, TKD_G)], cam=dict(az=20), target="partner",
                         opp=[(0, tkd_opp(TKD_OPP, 8))], hits=[(15, "rball")]),
    "tkd_dollyo_chagi": Move("taekwondo", 44, [(0, TKD_G), (8, DOLLYO_CH), (15, DOLLYO), (19, DOLLYO),
                                               (26, DOLLYO_BACK), (36, TKD_G)], cam=dict(az=18), target="partner",
                             opp=[(0, tkd_opp(TKD_OPP, -15))], hits=[(15, "rankle")]),
    "tkd_yeop_chagi": Move("taekwondo", 48, [(0, TKD_G), (10, YEOP_CH), (17, YEOP), (22, YEOP), (29, YEOP_CH),
                                             (38, TKD_G)], cam=dict(az=18), target="partner",
                           opp=[(0, tkd_opp(TKD_OPP, 8))], hits=[(17, "lheel")]),
    "tkd_dwi_chagi": Move("taekwondo", 56, [(0, TKD_G), (10, DWI_TURN), (15, DWI_CH), (19, DWI), (24, DWI),
                                            (29, DWI_CH), (35, DWI_TURN), (46, TKD_G)], cam=dict(az=16),
                          target="partner", opp=[(0, tkd_opp(TKD_OPP, 8))], hits=[(19, "rheel")]),
    "tkd_naeryo_chagi": Move("taekwondo", 52, [(0, TKD_G), (9, NAERYO_RISE), (15, NAERYO_UP), (19, NAERYO_UP),
                                               (22, NAERYO_MID), (25, NAERYO_DOWN), (30, NAERYO_DOWN),
                                               (36, TKD_KNEE_R), (44, TKD_G)], cam=dict(az=18),
                             target="partner", opp=[(0, tkd_opp(TKD_OPP_LOW, 4.5))], hits=[(25, "rheel")]),
    "tkd_footwork": Move("taekwondo", 56, [
        (0, TKD_FW), (4, TKD_FW_UP), (8, TKD_FW), (12, shift(TKD_FW_UP, dx=15)), (16, shift(TKD_FW, dx=30)),
        (20, shift(TKD_FW_UP, dx=15)), (24, TKD_FW), (28, TKD_SWITCH), (32, TKD_FW_S), (36, TKD_FW_S_UP),
        (40, TKD_FW_S), (44, TKD_SWITCH), (48, TKD_FW), (52, TKD_FW_UP)], cam=dict(az=70)),
    "tkd_taegeuk1": Move("taekwondo", 172, TAEGEUK, cam=dict(az=-15)),
}
