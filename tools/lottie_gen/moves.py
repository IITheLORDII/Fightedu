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


def run_knee(side):
    """Yerinde koşu: bir diz yukarıda, kollar karşıt sallanıyor."""
    o = "r" if side == "l" else "l"
    zs = -11 if side == "l" else 11
    up = air((16, 50, zs), yaw=0, pitch=25, knee=(1, 0.6, 0))
    arm_fwd, arm_back = (24, 2, -16 if o == "l" else 16), (-16, -8, -18 if side == "l" else 18)
    d = {side + "f": up, o + "f": planted(4, -zs, 0, heel=35), "y": 99}
    d[o + "h"] = arm_fwd
    d[side + "h"] = arm_back
    d[o + "e"] = (-1, -0.3, 0)
    d[side + "e"] = (-1, -0.3, 0)
    return P(STAND, **d)


def plank_body(x, y, pitch, feet_x=-100, heel=72):
    return dict(x=x, y=y, pitch=pitch, look=0, hpitch=-50, autoy=0,
                lf=planted(feet_x, -10, 0, heel=heel), rf=planted(feet_x, 10, 0, heel=heel))


PU_UP = P(STAND, **plank_body(-14, 50, 68), lhw=(30, 4, -22), rhw=(30, 4, 22), lhk=1, rhk=1,
          le=(0, -1, -0.6), re=(0, -1, 0.6))
PU_DN = P(PU_UP, x=-10, y=30, pitch=80)
PLANK = P(STAND, **plank_body(-12, 33, 80, feet_x=-104, heel=78), lhw=(30, 4, -12), rhw=(30, 4, 12),
          lhk=1, rhk=1, le=(-0.2, -1, -0.5), re=(-0.2, -1, 0.5))
SIT_DOWN = P(STAND, y=11, pitch=-88, look=0, hpitch=-30, autoy=0, lh=(13, 24, 9), rh=(13, 24, -9),
             le=(0, -1, -1), re=(0, -1, 1), lf=planted(38, -11, 0), rf=planted(38, 11, 0))
SIT_UP = P(SIT_DOWN, pitch=-24, hpitch=0)
SQUAT_LOW = P(STAND_WIDE, y=54, pitch=30, cpitch=8, le=(0, -1, -0.3), re=(0, -1, 0.3))
SQUAT_LOW = hand_at(hand_at(SQUAT_LOW, "l", (56, 0, 4)), "r", (56, 0, -4))
SQUAT_MID = P(STAND_WIDE, y=78, pitch=16, cpitch=4, lh=(30, 14, -14), rh=(30, 14, 14),
              le=(0, -1, -0.3), re=(0, -1, 0.3))
CROUCH = P(STAND_WIDE, y=50, pitch=48, cpitch=10, look=0, hpitch=-20, lhw=(40, 4, -16), rhw=(40, 4, 16),
           lhk=1, rhk=1, le=(-0.5, -1, -0.3), re=(-0.5, -1, 0.3), autoy=1)
JUMP_UP = P(STAND, y=112, autoy=0, lf=air((2, 16, -12), yaw=-6, pitch=35), rf=air((2, 16, 12), yaw=6, pitch=35),
            lh=(4, 62, -16), rh=(4, 62, 16), le=(0, 0.2, -1), re=(0, 0.2, 1))
ROPE_DOWN = P(STAND, y=96, lf=planted(4, -12, -6, heel=28), rf=planted(4, 12, 6, heel=28),
              lh=(8, -20, -26), rh=(8, -20, 26), le=(-1, -0.6, -0.2), re=(-1, -0.6, 0.2))
ROPE_UP = P(ROPE_DOWN, y=104, autoy=0, lf=air((5, 15, -12), yaw=-6, pitch=40), rf=air((5, 15, 12), yaw=6, pitch=40),
            lh=(4, -22, -27), rh=(4, -22, 27))
HAM = P(STAND, pitch=72, cpitch=16, look=0, hpitch=-20, y=96, lhw=(22, 22, -10), rhw=(22, 22, 10),
        lhk=1, rhk=1, le=(-0.2, -1, -0.4), re=(-0.2, -1, 0.4), lf=planted(4, -10, -4), rf=planted(4, 10, 4))
QUAD_ST = P(STAND, lf=planted(4, -8, -4), rf=air((-18, 86, 10), yaw=180, pitch=-70, knee=(0.15, -1, 0)),
            rhw=(-20, 90, 17), rhk=1, re=(-1, -0.3, 0.6), lh=(30, 18, -22), le=(0, -1, -0.5), roll=-2)
SHOULDER_ST = P(STAND, lh=(16, 24, 38), le=(1, 0, 0), rh=(24, 22, 2), re=(0, -1, 0.6))

