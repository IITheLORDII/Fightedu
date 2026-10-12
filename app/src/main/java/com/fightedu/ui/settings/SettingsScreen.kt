package com.fightedu.ui.settings

import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.fightedu.reminders.ReminderNotifications
import com.fightedu.ui.UiState
import com.fightedu.ui.components.AppScaffold
import com.fightedu.ui.components.SectionTitle
import com.fightedu.ui.longLabel
import com.fightedu.ui.longTr

private val REMINDER_HOURS = listOf(7, 9, 12, 17, 18, 19, 20)

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SettingsScreen(
    state: UiState,
    onSetReminder: (enabled: Boolean, hour: Int) -> Unit,
    onResetPlan: () -> Unit,
) {
    val context = LocalContext.current
    val plan = state.plan
    val sport = state.sport
    var confirmReset by rememberSaveable { mutableStateOf(false) }
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

    AppScaffold(title = "Ayarlar", underBottomBar = true) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
        ) {
            SectionTitle("Programım")
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    if (plan != null) {
                        Text("${sport?.emoji.orEmpty()} ${sport?.name.orEmpty()}", style = MaterialTheme.typography.titleMedium)
                        Text("Haftada ${plan.daysPerWeek} gün: ${plan.sortedDays.joinToString { it.longTr }}")
                        Text("Başlangıç: ${plan.startDate.longLabel()}")
                        state.sessions.lastOrNull()?.let { Text("Bitiş: ${it.date.longLabel()}") }
                        Text("Tamamlanan: ${state.tracker.completedCount} / ${state.sessions.size}")
                    }
                    Spacer(Modifier.padding(top = 8.dp))
                    OutlinedButton(onClick = { confirmReset = true }) { Text("Spor / günleri değiştir") }
                }
            }

            SectionTitle("Hatırlatıcı")
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text("Antrenman günlerinde bildirim", style = MaterialTheme.typography.bodyLarge)
                            Text(
                                "Seçtiğin saatte, o günün antrenmanı henüz yapılmadıysa hatırlatır.",
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                        Switch(
                            checked = state.reminder.enabled,
                            onCheckedChange = { on -> if (on) enableReminder() else onSetReminder(false, state.reminder.hour) },
                        )
                    }
                    if (state.reminder.enabled) {
                        Spacer(Modifier.padding(top = 8.dp))
                        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
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

            SectionTitle("Güvenli antrenman")
            Card(Modifier.fillMaxWidth()) {
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
                "FightEdu 1.0 · Boks, Kick Boks, Güreş ve Tekvando için 8 haftalık temel eğitim programı. " +
                    "Tüm içerik çevrimdışı çalışır; ilerlemen yalnızca bu cihazda saklanır.",
                style = MaterialTheme.typography.bodySmall,
            )
            Spacer(Modifier.padding(bottom = 24.dp))
        }
    }

    if (confirmReset) {
        AlertDialog(
            onDismissRequest = { confirmReset = false },
            title = { Text("Program yeniden oluşturulsun mu?") },
            text = { Text("Spor veya gün seçimini değiştirmek için yeni bir program oluşturulur. Mevcut ilerlemen silinecek.") },
            confirmButton = {
                TextButton(onClick = {
                    confirmReset = false
                    onResetPlan()
                }) { Text("Yeni program") }
            },
            dismissButton = { TextButton(onClick = { confirmReset = false }) { Text("Vazgeç") } },
        )
    }
}
