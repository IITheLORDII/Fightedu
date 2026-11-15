package com.fightedu

import android.content.Context
import com.fightedu.core.content.ContentLibrary
import com.fightedu.core.domain.TrainingPlanner
import com.fightedu.core.voice.VoiceScript
import com.fightedu.data.AuthRepository
import com.fightedu.data.SessionStore
import com.fightedu.data.TrainingRepository
import com.fightedu.data.db.AppDatabase
import com.fightedu.health.HealthConnectGateway
import com.fightedu.core.health.HealthGateway

/** Basit manuel bağımlılık kabı. */
class AppContainer(context: Context) {
    private val appContext = context.applicationContext

    val content: ContentLibrary by lazy {
        ContentLibrary.load { path -> appContext.assets.open(path).bufferedReader().use { it.readText() } }
    }

    val planner: TrainingPlanner by lazy { TrainingPlanner(content) }

    /** Sesli koçun rauntlara özel metinleri ve ses planları (assets/voice); yoksa null. */
    val voice: VoiceScript? by lazy {
        VoiceScript.load(content.sports.map { it.id }) { path ->
            runCatching { appContext.assets.open(path).bufferedReader().use { it.readText() } }.getOrNull()
        }
    }

    /** Cümlelerin Türkçe ses kayıtları uygulamada var mı (yoksa aynı metinleri cihazın konuşma motoru okur). */
    val voiceRecorded: Boolean by lazy {
        val id = voice?.manifest?.clips?.keys?.firstOrNull() ?: return@lazy false
        runCatching { appContext.assets.open(VoiceScript.clipAsset(id)).close() }.isSuccess
    }

    private val database: AppDatabase by lazy { AppDatabase.create(appContext) }

    val session: SessionStore by lazy { SessionStore(appContext) }

    val repository: TrainingRepository by lazy { TrainingRepository(database) }

    val auth: AuthRepository by lazy { AuthRepository(database, session) }

    /** Sağlık uygulamaları (Android'de Health Connect; Samsung Health buradan okur). */
    val health: HealthGateway by lazy { HealthConnectGateway(appContext) }
}
