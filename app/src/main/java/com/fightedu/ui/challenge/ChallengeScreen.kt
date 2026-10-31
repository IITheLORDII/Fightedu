package com.fightedu.ui.challenge

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fightedu.core.domain.ChallengeCalendar
import com.fightedu.core.domain.ChallengeDay
import com.fightedu.core.domain.ChallengeProgress
import com.fightedu.core.domain.TrainingPlanner
import com.fightedu.core.model.Sport
import com.fightedu.data.User
import com.fightedu.ui.components.BlockChip
import com.fightedu.ui.components.HeroImage
import com.fightedu.ui.components.Scrim
import com.fightedu.ui.theme.DisplayFont
import com.fightedu.ui.theme.SuccessGreen

private val Gold = Color(0xFFFFB300)

/** Ana sekme: 30 günlük meydan okuma — ilerleme halkası, bugünün kartı, haftalık gün ızgarası, evreler. */
@Composable
fun ChallengeScreen(
    user: User?,
    sport: Sport,
    challenge: ChallengeProgress,
    planner: TrainingPlanner,
    totalMinutes: Int,
    onOpenDay: (ChallengeDay) -> Unit,
    onStartDay: (ChallengeDay) -> Unit,
    onOpenProfile: () -> Unit,
    onChangeSport: () -> Unit,
    onRestart: () -> Unit,
) {
    var lockedDay by rememberSaveable { mutableStateOf<Int?>(null) }
    var confirmRestart by rememberSaveable { mutableStateOf(false) }
    val accent = MaterialTheme.colorScheme.primary

    fun tap(day: ChallengeDay) {
        if (challenge.isUnlocked(day.number)) onOpenDay(day) else lockedDay = day.number
    }

    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item { Header(user, sport, challenge, onOpenProfile, onChangeSport) }
        item {
            Row(Modifier.padding(horizontal = 16.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                StatTile("🔥", "${challenge.currentStreak}", "günlük seri", Modifier.weight(1f))
                StatTile("💪", "${challenge.workoutsDone}", "antrenman", Modifier.weight(1f))
                StatTile("⏱", "$totalMinutes", "dakika", Modifier.weight(1f))
            }
        }
        item {
            val current = challenge.current
            Box(Modifier.padding(horizontal = 16.dp)) {
                when (current) {
                    null -> FinishedCard(sport, onRestart = { confirmRestart = true }, onChangeSport = onChangeSport)
                    is ChallengeDay.Workout -> WorkoutCard(current, planner, challenge, onStart = { onStartDay(current) },
                        onDetails = { onOpenDay(current) })
                    is ChallengeDay.Rest -> RestCard(current, onOpen = { onOpenDay(current) })
                }
            }
        }
        item {
            Row(
                Modifier.fillMaxWidth().padding(start = 16.dp, end = 16.dp, top = 6.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("30 GÜNLÜK PLAN", style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
                Legend("😴", "dinlenme")
                Spacer(Modifier.width(10.dp))
                Legend("🏆", "hafta")
            }
        }
        items(ChallengeCalendar.weeks) { i -> WeekRow(i + 1, challenge, ::tap) }
        item {
            Column(Modifier.padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("EVRELER", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(top = 6.dp))
                challenge.program.phases.forEachIndexed { i, phase ->
                    val days = challenge.daysOfPhase(phase)
                    val done = days.count { challenge.isDone(it) }
                    val active = challenge.current?.let { challenge.phaseOf(it.number) } == phase
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = if (active) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant,
                        ),
                        shape = RoundedCornerShape(16.dp),
                    ) {
                        Column(Modifier.fillMaxWidth().padding(14.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text("${i + 1}. ${phase.title}", style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                                Text("Gün ${days.first()}–${days.last()}", style = MaterialTheme.typography.labelMedium)
                            }
                            Text(phase.goal, style = MaterialTheme.typography.bodySmall, modifier = Modifier.padding(vertical = 6.dp))
                            LinearProgressIndicator(
                                progress = { done.toFloat() / days.size },
                                modifier = Modifier.fillMaxWidth().height(6.dp).clip(CircleShape),
                                color = if (done == days.size) SuccessGreen else accent,
                            )
                        }
                    }
                }
            }
        }
    }

    lockedDay?.let { n ->
        val day = challenge.day(n)
        AlertDialog(
            onDismissRequest = { lockedDay = null },
            icon = { Icon(Icons.Filled.Lock, contentDescription = null) },
            title = { Text("Gün $n henüz kilitli") },
            text = { Text("Önce Gün ${n - 1}'i tamamla. Günler sırayla açılır; vücudunun her güne hazır olması için böylesi daha güvenli.") },
            confirmButton = { TextButton(onClick = { lockedDay = null }) { Text("Tamam") } },
            dismissButton = {
                if (day != null) {
                    TextButton(onClick = {
                        lockedDay = null
                        onOpenDay(day)
                    }) { Text("Yine de göz at") }
                }
            },
        )
    }
    if (confirmRestart) {
        AlertDialog(
            onDismissRequest = { confirmRestart = false },
            title = { Text("Meydan okuma baştan başlasın mı?") },
            text = { Text("${sport.name} için tamamladığın günler sıfırlanır. Serin ve diğer dallardaki ilerlemen korunur.") },
            confirmButton = {
                TextButton(onClick = {
                    confirmRestart = false
                    onRestart()
                }) { Text("Baştan başlat") }
            },
            dismissButton = { TextButton(onClick = { confirmRestart = false }) { Text("Vazgeç") } },
        )
    }
}

@Composable
private fun Header(
    user: User?,
    sport: Sport,
    challenge: ChallengeProgress,
    onOpenProfile: () -> Unit,
    onChangeSport: () -> Unit,
) {
    val bg = MaterialTheme.colorScheme.background
    Box(Modifier.fillMaxWidth().height(300.dp)) {
        HeroImage(sport.id, Modifier.fillMaxSize(), alignment = Alignment.TopCenter)
        Box(Modifier.matchParentSize().background(Color.Black.copy(alpha = 0.25f)))
        Scrim(from = 0.45f, color = bg, strength = 1f)
        Row(
            Modifier.statusBarsPadding().padding(horizontal = 16.dp, vertical = 8.dp).fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                Modifier
                    .size(42.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.primary)
                    .clickable(onClick = onOpenProfile),
                contentAlignment = Alignment.Center,
            ) {
                Text(user?.initials ?: "?", color = MaterialTheme.colorScheme.onPrimary, fontWeight = FontWeight.Bold)
            }
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f)) {
                Text("Merhaba", color = Color.White.copy(alpha = 0.8f), fontSize = 12.sp)
                Text(user?.name ?: "Sporcu", color = Color.White, fontWeight = FontWeight.Bold, maxLines = 1,
                    overflow = TextOverflow.Ellipsis)
            }
            Surface(
                onClick = onChangeSport,
                color = Color.Black.copy(alpha = 0.45f),
                contentColor = Color.White,
                shape = RoundedCornerShape(50),
            ) {
                Text("${sport.emoji} Dalı değiştir", fontSize = 13.sp, modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp))
            }
        }
        Row(
            Modifier.align(Alignment.BottomStart).fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp),
            verticalAlignment = Alignment.Bottom,
        ) {
            Column(Modifier.weight(1f)) {
                Text(sport.name.uppercase(), fontFamily = DisplayFont, fontWeight = FontWeight.ExtraBold, fontSize = 40.sp,
                    lineHeight = 40.sp, color = MaterialTheme.colorScheme.onBackground)
                Text("30 GÜNLÜK MEYDAN OKUMA", fontFamily = DisplayFont, fontWeight = FontWeight.Bold, letterSpacing = 2.sp,
                    color = MaterialTheme.colorScheme.primary)
                challenge.current?.let { cur ->
                    challenge.phaseOf(cur.number)?.let {
                        Text("Evre: ${it.title}", style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
            ProgressRing(challenge.doneCount, ChallengeCalendar.LENGTH, 104.dp)
        }
    }
}

@Composable
fun ProgressRing(done: Int, total: Int, size: Dp, stroke: Dp = 10.dp) {
    val accent = MaterialTheme.colorScheme.primary
    val track = MaterialTheme.colorScheme.surfaceVariant
    val sweep by animateFloatAsState(done.toFloat() / total, tween(900), label = "ring")
    Box(Modifier.size(size), contentAlignment = Alignment.Center) {
        Canvas(Modifier.fillMaxSize()) {
            val w = stroke.toPx()
            val arc = Size(this.size.width - w, this.size.height - w)
            val tl = Offset(w / 2, w / 2)
            drawArc(track, -90f, 360f, false, tl, arc, style = Stroke(w))
            drawArc(
                Brush.sweepGradient(listOf(lerp(accent, Color.White, 0.25f), accent, lerp(accent, Color.White, 0.25f))),
                -90f, 360f * sweep, false, tl, arc, style = Stroke(w, cap = StrokeCap.Round),
            )
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text("$done", fontFamily = DisplayFont, fontWeight = FontWeight.ExtraBold, fontSize = (size.value * 0.3f).sp,
                lineHeight = (size.value * 0.3f).sp, color = MaterialTheme.colorScheme.onBackground)
            Text("/ $total gün", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun StatTile(icon: String, value: String, label: String, modifier: Modifier = Modifier) {
    Surface(color = MaterialTheme.colorScheme.surfaceVariant, shape = RoundedCornerShape(16.dp), modifier = modifier) {
        Column(Modifier.padding(vertical = 10.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Text(icon, fontSize = 18.sp)
            Text(value, fontFamily = DisplayFont, fontWeight = FontWeight.ExtraBold, fontSize = 24.sp)
            Text(label, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun WorkoutCard(
    day: ChallengeDay.Workout,
    planner: TrainingPlanner,
    challenge: ChallengeProgress,
    onStart: () -> Unit,
    onDetails: () -> Unit,
) {
    val t = day.training
    val isFinal = day.number == ChallengeCalendar.LENGTH
    Card(
        shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
    ) {
        Column(Modifier.fillMaxWidth().padding(18.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    if (challenge.trainedToday) "SIRADAKİ" else "BUGÜN",
                    fontFamily = DisplayFont, fontWeight = FontWeight.Bold, letterSpacing = 2.sp,
                    color = MaterialTheme.colorScheme.primary, modifier = Modifier.weight(1f),
                )
                if (isFinal) Text("🏆 FİNAL", fontFamily = DisplayFont, fontWeight = FontWeight.Bold, color = Gold)
            }
            Row(verticalAlignment = Alignment.Bottom) {
                Text("GÜN ${day.number}", fontFamily = DisplayFont, fontWeight = FontWeight.ExtraBold, fontSize = 44.sp,
                    lineHeight = 44.sp, color = MaterialTheme.colorScheme.primary)
                Text(" / 30", fontFamily = DisplayFont, fontWeight = FontWeight.Bold, fontSize = 22.sp,
                    modifier = Modifier.padding(bottom = 4.dp))
            }
            Text(t.title, style = MaterialTheme.typography.titleLarge)
            Text(t.focus, style = MaterialTheme.typography.bodyMedium)
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
                modifier = Modifier.padding(vertical = 4.dp),
            ) {
                t.blocks.forEach { BlockChip(it) }
            }
            Text("≈ ${planner.estimatedMinutes(t)} dakika · ${t.blocks.size} blok", style = MaterialTheme.typography.labelLarge)
            Button(onClick = onStart, modifier = Modifier.fillMaxWidth().height(56.dp), shape = RoundedCornerShape(16.dp)) {
                Icon(Icons.Filled.PlayArrow, contentDescription = null)
                Text(" Antrenmanı başlat", fontSize = 17.sp, fontWeight = FontWeight.Bold)
            }
            TextButton(onClick = onDetails, modifier = Modifier.align(Alignment.CenterHorizontally)) {
                Text("Günün detayları ve hareketler")
            }
        }
    }
}

@Composable
private fun RestCard(day: ChallengeDay.Rest, onOpen: () -> Unit) {
    Card(
        shape = RoundedCornerShape(22.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF1E3A5F)),
        onClick = onOpen,
    ) {
        Row(Modifier.fillMaxWidth().padding(18.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("GÜN ${day.number} · DİNLENME", fontFamily = DisplayFont, fontWeight = FontWeight.Bold,
                    letterSpacing = 1.5.sp, color = Color(0xFF9CC9FF))
                Text("Kasların toparlanıyor", style = MaterialTheme.typography.titleLarge, color = Color.White)
                Text("İstersen 8 dakikalık hafif esneme yap, sonra günü tamamla.",
                    style = MaterialTheme.typography.bodyMedium, color = Color(0xFFD7E6F7))
                Spacer(Modifier.height(6.dp))
                Button(onClick = onOpen, shape = RoundedCornerShape(14.dp)) { Text("Dinlenme gününe git") }
            }
            Text("😴", fontSize = 56.sp, modifier = Modifier.padding(start = 8.dp))
        }
    }
}

@Composable
private fun FinishedCard(sport: Sport, onRestart: () -> Unit, onChangeSport: () -> Unit) {
    Card(shape = RoundedCornerShape(22.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
        Column(Modifier.fillMaxWidth().padding(20.dp), horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("🏆", fontSize = 56.sp)
            Text("MEYDAN OKUMA TAMAMLANDI!", fontFamily = DisplayFont, fontWeight = FontWeight.ExtraBold, fontSize = 26.sp,
                textAlign = TextAlign.Center)
            Text("${sport.name} için 30 günü bitirdin. Yeni bir dal dene ya da tekrar ederek tekniğini pekiştir.",
                textAlign = TextAlign.Center, style = MaterialTheme.typography.bodyMedium)
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedButton(onClick = onRestart) { Text("Baştan başla") }
                Button(onClick = onChangeSport) { Text("Yeni dal seç") }
            }
        }
    }
}

@Composable
private fun Legend(icon: String, label: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text(icon, fontSize = 12.sp)
        Text(" $label", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun WeekRow(week: Int, challenge: ChallengeProgress, onTap: (ChallengeDay) -> Unit) {
    val days = ChallengeCalendar.daysOfWeek(week).toList()
    val weekDone = challenge.isWeekDone(week)
    Surface(
        color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f),
        shape = RoundedCornerShape(18.dp),
        modifier = Modifier.padding(horizontal = 16.dp),
    ) {
        Column(Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("HAFTA $week", fontFamily = DisplayFont, fontWeight = FontWeight.Bold, letterSpacing = 1.sp,
                    modifier = Modifier.weight(1f))
                Text("${days.count { challenge.isDone(it) }}/${days.size}", fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Spacer(Modifier.height(8.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                for (slot in 0 until ChallengeCalendar.WEEK) {
                    Box(Modifier.weight(1f), contentAlignment = Alignment.Center) {
                        days.getOrNull(slot)?.let { n -> challenge.day(n)?.let { DayCircle(it, challenge, onTap) } }
                    }
                }
                Box(Modifier.width(30.dp), contentAlignment = Alignment.Center) {
                    // renkli emoji boyanamaz: tamamlanmayan hafta soluk
                    Text("🏆", fontSize = 20.sp, modifier = Modifier.scale(if (weekDone) 1.15f else 0.9f)
                        .alpha(if (weekDone) 1f else 0.25f))
                }
            }
        }
    }
}

@Composable
private fun DayCircle(day: ChallengeDay, challenge: ChallengeProgress, onTap: (ChallengeDay) -> Unit) {
    val n = day.number
    val done = challenge.isDone(n)
    val isCurrent = challenge.current?.number == n
    val unlocked = challenge.isUnlocked(n)
    val accent = MaterialTheme.colorScheme.primary
    val rest = day is ChallengeDay.Rest
    val pulse = if (isCurrent) {
        val t = rememberInfiniteTransition(label = "pulse")
        t.animateFloat(1f, 1.12f, infiniteRepeatable(tween(700), RepeatMode.Reverse), label = "s").value
    } else {
        1f
    }
    val bg = when {
        done -> if (rest) SuccessGreen else accent
        isCurrent -> accent.copy(alpha = 0.16f)
        else -> MaterialTheme.colorScheme.surface
    }
    Box(
        Modifier
            .scale(pulse)
            .size(40.dp)
            .aspectRatio(1f)
            .clip(CircleShape)
            .background(bg)
            .then(if (isCurrent) Modifier.border(2.5.dp, accent, CircleShape) else Modifier)
            .clickable { onTap(day) },
        contentAlignment = Alignment.Center,
    ) {
        when {
            done -> Icon(Icons.Filled.Check, contentDescription = "Gün $n tamamlandı", tint = Color.White,
                modifier = Modifier.size(22.dp))
            rest -> Text("😴", fontSize = 16.sp)
            else -> Text(
                "$n",
                fontFamily = DisplayFont,
                fontWeight = FontWeight.ExtraBold,
                fontSize = 17.sp,
                color = when {
                    isCurrent -> accent
                    unlocked -> MaterialTheme.colorScheme.onSurface
                    else -> MaterialTheme.colorScheme.outline
                },
            )
        }
    }
}
