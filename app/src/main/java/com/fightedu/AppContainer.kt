package com.fightedu

import android.content.Context
import com.fightedu.core.content.ContentLibrary
import com.fightedu.core.domain.TrainingPlanner
import com.fightedu.data.AuthRepository
import com.fightedu.data.SessionStore
import com.fightedu.data.TrainingRepository
import com.fightedu.data.db.AppDatabase

/** Basit manuel bağımlılık kabı. */
class AppContainer(context: Context) {
    private val appContext = context.applicationContext

    val content: ContentLibrary by lazy {
        ContentLibrary.load { path -> appContext.assets.open(path).bufferedReader().use { it.readText() } }
    }

    val planner: TrainingPlanner by lazy { TrainingPlanner(content) }

    private val database: AppDatabase by lazy { AppDatabase.create(appContext) }

    val session: SessionStore by lazy { SessionStore(appContext) }

    val repository: TrainingRepository by lazy { TrainingRepository(database) }

    val auth: AuthRepository by lazy { AuthRepository(database, session) }
}
