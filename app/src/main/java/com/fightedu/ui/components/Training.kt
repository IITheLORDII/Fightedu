package com.fightedu.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.fightedu.core.domain.TrainingPlanner
import com.fightedu.core.model.Block
import com.fightedu.core.model.BlockKind
import com.fightedu.core.model.BlockMode

/** Blok türünün rengi (spor renginden bağımsız, her temada okunur). */
fun blockColor(kind: BlockKind): Color = when (kind) {
    BlockKind.WARMUP -> Color(0xFFF2A900)
    BlockKind.TECHNIQUE -> Color(0xFF3D7BD9)
    BlockKind.SHADOW -> Color(0xFF7A5AF8)
    BlockKind.BAG -> Color(0xFFD9412B)
    BlockKind.DRILL -> Color(0xFFD9412B)
    BlockKind.FORM -> Color(0xFF0F9D8A)
    BlockKind.CONDITIONING -> Color(0xFF2E9E4F)
    BlockKind.COOLDOWN -> Color(0xFF5E8CA6)
}

/** Blok türü rozeti: renkli nokta + etiket. */
@Composable
fun KindBadge(kind: BlockKind, modifier: Modifier = Modifier, label: String = kind.label) {
    val c = blockColor(kind)
    Surface(color = c.copy(alpha = 0.14f), contentColor = c, shape = RoundedCornerShape(50), modifier = modifier) {
        Row(
            Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Box(Modifier.size(8.dp).background(c, CircleShape))
            Text(label.uppercase(), style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
        }
    }
}

/** Antrenman özeti çipi: "6 × 2 dk torba" gibi. */
@Composable
fun BlockChip(block: Block, modifier: Modifier = Modifier) {
    val c = blockColor(block.kind)
    Surface(
        color = MaterialTheme.colorScheme.surface,
        contentColor = MaterialTheme.colorScheme.onSurface,
        shape = RoundedCornerShape(10.dp),
        modifier = modifier,
    ) {
        Row(Modifier.padding(horizontal = 10.dp, vertical = 6.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(width = 4.dp, height = 18.dp).background(c, RoundedCornerShape(2.dp)))
            Text(
                "  ${block.title} · ${shortSummary(block)}",
                style = MaterialTheme.typography.labelLarge,
            )
        }
    }
}

fun shortSummary(block: Block): String = TrainingPlanner.summary(block).substringBefore(" · ")

/** Bloğun yaklaşık süresi (sn); şeritlerde oran için. */
fun blockSeconds(b: Block): Int = when (b.mode) {
    BlockMode.ROUND -> b.rounds * b.work + (b.rounds - 1) * b.rest
    BlockMode.CIRCUIT -> b.rounds * b.moves.size * (b.work + b.rest) - b.rest
    BlockMode.REPS -> b.rounds * b.moves.size * ((b.reps ?: 0) * TrainingPlanner.SECONDS_PER_REP + b.rest) - b.rest
}
