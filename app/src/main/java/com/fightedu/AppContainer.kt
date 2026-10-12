package com.fightedu

import android.content.Context
import com.fightedu.core.content.ContentLibrary
import com.fightedu.core.domain.PlanGenerator
import com.fightedu.data.TrainingRepository
import com.fightedu.data.db.AppDatabase

/** Basit manuel bağımlılık kabı. */
class AppContainer(context: Context) {
    private val appContext = context.applicationContext

    val content: ContentLibrary by lazy {
        ContentLibrary.load { path -> appContext.assets.open(path).bufferedReader().use { it.readText() } }
    }

    val planGenerator: PlanGenerator by lazy { PlanGenerator(content) }

    private val database: AppDatabase by lazy { AppDatabase.create(appContext) }

    val repository: TrainingRepository by lazy { TrainingRepository(database) }
}
