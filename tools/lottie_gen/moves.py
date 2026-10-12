"""Hareket poz tanımları (eklem açıları). Açı kuralları için rig.py'ye bakın."""

CENTER_X = 200  # eski 400 px tuvalin ortası; M(x=...) değerleri buna göre kaydırmadır

# --------------------------------------------------------------------------
# Temel pozlar
# --------------------------------------------------------------------------
STAND = dict(t=0, fua=185, ffa=175, bua=187, bfa=177,
             fth=175, fsh=180, bth=188, bsh=190, dx=0, lift=0)

BOX = dict(t=8, fua=150, ffa=5, bua=170, bfa=8,
           fth=152, fsh=180, bth=203, bsh=212, dx=0, lift=0)
KB = dict(BOX, t=4, fth=162, fsh=180, bth=195, bsh=203)

WR = dict(t=45, fua=125, ffa=70, bua=135, bfa=75,
          fth=128, fsh=195, bth=200, bsh=228, dx=0, lift=0)

CHAMBER_F = dict(fua=195, ffa=100)       # ön yumruk belde
CHAMBER_B = dict(bua=197, bfa=102)       # arka yumruk belde
TKD = dict(t=0, fua=172, ffa=125, bua=176, bfa=128,
           fth=170, fsh=176, bth=192, bsh=190, dx=0, lift=0)
TKD_GUARD = dict(TKD, fua=155, ffa=20, bua=170, bfa=15, t=-3,
                 fth=165, fsh=178, bth=198, bsh=205)

# Sık kullanılan parçalar
JAB = dict(fua=90, ffa=90, t=14, dx=4)
CROSS = dict(bua=88, bfa=90, t=22, dx=6, bth=212, bsh=228, fua=155, ffa=0)
LHOOK = dict(fua=100, ffa=35, t=16, dx=3)
RHOOK = dict(bua=100, bfa=35, t=22, dx=4, bth=212, bsh=228)
LUPPER = dict(fua=125, ffa=0, t=12, fth=150, fsh=188, dx=3)
RUPPER = dict(bua=128, bfa=0, t=18, bth=210, bsh=226, dx=4)
SLIP = dict(t=28, fth=148, fsh=192, bth=200, bsh=228, dx=4)
ROLL = dict(t=38, fth=115, fsh=205, bth=168, bsh=236, dx=8)
BLOCK = dict(fua=175, ffa=-12, t=5)
PARRY = dict(bua=140, bfa=50)

QUAD = dict(t=70, fua=180, ffa=180, bua=182, bfa=182,
            fth=180, fsh=270, bth=182, bsh=270, dx=0, lift=0)
LYING = dict(t=270, fua=100, ffa=20, bua=105, bfa=25,
             fth=50, fsh=150, bth=55, bsh=152, dx=30, lift=0)
PLANK_UP = dict(t=63, fua=180, ffa=180, bua=182, bfa=182,
                fth=243, fsh=243, bth=245, bsh=245, dx=-20, lift=0)
SQUAT = dict(t=35, fth=95, fsh=195, bth=100, bsh=200,
             fua=90, ffa=90, bua=95, bfa=95)

WR_LEVEL = dict(t=40, fth=105, fsh=205, bth=172, bsh=258)
WR_PEN = dict(t=35, fth=175, fsh=265, bth=235, bsh=248, dx=30)
WR_SPRAWL = dict(t=72, fth=255, fsh=262, bth=258, bsh=265,
                 fua=100, ffa=150, bua=105, bfa=155)


def P(base, **kw):
    d = dict(base)
    d.update(kw)
    return d


def M(sport, base, dur, keys, x=CENTER_X, target=None, opp=None, opp_base=None, opp_dist=None):
    """Bir hareket tanımı.

    keys     : [(frame, overrides)] – overrides `base` üzerine uygulanır.
    x        : figürün yatay konum kaydırması (CENTER_X'e göre, eski 400 px tuval referansı).
    target   : None | "bag" | "long_bag" | "opponent" | "opponent_left"
    opp      : rakip için [(frame, overrides)] (opp_base üzerine). Rakip aynalanmış çizilir.
    opp_dist : rakibin kalçasının figürün kalçasına yatay uzaklığı (None = otomatik).
    """
    return {"sport": sport, "base": base, "dur": dur, "keys": keys, "x_shift": x - CENTER_X,
            "target": target, "opp": opp, "opp_base": opp_base, "opp_dist": opp_dist}


