package com.fightedu.ui.onboarding

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.FilterChip
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.fightedu.core.content.ContentLibrary
import com.fightedu.core.domain.PlanConfig
import com.fightedu.core.model.Sport
import com.fightedu.ui.longTr
import com.fightedu.ui.shortTr
import com.fightedu.ui.theme.parseColor
import java.time.DayOfWeek

private val RECOMMENDED_DAYS = mapOf(
    3 to setOf(DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY),
    4 to setOf(DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.THURSDAY, DayOfWeek.FRIDAY),
    5 to setOf(DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY, DayOfWeek.SATURDAY),
)

@Composable
fun OnboardingScreen(
    content: ContentLibrary,
    initialSportId: String? = null,
    onSportPreview: (String?) -> Unit,
    onCreate: (PlanConfig) -> Unit,
) {
    var step by rememberSaveable { mutableIntStateOf(0) }
    var sportId by rememberSaveable { mutableStateOf(initialSportId) }
    var daysMask by rememberSaveable { mutableIntStateOf(PlanConfig.daysToMask(RECOMMENDED_DAYS.getValue(3))) }
    var acceptedSafety by rememberSaveable { mutableStateOf(false) }

    val days = PlanConfig.maskToDays(daysMask)
    val daysValid = days.size in ContentLibrary.MIN_DAYS_PER_WEEK..ContentLibrary.MAX_DAYS_PER_WEEK

    Column(
        modifier = Modifier
            .fillMaxSize()
            .statusBarsPadding()
            .navigationBarsPadding()
            .padding(horizontal = 20.dp),
    ) {
        Spacer(Modifier.padding(top = 12.dp))
        Text("FightEdu", style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.primary)
        Text("24 günde koç eşliğinde temel dövüş eğitimi", style = MaterialTheme.typography.bodyMedium)
        LinearProgressIndicator(
            progress = { (step + 1) / 3f },
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 16.dp),
        )

        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState()),
        ) {
            when (step) {
                0 -> SportStep(content.sports, sportId) {
                    sportId = it
                    onSportPreview(it)
                }
                1 -> DaysStep(days) { daysMask = PlanConfig.daysToMask(it) }
                else -> {
                    val config = PlanConfig(sportId!!, days)
                    StartStep(
                        content = content,
                        config = config,
                        acceptedSafety = acceptedSafety,
                        onAcceptedSafety = { acceptedSafety = it },
                    )
                }
            }
        }

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            if (step > 0) {
                OutlinedButton(onClick = { step-- }, modifier = Modifier.weight(1f)) { Text("Geri") }
            }
            val canContinue = when (step) {
                0 -> sportId != null
                1 -> daysValid
                else -> acceptedSafety
            }
            Button(
                onClick = {
                    if (step < 2) step++ else onCreate(PlanConfig(sportId!!, days))
                },
                enabled = canContinue,
                modifier = Modifier.weight(1f),
            ) {
                Text(if (step < 2) "Devam" else "Antrenmana Başla")
            }
        }
    }
}

