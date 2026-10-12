#!/usr/bin/env python3
"""FightEdu Lottie animasyon üreticisi.

Her hareket, bir "iskelet figür"ün eklem açılarıyla tanımlanan anahtar pozlarından
oluşur. Script bu pozları Lottie formatına (parent'lı shape layer'lar + rotasyon
keyframe'leri) çevirir ve app/src/main/assets/lottie/<move_id>.json olarak yazar.

Açı kuralı (derece, mutlak/dünya koordinatı):
    0 = yukarı, 90 = ileri (sağ, figürün baktığı yön), 180 = aşağı, 270 = geri.
Poz anahtarları:
    t   : gövde (kalça -> boyun)
    fua, ffa : ön kol üst / ön kol alt (ön = izleyiciye yakın, öndeki taraf)
    bua, bfa : arka kol üst / alt
    fth, fsh : ön uyluk / ön baldır
    bth, bsh : arka uyluk / baldır
    dx  : kalçanın yatay kayması (px)
    lift: yerden yükseklik (zıplama) (px)
Figür her keyframe'de en alçak noktası zemine değecek şekilde otomatik yerleştirilir.

Kullanım:  python3 tools/lottie_gen/generate.py [--out DIR] [--only move_id ...]
Tasarımcı yapımı bir Lottie dosyası aynı isimle assets/lottie altına konarak
üretilen dosyanın yerine kullanılabilir.
"""
import argparse
import json
import math
import os
import sys

FPS = 30
W, H = 400, 400
GROUND = 370
CENTER_X = 200

TORSO, NECK, HEAD_R = 92, 7, 19
UPPER_ARM, FOREARM = 50, 48
THIGH, SHIN = 64, 62
SHOULDER_DROP = 4  # omuz, boyun noktasının biraz altında

LIMB_W, TORSO_W = 14, 19

DARK = "#37474F"
LIGHT = "#90A4AE"

SPORT_STYLE = {
    "general": {"accent": "#EF6C00", "gloves": False},
    "boxing": {"accent": "#D32F2F", "gloves": True},
    "kickboxing": {"accent": "#1565C0", "gloves": True},
    "wrestling": {"accent": "#2E7D32", "gloves": False},
    "taekwondo": {"accent": "#6A1B9A", "gloves": False},
}

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


def M(sport, base, dur, keys, x=CENTER_X):
    """keys: [(frame, overrides_dict)], overrides base üzerine uygulanır."""
    return {"sport": sport, "base": base, "dur": dur, "keys": keys, "x": x}


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
        (32, LHOOK), (37, LHOOK), (48, {})]),
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
        (0, {}), (7, JAB), (12, dict(t=8)), (19, CROSS), (24, dict(t=12)), (31, LHOOK),
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
        (27, dict(bth=135, bsh=138, t=0, fth=180, fsh=182)), (40, {})]),
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
# Kinematik
# --------------------------------------------------------------------------
POSE_KEYS = ["t", "fua", "ffa", "bua", "bfa", "fth", "fsh", "bth", "bsh", "dx", "lift"]


def vec(angle_deg, length):
    a = math.radians(angle_deg)
    return math.sin(a) * length, -math.cos(a) * length


def add(p, q):
    return p[0] + q[0], p[1] + q[1]


def joints(pose):
    """Kalça (0,0) iken tüm eklem noktaları."""
    hip = (0.0, 0.0)
    neck = vec(pose["t"], TORSO)
    shoulder = vec(pose["t"], TORSO - SHOULDER_DROP)
    head_c = add(neck, vec(pose["t"], NECK + HEAD_R))
    pts = {"hip": hip, "neck": neck, "head": head_c}
    for side in ("f", "b"):
        elbow = add(shoulder, vec(pose[side + "ua"], UPPER_ARM))
        hand = add(elbow, vec(pose[side + "fa"], FOREARM))
        knee = add(hip, vec(pose[side + "th"], THIGH))
        foot = add(knee, vec(pose[side + "sh"], SHIN))
        pts.update({side + "elbow": elbow, side + "hand": hand, side + "knee": knee, side + "foot": foot})
    return pts


