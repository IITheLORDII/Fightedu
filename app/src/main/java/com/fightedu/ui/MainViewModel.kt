package com.fightedu.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.fightedu.appContainer
import com.fightedu.core.content.ContentLibrary
import com.fightedu.core.domain.PlanConfig
import com.fightedu.core.domain.ProgressTracker
import com.fightedu.core.domain.TrainingPlanner
import com.fightedu.core.model.Sport
import com.fightedu.core.model.TrainingDay
import com.fightedu.core.model.TrainingProgram
import com.fightedu.data.CoachSettings
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
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class UiState(
    val isLoading: Boolean = true,
    val content: ContentLibrary? = null,
    val planner: TrainingPlanner? = null,
    val plan: PlanConfig? = null,
    val completedDays: Set<Int> = emptySet(),
    val reminder: ReminderSettings = ReminderSettings(false, TrainingRepository.DEFAULT_REMINDER_HOUR),
    val coach: CoachSettings = CoachSettings(),
    val error: String? = null,
) {
    val sport: Sport? get() = plan?.let { content?.sport(it.sportId) }
    val program: TrainingProgram? get() = plan?.let { content?.program(it.sportId) }
    val tracker: ProgressTracker? by lazy { program?.let { ProgressTracker(it, completedDays) } }

    fun day(number: Int): TrainingDay? = program?.day(number)
}

class MainViewModel(app: Application) : AndroidViewModel(app) {
    private val container = app.appContainer
    private val repo = container.repository

    private val contentFlow = flow { emit(container.content to container.planner) }.flowOn(Dispatchers.IO)

    private val settings = combine(repo.reminder, repo.coach) { r, c -> r to c }

    val state: StateFlow<UiState> = combine(
        contentFlow,
        repo.plan,
        repo.completedKeys,
        settings,
    ) { (content, planner), plan, keys, (reminder, coach) ->
        UiState(
            isLoading = false,
            content = content,
            planner = planner,
            plan = plan,
            completedDays = ProgressTracker.daysFromKeys(keys),
            reminder = reminder,
            coach = coach,
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

    fun setDayCompleted(day: Int, completed: Boolean) {
        viewModelScope.launch {
            val key = ProgressTracker.keyOf(day)
            if (completed) repo.markCompleted(key) else repo.unmarkCompleted(key)
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

    fun setCoach(settings: CoachSettings) {
        viewModelScope.launch { repo.setCoach(settings) }
    }
}