@Composable
private fun SportStep(sports: List<Sport>, selected: String?, onSelect: (String) -> Unit) {
    Text("Hangi sporu öğrenmek istiyorsun?", style = MaterialTheme.typography.titleLarge)
    Spacer(Modifier.padding(top = 12.dp))
    sports.forEach { sport ->
        val color = parseColor(sport.colorHex) ?: MaterialTheme.colorScheme.primary
        val isSelected = sport.id == selected
        Card(
            onClick = { onSelect(sport.id) },
            border = if (isSelected) BorderStroke(2.dp, color) else null,
            colors = CardDefaults.cardColors(
                containerColor = if (isSelected) color.copy(alpha = 0.10f) else MaterialTheme.colorScheme.surfaceVariant,
            ),
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 12.dp),
        ) {
            Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(sport.emoji, style = MaterialTheme.typography.headlineMedium)
                Spacer(Modifier.width(16.dp))
                Column {
                    Text(sport.name, style = MaterialTheme.typography.titleMedium, color = color)
                    Text(sport.tagline, style = MaterialTheme.typography.bodyMedium)
                    if (isSelected) {
                        Spacer(Modifier.padding(top = 6.dp))
                        Text(sport.description, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun DaysStep(days: Set<DayOfWeek>, onChange: (Set<DayOfWeek>) -> Unit) {
    Text("Haftada kaç gün antrenman yapacaksın?", style = MaterialTheme.typography.titleLarge)
    Spacer(Modifier.padding(top = 12.dp))
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        RECOMMENDED_DAYS.forEach { (count, preset) ->
            FilterChip(
                selected = days.size == count,
                onClick = { onChange(preset) },
                label = { Text("$count gün") },
            )
        }
    }
    Spacer(Modifier.padding(top = 20.dp))
    Text("Hangi günler?", style = MaterialTheme.typography.titleMedium)
    Text(
        "Önerilen günler seçildi; dilediğin gibi değiştirebilirsin. Antrenmanlar arasında dinlenme günü bırakmak toparlanmayı hızlandırır.",
        style = MaterialTheme.typography.bodySmall,
    )
    Spacer(Modifier.padding(top = 8.dp))
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        DayOfWeek.entries.forEach { day ->
            val selected = day in days
            FilterChip(
                selected = selected,
                onClick = { onChange(if (selected) days - day else days + day) },
                label = { Text(day.shortTr) },
            )
        }
    }
    Spacer(Modifier.padding(top = 8.dp))
    val n = days.size
    val valid = n in ContentLibrary.MIN_DAYS_PER_WEEK..ContentLibrary.MAX_DAYS_PER_WEEK
    Text(
        text = if (valid) {
            "Seçilen: $n gün (${days.sortedBy { it.value }.joinToString { it.longTr }})"
        } else {
            "Lütfen ${ContentLibrary.MIN_DAYS_PER_WEEK} ile ${ContentLibrary.MAX_DAYS_PER_WEEK} arasında gün seç (şu an $n)."
        },
        color = if (valid) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.error,
        style = MaterialTheme.typography.bodyMedium,
    )
    Spacer(Modifier.padding(top = 16.dp))
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
        Column(Modifier.padding(16.dp)) {
            Text("Antrenmanlar sırayla ilerler", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.padding(top = 4.dp))
            Text(
                "Gün 1'den Gün 24'e kadar her antrenmanı koç kurar: ip, gölge, torba/drill raundları, kondisyon ve " +
                    "esneme. Seçtiğin günlerde sana hatırlatma gönderilir; bir günü kaçırırsan kaldığın yerden devam edersin.",
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun StartStep(
    content: ContentLibrary,
    config: PlanConfig,
    acceptedSafety: Boolean,
    onAcceptedSafety: (Boolean) -> Unit,
) {
    val sport = content.sport(config.sportId)
    val program = content.program(config.sportId)
    val total = program?.totalDays ?: ContentLibrary.TOTAL_DAYS
    val weeks = (total + config.daysPerWeek - 1) / config.daysPerWeek

    Text("Hazırsın", style = MaterialTheme.typography.titleLarge)
    Spacer(Modifier.padding(top = 12.dp))
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text("${sport?.emoji.orEmpty()} ${sport?.name.orEmpty()} antrenmanların", style = MaterialTheme.typography.titleMedium)
            Text("• $total günlük antrenman, ${program?.phases?.size ?: 4} evre")
            Text("• Haftada ${config.daysPerWeek} gün ile yaklaşık $weeks hafta")
            Text("• Hatırlatma günleri: ${config.sortedDays.joinToString { it.shortTr }}")
            program?.phases?.forEach { Text("• Gün ${it.from}–${it.to}: ${it.title}") }
        }
    }
    Spacer(Modifier.padding(top = 16.dp))
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(16.dp)) {
            Text("⚠️ Güvenlik ve sağlık uyarısı", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.padding(top = 4.dp))
            Text(
                "Bu uygulama temel eğitim amaçlıdır ve bir antrenörün yerini tutmaz. Kalp, eklem veya başka bir " +
                    "sağlık sorunun varsa başlamadan önce doktoruna danış. Her antrenmana ısınarak başla, ağrı " +
                    "hissedersen dur. Partnerle çalışma, sparring ve atış tekniklerini mutlaka bir antrenör " +
                    "gözetiminde ve uygun koruyucu ekipmanla yap.",
                style = MaterialTheme.typography.bodyMedium,
            )
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onAcceptedSafety(!acceptedSafety) },
            ) {
                Checkbox(checked = acceptedSafety, onCheckedChange = onAcceptedSafety)
                Text("Okudum, anladım.", style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}