def lowest_y(pose):
    pts = joints(pose)
    ys = [y + LIMB_W / 2 for k, (x, y) in pts.items() if k != "head"]
    ys.append(pts["head"][1] + HEAD_R)
    return max(ys)


def hip_position(pose, base_x):
    return [round(base_x + pose["dx"], 1), round(GROUND - lowest_y(pose) - pose["lift"], 1)]


# --------------------------------------------------------------------------
# Lottie üretimi
# --------------------------------------------------------------------------
def rgba(hex_color):
    h = hex_color.lstrip("#")
    return [round(int(h[i:i + 2], 16) / 255, 4) for i in (0, 2, 4)] + [1]


EASE_OUT = {"x": [0.42], "y": [0]}
EASE_IN = {"x": [0.58], "y": [1]}


def animated(frames_values, dims, linear=False):
    """frames_values: [(frame, value)] -> Lottie animated property."""
    uniq = []
    for f, v in frames_values:
        if uniq and uniq[-1][0] == f:
            uniq[-1] = (f, v)
        else:
            uniq.append((f, v))
    if all(v == uniq[0][1] for _, v in uniq):
        val = uniq[0][1]
        return {"a": 0, "k": val if dims > 1 else val[0]}
    kfs = []
    for i, (f, v) in enumerate(uniq):
        kf = {"t": f, "s": v}
        if i < len(uniq) - 1:
            kf["o"] = LINEAR_OUT if linear else EASE_OUT
            kf["i"] = LINEAR_IN if linear else EASE_IN
        kfs.append(kf)
    return {"a": 1, "k": kfs}


def bezier_ease(u, x1=0.42, y1=0.0, x2=0.58, y2=1.0):
    """Lottie'nin uyguladığı cubic-bezier easing (EASE_OUT/EASE_IN ile aynı)."""
    def coord(s, a, b):
        return 3 * a * s * (1 - s) ** 2 + 3 * b * s * s * (1 - s) + s ** 3
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if coord(mid, x1, x2) < u:
            lo = mid
        else:
            hi = mid
    return coord((lo + hi) / 2, y1, y2)


def dense_hip_track(keys, base_x, step=2):
    """Kalça konumu: eklemlerle aynı easing'le ara pozları hesaplayıp zemine oturtur,
    böylece geçişlerde ayaklar zemine girmez. Doğrusal keyframe'ler olarak döner."""
    out = []
    for (f0, p0), (f1, p1) in zip(keys, keys[1:]):
        f = f0
        while f < f1:
            e = bezier_ease((f - f0) / (f1 - f0))
            pose = {k: p0[k] + (p1[k] - p0[k]) * e for k in POSE_KEYS}
            out.append((f, hip_position(pose, base_x) + [0]))
            f += step
    out.append((keys[-1][0], hip_position(keys[-1][1], base_x) + [0]))
    return out


LINEAR_OUT = {"x": [0], "y": [0]}
LINEAR_IN = {"x": [1], "y": [1]}


def static(v):
    return {"a": 0, "k": v}


def transform(p, r, a=(0, 0)):
    return {
        "o": static(100),
        "r": r,
        "p": p,
        "a": static([a[0], a[1], 0]),
        "s": static([100, 100, 100]),
    }


def group_transform():
    return {"ty": "tr", "p": static([0, 0]), "a": static([0, 0]), "s": static([100, 100]),
            "r": static(0), "o": static(100), "sk": static(0), "sa": static(0), "nm": "Transform"}


def line_shape(length, width, color):
    return [{
        "ty": "gr", "nm": "seg",
        "it": [
            {"ty": "sh", "nm": "path", "ks": static({"i": [[0, 0], [0, 0]], "o": [[0, 0], [0, 0]],
                                                      "v": [[0, 0], [0, -length]], "c": False})},
            {"ty": "st", "nm": "stroke", "c": static(rgba(color)), "o": static(100), "w": static(width),
             "lc": 2, "lj": 2, "ml": 4},
            group_transform(),
        ],
    }]


