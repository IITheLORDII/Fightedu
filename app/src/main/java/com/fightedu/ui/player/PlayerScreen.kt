package com.fightedu.ui.player

import androidx.activity.compose.BackHandler
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.fightedu.coach.Coach
import com.fightedu.core.domain.SessionRunner
import com.fightedu.core.domain.Step
import com.fightedu.core.domain.TrainingPlanner
import com.fightedu.core.model.BlockMode
import com.fightedu.core.model.TrainingDay
import com.fightedu.data.CoachSettings
import com.fightedu.ui.components.KindBadge
import com.fightedu.ui.components.MoveAnimation
import com.fightedu.ui.components.blockColor
import com.fightedu.ui.formatClock

/** Raunt raunt, hareket hareket ilerleyen koçlu antrenman oynatıcısı. */
@Composable
fun PlayerScreen(
    day: TrainingDay,
    planner: TrainingPlanner,
    coach: CoachSettings,
    onExit: () -> Unit,
    onCompleted: () -> Unit,
    onDone: () -> Unit,
    vm: PlayerViewModel = viewModel(),
) {
    val steps = remember(day) { planner.steps(day) }
    LaunchedEffect(day, coach) { vm.setup(day.day, steps, coach) }
    val ui by vm.ui.collectAsStateWithLifecycle()
    var showExit by rememberSaveable { mutableStateOf(false) }
    val view = LocalView.current
    DisposableEffect(Unit) {
        view.keepScreenOn = true
        onDispose { view.keepScreenOn = false }
    }
    LaunchedEffect(ui.finished) { if (ui.finished) onCompleted() }
    BackHandler(enabled = !ui.finished) { showExit = true }

    val step = steps.getOrNull(ui.index)
    val isRest = step is Step.Rest && !ui.finished
    val bg = if (isRest) Color(0xFF14171C) else MaterialTheme.colorScheme.background
    val fg = if (isRest) Color(0xFFF2F3F5) else MaterialTheme.colorScheme.onBackground

    Surface(color = bg, contentColor = fg, modifier = Modifier.fillMaxSize()) {
        Column(
            Modifier
                .fillMaxSize()
                .statusBarsPadding()
                .navigationBarsPadding(),
        ) {
            TopBar(day, steps, ui, fg) { if (ui.finished) onDone() else showExit = true }
            Box(Modifier.weight(1f).fillMaxWidth()) {
                when {
                    ui.finished -> FinishedContent(day, steps, ui.totalElapsed, onDone)
                    step is Step.Work -> WorkContent(step, ui, vm::next)
                    step is Step.Rest -> RestContent(step, ui, fg, onAdd = { vm.addRest(15) })
                }
            }
            if (!ui.finished && step != null) Controls(step, ui.paused, fg, vm::prev, vm::togglePause, vm::next)
        }
    }

    if (showExit) {
        AlertDialog(
            onDismissRequest = { showExit = false },
            title = { Text("Antrenmandan çıkılsın mı?") },
            text = { Text("İlerlemen kaydedilmez; Gün ${day.day} tamamlanmamış olarak kalır.") },
            confirmButton = { TextButton(onClick = { showExit = false; onExit() }) { Text("Çık") } },
            dismissButton = { TextButton(onClick = { showExit = false }) { Text("Devam et") } },
        )
    }
}

@Composable
private fun TopBar(day: TrainingDay, steps: List<Step>, ui: PlayerUi, fg: Color, onClose: () -> Unit) {
    val current = steps.getOrNull(ui.index)
    val block = current?.let { day.blocks.getOrNull(it.blockIndex) }
    Column(Modifier.padding(horizontal = 16.dp, vertical = 8.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("GÜN ${day.day}", style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold,
                    color = fg.copy(alpha = 0.7f))
                Text(day.title, style = MaterialTheme.typography.titleMedium, maxLines = 1)
            }
            Text(formatClock(ui.totalElapsed), style = MaterialTheme.typography.titleMedium)
            IconButton(onClick = onClose) { Icon(Icons.Filled.Close, contentDescription = "Kapat", tint = fg) }
        }
        // blok segmentli ilerleme şeridi
        val perBlock = day.blocks.indices.map { b -> steps.count { it.blockIndex == b } }
        Row(Modifier.fillMaxWidth().height(6.dp).padding(top = 2.dp), horizontalArrangement = Arrangement.spacedBy(3.dp)) {
            day.blocks.forEachIndexed { b, blk ->
                val first = steps.indexOfFirst { it.blockIndex == b }
                val done = when {
                    ui.finished || (current != null && current.blockIndex > b) -> 1f
                    current != null && current.blockIndex == b -> (ui.index - first).toFloat() / perBlock[b].coerceAtLeast(1)
                    else -> 0f
                }
                val c = blockColor(blk.kind)
                Box(Modifier.weight(perBlock[b].coerceAtLeast(1).toFloat()).height(4.dp).background(c.copy(alpha = 0.25f), RoundedCornerShape(2.dp))) {
                    Box(Modifier.fillMaxWidth(done.coerceIn(0f, 1f)).height(4.dp).background(c, RoundedCornerShape(2.dp)))
                }
            }
        }
        block?.let { Text(it.title, style = MaterialTheme.typography.labelSmall, color = fg.copy(alpha = 0.7f)) }
    }
}

