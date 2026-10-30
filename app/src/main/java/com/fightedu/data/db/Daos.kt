package com.fightedu.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

@Dao
interface PlanDao {
    @Query("SELECT * FROM user_plan WHERE id = 1")
    fun observe(): Flow<UserPlanEntity?>

    @Query("SELECT * FROM user_plan WHERE id = 1")
    suspend fun get(): UserPlanEntity?

    @Upsert
    suspend fun upsert(plan: UserPlanEntity)

    @Query("DELETE FROM user_plan")
    suspend fun clear()
}

@Dao
interface ProgressDao {
    @Query("SELECT * FROM completed_sessions")
    fun observeAll(): Flow<List<CompletedSessionEntity>>

    @Query("SELECT sessionKey FROM completed_sessions")
    suspend fun keys(): List<String>

    @Query("SELECT MAX(completedAt) FROM completed_sessions")
    suspend fun lastCompletedAt(): Long?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entity: CompletedSessionEntity)

    @Query("DELETE FROM completed_sessions WHERE sessionKey = :key")
    suspend fun delete(key: String)

    @Query("DELETE FROM completed_sessions")
    suspend fun clear()
}
