# Koç sesi otomatik dinleme raporu

Her klip faster-whisper (small) ile yazıya döküldü ve okunması istenen metinle karşılaştırıldı. Puan: boşluksuz karakter hata oranı (ASR rakamları okunuşa çevrilir); metinde olmayan bir tekrar ya da aykırı süre +1. ASR da yanılabilir: listedekiler kulakla kontrol edilmeli.

1301 klip, ort. hata 0.054, yeniden kaydedilen 0, hâlâ eşiği (0.2) aşan 17 (tekrar: 0, süre: 0); kenar temizliği: 868 klipten toplam 830 sn çöp kırpıldı

## Eşiği aşanlar

| puan | neden | metin | duyulan |
|---|---|---|---|
| 1.06 | - | Sık yapılan hata: acele etmek. Buna dikkat et. | Sık yapılan hata acele etmek. Buna dikkat et. Bardek ikinci nâiresi arikenden dere sâliye... |
| 0.55 | - | Şınav, elli saniye. Başla! | Şınav 80'e başlıyor. |
| 0.50 | - | Sağ kroşe! | Sağ kroşe, eğil. |
| 0.40 | - | Savun! | Sabon. |
| 0.35 | - | Gün on dört. Önce ısınıyoruz. | Günahın dört, öncesini yorusuz. |
| 0.35 | - | Gün yirmi dört. Önce ısınıyoruz. | Günaydın, dert onca asınıyoruz. |
| 0.33 | - | Diz! | Din. |
| 0.28 | - | Gün on: aktif dinlenme. | Gün on, attiftin nam me. |
| 0.26 | - | Sıradaki raunt: Dalış Adımı. | 3dki raunt, dalış adıma. |
| 0.24 | - | Bugünün konusu: tüm yumruklar. | Bugünün konusu Tüm Yungrooklarşı. |
| 0.24 | - | Bugünün konusu: yan tekme. | Bugünün konusu, Antrenman. |
| 0.23 | - | Tebrikler! Gün yirmi bir tamamlandı. | Tebrikler, gün üniversit tamamlandı. |
| 0.22 | - | Sıradaki: dördüncü tur, İp Atlama. | Sıradaki doldunca tour, İpe Atlama. |
| 0.21 | - | Düz Diz: arka dizi yukarı ve ileri sür, kalçayı öne it. | Bu arka dizi yukarı ve ileri suç kalçayı öneyit. |
| 0.21 | - | On saniye, hızlan! | Ansanya hızlan. |
| 0.21 | - | Form devresi: börpi ve Şınav. Hız değil, kontrol. | Formdebresi, bur piyvesi naf, hız dein, kontrol. |
| 0.21 | - | Sıradaki raunt: Seviye Değiştirme. | Söyledeki raunt sevgiye değiştirme. |