GENERAL = {
    "gen_jog": Move("general", 30, [(0, run_knee("l")), (15, run_knee("r"))], cam=dict(az=30)),
    "gen_arm_circles": Move("general", 64, [
        (0, P(STAND, lh=(2, -32, -24), rh=(2, -32, 24))),
        (8, P(STAND, lh=(44, -14, -26), rh=(-40, -14, 26))),
        (16, P(STAND, lh=(56, 27, -26), rh=(-54, 27, 26))),
        (24, P(STAND, lh=(40, 64, -26), rh=(-38, 64, 26))),
        (32, P(STAND, lh=(0, 82, -24), rh=(0, 82, 24))),
        (40, P(STAND, lh=(-38, 64, -26), rh=(40, 64, 26))),
        (48, P(STAND, lh=(-54, 27, -26), rh=(56, 27, 26))),
        (56, P(STAND, lh=(-40, -14, -26), rh=(44, -14, 26))),
    ], cam=dict(az=6)),
    "gen_squat": Move("general", 56, [(0, STAND_WIDE), (12, SQUAT_MID), (24, SQUAT_LOW), (32, SQUAT_LOW),
                                      (44, SQUAT_MID)], cam=dict(az=32)),
    "gen_jump_rope": Move("general", 20, [(0, ROPE_DOWN), (10, ROPE_UP)], cam=dict(az=48), rope=10),
    "gen_pushup": Move("general", 50, [(0, PU_UP), (20, PU_DN), (28, PU_DN)], cam=dict(az=10, el=10)),
    "gen_plank": Move("general", 60, [(0, PLANK), (30, P(PLANK, y=34.5))], cam=dict(az=10, el=10)),
    "gen_situp": Move("general", 50, [(0, SIT_DOWN), (20, SIT_UP), (26, SIT_UP)], cam=dict(az=10, el=10)),
    "gen_stretch_hamstring": Move("general", 80, [(0, STAND), (26, HAM), (54, P(HAM, pitch=78))], cam=dict(az=12)),
    "gen_stretch_quad": Move("general", 60, [(0, QUAD_ST), (30, P(QUAD_ST, pitch=3))], cam=dict(az=20)),
    "gen_stretch_shoulder": Move("general", 60, [(0, SHOULDER_ST), (30, P(SHOULDER_ST, rh=(18, 24, 2)))],
                                 cam=dict(az=55)),
    "gen_burpee": Move("general", 64, [(0, STAND), (12, CROUCH), (22, P(PU_UP, look=0, hpitch=-40)),
                                       (32, CROUCH), (44, JUMP_UP), (54, STAND)], cam=dict(az=14, el=8)),
}

# ==========================================================================
# BOKS
# ==========================================================================
BOX = P(BASE_POSE, y=90, z=2, yaw=38, pitch=5, cpitch=7, chin=10,
        lh=(24, 42, -15), rh=(14, 39, 7), le=(-0.1, -1, -0.45), re=(-0.25, -1, 0.4),
        lf=planted(26, -9, 22), rf=planted(-28, 15, 52, heel=20))
BOX_DIP = P(BOX, y=87, chin=12)
JAB = hand_at(P(BOX, yaw=44, cyaw=6, pitch=7, rf=planted(-28, 15, 52, heel=26), le=(0, -1, -0.2)),
              "l", (57, 6, 6))
CROSS = hand_at(P(BOX, x=3, yaw=6, cyaw=-6, pitch=9, rf=planted(-28, 15, 82, heel=48), lh=(18, 41, -9),
                  re=(0, -1, 0.2)), "r", (58, 4, -10))
LHOOK_PREP = P(BOX, yaw=30, cyaw=-6)
LHOOK = hand_at(P(BOX, yaw=62, cyaw=14, pitch=6, lf=planted(26, -9, 62, heel=14), rh=(13, 40, 6),
                  le=(0.1, 0.35, -1)), "l", (38, 6, 26))
RHOOK = hand_at(P(BOX, yaw=-2, cyaw=-16, pitch=6, rf=planted(-28, 15, 86, heel=50), lh=(16, 42, -8),
                  re=(0.1, 0.35, 1)), "r", (38, 6, -26))
LUPPER_DIP = P(BOX, y=84, roll=-6, croll=-8, cpitch=10, lh=(22, 28, -14), le=(0, -1, -0.2))
LUPPER = hand_at(P(BOX, yaw=50, cyaw=8, pitch=2, cpitch=4, roll=4, lf=planted(26, -9, 40, heel=10),
                   le=(0, -1, -0.1)), "l", (38, 4, 14))
RUPPER_DIP = P(BOX, y=84, roll=6, croll=8, cpitch=10, rh=(16, 26, 8), re=(0, -1, 0.2))
RUPPER = hand_at(P(BOX, yaw=8, cyaw=-8, pitch=4, rf=planted(-28, 15, 80, heel=45), lh=(18, 41, -8),
                   re=(0, -1, 0.1)), "r", (38, 2, -14))
SLIP = P(BOX, y=84, z=8, roll=4, croll=18, cyaw=-8, cpitch=12)
ROLL_L = P(BOX, y=76, z=-6, pitch=14, cpitch=20, croll=-14)
ROLL_B = P(BOX, y=68, pitch=18, cpitch=26)
ROLL_R = P(BOX, y=80, z=8, pitch=10, cpitch=14, croll=14)
PARRY = P(BOX, rh=(30, 44, -12), re=(0, -1, 0.2))
BLOCK = P(BOX, lh=(6, 50, -16), le=(-0.3, -1, -0.6), chin=14)
# kombinasyonlarda kroşe için yarım adım içeri
LHOOK_IN = hand_at(P(LHOOK, x=16, lf=planted(40, -9, 62, heel=14), rf=planted(-16, 15, 52, heel=24)),
                   "l", (34, 6, 26))


def box_feet(lx, rx, x):
    return P(BOX, x=x, lf=planted(lx, -9, 22), rf=planted(rx, 15, 52, heel=20))


