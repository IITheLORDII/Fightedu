package com.fightedu.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.airbnb.lottie.compose.LottieAnimation
import com.airbnb.lottie.compose.LottieCompositionSpec
import com.airbnb.lottie.compose.LottieConstants
import com.airbnb.lottie.compose.rememberLottieComposition
import com.fightedu.core.model.Move
import com.fightedu.ui.theme.AnimationStage

/**
 * Hareketin Lottie animasyonu (assets/lottie/<id>.json).
 * [playing] false ise animasyon [staticProgress] karesinde sabit gösterilir (liste küçük resimleri).
 */
@Composable
fun MoveAnimation(
    move: Move,
    modifier: Modifier = Modifier,
    playing: Boolean = true,
    speed: Float = 1f,
    staticProgress: Float = 0.3f,
    corner: Dp = 16.dp,
) {
    val result = rememberLottieComposition(LottieCompositionSpec.Asset(move.lottieAsset))
    val composition by result
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(corner))
            .background(AnimationStage),
        contentAlignment = Alignment.Center,
    ) {
        when {
            composition == null && result.isFailure -> Text("🥋", style = MaterialTheme.typography.headlineMedium)
            playing -> LottieAnimation(
                composition = composition,
                iterations = LottieConstants.IterateForever,
                isPlaying = true,
                speed = speed,
                modifier = Modifier.fillMaxSize(),
            )
            else -> LottieAnimation(
                composition = composition,
                progress = { staticProgress },
                modifier = Modifier.fillMaxSize(),
            )
        }
    }
}
