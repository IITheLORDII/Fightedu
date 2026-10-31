#!/usr/bin/env python3
"""Sesli koç: rauntlara özel Türkçe metinler ve "ipucu sayfaları" (cue sheet).

Her dalın her antrenman günü için, oynatıcının adım listesiyle (TrainingPlanner.steps) birebir aynı sırada,
hangi adımın başında ve kaçıncı saniyesinde hangi cümlelerin söyleneceğini üretir. Her cümle bir ses klibidir
(aynı cümle bir kez kaydedilir). Klip sesleri synthesize.py ile Google Cloud TTS'ten alınır; klip dosyası yoksa
uygulama aynı metni cihazın TTS'iyle okur.

Çıktılar (app/src/main/assets/voice/):
  manifest.json           klip kimliği -> {text: ekranda/inceleme metni, say: okunacak metin, ms: süre, measured}
  cues_<dal>.json         {"days": {"<gün>": DayCues}, "rest": {"<meydan okuma günü>": DayCues}}
                          DayCues = {"steps": [{"s": [klipler], "at": {"<saniye>": [klipler]}}], "finish": [klipler]}
  tools/voice/build/script_<dal>.md   inceleme dökümü
Klip süreleri biliniyorsa (synthesize.py ölçer) zamanlama gerçek sürelerle yapılır; bilinmiyorsa tahmin edilir.
Kullanım: python3 tools/voice/make_voice.py [--stats]
"""
import argparse
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
CONTENT = os.path.join(ROOT, "app", "src", "main", "assets", "content")
OUT = os.path.join(ROOT, "app", "src", "main", "assets", "voice")
BUILD = os.path.join(HERE, "build")

# TrainingPlanner ile aynı sabitler
CALL_START, CALL_INTERVAL, CALL_END_GAP, BLOCK_TRANSITION = 8, 15, 8, 30
# ChallengeCalendar ile aynı takvim
LENGTH, REST_DAYS = 30, (5, 10, 15, 20, 25, 28)

# --------------------------------------------------------------------------------------------
# Türkçe sayılar
# --------------------------------------------------------------------------------------------
ONES = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
TENS = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
ORD = {"bir": "birinci", "iki": "ikinci", "üç": "üçüncü", "dört": "dördüncü", "beş": "beşinci", "altı": "altıncı",
       "yedi": "yedinci", "sekiz": "sekizinci", "dokuz": "dokuzuncu", "on": "onuncu", "yirmi": "yirminci",
       "otuz": "otuzuncu", "kırk": "kırkıncı", "elli": "ellinci", "altmış": "altmışıncı", "yüz": "yüzüncü"}
DIST = {"bir": "birer", "iki": "ikişer", "üç": "üçer", "dört": "dörder", "beş": "beşer", "altı": "altışar",
        "yedi": "yedişer", "sekiz": "sekizer", "dokuz": "dokuzar", "on": "onar", "yirmi": "yirmişer",
        "otuz": "otuzar", "kırk": "kırkar", "elli": "ellişer", "altmış": "altmışar"}


