package com.fightedu.ui.sports

import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fightedu.core.content.ContentLibrary
import com.fightedu.core.domain.ChallengeCalendar
import com.fightedu.core.domain.TrainingPlanner
import com.fightedu.core.model.Sport
import com.fightedu.data.ReminderSettings
import com.fightedu.data.TrainingRepository
import com.fightedu.reminders.ReminderNotifications
import com.fightedu.ui.components.BrandBackground
import com.fightedu.ui.components.HeroImage
import com.fightedu.ui.components.Scrim
import com.fightedu.ui.theme.DisplayFont
import com.fightedu.ui.theme.parseColor

private val REMINDER_HOURS = listOf(7, 9, 12, 17, 18, 19, 20)

/** "Hangi dalda çalışmak istiyorsun?" — her dal büyük görselli bir kart; varsa ilerlemesi. */
@Composable
fun SportSelectScreen(
    userName: String?,
    sports: List<Sport>,
    progress: Map<String, Int>,
    currentSportId: String?,
    onBack: (() -> Unit)?,
    onSelect: (Sport) -> Unit,
) {
    BrandBackground {
        LazyColumn(
            Modifier.fillMaxSize(),
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, bottom = 24.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            item {
                Column(Modifier.statusBarsPadding().padding(top = 8.dp, bottom = 4.dp)) {
                    if (onBack != null) {
                        IconButton(onClick = onBack) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Geri", tint = Color.White)
                        }
                    } else {
                        Spacer(Modifier.height(16.dp))
                    }
                    Text(
                        if (userName != null) "Merhaba $userName 👋" else "Merhaba 👋",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Text(
                        "Hangi dalda çalışmak istiyorsun?",
                        style = MaterialTheme.typography.headlineLarge,
                        color = Color.White,
                    )
                    Text(
                        "Her dal 30 günlük bir meydan okuma: 24 antrenman + 6 dinlenme günü. Dalını istediğin zaman " +
                            "değiştirebilirsin; her dalın ilerlemesi ayrı saklanır.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(top = 6.dp),
                    )
                }
            }
            items(sports, key = { it.id }) { sport ->
                SportCard(sport, progress[sport.id] ?: 0, sport.id == currentSportId) { onSelect(sport) }
            }
        }
    }
}

@Composable
private fun SportCard(sport: Sport, done: Int, current: Boolean, onClick: () -> Unit) {
    val color = parseColor(sport.colorHex) ?: MaterialTheme.colorScheme.primary
    Box(
        Modifier
            .fillMaxWidth()
            .aspectRatio(1.9f)
            .clip(RoundedCornerShape(22.dp))
            .background(Color(0xFF181B22))
            .then(if (current) Modifier.border(2.dp, color, RoundedCornerShape(22.dp)) else Modifier)
            .clickable(onClick = onClick),
    ) {
        HeroImage(sport.id, Modifier.fillMaxSize())
        // soldan koyulaşan geçiş: yazı solda okunur
        Box(
            Modifier
                .matchParentSize()
                .background(
                    androidx.compose.ui.graphics.Brush.horizontalGradient(
                        0f to Color(0xF20E1116),
                        0.55f to Color(0x990E1116),
                        1f to Color.Transparent,
                    ),
                ),
        )
        Column(
            Modifier
                .align(Alignment.CenterStart)
                .fillMaxWidth(0.62f)
                .padding(18.dp),
        ) {
            Surface(color = color, shape = RoundedCornerShape(8.dp)) {
                Text(
                    "30 GÜN",
                    fontFamily = DisplayFont,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    letterSpacing = 1.sp,
                    color = Color.White,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                )
            }
            Spacer(Modifier.height(8.dp))
            Text(
                "${sport.emoji} ${sport.name.uppercase()}",
                fontFamily = DisplayFont,
                fontWeight = FontWeight.ExtraBold,
                fontSize = 28.sp,
                color = Color.White,
                lineHeight = 30.sp,
            )
            Text(sport.tagline, color = Color(0xFFC9CCD3), fontSize = 13.sp, lineHeight = 17.sp, maxLines = 2)
            Spacer(Modifier.height(10.dp))
            if (done > 0) {
                LinearProgressIndicator(
                    progress = { done.toFloat() / ChallengeCalendar.LENGTH },
                    color = color,
                    trackColor = Color.White.copy(alpha = 0.2f),
                    modifier = Modifier.fillMaxWidth().height(5.dp).clip(CircleShape),
                )
                Text(
                    if (done >= ChallengeCalendar.LENGTH) "🏆 Tamamlandı" else "$done / ${ChallengeCalendar.LENGTH} gün",
                    color = Color.White,
                    fontSize = 12.sp,
                    modifier = Modifier.padding(top = 4.dp),
                )
            } else {
                Text("Başlangıç seviyesi", color = Color(0xFF8A909C), fontSize = 12.sp)
            }
        }
    }
}