BOXING = {
    "box_stance": Move("boxing", 60, [(0, BOX), (15, BOX_DIP), (30, BOX), (45, BOX_DIP)], cam=dict(az=28)),
    "box_footwork": Move("boxing", 64, [
        (0, box_feet(14, -40, -12)), (10, box_feet(30, -40, -4)), (20, box_feet(30, -24, 4)),
        (32, box_feet(30, -24, 4)), (42, box_feet(30, -40, -4)), (52, box_feet(14, -40, -12))],
        cam=dict(az=12)),
    "box_jab": Move("boxing", 36, [(0, BOX), (8, JAB), (13, JAB), (24, BOX)], cam=dict(az=16),
                    target="bag", hits=[(8, "lhand")]),
    "box_cross": Move("boxing", 40, [(0, BOX), (10, CROSS), (15, CROSS), (28, BOX)], cam=dict(az=16),
                      target="bag", hits=[(10, "rhand")]),
    "box_lead_hook": Move("boxing", 42, [(0, BOX), (5, LHOOK_PREP), (13, LHOOK), (18, LHOOK), (30, BOX)],
                          cam=dict(az=34), target="bag", hits=[(13, "lhand")]),
    "box_rear_hook": Move("boxing", 42, [(0, BOX), (13, RHOOK), (18, RHOOK), (30, BOX)], cam=dict(az=34),
                          target="bag", hits=[(13, "rhand")]),
    "box_lead_uppercut": Move("boxing", 42, [(0, BOX), (6, LUPPER_DIP), (13, LUPPER), (18, LUPPER), (30, BOX)],
                              cam=dict(az=22), target="bag", hits=[(13, "lhand")]),
    "box_rear_uppercut": Move("boxing", 42, [(0, BOX), (6, RUPPER_DIP), (13, RUPPER), (18, RUPPER), (30, BOX)],
                              cam=dict(az=22), target="bag", hits=[(13, "rhand")]),
    "box_slip": Move("boxing", 44, [(0, BOX), (10, SLIP), (16, SLIP), (28, BOX)], cam=dict(az=42),
                     target="partner", opp_dist=128, opp=[(0, BOX), (10, JAB), (15, JAB), (26, BOX)],
                     trails=[("head", 0, 10)]),
    "box_roll": Move("boxing", 56, [(0, BOX), (10, ROLL_L), (18, ROLL_B), (27, ROLL_R), (40, BOX)],
                     cam=dict(az=42), target="partner", opp_dist=122,
                     opp=[(0, BOX), (8, LHOOK_PREP), (17, LHOOK), (22, LHOOK), (34, BOX)],
                     trails=[("head", 4, 28)]),
    "box_parry_block": Move("boxing", 48, [(0, BOX), (7, PARRY), (13, BOX), (24, BLOCK), (32, BLOCK), (40, BOX)],
                            cam=dict(az=38), target="partner", opp_dist=118,
                            opp=[(0, BOX), (7, JAB), (12, BOX), (18, LHOOK_PREP), (24, LHOOK), (31, LHOOK),
                                 (40, BOX)]),
    "box_combo_12": Move("boxing", 48, [(0, BOX), (7, JAB), (12, P(BOX, yaw=30)), (19, CROSS), (24, CROSS),
                                        (36, BOX)], cam=dict(az=16), target="bag",
                         hits=[(7, "lhand"), (19, "rhand")]),
    "box_combo_123": Move("boxing", 62, [(0, BOX), (7, JAB), (12, P(BOX, yaw=30)), (19, CROSS), (24, CROSS),
                                         (32, LHOOK_IN), (37, LHOOK_IN), (48, BOX)], cam=dict(az=20),
                          target="bag", hits=[(7, "lhand"), (19, "rhand"), (32, "lhand")]),
    "box_shadow": Move("boxing", 120, [
        (0, BOX), (7, JAB), (13, BOX), (20, CROSS), (28, BOX), (38, SLIP), (46, BOX), (54, LHOOK_PREP),
        (60, LHOOK), (68, BOX), (76, ROLL_L), (82, ROLL_B), (88, ROLL_R), (98, BOX), (105, RUPPER), (112, BOX)],
        cam=dict(az=24)),
}

# ==========================================================================
# KİCK BOKS
# ==========================================================================
KB = P(BOX, y=92, yaw=33, pitch=3, cpitch=5, lf=planted(24, -7, 15), rf=planted(-24, 13, 40, heel=15),
       lh=(24, 43, -14), rh=(14, 40, 7))
KB_DIP = P(KB, y=89)
KB_JAB = hand_at(P(KB, yaw=40, cyaw=6, pitch=5, rf=planted(-24, 13, 40, heel=22), le=(0, -1, -0.2)),
                 "l", (56, 6, 6))
KB_CROSS = hand_at(P(KB, x=3, yaw=4, cyaw=-6, pitch=7, rf=planted(-24, 13, 78, heel=45), lh=(18, 42, -9),
                     re=(0, -1, 0.2)), "r", (58, 4, -10))
KB_LHOOK = hand_at(P(KB, x=14, yaw=58, cyaw=14, pitch=5, lf=planted(38, -7, 58, heel=14),
                     rf=planted(-12, 13, 40, heel=20), rh=(13, 41, 6), le=(0.1, 0.35, -1)), "l", (34, 6, 26))
TEEP_CH = P(KB, pitch=-4, lf=air((32, 52, -6), yaw=10, pitch=-15, knee=(1, 0.6, 0)), rf=planted(-24, 13, 40, heel=8))
TEEP = P(KB, x=4, pitch=-14, cpitch=0, lf=air((80, 94, -4), yaw=0, pitch=-55, knee=(1, 0.3, 0)),
         rf=planted(-24, 13, 40, heel=6))
RK_STEP = P(KB, x=4, lf=planted(30, -12, -10), yaw=24)
RK_CH = P(KB, x=4, yaw=-8, roll=-6, pitch=0, lf=planted(30, -12, -40, heel=15),
          rf=air((-4, 52, 26), yaw=-30, pitch=40, knee=(0.8, 0.5, 0.6)))


def round_kick(height, lean, fy=-15):
    ank = {"low": (60, 50, -10), "mid": (62, 104, -4), "high": (52, 152, -2)}[height]
    knee = {"low": (0.4, 1, 0.6), "mid": (0.1, 1, 0.5), "high": (0, 1, 0.3)}[height]
    return P(KB, x=4, yaw=-62 - lean / 3, pitch=-6 - lean / 3, roll=-12 - lean, cyaw=10,
             lf=planted(30, -12, -78, heel=20 + lean),
             rf=air(ank, yaw=fy, pitch=40, knee=knee), rhw=(-24, 108, 36), rhk=1, re=(-0.5, -1, 0.6),
             lh=(22, 44, -4))