# --------------------------------------------------------------------------
# Hareket tanımları
# --------------------------------------------------------------------------
MOVES = {
    # ---------------- Genel ----------------
    "gen_jog": M("general", STAND, 30, [
        (0, dict(fth=95, fsh=185, bth=182, bsh=195, fua=210, ffa=130, bua=150, bfa=60, lift=4)),
        (15, dict(fth=180, fsh=192, bth=95, bsh=185, fua=150, ffa=60, bua=210, bfa=130, lift=4)),
    ]),
    "gen_arm_circles": M("general", STAND, 60, [
        (0, dict(fua=180, ffa=180, bua=0, bfa=0)),
        (15, dict(fua=90, ffa=90, bua=-90, bfa=-90)),
        (30, dict(fua=0, ffa=0, bua=-180, bfa=-180)),
        (45, dict(fua=-90, ffa=-90, bua=-270, bfa=-270)),
        (60, dict(fua=-180, ffa=-180, bua=-360, bfa=-360)),
    ]),
    "gen_squat": M("general", STAND, 50, [
        (0, {}), (20, SQUAT), (28, SQUAT),
    ]),
    "gen_jump_rope": M("general", STAND, 20, [
        (0, dict(fth=168, fsh=190, bth=172, bsh=192, fua=165, ffa=110, bua=168, bfa=112)),
        (10, dict(fth=176, fsh=184, bth=180, bsh=186, fua=172, ffa=135, bua=175, bfa=138, lift=14)),
    ]),
    "gen_pushup": M("general", PLANK_UP, 50, [
        (0, {}),
        (22, dict(t=80, fth=260, fsh=260, bth=262, bsh=262, fua=228, ffa=162, bua=230, bfa=164)),
        (28, dict(t=80, fth=260, fsh=260, bth=262, bsh=262, fua=228, ffa=162, bua=230, bfa=164)),
    ]),
    "gen_plank": M("general", PLANK_UP, 60, [
        (0, dict(t=77, fth=257, fsh=257, bth=258, bsh=258, fua=180, ffa=90, bua=182, bfa=92)),
        (30, dict(t=78, fth=256, fsh=256, bth=257, bsh=257, fua=180, ffa=90, bua=182, bfa=92, lift=2)),
    ]),
    "gen_situp": M("general", LYING, 50, [
        (0, {}),
        (20, dict(t=380, fua=210, ffa=130, bua=215, bfa=135)),
        (26, dict(t=380, fua=210, ffa=130, bua=215, bfa=135)),
    ]),
    "gen_stretch_hamstring": M("general", STAND, 80, [
        (0, {}),
        (25, dict(t=130, fua=170, ffa=100, bua=172, bfa=102, fth=172, bth=178, bsh=180)),
        (55, dict(t=135, fua=170, ffa=98, bua=172, bfa=100, fth=172, bth=178, bsh=180)),
    ]),
    "gen_stretch_quad": M("general", STAND, 60, [
        (0, dict(bth=180, bsh=12, bua=205, bfa=195, fua=100, ffa=95)),
        (30, dict(bth=182, bsh=10, bua=207, bfa=197, fua=96, ffa=90, t=2)),
    ]),
    "gen_stretch_shoulder": M("general", STAND, 60, [
        (0, dict(fua=90, ffa=90, bua=135, bfa=70)),
        (30, dict(fua=86, ffa=82, bua=130, bfa=62)),
    ]),
    "gen_burpee": M("general", STAND, 60, [
        (0, {}),
        (12, dict(t=45, fth=80, fsh=200, bth=85, bsh=205, fua=165, ffa=170, bua=168, bfa=172)),
        (24, PLANK_UP),
        (36, dict(t=45, fth=80, fsh=200, bth=85, bsh=205, fua=165, ffa=170, bua=168, bfa=172)),
        (48, dict(lift=26, fua=10, ffa=5, bua=15, bfa=10, fth=178, fsh=182, bth=184, bsh=188)),
    ]),

    # ---------------- Boks ----------------
    "box_stance": M("boxing", BOX, 60, [
        (0, {}),
        (30, dict(fth=155, fsh=186, bth=195, bsh=214, lift=0, t=10)),
    ]),
    "box_footwork": M("boxing", BOX, 60, [
        (0, dict(dx=-20)),
        (10, dict(dx=-8, fth=145, fsh=172)),
        (20, dict(dx=8)),
        (35, dict(dx=0, bth=210, bsh=222)),
        (48, dict(dx=-20)),
    ]),
    "box_jab": M("boxing", BOX, 36, [(0, {}), (8, JAB), (13, JAB), (24, {})]),
    "box_cross": M("boxing", BOX, 40, [(0, {}), (10, CROSS), (15, CROSS), (28, {})]),
    "box_lead_hook": M("boxing", BOX, 42, [
        (0, {}), (5, dict(fua=140, ffa=10, t=4)), (13, LHOOK), (18, LHOOK), (30, {})]),
    "box_rear_hook": M("boxing", BOX, 42, [
        (0, {}), (5, dict(t=4)), (13, RHOOK), (18, RHOOK), (30, {})]),
    "box_lead_uppercut": M("boxing", BOX, 42, [
        (0, {}), (6, dict(fth=148, fsh=192, fua=172, ffa=60, t=12)), (13, LUPPER), (18, LUPPER), (30, {})]),
    "box_rear_uppercut": M("boxing", BOX, 42, [
        (0, {}), (6, dict(bua=185, bfa=60, t=10, fth=150, fsh=190)), (13, RUPPER), (18, RUPPER), (30, {})]),
    "box_slip": M("boxing", BOX, 44, [(0, {}), (10, SLIP), (16, SLIP), (28, {})]),
    "box_roll": M("boxing", BOX, 56, [(0, {}), (16, ROLL), (24, ROLL), (40, {})]),
    "box_parry_block": M("boxing", BOX, 48, [
        (0, {}), (7, PARRY), (13, {}), (24, BLOCK), (32, BLOCK), (40, {})]),
    "box_combo_12": M("boxing", BOX, 48, [
        (0, {}), (7, JAB), (12, dict(t=10)), (19, CROSS), (24, CROSS), (36, {})]),
    "box_combo_123": M("boxing", BOX, 62, [
        (0, {}), (7, JAB), (12, dict(t=10)), (19, CROSS), (24, dict(t=14)),
        (32, P(LHOOK, dx=30)), (37, P(LHOOK, dx=30)), (48, {})]),
    "box_shadow": M("boxing", BOX, 120, [
        (0, dict(dx=-10)), (7, P(JAB, dx=-6)), (14, dict(dx=-8)), (21, CROSS), (30, dict(dx=0)),
        (40, SLIP), (50, dict(dx=0)), (58, LHOOK), (66, dict(dx=0)), (80, ROLL), (95, dict(dx=-5)),
        (102, P(RUPPER, dx=-3)), (110, dict(dx=-10)),
    ]),

    # ---------------- Kick Boks ----------------
    "kb_stance": M("kickboxing", KB, 60, [
        (0, {}), (30, dict(fth=158, fsh=184, bth=193, bsh=208, t=6)),
    ]),
    "kb_footwork": M("kickboxing", KB, 64, [
        (0, dict(dx=-18)), (10, dict(dx=-6, fth=148, fsh=172)), (20, dict(dx=8)),
        (34, dict(dx=0, bth=208, bsh=218)), (46, dict(dx=-18)),
    ]),
    "kb_jab_cross": M("kickboxing", KB, 48, [
        (0, {}), (7, JAB), (12, dict(t=8)), (19, CROSS), (24, CROSS), (36, {})]),
    "kb_teep": M("kickboxing", KB, 46, [
        (0, {}), (10, dict(fth=85, fsh=178, t=-4)), (17, dict(fth=80, fsh=82, t=-15, dx=4)),
        (22, dict(fth=80, fsh=82, t=-15, dx=4)), (29, dict(fth=88, fsh=180, t=-4)), (38, {})]),
    "kb_low_kick": M("kickboxing", KB, 48, [
        (0, {}), (8, dict(t=10, fth=172, fsh=180)),
        (18, dict(bth=118, bsh=106, t=-12, bua=215, bfa=200, fth=178, fsh=180)),
        (22, dict(bth=118, bsh=106, t=-12, bua=215, bfa=200, fth=178, fsh=180)),
        (30, dict(bth=150, bsh=215, t=0)), (40, {})]),
    "kb_middle_kick": M("kickboxing", KB, 50, [
        (0, {}), (8, dict(t=8, fth=172, fsh=180)),
        (19, dict(bth=85, bsh=80, t=-25, bua=220, bfa=205, fth=180, fsh=182)),
        (24, dict(bth=85, bsh=80, t=-25, bua=220, bfa=205, fth=180, fsh=182)),
        (32, dict(bth=140, bsh=220, t=0)), (42, {})]),
    "kb_high_kick": M("kickboxing", KB, 52, [
        (0, {}), (8, dict(t=8, fth=172, fsh=180)),
        (20, dict(bth=45, bsh=40, t=-42, bua=225, bfa=210, fth=182, fsh=182)),
        (25, dict(bth=45, bsh=40, t=-42, bua=225, bfa=210, fth=182, fsh=182)),
        (34, dict(bth=130, bsh=220, t=-5)), (44, {})]),
    "kb_knee": M("kickboxing", KB, 42, [
        (0, {}),
        (11, dict(bth=72, bsh=190, fua=120, ffa=150, bua=125, bfa=155, t=-5, fth=178, fsh=180)),
        (18, dict(bth=72, bsh=190, fua=125, ffa=160, bua=130, bfa=165, t=-5, fth=178, fsh=180)),
        (30, {})]),
    "kb_check": M("kickboxing", KB, 42, [
        (0, {}), (10, dict(fth=72, fsh=172, t=2, fua=175, ffa=-12, bth=186, bsh=190)),
        (22, dict(fth=72, fsh=172, t=2, fua=175, ffa=-12, bth=186, bsh=190)), (32, {})]),
    "kb_combo_jcl": M("kickboxing", KB, 66, [
        (0, {}), (7, JAB), (12, dict(t=8)), (19, CROSS), (24, dict(t=10, fth=172, fsh=180)),
        (34, dict(bth=118, bsh=106, t=-12, bua=215, bfa=200, fth=178, fsh=180)),
        (38, dict(bth=118, bsh=106, t=-12, bua=215, bfa=200, fth=178, fsh=180)),
        (46, dict(bth=150, bsh=215)), (54, {})]),
    "kb_combo_jcm": M("kickboxing", KB, 80, [
        (0, {}), (7, JAB), (12, dict(t=8)), (19, CROSS), (24, dict(t=12)), (31, P(LHOOK, dx=30)),
        (36, dict(t=8, fth=172, fsh=180)),
        (46, dict(bth=85, bsh=80, t=-25, bua=220, bfa=205, fth=180, fsh=182)),
        (50, dict(bth=85, bsh=80, t=-25, bua=220, bfa=205, fth=180, fsh=182)),
        (58, dict(bth=140, bsh=220)), (68, {})]),
    "kb_shadow": M("kickboxing", KB, 120, [
        (0, dict(dx=-8)), (7, JAB), (13, {}), (20, CROSS), (28, {}),
        (38, dict(fth=80, fsh=82, t=-15, dx=4)), (48, {}),
        (58, dict(bth=72, bsh=190, fua=120, ffa=150, bua=125, bfa=155, t=-5)), (68, {}),
        (80, dict(bth=85, bsh=80, t=-25, bua=220, bfa=205, fth=180, fsh=182)),
        (92, dict(bth=140, bsh=220)), (104, dict(dx=-8)),
    ]),

    # ---------------- Güreş ----------------
    "wr_stance": M("wrestling", WR, 60, [
        (0, dict(dx=-6)), (30, dict(dx=6, fth=124, fsh=198, t=47)),
    ]),
    "wr_level_change": M("wrestling", WR, 40, [
        (0, {}), (14, WR_LEVEL), (20, WR_LEVEL), (32, {})]),
    "wr_penetration": M("wrestling", WR, 70, [
        (0, {}), (12, WR_LEVEL), (24, WR_PEN), (30, WR_PEN),
        (44, dict(t=35, fth=100, fsh=190, bth=200, bsh=230, dx=30)), (58, dict(dx=30)),
    ], x=170),
    "wr_double_leg": M("wrestling", WR, 72, [
        (0, {}), (10, WR_LEVEL), (22, P(WR_PEN, fua=120, ffa=165, bua=125, bfa=168)),
        (28, P(WR_PEN, fua=120, ffa=165, bua=125, bfa=168)),
        (42, dict(t=28, dx=45, fth=150, fsh=185, bth=110, bsh=195, fua=125, ffa=60, bua=130, bfa=65)),
        (58, dict(dx=45)),
    ], x=165),
    "wr_single_leg": M("wrestling", WR, 72, [
        (0, {}), (10, WR_LEVEL), (22, P(WR_PEN, fua=125, ffa=170, bua=130, bfa=170)),
        (28, P(WR_PEN, fua=125, ffa=170, bua=130, bfa=170)),
        (44, dict(t=15, dx=35, fth=160, fsh=185, bth=200, bsh=215, fua=150, ffa=40, bua=155, bfa=45)),
        (52, dict(t=15, dx=35, fth=160, fsh=185, bth=200, bsh=215, fua=150, ffa=40, bua=155, bfa=45)),
        (62, dict(dx=35)),
    ], x=170),
    "wr_sprawl": M("wrestling", WR, 46, [
        (0, {}), (10, WR_SPRAWL), (24, WR_SPRAWL), (36, {})], x=220),
    "wr_bridge": M("wrestling", LYING, 64, [
        (0, {}),
        (24, dict(t=235, fth=115, fsh=180, bth=118, bsh=182, fua=65, ffa=-15, bua=70, bfa=-10)),
        (38, dict(t=235, fth=115, fsh=180, bth=118, bsh=182, fua=65, ffa=-15, bua=70, bfa=-10)),
    ], x=215),
    "wr_hand_fight": M("wrestling", WR, 48, [
        (0, {}), (10, dict(fua=100, ffa=80, bua=140, bfa=80)), (20, {}),
        (32, dict(fua=145, ffa=60, bua=105, bfa=85, dx=4)), (42, {})]),
    "wr_snap_down": M("wrestling", WR, 44, [
        (0, {}), (9, dict(fua=100, ffa=95, bua=105, bfa=100, t=38)),
        (16, dict(fua=170, ffa=150, bua=175, bfa=155, dx=-14, t=50)),
        (22, dict(fua=170, ffa=150, bua=175, bfa=155, dx=-14, t=50)), (34, {})]),
    "wr_sit_out": M("wrestling", QUAD, 64, [
        (0, {}),
        (22, dict(t=-20, fth=85, fsh=95, bth=80, bsh=92, bua=200, bfa=190, fua=120, ffa=90, dx=10)),
        (36, dict(t=-20, fth=85, fsh=95, bth=80, bsh=92, bua=200, bfa=190, fua=120, ffa=90, dx=10)),
    ], x=200),
    "wr_stand_up": M("wrestling", QUAD, 70, [
        (0, {}),
        (16, dict(t=5, fth=92, fsh=180, bth=180, bsh=270, fua=170, ffa=120, bua=175, bfa=125)),
        (34, dict(t=10, fth=168, fsh=180, bth=195, bsh=198, fua=170, ffa=120, bua=175, bfa=125)),
        (46, P(WR)),
    ]),
    "wr_shadow": M("wrestling", WR, 120, [
        (0, {}), (10, dict(fua=100, ffa=80)), (18, {}), (30, WR_LEVEL), (42, WR_PEN), (48, WR_PEN),
        (62, dict(dx=30)), (74, dict(dx=20)), (84, P(WR_SPRAWL, dx=10)), (94, P(WR_SPRAWL, dx=10)),
        (108, dict(dx=0)),
    ], x=180),

    # ---------------- Tekvando ----------------
    "tkd_ap_seogi": M("taekwondo", TKD, 64, [
        (0, dict(fth=178, fsh=180, bth=182, bsh=182)),
        (18, dict(fth=160, fsh=172, bth=200, bsh=198, fua=160, ffa=158, **CHAMBER_B)),
        (44, dict(fth=160, fsh=172, bth=200, bsh=198, fua=160, ffa=158, **CHAMBER_B)),
    ]),
    "tkd_ap_kubi": M("taekwondo", TKD, 64, [
        (0, dict(fth=178, fsh=180, bth=182, bsh=182)),
        (18, dict(fth=135, fsh=178, bth=225, bsh=225, t=5, fua=158, ffa=158, **CHAMBER_B)),
        (44, dict(fth=135, fsh=178, bth=225, bsh=225, t=5, fua=158, ffa=158, **CHAMBER_B)),
    ]),
    "tkd_dwit_kubi": M("taekwondo", TKD, 64, [
        (0, dict(fth=178, fsh=180, bth=182, bsh=182)),
        (18, dict(fth=148, fsh=158, bth=192, bsh=218, t=-6, fua=150, ffa=40, **CHAMBER_B)),
        (44, dict(fth=148, fsh=158, bth=192, bsh=218, t=-6, fua=150, ffa=40, **CHAMBER_B)),
    ]),
    "tkd_jireugi": M("taekwondo", TKD, 40, [
        (0, dict(bua=90, bfa=90, t=6, **CHAMBER_F)),
        (10, dict(fua=90, ffa=90, t=2, **CHAMBER_B)),
        (20, dict(fua=90, ffa=90, t=2, **CHAMBER_B)),
        (30, dict(bua=90, bfa=90, t=6, **CHAMBER_F)),
    ]),
    "tkd_arae_makgi": M("taekwondo", TKD, 48, [
        (0, dict(fua=150, ffa=-20, bua=150, bfa=150)),
        (12, dict(fua=160, ffa=160, **CHAMBER_B)),
        (30, dict(fua=160, ffa=160, **CHAMBER_B)),
    ]),
    "tkd_momtong_makgi": M("taekwondo", TKD, 48, [
        (0, dict(fua=230, ffa=-30, bua=120, bfa=95)),
        (12, dict(fua=150, ffa=45, **CHAMBER_B)),
        (30, dict(fua=150, ffa=45, **CHAMBER_B)),
    ]),
    "tkd_olgul_makgi": M("taekwondo", TKD, 48, [
        (0, dict(fua=175, ffa=125, bua=120, bfa=95)),
        (12, dict(fua=60, ffa=-30, **CHAMBER_B)),
        (30, dict(fua=60, ffa=-30, **CHAMBER_B)),
    ]),
    "tkd_ap_chagi": M("taekwondo", TKD_GUARD, 42, [
        (0, {}), (9, dict(bth=85, bsh=185, fth=176, fsh=180)),
        (15, dict(bth=78, bsh=72, t=-10, fth=178, fsh=180)),
        (19, dict(bth=78, bsh=72, t=-10, fth=178, fsh=180)),
        (25, dict(bth=85, bsh=185, fth=176, fsh=180)), (34, {})]),
    "tkd_dollyo_chagi": M("taekwondo", TKD_GUARD, 44, [
        (0, {}), (9, dict(bth=60, bsh=178, fth=178, fsh=180, t=-8)),
        (15, dict(bth=72, bsh=68, t=-28, fth=180, fsh=182, bua=215, bfa=200)),
        (19, dict(bth=72, bsh=68, t=-28, fth=180, fsh=182, bua=215, bfa=200)),
        (26, dict(bth=60, bsh=178, fth=178, fsh=180, t=-8)), (36, {})]),
    "tkd_yeop_chagi": M("taekwondo", TKD_GUARD, 48, [
        (0, {}), (10, dict(fth=60, fsh=200, t=-12, bth=186, bsh=188)),
        (17, dict(fth=86, fsh=86, t=-42, bth=190, bsh=190)),
        (22, dict(fth=86, fsh=86, t=-42, bth=190, bsh=190)),
        (29, dict(fth=60, fsh=200, t=-12, bth=186, bsh=188)), (38, {})]),
    "tkd_dwi_chagi": M("taekwondo", TKD_GUARD, 52, [
        (0, {}), (10, dict(t=20, bth=195, bsh=270, fth=176, fsh=180)),
        (18, dict(t=48, bth=275, bsh=277, fth=172, fsh=178)),
        (23, dict(t=48, bth=275, bsh=277, fth=172, fsh=178)),
        (31, dict(t=20, bth=195, bsh=270, fth=176, fsh=180)), (42, {})], x=230),
    "tkd_naeryo_chagi": M("taekwondo", TKD_GUARD, 52, [
        (0, {}), (15, dict(bth=8, bsh=4, t=-15, fth=180, fsh=182)),
        (19, dict(bth=8, bsh=4, t=-15, fth=180, fsh=182)),
        (24, dict(bth=34, bsh=40, t=-12, fth=180, fsh=182)),
        (30, dict(bth=135, bsh=138, t=0, fth=180, fsh=182)), (42, {})]),
    "tkd_footwork": M("taekwondo", TKD_GUARD, 40, [
        (0, dict(dx=-8)), (5, dict(dx=-4, lift=8)), (10, dict(dx=0)), (15, dict(dx=4, lift=8)),
        (20, dict(dx=8)), (25, dict(dx=4, lift=8)), (30, dict(dx=0)), (35, dict(dx=-4, lift=8)),
    ]),
    "tkd_taegeuk1": M("taekwondo", TKD, 132, [
        (0, dict(fth=178, fsh=180, bth=182, bsh=182, dx=-25)),
        (14, dict(fth=160, fsh=172, bth=200, bsh=198, fua=160, ffa=158, dx=-20, **CHAMBER_B)),
        (24, dict(fth=160, fsh=172, bth=200, bsh=198, fua=160, ffa=158, dx=-20, **CHAMBER_B)),
        (36, dict(fth=160, fsh=172, bth=200, bsh=198, bua=90, bfa=90, dx=-5, **CHAMBER_F)),
        (48, dict(fth=135, fsh=178, bth=225, bsh=225, fua=158, ffa=158, dx=5, **CHAMBER_B)),
        (60, dict(fth=135, fsh=178, bth=225, bsh=225, bua=90, bfa=90, dx=5, **CHAMBER_F)),
        (72, dict(fth=160, fsh=172, bth=200, bsh=198, fua=150, ffa=45, dx=10, **CHAMBER_B)),
        (84, dict(fth=160, fsh=172, bth=200, bsh=198, fua=60, ffa=-30, dx=10, **CHAMBER_B)),
        (96, dict(bth=78, bsh=72, t=-10, fth=178, fsh=180, fua=155, ffa=20, bua=170, bfa=15, dx=10)),
        (108, dict(fth=160, fsh=172, bth=200, bsh=198, fua=90, ffa=90, dx=20, **CHAMBER_B)),
        (120, dict(fth=178, fsh=180, bth=182, bsh=182, dx=0)),
    ]),
}

