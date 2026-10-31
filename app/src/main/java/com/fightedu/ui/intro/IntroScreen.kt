package com.fightedu.ui.intro

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
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
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fightedu.ui.components.BrandBackground
import com.fightedu.ui.components.Emblem
import com.fightedu.ui.components.HeroImage
import com.fightedu.ui.components.Scrim
import com.fightedu.ui.components.Wordmark
import com.fightedu.ui.theme.DisplayFont
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

private val INTRO_SPORTS = listOf("boxing", "kickboxing", "wrestling", "taekwondo", "general")

/**
 * Açılış: sistem açılış ekranındaki amblem büyüyüp yerine oturur, altında yazı ve dalların kahraman görselleri
 * belirir; ~1.6 sn sonra [onFinished].
 */
@Composable
fun IntroScreen(onFinished: () -> Unit) {
    val emblemScale = remember { Animatable(0.72f) }
    val textAlpha = remember { Animatable(0f) }
    val heroAlpha = remember { Animatable(0f) }
    LaunchedEffect(Unit) {
        launch { emblemScale.animateTo(1f, tween(650, easing = FastOutSlowInEasing)) }
        launch { heroAlpha.animateTo(0.55f, tween(900, delayMillis = 200)) }
        textAlpha.animateTo(1f, tween(500, delayMillis = 300))
        delay(800)
        onFinished()
    }
    BrandBackground {
        // alt kısımda dalların görselleri yan yana, hafifçe
        Row(
            Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .height(260.dp)
                .alpha(heroAlpha.value),
        ) {
            INTRO_SPORTS.forEach { HeroImage(it, Modifier.weight(1f).fillMaxSize()) }
        }
        Box(
            Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .height(260.dp)
                .alpha(heroAlpha.value),
        ) {
            Scrim(from = 0f, color = Color(0xFF0E1116), strength = 1f)
        }
        Column(
            Modifier.fillMaxSize().padding(bottom = 120.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Emblem(Modifier.size(176.dp).scale(emblemScale.value))
            Spacer(Modifier.height(20.dp))
            Wordmark(52.sp, Modifier.alpha(textAlpha.value))
            Text(
                "30 GÜNDE DÖVÜŞ SPORU",
                fontFamily = DisplayFont,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                letterSpacing = 4.sp,
                color = Color(0xFFC9CCD3),
                modifier = Modifier.alpha(textAlpha.value),
            )
        }
        Text(
            "Boks · Kick Boks · Güreş · Tekvando · Kondisyon",
            color = Color(0xFF8A909C),
            fontSize = 12.sp,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .navigationBarsPadding()
                .padding(bottom = 20.dp)
                .alpha(textAlpha.value),
        )
    }
}
