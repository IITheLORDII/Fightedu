package com.fightedu

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.fightedu.data.db.AppDatabase
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

/** 1.1'in (veritabanı sürüm 3) verisi 1.2'ye (sürüm 4) geçerken korunur ve şema Room'un beklediğiyle aynıdır. */
@RunWith(AndroidJUnit4::class)
class MigrationTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()
    private val name = "migration-test.db"

    @After
    fun tearDown() {
        context.deleteDatabase(name)
    }

    @Test
    fun `3 -> 4 geçişi veriyi korur ve yeni sütunlar varsayılanlarla gelir`() {
        // 1.1'deki Room'un oluşturduğu sürüm 3 şeması
        val file = context.getDatabasePath(name).apply { parentFile?.mkdirs() }
        SQLiteDatabase.openOrCreateDatabase(file, null).use { db ->
            db.execSQL("CREATE TABLE IF NOT EXISTS `users` (`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `name` TEXT NOT NULL, `email` TEXT, `passwordHash` TEXT, `passwordSalt` TEXT, `isGuest` INTEGER NOT NULL, `createdAt` INTEGER NOT NULL)")
            db.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS `index_users_email` ON `users` (`email`)")
            db.execSQL("CREATE TABLE IF NOT EXISTS `user_plan` (`userId` INTEGER NOT NULL, `sportId` TEXT NOT NULL, `daysMask` INTEGER NOT NULL, `reminderEnabled` INTEGER NOT NULL, `reminderHour` INTEGER NOT NULL, `voiceCoach` INTEGER NOT NULL, `vibration` INTEGER NOT NULL, PRIMARY KEY(`userId`))")
            db.execSQL("CREATE TABLE IF NOT EXISTS `completed_sessions` (`userId` INTEGER NOT NULL, `sportId` TEXT NOT NULL, `sessionKey` TEXT NOT NULL, `completedAt` INTEGER NOT NULL, PRIMARY KEY(`userId`, `sportId`, `sessionKey`))")
            db.execSQL("CREATE TABLE IF NOT EXISTS `activity_days` (`userId` INTEGER NOT NULL, `epochDay` INTEGER NOT NULL, PRIMARY KEY(`userId`, `epochDay`))")
            db.execSQL("INSERT INTO users VALUES (1, 'Ali', 'ali@ornek.com', 'hash', 'salt', 0, 1700000000000)")
            db.execSQL("INSERT INTO user_plan VALUES (1, 'boxing', 127, 1, 18, 1, 1)")
            db.execSQL("INSERT INTO completed_sessions VALUES (1, 'boxing', 'day_1', 1700000100000)")
            db.execSQL("INSERT INTO activity_days VALUES (1, 19700)")
            db.version = 3
        }

        val room = Room.databaseBuilder(context, AppDatabase::class.java, name)
            .addMigrations(AppDatabase.MIGRATION_3_4)
            .allowMainThreadQueries()
            .build()
        try {
            runBlocking {
                // Room açılışta şemayı doğrular; geçiş eksik/yanlışsa burada hata verir
                val user = requireNotNull(room.userDao().get(1))
                assertEquals("ali@ornek.com", user.email)
                assertEquals("hash", user.passwordHash)
                assertEquals("eski hesaplar eski tekrar sayısıyla", 60_000, user.passwordIterations)
                val plan = requireNotNull(room.planDao().get(1))
                assertEquals("boxing", plan.sportId)
                assertTrue(plan.reminderEnabled)
                assertFalse("sağlık senkronu kapalı başlar", plan.healthSync)
                val done = requireNotNull(room.progressDao().get(1, "boxing", "day_1"))
                assertNull(done.startedAt)
                assertNull(done.kcal)
                assertEquals(listOf(19700L), room.activityDao().days(1))
            }
        } finally {
            room.close()
        }
    }
}
