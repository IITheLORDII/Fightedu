package com.fightedu.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.fightedu.core.domain.ChallengeCalendar
import com.fightedu.core.domain.ChallengeDay
import com.fightedu.ui.auth.LoginScreen
import com.fightedu.ui.auth.RegisterScreen
import com.fightedu.ui.auth.WelcomeScreen
import com.fightedu.ui.challenge.ChallengeScreen
import com.fightedu.ui.components.BrandBackground
import com.fightedu.ui.intro.IntroScreen
import com.fightedu.ui.library.LibraryScreen
import com.fightedu.ui.library.MoveDetailScreen
import com.fightedu.ui.player.PlayerScreen
import com.fightedu.ui.profile.ProfileScreen
import com.fightedu.ui.rest.RestDayScreen
import com.fightedu.ui.session.SessionDetailScreen
import com.fightedu.ui.sports.SportConfirmScreen
import com.fightedu.ui.sports.SportSelectScreen
import com.fightedu.ui.theme.BrandTheme
import com.fightedu.ui.theme.DefaultAccent
import com.fightedu.ui.theme.FightEduTheme
import com.fightedu.ui.theme.parseColor

private object Routes {
    const val INTRO = "intro"
    const val WELCOME = "welcome"
    const val REGISTER = "register"
    const val LOGIN = "login"
    /** Oturum açıldıktan sonra kullanıcının verisi gelince doğru ekrana yönlendirir. */
    const val ROUTER = "router"
    const val SPORTS = "sports"
    const val SPORT = "sport/{id}"
    const val CHALLENGE = "challenge"
    const val LIBRARY = "library"
    const val PROFILE = "profile"
    const val SESSION = "day/{day}"
    const val PLAYER = "player/{day}"
    const val REST = "rest/{n}"
    const val REST_PLAYER = "restplayer/{n}"
    const val MOVE = "move/{id}"

    fun sport(id: String) = "sport/$id"
    fun session(day: Int) = "day/$day"
    fun player(day: Int) = "player/$day"
    fun rest(n: Int) = "rest/$n"
    fun restPlayer(n: Int) = "restplayer/$n"
    fun move(id: String) = "move/$id"
}

private data class Tab(val route: String, val label: String, val icon: ImageVector)

private val TABS = listOf(
    Tab(Routes.CHALLENGE, "Meydan Okuma", Icons.Filled.Star),
    Tab(Routes.LIBRARY, "Hareketler", Icons.AutoMirrored.Filled.List),
    Tab(Routes.PROFILE, "Profil", Icons.Filled.Person),
)

@Composable
fun FightEduRoot(vm: MainViewModel = viewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()
    FightEduTheme(accent = parseColor(state.sport?.colorHex) ?: DefaultAccent) {
        Surface(color = MaterialTheme.colorScheme.background, modifier = Modifier.fillMaxSize()) {
            when {
                // sistem açılış ekranı yükleme bitene kadar ekranda kalır (MainActivity)
                state.isLoading -> BrandTheme { BrandBackground {} }
                state.content == null -> ErrorView(state.error ?: "İçerik yüklenemedi")
                else -> AppNavigation(state, vm)
            }
        }
    }
}

