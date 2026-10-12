package com.fightedu.ui.player

import android.media.AudioManager
import android.media.ToneGenerator
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fightedu.core.domain.PlannedSession
import com.fightedu.core.domain.WorkoutPlanner
import com.fightedu.core.domain.WorkoutStep
import com.fightedu.ui.components.AppScaffold
import com.fightedu.ui.components.BulletList
import com.fightedu.ui.components.MoveAnimation
import com.fightedu.ui.components.Pill
import com.fightedu.ui.formatClock
import kotlinx.coroutines.delay

private fun durationOf(step: WorkoutStep): Int = when (step) {
    is WorkoutStep.Work -> step.seconds ?: 0
    is WorkoutStep.Rest -> step.seconds
}

private fun isTimed(step: WorkoutStep): Boolean = durationOf(step) > 0

@Composable
fun PlayerScreen(
    session: PlannedSession,
    onExit: () -> Unit,
    onCompleted: () -> Unit,
    onDone: () -> Unit,
) {
    val steps = remember(session.key) { WorkoutPlanner.steps(session) }
    var index by rememberSaveable { mutableIntStateOf(0) }
    var remaining by rememberSaveable { mutableIntStateOf(durationOf(steps.first())) }
    var paused by rememberSaveable { mutableStateOf(false) }
    var finished by rememberSaveable { mutableStateOf(false) }
    var elapsed by rememberSaveable { mutableIntStateOf(0) }
    var showExitDialog by remember { mutableStateOf(false) }

    fun goTo(target: Int) {
        if (target >= steps.size) {
            finished = true
        } else {
            index = target.coerceAtLeast(0)
            remaining = durationOf(steps[index])
        }
    }

    // Ekran antrenman boyunca açık kalsın.
    val view = LocalView.current
    DisposableEffect(view) {
        view.keepScreenOn = true
        onDispose { view.keepScreenOn = false }
    }

    val tone = remember { runCatching { ToneGenerator(AudioManager.STREAM_MUSIC, 80) }.getOrNull() }
    DisposableEffect(tone) { onDispose { tone?.release() } }

    val step = steps[index]

    // Geri sayım: süreli adımlarda 0'a gelince otomatik ilerler.
    LaunchedEffect(index, paused, finished) {
        if (finished || paused || !isTimed(step)) return@LaunchedEffect
        while (remaining > 0) {
            delay(1_000)
            remaining -= 1
            if (remaining in 1..3) tone?.startTone(ToneGenerator.TONE_PROP_BEEP, 120)
        }
        tone?.startTone(ToneGenerator.TONE_PROP_BEEP2, 350)
        goTo(index + 1)
    }

    LaunchedEffect(paused, finished) {
        while (!paused && !finished) {
            delay(1_000)
            elapsed += 1
        }
    }

    LaunchedEffect(finished) {
        if (finished) onCompleted()
    }

    BackHandler { if (finished) onDone() else showExitDialog = true }

    AppScaffold(
        title = "Hafta ${session.week} · ${session.title}",
        actions = {
            IconButton(onClick = { if (finished) onDone() else showExitDialog = true }) {
                Icon(Icons.Filled.Close, contentDescription = "Kapat")
            }
        },
        bottomBar = {
            if (!finished) {
                Controls(
                    step = step,
                    canGoBack = index > 0,
                    paused = paused,
                    onPrevious = { goTo(index - 1) },
                    onTogglePause = { paused = !paused },
                    onNext = { goTo(index + 1) },
                    onAddTime = { remaining += 15 },
                )
            }
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp),
        ) {
            LinearProgressIndicator(
                progress = { if (finished) 1f else (index + 1f) / steps.size },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 8.dp),
            )
            when {
                finished -> FinishedContent(elapsed, onDone)
                step is WorkoutStep.Work -> WorkContent(step, remaining, paused, nextName = steps.drop(index + 1)
                    .filterIsInstance<WorkoutStep.Work>().firstOrNull()?.exercise?.move?.name)
                step is WorkoutStep.Rest -> RestContent(step, remaining)
            }
        }
    }

    if (showExitDialog) {
        AlertDialog(
            onDismissRequest = { showExitDialog = false },
            title = { Text("Antrenmandan çıkılsın mı?") },
            text = { Text("Bu antrenman tamamlanmış olarak kaydedilmeyecek.") },
            confirmButton = {
                TextButton(onClick = {
                    showExitDialog = false
                    onExit()
                }) { Text("Çık") }
            },
            dismissButton = { TextButton(onClick = { showExitDialog = false }) { Text("Devam et") } },
        )
    }
}