RK_LOW, RK_MID, RK_HIGH = round_kick("low", 0), round_kick("mid", 8), round_kick("high", 16)
RK_BACK = P(KB, x=4, yaw=-10, lf=planted(30, -12, -30, heel=12),
            rf=air((-14, 56, 30), yaw=-20, pitch=30, knee=(0.6, 0.6, 0.6)))
CLINCH = P(KB, y=94, lhw=(44, 150, -10), rhw=(44, 150, 10), lhk=1, rhk=1, le=(-0.2, -1, -0.9), re=(-0.2, -1, 0.9))
KNEE = P(CLINCH, x=4, yaw=12, pitch=-8, lhw=(36, 126, -10), rhw=(36, 126, 10),
         lf=planted(24, -7, 15, heel=28), rf=air((-4, 54, 8), yaw=0, pitch=55, knee=(1, 0.7, 0)))
CHECK = P(KB, pitch=2, roll=5, lf=air((22, 46, -20), yaw=-30, pitch=30, knee=(0.6, 0.7, -0.5)),
          lh=(10, 44, -18), le=(-0.1, -1, -0.5))


def kb_feet(lx, rx, x):
    return P(KB, x=x, lf=planted(lx, -7, 15), rf=planted(rx, 13, 40, heel=15))


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
    "kb_low_kick": Move("kickboxing", 48, [(0, KB), (7, RK_STEP), (12, RK_CH), (18, RK_LOW), (22, RK_LOW),
                                           (30, RK_BACK), (40, KB)], cam=dict(az=12), target="long_bag",
                        hits=[(18, "rankle")]),
    "kb_middle_kick": Move("kickboxing", 50, [(0, KB), (7, RK_STEP), (12, RK_CH), (19, RK_MID), (23, RK_MID),
                                              (31, RK_BACK), (42, KB)], cam=dict(az=12), target="long_bag",
                           hits=[(19, "rankle")]),
    "kb_high_kick": Move("kickboxing", 52, [(0, KB), (7, RK_STEP), (12, RK_CH), (20, RK_HIGH), (24, RK_HIGH),
                                            (33, RK_BACK), (44, KB)], cam=dict(az=12), target="long_bag",
                         hits=[(20, "rankle")]),
    "kb_knee": Move("kickboxing", 42, [(0, KB), (6, CLINCH), (12, KNEE), (18, KNEE), (28, CLINCH), (36, KB)],
                    cam=dict(az=12), target="long_bag", hits=[(12, "rknee")]),
    "kb_check": Move("kickboxing", 42, [(0, KB), (10, CHECK), (21, CHECK), (32, KB)], cam=dict(az=30),
                     target="partner", opp_dist=118,
                     opp=[(0, KB), (5, RK_STEP), (12, RK_LOW), (20, RK_LOW), (28, RK_BACK), (36, KB)]),
    "kb_combo_jcl": Move("kickboxing", 66, [(0, KB), (7, KB_JAB), (12, P(KB, yaw=26)), (19, KB_CROSS),
                                            (25, RK_STEP), (29, RK_CH), (35, RK_LOW), (39, RK_LOW),
                                            (47, RK_BACK), (56, KB)], cam=dict(az=14), target="long_bag",
                         hits=[(7, "lhand"), (19, "rhand"), (35, "rankle")]),
    "kb_combo_jcm": Move("kickboxing", 82, [(0, KB), (7, KB_JAB), (12, P(KB, yaw=26)), (19, KB_CROSS),
                                            (24, P(KB, yaw=26)), (31, KB_LHOOK), (37, RK_STEP), (41, RK_CH),
                                            (48, RK_MID), (52, RK_MID), (60, RK_BACK), (70, KB)],
                         cam=dict(az=16), target="long_bag",
                         hits=[(7, "lhand"), (19, "rhand"), (31, "lhand"), (48, "rankle")]),
    "kb_shadow": Move("kickboxing", 120, [
        (0, KB), (7, KB_JAB), (13, KB), (20, KB_CROSS), (28, KB), (36, TEEP_CH), (42, TEEP), (48, TEEP_CH),
        (56, KB), (62, CLINCH), (68, KNEE), (74, CLINCH), (82, KB), (88, RK_CH), (95, RK_MID), (102, RK_BACK),
        (112, KB)], cam=dict(az=18)),
}

# ==========================================================================
# GÜREŞ
# ==========================================================================
WR = P(BASE_POSE, y=72, yaw=22, pitch=34, cpitch=12, chin=-6,
       lf=planted(26, -15, 12), rf=planted(-26, 20, 30),
       lh=(26, 30, -14), rh=(24, 28, 14), le=(-0.2, -1, -0.5), re=(-0.2, -1, 0.5))
WR_STEP = P(WR, x=4, lf=planted(32, -15, 12))
WR_LEVEL = P(WR, y=54, pitch=30, cpitch=10)


def knee_down(x, z, side_sign):
    """Dizi mindere inmiş bacak (bilek arkada, parmaklar yerde)."""
    return air((x, 8, z), yaw=0, pitch=70, knee=(0.6, -1, 0.08 * side_sign))


WR_PEN = P(WR, x=30, y=46, pitch=42, cpitch=6, lf=knee_down(16, -12, -1),
           rf=planted(-40, 22, 10, heel=60), lh=(30, 24, -14), rh=(28, 22, 14))