@Composable
private fun WorkContent(step: Step.Work, ui: PlayerUi, onDoneReps: () -> Unit) {
    val block = step.block
    val color = blockColor(block.kind)
    val shown = ui.callout?.move ?: step.move
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
            KindBadge(block.kind)
            Spacer(Modifier.weight(1f))
            Text(roundLabel(step), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Black, color = color)
        }
        Box(Modifier.fillMaxWidth()) {
            MoveAnimation(shown, modifier = Modifier.fillMaxWidth().aspectRatio(1.25f), paused = ui.paused)
            // koç komutu bandı
            androidx.compose.animation.AnimatedVisibility( // ColumnScope sürümü değil; Box içinde hizalanır
                visible = ui.callout != null,
                enter = fadeIn() + scaleIn(initialScale = 0.8f),
                exit = fadeOut(),
                modifier = Modifier.align(Alignment.BottomCenter).padding(12.dp),
            ) {
                Surface(color = color, contentColor = Color.White, shape = RoundedCornerShape(12.dp)) {
                    Text(
                        (ui.callout?.let { Coach.callName(it.move) } ?: "").uppercase() + "!",
                        fontSize = 28.sp, fontWeight = FontWeight.Black,
                        modifier = Modifier.padding(horizontal = 18.dp, vertical = 8.dp),
                    )
                }
            }
        }
        Text(shown.name, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, textAlign = TextAlign.Center)
        if (step.seconds != null) {
            RingTimer(ui.remaining, step.seconds ?: 1, color, if (ui.paused) "DURAKLATILDI" else null, 190.dp)
        } else {
            Text("${step.reps} TEKRAR", fontSize = 48.sp, fontWeight = FontWeight.Black, color = color)
            Button(onClick = onDoneReps, modifier = Modifier.fillMaxWidth().height(56.dp)) {
                Text("Bitti ✓", style = MaterialTheme.typography.titleMedium)
            }
        }
        if (step.round == 1 && step.station == 1 && block.cue.isNotBlank()) {
            Text(block.cue, style = MaterialTheme.typography.bodyMedium, textAlign = TextAlign.Center)
        } else if (block.mode == BlockMode.ROUND && step.callouts.isNotEmpty()) {
            Text("Komutları dinle; arada ayak oyunu ve gard.", style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
private fun RestContent(step: Step.Rest, ui: PlayerUi, fg: Color, onAdd: () -> Unit) {
    val n = step.next
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Spacer(Modifier.height(8.dp))
        Text(if (step.betweenBlocks) "BLOK BİTTİ · DİNLEN" else "DİNLEN", fontSize = 26.sp, fontWeight = FontWeight.Black)
        RingTimer(ui.remaining, step.seconds, Color(0xFF7FD1AE), if (ui.paused) "DURAKLATILDI" else null, 220.dp, fg)
        Text("Burnundan nefes al, ağzından ver. Omuzlarını gevşet.", style = MaterialTheme.typography.bodyMedium,
            color = fg.copy(alpha = 0.8f), textAlign = TextAlign.Center)
        OutlinedButton(onClick = onAdd) { Text("+15 sn dinlenme", color = fg) }
        Surface(color = Color.White.copy(alpha = 0.08f), contentColor = fg, shape = RoundedCornerShape(16.dp), modifier = Modifier.fillMaxWidth()) {
            Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                MoveAnimation(n.move, playing = false, corner = 10.dp, modifier = Modifier.width(110.dp).aspectRatio(1.25f))
                Spacer(Modifier.width(12.dp))
                Column {
                    Text("SIRADAKİ", style = MaterialTheme.typography.labelMedium, color = blockColor(n.block.kind), fontWeight = FontWeight.Bold)
                    Text(n.block.title, style = MaterialTheme.typography.titleMedium)
                    Text("${roundLabel(n)} · ${n.move.name}", style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
}

@Composable
private fun FinishedContent(day: TrainingDay, steps: List<Step>, total: Int, onDone: () -> Unit) {
    val rounds = steps.count { it is Step.Work && it.block.mode == BlockMode.ROUND }
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("🏆", fontSize = 64.sp)
        Text("GÜN ${day.day} TAMAMLANDI", fontSize = 28.sp, fontWeight = FontWeight.Black, textAlign = TextAlign.Center)
        Text(day.title, style = MaterialTheme.typography.titleMedium)
        Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
            Stat(formatClock(total), "süre")
            Stat("$rounds", "raunt")
            Stat("${day.blocks.size}", "blok")
        }
        day.blocks.forEach { b ->
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(10.dp).background(blockColor(b.kind), RoundedCornerShape(5.dp)))
                Text("  ${b.title}", modifier = Modifier.weight(1f))
                Text(TrainingPlanner.summary(b).substringBefore(" · "), style = MaterialTheme.typography.bodySmall)
            }
        }
        Spacer(Modifier.height(8.dp))
        Button(onClick = onDone, modifier = Modifier.fillMaxWidth().height(56.dp)) { Text("Ana sayfaya dön") }
    }
}

@Composable
private fun Stat(value: String, label: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(value, fontSize = 30.sp, fontWeight = FontWeight.Black, color = MaterialTheme.colorScheme.primary)
        Text(label, style = MaterialTheme.typography.labelMedium)
    }
}

