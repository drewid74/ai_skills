---
name: android-obd
description: >
  Expert guidance for Android OBD2 / ELM327 development — protocol initialization,
  PID polling, vehicle data parsing, adapter quirks, transport quirks, and Android Auto
  integration. Use this skill whenever the user is working with OBD2 data, ELM327
  commands, AT command sequences, PID requests, DTC reading, vehicle protocol detection,
  0100 probe behavior, ELM327 prompt handling, ATSP0, ATZ, ATE0, ATL0, ATH0, ATAT1,
  vehicle bus initialization failures, adapter init timeouts, classic OBD socket connect,
  OBDLink MX+, OBDLink CX, Veepeak OBDCheck BLE+, generic ELM327 adapters, clone behavior,
  NO DATA, UNABLE TO CONNECT, BUS INIT, SEARCHING, CAN ERROR, STOPPED, ECU polling,
  race telemetry from OBD, Android Auto OBD display, or Car App Library integration with
  live vehicle data. Trigger for app issues where OBD appears connected but does not return
  valid data, where Home shows Connecting during adapter init/probe, or where BLE-vs-classic
  OBD path choice changes behavior. Do not use for generic Android Bluetooth permissions or
  pairing-only issues unless they are directly blocking OBD transport setup; use android-bluetooth for those.
---

# Android OBD2 / ELM327 Development Skill

Full guidance for ELM327-based OBD2 communication from Android — from adapter
identification through vehicle protocol init, PID polling, and Android Auto display.

---

## ELM327 Init Sequence

Always run this exact sequence after RFCOMM connects. Never skip it, even for
"previously connected" adapters — the adapter state is unknown until reset.

```kotlin
val INIT_SEQUENCE = listOf(
    "ATZ",    // full reset — wait up to 2s for ">" prompt
    "ATE0",   // echo off — cleans up response parsing
    "ATL0",   // linefeeds off
    "ATH0",   // headers off (set H1 if you need protocol headers)
    "ATSP0",  // auto protocol detection
    "ATAT1",  // adaptive timing mode 1 — improves slow ECU response
)

// After init, send first real PID to trigger bus initialization:
// "0100" — supported PIDs query, forces BUS INIT / SEARCHING...
```

### Reading Responses Correctly

ELM327 uses `>` as its ready prompt — not newline. Read until `>`, not by line:

```kotlin
fun readResponse(inputStream: InputStream, timeoutMs: Long = 5000): String {
    val buffer = StringBuilder()
    val deadline = System.currentTimeMillis() + timeoutMs
    
    while (System.currentTimeMillis() < deadline) {
        if (inputStream.available() > 0) {
            val char = inputStream.read().toChar()
            if (char == '>') break  // prompt = response complete
            buffer.append(char)
        } else {
            Thread.sleep(10)
        }
    }
    return buffer.toString().trim()
}
```

### Echo Handling

First two commands after `ATZ` will have echo (the command text prepended to response).
`ATZ` returns `ATZ\r\nELM327 v1.4b\r\n>` — the adapter echoes until `ATE0` takes effect.
Strip echo by checking if the response starts with the command you sent:

```kotlin
fun stripEcho(command: String, response: String): String {
    val cmd = command.trimEnd('\r').uppercase()
    return if (response.uppercase().startsWith(cmd)) {
        response.substring(cmd.length).trim()
    } else {
        response
    }
}
```

---

## Vehicle Protocol Detection

`ATSP0` sets auto-detect. On first real PID request (`0100`), ELM327 negotiates the
vehicle's protocol. This produces:

```
SEARCHING...    ← normal, ELM327 trying protocols
BUS INIT: OK    ← found protocol, initializing
41 00 BE 3F B8 13  ← actual PID response (0100 = supported PIDs)
```

**Do not treat `SEARCHING...` or `BUS INIT` as errors.** Allow up to 30 seconds for
first-connect protocol negotiation. Subsequent requests are fast (<200ms typically).

If you consistently get `UNABLE TO CONNECT`:
1. Ignition must be ACC or ON — engine doesn't need to run
2. Some vehicles need ignition fully ON (not just ACC) for OBD
3. Try `ATSP` with a specific protocol number if auto-detect fails

### Protocol Numbers for ATSP

| Protocol | ATSP | Notes |
|---|---|---|
| Auto | 0 | Start here always |
| SAE J1850 PWM | 1 | Ford pre-2008 |
| SAE J1850 VPW | 2 | GM pre-2008 |
| ISO 9141-2 | 3 | European pre-2008 |
| ISO 14230-4 KWP (5 baud) | 4 | |
| ISO 14230-4 KWP (fast) | 5 | |
| ISO 15765-4 CAN 11b 500k | 6 | Most common modern |
| ISO 15765-4 CAN 29b 500k | 7 | |
| ISO 15765-4 CAN 11b 250k | 8 | |
| ISO 15765-4 CAN 29b 250k | 9 | |

---

## PID Reference

### Mode 01 — Live Data (most common)

