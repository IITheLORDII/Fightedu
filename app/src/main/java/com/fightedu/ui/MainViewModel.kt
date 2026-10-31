package com.fightedu.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.fightedu.appContainer
import com.fightedu.coach.CoachVoice
import com.fightedu.core.content.ContentLibrary
import com.fightedu.core.domain.ChallengeProgress
import com.fightedu.core.domain.ProgressTracker
import com.fightedu.core.domain.TrainingPlanner
import com.fightedu.core.model.Sport
import com.fightedu.core.model.TrainingDay
import com.fightedu.core.model.TrainingProgram
import com.fightedu.core.voice.VoiceScript
import com.fightedu.data.AuthResult
import com.fightedu.data.CoachSettings
import com.fightedu.data.ReminderSettings
import com.fightedu.data.TrainingRepository
import com.fightedu.data.User
import com.fightedu.data.db.UserPlanEntity
import com.fightedu.reminders.ReminderScheduler
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.time.LocalDate

/** Oturumdaki kullanıcının verisi (kullanıcı yoksa boş). */
private data class UserData(
    val user: User? = null,
    val plan: UserPlanEntity? = null,
    val completedKeys: Set<String> = emptySet(),
    val activityDays: Set<Long> = emptySet(),
    val sportProgress: Map<String, Int> = emptyMap(),
)

data class UiState(
    val isLoading: Boolean = true,
    val content: ContentLibrary? = null,
    val planner: TrainingPlanner? = null,
    val user: User? = null,
    val sportId: String? = null,
    val completedKeys: Set<String> = emptySet(),
    val activityDays: Set<Long> = emptySet(),
    /** Dal -> tamamlanan meydan okuma günü (dal seçim kartlarında). */
    val sportProgress: Map<String, Int> = emptyMap(),
    val reminder: ReminderSettings = ReminderSettings(false, TrainingRepository.DEFAULT_REMINDER_HOUR),
    val coach: CoachSettings = CoachSettings(),
    val voice: VoiceScript? = null,
    val voiceRecorded: Boolean = false,
    val error: String? = null,
) {
    /** Antrenman gününün ([day] = programın gün numarası) ses planı. */
    fun workoutVoice(day: Int): CoachVoice? {
        val v = voice ?: return null
        val cues = sportId?.let { v.workout(it, day) } ?: return null
        return CoachVoice(v.manifest, cues, voiceRecorded)
    }

    /** Meydan okumanın [challengeDay]. günündeki (dinlenme) esneme seansının ses planı. */
    fun restVoice(challengeDay: Int): CoachVoice? {
        val v = voice ?: return null
        val cues = sportId?.let { v.restDay(it, challengeDay) } ?: return null
        return CoachVoice(v.manifest, cues, voiceRecorded)
    }

    val sport: Sport? get() = sportId?.let { content?.sport(it) }
    val program: TrainingProgram? get() = sportId?.let { content?.program(it) }
    val completedDays: Set<Int> get() = ProgressTracker.daysFromKeys(completedKeys)
    val challenge: ChallengeProgress? by lazy {
        program?.let { ChallengeProgress(it, completedKeys, activityDays, LocalDate.now()) }
    }

    /** Tamamlanan antrenmanların tahmini toplam süresi (dk). */
    val totalMinutes: Int by lazy {
        val p = program ?: return@lazy 0
        val pl = planner ?: return@lazy 0
        completedDays.sumOf { d -> p.day(d)?.let { pl.estimatedMinutes(it) } ?: 0 }
    }

    fun day(number: Int): TrainingDay? = program?.day(number)
}

class MainViewModel(app: Application) : AndroidViewModel(app) {
    private val container = app.appContainer
    private val repo = container.repository
    private val auth = container.auth

    private val contentFlow = flow {
        // ses planları da arka planda yüklensin (oynatıcı açılırken beklemesin)
        container.voice
        container.voiceRecorded
        emit(container.content to container.planner)
    }.flowOn(Dispatchers.IO)

