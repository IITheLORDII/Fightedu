package com.fightedu.ui.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fightedu.core.auth.AccountRules
import com.fightedu.data.AuthResult
import com.fightedu.ui.components.BrandBackground
import com.fightedu.ui.components.Emblem

/** Kayıt formu. Misafir oturumu açıksa hesap misafirin ilerlemesini devralır. */
@Composable
fun RegisterScreen(
    upgradingGuest: Boolean,
    onBack: () -> Unit,
    onSubmit: (name: String, email: String, password: String, onResult: (AuthResult) -> Unit) -> Unit,
    onSuccess: () -> Unit,
    onGoLogin: () -> Unit,
) {
    var name by rememberSaveable { mutableStateOf("") }
    var email by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    var confirm by rememberSaveable { mutableStateOf("") }
    var errors by rememberSaveable { mutableStateOf(mapOf<String, String>()) }
    var busy by rememberSaveable { mutableStateOf(false) }
    val focus = LocalFocusManager.current

    fun submit() {
        val e = AccountRules.validateRegister(name, email, password, confirm)
        errors = buildMap {
            e.name?.let { put("name", it) }
            e.email?.let { put("email", it) }
            e.password?.let { put("password", it) }
            e.confirm?.let { put("confirm", it) }
        }
        if (!e.isValid || busy) return
        busy = true
        focus.clearFocus()
        onSubmit(name, email, password) { r ->
            busy = false
            when (r) {
                is AuthResult.Success -> onSuccess()
                is AuthResult.Failure -> { errors = mapOf(r.field.key to r.message) }
            }
        }
    }

    AuthFrame(
        title = if (upgradingGuest) "Hesabını oluştur" else "Hesap oluştur",
        subtitle = if (upgradingGuest) {
            "Misafir olarak yaptığın ilerleme bu hesaba aktarılır."
        } else {
            "İlerlemen, serin ve seçtiğin dal hesabına kaydedilir."
        },
        onBack = onBack,
    ) {
        Field(name, { name = it; errors = errors - "name" }, "Adın", errors["name"],
            KeyboardOptions(capitalization = KeyboardCapitalization.Words, imeAction = ImeAction.Next),
            onNext = { focus.moveFocus(FocusDirection.Down) })
        Field(email, { email = it; errors = errors - "email" }, "E-posta", errors["email"],
            KeyboardOptions(keyboardType = KeyboardType.Email, imeAction = ImeAction.Next),
            onNext = { focus.moveFocus(FocusDirection.Down) })
        PasswordField(password, { password = it; errors = errors - "password" }, "Şifre (en az ${AccountRules.MIN_PASSWORD} karakter)",
            errors["password"], ImeAction.Next) { focus.moveFocus(FocusDirection.Down) }
        PasswordField(confirm, { confirm = it; errors = errors - "confirm" }, "Şifre tekrar", errors["confirm"],
            ImeAction.Done) { submit() }
        errors["general"]?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        LocalNote()
        PrimaryButton(if (upgradingGuest) "Hesabı oluştur" else "Kayıt ol", busy) { submit() }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {
            Text("Zaten hesabın var mı?", color = MaterialTheme.colorScheme.onSurfaceVariant)
            TextButton(onClick = onGoLogin) { Text("Giriş yap", fontWeight = FontWeight.Bold) }
        }
    }
}

@Composable
fun LoginScreen(
    onBack: () -> Unit,
    onSubmit: (email: String, password: String, onResult: (AuthResult) -> Unit) -> Unit,
    onSuccess: () -> Unit,
    onGoRegister: () -> Unit,
) {
    var email by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    var errors by rememberSaveable { mutableStateOf(mapOf<String, String>()) }
    var busy by rememberSaveable { mutableStateOf(false) }
    var showForgot by rememberSaveable { mutableStateOf(false) }
    val focus = LocalFocusManager.current

    fun submit() {
        errors = buildMap {
            AccountRules.emailError(email)?.let { put("email", it) }
            if (password.isEmpty()) put("password", "Şifreni yaz.")
        }
        if (errors.isNotEmpty() || busy) return
        busy = true
        focus.clearFocus()
        onSubmit(email, password) { r ->
            busy = false
            when (r) {
                is AuthResult.Success -> onSuccess()
                is AuthResult.Failure -> { errors = mapOf(r.field.key to r.message) }
            }
        }
    }

    AuthFrame(title = "Tekrar hoş geldin", subtitle = "Kaldığın günden devam et.", onBack = onBack) {
        Field(email, { email = it; errors = errors - "email" - "general" }, "E-posta", errors["email"],
            KeyboardOptions(keyboardType = KeyboardType.Email, imeAction = ImeAction.Next),
            onNext = { focus.moveFocus(FocusDirection.Down) })
        PasswordField(password, { password = it; errors = errors - "password" - "general" }, "Şifre",
            errors["password"], ImeAction.Done) { submit() }
        errors["general"]?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        TextButton(onClick = { showForgot = true }, modifier = Modifier.align(Alignment.End)) {
            Text("Şifremi unuttum")
        }
        PrimaryButton("Giriş yap", busy) { submit() }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {
            Text("Hesabın yok mu?", color = MaterialTheme.colorScheme.onSurfaceVariant)
            TextButton(onClick = onGoRegister) { Text("Hesap oluştur", fontWeight = FontWeight.Bold) }
        }
    }

    if (showForgot) {
        AlertDialog(
            onDismissRequest = { showForgot = false },
            title = { Text("Şifremi unuttum") },
            text = {
                Text(
                    "FightEdu hesapları yalnızca bu telefonda saklanır; bu yüzden e-postayla şifre sıfırlama yok. " +
                        "Şifreni hatırlayamıyorsan yeni bir hesap oluşturabilir ya da misafir olarak devam edebilirsin.",
                )
            },
            confirmButton = { TextButton(onClick = { showForgot = false }) { Text("Tamam") } },
        )
    }
}

