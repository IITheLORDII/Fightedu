package com.fightedu.ui.health

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import com.fightedu.core.health.HealthAvailability
import com.fightedu.health.HealthConnectGateway

/**
 * "Sağlık uygulamasına bağlan" eylemi: Health Connect kurulu değilse ya da eskiyse Play Store sayfasını açar,
 * kuruluysa tüm izinleri tek bir sistem ekranında ister. Ekrandan dönünce [onResult] çağrılır.
 */
@Composable
fun rememberHealthConnect(availability: HealthAvailability, onResult: () -> Unit): () -> Unit {
    val context = LocalContext.current
    val launcher = rememberLauncherForActivityResult(HealthConnectGateway.permissionContract()) { onResult() }
    return remember(availability, launcher) {
        {
            when (availability) {
                HealthAvailability.AVAILABLE -> launcher.launch(HealthConnectGateway.PERMISSIONS)
                else -> context.startSafely(HealthConnectGateway.installIntent())
            }
        }
    }
}

/** Health Connect ayarları (izinler ve Samsung Health senkronu). */
fun openHealthConnectSettings(context: Context) = context.startSafely(HealthConnectGateway.settingsIntent())

private fun Context.startSafely(intent: Intent) {
    try {
        startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    } catch (_: ActivityNotFoundException) {
        // Play Store ya da Health Connect ayarları yoksa sessizce geç (ör. Play'siz cihazlar)
    } catch (_: SecurityException) {
    }
}