# --------------------------------------------------------------------------
# Hedefler ve rakip (antrenman partneri)
#   target: "bag" | "long_bag" | "opponent" | "opponent_left"
#   opp   : rakibin pozları (kendi yerel yönünde; ekranda aynalanır)
#   opp_dist: kalçalar arası uzaklık (None = vuruş erişiminden otomatik)
# --------------------------------------------------------------------------
KB_LOW = dict(bth=118, bsh=106, t=-12, bua=215, bfa=200, fth=178, fsh=180)
TKD_FRONT_KICK = dict(bth=78, bsh=72, t=-10, fth=178, fsh=180)
WR_SHOT = dict(t=35, fth=175, fsh=265, bth=235, bsh=248, dx=30, fua=120, ffa=165, bua=125, bfa=168)
WR_FLAT = dict(t=82, fth=205, fsh=268, bth=228, bsh=262, dx=34, fua=150, ffa=185, bua=155, bfa=188)
WR_LIFTED = dict(t=-22, dx=-38, lift=16, fth=168, fsh=176, bth=188, bsh=192, fua=55, ffa=25, bua=70, bfa=40)

TARGETS = {
    # Kum torbası – boks
    **{m: dict(target="bag") for m in [
        "box_jab", "box_cross", "box_lead_hook", "box_rear_hook", "box_lead_uppercut",
        "box_rear_uppercut", "box_combo_12", "box_combo_123"]},
    # Uzun (muz) torba – kick boks
    **{m: dict(target="long_bag") for m in [
        "kb_jab_cross", "kb_teep", "kb_low_kick", "kb_middle_kick", "kb_high_kick", "kb_knee",
        "kb_combo_jcl", "kb_combo_jcm"]},
    # Savunmalar: rakip saldırır
    "box_slip": dict(target="opponent", opp_dist=172, opp=[(0, {}), (10, JAB), (15, JAB), (26, {})]),
    "box_roll": dict(target="opponent", opp_dist=178, opp=[
        (0, {}), (8, dict(fua=140, ffa=10, t=4)), (17, LHOOK), (22, LHOOK), (34, {})]),
    "box_parry_block": dict(target="opponent", opp_dist=162, opp=[
        (0, {}), (7, JAB), (12, {}), (18, dict(fua=140, ffa=10, t=4)), (24, LHOOK), (31, LHOOK), (40, {})]),
    "kb_check": dict(target="opponent", opp_dist=135, opp=[
        (0, {}), (5, dict(t=10, fth=172, fsh=180)), (12, KB_LOW), (20, KB_LOW),
        (28, dict(bth=150, bsh=215)), (36, {})]),
    "tkd_arae_makgi": dict(target="opponent", opp_base=TKD_GUARD, opp_dist=150, opp=[
        (0, {}), (6, dict(bth=85, bsh=185, fth=176, fsh=180)), (12, TKD_FRONT_KICK), (18, TKD_FRONT_KICK),
        (26, dict(bth=85, bsh=185, fth=176, fsh=180)), (36, {})]),
    "tkd_momtong_makgi": dict(target="opponent", opp_base=TKD_GUARD, opp_dist=145, opp=[
        (0, {}), (12, dict(bua=98, bfa=100, t=12)), (20, dict(bua=98, bfa=100, t=12)), (32, {})]),
    "tkd_olgul_makgi": dict(target="opponent", opp_base=TKD_GUARD, opp_dist=148, opp=[
        (0, {}), (12, dict(bua=80, bfa=72, t=12)), (20, dict(bua=80, bfa=72, t=12)), (32, {})]),
    # Tekvando hücumları: göğüs koruyuculu rakip hedef
    **{m: dict(target="opponent", opp_base=TKD_GUARD) for m in [
        "tkd_jireugi", "tkd_ap_chagi", "tkd_dollyo_chagi", "tkd_yeop_chagi", "tkd_naeryo_chagi"]},
    "tkd_dwi_chagi": dict(target="opponent_left", opp_base=TKD_GUARD),
    # Güreş: partnerle
    "wr_penetration": dict(target="opponent", opp_dist=215, opp=[(0, dict(t=32)), (30, dict(t=34, dx=-3))]),
    "wr_double_leg": dict(target="opponent", opp_dist=190, opp=[
        (0, dict(t=30)), (22, dict(t=28)), (28, dict(t=22)), (42, WR_LIFTED), (52, WR_LIFTED), (64, dict(t=30))]),
    "wr_single_leg": dict(target="opponent", opp_dist=190, opp=[
        (0, dict(t=30)), (22, dict(t=28)), (30, dict(t=20, fth=120, fsh=150)),
        (44, dict(t=-8, dx=-8, fth=82, fsh=100, bth=184, bsh=186, fua=60, ffa=20, bua=75, bfa=35)),
        (52, dict(t=-8, dx=-8, fth=82, fsh=100, bth=184, bsh=186, fua=60, ffa=20, bua=75, bfa=35)),
        (64, dict(t=30))]),
    "wr_sprawl": dict(target="opponent", opp_dist=205, opp=[
        (0, {}), (8, WR_SHOT), (14, WR_FLAT), (24, WR_FLAT), (36, {})]),
    "wr_hand_fight": dict(target="opponent", opp_dist=170, opp=[
        (0, {}), (10, dict(fua=140, ffa=60, bua=100, bfa=85)), (20, {}),
        (32, dict(fua=100, ffa=80, bua=140, bfa=80)), (42, {})]),
    "wr_snap_down": dict(target="opponent", opp_dist=165, opp=[
        (0, {}), (9, dict(t=40)),
        (16, dict(t=75, dx=22, fua=150, ffa=172, bua=155, bfa=176, fth=110, fsh=200)),
        (22, dict(t=75, dx=22, fua=150, ffa=172, bua=155, bfa=176, fth=110, fsh=200)), (34, {})]),
}

