package com.fightedu.ui.home

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.fightedu.core.domain.PlannedSession
import com.fightedu.core.domain.ProgressTracker
import com.fightedu.core.domain.WorkoutPlanner
import com.fightedu.ui.UiState
import com.fightedu.ui.components.AppScaffold
import com.fightedu.ui.components.MoveAnimation
import com.fightedu.ui.components.SectionTitle
import com.fightedu.ui.components.SessionStatus
import com.fightedu.ui.components.SessionStatusIcon
import com.fightedu.ui.shortLabel
import com.fightedu.ui.theme.SuccessGreen
import java.time.LocalDate

@Composable
fun HomeScreen(
    state: UiState,
    onOpenSession: (PlannedSession) -> Unit,
    onStartSession: (PlannedSession) -> Unit,
    onNewProgram: () -> Unit,
) {
    val sport = state.sport
    val tracker = state.tracker
    val today = LocalDate.now()
    val todaySession = tracker.sessionOn(today)
    val next = tracker.nextSession
    val currentWeek = tracker.currentWeek
    val currentPhase = state.sessions.firstOrNull { it.week == currentWeek }

    AppScaffold(title = "${sport?.emoji.orEmpty()} ${sport?.name.orEmpty()}", underBottomBar = true) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 8.dp),
        ) {
            OverallProgressCard(tracker, today)

            if (tracker.isFinished) {
                FinishedCard(onNewProgram)
            } else {
                SectionTitle("Bugün")
                when {
                    todaySession != null && tracker.isCompleted(todaySession) -> InfoCard(
                        "✅ Bugünün antrenmanı tamamlandı",
                        "Harika iş! Kaslarının toparlanması için iyi beslen ve uyu.",
                    )
                    todaySession != null -> SessionCard(
                        session = todaySession,
                        headline = "Bugünün antrenmanı",
                        onOpen = { onOpenSession(todaySession) },
                        onStart = { onStartSession(todaySession) },
                    )
                    else -> InfoCard(
                        "😌 Bugün dinlenme günü",
                        "Hafif esneme veya yürüyüş yapabilirsin. İstersen sıradaki antrenmanı şimdi de yapabilirsin.",
                    )
                }

                if (next != null && next != todaySession) {
                    SectionTitle("Sıradaki antrenman")
                    SessionCard(
                        session = next,
                        headline = next.date.shortLabel(today),
                        onOpen = { onOpenSession(next) },
                        onStart = { onStartSession(next) },
                    )
                }
            }

            if (currentPhase != null) {
                SectionTitle("Hafta $currentWeek · ${currentPhase.phaseTitle}")
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text("🎯 Hedef: ${currentPhase.phaseGoal}", style = MaterialTheme.typography.bodyMedium)
                        Spacer(Modifier.padding(top = 8.dp))
                        tracker.sessionsOfWeek(currentWeek).forEach { s ->
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clickable { onOpenSession(s) }
                                    .padding(vertical = 8.dp),
                            ) {
                                SessionStatusIcon(if (tracker.isCompleted(s)) SessionStatus.DONE else SessionStatus.OPEN)
                                Spacer(Modifier.width(12.dp))
                                Column(Modifier.weight(1f)) {
                                    Text("${s.code} · ${s.title}", style = MaterialTheme.typography.bodyLarge)
                                    Text(s.date.shortLabel(today), style = MaterialTheme.typography.bodySmall)
                                }
                            }
                        }
                    }
                }
            }
            Spacer(Modifier.padding(bottom = 16.dp))
        }
    }
}

@Composable
private fun OverallProgressCard(tracker: ProgressTracker, today: LocalDate) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text("8 haftalık program", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.padding(top = 4.dp))
            Text(
                "Hafta ${tracker.currentWeek} / ${tracker.totalWeeks} · ${tracker.completedCount} / ${tracker.sessions.size} antrenman",
                style = MaterialTheme.typography.bodyMedium,
            )
            LinearProgressIndicator(
                progress = { tracker.overallProgress },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 10.dp),
            )
            val missed = tracker.missedCount(today)
            if (missed > 0) {
                Text(
                    "⏰ Kaçırılan $missed antrenman var. Sorun değil; kaldığın yerden devam et.",
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }
    }
}

@Composable
private fun SessionCard(
    session: PlannedSession,
    headline: String,
    onOpen: () -> Unit,
    onStart: () -> Unit,
) {
    Card(onClick = onOpen, modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                val preview = session.main.firstOrNull()?.move
                if (preview != null) {
                    MoveAnimation(preview, Modifier.size(84.dp), playing = false, corner = 12.dp)
                    Spacer(Modifier.width(16.dp))
                }
                Column(Modifier.weight(1f)) {
                    Text(headline, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
                    Text("Seans ${session.code}: ${session.title}", style = MaterialTheme.typography.titleMedium)
                    Text(
                        "Hafta ${session.week} · ~${WorkoutPlanner.estimatedMinutes(session)} dk · ${session.main.size} ana hareket",
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
            Spacer(Modifier.padding(top = 12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                OutlinedButton(onClick = onOpen, modifier = Modifier.weight(1f)) { Text("Detay") }
                Button(onClick = onStart, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Filled.PlayArrow, contentDescription = null)
                    Spacer(Modifier.width(4.dp))
                    Text("Başla")
                }
            }
        }
    }
}

@Composable
private fun InfoCard(title: String, body: String) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.padding(top = 4.dp))
            Text(body, style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
private fun FinishedCard(onNewProgram: () -> Unit) {
    Spacer(Modifier.padding(top = 16.dp))
    Card(
        colors = CardDefaults.cardColors(containerColor = SuccessGreen.copy(alpha = 0.12f)),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text("🏆 Tebrikler! Programı tamamladın.", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.padding(top = 4.dp))
            Text(
                "Temel teknikleri öğrendin. Şimdi bir kulüpte antrenör eşliğinde partner çalışmasına geçmenin tam zamanı. " +
                    "İstersen başka bir sporla yeni bir program başlatabilirsin.",
                style = MaterialTheme.typography.bodyMedium,
            )
            Spacer(Modifier.padding(top = 12.dp))
            Button(onClick = onNewProgram) { Text("Yeni program başlat") }
        }
    }
}
