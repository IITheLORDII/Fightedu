package com.fightedu.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.fightedu.appContainer
import com.fightedu.core.content.ContentLibrary
import com.fightedu.core.domain.PlanConfig
import com.fightedu.core.domain.PlannedSession
import com.fightedu.core.domain.ProgressTracker
import com.fightedu.core.model.Sport
import com.fightedu.data.ReminderSettings
import com.fightedu.data.TrainingRepository
import com.fightedu.reminders.ReminderScheduler
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class UiState(
    val isLoading: Boolean = true,
    val content: ContentLibrary? = null,
    val plan: PlanConfig? = null,
    val sessions: List<PlannedSession> = emptyList(),
    val completed: Set<String> = emptySet(),
    val reminder: ReminderSettings = ReminderSettings(false, TrainingRepository.DEFAULT_REMINDER_HOUR),
    val error: String? = null,
) {
    val tracker: ProgressTracker by lazy { ProgressTracker(sessions, completed) }
    val sport: Sport? get() = plan?.let { content?.sport(it.sportId) }

    fun session(week: Int, index: Int): PlannedSession? =
        sessions.firstOrNull { it.week == week && it.index == index }
}

class MainViewModel(app: Application) : AndroidViewModel(app) {
    private val container = app.appContainer
    private val repo = container.repository

    private val contentFlow = flow { emit(container.content) }.flowOn(Dispatchers.IO)

    private val planWithSessions = repo.plan.map { plan ->
        plan to (plan?.let { container.planGenerator.generate(it) } ?: emptyList())
    }.flowOn(Dispatchers.Default)

    val state: StateFlow<UiState> = combine(
        contentFlow,
        planWithSessions,
        repo.completedKeys,
        repo.reminder,
    ) { content, (plan, sessions), completed, reminder ->
        UiState(
            isLoading = false,
            content = content,
            plan = plan,
            sessions = sessions,
            completed = completed,
            reminder = reminder,
        )
    }.catch { e ->
        emit(UiState(isLoading = false, error = e.message ?: e.toString()))
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), UiState())

    fun startPlan(config: PlanConfig, onDone: () -> Unit = {}) {
        viewModelScope.launch {
            repo.startPlan(config)
            onDone()
        }
    }

    fun setCompleted(sessionKey: String, completed: Boolean) {
        viewModelScope.launch {
            if (completed) repo.markCompleted(sessionKey) else repo.unmarkCompleted(sessionKey)
        }
    }

    fun resetPlan(onDone: () -> Unit = {}) {
        viewModelScope.launch {
            ReminderScheduler.cancel(getApplication())
            repo.reset()
            onDone()
        }
    }

    fun setReminder(enabled: Boolean, hour: Int) {
        viewModelScope.launch {
            repo.setReminder(enabled, hour)
            if (enabled) ReminderScheduler.schedule(getApplication(), hour) else ReminderScheduler.cancel(getApplication())
        }
    }
}
