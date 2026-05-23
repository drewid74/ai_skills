---
name: android-foreground-service
description: |
  Patterns for long-running Android foreground services used for continuous data collection —
  sensor streaming, BLE sessions, audio recording, or GPS logging that must survive Activity
  lifecycle changes. Covers Android 14+ mandatory foregroundServiceType, START_STICKY
  null-intent safety, notification channel setup, intent-based IPC, source fallback logic,
  and clean shutdown. Use this when: building a recording or sensor collection service, keeping
  BLE alive across screen rotation, handling Android 14 foregroundServiceType enforcement,
  wiring a Service to a Compose ViewModel, or implementing source-priority fallback.
license: Apache-2.0
metadata:
  author: Drew Fairweather
  last-updated: '2026-05-10'
  based-on: https://github.com/android/skills
  keywords:
  - foreground service
  - Android 14
  - UPSIDE_DOWN_CAKE
  - foregroundServiceType
  - START_STICKY
  - notification channel
  - BLE recording
  - sensor collection
  - StateFlow
  - data collection
---

> **Lineage:** Built upon and expanded from the official Android group skills repository at
> [github.com/android/skills](https://github.com/android/skills). The official set covers core
> Android patterns. This skill extends that foundation into long-running foreground data
> collection services — an area where LLMs consistently omit Android 14 type requirements and
> null-intent safety.

## Overview

The recommended pattern: a foreground service owns all hardware connections (BLE manager,
sensor listeners, location client) and exposes state via `StateFlow`. Activities and ViewModels
never hold hardware references — they issue `Intent` commands and observe published state.

## Manifest Declaration (Android 14+ required)

```xml
<service
    android:name=".service.DataCollectionService"
    android:foregroundServiceType="location"
    android:exported="false" />

<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_LOCATION" />
```

Android 14 (`UPSIDE_DOWN_CAKE`, API 34) **enforces** that `startForeground()` is called with a
type matching the manifest declaration. A mismatch throws `ForegroundServiceTypeNotAllowedException`
at runtime — not at compile time.

| Service purpose | `foregroundServiceType` |
|---|---|
| GPS / location recording | `location` |
| BLE data collection | `connectedDevice` |
| Camera / video capture | `camera` |
| Audio recording | `microphone` |
| Multiple (e.g. GPS + BLE) | `location\|connectedDevice` |

## startForeground with API-level guard

Call this **before any blocking work** — Android gives a 5-second window before ANR:

```kotlin
private fun startForegroundCompat(notification: Notification) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
        startForeground(
            NOTIFICATION_ID,
            notification,
            ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION
        )
    } else {
        startForeground(NOTIFICATION_ID, notification)
    }
}
```

## START_STICKY null-intent safety

Android may restart a `START_STICKY` service after process death with a `null` intent.
Handle this as the first check in `onStartCommand`:

```kotlin
override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
    // Satisfy the foreground window immediately — always, before any other work.
    startForegroundCompat(buildNotification("Tap to resume", 0))

    if (intent == null) {
        // Process-death restart with no context. Stop cleanly; the UI will
        // re-issue the correct action intent when the user re-opens the app.
        stopSelf()
        return START_NOT_STICKY
    }

    when (intent.action) {
        ACTION_START    -> startCollection(intent)
        ACTION_STOP     -> stopCollection()
        ACTION_UPGRADE  -> upgradeSource(intent)
        else            -> stopSelf()
    }
    return START_STICKY
}
```

## Intent-based IPC (no binding required)

Use `Context.startForegroundService(intent)` for commands. Expose state via `companion object`
`StateFlow`s that any observer can collect without binding:

```kotlin
class DataCollectionService : Service() {
    companion object {
        private val _status = MutableStateFlow<CollectionStatus>(CollectionStatus.Idle)
        val status: StateFlow<CollectionStatus> = _status.asStateFlow()

        private val _sampleCount = MutableStateFlow(0)
        val sampleCount: StateFlow<Int> = _sampleCount.asStateFlow()

        const val ACTION_START   = "com.example.service.START"
        const val ACTION_STOP    = "com.example.service.STOP"
        const val ACTION_UPGRADE = "com.example.service.UPGRADE"
    }
}
```

ViewModel observes without binding:
```kotlin
class RecordingViewModel : ViewModel() {
    val status = DataCollectionService.status
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), CollectionStatus.Idle)

    fun start(context: Context) {
        context.startForegroundService(
            Intent(context, DataCollectionService::class.java).apply { action = ACTION_START }
        )
    }
}
```

Always use `startForegroundService()` — `startService()` throws on API 26+ when the service
calls `startForeground()` after starting from a background state.

## Source Priority / Fallback

Services that support multiple data sources (e.g., external BLE device with phone sensor
fallback) should own all source-switching logic internally:

```kotlin
private fun startCollection(intent: Intent) {
    val externalDeviceAddress = intent.getStringExtra(EXTRA_DEVICE_ADDRESS)
    if (externalDeviceAddress != null) {
        connectExternal(externalDeviceAddress)
    } else {
        startInternalSensors()
    }
}

private fun connectExternal(address: String) {
    serviceScope.launch {
        bleManager.connect(getDevice(address))
            .done { _status.value = CollectionStatus.CollectingBle }
            .fail { _, _ ->
                Log.w(TAG, "External device unavailable, falling back to internal sensors")
                startInternalSensors()
            }
            .enqueue()
    }
}
```

## Notification Channel Setup

Create the channel in `Application.onCreate()`, not in the Service. Channel creation is
idempotent — safe to call multiple times:

```kotlin
override fun onCreate() {
    super.onCreate()
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        NotificationChannel(
            CHANNEL_ID,
            getString(R.string.collection_channel_name),
            NotificationManager.IMPORTANCE_LOW   // No sound; appropriate for persistent recording
        ).apply {
            setShowBadge(false)
            getSystemService(NotificationManager::class.java).createNotificationChannel(this)
        }
    }
}
```

Update the notification content as progress accumulates — but throttle to ~1Hz:
```kotlin
private fun updateNotification(count: Int) {
    notificationManager.notify(
        NOTIFICATION_ID,
        NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Collecting data")
            .setContentText("$count samples")
            .setSmallIcon(R.drawable.ic_recording)
            .setOngoing(true)
            .setOnlyAlertOnce(true)   // Suppress re-notification on every update
            .build()
    )
}
```

## Clean Shutdown

```kotlin
private fun stopCollection() {
    serviceScope.launch {
        bleManager.disconnect().enqueue()
        internalSensorManager.stop()
        flushPendingWrites()                   // flush before stopSelf — see telemetry-pipeline skill
        _status.value = CollectionStatus.Idle
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }
}
```

Never rely on `onDestroy()` for data persistence — the process can be killed between
`stopSelf()` and `onDestroy()`.

## Anti-Patterns

| Symptom | Root cause | Fix |
|---|---|---|
| `ForegroundServiceTypeNotAllowedException` (API 34) | Type missing from manifest `<service>` | Add matching `foregroundServiceType` attribute |
| ANR "did not call startForeground()" | Work executed before `startForeground()` | Call `startForegroundCompat()` as the first line of `onStartCommand` |
| Service restarts in broken state | `START_STICKY` without null-intent guard | Return `START_NOT_STICKY` after `stopSelf()` on null intent |
| Crash from background on API 26+ | `startService()` instead of `startForegroundService()` | Always use `startForegroundService()` |
| Lost data on unexpected kill | Flushing only in `onDestroy` | Flush in the stop-action handler before `stopSelf()` |
| Notification re-alerts on every update | Missing `setOnlyAlertOnce(true)` | Add to `NotificationCompat.Builder` |
