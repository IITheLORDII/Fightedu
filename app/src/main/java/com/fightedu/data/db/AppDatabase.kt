package com.fightedu.data.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [
        UserEntity::class,
        UserPlanEntity::class,
        CompletedSessionEntity::class,
        ActivityDayEntity::class,
    ],
    version = 3,
    exportSchema = false,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun userDao(): UserDao
    abstract fun planDao(): PlanDao
    abstract fun progressDao(): ProgressDao
    abstract fun activityDao(): ActivityDao

    companion object {
        fun create(context: Context): AppDatabase =
            Room.databaseBuilder(context, AppDatabase::class.java, "fightedu.db")
                // 1 -> 2: haftalık takvimden sıralı günlere geçildi.
                // 2 -> 3: hesaplar, dal başına ilerleme ve seri; uygulama henüz yayımlanmadı, eski veri taşınmıyor.
                .fallbackToDestructiveMigration()
                .build()
    }
}
