#!/usr/bin/env python3
"""Koç cümlelerini Türkçe yapay zekâ sesiyle kaydeder (uygulama bunları çevrimdışı çalar).

Önce make_voice.py çalışmış olmalı (assets/voice/manifest.json). İki motor:
  piper      (ücretsiz): açık kaynak Piper'ın Türkçe sesi (tr_TR-dfki-medium; ses lisansı ticari olmayan).
             Model dosyaları tools/voice/build/piper; .github/workflows/voice.yml indirir ve çalıştırır.
  chatterbox (ücretsiz, MIT, ticari serbest): Resemble AI Chatterbox Multilingual, Türkçe; hazır ses ya da
             --voice <referans.wav>. Her klip faster-whisper ile yazıya dökülüp denetlenir.
             .github/workflows/voice-chatterbox.yml paralel parçalarla çalıştırır.
  google (isteğe bağlı): Google Cloud TTS; anahtar yalnızca GOOGLE_TTS_API_KEY ortam değişkeninden okunur.

  python3 tools/voice/synthesize.py --samples      # aday seslerle örnek cümleler (tools/voice/samples)
  python3 tools/voice/synthesize.py --voice tr_TR-fahrettin-medium
  python3 tools/voice/make_voice.py                # ölçülen sürelerle zamanlamayı yeniden kur
  python3 tools/voice/synthesize.py --engine chatterbox --audit --out yeni/   # kayıtlıları dinle, bozukları yenile
  python3 tools/voice/synthesize.py --report yeni/  # qa_*.json -> tools/voice/qa_report.md

Her klip: ham ses -> ffmpeg ile baş/son sessizlik kırpma, -16 LUFS ses seviyesi, sonda 0.15 sn boşluk,
mono Opus 24 kbps -> app/src/main/assets/voice/clips/<id>.ogg. Ham sesler tools/voice/build/raw'da önbelleklenir.
"""
import argparse
import base64
import hashlib
import concurrent.futures as cf
import json
import os
import random
import re
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
    "Bugünün konusu: kafa kaçırma ve eğilme. Kafa kaçırırken baş gard çizgisinden az kayar; eğilirken dizlerden in, belden değil.",
    "Üçüncü raunt, başla! Sol kroşe: kolun bir kanca gibi sabit kalır; dönüşü gövde yapar.",
    "Sol direk! Sağ direk! Sol kroşe! Son on saniye, her şeyini ver!",
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


class ChatterboxEngine:
    """Resemble AI Chatterbox Multilingual (MIT): hazır ses ya da bir referans kayıttan ses; enerjik koç tonu.
    Kısa cümlelerde nadiren bozulabildiği için her klip ASR ile denetlenir ve gerekirse farklı tohumla yeniden üretilir."""
    ext = ".wav"
    asr = True

    def __init__(self, voice):
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        torch.set_num_threads(os.cpu_count() or 4)
        self.torch = torch
        self.voice = voice or "builtin"
        self.name = voice_name("chatterbox", self.voice)
        self.model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
        if self.voice != "builtin":
            if not os.path.exists(self.voice):
                sys.exit(f"Referans ses yok: {self.voice}")
            self.model.prepare_conditionals(self.voice, exaggeration=0.6)

    def write(self, text, path, attempt=0):
        import torchaudio
        seed = int(hashlib.sha1(f"{text}|{attempt}".encode()).hexdigest()[:8], 16)
        self.torch.manual_seed(seed)
        random.seed(seed)
        wav = self.model.generate(text, language_id="tr", exaggeration=0.6, cfg_weight=0.4, temperature=0.8)
        torchaudio.save(path, wav, self.model.sr)


def voice_name(kind, voice):
    if kind == "chatterbox":
        if not voice or voice == "builtin":
            return "chatterbox:builtin"
        with open(voice, "rb") as fh:
            return "chatterbox:ref-" + hashlib.sha1(fh.read()).hexdigest()[:8]
    return f"{kind}:{voice}"


def make_engine(kind, voice):
    if kind == "google":
        key()
        return GoogleEngine(voice)
    if kind == "chatterbox":
        return ChatterboxEngine(voice)
    return PiperEngine(voice or PIPER_VOICES[0])


