---
name: android-security
description: |
  Android security fundamentals: encrypted storage (EncryptedSharedPreferences, EncryptedFile),
  biometric authentication (BiometricPrompt, Credential Manager), network certificate pinning,
  SafetyNet/Play Integrity API, KeyStore-backed key generation, and secure data handling patterns.
  Use this when: storing sensitive data locally, implementing biometric login, pinning TLS
  certificates, protecting API keys, integrating Play Integrity attestation, generating
  cryptographic keys in Android KeyStore, or hardening an app against reverse engineering.
license: Apache-2.0
metadata:
  author: Drew Fairweather
  last-updated: '2026-05-10'
  based-on: https://github.com/android/skills
  keywords:
  - security
  - EncryptedSharedPreferences
  - BiometricPrompt
  - Credential Manager
  - KeyStore
  - certificate pinning
  - Play Integrity
  - encryption
  - authentication
  - biometrics
  - OkHttp
  - network security
---

> **Lineage:** Built upon and expanded from the official Android group skills repository at
> [github.com/android/skills](https://github.com/android/skills). That repo covers areas where
> evaluations show LLMs underperform on standard Android patterns. This skill extends that
> foundation into Android security patterns — an area the official set does not cover.

## Overview

Android security mistakes cluster around three areas:
1. **Storage**: plaintext SharedPreferences for tokens/keys
2. **Authentication**: rolling custom biometric flows instead of using platform APIs
3. **Network**: missing or mis-implemented certificate pinning

This skill covers the correct platform-provided solution for each.

## Encrypted Storage

### EncryptedSharedPreferences

```kotlin
// libs.versions.toml
[libraries]
security-crypto = { group = "androidx.security", name = "crypto", version = "1.1.0-alpha06" }
```

```kotlin
fun createEncryptedPrefs(context: Context): SharedPreferences {
    val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    return EncryptedSharedPreferences.create(
        context,
        "secure_prefs",                                    // file name
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
}
```

Use exactly like `SharedPreferences` — the encryption is transparent:

```kotlin
prefs.edit {
    putString("auth_token", token)
    putString("refresh_token", refreshToken)
}
val token = prefs.getString("auth_token", null)
```

Never store tokens in regular `SharedPreferences` — the file is readable on rooted devices and
in ADB backups if `android:allowBackup="true"`.

### EncryptedFile

For encrypting arbitrary files (e.g., exported data, cached sensitive content):

```kotlin
fun createEncryptedFile(context: Context, fileName: String): EncryptedFile {
    val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    return EncryptedFile.Builder(
        context,
        File(context.filesDir, fileName),
        masterKey,
        EncryptedFile.FileEncryptionScheme.AES256_GCM_HKDF_4KB
    ).build()
}

// Write
encryptedFile.openFileOutput().use { output ->
    output.write(sensitiveData.toByteArray())
}

// Read
encryptedFile.openFileInput().use { input ->
    val bytes = input.readBytes()
}
```

## Android KeyStore — Cryptographic Keys

Generate keys that never leave the secure hardware enclave:

```kotlin
fun generateKeyStoreKey(alias: String, requireUserAuth: Boolean = true) {
    val keyGenSpec = KeyGenParameterSpec.Builder(
        alias,
        KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
    )
        .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
        .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
        .setKeySize(256)
        .setUserAuthenticationRequired(requireUserAuth)
        .setUserAuthenticationParameters(
            30,                                          // valid for 30 seconds after auth
            KeyProperties.AUTH_BIOMETRIC_STRONG or KeyProperties.AUTH_DEVICE_CREDENTIAL
        )
        .build()

    KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        .apply { init(keyGenSpec) }
        .generateKey()
}

fun getKeyStoreKey(alias: String): SecretKey {
    val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
    return (keyStore.getEntry(alias, null) as KeyStore.SecretKeyEntry).secretKey
}
```

## Biometric Authentication

### BiometricPrompt (Activity/Fragment)

```kotlin
fun showBiometricPrompt(
    activity: FragmentActivity,
    onSuccess: (BiometricPrompt.AuthenticationResult) -> Unit,
    onError: (Int, CharSequence) -> Unit
) {
    val executor = ContextCompat.getMainExecutor(activity)
    val callback = object : BiometricPrompt.AuthenticationCallback() {
        override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) = onSuccess(result)
        override fun onAuthenticationError(errorCode: Int, errString: CharSequence) = onError(errorCode, errString)
        override fun onAuthenticationFailed() { /* finger not recognized, prompt stays open */ }
    }

    val prompt = BiometricPrompt(activity, executor, callback)
    val info = BiometricPrompt.PromptInfo.Builder()
        .setTitle("Authenticate")
        .setSubtitle("Confirm your identity to continue")
        .setAllowedAuthenticators(
            BiometricManager.Authenticators.BIOMETRIC_STRONG or
            BiometricManager.Authenticators.DEVICE_CREDENTIAL
        )
        .build()

    prompt.authenticate(info)
}
```

Check availability before showing the prompt:

```kotlin
fun isBiometricAvailable(context: Context): Boolean {
    val manager = BiometricManager.from(context)
    return manager.canAuthenticate(
        BiometricManager.Authenticators.BIOMETRIC_STRONG or
        BiometricManager.Authenticators.DEVICE_CREDENTIAL
    ) == BiometricManager.BIOMETRIC_SUCCESS
}
```

### Credential Manager (Passkeys + Biometric, API 34+)

For passkey/FIDO2 flows on Android 14+:

```kotlin
// libs.versions.toml
[libraries]
credentials = { group = "androidx.credentials", name = "credentials", version = "1.3.0" }
credentials-play = { group = "androidx.credentials", name = "credentials-play-services-auth", version = "1.3.0" }
```

```kotlin
suspend fun signInWithPasskey(activity: Activity): String? {
    val credentialManager = CredentialManager.create(activity)

    val request = GetCredentialRequest(
        listOf(
            GetPublicKeyCredentialOption(
                requestJson = createGetCredentialJson()  // FIDO2 assertion JSON from server
            )
        )
    )

    return try {
        val result = credentialManager.getCredential(activity, request)
        when (val credential = result.credential) {
            is PublicKeyCredential -> credential.authenticationResponseJson
            else -> null
        }
    } catch (e: GetCredentialException) {
        null
    }
}
```

## Certificate Pinning (OkHttp)

Pin by certificate public key hash, not the leaf certificate (leaf rotates; public key stays stable):

```kotlin
fun buildPinnedOkHttpClient(): OkHttpClient {
    val pinner = CertificatePinner.Builder()
        // Get pins with: openssl s_client -connect api.example.com:443 | openssl x509 -pubkey -noout | openssl rsa -pubin -outform der | openssl dgst -sha256 -binary | base64
        .add("api.example.com", "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")  // leaf
        .add("api.example.com", "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=")  // intermediate (backup)
        .build()

    return OkHttpClient.Builder()
        .certificatePinner(pinner)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
}
```

Always pin at least 2 keys: the current leaf and an intermediate/backup. If you pin only the
leaf and it rotates before you ship an update, all existing installs are bricked.

## Network Security Config

Restrict cleartext traffic and add certificate trust anchors declaratively:

```xml
<!-- res/xml/network_security_config.xml -->
<network-security-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>

    <!-- Debug only: allow cleartext to localhost -->
    <debug-overrides>
        <trust-anchors>
            <certificates src="user" />
        </trust-anchors>
    </debug-overrides>
</network-security-config>
```

```xml
<!-- AndroidManifest.xml -->
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ...>
```

## Play Integrity API

Attest that the app is genuine and running on an unmodified device:

```kotlin
// libs.versions.toml
[libraries]
play-integrity = { group = "com.google.android.play", name = "integrity", version = "1.4.0" }
```

```kotlin
suspend fun requestIntegrityToken(
    context: Context,
    nonce: String      // server-generated, base64url-encoded, >16 bytes
): String? {
    val manager = IntegrityManagerFactory.create(context)
    val request = IntegrityTokenRequest.builder()
        .setNonce(nonce)
        .setCloudProjectNumber(123456789L)   // from Google Cloud Console
        .build()

    return try {
        val response = manager.requestIntegrityToken(request).await()
        response.token()   // send to your server for verification
    } catch (e: IntegrityServiceException) {
        null
    }
}
```

The token is verified server-side via the Play Integrity API — never trust the device's own
assertion of its integrity.

## Secrets — Never in Code or Resources

API keys, client secrets, and tokens must never appear in:
- Source files (hardcoded strings)
- `res/values/strings.xml`
- `local.properties` committed to git
- `BuildConfig` fields generated from `local.properties` (visible in APK)

Safe approaches:
1. **Runtime fetch**: retrieve from your backend after authentication
2. **Android KeyStore**: generate keys on device, never transmit secrets
3. **Secrets Gradle Plugin**: obfuscates BuildConfig fields (raises the bar, not a security guarantee)

## ProGuard / R8 Rules for Security Libraries

```proguard
# Preserve Credential Manager
-keep class androidx.credentials.** { *; }
-keep class com.google.android.libraries.identity.** { *; }

# Preserve Play Integrity
-keep class com.google.android.play.core.integrity.** { *; }
```

## Anti-Patterns

| Symptom | Root cause | Fix |
|---|---|---|
| `KeyStoreException: Invalid key` after app update | `setUserAuthenticationRequired(true)` key invalidated on biometric enrollment change | Catch `UserNotAuthenticatedException`, re-prompt, retry |
| Biometric prompt doesn't appear | `setNegativeButtonText` missing for BIOMETRIC_STRONG without DEVICE_CREDENTIAL | Either add negative button or add DEVICE_CREDENTIAL to allowed authenticators |
| Certificate pinning breaks in production | Pinned leaf cert rotated | Always pin intermediate CA as backup; monitor cert expiry |
| `EncryptedSharedPreferences` crash on first run | `MasterKey` not initialized before prefs creation | `MasterKey.Builder` call must precede `EncryptedSharedPreferences.create` |
| `android:allowBackup="true"` leaks prefs | ADB backup captures `shared_prefs/` | Set `android:allowBackup="false"` or use backup rules to exclude sensitive files |
| Play Integrity fails with `APP_NOT_INSTALLED` | Sideloaded or from unknown source | Expected for dev; in prod, ensure distribution via Play Store |
