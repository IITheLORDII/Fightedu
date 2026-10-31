package com.fightedu

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.fightedu.ui.FightEduRoot
import com.fightedu.ui.MainViewModel

class MainActivity : ComponentActivity() {
    private val vm: MainViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        // amblemli sistem açılış ekranı: içerik ve oturum yüklenene kadar ekranda kalır
        installSplashScreen().setKeepOnScreenCondition { vm.state.value.isLoading }
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent { FightEduRoot(vm) }
    }
}
