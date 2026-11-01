# Koç sesi otomatik dinleme raporu

Her klip faster-whisper (small) ile yazıya döküldü ve okunması istenen metinle karşılaştırıldı. Puan: boşluksuz karakter hata oranı (ASR rakamları okunuşa çevrilir); metinde olmayan bir tekrar ya da aykırı süre +1. ASR da yanılabilir: listedekiler kulakla kontrol edilmeli.

1301 klip, ort. hata 0.053, yeniden kaydedilen 7, hâlâ eşiği (0.2) aşan 17 (tekrar: 0, süre: 0); kenar temizliği: 816 klipten toplam 778 sn çöp kırpıldı

## Eşiği aşanlar

| puan | neden | metin | duyulan |
|---|---|---|---|
| 1.06 | - | Sık yapılan hata: acele etmek. Buna dikkat et. | Sık yapılan hata acele etmek. Buna dikkat et.  Bardek ikinci nâiresi arikenden dere sâliye... |
| 0.55 | - | Şınav, elli saniye. Başla! | Şınav 80'e başlıyor. |
| 0.50 | - | Sağ kroşe! | Sağ kroşe, eğil. |
| 0.40 | - | Savun! | Sabon. |
| 0.35 | - | Gün on dört. Önce ısınıyoruz. | Günahın dört, öncesini yorusuz. |
| 0.35 | - | Gün yirmi dört. Önce ısınıyoruz. | Günaydın, dert onca asınıyoruz. |
| 0.33 | - | Gün on: aktif dinlenme. | Dün on, attiftin nam me. |
| 0.33 | - | Diz! | Din. |
| 0.26 | - | Sıradaki raunt: Dalış Adımı. | 3dki raunt, dalış adıma. |
| 0.24 | - | Sıradaki: dördüncü raunt. | Sıra da ki, doğru dönce raunt. |
| 0.24 | - | Bugünün konusu: yan tekme. | Bugünün konusu, Antrenman. |
| 0.23 | - | Kalçan aşağıda, başın yukarıda! | Kaçına şardak, basın yukarıda. |
| 0.22 | - | Sıradaki: dördüncü tur, İp Atlama. | Sıradaki doldunca tour, İpe Atlama. |
| 0.21 | - | On saniye, hızlan! | Ansanya hızlan. |
| 0.21 | - | Form devresi: börpi ve Şınav. Hız değil, kontrol. | Formdebresi, bur piyvesi naf, hız dein, kontrol. |
| 0.21 | - | Sıradaki raunt: Seviye Değiştirme. | Söyledeki raunt sevgiye değiştirme. |
| 0.20 | - | Sık yapılan hata: dik durarak mücadele etmek. Buna dikkat et. | Tüküya plan hata diktör alak mücadele etmek. Pınar dik kat et. |

## Yeniden kaydedilenler

| önce | sonra | metin | önce duyulan |
|---|---|---|---|
| 0.24 | 0.00 | Bugünün konusu: tüm yumruklar. | Bugünün konusu Tüm Yungrooklarşı. |
| 0.17 | 0.04 | Gün on altı. Önce ısınıyoruz. | Gün 16. Önce öfnüyoruz. |
| 0.17 | 0.08 | Bugünün konusu: tüm dalışlar. | Bugünün konusu timdelişler. |
| 0.14 | 0.09 | Bugünün konusu: gövde gücü. | Bugün konusu, Gövdekücü. |
| 0.10 | 0.10 | Börpi, başla! | Bir pi başla. |
| 0.08 | 0.00 | Dalış, savunma ve yerden çıkış. | Dalış Savunmada Yerden Çıkış. |
| 0.00 | 0.00 | Bugünün konusu: açılar. | Bugünün konusu açılar. |
