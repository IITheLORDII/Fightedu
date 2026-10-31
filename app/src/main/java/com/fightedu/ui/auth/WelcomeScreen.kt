package com.fightedu.ui.auth

import androidx.compose.animation.Crossfade
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fightedu.core.model.Sport
import com.fightedu.ui.components.BrandBackground
import com.fightedu.ui.components.Emblem
import com.fightedu.ui.components.HeroImage
import com.fightedu.ui.components.Scrim
import com.fightedu.ui.components.Wordmark
import com.fightedu.ui.theme.BrandDark
import com.fightedu.ui.theme.DisplayFont
import com.fightedu.ui.theme.parseColor
import kotlinx.coroutines.delay

/** Hoş geldin: dalların görselleri sırayla akar; hesap oluştur / giriş yap / misafir. */
@Composable
fun WelcomeScreen(
    sports: List<Sport>,
    onRegister: () -> Unit,
    onLogin: () -> Unit,
    onGuest: () -> Unit,
) {
    var index by rememberSaveable { mutableIntStateOf(0) }
    LaunchedEffect(sports.size) {
        while (sports.isNotEmpty()) {
            delay(3200)
            index = (index + 1) % sports.size
        }
    }
    val sport = sports.getOrNull(index)
    BrandBackground {
        Crossfade(targetState = sport?.id, animationSpec = tween(900), label = "hero") { id ->
            Box(Modifier.fillMaxSize()) {
                if (id != null) HeroImage(id, Modifier.fillMaxSize())
                Scrim(from = 0.25f, color = BrandDark, strength = 1f)
            }
        }
        Column(
            Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .navigationBarsPadding()
                .padding(horizontal = 24.dp, vertical = 20.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            if (sport != null) {
                Surface(
                    color = (parseColor(sport.colorHex) ?: MaterialTheme.colorScheme.primary).copy(alpha = 0.9f),
                    shape = RoundedCornerShape(50),
                ) {
                    Text(
                        "${sport.emoji}  ${sport.name.uppercase()}",
                        fontFamily = DisplayFont,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.5.sp,
                        color = Color.White,
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 5.dp),
                    )
                }
                Spacer(Modifier.height(10.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    sports.indices.forEach { i ->
                        Surface(
                            color = if (i == index) Color.White else Color.White.copy(alpha = 0.3f),
                            shape = CircleShape,
                            modifier = Modifier.size(if (i == index) 8.dp else 6.dp),
                        ) {}
                    }
                }
            }
            Spacer(Modifier.height(24.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Emblem(Modifier.size(64.dp))
                Spacer(Modifier.width(12.dp))
                Column {
                    Wordmark(36.sp)
                    Text("30 GÜNDE DÖVÜŞ SPORU", fontFamily = DisplayFont, fontWeight = FontWeight.Bold,
                        letterSpacing = 3.sp, color = Color(0xFFC9CCD3), fontSize = 14.sp)
                }
            }
            Spacer(Modifier.height(14.dp))
            Text(
                "Boks, kick boks, güreş, tekvando ya da kondisyon: dalını seç, sesli koç eşliğinde 30 günlük " +
                    "meydan okumayı adım adım tamamla.",
                style = MaterialTheme.typography.bodyMedium,
                color = Color(0xFFB8BCC6),
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(24.dp))
            Button(
                onClick = onRegister,
                modifier = Modifier.fillMaxWidth().height(56.dp),
                shape = RoundedCornerShape(16.dp),
            ) {
                Text("Hesap oluştur", fontSize = 17.sp, fontWeight = FontWeight.Bold)
            }
            Spacer(Modifier.height(12.dp))
            OutlinedButton(
                onClick = onLogin,
                modifier = Modifier.fillMaxWidth().height(56.dp),
                shape = RoundedCornerShape(16.dp),
                border = BorderStroke(1.5.dp, Color.White.copy(alpha = 0.7f)),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White),
            ) {
                Text("Giriş yap", fontSize = 17.sp, fontWeight = FontWeight.Bold)
            }
            TextButton(onClick = onGuest, modifier = Modifier.padding(top = 4.dp)) {
                Text("Misafir olarak devam et", color = Color(0xFFB8BCC6))
            }
        }
    }
}
