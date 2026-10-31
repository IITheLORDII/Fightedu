#!/usr/bin/env python3
"""Koç cümlelerini Google Cloud Text-to-Speech'in Türkçe sesiyle kaydeder (çevrimdışı çalınmak üzere).

Önce make_voice.py çalışmış olmalı (assets/voice/manifest.json). API anahtarı yalnızca GOOGLE_TTS_API_KEY ortam
değişkeninden okunur; hiçbir dosyaya ya da çıktıya yazılmaz.

  python3 tools/voice/synthesize.py --samples      # aday seslerle örnek cümleler (karşılaştırma sayfası)
  python3 tools/voice/synthesize.py                # eksik tüm klipleri kaydet, süreleri manifeste yaz
  python3 tools/voice/make_voice.py                # ölçülen sürelerle zamanlamayı yeniden kur

Her klip: Google'dan OGG_OPUS -> ffmpeg ile baş/son sessizlik kırpma, -16 LUFS ses seviyesi, sonda 0.15 sn boşluk,
mono Opus 24 kbps -> app/src/main/assets/voice/clips/<id>.ogg. Ham yanıtlar tools/voice/build/raw'da önbelleklenir.
"""
import argparse
import base64
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
VOICE_DIR = os.path.join(ROOT, "app", "src", "main", "assets", "voice")
CLIPS = os.path.join(VOICE_DIR, "clips")
RAW = os.path.join(HERE, "build", "raw")
SAMPLES = os.path.join(ROOT, "tools", "render3d", "build", "preview", "voices")
ENDPOINT = "https://texttospeech.googleapis.com/v1/text:synthesize"

# enerjik erkek koç sesi; ilki reddedilirse sıradakiler denenir
VOICES = ["tr-TR-Chirp3-HD-Fenrir", "tr-TR-Chirp3-HD-Puck", "tr-TR-Chirp3-HD-Orus", "tr-TR-Chirp3-HD-Alnilam",
          "tr-TR-Wavenet-E", "tr-TR-Wavenet-B"]
SAMPLE_LINES = [
    "Gün on üç: Slip ve Roll. Kafa gard çizgisinden az kayar; roll'da dizlerden in, belden değil.",
    "Üçüncü raunt, başla! Sol kroşe: kolun bir kanca gibi sabit kalır; dönüşü gövde yapar.",
    "Bir iki! Sol kroşe! Son on saniye, her şeyini ver!",
    "Dinlen, kırk beş saniye. Burnundan nefes al, ağzından ver. Hazırlan!",
]


def key():
    k = os.environ.get("GOOGLE_TTS_API_KEY", "").strip()
    if not k:
        sys.exit("GOOGLE_TTS_API_KEY ortam değişkeni yok. Ortam ayarlarına ekleyip yeni oturumda çalıştır.")
    return k


def synth(text, voice, rate=1.05):
    """OGG_OPUS bayt; hata mesajlarında anahtar görünmez."""
    body = {"input": {"text": text}, "voice": {"languageCode": "tr-TR", "name": voice},
            "audioConfig": {"audioEncoding": "OGG_OPUS", "sampleRateHertz": 24000}}
    if rate:
        body["audioConfig"]["speakingRate"] = rate
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json; charset=utf-8", "X-Goog-Api-Key": key()})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return base64.b64decode(json.load(resp)["audioContent"])
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 500, 503) and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            if e.code == 400 and rate and "speaking" in detail.lower():
                return synth(text, voice, rate=None)  # bu ses hız ayarını desteklemiyor
            raise RuntimeError(f"Google TTS {e.code}: {detail}") from None
        except urllib.error.URLError as e:
            if attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"Ağ hatası: {e.reason}") from None


def pick_voice():
    for v in [os.environ.get("FIGHTEDU_TTS_VOICE")] + VOICES:
        if not v:
            continue
        try:
            synth("Hazır mısın?", v)
            return v
        except RuntimeError as e:
            print(f"{v}: kullanılamıyor ({e})", file=sys.stderr)
    sys.exit("Hiçbir Türkçe ses kullanılamadı.")


def post(raw_path, out_path):
    """Sessizlik kırp, ses seviyesini eşitle, sona kısa boşluk ekle, mono Opus 24 kbps."""
    af = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,"
          "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,"
          "loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur=0.15")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw_path, "-af", af, "-ac", "1", "-ar", "24000",
                    "-c:a", "libopus", "-b:a", "24k", "-application", "voip", out_path], check=True)


def duration_ms(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout.strip()
    return int(round(float(out) * 1000))


def samples():
    os.makedirs(SAMPLES, exist_ok=True)
    text = " ".join(SAMPLE_LINES)
    rows = []
    for v in VOICES:
        try:
            data = synth(text, v)
        except RuntimeError as e:
            print(f"{v}: {e}", file=sys.stderr)
            continue
        raw = os.path.join(SAMPLES, f"{v}.raw.ogg")
        with open(raw, "wb") as fh:
            fh.write(data)
        m4a = os.path.join(SAMPLES, f"{v}.m4a")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-16", "-c:a", "aac", "-b:a", "96k",
                        m4a], check=True)
        rows.append(v)
        print("örnek:", v)
    with open(os.path.join(SAMPLES, "index.html"), "w", encoding="utf-8") as fh:
        fh.write("<!DOCTYPE html><meta charset=utf-8><title>Koç sesi örnekleri</title><body style='font-family:sans-serif'>")
        fh.write(f"<p>{text}</p>" + "".join(f"<h3>{v}</h3><audio controls src='{v}.m4a'></audio>" for v in rows))
    print("->", SAMPLES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="en fazla bu kadar klip (deneme için)")
    args = ap.parse_args()
    key()
    if args.samples:
        return samples()
    mpath = os.path.join(VOICE_DIR, "manifest.json")
    with open(mpath, encoding="utf-8") as fh:
        manifest = json.load(fh)
    voice = pick_voice()
    print("ses:", voice)
    os.makedirs(CLIPS, exist_ok=True)
    os.makedirs(os.path.join(RAW, voice), exist_ok=True)
    todo = [cid for cid in manifest["clips"] if not os.path.exists(os.path.join(CLIPS, f"{cid}.ogg"))]
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(todo)} klip kaydedilecek ({len(manifest['clips']) - len(todo)} hazır)")

    def one(cid):
        raw = os.path.join(RAW, voice, f"{cid}.ogg")
        if not os.path.exists(raw):
            data = synth(manifest["clips"][cid]["say"], voice)
            with tempfile.NamedTemporaryFile(dir=os.path.dirname(raw), delete=False) as tmp:
                tmp.write(data)
            os.replace(tmp.name, raw)
        out = os.path.join(CLIPS, f"{cid}.ogg")
        post(raw, out + ".tmp.ogg")
        os.replace(out + ".tmp.ogg", out)
        return cid

    done = 0
    with cf.ThreadPoolExecutor(args.jobs) as ex:
        for f in cf.as_completed([ex.submit(one, c) for c in todo]):
            f.result()
            done += 1
            if done % 50 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)}", flush=True)
    # süreleri ölç
    for cid, c in manifest["clips"].items():
        p = os.path.join(CLIPS, f"{cid}.ogg")
        if os.path.exists(p):
            c["ms"], c["measured"] = duration_ms(p), True
    manifest["voice"] = voice
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=0)
        fh.write("\n")
    total = sum(c["ms"] for c in manifest["clips"].values() if c.get("measured")) / 60000
    print(f"tamam: {total:.1f} dk ses. Şimdi: python3 tools/voice/make_voice.py")


if __name__ == "__main__":
    main()