@Composable
private fun WorkContent(step: WorkoutStep.Work, remaining: Int, paused: Boolean, nextName: String?) {
    val ex = step.exercise
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Pill(ex.section.label)
        if (step.totalSets > 1) Pill("Set ${step.set} / ${step.totalSets}")
    }
    Spacer(Modifier.padding(top = 8.dp))
    MoveAnimation(
        move = ex.move,
        playing = !paused,
        modifier = Modifier
            .fillMaxWidth()
            .aspectRatio(1.25f),
    )
    Spacer(Modifier.padding(top = 12.dp))
    Text(ex.move.name, style = MaterialTheme.typography.headlineMedium)
    Text(
        text = if (step.seconds != null) formatClock(remaining) else "${ex.reps} tekrar",
        fontSize = 56.sp,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.primary,
        textAlign = TextAlign.Center,
        modifier = Modifier.fillMaxWidth(),
    )
    if (paused) {
        Text("Duraklatıldı", textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth())
    }
    Spacer(Modifier.padding(top = 8.dp))
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text("Nasıl yapılır?", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.padding(top = 8.dp))
            BulletList(ex.move.steps, numbered = true)
            if (ex.move.tip.isNotBlank()) {
                Spacer(Modifier.padding(top = 8.dp))
                Text("💡 ${ex.move.tip}", style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
    if (nextName != null) {
        Text(
            "Sonraki: $nextName",
            style = MaterialTheme.typography.bodySmall,
            modifier = Modifier.padding(vertical = 12.dp),
        )
    }
}

@Composable
private fun RestContent(step: WorkoutStep.Rest, remaining: Int) {
    Spacer(Modifier.padding(top = 24.dp))
    Text("Dinlen", style = MaterialTheme.typography.headlineMedium, textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth())
    Text(
        formatClock(remaining),
        fontSize = 72.sp,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.primary,
        textAlign = TextAlign.Center,
        modifier = Modifier.fillMaxWidth(),
    )
    Text("Nefesini düzenle, su iç.", textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth())
    Spacer(Modifier.padding(top = 24.dp))
    Card(Modifier.fillMaxWidth()) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            MoveAnimation(step.next.move, Modifier.size(96.dp), corner = 12.dp)
            Spacer(Modifier.width(12.dp))
            Column {
                Text("Sıradaki", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
                Text(step.next.move.name, style = MaterialTheme.typography.titleMedium)
                Text(step.next.doseLabel, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
private fun FinishedContent(elapsed: Int, onDone: () -> Unit) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
        Spacer(Modifier.padding(top = 48.dp))
        Text("🎉", fontSize = 72.sp)
        Text("Antrenman tamamlandı!", style = MaterialTheme.typography.headlineMedium, textAlign = TextAlign.Center)
        Spacer(Modifier.padding(top = 8.dp))
        Text("Süre: ${formatClock(elapsed)}", style = MaterialTheme.typography.titleMedium)
        Text("İlerlemen kaydedildi.", style = MaterialTheme.typography.bodyMedium)
        Spacer(Modifier.padding(top = 24.dp))
        Button(onClick = onDone) { Text("Ana sayfaya dön") }
    }
}

@Composable
private fun Controls(
    step: WorkoutStep,
    canGoBack: Boolean,
    paused: Boolean,
    onPrevious: () -> Unit,
    onTogglePause: () -> Unit,
    onNext: () -> Unit,
    onAddTime: () -> Unit,
) {
    Surface(tonalElevation = 3.dp) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .navigationBarsPadding()
                .padding(16.dp),
        ) {
            if (step is WorkoutStep.Rest) {
                TextButton(onClick = onAddTime, modifier = Modifier.align(Alignment.CenterHorizontally)) {
                    Text("+15 sn dinlenme")
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = onPrevious, enabled = canGoBack, modifier = Modifier.weight(1f)) {
                    Text("Önceki")
                }
                if (isTimed(step)) {
                    OutlinedButton(onClick = onTogglePause, modifier = Modifier.weight(1f)) {
                        Text(if (paused) "Devam" else "Duraklat")
                    }
                }
                val isRepWork = step is WorkoutStep.Work && !isTimed(step)
                Button(onClick = onNext, modifier = Modifier.weight(1f)) {
                    Text(if (isRepWork) "Bitti ✓" else "Atla")
                }
            }
        }
    }
}
