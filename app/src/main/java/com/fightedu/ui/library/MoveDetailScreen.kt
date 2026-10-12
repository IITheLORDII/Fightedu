package com.fightedu.ui.library

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.fightedu.core.domain.formatDuration
import com.fightedu.core.model.Move
import com.fightedu.ui.components.AppScaffold
import com.fightedu.ui.components.BulletList
import com.fightedu.ui.components.LevelPill
import com.fightedu.ui.components.MoveAnimation
import com.fightedu.ui.components.Pill
import com.fightedu.ui.components.SectionTitle

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun MoveDetailScreen(move: Move, onBack: () -> Unit) {
    var slowMotion by rememberSaveable { mutableStateOf(false) }

    AppScaffold(title = move.name, onBack = onBack) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
        ) {
            MoveAnimation(
                move = move,
                speed = if (slowMotion) 0.4f else 1f,
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(1.25f),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
                FilterChip(selected = !slowMotion, onClick = { slowMotion = false }, label = { Text("Normal hız") })
                FilterChip(selected = slowMotion, onClick = { slowMotion = true }, label = { Text("🐢 Yavaş çekim") })
            }
            Spacer(Modifier.padding(top = 8.dp))
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Pill(move.category.label)
                LevelPill(move.level, move.levelLabel)
                val dose = move.reps?.let { "$it tekrar" } ?: move.sec?.let { formatDuration(it) }
                if (dose != null) Pill("Öneri: $dose", MaterialTheme.colorScheme.secondary)
            }
            Spacer(Modifier.padding(top = 12.dp))
            Text(move.description, style = MaterialTheme.typography.bodyLarge)

            SectionTitle("Nasıl yapılır?")
            BulletList(move.steps, numbered = true)

            if (move.mistakes.isNotEmpty()) {
                SectionTitle("Sık yapılan hatalar")
                BulletList(move.mistakes, bulletColor = MaterialTheme.colorScheme.error)
            }

            if (move.tip.isNotBlank()) {
                Spacer(Modifier.padding(top = 16.dp))
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("💡 İpucu: ${move.tip}", modifier = Modifier.padding(16.dp), style = MaterialTheme.typography.bodyMedium)
                }
            }
            Spacer(Modifier.padding(bottom = 24.dp))
        }
    }
}
