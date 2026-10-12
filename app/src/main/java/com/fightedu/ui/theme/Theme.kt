package com.fightedu.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.text.font.FontWeight

val DefaultAccent = Color(0xFFD32F2F)

/** Lottie figürleri koyu renkli çizildiği için animasyon sahnesi her temada açık renktir. */
val AnimationStage = Color(0xFFF1F4F6)
val SuccessGreen = Color(0xFF2E7D32)

fun parseColor(hex: String?): Color? = try {
    hex?.let { Color(android.graphics.Color.parseColor(it)) }
} catch (_: IllegalArgumentException) {
    null
}

private val AppTypography = Typography().let { t ->
    t.copy(
        headlineMedium = t.headlineMedium.copy(fontWeight = FontWeight.Bold),
        titleLarge = t.titleLarge.copy(fontWeight = FontWeight.Bold),
        titleMedium = t.titleMedium.copy(fontWeight = FontWeight.SemiBold),
    )
}

/** Uygulama teması; ana renk seçilen sporun rengidir. */
@Composable
fun FightEduTheme(
    accent: Color = DefaultAccent,
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val scheme = if (darkTheme) {
        val light = lerp(accent, Color.White, 0.35f)
        darkColorScheme(
            primary = light,
            onPrimary = Color.Black,
            primaryContainer = lerp(accent, Color.Black, 0.45f),
            onPrimaryContainer = Color.White,
            secondary = light,
        )
    } else {
        lightColorScheme(
            primary = accent,
            onPrimary = Color.White,
            primaryContainer = lerp(accent, Color.White, 0.85f),
            onPrimaryContainer = lerp(accent, Color.Black, 0.55f),
            secondary = lerp(accent, Color.DarkGray, 0.4f),
            background = Color(0xFFFAFAFA),
            surface = Color(0xFFFAFAFA),
        )
    }
    MaterialTheme(colorScheme = scheme, typography = AppTypography, content = content)
}
