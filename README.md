# FightEdu 🥊🦵🤼🥋

**Boks, Kick Boks, Güreş ve Tekvando** için yeni başlayanları **24 günlük, koç yönetimli** antrenmanlarla
temel seviyeye getiren, tamamen çevrimdışı çalışan bir Android uygulaması.

## Özellikler

- **Koç yönetimli günlük antrenman:** Program bir tablo değil; kullanıcı "**Gün 3 antrenmanını başlat**"
  der, koç günü kurar ve raunt raunt ilerletir. Örnek gün: *2 raunt ip → 3 dk teknik → 2 raunt gölge boksu →
  6 raunt torba → kondisyon devresi → esneme*. Günler sırayla açılır (Gün 1 → Gün 24); bir günü kaçırmak
  sorun değil, kaldığın yerden devam edersin. Seçilen hafta günleri yalnızca hatırlatıcı içindir.
- **4 evre (her spor için, 6'şar gün):** temeller → yeni teknikler → raunt temposu/kombinasyonlar →
  dövüş temposu ve final. Raunt süresi 2 → 3 dakikaya, ana raunt sayısı 4 → 8'e çıkar; her evrenin son
  günü bir değerlendirme günüdür. Güreşte torba yerine dalış/sprawl drilleri, tekvandoda tekme raundları
  ve Taegeuk 1 formu vardır.
- **Gerçekçi hareket videoları:** 63 hareketin her biri, gerçek insan oranlarına ve kas yapısına sahip
  3B bir sporcuyla (stüdyo ışığında render edilmiş, döngüsel kısa video) gösterilir. Kıyafetler spora
  göredir: boksta şort, eldiven ve bot; kick boksta tay şortu ve eldiven; güreşte mayo ve güreş
  ayakkabısı; tekvandoda dobok ve kuşak. Kalça/omuz dönüşü, ayak pivotu ve ağırlık aktarımı görünür;
  vuruşlar kum torbasına veya partnere yapılır, savunmalar gelen saldırıya karşı gösterilir
  (yavaş çekim seçeneği). Her hareketin adım adım anlatımı, sık yapılan hataları ve ipucu vardır.
- **Antrenman oynatıcısı:** Raunt sayacı ("RAUNT 3 / 6"), halka geri sayım, blok renkli ilerleme şeridi,
  hareket videosu, koç komutları ekranda ("BİR-İKİ!") ve videoda o hareket; dinlenme ekranında sıradaki
  raunt/blok, +15 sn; devre (istasyon) ve tekrarlı bloklar; bitişte özet. Ekran açık kalır, döndürmede
  kaldığı yerden devam eder.
- **Türkçe sesli koç:** Raunt başı/sonu gong, "Raunt 3. Başla!", raunt içinde komutlar ("Jab!",
  "Bir iki üç!", "Low kick!"), "Son on saniye!", dinlenmede sıradaki blok; titreşim. Cihazın metin okuma
  motorunu kullanır (Türkçe ses yoksa yalnızca zil); ayarlardan kapatılabilir.
- **İlerleme takibi:** Tamamlanan günler cihazda (Room) saklanır; evre ve genel ilerleme ana sayfada.
- **Hatırlatıcı:** Seçilen hafta günlerinde, o gün antrenman yapılmadıysa sıradaki günü hatırlatan bildirim (WorkManager).
- **Hareket kütüphanesi:** Spora ve kategoriye göre filtrelenebilir.

## Proje yapısı

```
core/                      Saf Kotlin (JVM) modül – Android'e bağımlı değil, birim testli
  model/Content.kt           Sport, Move, TrainingProgram/Day/Block (kotlinx.serialization)
  content/ContentLibrary.kt  assets/content JSON'larını yükler ve doğrular
  domain/Training.kt         Günü raunt/istasyon adımlarına açar (TrainingPlanner), koç komut zamanları,
                             oynatıcı durum makinesi ve olayları (SessionRunner)
  domain/Progress.kt         Sıralı gün ilerlemesi, sıradaki gün, evre ilerlemesi
app/                       Android uygulaması (Jetpack Compose, Material 3)
  data/                      Room veritabanı + TrainingRepository
  reminders/                 WorkManager hatırlatıcısı
  coach/Coach.kt             Sesli koç: TextToSpeech (tr-TR), gong/bip, titreşim
  ui/                        Ekranlar: onboarding, ana sayfa, antrenmanlar, gün, oynatıcı, kütüphane, ayarlar
  src/main/assets/content/   Sporlar, hareketler ve günlük antrenman programları (JSON)
  src/main/assets/video/     Hareket videoları (H.264 MP4, döngüsel)
  src/main/assets/poster/    Liste küçük resimleri (WebP)
tools/lottie_gen/          Hareket tanımları (3B anahtar pozlar) + hızlı 2B Lottie önizleme
tools/render3d/            Gerçekçi render: MakeHuman gövdesi + Blender Cycles -> MP4/WebP
```

## Derleme

Gereksinimler: Android Studio (Ladybug veya üstü) ya da JDK 17 + Android SDK 35.

```bash
./gradlew :core:test            # içerik, planlayıcı, oynatıcı durum makinesi ve ilerleme testleri
./gradlew :app:assembleDebug    # APK: app/build/outputs/apk/debug/
```

GitHub Actions (`.github/workflows/android.yml`) her push'ta testleri çalıştırır ve
debug APK'yı **fightedu-debug-apk** artifact'ı olarak yükler.

## İçerik düzenleme

- **Hareket eklemek/değiştirmek:** `app/src/main/assets/content/moves_<spor>.json`
- **Antrenmanları değiştirmek:** `tools/content/make_training.py` içindeki gün tanımlarını (tema, koç notu,
  teknik hareketleri, komutlar, ana raunt hareketleri) düzenleyip `python3 tools/content/make_training.py`
  çalıştır; `app/src/main/assets/content/training_<spor>.json` yeniden üretilir. Blok biçimleri:
  `round` (raunt; `calls` koç komutları), `circuit` (istasyonlu devre), `reps` (tekrarlı set).
- `./gradlew :core:test` içerik tutarlılığını (24 gün, evre kapsamı, geçersiz hareket, eksik video/kapak resmi,
  her hareketin kullanılması, günlük süre 20–60 dk) otomatik doğrular.

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
| `mhbody.py` | MakeHuman (MPFB2) temel gövdesi, şekil hedefleri (kas, kilo, boy, oranlar), iskelet ve deri ağırlıkları; omuz/önkol/kalça twist kemikleri |
| `character.py` | Sporcu: atletik gövde, hacmi koruyan (dual quaternion) deri + düzeltici yumuşatma, ten/saç/göz/kaş/dudak malzemeleri, kısa saç |
| `outfits.py` | Gövdeden türetilen giysiler (şort, mayo, dobok, tişört, çorap); şort ve dobok pantolonu kumaş simülasyonlu; ayak kalıbına oturan bağcıklı bot/ayakkabılar, metaball eldivenler |
| `retarget.py` | 1. aşamadaki iskelet çözümünü MakeHuman iskeletine aktarır (gövde dönüşleri + kol/bacak IK, parmaklar) |
| `studio.py` | Cycles ayarları, üç noktalı stüdyo ışığı, sonsuz fon, kamera |
| `render_moves.py` | Hareket başına sahne (sporcu, partner, torba, ip), kadraj, kumaş simülasyonu (ısınma turu sonrası döngüsel), render, MP4 + WebP kodlama |

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