WR_PEN_UP = P(WR, x=30, y=66, pitch=36, lf=planted(56, -15, 12), rf=planted(-6, 20, 30))
WR_SHOT = P(WR_PEN, x=40, lhw=(86, 50, -15), rhw=(86, 50, 13), lhk=1, rhk=1, le=(-0.6, -0.4, -1), re=(-0.6, -0.4, 1))
WR_DRIVE = P(WR, x=66, y=60, pitch=52, cpitch=8, chin=-12, lf=planted(92, -15, 12), rf=planted(36, 20, 25, heel=45),
             lhw=(126, 58, -15), rhw=(126, 58, 13), lhk=1, rhk=1, le=(-0.6, -0.4, -1), re=(-0.6, -0.4, 1))
WR_SINGLE = P(WR_PEN, x=38, lhw=(84, 46, -2), rhw=(84, 58, 6), lhk=1, rhk=1, le=(-0.5, -0.4, -1), re=(-0.5, -0.4, 1))
WR_SINGLE_UP = P(WR, x=44, y=86, pitch=14, cpitch=6, chin=0, lf=planted(70, -15, 12), rf=planted(10, 18, 30),
                 lhw=(78, 104, -4), rhw=(80, 112, 8), lhk=1, rhk=1, le=(-0.4, -0.6, -1), re=(-0.4, -0.6, 1))
WR_SPRAWL = P(BASE_POSE, x=-4, y=34, pitch=72, cpitch=6, chin=-20, autoy=0,
              lhw=(46, 60, -18), rhw=(46, 60, 18), lhk=1, rhk=1, le=(-0.2, -1, -0.6), re=(-0.2, -1, 0.6),
              lf=planted(-96, -26, -10, heel=78), rf=planted(-96, 26, 10, heel=78))
WR_SPRAWL_HALF = P(WR, x=-2, y=54, pitch=55, lf=planted(-30, -22, 0, heel=40), rf=planted(-60, 24, 10, heel=60))
QUAD = P(BASE_POSE, y=52, pitch=88, cpitch=0, look=0, hpitch=-55, autoy=0,
         lhw=(44, 4, -18), rhw=(44, 4, 18), lhk=1, rhk=1, le=(-0.2, -1, -0.3), re=(-0.2, -1, 0.3),
         lf=air((-42, 7, -13), yaw=180, pitch=0, knee=(0, -1, 0)), rf=air((-42, 7, 13), yaw=180, pitch=0,
                                                                         knee=(0, -1, 0)))
SIT_THROUGH = P(BASE_POSE, x=-10, y=16, pitch=-38, cpitch=4, look=0, hpitch=10, autoy=0,
                lhw=(-30, 4, -26), rhw=(-30, 4, 26), lhk=1, rhk=1, le=(-1, -0.2, -0.3), re=(-1, -0.2, 0.3),
                lf=planted(56, -14, -6), rf=planted(62, 12, 6))
SIT_MID = P(QUAD, x=0, y=36, pitch=40, hpitch=-30, lf=planted(20, -14, 0), rf=air((0, 10, 14), yaw=-60,
                                                                                  pitch=0, knee=(0.4, -0.6, 1)))
KNEEL = P(BASE_POSE, x=-6, y=52, pitch=8, cpitch=4, autoy=0, chin=-4,
          lf=planted(34, -13, 0), rf=air((-42, 7, 13), yaw=180, pitch=0, knee=(0, -1, 0)),
          lh=(6, -12, -20), rh=(6, -12, 20), le=(-1, -0.4, -0.4), re=(-1, -0.4, 0.4))
STAND_FROM_KNEEL = P(WR, x=6, y=80, pitch=20)
BRIDGE_LIE = P(BASE_POSE, y=12, pitch=-88, look=0, hpitch=-25, autoy=0, lh=(12, 22, 9), rh=(12, 22, -9),
               le=(0, -1, -1), re=(0, -1, 1), lf=planted(36, -13, 0), rf=planted(36, 13, 0))
BRIDGE_UP = P(BRIDGE_LIE, x=-2, y=44, pitch=-116, hpitch=-62)
HF_A = P(WR, lhw=(52, 104, -12), lhk=1, rh=(28, 26, 12), le=(-0.2, -1, -0.8))
HF_B = P(WR, rhw=(54, 102, 10), rhk=1, lh=(26, 28, -14), re=(-0.2, -1, 0.8))
SNAP_REACH = P(WR, y=78, pitch=26, lhw=(62, 138, -6), rhw=(58, 128, 8), lhk=1, rhk=1,
               le=(-0.2, -1, -0.8), re=(-0.2, -1, 0.8))
SNAP = P(WR, x=-14, y=70, pitch=40, lf=planted(10, -15, 12), rf=planted(-42, 20, 30),
         lhw=(42, 94, -6), rhw=(40, 88, 8), lhk=1, rhk=1, le=(-0.2, -1, -0.8), re=(-0.2, -1, 0.8))
OPP_SNAPPED = P(WR, x=18, y=62, pitch=66, cpitch=12, chin=-30, lf=planted(46, -15, 12),
                lh=(30, 10, -14), rh=(28, 8, 14))
OPP_LIFTED = P(WR, x=-26, y=104, pitch=-24, cpitch=-6, autoy=0, chin=-10,
               lf=air((-14, 22, -12), yaw=0, pitch=40, knee=(1, 0.3, 0)),
               rf=air((-16, 24, 12), yaw=0, pitch=40, knee=(1, 0.3, 0)),
               lh=(18, 52, -26), rh=(16, 54, 26), le=(0, 0.3, -1), re=(0, 0.3, 1))
OPP_LEG_HELD = P(WR, x=-6, y=86, pitch=6, cpitch=0, chin=-4,
                 lf=planted(-18, -15, 12), rf=air((42, 86, 18), yaw=0, pitch=30, knee=(1, 0.2, 0)),
                 lh=(16, 40, -28), rh=(16, 44, 28), le=(0, 0.3, -1), re=(0, 0.3, 1))
