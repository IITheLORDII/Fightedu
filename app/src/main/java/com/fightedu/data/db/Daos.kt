package com.fightedu.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

@Dao
interface UserDao {
    @Insert(onConflict = OnConflictStrategy.ABORT)
    suspend fun insert(user: UserEntity): Long

    @Update
    suspend fun update(user: UserEntity)

    @Query("SELECT * FROM users WHERE id = :id")
    suspend fun get(id: Long): UserEntity?

    @Query("SELECT * FROM users WHERE id = :id")
    fun observe(id: Long): Flow<UserEntity?>

    @Query("SELECT * FROM users WHERE email = :email LIMIT 1")
    suspend fun findByEmail(email: String): UserEntity?

    @Query("DELETE FROM users WHERE id = :id")
    suspend fun delete(id: Long)
}

@Dao
interface PlanDao {
    @Query("SELECT * FROM user_plan WHERE userId = :userId")
    fun observe(userId: Long): Flow<UserPlanEntity?>

    @Query("SELECT * FROM user_plan WHERE userId = :userId")
    suspend fun get(userId: Long): UserPlanEntity?

    @Upsert
    suspend fun upsert(plan: UserPlanEntity)

    @Query("DELETE FROM user_plan WHERE userId = :userId")
    suspend fun delete(userId: Long)
}

@Dao
interface ProgressDao {
    @Query("SELECT sessionKey FROM completed_sessions WHERE userId = :userId AND sportId = :sportId")
    fun observeKeys(userId: Long, sportId: String): Flow<List<String>>

    @Query("SELECT sessionKey FROM completed_sessions WHERE userId = :userId AND sportId = :sportId")
    suspend fun keys(userId: Long, sportId: String): List<String>

    @Query("SELECT sportId, COUNT(*) AS done FROM completed_sessions WHERE userId = :userId GROUP BY sportId")
    fun observeCounts(userId: Long): Flow<List<SportCount>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entity: CompletedSessionEntity)

    @Query("DELETE FROM completed_sessions WHERE userId = :userId AND sportId = :sportId AND sessionKey = :key")
    suspend fun delete(userId: Long, sportId: String, key: String)

    @Query("DELETE FROM completed_sessions WHERE userId = :userId AND sportId = :sportId")
    suspend fun clearSport(userId: Long, sportId: String)

    @Query("DELETE FROM completed_sessions WHERE userId = :userId")
    suspend fun clearUser(userId: Long)
}

@Dao
interface ActivityDao {
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insert(day: ActivityDayEntity)

    @Query("SELECT epochDay FROM activity_days WHERE userId = :userId")
    fun observe(userId: Long): Flow<List<Long>>

    @Query("SELECT epochDay FROM activity_days WHERE userId = :userId")
    suspend fun days(userId: Long): List<Long>

    @Query("DELETE FROM activity_days WHERE userId = :userId")
    suspend fun clearUser(userId: Long)
}
