package com.fightedu.core

import com.fightedu.core.content.ContentLibrary
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class ContentLibraryTest {
    private val library = TestContent.library

    @Test
    fun `beş dal yüklenir`() {
        assertEquals(listOf("boxing", "kickboxing", "wrestling", "taekwondo", "general"), library.sports.map { it.id })
    }

    @Test
    fun `içerik tutarlı ve her hareketin videosu ile kapak resmi var`() {
        val errors = library.validate { File(TestContent.assetsDir, it).isFile }
        assertTrue(errors.joinToString("\n"), errors.isEmpty())
    }

    @Test
    fun `her dalın 24 antrenman günlük programı ve yeterli hareketi var`() {
        for (sport in library.sports) {
            val program = library.program(sport.id)!!
            assertEquals(ContentLibrary.TOTAL_DAYS, program.totalDays)
            assertEquals(4, program.phases.size)
            assertTrue("${sport.id} hareket sayısı", library.movesForSport(sport.id).size >= 11)
        }
    }

    @Test
    fun `genel hareketler bir kez yüklenir ve dinlenme günü kısa`() {
        assertEquals(11, library.movesForSport(ContentLibrary.GENERAL).size)
        val rest = library.restDay!!
        val min = com.fightedu.core.domain.TrainingPlanner(library).estimatedMinutes(rest)
        assertTrue("dinlenme $min dk", min in ContentLibrary.REST_MIN_MINUTES..ContentLibrary.REST_MAX_MINUTES)
    }
}