WR_PARTNER_STAND = P(WR, y=78, pitch=26)
OPP_PUSHED = P(WR, x=-22, y=80, pitch=-12, cpitch=-10, chin=-6, lf=planted(-8, -15, 12), rf=planted(-46, 20, 30),
               lh=(18, 40, -26), rh=(16, 42, 26), le=(0, 0.2, -1), re=(0, 0.2, 1))
OPP_SEATED = P(BASE_POSE, x=-36, y=16, pitch=-52, cpitch=10, autoy=0, look=0, hpitch=20,
               lf=planted(16, -16, -8), rf=planted(22, 16, 8),
               lhw=(-60, 4, -24), rhw=(-60, 4, 24), lhk=1, rhk=1, le=(-1, -0.2, -0.3), re=(-1, -0.2, 0.3))
WR_TOP = P(WR, x=72, y=60, pitch=50, cpitch=8, chin=-10, lf=planted(100, -22, 10), rf=planted(48, 22, 20, heel=40),
           lhw=(120, 28, -16), rhw=(120, 28, 16), lhk=1, rhk=1, le=(-0.4, -1, -0.6), re=(-0.4, -1, 0.6))

WRESTLING = {
    "wr_stance": Move("wrestling", 60, [(0, WR), (15, WR_STEP), (30, P(WR, y=70)), (45, WR_STEP)], cam=dict(az=24)),
    "wr_level_change": Move("wrestling", 40, [(0, WR), (14, WR_LEVEL), (20, WR_LEVEL), (32, WR)], cam=dict(az=16)),
    "wr_penetration": Move("wrestling", 70, [(0, WR), (12, WR_LEVEL), (24, WR_PEN), (30, WR_PEN), (44, WR_PEN_UP),
                                             (58, P(WR, x=30))], cam=dict(az=18), target="partner", opp_dist=150,
                           opp=[(0, WR_PARTNER_STAND), (35, P(WR_PARTNER_STAND, x=-3))],
                           trails=[("head", 12, 26)]),
    "wr_double_leg": Move("wrestling", 80, [(0, WR), (10, WR_LEVEL), (22, WR_SHOT), (28, WR_SHOT), (40, WR_DRIVE),
                                            (52, WR_TOP), (60, WR_TOP), (70, P(WR, x=20))], cam=dict(az=20),
                          target="partner", opp_dist=118,
                          opp=[(0, WR_PARTNER_STAND), (22, WR_PARTNER_STAND),
                               (28, P(WR_PARTNER_STAND, pitch=10, y=82)), (40, OPP_PUSHED), (52, OPP_SEATED),
                               (60, OPP_SEATED), (70, WR_PARTNER_STAND)],
                          trails=[("head", 10, 24)]),
    "wr_single_leg": Move("wrestling", 76, [(0, WR), (10, WR_LEVEL), (22, WR_SINGLE), (28, WR_SINGLE),
                                            (44, WR_SINGLE_UP), (54, WR_SINGLE_UP), (66, P(WR, x=20))],
                          cam=dict(az=20), target="partner", opp_dist=118,
                          opp=[(0, WR_PARTNER_STAND), (24, WR_PARTNER_STAND), (44, OPP_LEG_HELD), (54, OPP_LEG_HELD),
                               (66, WR_PARTNER_STAND)], trails=[("head", 10, 24)]),
    "wr_sprawl": Move("wrestling", 48, [(0, WR), (8, WR_SPRAWL_HALF), (13, WR_SPRAWL), (26, WR_SPRAWL), (38, WR)],
                      cam=dict(az=18), target="partner", opp_dist=150,
                      opp=[(0, WR_PARTNER_STAND), (8, P(WR_SHOT, lhw=(70, 50, -14), rhw=(70, 50, 14))),
                           (14, P(WR_PEN, x=46, y=30, pitch=78, chin=-35, lhw=(70, 4, -22), rhw=(70, 4, 22),
                                  lhk=1, rhk=1)), (26, P(WR_PEN, x=46, y=30, pitch=78, chin=-35,
                                                         lhw=(70, 4, -22), rhw=(70, 4, 22), lhk=1, rhk=1)),
                           (38, WR_PARTNER_STAND)]),
    "wr_bridge": Move("wrestling", 64, [(0, BRIDGE_LIE), (24, BRIDGE_UP), (38, BRIDGE_UP)], cam=dict(az=10, el=10)),
    "wr_hand_fight": Move("wrestling", 48, [(0, WR), (10, HF_A), (20, WR), (32, HF_B), (42, WR)], cam=dict(az=22),
                          target="partner", opp_dist=112,
                          opp=[(0, WR), (10, HF_B), (20, WR), (32, HF_A), (42, WR)]),
    "wr_snap_down": Move("wrestling", 46, [(0, WR), (9, SNAP_REACH), (16, SNAP), (24, SNAP), (36, WR)],
                         cam=dict(az=20), target="partner", opp_dist=112,
                         opp=[(0, WR_PARTNER_STAND), (9, WR_PARTNER_STAND), (16, OPP_SNAPPED), (24, OPP_SNAPPED),
                              (36, WR_PARTNER_STAND)]),
    "wr_sit_out": Move("wrestling", 64, [(0, QUAD), (12, SIT_MID), (24, SIT_THROUGH), (38, SIT_THROUGH),
                                         (50, SIT_MID)], cam=dict(az=24, el=10)),
    "wr_stand_up": Move("wrestling", 70, [(0, QUAD), (16, KNEEL), (32, STAND_FROM_KNEEL), (44, WR),
                                          (58, KNEEL)], cam=dict(az=22, el=8)),
    "wr_shadow": Move("wrestling", 120, [(0, WR), (10, HF_A), (18, WR), (30, WR_LEVEL), (42, WR_PEN),
                                         (48, WR_PEN), (62, WR_PEN_UP), (74, WR), (84, WR_SPRAWL_HALF),
                                         (90, WR_SPRAWL), (98, WR_SPRAWL), (110, WR)], cam=dict(az=18)),
}

