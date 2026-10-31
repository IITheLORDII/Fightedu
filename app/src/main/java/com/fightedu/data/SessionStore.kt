package com.fightedu.data

import android.content.Context
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** Oturum açık kullanıcının kimliği (cihazda, SharedPreferences). Uygulama kapanıp açılınca oturum sürer. */
class SessionStore(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences("session", Context.MODE_PRIVATE)
    private val _userId = MutableStateFlow(prefs.getLong(KEY, NONE).takeIf { it != NONE })

    val userId: StateFlow<Long?> = _userId.asStateFlow()

    val current: Long? get() = _userId.value

    fun set(id: Long) {
        prefs.edit().putLong(KEY, id).apply()
        _userId.value = id
    }

    fun clear() {
        prefs.edit().remove(KEY).apply()
        _userId.value = null
    }

    private companion object {
        const val KEY = "currentUserId"
        const val NONE = -1L
    }
}
