package com.fightedu.ui.library

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.fightedu.core.content.ContentLibrary
import com.fightedu.core.model.Move
import com.fightedu.ui.components.AppScaffold
import com.fightedu.ui.components.LevelPill
import com.fightedu.ui.components.MoveAnimation

@Composable
fun LibraryScreen(content: ContentLibrary, defaultSportId: String?, onOpenMove: (Move) -> Unit) {
    var sportId by rememberSaveable { mutableStateOf(defaultSportId ?: content.sports.first().id) }
    var category by rememberSaveable { mutableStateOf<String?>(null) }

    val sportMoves = content.movesForSport(sportId).sortedWith(compareBy({ it.level }, { it.category.ordinal }))
    val categories = sportMoves.map { it.category }.distinct()
    val visible = sportMoves.filter { category == null || it.category.name == category }

    AppScaffold(title = "Hareket Kütüphanesi", underBottomBar = true) { padding ->
        Column(
            Modifier
                .fillMaxSize()
                .padding(padding),
        ) {
            ChipRow {
                content.sports.forEach { sport ->
                    FilterChip(
                        selected = sportId == sport.id,
                        onClick = {
                            sportId = sport.id
                            category = null
                        },
                        label = { Text("${sport.emoji} ${sport.name}") },
                    )
                }
                FilterChip(
                    selected = sportId == ContentLibrary.GENERAL,
                    onClick = {
                        sportId = ContentLibrary.GENERAL
                        category = null
                    },
                    label = { Text("💪 Isınma & Kondisyon") },
                )
            }
            ChipRow {
                FilterChip(selected = category == null, onClick = { category = null }, label = { Text("Tümü") })
                categories.forEach { c ->
                    FilterChip(selected = category == c.name, onClick = { category = c.name }, label = { Text(c.label) })
                }
            }
            LazyColumn(contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                items(visible, key = { it.id }) { move ->
                    Card(onClick = { onOpenMove(move) }, modifier = Modifier.fillMaxWidth()) {
                        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                            MoveAnimation(move, Modifier.size(72.dp), playing = false, corner = 12.dp)
                            Spacer(Modifier.width(12.dp))
                            Column(Modifier.weight(1f)) {
                                Text(move.name, style = MaterialTheme.typography.titleMedium)
                                Text(move.category.label, style = MaterialTheme.typography.bodySmall)
                                Spacer(Modifier.padding(top = 4.dp))
                                LevelPill(move.level, move.levelLabel)
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ChipRow(content: @Composable () -> Unit) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        modifier = Modifier
            .fillMaxWidth()
            .horizontalScroll(rememberScrollState())
            .padding(horizontal = 16.dp, vertical = 4.dp),
    ) { content() }
}
