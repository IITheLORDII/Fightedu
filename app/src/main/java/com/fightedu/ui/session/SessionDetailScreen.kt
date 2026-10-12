package com.fightedu.ui.session

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.fightedu.core.domain.PlannedExercise
import com.fightedu.core.domain.PlannedSession
import com.fightedu.core.domain.Section
import com.fightedu.core.domain.WorkoutPlanner
import com.fightedu.core.model.Move
import com.fightedu.ui.components.AppScaffold
import com.fightedu.ui.components.MoveAnimation
import com.fightedu.ui.components.Pill
import com.fightedu.ui.components.SectionTitle
import com.fightedu.ui.longLabel
import com.fightedu.ui.theme.SuccessGreen

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SessionDetailScreen(
    session: PlannedSession,
    completed: Boolean,
    onBack: () -> Unit,
    onStart: () -> Unit,
    onToggleCompleted: (Boolean) -> Unit,
    onOpenMove: (Move) -> Unit,
) {
    AppScaffold(
        title = "Hafta ${session.week} · Seans ${session.code}",
        onBack = onBack,
        bottomBar = {
            Surface(tonalElevation = 3.dp) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .navigationBarsPadding()
                        .padding(16.dp),
                ) {
                    OutlinedButton(onClick = { onToggleCompleted(!completed) }, modifier = Modifier.weight(1f)) {
                        Text(if (completed) "İşareti kaldır" else "Yapıldı işaretle")
                    }
                    Button(onClick = onStart, modifier = Modifier.weight(1f)) {
                        Icon(Icons.Filled.PlayArrow, contentDescription = null)
                        Spacer(Modifier.width(4.dp))
                        Text("Başlat")
                    }
                }
            }
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
        ) {
            Text(session.title, style = MaterialTheme.typography.headlineMedium)
            Text(session.date.longLabel(), style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.padding(top = 8.dp))
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Pill("~${WorkoutPlanner.estimatedMinutes(session)} dk")
                Pill(session.phaseTitle)
                if (completed) Pill("Tamamlandı ✓", SuccessGreen)
            }
            Spacer(Modifier.padding(top = 12.dp))
            Text("🎯 ${session.phaseGoal}", style = MaterialTheme.typography.bodyMedium)

            listOf(
                Section.WARMUP to session.warmup,
                Section.MAIN to session.main,
                Section.COOLDOWN to session.cooldown,
            ).forEach { (section, exercises) ->
                SectionTitle(section.label)
                Card(Modifier.fillMaxWidth()) {
                    exercises.forEachIndexed { i, ex ->
                        if (i > 0) HorizontalDivider()
                        ExerciseRow(ex, onClick = { onOpenMove(ex.move) })
                    }
                }
            }
            Spacer(Modifier.padding(bottom = 16.dp))
        }
    }
}

@Composable
private fun ExerciseRow(exercise: PlannedExercise, onClick: () -> Unit) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .fillMaxWidth()
            .padding(12.dp),
    ) {
        Card(onClick = onClick) {
            MoveAnimation(exercise.move, Modifier.size(64.dp), playing = false, corner = 12.dp)
        }
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text(exercise.move.name, style = MaterialTheme.typography.bodyLarge)
            Text(
                exercise.doseLabel + if (exercise.sets > 1 || exercise.rest > 0) " · ${exercise.rest} sn dinlenme" else "",
                style = MaterialTheme.typography.bodySmall,
            )
        }
        OutlinedButton(onClick = onClick) { Text("Nasıl?") }
    }
}
