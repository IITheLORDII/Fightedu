# FightEdu 🥊🦵🤼🥋

**Boks, Kick Boks, Güreş ve Tekvando** için yeni başlayanları **8 haftalık (2 ay)** programla
temel seviyeye getiren, tamamen çevrimdışı çalışan bir Android uygulaması.

## Özellikler

- **Kişiye göre program:** Kullanıcı sporu, haftada kaç gün (3/4/5) ve **hangi günler** çalışacağını
  seçer. 8 haftalık program bu günlere otomatik yerleştirilir ve takvim tarihleri hesaplanır.
- **4 evreli müfredat (her spor için):**
  1. Hafta 1-2 – Temeller (duruş, ayak oyunu, temel teknikler)
  2. Hafta 3-4 – Yeni teknikler ve savunma
  3. Hafta 5-6 – Akıcılık, kombinasyonlar ve raunt temposu
  4. Hafta 7-8 – Pekiştirme ve **değerlendirme seansı**
- **Gün sayısına göre seanslar:** 3 gün → A, B, C · 4 gün → + D (teknik tekrar) · 5 gün → + E (kondisyon).
  Her evrenin 2. haftasında tekrar/süreler %15 artar (kademeli yüklenme).
- **Gerçekçi hareket videoları:** 63 hareketin her biri, gerçek insan oranlarına ve kas yapısına sahip
  3B bir sporcuyla (stüdyo ışığında render edilmiş, döngüsel kısa video) gösterilir. Kıyafetler spora
  göredir: boksta şort, eldiven ve bot; kick boksta tay şortu ve eldiven; güreşte mayo ve güreş
  ayakkabısı; tekvandoda dobok ve kuşak. Kalça/omuz dönüşü, ayak pivotu ve ağırlık aktarımı görünür;
  vuruşlar kum torbasına veya partnere yapılır, savunmalar gelen saldırıya karşı gösterilir
  (yavaş çekim seçeneği). Her hareketin adım adım anlatımı, sık yapılan hataları ve ipucu vardır.
- **Antrenman oynatıcısı:** Isınma → ana bölüm → soğuma; set/tekrar takibi, geri sayım, dinlenme
  zamanlayıcısı, sesli uyarı, ekranın açık kalması.
- **İlerleme takibi:** Tamamlanan seanslar cihazda (Room) saklanır. Bir sonraki hafta, öncekinin
  %70'i tamamlanınca açılır (yumuşak kilit – istenirse uyarıyla geçilebilir).
- **Hatırlatıcı:** Antrenman günlerinde seçilen saatte bildirim (WorkManager).
- **Hareket kütüphanesi:** Spora ve kategoriye göre filtrelenebilir.

## Proje yapısı

```
core/                      Saf Kotlin (JVM) modül – Android'e bağımlı değil, birim testli
  model/Content.kt           Sport, Move, ProgramTemplate... (kotlinx.serialization)
  content/ContentLibrary.kt  assets/content JSON'larını yükler ve doğrular
  domain/PlanGenerator.kt    Kullanıcı seçimlerinden 8 haftalık takvimli program üretir
  domain/Progress.kt         İlerleme, hafta kilidi, sıradaki seans
  domain/Workout.kt          Oynatıcı adımları (set/dinlenme) ve süre tahmini
app/                       Android uygulaması (Jetpack Compose, Material 3)
  data/                      Room veritabanı + TrainingRepository
  reminders/                 WorkManager hatırlatıcısı
  ui/                        Ekranlar: onboarding, ana sayfa, program, seans, oynatıcı, kütüphane, ayarlar
  src/main/assets/content/   Sporlar, hareketler ve program şablonları (JSON)
  src/main/assets/video/     Hareket videoları (H.264 MP4, döngüsel)
  src/main/assets/poster/    Liste küçük resimleri (WebP)
tools/lottie_gen/          Hareket tanımları (3B anahtar pozlar) + hızlı 2B Lottie önizleme
tools/render3d/            Gerçekçi render: MakeHuman gövdesi + Blender Cycles -> MP4/WebP
```

## Derleme

Gereksinimler: Android Studio (Ladybug veya üstü) ya da JDK 17 + Android SDK 35.

```bash
./gradlew :core:test            # program üretici ve içerik testleri
./gradlew :app:assembleDebug    # APK: app/build/outputs/apk/debug/
```

GitHub Actions (`.github/workflows/android.yml`) her push'ta testleri çalıştırır ve
debug APK'yı **fightedu-debug-apk** artifact'ı olarak yükler.

