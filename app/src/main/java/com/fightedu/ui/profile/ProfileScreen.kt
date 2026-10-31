package com.fightedu.ui.profile

import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fightedu.core.domain.ChallengeCalendar
import com.fightedu.data.CoachSettings
import com.fightedu.reminders.ReminderNotifications
import com.fightedu.ui.UiState
import com.fightedu.ui.components.SectionTitle
import com.fightedu.ui.theme.DisplayFont

private val REMINDER_HOURS = listOf(7, 9, 12, 17, 18, 19, 20)

/** Profil: kullanıcı, istatistikler, dal, koç ve hatırlatıcı ayarları, güvenlik, hakkında, çıkış. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ProfileScreen(
    state: UiState,
    onChangeSport: () -> Unit,
    onCreateAccount: () -> Unit,
    onRename: (String, (String?) -> Unit) -> Unit,
    onSetReminder: (enabled: Boolean, hour: Int) -> Unit,
    onSetCoach: (CoachSettings) -> Unit,
    onRestart: () -> Unit,
    onLogout: () -> Unit,
) {
    val context = LocalContext.current
    val user = state.user
    val sport = state.sport
    val challenge = state.challenge
    var confirmLogout by rememberSaveable { mutableStateOf(false) }
    var confirmRestart by rememberSaveable { mutableStateOf(false) }
    var editing by rememberSaveable { mutableStateOf(false) }
    var permissionDenied by rememberSaveable { mutableStateOf(false) }

    val permissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        permissionDenied = !granted
        if (granted) onSetReminder(true, state.reminder.hour)
    }

    fun enableReminder() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU && !ReminderNotifications.canNotify(context)) {
            permissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        } else {
            onSetReminder(true, state.reminder.hour)
        }
    }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .statusBarsPadding()
            .padding(16.dp),
    ) {
        // -- kullanıcı ---------------------------------------------------------------------------
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                Modifier.size(64.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primary),
                contentAlignment = Alignment.Center,
            ) {
                Text(user?.initials ?: "?", color = MaterialTheme.colorScheme.onPrimary, fontSize = 24.sp,
                    fontWeight = FontWeight.Bold)
            }
            Spacer(Modifier.width(14.dp))
            Column(Modifier.weight(1f)) {
                Text(user?.name ?: "Sporcu", style = MaterialTheme.typography.headlineSmall)
                Text(
                    if (user?.isGuest == true) "Misafir hesabı · ilerlemen bu cihazda" else user?.email.orEmpty(),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            TextButton(onClick = { editing = true }) { Text("Düzenle") }
        }
        if (user?.isGuest == true) {
            Spacer(Modifier.height(12.dp))
            Card(shape = RoundedCornerShape(16.dp), modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("İlerlemeni kaybetme", style = MaterialTheme.typography.titleMedium)
                    Text("Bir hesap oluştur; şimdiye kadarki günlerin ve serin hesabına aktarılsın.",
                        style = MaterialTheme.typography.bodySmall)
                    Button(onClick = onCreateAccount) { Text("Hesap oluştur") }
                }
            }
        }

        // -- istatistik -------------------------------------------------------------------------
        SectionTitle("İstatistikler")
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Stat("${challenge?.doneCount ?: 0}/${ChallengeCalendar.LENGTH}", "gün", Modifier.weight(1f))
            Stat("${challenge?.currentStreak ?: 0}", "seri 🔥", Modifier.weight(1f))
            Stat("${challenge?.bestStreak ?: 0}", "en iyi seri", Modifier.weight(1f))
            Stat("${state.totalMinutes}", "dakika", Modifier.weight(1f))
        }

        // -- dal ----------------------------------------------------------------------------------
        SectionTitle("Dalım")
        Card(Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp)) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("${sport?.emoji.orEmpty()} ${sport?.name.orEmpty()}", style = MaterialTheme.typography.titleLarge)
                Text("30 günlük meydan okuma · ${challenge?.doneCount ?: 0} gün tamamlandı",
                    style = MaterialTheme.typography.bodyMedium)
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.padding(top = 6.dp)) {
                    Button(onClick = onChangeSport) { Text("Dalı değiştir") }
                    OutlinedButton(onClick = { confirmRestart = true }) { Text("Baştan başla") }
                }
            }
        }

        // -- koç ----------------------------------------------------------------------------------
        SectionTitle("Koç")
        Card(Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp)) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                SettingSwitch(
                    title = "Sesli koç",
                    subtitle = "Raunt başı, komutlar (\"Bir-iki!\"), son 10 saniye ve dinlenme Türkçe söylenir.",
                    checked = state.coach.voice,
                    onChange = { onSetCoach(state.coach.copy(voice = it)) },
                )
                SettingSwitch(
                    title = "Titreşim",
                    subtitle = "Raunt ve dinlenme başında kısa titreşim.",
                    checked = state.coach.vibration,
                    onChange = { onSetCoach(state.coach.copy(vibration = it)) },
                )
            }
        }

        // -- hatırlatıcı --------------------------------------------------------------------------
        SectionTitle("Hatırlatıcı")
        Card(Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp)) {
            Column(Modifier.padding(16.dp)) {
                SettingSwitch(
                    title = "Günlük hatırlatıcı",
                    subtitle = "O gün henüz çalışmadıysan seçtiğin saatte sıradaki günü hatırlatır.",
                    checked = state.reminder.enabled,
                    onChange = { on -> if (on) enableReminder() else onSetReminder(false, state.reminder.hour) },
                )
                if (state.reminder.enabled) {
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
                        REMINDER_HOURS.forEach { h ->
                            FilterChip(
                                selected = state.reminder.hour == h,
                                onClick = { onSetReminder(true, h) },
                                label = { Text("%02d:00".format(h)) },
                            )
                        }
                    }
                }
                if (permissionDenied) {
                    Text(
                        "Bildirim izni verilmedi. Sistem ayarlarından FightEdu için bildirimlere izin verebilirsin.",
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }

        // -- güvenlik / hakkında ------------------------------------------------------------------
        SectionTitle("Güvenli antrenman")
        Card(Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp)) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("• Her antrenmana ısınmayla başla, soğumayla bitir.")
                Text("• Ağrı (kas yorgunluğundan farklı, keskin ağrı) hissedersen dur.")
                Text("• Bol su iç; antrenmandan 1-2 saat önce ağır yemek yeme.")
                Text("• Torba ve partner çalışmasında el sargısı ve eldiven kullan.")
                Text("• Sparring, atış ve yer güreşini mutlaka antrenör gözetiminde yap.")
                Text("• Sağlık sorunun varsa başlamadan önce doktoruna danış.")
            }
        }
        SectionTitle("Hakkında")
        Text(
            "FightEdu 1.1 · Boks, Kick Boks, Güreş, Tekvando ve Genel Kondisyon için 30 günlük meydan okumalar. " +
                "Tüm içerik çevrimdışı çalışır; hesabın ve ilerlemen yalnızca bu cihazda saklanır.",
            style = MaterialTheme.typography.bodySmall,
        )
        Spacer(Modifier.height(16.dp))
        OutlinedButton(onClick = { confirmLogout = true }, modifier = Modifier.fillMaxWidth().height(50.dp)) {
            Text("Çıkış yap", color = MaterialTheme.colorScheme.error)
        }
        Spacer(Modifier.height(24.dp))
    }

    if (editing) {
        var name by rememberSaveable { mutableStateOf(user?.name.orEmpty()) }
        var error by rememberSaveable { mutableStateOf<String?>(null) }
        val err = error
        AlertDialog(
            onDismissRequest = { editing = false },
            title = { Text("Adını düzenle") },
            text = {
                OutlinedTextField(name, { name = it; error = null }, singleLine = true, isError = err != null,
                    supportingText = if (err != null) { { Text(err) } } else null, label = { Text("Adın") })
            },
            confirmButton = {
                TextButton(onClick = { onRename(name) { e -> if (e == null) { editing = false } else { error = e } } }) { Text("Kaydet") }
            },
            dismissButton = { TextButton(onClick = { editing = false }) { Text("Vazgeç") } },
        )
    }
    if (confirmRestart) {
        AlertDialog(
            onDismissRequest = { confirmRestart = false },
            title = { Text("Meydan okuma baştan başlasın mı?") },
            text = { Text("${sport?.name.orEmpty()} için tamamladığın günler sıfırlanır. Serin ve diğer dallardaki ilerlemen korunur.") },
            confirmButton = { TextButton(onClick = { confirmRestart = false; onRestart() }) { Text("Baştan başlat") } },
            dismissButton = { TextButton(onClick = { confirmRestart = false }) { Text("Vazgeç") } },
        )
    }
    if (confirmLogout) {
        AlertDialog(
            onDismissRequest = { confirmLogout = false },
            title = { Text("Çıkış yapılsın mı?") },
            text = {
                Text(
                    if (user?.isGuest == true) {
                        "Misafir olarak yaptığın ilerleme silinecek. Saklamak için önce hesap oluştur."
                    } else {
                        "İlerlemen hesabında saklı; tekrar giriş yaptığında kaldığın yerden devam edersin."
                    },
                )
            },
            confirmButton = { TextButton(onClick = { confirmLogout = false; onLogout() }) { Text("Çıkış yap") } },
            dismissButton = { TextButton(onClick = { confirmLogout = false }) { Text("Vazgeç") } },
        )
    }
}

@Composable
private fun Stat(value: String, label: String, modifier: Modifier = Modifier) {
    Surface(color = MaterialTheme.colorScheme.surfaceVariant, shape = RoundedCornerShape(14.dp), modifier = modifier) {
        Column(Modifier.padding(vertical = 10.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Text(value, fontFamily = DisplayFont, fontWeight = FontWeight.ExtraBold, fontSize = 22.sp)
            Text(label, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun SettingSwitch(title: String, subtitle: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.bodyLarge)
            Text(subtitle, style = MaterialTheme.typography.bodySmall)
        }
        Switch(checked = checked, onCheckedChange = onChange)
    }
}
