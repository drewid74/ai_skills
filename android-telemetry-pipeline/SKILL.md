---
name: android-telemetry-pipeline
description: |
  High-frequency sensor data pipeline for Android: hybrid storage (Room for session metadata +
  CSV/binary files for sample data), StateFlow-based streaming to UI, session lifecycle management,
  and offline-first write patterns. Covers atomic session creation, buffered CSV writes, telemetry
  normalization across sources (BLE device vs phone GPS+IMU), and post-session data analysis.
  Use this when: ingesting 10-100Hz sensor data, designing a session storage schema, streaming
  live telemetry to a Compose ViewModel, building a session list/review flow, handling source
  switching mid-session, or implementing post-session analysis pipelines.
license: Apache-2.0
metadata:
  author: Drew Fairweather
  last-updated: '2026-05-10'
  based-on: https://github.com/android/skills
  keywords:
  - telemetry
  - sensor pipeline
  - Room database
  - CSV storage
  - hybrid storage
  - StateFlow
  - session management
  - offline-first
  - high-frequency data
  - GPS
  - IMU
  - post-session analysis
---

> **Lineage:** Built upon and expanded from the official Android group skills repository at
> [github.com/android/skills](https://github.com/android/skills). That repo covers areas where
> evaluations show LLMs underperform on standard Android patterns. This skill extends that
> foundation into high-frequency telemetry pipelines — an area the official set does not cover.

## Overview

Core principle: **Room stores metadata only. Raw samples go to files.**

Storing 25Hz telemetry rows in Room causes excessive WAL churn and query overhead.
The split — `SessionEntity` (metadata) in Room + `session_{id}.csv` (samples) on disk —
gives fast session list queries, simple backup/export, and zero SQLite write contention.

## Storage Architecture

```
app/files/sessions/
├── session_20260510_143022.csv     ← raw telemetry samples (append-only)
├── session_20260510_151847.csv
└── ...

Room (sessions table):
├── id, startTime, endTime, sampleCount, csvFilePath
├── locationId, locationName
├── analysisComplete, analysisResult
└── (index on startTime, locationId, analysisComplete)
```

## Dependencies

```kotlin
// libs.versions.toml
[versions]
room = "2.6.1"
ksp = "2.0.0-1.0.22"

[libraries]
room-runtime  = { group = "androidx.room", name = "room-runtime",  version.ref = "room" }
room-ktx      = { group = "androidx.room", name = "room-ktx",      version.ref = "room" }
room-compiler = { group = "androidx.room", name = "room-compiler", version.ref = "room" }

[plugins]
ksp = { id = "com.google.devtools.ksp", version.ref = "ksp" }
```

Always use **KSP** for Room annotation processing — `kapt` is deprecated.

```kotlin
// app/build.gradle.kts
plugins {
    alias(libs.plugins.ksp)
}
dependencies {
    ksp(libs.room.compiler)
    implementation(libs.room.runtime)
    implementation(libs.room.ktx)
}
```

## Session Entity

```kotlin
@Entity(
    tableName = "sessions",
    indices = [
        Index("startTime"),
        Index("locationId"),
        Index("analysisComplete")
    ]
)
data class SessionEntity(
    @PrimaryKey val id: String,                // UUID string
    val startTime: Long,                       // epoch millis
    val endTime: Long?,
    val sampleCount: Int,
    val csvFilePath: String,                   // absolute path
    val locationId: String?,
    val locationName: String?,
    val analysisComplete: Boolean = false,
    val analysisResult: String?                // summary output from post-session analysis
)
```

Never store sample data (lat, lon, speed, g-forces) in Room rows — use the CSV file.
Only store aggregates in the entity if you query on them (e.g., `maxSpeedKph` for a leaderboard).

## DAO

```kotlin
@Dao
interface SessionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(session: SessionEntity)

    @Update
    suspend fun update(session: SessionEntity)

    @Query("SELECT * FROM sessions ORDER BY startTime DESC")
    fun getAllSessions(): Flow<List<SessionEntity>>   // Flow for reactive list

    @Query("SELECT * FROM sessions WHERE id = :id")
    suspend fun getById(id: String): SessionEntity?

    @Query("UPDATE sessions SET endTime = :endTime, sampleCount = :count WHERE id = :id")
    suspend fun finalizeSession(id: String, endTime: Long, count: Int)

    @Query("UPDATE sessions SET analysisComplete = 1, analysisResult = :result WHERE id = :id")
    suspend fun markAnalysisComplete(id: String, result: String?)
}
```

## Database

```kotlin
@Database(entities = [SessionEntity::class], version = 2, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    abstract fun sessionDao(): SessionDao

    companion object {
        @Volatile private var instance: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase =
            instance ?: synchronized(this) {
                instance ?: Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "sessions.db"
                )
                .fallbackToDestructiveMigration()   // dev only; use proper migrations in production
                .build().also { instance = it }
            }
    }
}
```

Use `fallbackToDestructiveMigration()` only during development. Before shipping, add a proper
`Migration` object for each version bump.

## Telemetry Normalization

Define a common data class regardless of source (BLE device vs phone sensors):

```kotlin
data class TelemetryFrame(
    val timestampMs: Long,          // epoch millis
    val source: TelemetrySource,    // BLE, PHONE
    val latDeg: Double,
    val lonDeg: Double,
    val speedKph: Float,
    val headingDeg: Float,
    val altitudeM: Float,
    val accelX: Float,              // m/s² lateral
    val accelY: Float,              // m/s² longitudinal
    val accelZ: Float,              // m/s² vertical
    val satellites: Int = 0,
    val hdop: Float = 0f            // horizontal dilution of precision
)

enum class TelemetrySource { BLE, PHONE }
```

Map all hardware-specific data types to `TelemetryFrame` in the source layer (BLE manager or
sensor manager). The ViewModel, CSV writer, and analysis pipeline see only `TelemetryFrame`.

## Buffered CSV Writer

Write samples to a `ConcurrentLinkedQueue` buffer, flush to disk periodically to avoid
I/O on every sample at 25Hz:

```kotlin
private val writeBuffer = ConcurrentLinkedQueue<TelemetryFrame>()
private val sampleCounter = AtomicInteger(0)

fun onTelemetryReceived(frame: TelemetryFrame) {
    writeBuffer.add(frame)
    val count = sampleCounter.incrementAndGet()
    _sampleCount.value = count

    // Flush every 250 samples (~10 seconds at 25Hz)
    if (count % 250 == 0) {
        serviceScope.launch(Dispatchers.IO) { flushBuffer() }
    }
}

private fun flushBuffer() {
    val frames = mutableListOf<TelemetryFrame>()
    while (true) frames.add(writeBuffer.poll() ?: break)
    if (frames.isEmpty()) return

    val csv = buildCsvContent(frames)
    File(currentCsvPath).appendText(csv)
}

private fun buildCsvContent(frames: List<TelemetryFrame>): String =
    buildString {
        for (f in frames) {
            append("${f.timestampMs},${f.source},${f.latDeg},${f.lonDeg},")
            append("${f.speedKph},${f.headingDeg},${f.altitudeM},")
            append("${f.accelX},${f.accelY},${f.accelZ},")
            append("${f.satellites},${f.hdop}\n")
        }
    }
```

Write the CSV header once at session creation, not on every flush.

## Session Lifecycle

```kotlin
// SessionRepository
suspend fun createSession(csvFilePath: String, sessionId: String? = null): SessionEntity {
    val id = sessionId ?: UUID.randomUUID().toString()
    val entity = SessionEntity(
        id = id,
        startTime = Instant.now().toEpochMilli(),
        endTime = null,
        sampleCount = 0,
        csvFilePath = csvFilePath,
        locationId = null,
        locationName = null
    )
    db.sessionDao().insert(entity)
    return entity
}

suspend fun finalizeSession(id: String, endTime: Instant, sampleCount: Int) {
    db.sessionDao().finalizeSession(id, endTime.toEpochMilli(), sampleCount)
}

suspend fun markAnalysisComplete(id: String, result: String?) {
    db.sessionDao().markAnalysisComplete(id, result)
}

fun getAllSessions(): Flow<List<SessionEntity>> = db.sessionDao().getAllSessions()
```

## ViewModel Wiring

```kotlin
class SessionListViewModel(private val repo: SessionRepository) : ViewModel() {
    val sessions: StateFlow<List<SessionEntity>> = repo.getAllSessions()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())
}

class RecordingViewModel : ViewModel() {
    val sampleCount = TelemetryRecordingService.sampleCount
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), 0)

    val activeSource = TelemetryRecordingService.activeSource
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), TelemetrySource.PHONE)
}
```

Use `SharingStarted.WhileSubscribed(5_000)` — the 5-second timeout keeps the flow alive
through configuration changes (rotation) without leaking indefinitely.

## CSV File Management

```kotlin
fun createCsvFile(context: Context, sessionId: String): File {
    val dir = File(context.filesDir, "sessions").apply { mkdirs() }
    val file = File(dir, "session_$sessionId.csv")
    // Write header
    file.writeText("timestampMs,source,lat,lon,speedKph,heading,altitude,accelX,accelY,accelZ,sats,hdop\n")
    return file
}
```

Use `context.filesDir` (internal storage) — no permissions required, automatically backed up
if `android:allowBackup="true"`, and excluded from media scans. Never use `Environment.getExternalStorageDirectory()` for telemetry data.

## Post-Session Analysis Pipeline

Trigger analysis after `finalizeSession`. Run on a background dispatcher, update Room when done:

```kotlin
class PostSessionAnalyzer(private val repo: SessionRepository) {
    suspend fun analyze(session: SessionEntity) = withContext(Dispatchers.Default) {
        val frames = parseCsv(File(session.csvFilePath))
        val result = computeSummary(frames)   // app-specific: max speed, distance, etc.
        repo.markAnalysisComplete(session.id, result)
    }

    private fun parseCsv(file: File): List<TelemetryFrame> {
        // Read CSV, skip header line, parse each row into TelemetryFrame
        return file.readLines().drop(1).mapNotNull { line ->
            runCatching { parseLine(line) }.getOrNull()
        }
    }
}
```

## Anti-Patterns

| Symptom | Root cause | Fix |
|---|---|---|
| `kapt` annotation errors on Room | Using `kapt` instead of KSP | Switch to `ksp(libs.room.compiler)` |
| Database locked / WAL errors | Writing sample rows to Room at 25Hz | Move samples to file; only metadata in Room |
| Lost samples on process kill | Flushing only in `onDestroy` | Flush buffer in the stop-recording action handler |
| Session list doesn't update | Using `suspend` query instead of `Flow` | `getAllSessions()` must return `Flow<List<>>` |
| CSV grows unbounded | No size/age pruning | Prune sessions older than N days on app start |
| Concurrent write corruption | Multiple coroutines writing to same file | Confine all file writes to a single `Dispatchers.IO` context or use `Mutex` |