## İçerik düzenleme

- **Hareket eklemek/değiştirmek:** `app/src/main/assets/content/moves_<spor>.json`
- **Programı değiştirmek:** `app/src/main/assets/content/program_<spor>.json`
  (her evrede 5 seans şablonu – A..E – olmalı; her egzersizde `reps` veya `sec`'ten biri bulunmalı)
- `./gradlew :core:test` içerik tutarlılığını (geçersiz hareket referansı, eksik video/kapak resmi, hafta sayısı)
  otomatik doğrular.

## Hareket videoları

Videolar iki aşamada üretilir; hareketin kendisi tek bir yerde (`tools/lottie_gen/moves.py`) tanımlıdır.

**1. Hareket tanımları – `tools/lottie_gen/`** (yalnızca Python, harici araç gerekmez)

| Dosya | İçerik |
|---|---|
| `moves.py` | 63 hareketin 3B anahtar pozları, kamera açısı, hedefi (kum torbası / partner), darbe kareleri |
| `skeleton.py` | Vücut ölçüleri, poz parametreleri, kol/bacak için ters kinematik (IK), poz döndürme/kaydırma |
| `scene.py` | Kareleri çözer (partner ve torba yerleşimi, geri tepme, torba salınımı); 2B Lottie dışa aktarımı |
| `figure.py`, `camera.py`, `mathx.py` | 2B önizleme figürü, ortografik kamera, vektör matematiği |
| `generate.py` | Hızlı 2B Lottie önizleme (`build/lottie`) ve içerik kapsam kontrolü |

Bir poz; kalçanın konumu/yönü, göğsün kalçaya göre dönüşü (omuz dönüşü), başın bakışı, ellerin ve
ayakların hedef konumlarıyla tanımlanır. Dirsek ve dizler IK ile hesaplanır, yere basan ayaklar için
kalça yüksekliği otomatik ayarlanır.

```bash
python3 tools/lottie_gen/generate.py --check-content   # tüm hareketler tanımlı mı + 2B önizleme
```

**2. Gerçekçi render – `tools/render3d/`** (Blender'ın Python modülü `bpy`, Python 3.13)

| Dosya | İçerik |
|---|---|
| `mhbody.py` | MakeHuman (MPFB2) temel gövdesi, şekil hedefleri (kas, kilo, boy, oranlar), iskelet ve deri ağırlıkları |
| `character.py` | Sporcu: atletik gövde, ten/saç/göz/kaş/dudak malzemeleri, kısa saç |
| `outfits.py` | Gövdeden türetilen giysiler (şort, mayo, dobok, tişört, çorap), metaball eldiven ve ayakkabılar |
| `retarget.py` | 1. aşamadaki iskelet çözümünü MakeHuman iskeletine aktarır (gövde dönüşleri + kol/bacak IK, parmaklar) |
| `studio.py` | Cycles ayarları, üç noktalı stüdyo ışığı, sonsuz fon, kamera |
| `render_moves.py` | Hareket başına sahne (sporcu, partner, torba, ip), kadraj, render, MP4 + WebP kodlama |

`skeleton.py` ölçüleri render sırasında MakeHuman gövdesine eşitlenir; böylece yere basan ayaklar ve
torbaya/partnere değen yumruklar gerçekçi gövdede de birebir tutar.

```bash
tools/render3d/setup.sh                                            # bpy + MPFB2 verisi (bir kez)
tools/render3d/.venv/bin/python tools/render3d/render_moves.py --only box_jab --preview 0,8  # tek kare
tools/render3d/.venv/bin/python tools/render3d/render_moves.py     # tümü -> app/src/main/assets/{video,poster}
```

Tüm hareketlerin render'ı 4 çekirdekli bir CPU'da birkaç saat sürer; bu yüzden CI'da çalıştırılmaz,
üretilen videolar depoya eklenir. Gövde, şekil hedefleri ve iskelet MakeHuman/MPFB2 projesine aittir
(CC0); `setup.sh` bunları `anny` Python paketinin içinden indirir.

Profesyonel çekim bir video aynı isimle (`app/src/main/assets/video/<hareket_id>.mp4`) konursa uygulama
kodu değişmeden onu kullanır.

## Güvenlik notu

Uygulama temel eğitim amaçlıdır ve antrenörün yerini tutmaz. Partner çalışması, sparring,
atış ve yer güreşi bir antrenör gözetiminde ve uygun koruyucu ekipmanla yapılmalıdır.
