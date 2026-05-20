---
name: android-bluetooth
description: >
  Expert guidance for Android Bluetooth Classic (SPP/RFCOMM) and BLE development.
  Use this skill whenever the user is building, debugging, or architecting Android
  apps that connect to Bluetooth devices — including BluetoothSocket, RFCOMM, SPP,
  BLE, GATT, BluetoothAdapter, BluetoothDevice, bonded devices, paired devices,
  classic-vs-BLE transport selection, device scan routing, ACL disconnect, disconnect
  detection, reconnect loops, stuck Connecting UI, stale connected state, background
  Bluetooth, foreground service ownership of connection state, Android 12+ Bluetooth
  permissions, BLUETOOTH_SCAN, BLUETOOTH_CONNECT, Bluetooth connection dropping,
  Android app shows connected when it is not, OBDLink MX+ classic pairing, Veepeak BLE+
  routing, RaceBox Bluetooth lifecycle, or coroutine/state-machine bugs in Android
  Bluetooth connection management. Do not use for non-Android Bluetooth firmware or
  low-level ECU / PID parsing questions; use android-obd for ELM327 and OBD protocol work.
---

# Android Bluetooth Development Skill

Comprehensive guidance for building robust Bluetooth connections on Android — Classic
(SPP/RFCOMM) and BLE (GATT). Covers the full lifecycle: discovery → pairing → connect
→ init → read/write → disconnect detection → reconnect.

## Quick Reference — Which Path to Use

| Use Case | Transport | API |
|---|---|---|
| ELM327 / OBD adapters | Classic BT / SPP | RFCOMM + BluetoothSocket |
| Most serial/UART peripherals | Classic BT / SPP | RFCOMM + BluetoothSocket |
| GPS race trackers (RaceBox, Garmin GLO) | BLE | BluetoothGatt |
| Heart rate / fitness sensors | BLE | BluetoothGatt |
| Custom ESP32/Arduino | Either | Check device spec |

---

## Permissions — Android Version Matrix

This is the most common source of silent failures. Get this right first.

```xml
<!-- AndroidManifest.xml -->

<!-- Android 12+ (API 31+) — new granular permissions -->
<uses-permission android:name="android.permission.BLUETOOTH_SCAN"
    android:usesPermissionFlags="neverForLocation" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
<uses-permission android:name="android.permission.BLUETOOTH_ADVERTISE" />

<!-- Legacy — still required for API < 31 -->
<uses-permission android:name="android.permission.BLUETOOTH" />
<uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />

<!-- Required for discovery on API < 31 — NOT needed if neverForLocation flag set -->
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />

<!-- Android 14+ foreground service type — mandatory for connected device services -->
<uses-permission android:name="android.permission.FOREGROUND_SERVICE_CONNECTED_DEVICE" />
```

```kotlin
// Runtime permission request — Android 12+
val permissions = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
    arrayOf(
        Manifest.permission.BLUETOOTH_SCAN,
        Manifest.permission.BLUETOOTH_CONNECT,
    )
} else {
    arrayOf(
        Manifest.permission.BLUETOOTH,
        Manifest.permission.ACCESS_FINE_LOCATION,
    )
}
ActivityCompat.requestPermissions(activity, permissions, REQUEST_CODE)
```

---

## Classic Bluetooth / SPP / RFCOMM

### Device Discovery vs Bonded Devices

For SPP devices (OBD, serial peripherals): **enumerate bonded devices, don't scan**.
Scanning finds unconnected devices; bonded devices are already paired and ready for RFCOMM.

```kotlin
val bluetoothAdapter = BluetoothAdapter.getDefaultAdapter()
    ?: error("No Bluetooth adapter")

// Cancel any active discovery — MUST do this before connect
bluetoothAdapter.cancelDiscovery()

val device = bluetoothAdapter.bondedDevices
    .firstOrNull { it.name?.contains("OBDLink", ignoreCase = true) == true }
    ?: error("Device not found in bonded list")
```

### Connection — Three Paths in Priority Order

Most Android SPP bugs come from using the wrong socket creation method. Try in this order:

