---
name: android-ble-hardware
description: |
  Android BLE hardware integration using the Nordic Semiconductor BLE library (no.nordicsemi.android:ble).
  Covers UART/GATT service discovery, callbackFlow-based device scanning, connection lifecycle
  management, multi-device type detection, automatic reconnection, and byte-level protocol parsing.
  Use this when: integrating a BLE peripheral, implementing a GATT profile, scanning for devices
  by UUID or name pattern, handling BLE permissions on Android 12+, parsing binary telemetry
  packets, building a BleManager subclass, handling disconnect/reconnect loops, integrating
  GPS loggers, sensor hardware, OBD-II adapters, or any custom BLE peripheral.
license: Apache-2.0
metadata:
  author: Drew Fairweather
  last-updated: '2026-05-10'
  based-on: https://github.com/android/skills
  keywords:
  - BLE
  - Bluetooth LE
  - GATT
  - UART
  - Nordic
  - no.nordicsemi
  - OBD-II
  - callbackFlow
  - device scanning
  - telemetry
  - hardware integration
  - Android 12+
  - BLUETOOTH_SCAN
  - BLUETOOTH_CONNECT
---

> **Lineage:** Built upon and expanded from the official Android group skills repository at
> [github.com/android/skills](https://github.com/android/skills). That repo covers areas where
> evaluations show LLMs underperform on standard Android patterns. This skill extends that
> foundation into BLE hardware integration — an area the official set does not cover.

## Overview

Use the Nordic Semiconductor Android BLE library (`no.nordicsemi.android:ble` +
`no.nordicsemi.android:ble-ktx`) as the BLE abstraction layer. Prefer this over raw
`BluetoothGatt` callbacks — it handles connection retries, queued operations, and MTU negotiation.

## Dependencies

```kotlin
// libs.versions.toml
[versions]
nordic-ble = "2.7.0"

[libraries]
nordic-ble     = { group = "no.nordicsemi.android", name = "ble",     version.ref = "nordic-ble" }
nordic-ble-ktx = { group = "no.nordicsemi.android", name = "ble-ktx", version.ref = "nordic-ble" }
```

## BLE Permissions (Android 12+)

Declare in `AndroidManifest.xml` and request at runtime before any BLE operation:

```xml
<uses-permission android:name="android.permission.BLUETOOTH_SCAN"
    android:usesPermissionFlags="neverForLocation" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-feature android:name="android.hardware.bluetooth_le" android:required="false" />
```

Required permissions by API level:
- API < 31: `BLUETOOTH`, `BLUETOOTH_ADMIN`, `ACCESS_FINE_LOCATION`
- API 31+: `BLUETOOTH_SCAN`, `BLUETOOTH_CONNECT` (+ `ACCESS_FINE_LOCATION` if deriving location)

Suppress `@SuppressLint("MissingPermission")` only **after** confirming permissions are held at
the call site. Never apply it at the class level.

## Device Type Detection

Define device types with UUID and name-pattern matching. Never scatter raw UUIDs across files —
keep them in the companion object of the manager that owns that GATT profile.

```kotlin
enum class DeviceType {
    GPS_LOGGER,  // e.g. Nordic UART service: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E
    OBD_ELM327,  // name often starts with "OBDII" or "ELM327"
    HEART_RATE,  // standard BLE Heart Rate Service: 0x180D
    UNKNOWN;

    companion object {
        fun detect(device: BluetoothDevice, serviceUuids: List<ParcelUuid>?): DeviceType {
            if (hasMatchingService(serviceUuids, UART_SERVICE_UUID)) return GPS_LOGGER
            if (matchesDeviceName(device.name, listOf("OBDII", "ELM327", "OBD"))) return OBD_ELM327
            if (hasMatchingService(serviceUuids, UUID.fromString("0000180D-0000-1000-8000-00805F9B34FB"))) return HEART_RATE
            return UNKNOWN
        }

        private fun hasMatchingService(uuids: List<ParcelUuid>?, target: UUID) =
            uuids?.any { it.uuid == target } == true

        private fun matchesDeviceName(name: String?, patterns: List<String>) =
            name != null && patterns.any { name.uppercase().contains(it) }
    }
}
```

## Scanning (callbackFlow pattern)

Expose scanning as a `Flow<ScannedDevice>` so the ViewModel can collect it. Never hold a scan
callback reference in a ViewModel — keep it in a repository or manager that outlives
configuration changes.

```kotlin
@SuppressLint("MissingPermission")
fun scanForDevices(deviceTypes: Set<DeviceType> = emptySet()): Flow<ScannedDevice> =
    callbackFlow {
        val scanner = bluetoothAdapter?.bluetoothLeScanner
            ?: run { close(IllegalStateException("BLE not available")); return@callbackFlow }

        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()

        val callback = object : ScanCallback() {
            override fun onScanResult(callbackType: Int, result: ScanResult) {
                val detected = DeviceType.detect(result.device, result.scanRecord?.serviceUuids)
                if (deviceTypes.isEmpty() || detected in deviceTypes) {
                    trySend(ScannedDevice(result.device, detected, result.rssi))
                }
            }
            override fun onScanFailed(errorCode: Int) {
                close(RuntimeException("BLE scan failed: $errorCode"))
            }
        }

        scanner.startScan(buildFilters(deviceTypes), settings, callback)
        awaitClose { scanner.stopScan(callback) }
    }
```

Rules:
- Use `SCAN_MODE_LOW_LATENCY` during active device selection; switch to `SCAN_MODE_LOW_POWER` in background.
- Always call `stopScan` in `awaitClose` — an unclosed scanner drains battery continuously.
- Use `trySend` (not `send`) in scan callbacks — the callback fires on a non-coroutine thread.

## BleManager Subclass (Nordic library)

Extend `BleManager` for each device profile. One manager instance per connected device.

```kotlin
class UartBleManager(context: Context) : BleManager(context) {

    companion object {
        val UART_SERVICE_UUID = UUID.fromString("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
        val UART_TX_UUID      = UUID.fromString("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
        val UART_RX_UUID      = UUID.fromString("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
    }

    private var txChar: BluetoothGattCharacteristic? = null
    private var rxChar: BluetoothGattCharacteristic? = null
    var dataListener: ((ByteArray) -> Unit)? = null

    override fun getGattCallback(): BleManagerGattCallback = Callback()

    private inner class Callback : BleManagerGattCallback() {
        override fun isRequiredServiceSupported(gatt: BluetoothGatt): Boolean {
            val svc = gatt.getService(UART_SERVICE_UUID) ?: return false
            txChar = svc.getCharacteristic(UART_TX_UUID)
            rxChar = svc.getCharacteristic(UART_RX_UUID)
            return txChar != null && rxChar != null
        }

        override fun initialize() {
            // Device → phone notifications on RX characteristic
            setNotificationCallback(rxChar).with { _, data ->
                data.value?.let { dataListener?.invoke(it) }
            }
            enableNotifications(rxChar).enqueue()
        }

        override fun onServicesInvalidated() {
            txChar = null; rxChar = null
        }
    }

    fun sendCommand(bytes: ByteArray) {
        writeCharacteristic(txChar, bytes, BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE)
            .enqueue()
    }
}
```

Rules:
- `isRequiredServiceSupported` returning `false` causes a clean disconnect — always return `false` when any required characteristic is missing rather than crashing later.
- Call `.enqueue()` on every operation — never fire-and-forget.
- Use `WRITE_TYPE_NO_RESPONSE` for high-throughput streams; `WRITE_TYPE_DEFAULT` for acknowledged commands.

## Connection Lifecycle

```kotlin
// Connect — run from a scope that survives configuration changes (Service or Repository)
bleManager.connect(device)
    .useAutoConnect(false)   // true only for background reconnect after initial bond
    .timeout(10_000)
    .retry(3, 500)
    .done  { /* connected */ }
    .fail  { _, status -> /* handle */ }
    .enqueue()

// Disconnect
bleManager.disconnect().enqueue()
```

Automatic reconnection after unexpected disconnect:
```kotlin
override fun onDeviceDisconnected(device: BluetoothDevice, reason: Int) {
    super.onDeviceDisconnected(device, reason)
    if (shouldReconnect && reason != ConnectionObserver.REASON_SUCCESS) {
        coroutineScope.launch {
            delay(1_000)
            bleManager.connect(device).useAutoConnect(true).retry(5, 2_000).enqueue()
        }
    }
}
```

## Packet Framing

For devices that stream raw bytes over UART, use a stateful `PacketAssembler` that buffers
incoming chunks and emits complete frames:

```kotlin
class PacketAssembler {
    private val buffer = mutableListOf<Byte>()

    /** Returns a complete packet if one is ready, null otherwise. */
    fun feed(bytes: ByteArray): ByteArray? {
        buffer.addAll(bytes.toList())
        return tryExtract()
    }

    private fun tryExtract(): ByteArray? {
        // Example: 2-byte big-endian length prefix
        if (buffer.size < 2) return null
        val length = ((buffer[0].toInt() and 0xFF) shl 8) or (buffer[1].toInt() and 0xFF)
        if (buffer.size < length + 2) return null
        val packet = buffer.subList(2, length + 2).toByteArray()
        repeat(length + 2) { buffer.removeAt(0) }
        return packet
    }
}
```

## Testing Without Hardware

Provide a `DemoDeviceGenerator` that emits synthetic `ScannedDevice` objects and a
`DemoDataGenerator` that emits synthetic frames at the expected rate. Gate with
`BuildConfig.USE_DEMO_MODE` so the flag never ships in release builds.

## Anti-Patterns

| Symptom | Root cause | Fix |
|---|---|---|
| `SecurityException` on scan | Missing runtime permission | Check `BLUETOOTH_SCAN` before `startScan` |
| Scan finds no devices | `neverForLocation` + missing `ACCESS_FINE_LOCATION` on API < 31 | Add location permission for pre-31 code paths |
| `isRequiredServiceSupported` returns false | Wrong UUID or hardware revision | Log all discovered services in debug builds |
| `onScanFailed(2)` | >5 scan starts in 30 seconds | Debounce scan start; reuse scanner instance |
| Notifications never fire | `enableNotifications()` not called or CCCD write failed | Verify `initialize()` executes and check library verbose logs |
| `BLUETOOTH_CONNECT` crash on API 33+ | Permission not declared | Add to manifest and request at runtime |
| Battery drain | Scanner not stopped on Flow cancellation | Confirm `awaitClose { stopScan(callback) }` is present |