@Composable
private fun ErrorView(message: String) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("Bir sorun oluştu", style = MaterialTheme.typography.titleLarge)
        Text(message, style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
private fun AppNavigation(state: UiState, vm: MainViewModel) {
    val content = requireNotNull(state.content)
    val planner = requireNotNull(state.planner)
    val nav = rememberNavController()
    val backStack by nav.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route
    val showBottomBar = TABS.any { it.route == currentRoute }
    val latest by rememberUpdatedState(state)

    /** Oturum ve dal durumuna göre gidilecek ilk ekran; geri yığını temizlenir. */
    fun goHome() {
        val s = latest
        val target = when {
            s.user == null -> Routes.WELCOME
            s.sportId == null -> Routes.SPORTS
            else -> Routes.CHALLENGE
        }
        nav.navigate(target) { popUpTo(nav.graph.id) { inclusive = true } }
    }

    fun openChallengeDay(day: ChallengeDay) = when (day) {
        is ChallengeDay.Workout -> nav.navigate(Routes.session(day.training.day))
        is ChallengeDay.Rest -> nav.navigate(Routes.rest(day.number))
    }

    fun startChallengeDay(day: ChallengeDay) = when (day) {
        is ChallengeDay.Workout -> nav.navigate(Routes.player(day.training.day))
        is ChallengeDay.Rest -> nav.navigate(Routes.rest(day.number))
    }

    Scaffold(
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        bottomBar = {
            if (showBottomBar) {
                NavigationBar {
                    TABS.forEach { tab ->
                        NavigationBarItem(
                            selected = currentRoute == tab.route,
                            onClick = { nav.navigateToTab(tab.route) },
                            icon = { Icon(tab.icon, contentDescription = tab.label) },
                            label = { Text(tab.label) },
                        )
                    }
                }
            }
        },
    ) { inner ->
        NavHost(navController = nav, startDestination = Routes.INTRO, modifier = Modifier.padding(inner)) {
            // -- açılış ve hesap ---------------------------------------------------------------------
            composable(Routes.INTRO) {
                BrandTheme { IntroScreen(onFinished = { goHome() }) }
            }
            composable(Routes.WELCOME) {
                BrandTheme {
                    WelcomeScreen(
                        sports = content.sports,
                        onRegister = { nav.navigate(Routes.REGISTER) },
                        onLogin = { nav.navigate(Routes.LOGIN) },
                        onGuest = { vm.continueAsGuest { nav.navigate(Routes.ROUTER) { popUpTo(nav.graph.id) { inclusive = true } } } },
                    )
                }
            }
            composable(Routes.REGISTER) {
                val upgrading = state.user?.isGuest == true
                BrandTheme {
                    RegisterScreen(
                        upgradingGuest = upgrading,
                        onBack = { nav.popBackStack() },
                        onSubmit = vm::register,
                        onSuccess = {
                            if (upgrading) {
                                nav.popBackStack()
                            } else {
                                nav.navigate(Routes.ROUTER) { popUpTo(nav.graph.id) { inclusive = true } }
                            }
                        },
                        onGoLogin = {
                            nav.navigate(Routes.LOGIN) { popUpTo(Routes.REGISTER) { inclusive = true } }
                        },
                    )
                }
            }
            composable(Routes.LOGIN) {
                BrandTheme {
                    LoginScreen(
                        onBack = { nav.popBackStack() },
                        onSubmit = vm::login,
                        onSuccess = { nav.navigate(Routes.ROUTER) { popUpTo(nav.graph.id) { inclusive = true } } },
                        onGoRegister = {
                            nav.navigate(Routes.REGISTER) { popUpTo(Routes.LOGIN) { inclusive = true } }
                        },
                    )
                }
            }
            composable(Routes.ROUTER) {
                // kullanıcının planı akıştan gelince yönlendir
                LaunchedEffect(state.user?.id) { if (state.user != null) goHome() }
                BrandTheme { BrandBackground {} }
            }

            // -- dal seçimi --------------------------------------------------------------------------
            composable(Routes.SPORTS) {
                BrandTheme {
                    SportSelectScreen(
                        userName = state.user?.name,
                        sports = content.sports,
                        progress = state.sportProgress,
                        currentSportId = state.sportId,
                        onBack = if (state.sportId != null) ({ nav.popBackStack(); Unit }) else null,
                        onSelect = { nav.navigate(Routes.sport(it.id)) },
                    )
                }
            }
            composable(Routes.SPORT, arguments = listOf(navArgument("id") { type = NavType.StringType })) { entry ->
                val sport = entry.arguments?.getString("id")?.let { content.sport(it) }
                if (sport == null) {
                    MissingContent { nav.popBackStack() }
                } else {
                    BrandTheme {
                        SportConfirmScreen(
                            sport = sport,
                            content = content,
                            planner = planner,
                            progressDone = state.sportProgress[sport.id] ?: 0,
                            reminder = if (state.sportId != null) state.reminder else null,
                            onBack = { nav.popBackStack() },
                            onStart = { reminder ->
                                vm.selectSport(sport.id, reminder) {
                                    nav.navigate(Routes.CHALLENGE) { popUpTo(nav.graph.id) { inclusive = true } }
                                }
                            },
                        )
                    }
                }
            }

            // -- sekmeler ----------------------------------------------------------------------------
            composable(Routes.CHALLENGE) {
                val sport = state.sport
                val challenge = state.challenge
                if (sport == null || challenge == null) {
                    LaunchedEffect(Unit) { goHome() }
                } else {
                    ChallengeScreen(
                        user = state.user,
                        sport = sport,
                        challenge = challenge,
                        planner = planner,
                        totalMinutes = state.totalMinutes,
                        onOpenDay = ::openChallengeDay,
                        onStartDay = ::startChallengeDay,
                        onOpenProfile = { nav.navigateToTab(Routes.PROFILE) },
                        onChangeSport = { nav.navigate(Routes.SPORTS) },
                        onRestart = vm::restartChallenge,
                    )
                }
            }
            composable(Routes.LIBRARY) {
                LibraryScreen(
                    content = content,
                    defaultSportId = state.sportId,
                    onOpenMove = { nav.navigate(Routes.move(it.id)) },
                )
            }
            composable(Routes.PROFILE) {
                ProfileScreen(
                    state = state,
                    onChangeSport = { nav.navigate(Routes.SPORTS) },
                    onCreateAccount = { nav.navigate(Routes.REGISTER) },
                    onRename = vm::rename,
                    onSetReminder = vm::setReminder,
                    onSetCoach = vm::setCoach,
                    onRestart = vm::restartChallenge,
                    onLogout = { vm.logout { nav.navigate(Routes.WELCOME) { popUpTo(nav.graph.id) { inclusive = true } } } },
                )
            }

            // -- günler ------------------------------------------------------------------------------
            composable(Routes.SESSION, arguments = listOf(navArgument("day") { type = NavType.IntType })) { entry ->
                val day = state.day(requireNotNull(entry.arguments).getInt("day"))
                if (day == null) {
                    MissingContent { nav.popBackStack() }
                } else {
                    val n = ChallengeCalendar.challengeDayOf(day.day)
                    SessionDetailScreen(
                        day = day,
                        phase = state.program?.phaseOf(day.day),
                        content = content,
                        planner = planner,
                        completed = day.day in state.completedDays,
                        onBack = { nav.popBackStack() },
                        onStart = { nav.navigate(Routes.player(day.day)) },
                        onToggleCompleted = { vm.setDayCompleted(day.day, it) },
                        onOpenMove = { nav.navigate(Routes.move(it.id)) },
                        title = "Gün $n / ${ChallengeCalendar.LENGTH}",
                    )
                }
            }
            composable(Routes.PLAYER, arguments = listOf(navArgument("day") { type = NavType.IntType })) { entry ->
                val day = state.day(requireNotNull(entry.arguments).getInt("day"))
                if (day == null) {
                    MissingContent { nav.popBackStack() }
                } else {
                    PlayerScreen(
                        day = day,
                        planner = planner,
                        coach = state.coach,
                        label = "GÜN ${ChallengeCalendar.challengeDayOf(day.day)} / ${ChallengeCalendar.LENGTH}",
                        onExit = { nav.popBackStack() },
                        onCompleted = { vm.setDayCompleted(day.day, true) },
                        onDone = { if (!nav.popBackStack(Routes.CHALLENGE, inclusive = false)) nav.popBackStack() },
                    )
                }
            }
            composable(Routes.REST, arguments = listOf(navArgument("n") { type = NavType.IntType })) { entry ->
                val n = requireNotNull(entry.arguments).getInt("n")
                val challenge = state.challenge
                if (challenge == null || !ChallengeCalendar.isRest(n)) {
                    MissingContent { nav.popBackStack() }
                } else {
                    RestDayScreen(
                        number = n,
                        restDay = content.restDay,
                        planner = planner,
                        done = challenge.isDone(n),
                        onBack = { nav.popBackStack() },
                        onStartStretch = { nav.navigate(Routes.restPlayer(n)) },
                        onComplete = { done ->
                            vm.setRestCompleted(n, done)
                            if (done) nav.popBackStack()
                        },
                    )
                }
            }
            composable(Routes.REST_PLAYER, arguments = listOf(navArgument("n") { type = NavType.IntType })) { entry ->
                val n = requireNotNull(entry.arguments).getInt("n")
                val restDay = content.restDay
                if (restDay == null) {
                    MissingContent { nav.popBackStack() }
                } else {
                    PlayerScreen(
                        day = restDay,
                        planner = planner,
                        coach = state.coach,
                        label = "GÜN $n · DİNLENME",
                        onExit = { nav.popBackStack() },
                        onCompleted = { vm.setRestCompleted(n, true) },
                        onDone = { if (!nav.popBackStack(Routes.CHALLENGE, inclusive = false)) nav.popBackStack() },
                    )
                }
            }
            composable(Routes.MOVE, arguments = listOf(navArgument("id") { type = NavType.StringType })) { entry ->
                val move = entry.arguments?.getString("id")?.let { content.move(it) }
                if (move == null) {
                    MissingContent { nav.popBackStack() }
                } else {
                    MoveDetailScreen(move = move, onBack = { nav.popBackStack() })
                }
            }
        }
    }
}

private fun NavHostController.navigateToTab(route: String) {
    navigate(route) {
        popUpTo(Routes.CHALLENGE) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}

@Composable
private fun MissingContent(onBack: () -> Unit) {
    // Örn. dal değiştikten sonra eski bir ekrana dönüldüğünde.
    LaunchedEffect(Unit) { onBack() }
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        TextButton(onClick = onBack) { Text("Geri dön") }
    }
}