@Composable
private fun RingTimer(remaining: Int, total: Int, color: Color, note: String?, size: Dp, fg: Color = MaterialTheme.colorScheme.onBackground) {
    Box(Modifier.size(size), contentAlignment = Alignment.Center) {
        Canvas(Modifier.fillMaxSize()) {
            val stroke = 14.dp.toPx()
            val inset = stroke / 2
            val arcSize = androidx.compose.ui.geometry.Size(this.size.width - stroke, this.size.height - stroke)
            val tl = androidx.compose.ui.geometry.Offset(inset, inset)
            drawArc(color.copy(alpha = 0.18f), 0f, 360f, false, tl, arcSize, style = Stroke(stroke))
            val frac = if (total > 0) remaining.toFloat() / total else 0f
            drawArc(color, -90f, 360f * frac.coerceIn(0f, 1f), false, tl, arcSize, style = Stroke(stroke, cap = StrokeCap.Round))
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(formatClock(remaining), fontSize = 52.sp, fontWeight = FontWeight.Black, color = fg)
            if (note != null) Text(note, style = MaterialTheme.typography.labelMedium, color = fg.copy(alpha = 0.7f))
        }
    }
}

@Composable
private fun Controls(step: Step, paused: Boolean, fg: Color, onPrev: () -> Unit, onPause: () -> Unit, onNext: () -> Unit) {
    val timed = SessionRunner.durationOf(step) > 0
    Row(
        Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        TextButton(onClick = onPrev) { Text("◀ Önceki", color = fg) }
        if (timed) {
            FilledIconButton(
                onClick = onPause,
                modifier = Modifier.size(72.dp),
                colors = IconButtonDefaults.filledIconButtonColors(),
            ) {
                if (paused) {
                    Icon(Icons.Filled.PlayArrow, contentDescription = "Devam", modifier = Modifier.size(40.dp))
                } else {
                    Text("❚❚", fontSize = 26.sp, fontWeight = FontWeight.Black)
                }
            }
        }
        TextButton(onClick = onNext) { Text(if (step is Step.Rest) "Atla ▶" else "Sonraki ▶", color = fg) }
    }
}

private fun roundLabel(s: Step.Work): String = when (s.block.mode) {
    BlockMode.ROUND -> "RAUNT ${s.round} / ${s.totalRounds}"
    BlockMode.CIRCUIT -> "TUR ${s.round}/${s.totalRounds} · ${s.station}/${s.stations}"
    BlockMode.REPS -> "SET ${s.round}/${s.totalRounds} · ${s.station}/${s.stations}"
}
