package com.fightedu.ui.program

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.fightedu.ui.UiState
import com.fightedu.ui.components.AppScaffold
import com.fightedu.ui.components.Pill
import com.fightedu.ui.components.SessionStatus
import com.fightedu.ui.components.SessionStatusIcon
import com.fightedu.ui.components.blockColor
import com.fightedu.ui.components.blockSeconds

/** 24 günlük antrenman listesi: evre başlıkları altında günler (tamam / sıradaki / kilitli). */
@Composable
fun ProgramScreen(state: UiState, onOpenDay: (Int) -> Unit) {
    val program = state.program
    val tracker = state.tracker
    val planner = state.planner
    var lockedDay by rememberSaveable { mutableStateOf<Int?>(null) }

    AppScaffold(title = "Antrenmanlar", underBottomBar = true) { inner ->
        if (program == null || tracker == null || planner == null) return@AppScaffold
        val next = tracker.nextDay?.day
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(inner),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            program.phases.forEach { phase ->
                item(key = "phase_${phase.from}") {
                    Column(Modifier.padding(top = 12.dp, bottom = 4.dp)) {
                        Text(
                            "GÜN ${phase.from}–${phase.to} · ${phase.title.uppercase()}",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.primary,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(phase.goal, style = MaterialTheme.typography.bodySmall)
                    }
                }
                items(program.days.filter { it.day in phase.from..phase.to }, key = { "day_${it.day}" }) { d ->
                    val done = tracker.isCompleted(d.day)
                    val unlocked = tracker.isUnlocked(d.day)
                    val isNext = d.day == next
                    Card(
                        onClick = { if (unlocked) onOpenDay(d.day) else lockedDay = d.day },
                        colors = CardDefaults.cardColors(
                            containerColor = if (isNext) MaterialTheme.colorScheme.primaryContainer
                            else MaterialTheme.colorScheme.surfaceVariant,
                        ),
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                            SessionStatusIcon(
                                when {
                                    done -> SessionStatus.DONE
                                    unlocked -> SessionStatus.OPEN
                                    else -> SessionStatus.LOCKED
                                },
                                Modifier.size(24.dp),
                            )
                            Spacer(Modifier.width(12.dp))
                            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Text("Gün ${d.day} · ${d.title}", style = MaterialTheme.typography.titleSmall)
                                // blok şeridi: her blok süresiyle orantılı renkli parça
                                Row(Modifier.fillMaxWidth().height(6.dp), horizontalArrangement = Arrangement.spacedBy(2.dp)) {
                                    d.blocks.forEach { b ->
                                        Box(
                                            Modifier
                                                .weight(blockSeconds(b).coerceAtLeast(1).toFloat())
                                                .height(6.dp)
                                                .background(blockColor(b.kind), RoundedCornerShape(3.dp)),
                                        )
                                    }
                                }
                                Text("~${planner.estimatedMinutes(d)} dk · ${d.blocks.joinToString(" · ") { it.title }}",
                                    style = MaterialTheme.typography.bodySmall, maxLines = 1)
                            }
                            if (isNext) Pill("Sıradaki")
                        }
                    }
                }
            }
        }
    }

    lockedDay?.let { day ->
        AlertDialog(
            onDismissRequest = { lockedDay = null },
            title = { Text("Gün $day henüz açılmadı") },
            text = { Text("Antrenmanlar sırayla açılır. Önce Gün ${day - 1}'i tamamla; yine de bakmak istersen açabilirsin.") },
            confirmButton = {
                TextButton(onClick = {
                    lockedDay = null
                    onOpenDay(day)
                }) { Text("Yine de aç") }
            },
            dismissButton = { TextButton(onClick = { lockedDay = null }) { Text("Vazgeç") } },
        )
    }
}
