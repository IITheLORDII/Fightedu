package com.fightedu.ui.components

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.ScaffoldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.fightedu.ui.theme.SuccessGreen

/**
 * Ekran iskeleti. [underBottomBar] true ise alt gezinme çubuğu kök Scaffold tarafından
 * çizildiği için bu ekran alt sistem boşluğunu tekrar eklemez.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppScaffold(
    title: String,
    onBack: (() -> Unit)? = null,
    underBottomBar: Boolean = false,
    actions: @Composable () -> Unit = {},
    bottomBar: @Composable () -> Unit = {},
    content: @Composable (PaddingValues) -> Unit,
) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(title, maxLines = 1, overflow = TextOverflow.Ellipsis) },
                navigationIcon = {
                    if (onBack != null) {
                        IconButton(onClick = onBack) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Geri")
                        }
                    }
                },
                actions = { actions() },
            )
        },
        bottomBar = bottomBar,
        contentWindowInsets = if (underBottomBar) WindowInsets(0, 0, 0, 0) else ScaffoldDefaults.contentWindowInsets,
        content = content,
    )
}

@Composable
fun SectionTitle(text: String, modifier: Modifier = Modifier) {
    Text(
        text = text,
        style = MaterialTheme.typography.titleMedium,
        modifier = modifier.padding(top = 16.dp, bottom = 8.dp),
    )
}

@Composable
fun Pill(text: String, color: Color = MaterialTheme.colorScheme.primary, modifier: Modifier = Modifier) {
    Surface(
        color = color.copy(alpha = 0.12f),
        contentColor = color,
        shape = RoundedCornerShape(50),
        modifier = modifier,
    ) {
        Text(text, style = MaterialTheme.typography.labelMedium, modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp))
    }
}

@Composable
fun LevelPill(level: Int, label: String) {
    val color = when (level) {
        1 -> SuccessGreen
        2 -> Color(0xFFEF6C00)
        else -> Color(0xFFC62828)
    }
    Pill(label, color)
}

enum class SessionStatus { DONE, OPEN, LOCKED }

@Composable
fun SessionStatusIcon(status: SessionStatus, modifier: Modifier = Modifier) {
    when (status) {
        SessionStatus.DONE -> Icon(Icons.Filled.CheckCircle, "Tamamlandı", tint = SuccessGreen, modifier = modifier)
        SessionStatus.LOCKED -> Icon(Icons.Filled.Lock, "Kilitli", tint = MaterialTheme.colorScheme.outline, modifier = modifier)
        SessionStatus.OPEN -> Box(
            modifier = modifier
                .padding(2.dp)
                .size(20.dp)
                .border(2.dp, MaterialTheme.colorScheme.outline, CircleShape),
        )
    }
}

@Composable
fun BulletList(items: List<String>, numbered: Boolean = false, bulletColor: Color = MaterialTheme.colorScheme.primary) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        items.forEachIndexed { i, item ->
            Row(verticalAlignment = Alignment.Top, modifier = Modifier.fillMaxWidth()) {
                Text(
                    text = if (numbered) "${i + 1}." else "•",
                    color = bulletColor,
                    style = MaterialTheme.typography.bodyLarge,
                    modifier = Modifier.padding(end = 8.dp),
                )
                Text(item, style = MaterialTheme.typography.bodyLarge)
            }
        }
    }
}
