package com.fightedu.health

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.fightedu.ui.privacy.PrivacyPolicyScreen
import com.fightedu.ui.theme.FightEduTheme

/**
 * Health Connect izin ekranındaki "gizlilik politikası" bağlantısının açtığı sayfa (Health Connect bunu zorunlu tutar).
 * Yalnızca sabit metin gösterir; gelen niyetten veri okumaz, sonuç döndürmez.
 */
class PrivacyPolicyActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent { FightEduTheme { PrivacyPolicyScreen(onBack = ::finish) } }
    }
}
