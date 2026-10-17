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
- **Animasyonlu hareketler:** 63 hareketin her biri, 3B iskelet üzerinden üretilmiş gerçekçi oranlı,
  spora uygun kıyafetli bir insan figürüyle Lottie animasyonu olarak gösterilir. Kalça/omuz dönüşü,
  ayak pivotu ve ağırlık aktarımı görünür; vuruşlar kum torbasına veya partnere yapılır, savunmalar
  gelen saldırıya karşı gösterilir, vuruşun yolu iz olarak çizilir (yavaş çekim seçeneği).
  Her hareketin adım adım anlatımı, sık yapılan hataları ve ipucu vardır.
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
  src/main/assets/lottie/    Hareket animasyonları (Lottie JSON)
tools/lottie_gen/generate.py Animasyon üreticisi
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
- `./gradlew :core:test` içerik tutarlılığını (geçersiz hareket referansı, eksik animasyon, hafta sayısı)
  otomatik doğrular.

## Animasyonlar

Animasyonlar `tools/lottie_gen/` altındaki Python betikleriyle **3B iskelet** üzerinden üretilir
(harici araç gerekmez):

| Dosya | İçerik |
|---|---|
| `moves.py` | 63 hareketin 3B anahtar pozları, kamera açısı, hedefi (kum torbası / partner), darbe kareleri |
| `skeleton.py` | Vücut ölçüleri, poz parametreleri, kol/bacak için ters kinematik (IK), poz döndürme/kaydırma |
| `figure.py` | 3B gövdeyi kamera açısından çizen figür: kas hatlı uzuvlar, gövde, yüz, saç, spora göre kıyafet |
| `camera.py` | Ortografik kamera ve 2B bezier yol yardımcıları |
| `mathx.py` | Vektör/eksen takımı matematiği ve döngüsel (periyodik) PCHIP interpolasyonu |
| `scene.py` | Sahne: kum torbası, partner, zemin, gölgeler, vuruş izi ve darbe efekti; Lottie'ye dönüştürme |
| `generate.py` | Komut satırı aracı |

Nasıl çalışır:

- Bir poz; kalçanın konumu/yönü, göğsün kalçaya göre dönüşü (omuz dönüşü), başın bakışı, ellerin
  ve ayakların hedef konumlarıyla tanımlanır. Dirsek ve dizler IK ile hesaplanır, yere basan ayaklar
  için kalça yüksekliği otomatik ayarlanır. Böylece pivot, kalça dönüşü, ağırlık aktarımı gibi
  tekniğin özü görünür.
- Her hareket kendine en uygun kamera açısından gösterilir (ör. slip ve roll için önden, tekmeler
  için yandan). Gövde parçaları her karede derinliğe göre sıralanır.
- Vuruşlarda yumruğun/tekmenin izlediği yol yarı saydam bir izle, temas anı darbe efektiyle gösterilir.
  Savunmalarda partner saldırır; güreşte partner tepki verir (itilir, mindere düşer, bacağı tutulur).
- Partner otomatik olarak aynalanır (solak), böylece iki figürün de göğsü kameraya döner.

```bash
python3 tools/lottie_gen/generate.py --check-content   # tümünü üret + içerik kapsamını kontrol et
python3 tools/lottie_gen/generate.py --only box_jab    # tek bir hareket
```

Profesyonel bir tasarımcıdan alınan Lottie dosyası aynı isimle
(`app/src/main/assets/lottie/<hareket_id>.json`) konursa uygulama kodu değişmeden onu kullanır.
Bu durumda o hareketi `moves.py`'den kaldırın ki yeniden üretim dosyanın üzerine yazmasın.

## Güvenlik notu

Uygulama temel eğitim amaçlıdır ve antrenörün yerini tutmaz. Partner çalışması, sparring,
atış ve yer güreşi bir antrenör gözetiminde ve uygun koruyucu ekipmanla yapılmalıdır.
