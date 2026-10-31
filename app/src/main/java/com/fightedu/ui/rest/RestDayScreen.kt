package com.fightedu.ui.rest

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fightedu.core.domain.TrainingPlanner
import com.fightedu.core.model.TrainingDay
import com.fightedu.ui.components.AppScaffold
import com.fightedu.ui.components.BlockChip
import com.fightedu.ui.components.BulletList
import com.fightedu.ui.theme.DisplayFont

private val TIPS = listOf(
    "Bol su iç; idrar rengin açık olsun.",
    "7-9 saat uyu: kaslar en çok uykuda onarılır.",
    "Hafif yürüyüş ya da esneme kan dolaşımını hızlandırır, ağrıyı azaltır.",
    "Proteinli beslen (yumurta, yoğurt, baklagil, et).",
    "Ağrıyan bir yer varsa bugün onu zorlama; keskin ağrı sürerse dinlenmeyi uzat.",
)

/** Meydan okumanın dinlenme günü: kısa aktif dinlenme seansı (isteğe bağlı) ve günü tamamlama. */
@Composable
fun RestDayScreen(
    number: Int,
    restDay: TrainingDay?,
    planner: TrainingPlanner,
    done: Boolean,
    onBack: () -> Unit,
    onStartStretch: () -> Unit,
    onComplete: (Boolean) -> Unit,
) {
    AppScaffold(
        title = "Gün $number · Dinlenme",
        onBack = onBack,
        bottomBar = {
            Row(
                Modifier.fillMaxWidth().navigationBarsPadding().padding(16.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                if (restDay != null) {
                    OutlinedButton(onClick = onStartStretch, modifier = Modifier.weight(1f).height(54.dp)) {
                        Icon(Icons.Filled.PlayArrow, contentDescription = null)
                        Text(" ${planner.estimatedMinutes(restDay)} dk esneme")
                    }
                }
                Button(onClick = { onComplete(!done) }, modifier = Modifier.weight(1.2f).height(54.dp)) {
                    Text(if (done) "Tamamlandı ✓" else "Dinlendim, günü tamamla", fontWeight = FontWeight.Bold)
                }
            }
        },
    ) { inner ->
        Column(
            Modifier.fillMaxSize().padding(inner).verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text("😴", fontSize = 72.sp)
            Text("DİNLENME GÜNÜ", fontFamily = DisplayFont, fontWeight = FontWeight.ExtraBold, fontSize = 32.sp)
            Text(
                "Güç antrenman sırasında değil, dinlenirken gelişir. Bugün ağır antrenman yok; " +
                    "istersen kısa bir esneme seansı yap ve günü tamamla. Serin devam eder.",
                textAlign = TextAlign.Center,
                style = MaterialTheme.typography.bodyLarge,
            )
            if (restDay != null) {
                Card(shape = RoundedCornerShape(18.dp), modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(restDay.title, style = MaterialTheme.typography.titleLarge)
                        Text(restDay.focus, style = MaterialTheme.typography.bodyMedium)
                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) { restDay.blocks.forEach { BlockChip(it) } }
                    }
                }
            }
            Card(shape = RoundedCornerShape(18.dp), modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Toparlanma ipuçları", style = MaterialTheme.typography.titleLarge)
                    BulletList(TIPS)
                }
            }
        }
    }
}