    @OptIn(ExperimentalCoroutinesApi::class)
    private val userData: Flow<UserData> = auth.currentUser.flatMapLatest { user ->
        if (user == null) {
            flowOf(UserData())
        } else {
            repo.plan(user.id).flatMapLatest { plan ->
                val keys = plan?.let { repo.completedKeys(user.id, it.sportId) } ?: flowOf(emptySet())
                combine(keys, repo.activityDays(user.id), repo.sportProgress(user.id)) { k, a, sp ->
                    UserData(user, plan, k, a, sp)
                }
            }
        }
    }

    val state: StateFlow<UiState> = combine(contentFlow, userData) { (content, planner), data ->
        val plan = data.plan
        UiState(
            isLoading = false,
            content = content,
            planner = planner,
            user = data.user,
            sportId = plan?.sportId?.takeIf { content.program(it) != null },
            completedKeys = data.completedKeys,
            activityDays = data.activityDays,
            sportProgress = data.sportProgress,
            voice = container.voice,
            voiceRecorded = container.voiceRecorded,
            reminder = ReminderSettings(plan?.reminderEnabled ?: false,
                plan?.reminderHour ?: TrainingRepository.DEFAULT_REMINDER_HOUR),
            coach = CoachSettings(plan?.voiceCoach ?: true, plan?.vibration ?: true),
        )
    }.catch { e ->
        emit(UiState(isLoading = false, error = e.message ?: e.toString()))
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), UiState())

    private val userId: Long? get() = container.session.current

    // -- hesap ------------------------------------------------------------------------------------
    fun register(name: String, email: String, password: String, onResult: (AuthResult) -> Unit) {
        viewModelScope.launch { onResult(auth.register(name, email, password)) }
    }

    fun login(email: String, password: String, onResult: (AuthResult) -> Unit) {
        viewModelScope.launch { onResult(auth.login(email, password)) }
    }

    fun continueAsGuest(onDone: () -> Unit) {
        viewModelScope.launch {
            auth.continueAsGuest()
            onDone()
        }
    }

    fun rename(name: String, onResult: (String?) -> Unit) {
        viewModelScope.launch { onResult(auth.rename(name)) }
    }

    fun logout(onDone: () -> Unit) {
        viewModelScope.launch {
            ReminderScheduler.cancel(getApplication())
            auth.logout()
            onDone()
        }
    }

    // -- meydan okuma -----------------------------------------------------------------------------
    fun selectSport(sportId: String, reminder: ReminderSettings, onDone: () -> Unit = {}) {
        val id = userId ?: return
        viewModelScope.launch {
            repo.selectSport(id, sportId, reminder)
            applyReminder(reminder)
            onDone()
        }
    }

    /** Antrenman günü ([day] = programın antrenman günü numarası) tamamlandı / geri alındı. */
    fun setDayCompleted(day: Int, completed: Boolean) = setKey(ProgressTracker.keyOf(day), completed)

    /** Meydan okumanın [number]. günü (dinlenme) tamamlandı / geri alındı. */
    fun setRestCompleted(number: Int, completed: Boolean) = setKey(ChallengeProgress.restKey(number), completed)

    private fun setKey(key: String, completed: Boolean) {
        val id = userId ?: return
        val sport = state.value.sportId ?: return
        viewModelScope.launch {
            if (completed) repo.markCompleted(id, sport, key) else repo.unmarkCompleted(id, sport, key)
        }
    }

    fun restartChallenge() {
        val id = userId ?: return
        val sport = state.value.sportId ?: return
        viewModelScope.launch { repo.restartSport(id, sport) }
    }

    // -- ayarlar ----------------------------------------------------------------------------------
    fun setReminder(enabled: Boolean, hour: Int) {
        val id = userId ?: return
        viewModelScope.launch {
            repo.setReminder(id, enabled, hour)
            applyReminder(ReminderSettings(enabled, hour))
        }
    }

    private fun applyReminder(reminder: ReminderSettings) {
        if (reminder.enabled) {
            ReminderScheduler.schedule(getApplication(), reminder.hour)
        } else {
            ReminderScheduler.cancel(getApplication())
        }
    }

    fun setCoach(settings: CoachSettings) {
        val id = userId ?: return
        viewModelScope.launch { repo.setCoach(id, settings) }
    }
}
