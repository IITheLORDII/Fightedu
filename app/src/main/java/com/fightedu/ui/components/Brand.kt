package com.fightedu.ui.components

import android.content.Context
import android.graphics.BitmapFactory
import android.util.LruCache
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.BiasAlignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.sp
import com.fightedu.R
import com.fightedu.ui.theme.BrandRed
import com.fightedu.ui.theme.DisplayFont
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** FightEdu amblemi (kalkan + yüksek tekme silueti). */
@Composable
fun Emblem(modifier: Modifier = Modifier) {
    Image(painterResource(R.drawable.ic_emblem), contentDescription = "FightEdu", modifier = modifier)
}

/** "FIGHT" beyaz + "EDU" kırmızı yazı. */
@Composable
fun Wordmark(size: TextUnit = 44.sp, modifier: Modifier = Modifier, color: Color = Color.White) {
    Text(
        buildAnnotatedString {
            withStyle(SpanStyle(color = color)) { append("FIGHT") }
            withStyle(SpanStyle(color = BrandRed)) { append("EDU") }
        },
        fontFamily = DisplayFont,
        fontWeight = FontWeight.ExtraBold,
        fontSize = size,
        letterSpacing = (size.value * 0.09f).sp,
        modifier = modifier,
    )
}

/** Kahraman görsellerinde sporcunun dikey odak noktası (0 = üst, 1 = alt); kırpmada sporcu kadrajda kalsın. */
private val HERO_FOCUS = mapOf(
    "boxing" to 0.35f,
    "kickboxing" to 0.25f,
    "wrestling" to 0.55f,
    "taekwondo" to 0.28f,
    "general" to 0.72f,
)

/** Dalın görseli için kırpma hizası (yatayda orta, dikeyde sporcunun odak noktası). */
fun heroAlignment(sportId: String): Alignment = BiasAlignment(0f, (HERO_FOCUS[sportId] ?: 0.4f) * 2f - 1f)

/** Dalın koyu fonlu kahraman görseli (assets/hero/<dal>.webp); yüklenene kadar boş. */
@Composable
fun HeroImage(
    sportId: String,
    modifier: Modifier = Modifier,
    alignment: Alignment = heroAlignment(sportId),
    contentScale: ContentScale = ContentScale.Crop,
) {
    val context = LocalContext.current
    val asset = "hero/$sportId.webp"
    var bitmap by remember(asset) { mutableStateOf(HeroImages.cached(asset)) }
    LaunchedEffect(asset) {
        if (bitmap == null) bitmap = withContext(Dispatchers.IO) { HeroImages.load(context, asset) }
    }
    bitmap?.let {
        Image(it, contentDescription = null, contentScale = contentScale, alignment = alignment, modifier = modifier)
    }
}

/** Görselin üstüne alttan koyulaşan geçiş (yazı okunabilsin): [from]'da saydam, [full]'dan itibaren tam renk. */
@Composable
fun BoxScope.Scrim(from: Float = 0.35f, color: Color = Color.Black, strength: Float = 0.92f, full: Float = 1f) {
    Box(
        Modifier
            .matchParentSize()
            .background(
                Brush.verticalGradient(
                    from to Color.Transparent,
                    full to color.copy(alpha = strength),
                    1f to color.copy(alpha = strength),
                ),
            ),
    )
}

/** Tam ekran koyu marka arka planı: hafif kırmızı ışıma. */
@Composable
fun BrandBackground(modifier: Modifier = Modifier, content: @Composable BoxScope.() -> Unit) {
    Box(
        modifier
            .fillMaxSize()
            .background(Color(0xFF0E1116))
            .background(
                Brush.radialGradient(
                    0f to Color(0x55B0121C),
                    1f to Color.Transparent,
                    radius = 1400f,
                ),
            ),
        content = content,
    )
}

private object HeroImages {
    private val cache = LruCache<String, ImageBitmap>(6)

    fun cached(asset: String): ImageBitmap? = cache.get(asset)

    fun load(context: Context, asset: String): ImageBitmap? {
        cache.get(asset)?.let { return it }
        val bitmap = runCatching { context.assets.open(asset).use { BitmapFactory.decodeStream(it) } }.getOrNull()
            ?: return null
        return bitmap.asImageBitmap().also { cache.put(asset, it) }
    }
}
