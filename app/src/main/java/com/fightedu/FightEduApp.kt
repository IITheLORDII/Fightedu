package com.fightedu

import android.app.Application
import com.fightedu.reminders.ReminderNotifications

class FightEduApp : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
        ReminderNotifications.createChannel(this)
    }
}

val android.content.Context.appContainer: AppContainer
    get() = (applicationContext as FightEduApp).container