for _mid, _extra in TARGETS.items():
    MOVES[_mid].update(_extra)

# Darbe anları: (kare, vuran nokta) – torba/rakip bu noktaya göre yerleşir
HITS = {
    "box_jab": [(8, 'ffist')],
    "box_cross": [(10, 'bfist')],
    "box_lead_hook": [(13, 'ffist')],
    "box_rear_hook": [(13, 'bfist')],
    "box_lead_uppercut": [(13, 'ffist')],
    "box_rear_uppercut": [(13, 'bfist')],
    "box_combo_12": [(7, 'ffist'), (19, 'bfist')],
    "box_combo_123": [(7, 'ffist'), (19, 'bfist'), (32, 'ffist')],
    "kb_jab_cross": [(7, 'ffist'), (19, 'bfist')],
    "kb_teep": [(17, 'ftoe')],
    "kb_low_kick": [(18, 'bankle')],
    "kb_middle_kick": [(19, 'bankle')],
    "kb_high_kick": [(20, 'bankle')],
    "kb_knee": [(11, 'bknee')],
    "kb_combo_jcl": [(7, 'ffist'), (19, 'bfist'), (34, 'bankle')],
    "kb_combo_jcm": [(7, 'ffist'), (19, 'bfist'), (31, 'ffist'), (46, 'bankle')],
    "tkd_jireugi": [(10, 'ffist'), (30, 'bfist')],
    "tkd_ap_chagi": [(15, 'btoe')],
    "tkd_dollyo_chagi": [(15, 'bankle')],
    "tkd_yeop_chagi": [(17, 'fheel')],
    "tkd_dwi_chagi": [(18, 'bheel')],
    "tkd_naeryo_chagi": [(24, 'bheel')],
}

for _mid, _hits in HITS.items():
    MOVES[_mid]["hits"] = _hits
