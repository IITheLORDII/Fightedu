#!/usr/bin/env python3
"""Koç cümlelerini Türkçe yapay zekâ sesiyle kaydeder (uygulama bunları çevrimdışı çalar).

Önce make_voice.py çalışmış olmalı (assets/voice/manifest.json). İki motor:
  piper  (varsayılan, ücretsiz): açık kaynak Piper, Türkçe sesler (tr_TR-fahrettin/-dfki/-fettah-medium).
         Model dosyaları tools/voice/build/piper/<ses>.onnx(.json); .github/workflows/voice.yml indirir ve çalıştırır.
  google (isteğe bağlı): Google Cloud TTS; anahtar yalnızca GOOGLE_TTS_API_KEY ortam değişkeninden okunur.

  python3 tools/voice/synthesize.py --samples      # aday seslerle örnek cümleler (tools/voice/samples)
  python3 tools/voice/synthesize.py --voice tr_TR-fahrettin-medium
  python3 tools/voice/make_voice.py                # ölçülen sürelerle zamanlamayı yeniden kur

Her klip: ham ses -> ffmpeg ile baş/son sessizlik kırpma, -16 LUFS ses seviyesi, sonda 0.15 sn boşluk,
mono Opus 24 kbps -> app/src/main/assets/voice/clips/<id>.ogg. Ham sesler tools/voice/build/raw'da önbelleklenir.
"""
import argparse
import base64
import concurrent.futures as cf
import json
import os
import random
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
VOICE_DIR = os.path.join(ROOT, "app", "src", "main", "assets", "voice")
CLIPS = os.path.join(VOICE_DIR, "clips")
RAW = os.path.join(HERE, "build", "raw")
SAMPLES = os.path.join(HERE, "samples")
PIPER_DIR = os.path.join(HERE, "build", "piper")
PIPER_VOICES = sorted(f[:-5] for f in os.listdir(PIPER_DIR) if f.endswith(".onnx")) if os.path.isdir(PIPER_DIR) else []
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


class GoogleEngine:
    ext = ".ogg"

    def __init__(self, voice=None):
        self.voice = voice or pick_voice()
        self.name = self.voice

    def write(self, text, path):
        with open(path, "wb") as fh:
            fh.write(synth(text, self.voice))


class PiperEngine:
    """Açık kaynak Piper; enerjik ama net bir koç temposu (length_scale < 1 hızlı)."""
    ext = ".wav"

    def __init__(self, voice):
        from piper import PiperVoice, SynthesisConfig
        model = os.path.join(PIPER_DIR, f"{voice}.onnx")
        if not os.path.exists(model):
            sys.exit(f"Piper modeli yok: {model} (voice.yml indirir)")
        self.voice = PiperVoice.load(model)
        self.cfg = SynthesisConfig(length_scale=0.92, noise_scale=0.6, noise_w_scale=0.8)
        self.name = f"piper:{voice}"

    def write(self, text, path):
        with wave.open(path, "wb") as wf:
            self.voice.synthesize_wav(text, wf, syn_config=self.cfg)


def make_engine(kind, voice):
    if kind == "google":
        key()
        return GoogleEngine(voice)
    return PiperEngine(voice or PIPER_VOICES[0])


def samples(kind):
    os.makedirs(SAMPLES, exist_ok=True)
    text = " ".join(SAMPLE_LINES)
    voices = PIPER_VOICES if kind == "piper" else VOICES
    made = []
    for v in voices:
        try:
            eng = make_engine(kind, v)
        except SystemExit as e:
            print(f"{v}: {e}", file=sys.stderr)
            continue
        raw = os.path.join(SAMPLES, f"{v}.raw{eng.ext}")
        eng.write(text, raw)
        out = os.path.join(SAMPLES, f"{v}.m4a")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-16", "-ac", "1", "-c:a", "aac",
                        "-b:a", "64k", out], check=True)
        os.remove(raw)
        made.append(v)
        print("örnek:", v, flush=True)
    with open(os.path.join(SAMPLES, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("# Koç sesi örnekleri\n\n" + text + "\n\n" + "\n".join(f"- {v}.m4a" for v in made) + "\n")


def mean_volume(path):
    out = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    for line in out.splitlines():
        if "mean_volume" in line:
            return float(line.split(":")[1].split()[0])
    return -99.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["piper", "google"], default="piper")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--samples", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="en fazla bu kadar klip (deneme için)")
    ap.add_argument("--redo", action="store_true", help="var olan klipleri de yeniden kaydet (ses değişince)")
    args = ap.parse_args()
    if args.samples:
        return samples(args.engine)
    mpath = os.path.join(VOICE_DIR, "manifest.json")
    with open(mpath, encoding="utf-8") as fh:
        manifest = json.load(fh)
    eng = make_engine(args.engine, args.voice)
    print("ses:", eng.name, flush=True)
    if manifest.get("voice") and manifest["voice"] != eng.name:
        args.redo = True  # başka bir sesle kaydedilmiş klipler karışmasın
    os.makedirs(CLIPS, exist_ok=True)
    raw_dir = os.path.join(RAW, eng.name.replace(":", "_"))
    os.makedirs(raw_dir, exist_ok=True)
    todo = [cid for cid in manifest["clips"] if args.redo or not os.path.exists(os.path.join(CLIPS, f"{cid}.ogg"))]
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(todo)} klip kaydedilecek ({len(manifest['clips']) - len(todo)} hazır)", flush=True)

    # 1) ham ses (Piper tek süreçte sırayla; Google ağ çağrısı)
    raws = {}
    for i, cid in enumerate(todo, 1):
        raw = os.path.join(raw_dir, cid + eng.ext)
        if not os.path.exists(raw):
            eng.write(manifest["clips"][cid]["say"], raw + ".tmp")
            os.replace(raw + ".tmp", raw)
        raws[cid] = raw
        if i % 100 == 0 or i == len(todo):
            print(f"  ses {i}/{len(todo)}", flush=True)

    # 2) son işlem paralel
    def one(cid):
        out = os.path.join(CLIPS, f"{cid}.ogg")
        post(raws[cid], out + ".tmp.ogg")
        os.replace(out + ".tmp.ogg", out)

    with cf.ThreadPoolExecutor(args.jobs) as ex:
        list(ex.map(one, todo))

    # 3) süreler ve kalite kontrolü
    bad = []
    for cid, c in manifest["clips"].items():
        p = os.path.join(CLIPS, f"{cid}.ogg")
        if not os.path.exists(p):
            bad.append(f"{cid}: dosya yok")
            continue
        c["ms"], c["measured"] = duration_ms(p), True
        if c["ms"] < 300:
            bad.append(f"{cid}: çok kısa ({c['ms']} ms) '{c['text']}'")
    for cid in random.Random(1).sample(sorted(manifest["clips"]), min(40, len(manifest["clips"]))):
        v = mean_volume(os.path.join(CLIPS, f"{cid}.ogg"))
        if v < -45:
            bad.append(f"{cid}: sessiz ({v} dB)")
    if bad:
        sys.exit("Kalite kontrolü geçmedi:\n" + "\n".join(bad[:30]))
    manifest["voice"] = eng.name
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=0)
        fh.write("\n")
    total = sum(c["ms"] for c in manifest["clips"].values()) / 60000
    size = sum(os.path.getsize(os.path.join(CLIPS, f)) for f in os.listdir(CLIPS)) / 1e6
    print(f"tamam: {len(manifest['clips'])} klip, {total:.1f} dk ses, {size:.1f} MB. Şimdi: make_voice.py", flush=True)


if __name__ == "__main__":
    main()
