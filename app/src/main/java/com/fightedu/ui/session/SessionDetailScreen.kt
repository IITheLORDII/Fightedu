package com.fightedu.ui.session

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.fightedu.core.content.ContentLibrary
import com.fightedu.core.domain.TrainingPlanner
import com.fightedu.core.model.Block
import com.fightedu.core.model.Move
import com.fightedu.core.model.TrainingDay
import com.fightedu.core.model.TrainingPhase
import com.fightedu.ui.components.AppScaffold
import com.fightedu.ui.components.KindBadge
import com.fightedu.ui.components.MoveAnimation
import com.fightedu.ui.components.Pill
import com.fightedu.ui.components.blockColor
import com.fightedu.ui.theme.SuccessGreen

/** Bir antrenman günü: koçun notu ve blokların zaman çizelgesi; buradan oynatıcı başlatılır. */
@Composable
fun SessionDetailScreen(
    day: TrainingDay,
    phase: TrainingPhase?,
    content: ContentLibrary,
    planner: TrainingPlanner,
    completed: Boolean,
    onBack: () -> Unit,
    onStart: () -> Unit,
    onToggleCompleted: (Boolean) -> Unit,
    onOpenMove: (Move) -> Unit,
) {
    AppScaffold(
        title = "Gün ${day.day}",
        onBack = onBack,
        bottomBar = {
            Row(
                Modifier
                    .fillMaxWidth()
                    .navigationBarsPadding()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                OutlinedButton(onClick = { onToggleCompleted(!completed) }, modifier = Modifier.weight(1f).height(52.dp)) {
                    Text(if (completed) "Tamamlandı ✓" else "Yapıldı işaretle")
                }
                Button(onClick = onStart, modifier = Modifier.weight(1.4f).height(52.dp)) {
                    Icon(Icons.Filled.PlayArrow, contentDescription = null)
                    Text(" Başlat", style = MaterialTheme.typography.titleMedium)
                }
            }
        },
    ) { inner ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(inner),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            item {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(day.title, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Pill("~${planner.estimatedMinutes(day)} dk")
                        phase?.let { Pill(it.title) }
                        if (completed) Pill("Tamamlandı", SuccessGreen)
                    }
                }
            }
            item {
                Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("KOÇUN NOTU", style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
                        Text(day.focus, style = MaterialTheme.typography.bodyLarge)
                    }
                }
            }
            itemsIndexed(day.blocks) { i, block ->
                BlockTimelineItem(i, day.blocks.size, block, content, onOpenMove)
            }
        }
    }
}

@Composable
private fun BlockTimelineItem(index: Int, count: Int, block: Block, content: ContentLibrary, onOpenMove: (Move) -> Unit) {
    val color = blockColor(block.kind)
    Row(Modifier.fillMaxWidth().height(IntrinsicSize.Min)) {
        // zaman çizelgesi: numaralı daire ve bağlantı çizgisi
        Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.width(32.dp).fillMaxHeight()) {
            Box(Modifier.size(28.dp).background(color, CircleShape), contentAlignment = Alignment.Center) {
                Text("${index + 1}", color = MaterialTheme.colorScheme.surface, fontWeight = FontWeight.Bold)
            }
            if (index < count - 1) {
                Box(Modifier.width(2.dp).weight(1f).background(color.copy(alpha = 0.35f)))
            }
        }
        Spacer(Modifier.width(10.dp))
        Card(Modifier.weight(1f).padding(bottom = 6.dp)) {
            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(block.title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    KindBadge(block.kind)
                }
                Text(TrainingPlanner.summary(block), style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
                if (block.cue.isNotBlank()) Text(block.cue, style = MaterialTheme.typography.bodySmall)
                val moves = (block.moves + block.calls).distinct().mapNotNull { content.move(it) }
                LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(moves.size) { k ->
                        val m = moves[k]
                        Column(Modifier.width(96.dp).clickable { onOpenMove(m) }) {
                            MoveAnimation(m, playing = false, corner = 10.dp, modifier = Modifier.width(96.dp).height(77.dp))
                            Text(m.name, style = MaterialTheme.typography.labelSmall, maxLines = 2, overflow = TextOverflow.Ellipsis)
                        }
                    }
                }
                if (block.calls.isNotEmpty()) {
                    Surface(color = color.copy(alpha = 0.10f), shape = RoundedCornerShape(8.dp)) {
                        Text(
                            "Koç komutları: " + block.calls.mapNotNull { content.move(it)?.name }.joinToString(", "),
                            style = MaterialTheme.typography.bodySmall,
                            modifier = Modifier.padding(8.dp),
                        )
                    }
                }
            }
        }
    }
}
