# kotlinx.serialization: core modülündeki içerik (core.model) ve ses planı (core.voice) modelleri JSON'dan okunur.
# Derleyicinin ürettiği serializer sınıfları ve Companion.serializer() R8 tarafından silinmemeli.
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.**
-keep,includedescriptorclasses class com.fightedu.core.**$$serializer { *; }
-keepclassmembers class com.fightedu.core.** {
    *** Companion;
}
-keepclasseswithmembers class com.fightedu.core.** {
    kotlinx.serialization.KSerializer serializer(...);
}

# Hata ayıklama için satır numaraları korunur, kaynak dosya adı gizlenir.
-keepattributes SourceFile, LineNumberTable
-renamesourcefileattribute SourceFile