```kotlin
// Request format: "01 XX\r" where XX is PID hex
// Response format: "41 XX [data bytes]\r"

object PID {
    const val SUPPORTED_PIDS_1   = "0100"
    const val ENGINE_RPM         = "010C"  // response / 4 = RPM
    const val VEHICLE_SPEED      = "010D"  // response = km/h
    const val COOLANT_TEMP       = "0105"  // response - 40 = °C
    const val THROTTLE_POS       = "0111"  // response * 100/255 = %
    const val INTAKE_AIR_TEMP    = "010F"  // response - 40 = °C
    const val MAF_RATE           = "0110"  // (256*A + B) / 100 = g/s
    const val FUEL_LEVEL         = "012F"  // response * 100/255 = %
    const val ENGINE_LOAD        = "0104"  // response * 100/255 = %
    const val SHORT_TERM_FUEL    = "0106"  // (response - 128) * 100/128 = %
    const val LONG_TERM_FUEL     = "0107"  // (response - 128) * 100/128 = %
    const val INTAKE_MANIFOLD    = "010B"  // response = kPa
    const val TIMING_ADVANCE     = "010E"  // response/2 - 64 = degrees
    const val OBD_STANDARDS      = "011C"
    const val RUNTIME_SINCE_START= "011F"  // (256*A + B) = seconds
    const val FUEL_PRESSURE      = "010A"  // response * 3 = kPa
}
```

### Response Parsing

```kotlin
fun parseOBDResponse(response: String): ByteArray? {
    // Strip whitespace, check for error strings
    val cleaned = response.replace("\\s".toRegex(), "").uppercase()
    
    if (cleaned.contains("NODATA") || 
        cleaned.contains("UNABLETOCONNECT") ||
        cleaned.contains("ERROR") ||
        cleaned.contains("STOPPED")) return null
    
    // Response starts with "41" for mode 01 replies
    val dataStart = cleaned.indexOf("41")
    if (dataStart < 0) return null
    
    return try {
        cleaned.substring(dataStart + 4) // skip "41 XX" prefix
            .chunked(2)
            .map { it.toInt(16).toByte() }
            .toByteArray()
    } catch (e: NumberFormatException) {
        null
    }
}

// Example: parse RPM from 010C response
fun parseRPM(data: ByteArray): Int {
    if (data.size < 2) return -1
    return ((data[0].toInt() and 0xFF) * 256 + (data[1].toInt() and 0xFF)) / 4
}

// Example: parse speed
fun parseSpeed(data: ByteArray): Int {
    if (data.isEmpty()) return -1
    return data[0].toInt() and 0xFF  // km/h
}
```

---

## OBDLink MX+ Specific Notes

The MX+ is a genuine ELM327-compatible adapter with extended capabilities. Key facts:

- **Always use reflection-channel-1 RFCOMM** — standard UUID-based connect is less
  reliable on the MX+. See android-bluetooth skill for connection code.
- **Has both Classic BT (SPP) and BLE** — BLE uses a proprietary GATT profile not
  documented publicly. Third-party apps must use SPP, not BLE.
- **Supports extended AT commands** that clones don't:
  - `ATAL` — allow long messages
  - `ATAT1/2` — adaptive timing (don't use on clones — many drop the connection)
  - `ATBI` — bypass initialization (useful for testing)
  - `ATSTH XX` — set headers
- **`ATI` response** confirms adapter: `OBDLink MX+ v?.?` — use this to detect MX+
  post-connect and enable extended commands.
- **One connection at a time** — force-stop OBDLink app before testing your app.
  The OBDLink app holds the SPP connection even when backgrounded.

---

## DTC Reading — Mode 03

```kotlin
const val READ_DTC = "03"  // no PID — just mode

fun parseDTCs(response: String): List<String> {
    val cleaned = response.replace("\\s".toRegex(), "").uppercase()
    if (cleaned.contains("NODATA") || cleaned.contains("43")) {
        // "43" prefix = mode 03 response
        val data = cleaned.substringAfter("43")
        return data.chunked(4).mapNotNull { parseDTC(it) }
    }
    return emptyList()
}

fun parseDTC(raw: String): String? {
    if (raw.length < 4 || raw == "0000") return null
    val first = raw[0].digitToInt(16)
    val prefix = when (first shr 2) {
        0 -> "P"  // Powertrain
        1 -> "C"  // Chassis
        2 -> "B"  // Body
        3 -> "U"  // Network
        else -> "P"
    }
    return "$prefix${(first and 0x3).toString(16)}${raw.substring(1)}"
}
```

---

## Android Auto Integration

See `references/android-auto.md` for full Android Auto / Car App Library integration,
including:
- Car App Library setup (CAL 1.7.0+)
- PaneTemplate for live PID display
- Sideload testing without Play Store
- Category requirements and Play Store submission notes
- DHU (Desktop Head Unit) emulator setup

---

## Common Response Strings and Meanings

| Response | Meaning | Action |
|---|---|---|
| `OK` | Command accepted | Continue |
| `>` | Prompt — ready for next command | Send next command |
| `SEARCHING...` | Protocol negotiation in progress | Wait, do not resend |
| `BUS INIT: OK` | Protocol found, initializing | Wait for data |
| `NO DATA` | ECU didn't respond | Check ignition, retry |
| `UNABLE TO CONNECT` | Can't find vehicle protocol | Check ignition ON, try ATSP |
| `BUS BUSY` | Bus traffic collision | Retry after short delay |
| `ERROR` | Command or hardware error | Re-run init sequence |
| `STOPPED` | Command interrupted | Re-run init sequence |
| `?` | Unknown AT command | Check command syntax |
| `FB ERROR` | Feedback error on some clones | Ignore or retry |

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