def num(n):
    if n == 0:
        return "sıfır"
    parts = []
    if n >= 100:
        h = n // 100
        parts.append(("" if h == 1 else ONES[h] + " ") + "yüz")
        n %= 100
    if n >= 10:
        parts.append(TENS[n // 10])
        n %= 10
    if n:
        parts.append(ONES[n])
    return " ".join(parts)


def _last(words, table):
    w = words.split(" ")
    w[-1] = table[w[-1]]
    return " ".join(w)


def ordinal(n):
    return _last(num(n), ORD)


def each(n):
    return _last(num(n), DIST)


def dur(sec):
    """45 -> "kırk beş saniye", 90 -> "bir buçuk dakika", 150 -> "iki buçuk dakika"."""
    if sec < 60:
        return f"{num(sec)} saniye"
    m, s = divmod(sec, 60)
    if s == 0:
        return f"{num(m)} dakika"
    if s == 30:
        return f"{num(m)} buçuk dakika"
    return f"{num(m)} dakika {num(s)} saniye"


def dur_each(sec):
    """60 -> "birer dakika", 120 -> "ikişer dakika", 40 -> "kırkar saniye"."""
    if sec < 60:
        return f"{each(sec)} saniye"
    m, s = divmod(sec, 60)
    if s == 0:
        return f"{each(m)} dakika"
    if s == 30:
        return f"{each(m)} buçuk dakika"
    return f"{each(m)} dakika {num(s)} saniye"


TR_UPPER = str.maketrans({"i": "İ", "ı": "I"})
TR_LOWER = str.maketrans({"İ": "i", "I": "ı"})


def cap(s):
    return s[:1].translate(TR_UPPER).upper() + s[1:] if s else s


def low(s):
    return s[:1].translate(TR_LOWER).lower() + s[1:] if s else s


# --------------------------------------------------------------------------------------------
# Okunuş: TTS'e giden metin (ekrandaki metin değişmez). Yabancı terimler Türkçe okunuşla yazılır.
# --------------------------------------------------------------------------------------------
SAY = [
    (r"bob\s*&\s*weave", "bob end viv"), (r"kick\s*boks", "kik boks"), (r"low\s*kick", "lov kik"),
    (r"middle\s*kick", "midıl kik"), (r"high\s*kick", "hay kik"), (r"snap\s*down", "snep davn"),
    (r"sit[-\s]out", "sit avt"), (r"stand[-\s]up", "stend ap"), (r"hand\s*fight", "hend fayt"),
    (r"il\s*jang", "il cang"), (r"middle", "midıl"), (r"low", "lov"), (r"high", "hay"), (r"kick", "kik"),
    (r"jab", "ceb"), (r"cross", "kros"), (r"roll", "rol"), (r"parry", "peri"), (r"teep", "tiip"),
    (r"check", "çek"), (r"sprawl", "sprol"), (r"burpee", "börpi"), (r"squat", "skuat"), (r"hiit", "hit"),
    (r"chagi", "çagi"), (r"seogi", "sogi"), (r"jireugi", "cirugi"), (r"taegeuk", "tegık"), (r"dollyo", "dolyo"),
    (r"yeop", "yop"), (r"naeryo", "neryo"), (r"dwit", "dvit"), (r"dwi", "dvi"), (r"arae", "are"),
    (r"drill", "dril"), (r"steps", "steps"), (r"bag", "beg"), (r"shadow", "şedov"),
]
SAY_RE = [(re.compile(r"(?<![\w])" + p + r"(?![\w])", re.IGNORECASE | re.UNICODE), r) for p, r in SAY]


def say_text(text):
    s = text
    s = re.sub(r"\s*\([^)]*\)", "", s)  # parantez içleri okunmaz
    s = re.sub(r"(\d+)\s*°", lambda m: m.group(1) + " derece", s)
    s = re.sub(r"(\d+)\s*cm\b", lambda m: m.group(1) + " santim", s)
    s = re.sub(r"(\d+)\s*-\s*(?=\d)", lambda m: num(int(m.group(1))) + " ", s)  # 1-2-3 -> bir iki üç
    s = re.sub(r"\d+", lambda m: num(int(m.group(0))), s)
    s = s.replace("–", ", ").replace("—", ", ").replace(" / ", " ya da ").replace("&", " ve ")
    for rx, rep in SAY_RE:
        s = rx.sub(rep, s)
    s = re.sub(r"\s+", " ", s).replace(" ,", ",").strip()
    return cap(s)


# --------------------------------------------------------------------------------------------
# İçerik
# --------------------------------------------------------------------------------------------
def load(name):
    with open(os.path.join(CONTENT, name), encoding="utf-8") as fh:
        return json.load(fh)


SPORTS = load("sports.json")
MOVES = {}
for f in dict.fromkeys(["general"] + [s["id"] for s in SPORTS]):
    for m in load(f"moves_{f}.json"):
        MOVES[m["id"]] = m
PROGRAMS = {s["id"]: load(f"training_{s['id']}.json") for s in SPORTS}
REST_SESSION = load("rest_day.json")

CALLS = {  # Coach.CALLS ile aynı
    "box_combo_12": "Bir iki", "box_combo_123": "Bir iki üç", "box_footwork": "Ayak oyunu", "box_parry_block": "Blok",
    "box_slip": "Slip", "box_roll": "Roll", "box_lead_hook": "Sol kroşe", "box_rear_hook": "Sağ kroşe",
    "box_lead_uppercut": "Sol aparkat", "box_rear_uppercut": "Sağ aparkat", "box_cross": "Cross",
    "kb_combo_jcl": "Jab cross low kick", "kb_combo_jcm": "Jab cross kroşe middle", "kb_jab_cross": "Jab cross",
    "kb_footwork": "Açı değiştir", "kb_knee": "Diz", "wr_level_change": "Seviye", "wr_penetration": "Penetrasyon",
    "wr_double_leg": "Çift bacak", "wr_single_leg": "Tek bacak", "wr_hand_fight": "El mücadelesi",
    "wr_sit_out": "Sit out", "wr_stand_up": "Kalk", "tkd_footwork": "Ayak oyunu", "tkd_taegeuk1": "Taegeuk",
}


def short(mid):
    n = MOVES[mid]["name"].split(" (")[0]
    return n.split(" / ")[0].strip()


def call_name(mid):
    return CALLS.get(mid) or short(mid).split(": ")[-1].replace("–", " ").strip()


def clean(s):
    s = re.sub(r"\s*\([^)]*\)", "", s).strip()
    return s if s.endswith((".", "!", "?")) else s + "."


def points(mid):
    m = MOVES[mid]
    return [clean(x) for x in m.get("steps", [])] + ([clean(m["tip"])] if m.get("tip") else [])


def mistakes(mid):
    return [re.sub(r"\s*\([^)]*\)", "", x).strip().rstrip(".") for x in MOVES[mid].get("mistakes", [])]


def workout_of(n):
    return None if n in REST_DAYS else n - sum(1 for r in REST_DAYS if r < n)


def challenge_day_of(w):
    return next(n for n in range(1, LENGTH + 1) if workout_of(n) == w)


# --------------------------------------------------------------------------------------------
# Adım açılımı (TrainingPlanner.steps ile aynı)
# --------------------------------------------------------------------------------------------
def works(bi, b):
    out = []
    if b["mode"] == "round":
        for r in range(1, b["rounds"] + 1):
            calls, t, k = [], CALL_START, r - 1
            if b.get("calls"):
                while t <= b["work"] - CALL_END_GAP:
                    calls.append((t, b["calls"][k % len(b["calls"])]))
                    t += CALL_INTERVAL
                    k += 1
            out.append(dict(type="work", bi=bi, b=b, round=r, total=b["rounds"], move=b["moves"][(r - 1) % len(b["moves"])],
                            station=1, stations=1, sec=b["work"], reps=None, calls=calls))
    else:
        for r in range(1, b["rounds"] + 1):
            for i, m in enumerate(b["moves"]):
                timed = b["mode"] == "circuit"
                out.append(dict(type="work", bi=bi, b=b, round=r, total=b["rounds"], move=m, station=i + 1,
                                stations=len(b["moves"]), sec=b["work"] if timed else None,
                                reps=None if timed else b["reps"], calls=[]))
    return out


def steps(day):
    out = []
    for bi, b in enumerate(day["blocks"]):
        w = works(bi, b)
        if out and w:
            out.append(dict(type="rest", bi=bi, sec=max(b["rest"], BLOCK_TRANSITION), next=w[0], between=True))
        for i, x in enumerate(w):
            out.append(x)
            if i + 1 < len(w) and b["rest"] > 0:
                out.append(dict(type="rest", bi=bi, sec=b["rest"], next=w[i + 1], between=False))
    return out


# --------------------------------------------------------------------------------------------
# Metinler
# --------------------------------------------------------------------------------------------
SHADOW_INTRO = {
    "boxing": "Gölge boksu. Komutları dinle, her yumruktan sonra gard; hiç yerinde durma.",
    "kickboxing": "Gölge kick boks. Komut gelince tekniği at, sonra hemen gard ve ayak oyunu.",
    "wrestling": "Gölge güreş, zincir drill. Komutları dinle, her hareketten sonra duruşuna dön.",
    "taekwondo": "Ayak oyunu ve gölge. Ritmi koru, komut gelince tekmeni at.",
}
MAIN_INTRO = {
    "bag": "Torba çalışması. Komut gelince o tekniği at; aralarda ayak oyunu ve kafa hareketi.",
    "drill_wrestling": "Dalış drilli. Komut gelince tekniği uygula, sonra hemen duruşa dön.",
    "drill_taekwondo": "Tekme raundu. Komut gelince tekmeni at, her tekmeden sonra gard ve ritim.",
}
ENCOURAGE = {
    "boxing": ["Ellerin yukarıda, çenen içeride!", "Ayaklarını hareket ettir!", "Nefesini kontrol et, omuzlar gevşek!",
               "Güzel gidiyorsun, tempoyu koru!", "Her kombinasyondan sonra kafanı oynat!"],
    "kickboxing": ["Tekmeden sonra hemen gard!", "Ellerin yukarıda, çenen içeride!", "Güzel gidiyorsun, tempoyu koru!",
                   "Kalçanı döndür, güç oradan gelir!", "Nefesini kontrol et!"],
    "wrestling": ["Kalçan aşağıda, başın yukarıda!", "Tempoyu düşürme!", "Güzel gidiyorsun, devam!",
                  "Her hareketten sonra duruşa dön!", "Nefesini kontrol et!"],
    "taekwondo": ["Her tekmeden sonra bacağını hızla geri çek!", "Gard yukarıda!", "Güzel gidiyorsun, ritmi koru!",
                  "Destek ayağını döndür!", "Nefesini kontrol et!"],
    "general": ["Formunu bozma, nefes al!", "Güzel gidiyorsun, devam!", "Tempoyu düşürme!", "Karnın sıkı, sırtın düz!",
                "Bir tekrar daha, sonra bir tane daha!"],
}
WARM = ["Ritmi koru, nefesini düzenle.", "Omuzlar gevşek, hafif kal.", "Güzel, vücudun ısınıyor."]
REST_TIPS = ["Burnundan nefes al, ağzından ver.", "Omuzlarını gevşet, kollarını salla.", "Bir yudum su iç, nefesini topla.",
             "Yerinde hafifçe yürü, nefesini düzenle.", "Ellerini başının üstüne koy, derin nefes al.",
             "Bir önceki rauntta neyi daha iyi yapabileceğini düşün."]
DONE = ["Blok bitti, iyi iş!", "Güzel, bu bölüm tamam!", "Harika, devam ediyoruz!", "Çok iyi, bir sonraki bölüme geçiyoruz!"]
TEN = ["Son on saniye!", "On saniye, hızlan!", "Son on saniye, bitir!", "On saniye kaldı, dayan!"]
SPORT_PERSON = {"boxing": "boksör", "kickboxing": "kick boksçu", "wrestling": "güreşçi", "taekwondo": "tekvandocu",
                "general": "sporcu"}


def block_intro(sport, b):
    k, mv = b["kind"], [short(m) for m in b["moves"]]
    if k == "warmup":
        if b["moves"] == ["gen_jump_rope"]:
            return "Isınma: ip atlama. Omuzlar gevşek, ayak uçlarında hafif zıpla."
        if sport is None:
            return "Hafif hareket: kan dolaşsın, terlemek yok."
        return "Isınma: yerinde koşu, kol çevirme ve ip. Vücudunu yavaş yavaş ısıt."
    if k == "technique":
        if b["mode"] == "circuit":
            return f"Form devresi: {join(mv)}. Hız değil, kontrol."
        return f"Teknik çalışma: {join(mv)}. Yavaş ve doğru; hız sonra gelir."
    if k == "shadow":
        return SHADOW_INTRO[sport]
    if k == "bag":
        return MAIN_INTRO["bag"]
    if k == "drill":
        return MAIN_INTRO["drill_" + sport]
    if k == "conditioning":
        if b["mode"] == "round":
            return "Bitirici! Son bir gayret, tempoyu sonuna kadar koru."
        if sport == "general":
            if b["title"].startswith("Test"):
                return "Test devresi. Her istasyonda tekrarlarını say; formunu bozma."
            return f"Her istasyonda {dur(b['work'])} çalış, {dur(b['rest'])} dinlen. Tempo yüksek, form temiz!"
        return "Kondisyon devresi: temiz form, düzenli nefes."
    if k == "cooldown":
        return "Nefesini yavaşlat, esnemeleri zorlamadan yap."
    return clean(b.get("cue") or b["title"])


def join(items):
    items = list(dict.fromkeys(items))
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " ve " + items[-1]


def block_summary(b):
    t = b["title"]
    if b["mode"] == "round":
        if b["rounds"] == 1:
            return f"Sıradaki: {t}, {dur(b['work'])}."
        return f"Sıradaki: {t}. {cap(num(b['rounds']))} raunt, {dur_each(b['work'])}."
    if b["mode"] == "circuit":
        return f"Sıradaki: {t}. {cap(num(b['rounds']))} tur, {num(len(b['moves']))} hareket."
    return f"Sıradaki: {t}. {cap(num(b['rounds']))} set, {num(b['reps'])} tekrar."


def round_start(s):
    r, R = s["round"], s["total"]
    if R == 1:
        return "Başla!"
    if r == R:
        return "Son raunt, başla!"
    return f"{cap(ordinal(r))} raunt, başla!"


# --------------------------------------------------------------------------------------------
# Zamanlama
# --------------------------------------------------------------------------------------------
class Clips:
    def __init__(self, known):
        self.known = known  # id -> ms (ölçülmüş)
        self.used = {}

    def add(self, text):
        text = re.sub(r"\s+", " ", text).strip()
        say = say_text(text)
        cid = hashlib.sha1(say.encode("utf-8")).hexdigest()[:12]
        if cid not in self.used:
            ms = self.known.get(cid, {}).get("ms") if self.known.get(cid, {}).get("measured") else None
            self.used[cid] = dict(text=text, say=say, ms=ms or estimate(say), measured=ms is not None)
        return cid

    def sec(self, ids):
        return sum(self.used[i]["ms"] for i in ids) / 1000.0 + 0.25 * max(0, len(ids) - 1)


def estimate(say):
    return int(len(say) / 14.0 * 1000) + 350


def plan_step(clips, length, start, fixed, flex):
    """start: [(metin, isteğe_bağlı)], fixed: [(sn, metin, zorunlu_mu)], flex: [(istenen_sn, metin)].
    Dönüş: (başlangıç klipleri, {sn: klipler}). Çakışan isteğe bağlı parçalar atılır."""
    limit = length - (10.5 if any(t == length - 10 for t, _, _ in fixed) else 3.5) if length else 1e9
    ids = [(clips.add(t), opt) for t, opt in start]
    while clips.sec([i for i, _ in ids]) > limit and any(o for _, o in ids):
        drop = max(k for k, (_, o) in enumerate(ids) if o)
        ids.pop(drop)
    start_ids = [i for i, _ in ids]
    busy = [(0.0, clips.sec(start_ids) + 0.4)] if start_ids else []
    at = {}

    def free(t, d):
        return all(t >= e or t + d <= s for s, e in busy) and (not length or t + d <= length - 0.5)

    for t, text, must in sorted(fixed, key=lambda x: x[0]):
        cid = clips.add(text)
        d = clips.sec([cid])
        if t <= 0 or (length and t >= length):
            continue
        if free(t, d) or must and all(t >= e for s, e in busy if s <= t):
            busy.append((t, t + d + 0.3))
            at.setdefault(t, []).append(cid)
    for want, text in flex:
        cid = clips.add(text)
        d = clips.sec([cid]) + 0.3
        cands = list(range(int(want), int(length - d - 11))) + list(range(int(want) - 1, 0, -1))
        for t in cands:
            if t > 0 and free(t, d) and (not length or t + d < length - 10.5):
                busy.append((t, t + d))
                at.setdefault(t, []).append(cid)
                break
    return start_ids, {str(k): v for k, v in sorted(at.items())}


def day_cues(sport, prog, day, clips, challenge_n, intro, finish, script):
    st = steps(day)
    phase_of = {d: p for p in prog["phases"] for d in range(p["from"], p["to"] + 1)} if prog else {}
    out = []
    rest_k = ten_k = enc_k = done_k = 0
    seed = day["day"]
    for idx, s in enumerate(st):
        start, fixed, flex = [], [], []
        if s["type"] == "work":
            b, mid, r = s["b"], s["move"], s["round"]
            if idx == 0:
                start += [(t, False) for t in intro]
                start.append((block_intro(sport, b), False))
            if b["mode"] == "round":
                start.append((round_start(s), False))
                pts = points(mid)
                if b["kind"] in ("technique", "shadow", "bag", "drill") or b["moves"] == ["gen_jump_rope"]:
                    tip = pts[(seed + r - 1) % len(pts)]
                    tip_text = f"{short(mid)}: {low(tip)}" if b["kind"] == "technique" else tip
                    if s["calls"]:
                        flex.append((s["calls"][0][0] + 2, tip_text))
                    else:
                        start.append((tip_text, True))
                for t, cm in s["calls"]:
                    fixed.append((t, call_name(cm) + "!", True))
            else:
                first = r == 1
                name = short(mid)
                if s["reps"]:
                    head = f"{name}. {cap(num(s['reps']))} tekrar."
                elif first:
                    head = f"{name}, {dur(s['sec'])}. Başla!"
                elif s["station"] == 1:
                    head = f"{cap(ordinal(r))} tur. {name}, başla!"
                else:
                    head = f"{name}, başla!"
                start.append((head, False))
                pts = points(mid)
                if first and MOVES[mid].get("tip"):
                    start.append((clean(MOVES[mid]["tip"]), True))
                elif pts and (s["sec"] or 0) >= 30:
                    start.append((pts[(seed + r) % len(pts)], True))
            sec = s["sec"] or 0
            mist = mistakes(mid)
            if sec >= 40 and mist and b["kind"] not in ("cooldown",):
                m = mist[(seed + r + s["station"]) % len(mist)]
                flex.append((sec // 2, f"Sık yapılan hata: {low(m)}. Buna dikkat et."))
            if sec >= 120:
                pool = WARM if b["kind"] == "warmup" else ENCOURAGE[sport or "general"]
                flex.append((int(sec * 0.68), pool[enc_k % len(pool)]))
                enc_k += 1
            if sec >= 30 and b["kind"] != "cooldown":
                last = b["mode"] == "round" and r == s["total"] and s["total"] > 1
                calm = sport is None or b["kind"] == "warmup"
                txt = ("Son on saniye." if calm else "Son on saniye, her şeyini ver!" if last
                       else TEN[ten_k % len(TEN)])
                ten_k += 1
                fixed.append((sec - 10, txt, True))
            length = sec
        else:
            n, sec, b = s["next"], s["sec"], s["next"]["b"]
            if s["between"]:
                start.append((f"{DONE[done_k % len(DONE)]} {cap(dur(sec))} dinlen.", False))
                done_k += 1
                start.append((block_summary(b), False))
                start.append((block_intro(sport, b), True))
            elif b["mode"] == "round":
                head = f"Dinlen, {dur(sec)}."
                if b["kind"] == "technique" and len(b["moves"]) > 1:
                    nxt = f"Sıradaki raunt: {short(n['move'])}."
                elif n["round"] == n["total"]:
                    nxt = "Sıradaki: son raunt."
                else:
                    nxt = f"Sıradaki: {ordinal(n['round'])} raunt."
                start += [(head, False), (nxt, False)]
                if sec >= 30:
                    start.append((REST_TIPS[(seed + rest_k) % len(REST_TIPS)], True))
                    rest_k += 1
            else:
                if n["station"] == 1:
                    nxt = f"Sıradaki: {ordinal(n['round'])} tur, {short(n['move'])}."
                else:
                    nxt = f"Sıradaki: {short(n['move'])}."
                start += [(f"Dinlen, {dur(sec)}." if sec >= 20 else "Dinlen.", False), (nxt, False)]
            if sec >= 20:
                fixed.append((sec - 6, "Hazırlan!", True))
            length = sec
        cue_s, cue_at = plan_step(clips, length, start, fixed, flex)
        out.append({"s": cue_s, "at": cue_at} if cue_at else {"s": cue_s})
        script.append((idx, s, cue_s, cue_at))
    fin = [clips.add(t) for t in finish]
    return {"steps": out, "finish": fin}


def finish_texts(sport, prog, w):
    n = challenge_day_of(w)
    out = [f"Tebrikler! Gün {num(n)} tamamlandı."]
    if n == LENGTH:
        out.append(f"Otuz günlük meydan okumayı bitirdin! Artık gerçek bir {SPORT_PERSON[sport]} gibi çalışıyorsun.")
        return out
    ph = next((p for p in prog["phases"] if p["to"] == w), None)
    if ph is not None:
        nxt = next((p for p in prog["phases"] if p["from"] == w + 1), None)
        if nxt:
            out.append(f"{ph['title']} evresi bitti. Sıradaki evre: {nxt['title']}.")
    if (n + 1) in REST_DAYS:
        out.append("Yarın dinlenme günü: kaslarını dinlendir, istersen hafif esneme yap.")
    else:
        nd = next(d for d in prog["days"] if d["day"] == workout_of(n + 1))
        out.append(f"Sıradaki gün: {nd['title']}. Görüşmek üzere!")
    return out


def build(known):
    clips = Clips(known)
    sheets = {}
    scripts = {}
    for sp in SPORTS:
        sid, prog = sp["id"], PROGRAMS[sp["id"]]
        days, rests, script = {}, {}, []
        for day in prog["days"]:
            n = challenge_day_of(day["day"])
            intro = [f"Gün {num(n)}: {day['title']}.", clean(day["focus"])]
            script.append(("day", n, day["title"]))
            days[str(day["day"])] = day_cues(sid, prog, day, clips, n, intro, finish_texts(sid, prog, day["day"]), script)
        for n in REST_DAYS:
            intro = [f"Gün {num(n)}: aktif dinlenme.", "Bugün ağır antrenman yok; birkaç dakika hafif hareket ve esneme."]
            nxt = next(d for d in prog["days"] if d["day"] == workout_of(n + 1))
            fin = [f"Dinlenme günü tamamlandı.", f"Yarın gün {num(n + 1)}: {nxt['title']}. Dinç gel!"]
            script.append(("rest", n, "Aktif Dinlenme"))
            rests[str(n)] = day_cues(None, None, REST_SESSION, clips, n, intro, fin, script)
        sheets[sid] = {"sport": sid, "days": days, "rest": rests}
        scripts[sid] = script
    return clips, sheets, scripts


def write_review(sid, script, clips):
    os.makedirs(BUILD, exist_ok=True)
    lines = [f"# Sesli koç metinleri — {sid}", ""]
    for item in script:
        if item[0] in ("day", "rest"):
            lines += ["", f"## Gün {item[1]} — {item[2]}", ""]
            continue
        idx, s, cs, cat = item
        if s["type"] == "work":
            what = f"{s['b']['title']} · " + (f"raunt {s['round']}/{s['total']}" if s["b"]["mode"] == "round"
                                              else f"tur {s['round']}/{s['total']} · {s['station']}/{s['stations']}")
            what += f" · {short(s['move'])} · {s['sec'] or s['reps']} {'sn' if s['sec'] else 'tekrar'}"
        else:
            what = f"Dinlenme {s['sec']} sn"
        lines.append(f"- **{idx + 1}. {what}**: " + " ".join(clips.used[i]["text"] for i in cs))
        for t, ids in cat.items():
            lines.append(f"  - {t}. sn: " + " ".join(clips.used[i]["text"] for i in ids))
    with open(os.path.join(BUILD, f"script_{sid}.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true", help="yalnızca sayıları yaz, dosya üretme")
    args = ap.parse_args()
    known, voice = {}, None
    mpath = os.path.join(OUT, "manifest.json")
    if os.path.exists(mpath):
        with open(mpath, encoding="utf-8") as fh:
            old = json.load(fh)
        known, voice = old.get("clips", {}), old.get("voice")
    clips, sheets, scripts = build(known)
    # ölçülmüş süreler değiştiyse zamanlamayı bir kez daha kur (kararlı)
    chars = sum(len(c["say"]) for c in clips.used.values())
    secs = sum(c["ms"] for c in clips.used.values()) / 1000
    measured = sum(1 for c in clips.used.values() if c["measured"])
    print(f"{len(clips.used)} klip, {chars} karakter, ~{secs / 60:.0f} dk ses ({measured} ölçülmüş)")
    if args.stats:
        return
    os.makedirs(OUT, exist_ok=True)
    with open(mpath, "w", encoding="utf-8") as fh:
        head = {"version": 1, **({"voice": voice} if voice else {})}
        json.dump({**head, "clips": dict(sorted(clips.used.items()))}, fh, ensure_ascii=False, indent=0)
        fh.write("\n")
    for sid, sheet in sheets.items():
        with open(os.path.join(OUT, f"cues_{sid}.json"), "w", encoding="utf-8") as fh:
            json.dump(sheet, fh, ensure_ascii=False, separators=(",", ":"))
            fh.write("\n")
        write_review(sid, scripts[sid], clips)
    print("->", os.path.relpath(OUT, ROOT), "ve", os.path.relpath(BUILD, ROOT))


if __name__ == "__main__":
    main()
