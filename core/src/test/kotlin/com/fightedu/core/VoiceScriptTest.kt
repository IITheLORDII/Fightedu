package com.fightedu.core

import com.fightedu.core.voice.TurkishNumbers
import com.fightedu.core.voice.VoiceScript
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class VoiceScriptTest {
    private val library = TestContent.library
    private val voice = VoiceScript.load(library.sports.map { it.id }) { path ->
        File(TestContent.assetsDir, path).takeIf { it.isFile }?.readText()
    }

    @Test
    fun `ses planları oynatıcının adımlarıyla birebir eşleşir`() {
        assertNotNull("assets/voice yok", voice)
        val errors = voice!!.validate(library)
        assertTrue(errors.take(20).joinToString("\n"), errors.isEmpty())
    }

    @Test
    fun `her klibin ses dosyası ya var ya da hiçbiri yok (TTS yedeği)`() {
        val v = voice!!
        val present = v.manifest.clips.keys.count { File(TestContent.assetsDir, VoiceScript.clipAsset(it)).isFile }
        assertTrue("$present / ${v.manifest.clips.size} klip dosyası var", present == 0 || present == v.manifest.clips.size)
        v.manifest.clips.values.forEach { c ->
            assertTrue("boş metin", c.text.isNotBlank() && c.say.isNotBlank())
            assertTrue("rakam okunmamalı: ${c.say}", c.say.none { it.isDigit() })
        }
    }

    @Test
    fun `türkçe sayılar`() {
        assertEquals("kırk beş", TurkishNumbers.cardinal(45))
        assertEquals("yüz yirmi", TurkishNumbers.cardinal(120))
        assertEquals("üçüncü", TurkishNumbers.ordinal(3))
        assertEquals("on dördüncü", TurkishNumbers.ordinal(14))
        assertEquals("bir buçuk dakika", TurkishNumbers.duration(90))
        assertEquals("kırk beş saniye", TurkishNumbers.duration(45))
        assertEquals("üç dakika", TurkishNumbers.duration(180))
    }
}