```kotlin
// Path 1 (recommended): Reflection — bypasses SDP lookup, most reliable
// This is what works when standard paths fail on many devices
fun createReflectionSocket(device: BluetoothDevice, channel: Int = 1): BluetoothSocket {
    val method = device.javaClass.getMethod("createRfcommSocket", Int::class.java)
    return method.invoke(device, channel) as BluetoothSocket
}

// Path 2: Secure RFCOMM via service record (standard API)
fun createSecureSocket(device: BluetoothDevice): BluetoothSocket =
    device.createRfcommSocketToServiceRecord(SPP_UUID)

// Path 3: Insecure RFCOMM (no auth — some devices require this)
fun createInsecureSocket(device: BluetoothDevice): BluetoothSocket =
    device.createInsecureRfcommSocketToServiceRecord(SPP_UUID)

val SPP_UUID: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
```

### Connect with Retry and Teardown

```kotlin
// CRITICAL: Always close previous socket before retrying
// After a failed connect, wait 500ms for the L2CAP channel to fully teardown
// before creating a new socket — skipping this causes the next attempt to fail

suspend fun connectWithRetry(device: BluetoothDevice): BluetoothSocket =
    withContext(Dispatchers.IO) {
        var lastSocket: BluetoothSocket? = null

        val socketFactories = listOf(
            { createReflectionSocket(device, 1) },
            { createSecureSocket(device) },
            { createInsecureSocket(device) },
        )

        for (factory in socketFactories) {
            try {
                lastSocket?.close()
                delay(500) // stack settle after close
                
                bluetoothAdapter.cancelDiscovery() // always cancel before connect
                
                val socket = factory()
                socket.connect() // blocks until connected or throws
                return@withContext socket
            } catch (e: IOException) {
                Log.w(TAG, "Socket path failed: ${e.message}")
                lastSocket = null
            }
        }
        throw IOException("All RFCOMM paths failed")
    }
```

---

## Disconnect Detection — Three-Layer Pattern

Android's `BluetoothSocket.isConnected` is **useless** for detecting remote disconnect —
it returns the last known state, not actual socket health. `ACTION_ACL_DISCONNECTED`
fires late (5-30s) or not at all on many devices. The only reliable detection is I/O.

### Layer 1 — Read Loop (primary)

```kotlin
private fun startReadLoop(socket: BluetoothSocket) {
    scope.launch(Dispatchers.IO) {
        try {
            val reader = socket.inputStream.bufferedReader()
            while (isActive) {
                val line = reader.readLine() ?: break // null = stream closed
                handleResponse(line)
            }
        } catch (e: IOException) {
            // This is how you know the connection is dead
            Log.i(TAG, "Read loop ended: ${e.message}")
            handleDisconnect("read loop IOException")
        }
    }
}
```

### Layer 2 — Heartbeat Writer

```kotlin
private var heartbeatJob: Job? = null

fun startHeartbeat() {
    heartbeatJob = scope.launch {
        while (isActive) {
            delay(5_000)
            if (!sendHeartbeat()) {
                handleDisconnect("heartbeat failed")
                break
            }
        }
    }
}

private fun sendHeartbeat(): Boolean = try {
    // For ELM327: "AT\r" returns "OK" or "?" — either proves socket is alive
    writeToSocket("AT\r")
    true
} catch (e: IOException) {
    false
}
```

### Layer 3 — ACL Broadcast Receiver (backup)

```kotlin
private val aclReceiver = object : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == BluetoothDevice.ACTION_ACL_DISCONNECTED) {
            val device = intent.getParcelableExtra<BluetoothDevice>(
                BluetoothDevice.EXTRA_DEVICE
            )
            if (device?.address == connectedDevice?.address) {
                handleDisconnect("ACL_DISCONNECTED broadcast")
            }
        }
    }
}

// Register in service onCreate:
registerReceiver(aclReceiver, IntentFilter(BluetoothDevice.ACTION_ACL_DISCONNECTED))

// Unregister in onDestroy:
unregisterReceiver(aclReceiver)
```

### handleDisconnect — Must Be Idempotent

All three layers can fire in rapid succession. Guard against double-execution:

```kotlin
private val disconnecting = AtomicBoolean(false)

private fun handleDisconnect(reason: String) {
    if (!disconnecting.compareAndSet(false, true)) return // already handling
    
    Log.i(TAG, "Disconnect: $reason")
    heartbeatJob?.cancel()
    try { socket?.close() } catch (e: Exception) { }
    socket = null
    _state.value = ConnectionState.DISCONNECTED
    broadcastDisconnected()
    disconnecting.set(false)
}
```