private val AuthResult.Field.key: String
    get() = when (this) {
        AuthResult.Field.NAME -> "name"
        AuthResult.Field.EMAIL -> "email"
        AuthResult.Field.PASSWORD -> "password"
        AuthResult.Field.GENERAL -> "general"
    }

@Composable
private fun AuthFrame(
    title: String,
    subtitle: String,
    onBack: () -> Unit,
    content: @Composable androidx.compose.foundation.layout.ColumnScope.() -> Unit,
) {
    BrandBackground {
        Column(
            Modifier
                .fillMaxSize()
                .statusBarsPadding()
                .navigationBarsPadding()
                .imePadding()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            IconButton(onClick = onBack, modifier = Modifier.padding(top = 4.dp)) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Geri", tint = Color.White)
            }
            Emblem(Modifier.size(72.dp))
            Text(title, style = MaterialTheme.typography.headlineLarge, color = Color.White)
            Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(4.dp))
            content()
            Spacer(Modifier.height(16.dp))
        }
    }
}

@Composable
private fun Field(
    value: String,
    onChange: (String) -> Unit,
    label: String,
    error: String?,
    keyboard: KeyboardOptions,
    onNext: () -> Unit,
) {
    OutlinedTextField(
        value = value,
        onValueChange = onChange,
        label = { Text(label) },
        isError = error != null,
        supportingText = if (error != null) { { Text(error) } } else null,
        singleLine = true,
        keyboardOptions = keyboard,
        keyboardActions = KeyboardActions(onNext = { onNext() }),
        shape = RoundedCornerShape(14.dp),
        modifier = Modifier.fillMaxWidth(),
    )
}

@Composable
private fun PasswordField(
    value: String,
    onChange: (String) -> Unit,
    label: String,
    error: String?,
    ime: ImeAction,
    onIme: () -> Unit,
) {
    var visible by rememberSaveable { mutableStateOf(false) }
    OutlinedTextField(
        value = value,
        onValueChange = onChange,
        label = { Text(label) },
        isError = error != null,
        supportingText = if (error != null) { { Text(error) } } else null,
        singleLine = true,
        leadingIcon = { Icon(Icons.Filled.Lock, contentDescription = null) },
        trailingIcon = {
            TextButton(onClick = { visible = !visible }) { Text(if (visible) "Gizle" else "Göster") }
        },
        visualTransformation = if (visible) VisualTransformation.None else PasswordVisualTransformation(),
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password, imeAction = ime),
        keyboardActions = KeyboardActions(onNext = { onIme() }, onDone = { onIme() }),
        shape = RoundedCornerShape(14.dp),
        modifier = Modifier.fillMaxWidth(),
    )
}

@Composable
private fun LocalNote() {
    Text(
        "🔒 Hesabın bu telefonda saklanır; şifren şifrelenmiş (özetlenmiş) olarak tutulur.",
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
}

@Composable
private fun PrimaryButton(text: String, busy: Boolean, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        enabled = !busy,
        modifier = Modifier.fillMaxWidth().height(56.dp),
        shape = RoundedCornerShape(16.dp),
    ) {
        if (busy) {
            CircularProgressIndicator(Modifier.size(22.dp), strokeWidth = 2.5.dp, color = Color.White)
        } else {
            Text(text, fontSize = 17.sp, fontWeight = FontWeight.Bold)
        }
    }
}
