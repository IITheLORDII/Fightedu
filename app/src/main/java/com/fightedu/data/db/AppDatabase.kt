package com.fightedu.data.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

@Database(
    entities = [
        UserEntity::class,
        UserPlanEntity::class,
        CompletedSessionEntity::class,
        ActivityDayEntity::class,
    ],
    version = 4,
    exportSchema = true,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun userDao(): UserDao
    abstract fun planDao(): PlanDao
    abstract fun progressDao(): ProgressDao
    abstract fun activityDao(): ActivityDao

    companion object {
        const val NAME = "fightedu.db"

        /**
         * 3 -> 4 (1.2): şifre özeti tekrar sayısı (mevcut hesaplar 60.000; girişte yükseltilir), sağlık uygulaması
         * senkronu, tamamlanan antrenmanın başlangıcı, süresi ve tahmini kalorisi. Veri korunur.
         */
        val MIGRATION_3_4 = object : Migration(3, 4) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE users ADD COLUMN passwordIterations INTEGER NOT NULL DEFAULT 60000")
                db.execSQL("ALTER TABLE user_plan ADD COLUMN healthSync INTEGER NOT NULL DEFAULT 0")
                db.execSQL("ALTER TABLE completed_sessions ADD COLUMN startedAt INTEGER")
                db.execSQL("ALTER TABLE completed_sessions ADD COLUMN durationSec INTEGER")
                db.execSQL("ALTER TABLE completed_sessions ADD COLUMN kcal REAL")
            }
        }

        fun create(context: Context): AppDatabase =
            Room.databaseBuilder(context, AppDatabase::class.java, NAME)
                .addMigrations(MIGRATION_3_4)
                // 1-2 -> 4: yayın öncesi sürümler (eski veri taşınmıyor); sürüm düşürmede de veri sıfırlanır.
                // 3 -> 4 ve sonraki tüm geçişler veriyi korur.
                .fallbackToDestructiveMigrationFrom(1, 2)
                .fallbackToDestructiveMigrationOnDowngrade()
                .build()
    }
}
