#!/usr/bin/env python3
"""Günlük antrenman programlarını üretir: app/src/main/assets/content/training_<spor>.json

Her spor 24 antrenman günü, 4 evre (6'şar gün); uygulama bunları 6 dinlenme günüyle 30 günlük meydan okumaya
yerleştirir (dinlenme seansı: rest_day.json). Bir gün: ısınma -> teknik raundu -> gölge -> ana raundlar
(torba / drill / tekme) -> kondisyon devresi -> esneme. Evre ilerledikçe raunt süresi ve sayısı artar.
Günlerin tema, koç notu ve hareket/komut listeleri aşağıda elle yazılmıştır; bu betik yalnızca blokları
kurar ve süreyi kontrol eder. Kullanım: python3 tools/content/make_training.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "app", "src", "main", "assets", "content"))

# evre parametreleri: raunt süresi, raunt dinlenmesi, gölge raunt, ana raunt
PHASE = [
    dict(work=120, rest=45, shadow=2, main=4),
    dict(work=120, rest=45, shadow=2, main=5),
    dict(work=180, rest=60, shadow=2, main=5),
    dict(work=180, rest=60, shadow=3, main=6),
]
COND = [
    ["gen_pushup", "gen_squat", "gen_plank"],
    ["gen_burpee", "gen_situp", "gen_squat"],
    ["gen_pushup", "gen_situp", "gen_burpee", "gen_plank"],
]
STRETCH = ["gen_stretch_shoulder", "gen_stretch_hamstring", "gen_stretch_quad"]


def R(kind, title, rounds, work, rest, moves, calls=(), cue=""):
    return dict(kind=kind, title=title, mode="round", rounds=rounds, work=work, rest=rest, moves=list(moves),
                calls=list(calls), cue=cue)


def C(kind, title, rounds, work, rest, moves, cue=""):
    return dict(kind=kind, title=title, mode="circuit", rounds=rounds, work=work, rest=rest, moves=list(moves),
                cue=cue)


def minutes(blocks):
    t = 0
    for i, b in enumerate(blocks):
        if b["mode"] == "round":
            n = b["rounds"]
            t += n * b["work"] + (n - 1) * b["rest"]
        else:
            n = b["rounds"] * len(b["moves"])
            t += n * b["work"] + (n - 1) * b["rest"]
        if i:
            t += max(b["rest"], 30)
    return t / 60


def day(sport, d, title, focus, tech, calls, main_moves, main_kind, main_title, warm, shadow_move, evaluate=False):
    p = (d - 1) // 6
    ph = PHASE[p]
    blocks = [warm(p)]
    if tech and not evaluate:
        blocks.append(R("technique", "Teknik", 3, 60, 30, tech, cue=f"Teknik raundu: {focus}"))
    blocks.append(R("shadow", "Gölge", ph["shadow"], ph["work"], ph["rest"], [shadow_move], calls,
                    cue="Gölge raundu. Komutları dinle, gardını hiç düşürme."))
    rounds = ph["main"] + (2 if evaluate else 0)
    blocks.append(R(main_kind, main_title, rounds, ph["work"], ph["rest"], main_moves, calls,
                    cue=f"{main_title}: {rounds} raunt. Komut gelince o tekniği at, aralarda ayak oyunu."))
    cond = COND[(d - 1) % 3]
    blocks.append(C("conditioning", "Kondisyon", 2 if p < 2 else 3, 40, 20, cond,
                    cue="Kondisyon devresi: her harekette 40 saniye, temiz form."))
    blocks.append(C("cooldown", "Esneme", 1, 40, 10, STRETCH, cue="Nefesini yavaşlat, esnemeleri zorlamadan yap."))
    m = minutes(blocks)
    # süre bandı: uzun günlerde kondisyonu kısalt
    while m > 58 and blocks[-2]["rounds"] > 1:
        blocks[-2]["rounds"] -= 1
        m = minutes(blocks)
    assert 20 <= m <= 60, (sport, d, m)
    return dict(day=d, title=title, focus=focus, blocks=blocks)


def rope_warm(p):
    return R("warmup", "İp atlama", 2 if p < 2 else 3, 120, 30, ["gen_jump_rope"],
             cue="Isınma: ip atla, omuzlar gevşek, ayak uçlarında.")


def mobility_warm(p):
    return C("warmup", "Isınma", 1, 60, 15, ["gen_jog", "gen_arm_circles", "gen_jump_rope"],
             cue="Isınma: yerinde koşu, kol çevirme ve ip.")


PHASE_INFO = {
    "boxing": [("Temeller", "Duruş, ayak oyunu, jab–cross ve temel savunma."),
               ("Kroşe ve Aparkat", "Dört yumruğu tamamla, kafa hareketini ekle."),
               ("Raunt Temposu", "3 dakikalık raundlarda saldırı ve savunmayı birleştir."),
               ("Ringe Hazırlık", "Kombinasyon akışı, karşı atak ve dayanıklılık.")],
    "kickboxing": [("Temeller", "Duruş, jab–cross, teep ve low kick."),
                   ("Tekme ve Diz", "Middle/high kick, diz ve tekme bloğu."),
                   ("Kombinasyonlar", "Yumruk–tekme zincirleri, 3 dakikalık raundlar."),
                   ("Dövüş Temposu", "Uzun raundlar, karşı atak ve dayanıklılık.")],
    "wrestling": [("Temeller", "Duruş, seviye değiştirme ve penetrasyon."),
                  ("Dalışlar", "Çift ve tek bacak dalışı, sprawl savunması."),
                  ("Bağlantılar", "El mücadelesi, snap down ve yer çıkışları."),
                  ("Maç Temposu", "Zincir drill, yüksek tempo ve dayanıklılık.")],
    "taekwondo": [("Temeller", "Duruşlar, jireugi ve alt/orta blok."),
                  ("Tekmeler", "Ön, yuvarlak ve yan tekme; ayak oyunu."),
                  ("İleri Tekmeler", "Geri ve balta tekmesi, üst blok, form."),
                  ("Form ve Tempo", "Taegeuk 1, tekme kombinasyonları, dayanıklılık.")],
}

# (başlık, koç notu, teknik hareketleri, komutlar, ana raunt hareketleri, değerlendirme?)
BOXING = [
    ("Duruş ve Jab", "Ağırlık ortada, çene içeride; jab omuzdan düz çıkar, aynı yoldan döner.",
     ["box_stance", "box_jab"], ["box_jab", "box_footwork"], ["box_jab"]),
    ("Cross ve 1-2", "Cross'ta arka ayak döner, kalça ve omuz birlikte; yumruk dönerken gard yüze.",
     ["box_cross", "box_combo_12"], ["box_jab", "box_combo_12"], ["box_combo_12", "box_cross"]),
    ("Blok ve Parry", "Gelen jab'ı arka elle sektir; blokta dirsekler kaburgada.",
     ["box_parry_block", "box_stance"], ["box_parry_block", "box_jab", "box_combo_12"], ["box_jab", "box_combo_12"]),
    ("Ayak Oyunu", "Önde giden ayak yönü belirler; adımlar kısa, ayaklar hiç çapraz geçmez.",
     ["box_footwork", "box_jab"], ["box_footwork", "box_jab", "box_combo_12"], ["box_combo_12"]),
    ("1-2 Torba Günü", "Her 1-2'den sonra çık ya da açı al; torbanın önünde durma.",
     ["box_combo_12", "box_footwork"], ["box_combo_12", "box_jab", "box_cross"], ["box_combo_12", "box_jab"]),
    ("Değerlendirme 1", "Temeller tamam: 6 raunt torba, temiz 1-2 ve ayak oyunu.",
     None, ["box_jab", "box_cross", "box_combo_12", "box_footwork"], ["box_combo_12", "box_jab"], True),
    ("Sol Kroşe", "Dirsek omuz hizasında, ön ayak içe döner; yumruk yatay bir yayla gelir.",
     ["box_lead_hook", "box_combo_123"], ["box_lead_hook", "box_combo_12", "box_combo_123"], ["box_lead_hook", "box_combo_123"]),
    ("Sağ Kroşe", "Arka ayak döner, kalça önce; sol eldiven yanakta kalır.",
     ["box_rear_hook", "box_lead_hook"], ["box_rear_hook", "box_jab", "box_lead_hook"], ["box_rear_hook", "box_combo_12"]),
    ("Aparkatlar", "Dizlerden yay, yumruk aşağıdan çeneye; kol savrulmaz, kısa ve sıkı.",
     ["box_lead_uppercut", "box_rear_uppercut"], ["box_lead_uppercut", "box_rear_uppercut", "box_combo_12"],
     ["box_lead_uppercut", "box_rear_uppercut"]),
    ("Slip ve Roll", "Slip'te kafa gard çizgisinden az kayar; roll'da dizlerden in, belden değil.",
     ["box_slip", "box_roll"], ["box_slip", "box_roll", "box_combo_12"], ["box_combo_12", "box_lead_hook"]),
    ("1-2-3", "Cross'un dönüşü kroşeyi yükler; üç yumruk tek akış.",
     ["box_combo_123", "box_lead_hook"], ["box_combo_123", "box_combo_12", "box_slip"], ["box_combo_123"]),
    ("Değerlendirme 2", "Dört yumruk + savunma: komutlara anında cevap ver.",
     None, ["box_combo_123", "box_rear_hook", "box_lead_uppercut", "box_roll", "box_slip"],
     ["box_combo_123", "box_rear_hook"], True),
    ("Saldırı + Savunma", "Her kombinasyondan sonra bir savunma: 1-2, slip, 1-2-3, roll.",
     ["box_combo_12", "box_slip"], ["box_combo_12", "box_slip", "box_combo_123", "box_roll"], ["box_combo_12", "box_combo_123"]),
    ("Yakın Mesafe", "İçeride kroşe ve aparkat; başını gardın arkasında tut.",
     ["box_lead_uppercut", "box_rear_hook"], ["box_lead_uppercut", "box_rear_hook", "box_rear_uppercut", "box_roll"],
     ["box_rear_uppercut", "box_lead_hook"]),
    ("Açılar", "Vur ve çık: kombinasyon sonrası yana adım, yeni açıdan jab.",
     ["box_footwork", "box_combo_12"], ["box_footwork", "box_jab", "box_combo_123"], ["box_combo_123", "box_jab"]),
    ("Hız Torbası", "Hızlı ve hafif: her komutta en hızlı haliyle, sonra gevşe.",
     ["box_jab", "box_cross"], ["box_jab", "box_combo_12", "box_combo_123", "box_cross"], ["box_jab", "box_combo_12"]),
    ("Dayanıklılık", "Tempo düşmesin: son 30 saniyede sürekli 1-2.",
     ["box_combo_123", "box_parry_block"], ["box_combo_123", "box_parry_block", "box_combo_12"], ["box_combo_123", "box_combo_12"]),
    ("Değerlendirme 3", "3 dakikalık raundlarda saldırı ve savunma bir arada.",
     None, ["box_combo_123", "box_slip", "box_rear_hook", "box_roll", "box_lead_uppercut"],
     ["box_combo_123", "box_rear_hook"], True),
    ("Tüm Yumruklar", "1'den 6'ya bütün yumruklar; komutları say ve at.",
     ["box_lead_hook", "box_rear_uppercut"],
     ["box_jab", "box_cross", "box_lead_hook", "box_rear_hook", "box_lead_uppercut", "box_rear_uppercut"],
     ["box_lead_hook", "box_rear_uppercut"]),
    ("Karşı Atak", "Önce savun, hemen cevap ver: parry-1-2, slip-kroşe, roll-aparkat.",
     ["box_parry_block", "box_slip"], ["box_parry_block", "box_slip", "box_roll", "box_combo_12"], ["box_combo_12", "box_lead_hook"]),
    ("Güç Raundu", "Her yumrukta kalça döner; az ama sert, sonra çık.",
     ["box_rear_hook", "box_cross"], ["box_cross", "box_rear_hook", "box_lead_hook"], ["box_rear_hook", "box_cross"]),
    ("Kombinasyon Akışı", "Kombinasyonlar arası boşluk yok; nefesini yumruklarla ver.",
     ["box_combo_123", "box_footwork"], ["box_combo_12", "box_combo_123", "box_lead_uppercut", "box_footwork"],
     ["box_combo_123", "box_combo_12"]),
    ("Yüksek Tempo", "Raundun her dakikası farklı tempo: hafif, orta, tam güç.",
     ["box_jab", "box_roll"], ["box_jab", "box_combo_123", "box_roll", "box_rear_uppercut"], ["box_jab", "box_combo_123"]),
    ("Final", "8 raunt: her şeyi kullan, son raundu en iyi raundun yap.",
     None, ["box_combo_12", "box_combo_123", "box_slip", "box_roll", "box_rear_hook", "box_lead_uppercut"],
     ["box_combo_123", "box_rear_hook", "box_combo_12"], True),
]

KICKBOXING = [
    ("Duruş ve Jab–Cross", "Boks duruşundan biraz daha dik; ağırlık ortada, tekmeye hazır.",
     ["kb_stance", "kb_jab_cross"], ["kb_jab_cross", "kb_footwork"], ["kb_jab_cross"]),
    ("Teep", "Ön dizi kaldır, kalçayı it; ayak tabanı karına.",
     ["kb_teep", "kb_stance"], ["kb_teep", "kb_jab_cross"], ["kb_teep", "kb_jab_cross"]),
    ("Low Kick", "Kaval vurur, ayak değil; destek ayağının parmakları torbaya.",
     ["kb_low_kick", "kb_jab_cross"], ["kb_low_kick", "kb_jab_cross"], ["kb_low_kick"]),
    ("Ayak Oyunu", "Açı değiştir, tekme mesafesinde kalma; adım–vur–çık.",
     ["kb_footwork", "kb_teep"], ["kb_footwork", "kb_teep", "kb_jab_cross"], ["kb_jab_cross", "kb_teep"]),
    ("Jab–Cross–Low", "Cross'un dönüşü low kick'i yükler; üç vuruş tek akış.",
     ["kb_combo_jcl", "kb_low_kick"], ["kb_combo_jcl", "kb_jab_cross", "kb_low_kick"], ["kb_combo_jcl", "kb_low_kick"]),
    ("Değerlendirme 1", "Yumruk + teep + low kick, 6 raunt.",
     None, ["kb_jab_cross", "kb_teep", "kb_low_kick", "kb_combo_jcl"], ["kb_combo_jcl", "kb_teep"], True),
    ("Middle Kick", "Kalça devrilir, kaval kaburgaya; kol aşağı savrulur, diğer el çenede.",
     ["kb_middle_kick", "kb_stance"], ["kb_middle_kick", "kb_jab_cross"], ["kb_middle_kick"]),
    ("Check", "Ön dizi kaldır, kaval tekmeye; hemen cevap ver.",
     ["kb_check", "kb_low_kick"], ["kb_check", "kb_low_kick", "kb_jab_cross"], ["kb_low_kick", "kb_jab_cross"]),
    ("Diz", "Kalçayı öne it, diz hedefe; eller boyun ya da gardda.",
     ["kb_knee", "kb_teep"], ["kb_knee", "kb_jab_cross", "kb_teep"], ["kb_knee", "kb_jab_cross"]),
    ("High Kick", "Esneklik + kalça: destek ayağı torbaya, bacak yukarı yayla.",
     ["kb_high_kick", "kb_middle_kick"], ["kb_high_kick", "kb_middle_kick", "kb_jab_cross"], ["kb_high_kick", "kb_middle_kick"]),
    ("Tekme Karışık", "Low, middle, high: seviyeyi değiştir, rakip tahmin etmesin.",
     ["kb_low_kick", "kb_high_kick"], ["kb_low_kick", "kb_middle_kick", "kb_high_kick", "kb_check"], ["kb_middle_kick", "kb_low_kick"]),
    ("Değerlendirme 2", "Tekme + diz + savunma, 6 raunt.",
     None, ["kb_middle_kick", "kb_knee", "kb_check", "kb_combo_jcl", "kb_teep"], ["kb_middle_kick", "kb_knee"], True),
    ("Jab–Cross–Kroşe–Middle", "Dört vuruş: kroşe ağırlığı ön bacağa koyar, middle ondan çıkar.",
     ["kb_combo_jcm", "kb_middle_kick"], ["kb_combo_jcm", "kb_combo_jcl", "kb_jab_cross"], ["kb_combo_jcm"]),
    ("Kombinasyon Karışık", "JCL ve JCM arası geçiş; her kombinasyondan sonra açı al.",
     ["kb_combo_jcl", "kb_combo_jcm"], ["kb_combo_jcl", "kb_combo_jcm", "kb_footwork"], ["kb_combo_jcl", "kb_combo_jcm"]),
    ("Teep ve Diz", "Mesafeyi teep ile kur, yakına gelince diz.",
     ["kb_teep", "kb_knee"], ["kb_teep", "kb_knee", "kb_jab_cross"], ["kb_teep", "kb_knee"]),
    ("Savunma Raundu", "Check sonrası cevap: check–low, check–cross.",
     ["kb_check", "kb_jab_cross"], ["kb_check", "kb_low_kick", "kb_jab_cross", "kb_middle_kick"], ["kb_jab_cross", "kb_low_kick"]),
    ("Dayanıklılık", "Son 30 saniyede sürekli middle kick, sağ–sol.",
     ["kb_middle_kick", "kb_knee"], ["kb_middle_kick", "kb_knee", "kb_combo_jcl"], ["kb_middle_kick", "kb_combo_jcl"]),
    ("Değerlendirme 3", "Kombinasyonlar 3 dakikalık raundlarda.",
     None, ["kb_combo_jcm", "kb_combo_jcl", "kb_high_kick", "kb_check", "kb_knee"], ["kb_combo_jcm", "kb_combo_jcl"], True),
    ("Tüm Silahlar", "Yumruk, tekme, diz: komutları say ve at.",
     ["kb_jab_cross", "kb_high_kick"],
     ["kb_jab_cross", "kb_teep", "kb_low_kick", "kb_middle_kick", "kb_high_kick", "kb_knee"], ["kb_middle_kick", "kb_jab_cross"]),
    ("Karşı Atak", "Teep'i yakala, check'le, hemen cevap ver.",
     ["kb_check", "kb_teep"], ["kb_check", "kb_teep", "kb_combo_jcl"], ["kb_combo_jcl", "kb_teep"]),
    ("Güç Raundu", "Her tekmede kalça döner; az ama sert.",
     ["kb_low_kick", "kb_middle_kick"], ["kb_low_kick", "kb_middle_kick", "kb_combo_jcl"], ["kb_low_kick", "kb_middle_kick"]),
    ("Gölge Akışı", "Gölge raundu gibi torba: kombinasyonlar arası boşluk yok.",
     ["kb_footwork", "kb_combo_jcm"], ["kb_combo_jcm", "kb_combo_jcl", "kb_knee", "kb_footwork"], ["kb_combo_jcm", "kb_knee"]),
    ("Yüksek Tempo", "Raundun her dakikası farklı tempo: hafif, orta, tam güç.",
     ["kb_jab_cross", "kb_low_kick"], ["kb_jab_cross", "kb_low_kick", "kb_high_kick", "kb_check"], ["kb_jab_cross", "kb_low_kick"]),
    ("Final", "8 raunt: her şeyi kullan, son raundu en iyi raundun yap.",
     None, ["kb_combo_jcm", "kb_combo_jcl", "kb_high_kick", "kb_knee", "kb_check", "kb_teep"],
     ["kb_combo_jcm", "kb_middle_kick", "kb_combo_jcl"], True),
]

WRESTLING = [
    ("Duruş", "Dizler bükük, sırt düz, eller önde; ağırlık ayak uçlarında.",
     ["wr_stance", "wr_level_change"], ["wr_level_change", "wr_stance"], ["wr_level_change", "wr_stance"]),
    ("Seviye Değiştirme", "Belden değil dizlerden in; baş yukarıda, sırt düz.",
     ["wr_level_change", "wr_stance"], ["wr_level_change", "wr_penetration"], ["wr_level_change"]),
    ("Penetrasyon", "Ön diz yere yakın kayar, arka ayak hemen toparlanır.",
     ["wr_penetration", "wr_level_change"], ["wr_penetration", "wr_level_change"], ["wr_penetration"]),
    ("Köprü", "Boyun ve ayaklar üzerinde kalça yukarı; yavaş ve kontrollü.",
     ["wr_bridge", "wr_stance"], ["wr_level_change", "wr_penetration"], ["wr_penetration", "wr_level_change"]),
    ("Sprawl", "Kalçayı yere at, bacaklar geriye; eller rakibin sırtında.",
     ["wr_sprawl", "wr_stance"], ["wr_sprawl", "wr_level_change", "wr_penetration"], ["wr_sprawl", "wr_penetration"]),
    ("Değerlendirme 1", "Seviye değiştir, penetrasyon, sprawl: komutlara anında tepki.",
     None, ["wr_level_change", "wr_penetration", "wr_sprawl"], ["wr_penetration", "wr_sprawl"], True),
    ("Çift Bacak", "Penetrasyon + iki dizin arkası; baş yan tarafta, kalçayı sür.",
     ["wr_double_leg", "wr_penetration"], ["wr_double_leg", "wr_level_change", "wr_sprawl"], ["wr_double_leg"]),
    ("Tek Bacak", "Ön bacağı yakala, baş içeride; bacağı kaldır ve döndür.",
     ["wr_single_leg", "wr_penetration"], ["wr_single_leg", "wr_level_change", "wr_sprawl"], ["wr_single_leg"]),
    ("Dalış Karışık", "Komuta göre çift ya da tek bacak; her dalıştan sonra hemen duruşa dön.",
     ["wr_double_leg", "wr_single_leg"], ["wr_double_leg", "wr_single_leg", "wr_sprawl"], ["wr_double_leg", "wr_single_leg"]),
    ("Sprawl ve Dönüş", "Sprawl'dan sonra yana dön, arkaya geç.",
     ["wr_sprawl", "wr_bridge"], ["wr_sprawl", "wr_double_leg", "wr_level_change"], ["wr_sprawl", "wr_double_leg"]),
    ("Yerden Çıkış", "Sit-out ile yana dön, stand-up ile ayağa kalk; eller kontrolde.",
     ["wr_sit_out", "wr_stand_up"], ["wr_sit_out", "wr_stand_up", "wr_sprawl"], ["wr_sit_out", "wr_stand_up"]),
    ("Değerlendirme 2", "Dalış + savunma + yerden çıkış.",
     None, ["wr_double_leg", "wr_single_leg", "wr_sprawl", "wr_stand_up"], ["wr_double_leg", "wr_sit_out"], True),
    ("El Mücadelesi", "Bilekleri kontrol et, dirsekleri içeride tut; açıklık yarat.",
     ["wr_hand_fight", "wr_stance"], ["wr_hand_fight", "wr_level_change", "wr_single_leg"], ["wr_hand_fight"]),
    ("Snap Down", "Başı çek, rakibi öne düşür, arkasına geç.",
     ["wr_snap_down", "wr_hand_fight"], ["wr_snap_down", "wr_hand_fight", "wr_sprawl"], ["wr_snap_down", "wr_hand_fight"]),
    ("Zincir Drill", "Bir hareket diğerine bağlanır: hand fight, seviye, dalış.",
     ["wr_shadow", "wr_hand_fight"], ["wr_hand_fight", "wr_double_leg", "wr_snap_down"], ["wr_shadow"]),
    ("Alt Pozisyon", "Sit-out, stand-up, köprü: yerde asla düz kalma.",
     ["wr_sit_out", "wr_bridge"], ["wr_sit_out", "wr_stand_up", "wr_bridge"], ["wr_stand_up", "wr_sit_out"]),
    ("Dayanıklılık", "Son 30 saniyede sürekli sprawl.",
     ["wr_sprawl", "wr_penetration"], ["wr_sprawl", "wr_penetration", "wr_double_leg"], ["wr_sprawl", "wr_double_leg"]),
    ("Değerlendirme 3", "El mücadelesi, snap down ve dalış zinciri.",
     None, ["wr_hand_fight", "wr_snap_down", "wr_single_leg", "wr_double_leg", "wr_sprawl"], ["wr_shadow", "wr_snap_down"], True),
    ("Tüm Dalışlar", "Komuta göre dalış, sprawl ya da snap down.",
     ["wr_single_leg", "wr_double_leg"], ["wr_double_leg", "wr_single_leg", "wr_snap_down", "wr_sprawl"], ["wr_double_leg", "wr_single_leg"]),
    ("Karşı Atak", "Sprawl'dan snap down'a, snap down'dan arkaya.",
     ["wr_sprawl", "wr_snap_down"], ["wr_sprawl", "wr_snap_down", "wr_hand_fight"], ["wr_sprawl", "wr_snap_down"]),
    ("Güç ve Patlayıcılık", "Her dalış tam güç; arada kısa toparlanma.",
     ["wr_penetration", "wr_double_leg"], ["wr_penetration", "wr_double_leg", "wr_level_change"], ["wr_double_leg", "wr_penetration"]),
    ("Maç Simülasyonu", "Ayakta, altta, üstte: her komutta pozisyon değişir.",
     ["wr_shadow", "wr_sit_out"], ["wr_hand_fight", "wr_single_leg", "wr_sprawl", "wr_sit_out", "wr_stand_up"], ["wr_shadow"]),
    ("Yüksek Tempo", "Raundun her dakikası farklı tempo: hafif, orta, tam güç.",
     ["wr_level_change", "wr_sprawl"], ["wr_level_change", "wr_double_leg", "wr_sprawl", "wr_snap_down"], ["wr_shadow", "wr_sprawl"]),
    ("Final", "8 raunt: zincir drill ve dalışlar; son raundu en iyi raundun yap.",
     None, ["wr_hand_fight", "wr_double_leg", "wr_single_leg", "wr_snap_down", "wr_sprawl", "wr_stand_up"],
     ["wr_shadow", "wr_double_leg", "wr_snap_down"], True),
]

TAEKWONDO = [
    ("Duruşlar", "Ap seogi yürüyüş boyunda, ap kubi'de ön diz ayak ucunun üstünde.",
     ["tkd_ap_seogi", "tkd_ap_kubi"], ["tkd_ap_seogi", "tkd_ap_kubi", "tkd_footwork"], ["tkd_ap_kubi", "tkd_ap_seogi"]),
    ("Jireugi", "Yumruk kalçadan döner, çeken el avuç yukarı bele.",
     ["tkd_jireugi", "tkd_ap_kubi"], ["tkd_jireugi", "tkd_ap_seogi"], ["tkd_jireugi"]),
    ("Alt Blok", "Blok eli karşı omuzdan iner, çeken el bele.",
     ["tkd_arae_makgi", "tkd_ap_kubi"], ["tkd_arae_makgi", "tkd_jireugi"], ["tkd_arae_makgi", "tkd_jireugi"]),
    ("Orta Blok", "Kol dışarıdan içeriye, dirsek 90 derece.",
     ["tkd_momtong_makgi", "tkd_dwit_kubi"], ["tkd_momtong_makgi", "tkd_jireugi", "tkd_arae_makgi"], ["tkd_momtong_makgi", "tkd_jireugi"]),
    ("Ön Tekme", "Diz yukarı, ayak topuyla vur, hemen geri çek.",
     ["tkd_ap_chagi", "tkd_ap_seogi"], ["tkd_ap_chagi", "tkd_jireugi", "tkd_footwork"], ["tkd_ap_chagi"]),
    ("Değerlendirme 1", "Duruş, yumruk, blok ve ön tekme.",
     None, ["tkd_jireugi", "tkd_arae_makgi", "tkd_momtong_makgi", "tkd_ap_chagi"], ["tkd_ap_chagi", "tkd_jireugi"], True),
    ("Dollyo Chagi", "Destek ayağı hedefe, kalça döner, ayak üstüyle vur.",
     ["tkd_dollyo_chagi", "tkd_footwork"], ["tkd_dollyo_chagi", "tkd_ap_chagi"], ["tkd_dollyo_chagi"]),
    ("Ayak Oyunu", "Hafif sekme, mesafeyi tekmeyle kontrol et.",
     ["tkd_footwork", "tkd_dollyo_chagi"], ["tkd_footwork", "tkd_dollyo_chagi", "tkd_ap_chagi"], ["tkd_dollyo_chagi", "tkd_ap_chagi"]),
    ("Yeop Chagi", "Yan dön, diz göğse, topuk önde düz it.",
     ["tkd_yeop_chagi", "tkd_dwit_kubi"], ["tkd_yeop_chagi", "tkd_dollyo_chagi"], ["tkd_yeop_chagi"]),
    ("Tekme Karışık", "Ön, yuvarlak, yan: komuta göre değiştir.",
     ["tkd_ap_chagi", "tkd_yeop_chagi"], ["tkd_ap_chagi", "tkd_dollyo_chagi", "tkd_yeop_chagi", "tkd_footwork"],
     ["tkd_dollyo_chagi", "tkd_yeop_chagi"]),
    ("Blok ve Karşı", "Blokla, aynı anda çeken elle cevap ver.",
     ["tkd_momtong_makgi", "tkd_jireugi"], ["tkd_momtong_makgi", "tkd_arae_makgi", "tkd_jireugi", "tkd_dollyo_chagi"],
     ["tkd_jireugi", "tkd_dollyo_chagi"]),
    ("Değerlendirme 2", "Üç temel tekme ve ayak oyunu.",
     None, ["tkd_ap_chagi", "tkd_dollyo_chagi", "tkd_yeop_chagi", "tkd_footwork"], ["tkd_dollyo_chagi", "tkd_yeop_chagi"], True),
    ("Dwi Chagi", "Dön, omzun üstünden bak, topuk düz geriye.",
     ["tkd_dwi_chagi", "tkd_dwit_kubi"], ["tkd_dwi_chagi", "tkd_dollyo_chagi"], ["tkd_dwi_chagi"]),
    ("Naeryo Chagi", "Bacak düz yukarı, topukla aşağı in.",
     ["tkd_naeryo_chagi", "tkd_ap_seogi"], ["tkd_naeryo_chagi", "tkd_ap_chagi"], ["tkd_naeryo_chagi"]),
    ("Üst Blok", "Kol alnın üstünde, bilek dışa dönük.",
     ["tkd_olgul_makgi", "tkd_ap_kubi"], ["tkd_olgul_makgi", "tkd_jireugi", "tkd_momtong_makgi"], ["tkd_olgul_makgi", "tkd_jireugi"]),
    ("Taegeuk 1 – Bölüm 1", "Formun ilk bölümü: yavaş, net duruşlar.",
     ["tkd_taegeuk1", "tkd_arae_makgi"], ["tkd_arae_makgi", "tkd_jireugi", "tkd_ap_seogi"], ["tkd_taegeuk1"]),
    ("İleri Tekmeler", "Dwi ve naeryo arası geçiş; her tekmeden sonra gard.",
     ["tkd_dwi_chagi", "tkd_naeryo_chagi"], ["tkd_dwi_chagi", "tkd_naeryo_chagi", "tkd_dollyo_chagi"], ["tkd_dwi_chagi", "tkd_naeryo_chagi"]),
    ("Değerlendirme 3", "İleri tekmeler ve form.",
     None, ["tkd_dwi_chagi", "tkd_naeryo_chagi", "tkd_yeop_chagi", "tkd_olgul_makgi"], ["tkd_taegeuk1", "tkd_dwi_chagi"], True),
    ("Taegeuk 1 – Tam Form", "Formu baştan sona; her hareket sonunda dur ve kontrol et.",
     ["tkd_taegeuk1", "tkd_ap_kubi"], ["tkd_arae_makgi", "tkd_olgul_makgi", "tkd_ap_chagi", "tkd_jireugi"], ["tkd_taegeuk1"]),
    ("Kombinasyonlar", "Dollyo–dwi, ap–dollyo: ikinci tekme ilkinin dönüşünden.",
     ["tkd_dollyo_chagi", "tkd_dwi_chagi"], ["tkd_ap_chagi", "tkd_dollyo_chagi", "tkd_dwi_chagi", "tkd_footwork"],
     ["tkd_dollyo_chagi", "tkd_dwi_chagi"]),
    ("Güç Raundu", "Her tekme tam kalça dönüşüyle; az ama sert.",
     ["tkd_yeop_chagi", "tkd_naeryo_chagi"], ["tkd_yeop_chagi", "tkd_naeryo_chagi", "tkd_dollyo_chagi"], ["tkd_yeop_chagi", "tkd_dollyo_chagi"]),
    ("Duruş ve Blok Akışı", "Dwit kubi'de orta blok, ap kubi'de yumruk.",
     ["tkd_dwit_kubi", "tkd_momtong_makgi"], ["tkd_momtong_makgi", "tkd_olgul_makgi", "tkd_jireugi", "tkd_arae_makgi"],
     ["tkd_taegeuk1", "tkd_jireugi"]),
    ("Yüksek Tempo", "Raundun her dakikası farklı tempo: hafif, orta, tam güç.",
     ["tkd_footwork", "tkd_ap_chagi"], ["tkd_ap_chagi", "tkd_dollyo_chagi", "tkd_yeop_chagi", "tkd_dwi_chagi"],
     ["tkd_dollyo_chagi", "tkd_ap_chagi"]),
    ("Final", "Form + 8 raunt tekme: son raundu en iyi raundun yap.",
     None, ["tkd_dollyo_chagi", "tkd_dwi_chagi", "tkd_naeryo_chagi", "tkd_yeop_chagi", "tkd_ap_chagi"],
     ["tkd_dollyo_chagi", "tkd_taegeuk1", "tkd_yeop_chagi"], True),
]

SPORTS = {
    "boxing": (BOXING, rope_warm, "box_shadow", "bag", "Torba"),
    "kickboxing": (KICKBOXING, rope_warm, "kb_shadow", "bag", "Torba"),
    "wrestling": (WRESTLING, mobility_warm, "wr_shadow", "drill", "Dalış drilli"),
    "taekwondo": (TAEKWONDO, mobility_warm, "tkd_footwork", "drill", "Tekme raundu"),
}


# ---------------------------------------------------------------------------------------------
# Genel Kondisyon: dövüş tekniği yok; ısınma -> form devresi -> HIIT devresi -> bitirici -> esneme.
# Evre ilerledikçe çalışma/dinlenme oranı artar (30/30 -> 40/20 -> 45/15 -> 50/10) ve tur sayısı çoğalır.
# ---------------------------------------------------------------------------------------------
GEN_PHASE = [
    dict(work=30, rest=30, rounds=3),
    dict(work=40, rest=20, rounds=3),
    dict(work=45, rest=15, rounds=4),
    dict(work=50, rest=10, rounds=4),
]

PHASE_INFO["general"] = [
    ("Temel Kondisyon", "Doğru form, nefes ritmi ve temel dayanıklılık."),
    ("Güç ve Dayanıklılık", "Daha uzun çalışma, daha kısa dinlenme; burpee devreye girer."),
    ("Yüksek Tempo", "45/15 aralıklarla tempo ve hızlı toparlanma."),
    ("Zirve", "50/10 aralıklar: dövüşçü dayanıklılığı ve final testi."),
]

S, P, PL, SU, B, J, JO = ("gen_squat", "gen_pushup", "gen_plank", "gen_situp", "gen_burpee", "gen_jump_rope",
                          "gen_jog")
# (başlık, koç notu, form hareketleri, HIIT hareketleri, değerlendirme?)
GENERAL = [
    ("Başlangıç", "Her harekette temiz form; hız değil kontrol.", [S, P], [S, P, JO, PL]),
    ("Gövde Gücü", "Karın sıkı, bel düz; plank'te kalçayı düşürme.", [PL, SU], [SU, PL, S, JO]),
    ("Bacak Günü", "Squat'ta dizler parmak yönünde, topuklar yerde.", [S, JO], [S, J, SU, PL]),
    ("Üst Vücut", "Şınavda dirsekler 45°, gövde tek parça.", [P, PL], [P, PL, JO, SU]),
    ("İp ve Ritim", "İpi bilekten çevir, ayak uçlarında hafif zıpla.", [J, JO], [J, S, P, PL]),
    ("Test 1", "Her istasyonda temiz tekrar sayını aklında tut; bir sonraki testte geçeceksin.",
     None, [S, P, SU, PL, JO], True),
    ("Burpee'ye Giriş", "Burpee'de önce form: çömel, ayakları geri at, göğüs yere, patlayarak kalk.", [B, S],
     [B, S, PL, JO]),
    ("Gövde Devresi", "Mekikte boynu çekme; gücü karından al.", [SU, PL], [SU, PL, B, J]),
    ("Tam Vücut", "Üst ve alt vücut sırayla: biri çalışırken diğeri dinlenir.", [P, S], [P, S, B, SU]),
    ("Kardiyo Patlaması", "Nabız yüksek; dinlenmede burnundan nefes al.", [JO, J], [JO, J, B, S]),
    ("Kuvvet Dayanıklılığı", "Son 10 saniyede tempoyu düşürme.", [P, PL], [P, PL, S, SU, JO]),
    ("Test 2", "Test 1'deki sayılarını geç: aynı form, daha çok tekrar.", None, [B, P, S, SU, J], True),
    ("Tempo Squat", "İnişte 2 saniye, çıkışta patlayıcı.", [S, B], [S, B, J, PL]),
    ("Şınav Merdiveni", "Yorulunca dizden şınava geç ama durma.", [P, SU], [P, SU, JO, B]),
    ("Dövüşçü Kondisyonu", "İp ve burpee: dövüşçülerin klasik ikilisi.", [J, B], [J, B, P, S, PL]),
    ("Gövde Kalkanı", "Gövde sert, nefes kontrollü; darbe almaya hazır bir karın.", [PL, SU], [PL, SU, B, JO]),
    ("Patlayıcı Güç", "Her tekrar maksimum hız, tam hareket açıklığı.", [B, S], [B, S, P, J]),
    ("Test 3", "45/15 temposunda tüm istasyonlar; formu bozma.", None, [B, S, P, SU, PL], True),
    ("Zirve Devresi", "50/10: dinlenme kısa, nefesini hareket sırasında düzenle.", [B, P], [B, P, S, JO, PL]),
    ("Uzun Raunt", "Kardiyo ağırlıklı uzun devre; tempoyu eşit dağıt.", [J, JO], [J, JO, B, SU, S]),
    ("Güç Zinciri", "Squat, şınav, burpee zinciri: kas dayanıklılığı.", [S, P], [S, P, B, PL, SU]),
    ("Kardiyo Fırtınası", "En yüksek nabız günü; son turda her şeyini ver.", [JO, B], [JO, B, J, S, P]),
    ("Son Hazırlık", "Finalden önce temiz ve kontrollü bir devre.", [PL, SU], [PL, SU, P, S, B]),
    ("Final", "30 günün sonu: tüm istasyonlar, en iyi formun ve en çok tekrarın.", None,
     [B, S, P, SU, PL, J], True),
]


def general_day(d, title, focus, tech, mains, evaluate=False):
    p = (d - 1) // 6
    ph = GEN_PHASE[p]
    blocks = [mobility_warm(p)]
    if tech and not evaluate:
        blocks.append(C("technique", "Form", 2, 40, 20, tech, cue=f"Form devresi: {focus}"))
    rounds = ph["rounds"] + (1 if evaluate else 0)
    blocks.append(C("conditioning", "Test devresi" if evaluate else "HIIT devresi", rounds, ph["work"], ph["rest"],
                    mains, cue=f"{rounds} tur: her istasyonda {ph['work']} sn çalış, {ph['rest']} sn dinlen."))
    if not evaluate:
        blocks.append(R("conditioning", "Bitirici", 1, 60 + 15 * p, 0, [J if p % 2 else JO],
                        cue="Bitirici: son bir dakika, tempoyu koru."))
    blocks.append(C("cooldown", "Esneme", 1, 40, 10, STRETCH, cue="Nefesini yavaşlat, esnemeleri zorlamadan yap."))
    m = minutes(blocks)
    assert 20 <= m <= 60, ("general", d, m)
    return dict(day=d, title=title, focus=focus, blocks=blocks)


def rest_day():
    """30 günlük meydan okumanın dinlenme günleri için ~8-10 dk aktif dinlenme."""
    blocks = [
        C("warmup", "Hafif hareket", 1, 45, 15, [JO, "gen_arm_circles"], cue="Hafif tempo; terlemek yok, kan dolaşsın."),
        C("cooldown", "Esneme", 2, 45, 15, STRETCH, cue="Her esnemede derin nefes; acı değil, gerilme hissi."),
    ]
    m = minutes(blocks)
    assert 5 <= m <= 15, m
    return dict(day=0, title="Aktif Dinlenme",
                focus="Bugün kaslarının toparlanma günü. İstersen bu kısa esneme seansıyla vücudunu gevşet.",
                blocks=blocks)


def main():
    days = [general_day(i + 1, *spec) for i, spec in enumerate(GENERAL)]
    assert len(days) == 24
    write_program("general", days)
    with open(os.path.join(OUT, "rest_day.json"), "w", encoding="utf-8") as fh:
        json.dump(rest_day(), fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"rest_day: {round(minutes(rest_day()['blocks']), 1)} dk")
    for sport, (days, warm, shadow, kind, main_title) in SPORTS.items():
        assert len(days) == 24, sport
        out = []
        for i, spec in enumerate(days):
            title, focus, tech, calls, mains = spec[:5]
            ev = len(spec) > 5 and spec[5]
            out.append(day(sport, i + 1, title, focus, tech, calls, mains, kind, main_title, warm, shadow, ev))
        write_program(sport, out)


def write_program(sport, out):
    phases = [dict(title=t, **{"from": 6 * k + 1, "to": 6 * k + 6}, goal=g) for k, (t, g) in enumerate(PHASE_INFO[sport])]
    path = os.path.join(OUT, f"training_{sport}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(dict(sport=sport, phases=phases, days=out), fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    mins = [round(minutes(d["blocks"])) for d in out]
    print(f"{sport}: {len(out)} gün, {min(mins)}-{max(mins)} dk")


if __name__ == "__main__":
    main()
