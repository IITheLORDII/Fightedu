package com.fightedu.ui.components

import android.content.Context
import android.graphics.BitmapFactory
import android.util.LruCache
import android.view.TextureView
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import com.fightedu.core.model.Move
import com.fightedu.ui.theme.AnimationStage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * Hareketin gerçekçi videosu (assets/video/<id>.mp4, döngüsel).
 * [playing] false ise yalnızca kapak resmi (assets/poster/<id>.webp) gösterilir (liste küçük resimleri);
 * video da ilk karesi hazır olana kadar kapak resminin üstünde görünmez tutulur.
 * [paused] videoyu bulunduğu karede durdurur (antrenman duraklatıldığında).
 */
@Composable
fun MoveAnimation(
    move: Move,
    modifier: Modifier = Modifier,
    playing: Boolean = true,
    paused: Boolean = false,
    speed: Float = 1f,
    corner: Dp = 16.dp,
) {
    val context = LocalContext.current
    val poster by produceState<ImageBitmap?>(initialValue = Posters.cached(move.posterAsset), move.posterAsset) {
        if (value == null) value = withContext(Dispatchers.IO) { Posters.load(context, move.posterAsset) }
    }
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(corner))
            .background(AnimationStage),
        contentAlignment = Alignment.Center,
    ) {
        val image = poster
        if (image != null) {
            Image(
                bitmap = image,
                contentDescription = move.name,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize(),
            )
        } else {
            Text("🥋", style = MaterialTheme.typography.headlineMedium)
        }
        if (playing) {
            // hareket değişince oynatıcı ve TextureView birlikte yeniden kurulsun
            key(move.videoAsset) { MoveVideo(move.videoAsset, speed, paused, Modifier.fillMaxSize()) }
        }
    }
}

@Composable
private fun MoveVideo(asset: String, speed: Float, paused: Boolean, modifier: Modifier) {
    val context = LocalContext.current
    val player = remember {
        ExoPlayer.Builder(context).build().apply {
            setMediaItem(MediaItem.fromUri("asset:///$asset"))
            repeatMode = Player.REPEAT_MODE_ONE
            volume = 0f
            playWhenReady = true
            prepare()
        }
    }
    var firstFrame by remember { mutableStateOf(false) }
    LaunchedEffect(player, speed) { player.setPlaybackSpeed(speed) }
    LaunchedEffect(player, paused) { if (paused) player.pause() else player.play() }

    val lifecycleOwner = LocalLifecycleOwner.current
    val currentPaused by rememberUpdatedState(paused)
    DisposableEffect(player, lifecycleOwner) {
        val listener = object : Player.Listener {
            override fun onRenderedFirstFrame() {
                firstFrame = true
            }
        }
        player.addListener(listener)
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_START -> if (!currentPaused) player.play()
                Lifecycle.Event.ON_STOP -> player.pause()
                else -> Unit
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
            player.removeListener(listener)
            player.release()
        }
    }
    AndroidView(
        factory = { ctx -> TextureView(ctx).also { player.setVideoTextureView(it) } },
        modifier = modifier.alpha(if (firstFrame) 1f else 0f),
    )
}

/** Kapak resimleri için küçük bellek önbelleği (listelerde tekrar tekrar çözülmesin). */
private object Posters {
    private val cache = LruCache<String, ImageBitmap>(48)

    fun cached(asset: String): ImageBitmap? = cache.get(asset)

    fun load(context: Context, asset: String): ImageBitmap? {
        cache.get(asset)?.let { return it }
        val bitmap = runCatching {
            context.assets.open(asset).use { BitmapFactory.decodeStream(it) }
        }.getOrNull() ?: return null
        return bitmap.asImageBitmap().also { cache.put(asset, it) }
    }
}