def circle_shape(center, radius, color):
    return [{
        "ty": "gr", "nm": "circle",
        "it": [
            {"ty": "el", "nm": "ellipse", "p": static(list(center)), "s": static([radius * 2, radius * 2]), "d": 1},
            {"ty": "fl", "nm": "fill", "c": static(rgba(color)), "o": static(100), "r": 1},
            group_transform(),
        ],
    }]


class LayerBuilder:
    def __init__(self, dur):
        self.dur = dur
        self.layers = []
        self.next_ind = 1

    def add(self, name, ty, ks, shapes=None, parent=None, opacity=100):
        ind = self.next_ind
        self.next_ind += 1
        layer = {"ddd": 0, "ind": ind, "ty": ty, "nm": name, "sr": 1, "ks": ks, "ao": 0,
                 "ip": 0, "op": self.dur, "st": 0, "bm": 0}
        layer["ks"]["o"] = static(opacity)
        if parent is not None:
            layer["parent"] = parent
        if shapes is not None:
            layer["shapes"] = shapes
        self.layers.append(layer)
        return ind


def build_move(move_id, spec):
    sport = spec["sport"]
    style = SPORT_STYLE[sport]
    dur = spec["dur"]
    base = spec["base"]

    keys = [(f, P(base, **ov)) for f, ov in spec["keys"]]
    for f, pose in keys:
        missing = [k for k in POSE_KEYS if k not in pose]
        if missing:
            raise ValueError(f"{move_id}: frame {f} eksik anahtarlar {missing}")
    if keys[-1][0] != dur:
        keys.append((dur, keys[0][1]))
    if keys[0][0] != 0:
        raise ValueError(f"{move_id}: ilk keyframe 0 olmalı")

    def track(fn):
        return [(f, fn(p)) for f, p in keys]

    hip_track = dense_hip_track(keys, spec["x"])
    rot = {
        "torso": track(lambda p: [p["t"]]),
        "fua": track(lambda p: [p["fua"] - p["t"]]),
        "ffa": track(lambda p: [p["ffa"] - p["fua"]]),
        "bua": track(lambda p: [p["bua"] - p["t"]]),
        "bfa": track(lambda p: [p["bfa"] - p["bua"]]),
        "fth": track(lambda p: [p["fth"]]),
        "fsh": track(lambda p: [p["fsh"] - p["fth"]]),
        "bth": track(lambda p: [p["bth"]]),
        "bsh": track(lambda p: [p["bsh"] - p["bth"]]),
    }

    lb = LayerBuilder(dur)
    # Layer sırası: önce listelenen en üstte çizilir. Parent ind'leri önceden bilmek için
    # önce iskeleti (sırasız) kurup sonra çizim sırasına diziyoruz.
    accent = style["accent"]
    hand_r = 10 if style["gloves"] else 6.5
    hand_color_f = accent if style["gloves"] else DARK
    hand_color_b = accent if style["gloves"] else LIGHT

    hip = lb.add("hip", 3, transform(animated(hip_track, 3, linear=True), static(0)))
    torso = lb.add("torso", 4, transform(static([0, 0, 0]), animated(rot["torso"], 1)),
                   line_shape(TORSO, TORSO_W, accent), parent=hip)
    head = lb.add("head", 4, transform(static([0, -TORSO, 0]), static(0)),
                  circle_shape((0, -(NECK + HEAD_R)), HEAD_R, DARK), parent=torso)
    sh_y = -(TORSO - SHOULDER_DROP)
    f_ua = lb.add("front_upper_arm", 4, transform(static([0, sh_y, 0]), animated(rot["fua"], 1)),
                  line_shape(UPPER_ARM, LIMB_W, DARK), parent=torso)
    f_fa = lb.add("front_forearm", 4, transform(static([0, -UPPER_ARM, 0]), animated(rot["ffa"], 1)),
                  line_shape(FOREARM, LIMB_W, DARK), parent=f_ua)
    f_hand = lb.add("front_hand", 4, transform(static([0, -FOREARM, 0]), static(0)),
                    circle_shape((0, 0), hand_r, hand_color_f), parent=f_fa)
    b_ua = lb.add("back_upper_arm", 4, transform(static([0, sh_y, 0]), animated(rot["bua"], 1)),
                  line_shape(UPPER_ARM, LIMB_W, LIGHT), parent=torso)
    b_fa = lb.add("back_forearm", 4, transform(static([0, -UPPER_ARM, 0]), animated(rot["bfa"], 1)),
                  line_shape(FOREARM, LIMB_W, LIGHT), parent=b_ua)
    b_hand = lb.add("back_hand", 4, transform(static([0, -FOREARM, 0]), static(0)),
                    circle_shape((0, 0), hand_r, hand_color_b), parent=b_fa)
    f_th = lb.add("front_thigh", 4, transform(static([0, 0, 0]), animated(rot["fth"], 1)),
                  line_shape(THIGH, LIMB_W + 1, DARK), parent=hip)
    f_sh = lb.add("front_shin", 4, transform(static([0, -THIGH, 0]), animated(rot["fsh"], 1)),
                  line_shape(SHIN, LIMB_W, DARK), parent=f_th)
    b_th = lb.add("back_thigh", 4, transform(static([0, 0, 0]), animated(rot["bth"], 1)),
                  line_shape(THIGH, LIMB_W + 1, LIGHT), parent=hip)
    b_sh = lb.add("back_shin", 4, transform(static([0, -THIGH, 0]), animated(rot["bsh"], 1)),
                  line_shape(SHIN, LIMB_W, LIGHT), parent=b_th)
    shadow = lb.add("shadow", 4, transform(static([CENTER_X, GROUND + 2, 0]), static(0)), [{
        "ty": "gr", "nm": "shadow", "it": [
            {"ty": "el", "p": static([0, 0]), "s": static([170, 12]), "d": 1},
            {"ty": "fl", "c": static(rgba("#000000")), "o": static(12), "r": 1},
            group_transform(),
        ]}])
    ground = lb.add("ground", 4, transform(static([0, 0, 0]), static(0)), [{
        "ty": "gr", "nm": "ground", "it": [
            {"ty": "sh", "ks": static({"i": [[0, 0], [0, 0]], "o": [[0, 0], [0, 0]],
                                        "v": [[30, GROUND + 2], [W - 30, GROUND + 2]], "c": False})},
            {"ty": "st", "c": static(rgba("#B0BEC5")), "o": static(100), "w": static(3), "lc": 2, "lj": 2},
            group_transform(),
        ]}])

    by_ind = {layer["ind"]: layer for layer in lb.layers}
    draw_order = [f_hand, f_fa, f_ua, head, torso, f_sh, f_th, b_sh, b_th, b_hand, b_fa, b_ua,
                  hip, shadow, ground]
    layers = [by_ind[i] for i in draw_order]

    return {
        "v": "5.7.4", "fr": FPS, "ip": 0, "op": dur, "w": W, "h": H, "nm": move_id, "ddd": 0,
        "assets": [], "layers": layers, "markers": [],
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_out = os.path.normpath(os.path.join(here, "..", "..", "app", "src", "main", "assets", "lottie"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=default_out)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--check-content", action="store_true",
                        help="assets/content altındaki tüm hareketlerin animasyonu var mı kontrol et")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    ids = args.only or sorted(MOVES)
    for mid in ids:
        data = build_move(mid, MOVES[mid])
        with open(os.path.join(args.out, f"{mid}.json"), "w", encoding="utf-8") as fh:
            json.dump(data, fh, separators=(",", ":"))
    print(f"{len(ids)} animasyon yazıldı -> {args.out}")

    if args.check_content:
        content_dir = os.path.join(os.path.dirname(args.out), "content")
        missing = []
        for name in os.listdir(content_dir):
            if name.startswith("moves_"):
                with open(os.path.join(content_dir, name), encoding="utf-8") as fh:
                    for mv in json.load(fh):
                        if mv["id"] not in MOVES:
                            missing.append(mv["id"])
        if missing:
            print("Animasyonu olmayan hareketler:", ", ".join(missing))
            sys.exit(1)
        print("Tüm hareketlerin animasyonu mevcut.")


if __name__ == "__main__":
    main()