# --------------------------------------------------------------------------------------------
# Otomatik dinleme kontrolü: klip yazıya dökülür, okunması istenen metinle karşılaştırılır
# --------------------------------------------------------------------------------------------
_TR = str.maketrans({"İ": "i", "I": "ı"})
LIMIT = 0.3        # kayıt sırasında: bunu aşan deneme yeniden üretilir
AUDIT_LIMIT = 0.2  # denetimde: bunu aşan (ya da tekrarlı/süresi aykırı) klip yeniden kaydedilir


def _spell(m):
    n = int(m.group())
    if n >= 1000:
        return m.group()
    sys.path.insert(0, HERE)
    from make_voice import num
    return f" {num(n)} "


def norm(s):
    """Küçük harf, noktalama yok; ASR'nin yazdığı rakamlar Türkçe okunuşa çevrilir ("16" -> "on altı")."""
    s = re.sub(r"\d+", _spell, s.translate(_TR).lower())
    s = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in s)
    return " ".join(s.split())


def repeated(ref, hyp):
    """Seste metinde olmayan bir tekrar var mı ("Dinç gel. Dinç gel.")? Model bazen cümle sonunu yineler."""
    r, h = norm(ref).split(), norm(hyp).split()
    rs = f" {' '.join(r)} "
    for n in range(1, 5):
        for i in range(len(h) - 2 * n + 1):
            a = h[i:i + n]
            if a == h[i + n:i + 2 * n] and len("".join(a)) >= 3 and f" {' '.join(a + a)} " not in rs:
                return True
    return False


def judge_score(text, heard, seconds):
    """Dönüş: (puan, neden). Puan boşluksuz karakter hata oranı; tekrar ya da aykırı süre +1."""
    score, why = cer(text, heard), []
    if repeated(text, heard):
        score += 1.0
        why.append("tekrar")
    est = max(0.6, len(text) / 14.0)
    if not (0.35 * est <= seconds <= 2.5 * est + 1.0):
        score += 1.0  # aşırı kısa/uzun: büyük olasılıkla bozuk
        why.append("süre")
    return score, ",".join(why)


def cer(ref, hyp):
    # boşluklar sayılmaz: ASR'nin kelime bölmesi ("sıra da ki") hata değildir
    a, b = norm(ref).replace(" ", ""), norm(hyp).replace(" ", "")
    if not a:
        return 0.0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        prev = cur
    return prev[-1] / len(a)


class Judge:
    def __init__(self):
        from faster_whisper import WhisperModel
        self.model = WhisperModel("small", device="cpu", compute_type="int8")

    def hear(self, path):
        segs, _ = self.model.transcribe(path, language="tr", beam_size=1, vad_filter=False,
                                        condition_on_previous_text=False)
        return " ".join(s.text for s in segs).strip()


def wav_seconds(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out or 0)


def record(eng, judge, text, raw, attempts=4, limit=LIMIT, first=0):
    """Klibi üretir; ASR varsa okunanla metni karşılaştırıp en iyi denemeyi tutar. Dönüş: (puan, duyulan, neden).
    [first]: ilk denemenin numarası (tohum); yeniden kayıtta önceki denemelerden farklı ses çıksın diye."""
    tmp = raw[: -len(eng.ext)] + ".try{}" + eng.ext
    best = None
    for k in range(first, first + (attempts if judge else 1)):
        path = tmp.format(k)
        if isinstance(eng, ChatterboxEngine):
            eng.write(text, path, attempt=k)
        else:
            eng.write(text, path)
        if not judge:
            best = (0.0, "", "", path)
            break
        heard = judge.hear(path)
        score, why = judge_score(text, heard, wav_seconds(path))
        if best is None or score < best[0]:
            if best:
                os.remove(best[3])
            best = (score, heard, why, path)
        else:
            os.remove(path)
        if score <= limit:
            break
    os.replace(best[3], raw)
    return best[0], best[1], best[2]