/** Dal onayı: açıklama, evreler, hatırlatıcı ve güvenlik onayı -> meydan okumayı başlat. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SportConfirmScreen(
    sport: Sport,
    content: ContentLibrary,
    planner: TrainingPlanner,
    progressDone: Int,
    reminder: ReminderSettings?,
    onBack: () -> Unit,
    onStart: (ReminderSettings) -> Unit,
) {
    val context = LocalContext.current
    val color = parseColor(sport.colorHex) ?: MaterialTheme.colorScheme.primary
    val program = content.program(sport.id)
    val minutes = program?.days?.map { planner.estimatedMinutes(it) }.orEmpty()
    var remind by rememberSaveable { mutableStateOf(reminder?.enabled ?: true) }
    var hour by rememberSaveable { mutableIntStateOf(reminder?.hour ?: TrainingRepository.DEFAULT_REMINDER_HOUR) }
    var accepted by rememberSaveable { mutableStateOf(false) }
    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (!granted) remind = false
    }

    BrandBackground {
        Column(
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState()),
        ) {
            Box(Modifier.fillMaxWidth().height(340.dp)) {
                HeroImage(sport.id, Modifier.fillMaxSize())
                Scrim(from = 0.35f, color = Color(0xFF0E1116), strength = 1f)
                IconButton(onClick = onBack, modifier = Modifier.statusBarsPadding().padding(8.dp)) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Geri", tint = Color.White)
                }
                Column(Modifier.align(Alignment.BottomStart).padding(horizontal = 20.dp)) {
                    Text("30 GÜNLÜK MEYDAN OKUMA", fontFamily = DisplayFont, fontWeight = FontWeight.Bold,
                        color = color, letterSpacing = 2.sp)
                    Text("${sport.emoji} ${sport.name}", style = MaterialTheme.typography.displaySmall, color = Color.White)
                }
            }
            Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    Fact("24", "antrenman", Modifier.weight(1f))
                    Fact("6", "dinlenme", Modifier.weight(1f))
                    Fact(if (minutes.isEmpty()) "-" else "${minutes.min()}–${minutes.max()}", "dk / gün", Modifier.weight(1f))
                }
                Text(sport.description, style = MaterialTheme.typography.bodyMedium, color = Color(0xFFD5D8DE))
                program?.phases?.let { phases ->
                    Text("Yol haritası", style = MaterialTheme.typography.titleLarge, color = Color.White)
                    phases.forEachIndexed { i, ph ->
                        Row(verticalAlignment = Alignment.Top) {
                            Box(
                                Modifier.size(30.dp).clip(CircleShape).background(color.copy(alpha = 0.18f)),
                                contentAlignment = Alignment.Center,
                            ) { Text("${i + 1}", color = color, fontWeight = FontWeight.Bold) }
                            Spacer(Modifier.width(12.dp))
                            Column {
                                val from = ChallengeCalendar.challengeDayOf(ph.from)
                                val to = if (i == phases.lastIndex) ChallengeCalendar.LENGTH else ChallengeCalendar.challengeDayOf(phases[i + 1].from) - 1
                                Text("${ph.title} · Gün $from–$to", color = Color.White, fontWeight = FontWeight.SemiBold)
                                Text(ph.goal, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }
                    }
                }
                Surface(color = Color(0xFF181B22), shape = RoundedCornerShape(16.dp)) {
                    Column(Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text("Günlük hatırlatıcı", color = Color.White, fontWeight = FontWeight.SemiBold)
                                Text("O gün çalışmadıysan sıradaki günü hatırlatır.", style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            Switch(checked = remind, onCheckedChange = { on ->
                                remind = on
                                if (on && Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                                    !ReminderNotifications.canNotify(context)
                                ) {
                                    permission.launch(Manifest.permission.POST_NOTIFICATIONS)
                                }
                            })
                        }
                        if (remind) {
                            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
                                REMINDER_HOURS.forEach { h ->
                                    FilterChip(selected = hour == h, onClick = { hour = h }, label = { Text("%02d:00".format(h)) })
                                }
                            }
                        }
                    }
                }
                Surface(color = Color(0x26FF6B6B), shape = RoundedCornerShape(16.dp)) {
                    Row(Modifier.clickable { accepted = !accepted }.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked = accepted, onCheckedChange = { accepted = it })
                        Text(
                            "Isınmadan başlamayacağım; keskin ağrıda duracağım. Sağlık sorunum varsa önce doktoruma danışacağım.",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFFF2F3F5),
                        )
                    }
                }
                Button(
                    onClick = {
                        if (remind && Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                            !ReminderNotifications.canNotify(context)
                        ) {
                            remind = false
                        }
                        onStart(ReminderSettings(remind, hour))
                    },
                    enabled = accepted,
                    modifier = Modifier.fillMaxWidth().height(58.dp),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Text(
                        if (progressDone > 0) "Kaldığın yerden devam et (Gün ${minOf(progressDone + 1, 30)})" else "Meydan okumaya başla",
                        fontSize = 17.sp,
                        fontWeight = FontWeight.Bold,
                    )
                }
                Spacer(Modifier.navigationBarsPadding().height(16.dp))
            }
        }
    }
}

@Composable
private fun Fact(value: String, label: String, modifier: Modifier = Modifier) {
    Surface(color = Color(0xFF181B22), shape = RoundedCornerShape(14.dp), modifier = modifier) {
        Column(Modifier.padding(vertical = 12.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Text(value, fontFamily = DisplayFont, fontWeight = FontWeight.ExtraBold, fontSize = 26.sp, color = Color.White)
            Text(label, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}