# ==========================================================================
# TEKVANDO
# ==========================================================================
TKD_G = P(BASE_POSE, y=94, yaw=48, pitch=2, cpitch=4, chin=6,
          lf=planted(26, -6, 28), rf=planted(-26, 12, 62, heel=24),
          lh=(22, 30, -12), rh=(14, 27, 8), le=(-0.2, -1, -0.4), re=(-0.2, -1, 0.4))
TKD_BOUNCE = P(TKD_G, y=97, lf=planted(26, -6, 28, heel=20), rf=planted(-26, 12, 62, heel=34))
READY = P(STAND, lf=planted(4, -15, -10), rf=planted(4, 15, 10), lh=(16, -6, -10), rh=(16, -6, 10),
          le=(-0.3, -1, -0.7), re=(-0.3, -1, 0.7), look=0)
WALK = dict(y=96, lf=planted(32, -10, 0), rf=planted(-26, 10, 20), look=0)
FRONT = dict(y=84, lf=planted(48, -10, 0), rf=planted(-40, 12, 22), look=0)
BACK = dict(x=-10, y=86, yaw=70, lf=planted(24, -2, 0), rf=planted(-32, 6, 90), look=1)
LOW_BLOCK_L = dict(lh=(30, -44, -16), le=(0, -1, -1))
LOW_PREP_L = dict(lh=(12, 30, 12), le=(0, -1, -0.4), rh=(30, -28, 2))
MID_BLOCK_L = dict(lh=(26, 30, -2), le=(0.3, -1, -0.1))
MID_PREP_L = dict(lh=(-2, 44, -26), le=(-0.3, -1, -1))
HIGH_BLOCK_L = dict(lh=(14, 60, -6), le=(0.7, 0.3, -1))
HIGH_PREP_L = dict(lh=(18, -6, 10), le=(0, -1, -0.3))
AP_SEOGI = P(STAND, **WALK, **LOW_BLOCK_L, **CHAMBER_R)
AP_KUBI = P(STAND, **FRONT, **LOW_BLOCK_L, **CHAMBER_R)
DWIT_KUBI = P(STAND, **BACK, **MID_BLOCK_L, **CHAMBER_R)
PUNCH_BASE_L = P(STAND, **FRONT, **CHAMBER_L, **CHAMBER_R)
PUNCH_L = hand_at(P(PUNCH_BASE_L, cyaw=8, **CHAMBER_R), "l", (54, -14, 14))
PUNCH_R = hand_at(P(PUNCH_BASE_L, cyaw=-8, **CHAMBER_L), "r", (54, -14, -14))
WALK_PUNCH_R = hand_at(P(STAND, **WALK, cyaw=-8, **CHAMBER_L), "r", (54, -10, -14))
TKD_CH_R = P(TKD_G, yaw=30, rf=air((22, 62, 10), yaw=20, pitch=0, knee=(1, 0.5, 0)), lf=planted(26, -6, 20, heel=12))
AP_CHAGI = P(TKD_G, yaw=24, pitch=-8, lf=planted(26, -6, 16, heel=18), rf=air((78, 112, 4), yaw=0, pitch=-40,
                                                                            knee=(1, 0.2, 0)))
DOLLYO_CH = P(TKD_G, yaw=-10, roll=-6, lf=planted(26, -6, -40, heel=20),
              rf=air((10, 70, 24), yaw=-40, pitch=40, knee=(0.8, 0.6, 0.4)))
DOLLYO = P(TKD_G, yaw=-72, pitch=-8, roll=-16, cyaw=10, lf=planted(26, -6, -100, heel=28),
           rf=air((66, 112, -2), yaw=-12, pitch=45, knee=(0, 1, 0.4)), rhw=(-20, 112, 34), rhk=1)
YEOP_CH = P(TKD_G, yaw=88, roll=6, rf=planted(-26, 12, 120, heel=10),
            lf=air((26, 70, -2), yaw=90, pitch=0, knee=(1, 0.7, 0)))
YEOP = P(TKD_G, yaw=90, roll=26, x=-4, rf=planted(-26, 12, 126, heel=12),
         lf=air((88, 102, 0), yaw=90, pitch=-8, knee=(0, 1, -0.6)), lh=(20, 30, -8))
DWI_TURN = P(TKD_G, yaw=130, lf=planted(26, -6, 140, heel=20), rf=planted(-26, 12, 120, heel=40))
DWI = P(TKD_G, yaw=196, pitch=34, cpitch=6, lf=planted(26, -6, 196, heel=10),
        rf=air((78, 106, 2), yaw=180, pitch=75, knee=(0, -1, 0)), lh=(16, 26, -12), rh=(12, 24, 10))
NAERYO_UP = P(TKD_G, yaw=20, pitch=-14, lf=planted(26, -6, 20, heel=20),
              rf=air((34, 190, 6), yaw=0, pitch=-40, knee=(1, 0, 0)))
NAERYO_DOWN = P(TKD_G, yaw=20, pitch=-4, lf=planted(26, -6, 20, heel=10),
                rf=air((66, 112, 4), yaw=0, pitch=-10, knee=(1, 0, 0)))
TKD_SWITCH = P(TKD_G, yaw=-48, lf=planted(-26, -12, -62, heel=24), rf=planted(26, 6, -28),
               lh=(14, 27, -8), rh=(22, 30, 12))