---

## State Machine

Never use boolean flags for connection state. Use a sealed class or enum:

```kotlin
enum class ConnectionState {
    DISCONNECTED,
    BONDING,        // waiting for OS pairing
    CONNECTING,     // BluetoothSocket.connect() in progress
    INITIALIZING,   // socket open, running init sequence (ATZ, ATE0, etc.)
    CONNECTED,      // init complete, ready for commands
}

// Only transition to CONNECTED after init sequence completes successfully
// Never skip INITIALIZING — even for "saved" / previously-known devices
// A saved device skips discovery, NOT initialization
```

---

## Foreground Service — Android 14+ Requirements

Bluetooth connections die when your app is backgrounded unless you use a foreground service.
Android 14 added mandatory `connectedDevice` service type.

```xml
<!-- AndroidManifest.xml -->
<service
    android:name=".BluetoothService"
    android:foregroundServiceType="connectedDevice"
    android:exported="false" />
```

```kotlin
// In service onStartCommand — show notification before connecting
val notification = NotificationCompat.Builder(this, CHANNEL_ID)
    .setContentTitle("OBD Connected")
    .setSmallIcon(R.drawable.ic_bluetooth)
    .build()

startForeground(NOTIFICATION_ID, notification,
    ServiceInfo.FOREGROUND_SERVICE_TYPE_CONNECTED_DEVICE)
```

---

## BLE / GATT

See `references/ble-gatt.md` for full BLE guidance including:
- GATT service/characteristic discovery
- Notification subscription
- MTU negotiation
- Race tracker GATT profiles (RaceChrono DIY, NMEA over BLE, Nordic UART)

---

## Common Failure Patterns and Fixes

| Symptom | Cause | Fix |
|---|---|---|
| `read failed, socket might closed, ret: -1` | Prior socket not fully torn down | Close + 500ms delay before retry |
| App shows connected after car off | No disconnect detection | Add heartbeat + read loop IOException handler |
| All connect paths fail, device is bonded | SDP lookup racing | Use reflection-channel-1 first |
| Works once, fails on second connect | Stale socket held by previous session | Force-close any lingering socket before connect |
| `BLUETOOTH_CONNECT` SecurityException | Missing runtime permission (API 31+) | Request `BLUETOOTH_CONNECT` at runtime |
| Connection killed when app backgrounded | No foreground service | Add `connectedDevice` foreground service |
| `ACL_DISCONNECTED` fires 30s late | Known Android OS bug | Don't rely on ACL alone — use heartbeat |
| `isConnected` returns true but socket is dead | `isConnected` reflects last known state, not health | Always detect via I/O, not `isConnected` |

---

## Reference Files

- `references/ble-gatt.md` — BLE/GATT deep dive, service UUIDs, race tracker profiles
- `references/device-ids.md` — Known device names, MAC prefixes, adapter classification

## Automated / AI-Assisted Testing Tooling (local baseline)

Use the currently available local toolchain for automation-first Android validation:

- Primary tools available: `adb`, `emulator`, repo `./gradlew` / `./gradlew.bat`, `java`, `python3`, `node`, `npm`, `bun`, `aapt`, `aapt2`, `gh`
- Commonly referenced but currently unavailable in PATH: `android` CLI binary, `sdkmanager`, `avdmanager`, `maestro`, `apkanalyzer`, `bundletool`

Recommended unattended validation loop:

1. Run deterministic gates each iteration:
   - `:core:test`, `:app:test`, `:app:assembleDebug`, `:app:lint`
2. If a device is present (`adb devices`), run connected instrumentation:
   - `:app:connectedDebugAndroidTest`
3. Persist per-iteration logs and summaries under `.sisyphus/evidence/`.
4. Bucket failures by signature (for flaky analysis), especially:
   - `ComposeTimeoutException`
   - `No compose hierarchies found`
   - device transport errors (`No connected devices`, `device ... not found`)

For managed devices where keep-awake cannot be enabled, use a sleep-tolerant loop:

- continue non-device gates every cycle
- classify connected runs as `PASS` / `FAIL` / `SKIP(no-device)`
- avoid treating temporary device sleep as total run failure.
