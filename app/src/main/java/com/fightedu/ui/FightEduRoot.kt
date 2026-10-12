package com.fightedu.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.CircularProgressIndicator
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
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
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
import com.fightedu.ui.home.HomeScreen
import com.fightedu.ui.library.LibraryScreen
import com.fightedu.ui.library.MoveDetailScreen
import com.fightedu.ui.onboarding.OnboardingScreen
import com.fightedu.ui.player.PlayerScreen
import com.fightedu.ui.program.ProgramScreen
import com.fightedu.ui.session.SessionDetailScreen
import com.fightedu.ui.settings.SettingsScreen
import com.fightedu.ui.theme.DefaultAccent
import com.fightedu.ui.theme.FightEduTheme
import com.fightedu.ui.theme.parseColor

private object Routes {
    const val ONBOARDING = "onboarding"
    const val HOME = "home"
    const val PROGRAM = "program"
    const val LIBRARY = "library"
    const val SETTINGS = "settings"
    const val SESSION = "session/{week}/{index}"
    const val PLAYER = "player/{week}/{index}"
    const val MOVE = "move/{id}"

    fun session(week: Int, index: Int) = "session/$week/$index"
    fun player(week: Int, index: Int) = "player/$week/$index"
    fun move(id: String) = "move/$id"
}

private data class Tab(val route: String, val label: String, val icon: ImageVector)

private val TABS = listOf(
    Tab(Routes.HOME, "Ana Sayfa", Icons.Filled.Home),
    Tab(Routes.PROGRAM, "Program", Icons.Filled.DateRange),
    Tab(Routes.LIBRARY, "Hareketler", Icons.AutoMirrored.Filled.List),
    Tab(Routes.SETTINGS, "Ayarlar", Icons.Filled.Settings),
)

@Composable
fun FightEduRoot(vm: MainViewModel = viewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()
    var previewSportId by rememberSaveable { mutableStateOf<String?>(null) }
    val accentHex = state.sport?.colorHex ?: previewSportId?.let { state.content?.sport(it)?.colorHex }

    FightEduTheme(accent = parseColor(accentHex) ?: DefaultAccent) {
        Surface(color = MaterialTheme.colorScheme.background, modifier = Modifier.fillMaxSize()) {
            when {
                state.isLoading -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
                state.content == null -> ErrorView(state.error ?: "İçerik yüklenemedi")
                else -> AppNavigation(state, vm, onPreviewSport = { previewSportId = it })
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
private fun AppNavigation(state: UiState, vm: MainViewModel, onPreviewSport: (String?) -> Unit) {
    val content = requireNotNull(state.content)
    val nav = rememberNavController()
    val startRoute = remember { if (state.plan == null) Routes.ONBOARDING else Routes.HOME }
    val backStack by nav.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route
    val showBottomBar = TABS.any { it.route == currentRoute }

    fun restartToOnboarding() {
        nav.navigate(Routes.ONBOARDING) { popUpTo(nav.graph.id) { inclusive = true } }
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
        NavHost(navController = nav, startDestination = startRoute, modifier = Modifier.padding(inner)) {
            composable(Routes.ONBOARDING) {
                OnboardingScreen(
                    content = content,
                    onSportPreview = onPreviewSport,
                    onCreate = { config ->
                        vm.startPlan(config) {
                            nav.navigate(Routes.HOME) { popUpTo(nav.graph.id) { inclusive = true } }
                        }
                    },
                )
            }
            composable(Routes.HOME) {
                HomeScreen(
                    state = state,
                    onOpenSession = { nav.navigate(Routes.session(it.week, it.index)) },
                    onStartSession = { nav.navigate(Routes.player(it.week, it.index)) },
                    onNewProgram = { vm.resetPlan { restartToOnboarding() } },
                )
            }
            composable(Routes.PROGRAM) {
                ProgramScreen(state = state, onOpenSession = { nav.navigate(Routes.session(it.week, it.index)) })
            }
            composable(Routes.LIBRARY) {
                LibraryScreen(
                    content = content,
                    defaultSportId = state.plan?.sportId,
                    onOpenMove = { nav.navigate(Routes.move(it.id)) },
                )
            }
            composable(Routes.SETTINGS) {
                SettingsScreen(
                    state = state,
                    onSetReminder = vm::setReminder,
                    onResetPlan = { vm.resetPlan { restartToOnboarding() } },
                )
            }
            composable(
                Routes.SESSION,
                arguments = listOf(navArgument("week") { type = NavType.IntType }, navArgument("index") { type = NavType.IntType }),
            ) { entry ->
                val args = requireNotNull(entry.arguments)
                val session = state.session(args.getInt("week"), args.getInt("index"))
                if (session == null) {
                    MissingContent { nav.popBackStack() }
                } else {
                    SessionDetailScreen(
                        session = session,
                        completed = session.key in state.completed,
                        onBack = { nav.popBackStack() },
                        onStart = { nav.navigate(Routes.player(session.week, session.index)) },
                        onToggleCompleted = { vm.setCompleted(session.key, it) },
                        onOpenMove = { nav.navigate(Routes.move(it.id)) },
                    )
                }
            }
            composable(
                Routes.PLAYER,
                arguments = listOf(navArgument("week") { type = NavType.IntType }, navArgument("index") { type = NavType.IntType }),
            ) { entry ->
                val args = requireNotNull(entry.arguments)
                val session = state.session(args.getInt("week"), args.getInt("index"))
                if (session == null) {
                    MissingContent { nav.popBackStack() }
                } else {
                    PlayerScreen(
                        session = session,
                        onExit = { nav.popBackStack() },
                        onCompleted = { vm.setCompleted(session.key, true) },
                        onDone = { if (!nav.popBackStack(Routes.HOME, inclusive = false)) nav.popBackStack() },
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
        popUpTo(Routes.HOME) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
}

@Composable
private fun MissingContent(onBack: () -> Unit) {
    // Örn. program sıfırlandıktan sonra eski bir ekrana dönüldüğünde.
    LaunchedEffect(Unit) { onBack() }
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        TextButton(onClick = onBack) { Text("Geri dön") }
    }
}
