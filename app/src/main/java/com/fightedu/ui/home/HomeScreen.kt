package com.fightedu.ui.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fightedu.core.model.TrainingDay
import com.fightedu.ui.UiState
import com.fightedu.ui.components.AppScaffold
import com.fightedu.ui.components.BlockChip
import com.fightedu.ui.components.Pill
import com.fightedu.ui.components.SectionTitle
import com.fightedu.ui.components.SessionStatus
import com.fightedu.ui.components.SessionStatusIcon

@Composable
fun HomeScreen(
    state: UiState,
    onOpenDay: (Int) -> Unit,
    onStartDay: (Int) -> Unit,
    onNewProgram: () -> Unit,
) {
    val sport = state.sport
    val program = state.program
    val tracker = state.tracker
    val planner = state.planner
    AppScaffold(title = "${sport?.emoji.orEmpty()} ${sport?.name ?: "FightEdu"}", underBottomBar = true) { inner ->
        if (program == null || tracker == null || planner == null) return@AppScaffold
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(inner),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            val next = tracker.nextDay
            item {
                if (next != null) {
                    NextDayCard(next, program.totalDays, tracker.currentPhase?.title.orEmpty(), planner.estimatedMinutes(next),
                        onStart = { onStartDay(next.day) }, onOpen = { onOpenDay(next.day) })
                } else {
                    FinishedCard(onNewProgram)
                }
            }
            item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("İlerleme", style = MaterialTheme.typography.titleMedium)
                        Text("${tracker.completedCount} / ${tracker.totalDays} gün tamamlandı", style = MaterialTheme.typography.bodyMedium)
                        LinearProgressIndicator(progress = { tracker.overallProgress }, modifier = Modifier.fillMaxWidth())
                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            program.phases.forEach { ph ->
                                val n = ph.to - ph.from + 1
                                Column(Modifier.weight(1f)) {
                                    LinearProgressIndicator(
                                        progress = { tracker.completedInPhase(ph).toFloat() / n },
                                        modifier = Modifier.fillMaxWidth().height(6.dp),
                                    )
                                    Text(ph.title, style = MaterialTheme.typography.labelSmall, maxLines = 1)
                                }
                            }
                        }
                    }
                }
            }
            if (next != null) {
                val upcoming = program.days.filter { it.day > next.day }.take(3)
                if (upcoming.isNotEmpty()) {
                    item { SectionTitle("Sonraki günler") }
                    upcoming.forEach { d ->
                        item {
                            Card(onClick = { onOpenDay(d.day) }, modifier = Modifier.fillMaxWidth()) {
                                Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                                    SessionStatusIcon(SessionStatus.LOCKED, Modifier.size(22.dp))
                                    Spacer(Modifier.padding(start = 12.dp))
                                    Column(Modifier.weight(1f)) {
                                        Text("Gün ${d.day} · ${d.title}", style = MaterialTheme.typography.titleSmall)
                                        Text("~${planner.estimatedMinutes(d)} dk · ${d.blocks.size} blok", style = MaterialTheme.typography.bodySmall)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun NextDayCard(day: TrainingDay, total: Int, phase: String, minutes: Int, onStart: () -> Unit, onOpen: () -> Unit) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
        shape = RoundedCornerShape(20.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    "GÜN ${day.day}",
                    fontSize = 40.sp,
                    fontWeight = FontWeight.Black,
                    color = MaterialTheme.colorScheme.primary,
                )
                Text(" / $total", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 12.dp))
                Spacer(Modifier.weight(1f))
                Pill(phase)
            }
            Text(day.title, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text(day.focus, style = MaterialTheme.typography.bodyMedium)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                day.blocks.forEach { BlockChip(it) }
            }
            Text("Yaklaşık $minutes dakika", style = MaterialTheme.typography.labelLarge)
            Button(onClick = onStart, modifier = Modifier.fillMaxWidth().height(56.dp)) {
                Icon(Icons.Filled.PlayArrow, contentDescription = null)
                Text("  Gün ${day.day} antrenmanını başlat", style = MaterialTheme.typography.titleMedium)
            }
            TextButton(onClick = onOpen, modifier = Modifier.align(Alignment.CenterHorizontally)) { Text("Antrenmanın ayrıntıları") }
        }
    }
}

@Composable
private fun FinishedCard(onNewProgram: () -> Unit) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("🏆 Program tamamlandı!", style = MaterialTheme.typography.headlineSmall)
            Text("24 günün hepsini bitirdin. İstediğin günü tekrar yapabilir ya da yeni bir spora başlayabilirsin.")
            OutlinedButton(onClick = onNewProgram) { Text("Yeni program") }
        }
    }
}
