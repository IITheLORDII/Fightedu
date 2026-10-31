package com.fightedu.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.fightedu.R

val DefaultAccent = Color(0xFFD32F2F)

/** Marka renkleri (amblem, açılış ve giriş ekranları). */
val BrandDark = Color(0xFF0E1116)
val BrandSurface = Color(0xFF181B22)
val BrandRed = Color(0xFFFF5A3C)
val BrandRedDeep = Color(0xFFB0121C)

/** Başlıklar için dar ve kalın spor yazı tipi (Barlow Condensed, OFL). */
val DisplayFont = FontFamily(
    Font(R.font.barlow_condensed_semibold, FontWeight.SemiBold),
    Font(R.font.barlow_condensed_bold, FontWeight.Bold),
    Font(R.font.barlow_condensed_extrabold, FontWeight.ExtraBold),
)

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
        displayLarge = t.displayLarge.copy(fontFamily = DisplayFont, fontWeight = FontWeight.ExtraBold),
        displayMedium = t.displayMedium.copy(fontFamily = DisplayFont, fontWeight = FontWeight.ExtraBold),
        displaySmall = t.displaySmall.copy(fontFamily = DisplayFont, fontWeight = FontWeight.ExtraBold),
        headlineLarge = t.headlineLarge.copy(fontFamily = DisplayFont, fontWeight = FontWeight.ExtraBold),
        headlineMedium = t.headlineMedium.copy(fontFamily = DisplayFont, fontWeight = FontWeight.Bold, fontSize = 30.sp),
        headlineSmall = t.headlineSmall.copy(fontFamily = DisplayFont, fontWeight = FontWeight.Bold, fontSize = 26.sp),
        titleLarge = t.titleLarge.copy(fontFamily = DisplayFont, fontWeight = FontWeight.Bold, fontSize = 24.sp),
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

/** Açılış, hoş geldin, kayıt/giriş ve dal seçimi: her zaman koyu marka teması. */
@Composable
fun BrandTheme(content: @Composable () -> Unit) {
    val scheme = darkColorScheme(
        primary = BrandRed,
        onPrimary = Color.White,
        primaryContainer = BrandRedDeep,
        onPrimaryContainer = Color.White,
        secondary = BrandRed,
        background = BrandDark,
        onBackground = Color(0xFFF2F3F5),
        surface = BrandSurface,
        onSurface = Color(0xFFF2F3F5),
        surfaceVariant = Color(0xFF242832),
        onSurfaceVariant = Color(0xFFB8BCC6),
        outline = Color(0xFF4A505C),
        error = Color(0xFFFF6B6B),
    )
    MaterialTheme(colorScheme = scheme, typography = AppTypography, content = content)
}
