package com.fightedu.ui.program

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
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
import androidx.compose.ui.unit.dp
import com.fightedu.core.domain.PlannedSession
import com.fightedu.core.domain.ProgressTracker
import com.fightedu.ui.UiState
import com.fightedu.ui.components.AppScaffold
import com.fightedu.ui.components.SessionStatus
import com.fightedu.ui.components.SessionStatusIcon
import com.fightedu.ui.shortLabel
import java.time.LocalDate

@Composable
fun ProgramScreen(state: UiState, onOpenSession: (PlannedSession) -> Unit) {
    val tracker = state.tracker
    val weeks = (1..tracker.totalWeeks).toList()
    // Açık haftalar virgülle ayrılmış olarak saklanır (rememberSaveable için basit tip).
    var expanded by rememberSaveable { mutableStateOf(tracker.currentWeek.toString()) }
    val expandedSet = expanded.split(',').mapNotNull { it.toIntOrNull() }.toSet()
    var lockedTarget by rememberSaveable { mutableStateOf<String?>(null) }
    val today = LocalDate.now()

    AppScaffold(title = "8 Haftalık Program", underBottomBar = true) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
        ) {
            items(weeks, key = { it }) { week ->
                val sessions = tracker.sessionsOfWeek(week)
                val unlocked = tracker.isWeekUnlocked(week)
                val isOpen = week in expandedSet
                val phase = sessions.firstOrNull()
                val isPhaseStart = week == 1 || state.sessions.firstOrNull { it.week == week - 1 }?.phaseTitle != phase?.phaseTitle
                if (isPhaseStart && phase != null) {
                    Text(
                        "Evre: ${phase.phaseTitle}",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(top = 12.dp, bottom = 4.dp),
                    )
                    Text(phase.phaseGoal, style = MaterialTheme.typography.bodySmall, modifier = Modifier.padding(bottom = 8.dp))
                }
                WeekCard(
                    week = week,
                    sessions = sessions,
                    tracker = tracker,
                    unlocked = unlocked,
                    expanded = isOpen,
                    today = today,
                    onToggle = {
                        val newSet = if (isOpen) expandedSet - week else expandedSet + week
                        expanded = newSet.joinToString(",")
                    },
                    onSessionClick = { s ->
                        if (unlocked) onOpenSession(s) else lockedTarget = s.key
                    },
                )
            }
        }
    }

    val target = lockedTarget?.let { key -> state.sessions.firstOrNull { it.key == key } }
    if (target != null) {
        AlertDialog(
            onDismissRequest = { lockedTarget = null },
            title = { Text("Hafta ${target.week} henüz kilitli") },
            text = {
                Text(
                    "Bir sonraki haftaya geçmeden önce Hafta ${target.week - 1} antrenmanlarının en az " +
                        "${tracker.unlockThreshold} tanesini tamamlamanı öneriyoruz. Temeller sağlam olmadan " +
                        "ilerlemek sakatlık riskini artırır.",
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    lockedTarget = null
                    onOpenSession(target)
                }) { Text("Yine de aç") }
            },
            dismissButton = { TextButton(onClick = { lockedTarget = null }) { Text("Tamam") } },
        )
    }
}

@Composable
private fun WeekCard(
    week: Int,
    sessions: List<PlannedSession>,
    tracker: ProgressTracker,
    unlocked: Boolean,
    expanded: Boolean,
    today: LocalDate,
    onToggle: () -> Unit,
    onSessionClick: (PlannedSession) -> Unit,
) {
    val done = sessions.count { tracker.isCompleted(it) }
    val isCurrent = week == tracker.currentWeek
    Card(
        colors = CardDefaults.cardColors(
            containerColor = if (isCurrent) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant,
        ),
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 10.dp),
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier
                .fillMaxWidth()
                .clickable(onClick = onToggle)
                .padding(16.dp),
        ) {
            Column(Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Hafta $week", style = MaterialTheme.typography.titleMedium)
                    if (!unlocked) {
                        Spacer(Modifier.width(6.dp))
                        Icon(Icons.Filled.Lock, contentDescription = "Kilitli", tint = MaterialTheme.colorScheme.outline)
                    }
                }
                Text("$done / ${sessions.size} tamamlandı", style = MaterialTheme.typography.bodySmall)
                LinearProgressIndicator(
                    progress = { if (sessions.isEmpty()) 0f else done.toFloat() / sessions.size },
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 6.dp),
                )
            }
            Spacer(Modifier.width(12.dp))
            Icon(
                if (expanded) Icons.Filled.KeyboardArrowUp else Icons.Filled.KeyboardArrowDown,
                contentDescription = if (expanded) "Kapat" else "Aç",
            )
        }
        if (expanded) {
            HorizontalDivider()
            sessions.forEach { s ->
                val status = when {
                    tracker.isCompleted(s) -> SessionStatus.DONE
                    !unlocked -> SessionStatus.LOCKED
                    else -> SessionStatus.OPEN
                }
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onSessionClick(s) }
                        .padding(horizontal = 16.dp, vertical = 12.dp),
                ) {
                    SessionStatusIcon(status)
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Text("${s.code} · ${s.title}", style = MaterialTheme.typography.bodyLarge)
                        Text(
                            "${s.date.shortLabel(today)} · ${s.main.joinToString { it.move.name }}",
                            style = MaterialTheme.typography.bodySmall,
                            maxLines = 1,
                        )
                    }
                }
            }
        }
    }
}
