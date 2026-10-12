package com.fightedu.core

import com.fightedu.core.content.ContentLibrary
import java.io.File

object TestContent {
    val assetsDir: File = File(requireNotNull(System.getProperty("fightedu.assets")) { "fightedu.assets ayarlı değil" })

    val library: ContentLibrary by lazy {
        ContentLibrary.load { path -> File(assetsDir, path).readText() }
    }
}