def samples(kind, voice=None):
    os.makedirs(SAMPLES, exist_ok=True)
    text = " ".join(SAMPLE_LINES)
    voices = PIPER_VOICES if kind == "piper" else [voice or "builtin"] if kind == "chatterbox" else VOICES
    made = []
    for v in voices:
        try:
            eng = make_engine(kind, v)
        except SystemExit as e:
            print(f"{v}: {e}", file=sys.stderr)
            continue
        label = eng.name.replace(":", "-") if kind == "chatterbox" else v
        raw = os.path.join(SAMPLES, f"{label}.raw{eng.ext}")
        if kind == "chatterbox":
            # uzun metinde kalite düşer: cümle cümle üret, araya kısa boşluk koyarak birleştir
            judge = Judge()
            parts = []
            for i, line in enumerate(SAMPLE_LINES):
                part = os.path.join(SAMPLES, f"{label}.part{i}{eng.ext}")
                score, heard, _ = record(eng, judge, say_line(line), part)
                print(f"  cümle {i + 1}: CER {score:.2f} · duyulan: {heard}", flush=True)
                parts.append(part)
            inputs = sum((["-i", p] for p in parts), [])
            n = len(parts)
            graph = "".join(f"[{i}]apad=pad_dur=0.35[a{i}];" for i in range(n)) + "".join(f"[a{i}]" for i in range(n))
            subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph + f"concat=n={n}:v=0:a=1",
                            raw], check=True)
            for p in parts:
                os.remove(p)
        else:
            eng.write(text, raw)
        v = label
        out = os.path.join(SAMPLES, f"{v}.m4a")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "loudnorm=I=-16", "-ac", "1", "-c:a", "aac",
                        "-b:a", "64k", out], check=True)
        os.remove(raw)
        made.append(v)
        print("örnek:", v, flush=True)
    listed = sorted(f for f in os.listdir(SAMPLES) if f.endswith(".m4a"))
    with open(os.path.join(SAMPLES, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("# Koç sesi örnekleri\n\n" + text + "\n\n" + "\n".join(f"- {f}" for f in listed) + "\n\n"
                 + LICENSES)


def mean_volume(path):
    out = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    for line in out.splitlines():
        if "mean_volume" in line:
            return float(line.split(":")[1].split()[0])
    return -99.0


LICENSES = """## Lisanslar
- `piper-tr_TR-dfki-medium`: Piper (GPL-3 motor); ses modeli DFKI veri setiyle eğitildi, CC BY-NC-SA 4.0
  (ticari olmayan kullanım).
- `chatterbox-*`: Resemble AI Chatterbox Multilingual, MIT lisansı (ticari kullanım serbest).
"""


def say_line(line):
    sys.path.insert(0, HERE)
    from make_voice import say_text
    return say_text(line)


def finalize(manifest, mpath, name):
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
        p = os.path.join(CLIPS, f"{cid}.ogg")
        v = mean_volume(p) if os.path.exists(p) else -99
        if v < -45:
            bad.append(f"{cid}: sessiz ({v} dB)")
    if bad:
        sys.exit("Kalite kontrolü geçmedi:\n" + "\n".join(bad[:30]))
    manifest["voice"] = name
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=0)
        fh.write("\n")
    total = sum(c["ms"] for c in manifest["clips"].values()) / 60000
    size = sum(os.path.getsize(os.path.join(CLIPS, f)) for f in os.listdir(CLIPS)) / 1e6
    print(f"tamam: {len(manifest['clips'])} klip, {total:.1f} dk ses, {size:.1f} MB. Şimdi: make_voice.py", flush=True)


def shard_of(ids, shard):
    if not shard:
        return ids, "all"
    i, n = (int(x) for x in shard.split("/"))
    return ids[i::n], f"{i}of{n}"


def audit(manifest, args):
    """Kayıtlı klipleri yazıya döküp denetler; eşiği aşan, tekrarlı ya da süresi aykırı olanları yeni tohumlarla
    yeniden kaydeder ve yalnız daha iyi çıkanı --out klasörüne yazar. QA kaydı: <out>/qa_<parça>.json."""
    ids, tag = shard_of(sorted(manifest["clips"]), args.shard)
    out_dir = args.out or CLIPS
    os.makedirs(out_dir, exist_ok=True)
    judge = Judge()
    qa, flagged = {}, []
    for k, cid in enumerate(ids, 1):
        p = os.path.join(CLIPS, f"{cid}.ogg")
        text = manifest["clips"][cid]["say"]
        heard = judge.hear(p)
        score, why = judge_score(text, heard, wav_seconds(p))
        qa[cid] = dict(text=text, heard=heard, cer=round(score, 3), why=why)
        if score > AUDIT_LIMIT:
            flagged.append(cid)
    print(f"dinlendi: {len(ids)} klip, yeniden kaydedilecek {len(flagged)}", flush=True)
    if flagged:
        eng = make_engine(args.engine, args.voice)
        if manifest.get("voice") != eng.name:
            sys.exit(f"Klipler {manifest.get('voice')} ile kaydedilmiş, denetim sesi {eng.name}: önce tam kayıt yapın.")
        tmp = tempfile.mkdtemp()
        for cid in flagged:
            old, raw = qa[cid], os.path.join(tmp, cid + eng.ext)
            score, heard, why = record(eng, judge, old["text"], raw, attempts=6, limit=AUDIT_LIMIT, first=4)
            better = score < old["cer"]
            if better:
                post(raw, os.path.join(out_dir, f"{cid}.ogg"))
                qa[cid] = dict(text=old["text"], heard=heard, cer=round(score, 3), why=why, was=old["cer"],
                               was_heard=old["heard"], was_why=old["why"])
            os.remove(raw)
            print(f"  {old['cer']:.2f} -> {score:.2f} {'yenilendi' if better else 'eskisi kaldı'}  '{old['text']}'"
                  f"  ->  '{heard}'", flush=True)
    with open(os.path.join(out_dir, f"qa_{tag}.json"), "w", encoding="utf-8") as fh:
        json.dump(qa, fh, ensure_ascii=False, indent=1)


def report(folder):
    """Parça QA kayıtlarını birleştirir, özeti yazdırır ve tools/voice/qa_report.md'yi yazar."""
    import glob
    qa = {}
    for f in sorted(glob.glob(os.path.join(folder, "qa_*.json"))):
        with open(f, encoding="utf-8") as fh:
            qa.update(json.load(fh))
    if not qa:
        sys.exit(f"{folder}: QA kaydı yok")
    vals = [q["cer"] for q in qa.values()]
    fixed = [q for q in qa.values() if "was" in q]
    weak = sorted((q for q in qa.values() if q["cer"] > AUDIT_LIMIT), key=lambda q: -q["cer"])
    avg = sum(min(v, 1.0) for v in vals) / len(vals)
    head = (f"{len(qa)} klip, ort. hata {avg:.3f}, yeniden kaydedilen {len(fixed)}, "
            f"hâlâ eşiği ({AUDIT_LIMIT}) aşan {len(weak)} (tekrar: {sum('tekrar' in q.get('why', '') for q in weak)}, "
            f"süre: {sum('süre' in q.get('why', '') for q in weak)})")
    print("ASR:", head, flush=True)
    lines = ["# Koç sesi otomatik dinleme raporu", "",
             "Her klip faster-whisper (small) ile yazıya döküldü ve okunması istenen metinle karşılaştırıldı. Puan: "
             "boşluksuz karakter hata oranı (ASR rakamları okunuşa çevrilir); metinde olmayan bir tekrar ya da "
             "aykırı süre +1. ASR da yanılabilir: listedekiler kulakla kontrol edilmeli.", "", head, ""]
    if weak:
        lines += ["## Eşiği aşanlar", "", "| puan | neden | metin | duyulan |", "|---|---|---|---|"]
        lines += [f"| {q['cer']:.2f} | {q.get('why') or '-'} | {q['text']} | {q['heard']} |" for q in weak]
    if fixed:
        lines += ["", "## Yeniden kaydedilenler", "", "| önce | sonra | metin | önce duyulan |", "|---|---|---|---|"]
        lines += [f"| {q['was']:.2f} | {q['cer']:.2f} | {q['text']} | {q['was_heard']} |"
                  for q in sorted(fixed, key=lambda q: -q["was"])]
    with open(os.path.join(HERE, "qa_report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["piper", "google", "chatterbox"], default="piper")
    ap.add_argument("--shard", default=None, help="i/N: yalnız i. parçayı kaydet (paralel işler için)")
    ap.add_argument("--out", default=None, help="klipleri bu klasöre yaz (parça işleri)")
    ap.add_argument("--finalize", action="store_true", help="kayıtlı kliplerin sürelerini ölç, manifesti yaz")
    ap.add_argument("--asr", action="store_true", help="her klibi yazıya döküp metinle karşılaştır (chatterbox'ta hep açık)")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--samples", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="en fazla bu kadar klip (deneme için)")
    ap.add_argument("--redo", action="store_true", help="var olan klipleri de yeniden kaydet (ses değişince)")
    ap.add_argument("--audit", action="store_true",
                    help="kayıtlı klipleri dinle; bozuk olanları yeniden kaydet (--out klasörüne yalnız değişenler)")
    ap.add_argument("--report", default=None, metavar="KLASÖR", help="parçaların qa_*.json dosyalarından rapor yaz")
    args = ap.parse_args()
    if args.samples:
        return samples(args.engine, args.voice)
    if args.report:
        return report(args.report)
    mpath = os.path.join(VOICE_DIR, "manifest.json")
    with open(mpath, encoding="utf-8") as fh:
        manifest = json.load(fh)
    if args.audit:
        return audit(manifest, args)
    if args.finalize:
        return finalize(manifest, mpath, voice_name(args.engine, args.voice))
    eng = make_engine(args.engine, args.voice)
    print("ses:", eng.name, flush=True)
    if manifest.get("voice") and manifest["voice"] != eng.name:
        args.redo = True  # başka bir sesle kaydedilmiş klipler karışmasın
    out_dir = args.out or CLIPS
    os.makedirs(out_dir, exist_ok=True)
    raw_dir = os.path.join(RAW, eng.name.replace(":", "_"))
    os.makedirs(raw_dir, exist_ok=True)
    ids, _ = shard_of(sorted(manifest["clips"]), args.shard)
    if args.shard:
        args.redo = True
    todo = [cid for cid in ids if args.redo or not os.path.exists(os.path.join(out_dir, f"{cid}.ogg"))]
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(todo)} klip kaydedilecek ({len(ids) - len(todo)} hazır)", flush=True)

    # 1) ham ses (yerel modeller tek süreçte sırayla); gerekirse ASR denetimi ve yeniden deneme
    judge = Judge() if (args.asr or getattr(eng, "asr", False)) else None
    raws, qa = {}, {}
    for k, cid in enumerate(todo, 1):
        raw = os.path.join(raw_dir, cid + eng.ext)
        text = manifest["clips"][cid]["say"]
        if not os.path.exists(raw):
            score, heard, why = record(eng, judge, text, raw)
            qa[cid] = dict(text=text, heard=heard, cer=round(score, 3), why=why)
        raws[cid] = raw
        if k % 25 == 0 or k == len(todo):
            done = [q["cer"] for q in qa.values()]
            info = f", ort. CER {sum(done) / len(done):.3f}" if judge and done else ""
            print(f"  ses {k}/{len(todo)}{info}", flush=True)
    if judge:
        os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
        tag = args.shard.replace("/", "of") if args.shard else "all"
        with open(os.path.join(out_dir, f"qa_{tag}.json"), "w", encoding="utf-8") as fh:
            json.dump(qa, fh, ensure_ascii=False, indent=1)
        worst = sorted(qa.items(), key=lambda kv: -kv[1]["cer"])[:15]
        print("En zayıf klipler:", flush=True)
        for cid, q in worst:
            print(f"  {q['cer']:.2f}  '{q['text']}'  ->  '{q['heard']}'", flush=True)
        over = sum(1 for q in qa.values() if q["cer"] > LIMIT)
        print(f"Eşiği ({LIMIT}) aşan: {over}/{len(qa)}", flush=True)

    # 2) son işlem paralel
    def one(cid):
        out = os.path.join(out_dir, f"{cid}.ogg")
        post(raws[cid], out + ".tmp.ogg")
        os.replace(out + ".tmp.ogg", out)

    with cf.ThreadPoolExecutor(args.jobs) as ex:
        list(ex.map(one, todo))
    if args.shard or args.out:
        print(f"parça bitti: {len(todo)} klip -> {out_dir}", flush=True)
        return
    # 3) süreler ve kalite kontrolü
    finalize(manifest, mpath, eng.name)


if __name__ == "__main__":
    main()