TKD_PARTNER = TKD_G

TAEKWONDO = {
    "tkd_ap_seogi": Move("taekwondo", 64, [(0, READY), (18, AP_SEOGI), (44, AP_SEOGI)], cam=dict(az=38)),
    "tkd_ap_kubi": Move("taekwondo", 64, [(0, READY), (18, AP_KUBI), (44, AP_KUBI)], cam=dict(az=38)),
    "tkd_dwit_kubi": Move("taekwondo", 64, [(0, READY), (18, DWIT_KUBI), (44, DWIT_KUBI)], cam=dict(az=30)),
    "tkd_jireugi": Move("taekwondo", 44, [(0, PUNCH_R), (10, PUNCH_L), (20, PUNCH_L), (32, PUNCH_R)],
                        cam=dict(az=28), target="partner", opp=[(0, TKD_PARTNER)],
                        hits=[(10, "lhand"), (32, "rhand")]),
    "tkd_arae_makgi": Move("taekwondo", 50, [(0, P(AP_KUBI, **LOW_PREP_L)), (12, AP_KUBI), (30, AP_KUBI)],
                           cam=dict(az=32), target="partner", opp_dist=150,
                           opp=[(0, TKD_PARTNER), (6, TKD_CH_R), (12, AP_CHAGI), (18, AP_CHAGI), (28, TKD_CH_R),
                                (38, TKD_PARTNER)]),
    "tkd_momtong_makgi": Move("taekwondo", 50, [(0, P(AP_KUBI, **MID_PREP_L)), (12, P(AP_KUBI, **MID_BLOCK_L)),
                                                (30, P(AP_KUBI, **MID_BLOCK_L))], cam=dict(az=32),
                              target="partner", opp_dist=122,
                              opp=[(0, TKD_PARTNER), (12, hand_at(P(TKD_PARTNER, yaw=10, cyaw=-8), "r", (56, -18, -14))),
                                   (20, hand_at(P(TKD_PARTNER, yaw=10, cyaw=-8), "r", (56, -18, -14))),
                                   (32, TKD_PARTNER)]),
    "tkd_olgul_makgi": Move("taekwondo", 50, [(0, P(AP_KUBI, **HIGH_PREP_L)), (12, P(AP_KUBI, **HIGH_BLOCK_L)),
                                              (30, P(AP_KUBI, **HIGH_BLOCK_L))], cam=dict(az=32),
                            target="partner", opp_dist=118,
                            opp=[(0, TKD_PARTNER), (12, hand_at(P(TKD_PARTNER, yaw=10, cyaw=-8), "r", (54, 10, -14))),
                                 (20, hand_at(P(TKD_PARTNER, yaw=10, cyaw=-8), "r", (54, 10, -14))),
                                 (32, TKD_PARTNER)]),
    "tkd_ap_chagi": Move("taekwondo", 44, [(0, TKD_G), (9, TKD_CH_R), (15, AP_CHAGI), (19, AP_CHAGI),
                                           (25, TKD_CH_R), (34, TKD_G)], cam=dict(az=20), target="partner",
                         opp=[(0, TKD_PARTNER)], hits=[(15, "rball")]),
    "tkd_dollyo_chagi": Move("taekwondo", 44, [(0, TKD_G), (8, DOLLYO_CH), (15, DOLLYO), (19, DOLLYO),
                                               (26, DOLLYO_CH), (36, TKD_G)], cam=dict(az=18), target="partner",
                             opp=[(0, TKD_PARTNER)], hits=[(15, "rankle")]),
    "tkd_yeop_chagi": Move("taekwondo", 48, [(0, TKD_G), (10, YEOP_CH), (17, YEOP), (22, YEOP), (29, YEOP_CH),
                                             (38, TKD_G)], cam=dict(az=18), target="partner",
                           opp=[(0, TKD_PARTNER)], hits=[(17, "lheel")]),
    "tkd_dwi_chagi": Move("taekwondo", 56, [(0, TKD_G), (10, DWI_TURN), (19, DWI), (24, DWI), (33, DWI_TURN),
                                            (44, TKD_G)], cam=dict(az=16), target="partner",
                          opp=[(0, TKD_PARTNER)], hits=[(19, "rheel")]),
    "tkd_naeryo_chagi": Move("taekwondo", 52, [(0, TKD_G), (15, NAERYO_UP), (19, NAERYO_UP), (25, NAERYO_DOWN),
                                               (30, NAERYO_DOWN), (42, TKD_G)], cam=dict(az=18), target="partner",
                             opp=[(0, TKD_PARTNER)], hits=[(25, "rheel")]),
    "tkd_footwork": Move("taekwondo", 48, [(0, TKD_G), (6, TKD_BOUNCE), (12, P(TKD_G, x=10)), (18, P(TKD_BOUNCE, x=10)),
                                           (24, P(TKD_SWITCH, x=10)), (30, P(TKD_BOUNCE, x=6)), (36, P(TKD_G, x=0)),
                                           (42, TKD_BOUNCE)], cam=dict(az=24)),
    "tkd_taegeuk1": Move("taekwondo", 150, [
        (0, READY),
        (14, turn(AP_SEOGI, -90)), (26, turn(AP_SEOGI, -90)),
        (40, shift(turn(WALK_PUNCH_R, -90), dz=-30)),
        (56, shift(turn(AP_SEOGI, 90), dz=-30)), (66, shift(turn(AP_SEOGI, 90), dz=-30)),
        (80, turn(WALK_PUNCH_R, 90)),
        (96, AP_KUBI), (106, PUNCH_R),
        (122, P(AP_KUBI, **HIGH_BLOCK_L)), (136, READY)], cam=dict(az=36)),
}
