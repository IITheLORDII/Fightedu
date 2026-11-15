package com.fightedu.ui.privacy

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

/** Uygulamanın veri kullanımı; Health Connect izin ekranından ve Profil'den açılır. */
@Composable
fun PrivacyPolicyScreen(onBack: () -> Unit) {
    Surface(color = MaterialTheme.colorScheme.background, modifier = Modifier.fillMaxSize()) {
        Column(
            Modifier
                .fillMaxSize()
                .statusBarsPadding()
                .navigationBarsPadding()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onBack) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Geri")
                }
                Text("Gizlilik politikası", style = MaterialTheme.typography.headlineSmall)
            }
            PRIVACY_SECTIONS.forEach { (title, body) ->
                Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                body.forEach { Text("• $it", style = MaterialTheme.typography.bodyMedium) }
            }
        }
    }
}

/** Gizlilik metni (başlık -> maddeler). */
val PRIVACY_SECTIONS: List<Pair<String, List<String>>> = listOf(
    "Hesabın ve ilerlemen" to listOf(
        "Adın, e-postan ve antrenman ilerlemen yalnızca bu cihazda saklanır. Sunucumuz yoktur; uygulamanın internet izni bulunmaz.",
        "Şifren hiçbir yerde açık olarak tutulmaz; yalnızca PBKDF2 ile üretilmiş özeti saklanır.",
        "Hesap verileri cihaz yedeklemesine ve cihazdan cihaza aktarıma dahil edilmez.",
    ),
    "Sağlık uygulamaları (Health Connect, Samsung Health)" to listOf(
        "Bağlanmak isteğe bağlıdır; izin verirsen tamamladığın antrenmanları (tür, başlangıç-bitiş saati, başlık) ve tahmini aktif kalorini Health Connect'e yazarız. Samsung Health bu kayıtları Health Connect üzerinden alır.",
        "En son kilo kaydını yalnızca kalori tahmini için, antrenman süresince ölçülen nabzı yalnızca antrenman özetinde göstermek için okuruz. Okunan veriler saklanmaz.",
        "Sağlık verileri cihaz dışına gönderilmez, reklam ya da profil oluşturma amacıyla kullanılmaz, üçüncü taraflarla paylaşılmaz.",
        "İzinleri istediğin zaman Health Connect ayarlarından kaldırabilir, FightEdu'nun yazdığı kayıtları oradan silebilirsin.",
    ),
    "Bildirimler" to listOf(
        "Yalnızca açtığın günlük antrenman hatırlatıcısı için kullanılır.",
    ),
    "Verilerini silme" to listOf(
        "Profil > Hesabı sil: hesabın ve tüm ilerlemen bu cihazdan kalıcı olarak silinir.",
        "Uygulamayı kaldırdığında cihazdaki tüm veriler silinir.",
    ),
)
