---
name: android-compose-realtime
description: |
  High-frequency real-time data display in Jetpack Compose: recomposition avoidance strategies,
  Canvas-based gauge and graph rendering, StateFlow-to-Compose integration, and stable data
  class patterns. Covers derivedStateOf, remember keys, snapshot-based reads, and performance
  profiling for 25Hz+ UI updates.
  Use this when: displaying live sensor or telemetry data in Compose, building custom Canvas gauges
  or live graphs, optimizing a Compose screen that recomposes too often, streaming StateFlow values
  to UI at high frequency, or building a dashboard with multiple independently-updating widgets.
license: Apache-2.0
metadata:
  author: Drew Fairweather
  last-updated: '2026-05-10'
  based-on: https://github.com/android/skills
  keywords:
  - Jetpack Compose
  - real-time UI
  - high-frequency updates
  - Canvas
  - recomposition
  - StateFlow
  - derivedStateOf
  - gauge
  - live graph
  - performance
  - stable
  - snapshot
---

> **Lineage:** Built upon and expanded from the official Android group skills repository at
> [github.com/android/skills](https://github.com/android/skills). That repo covers areas where
> evaluations show LLMs underperform on standard Android patterns. This skill extends that
> foundation into high-frequency Compose UI for real-time data — an area the official set does
> not cover.

## Overview

The core challenge: Compose's snapshot system triggers recomposition on every state read inside
a `@Composable`. At 25Hz, naively reading a large `TelemetryFrame` from a `StateFlow` in a
composable causes full-tree recomposition 25 times/second. The fix is **granular state** +
**derivedStateOf** + **stable types**.

## Dependencies

```kotlin
// No additional deps beyond the standard Compose BOM
[versions]
compose-bom = "2024.06.00"

[libraries]
compose-bom    = { group = "androidx.compose", name = "compose-bom", version.ref = "compose-bom" }
compose-ui     = { group = "androidx.compose.ui", name = "ui" }
compose-runtime = { group = "androidx.compose.runtime", name = "runtime" }
compose-foundation = { group = "androidx.compose.foundation", name = "foundation" }
```

## Stable Data Classes

Mark data classes `@Stable` or `@Immutable` to opt out of default conservative recomposition:

```kotlin
@Immutable
data class GaugeState(
    val value: Float,
    val min: Float,
    val max: Float,
    val unit: String
)

@Stable
class LiveMetricsState(
    speed: Float,
    heading: Float,
    altitude: Float
) {
    var speed by mutableFloatStateOf(speed)
    var heading by mutableFloatStateOf(heading)
    var altitude by mutableFloatStateOf(altitude)
}
```

`@Immutable` tells the compiler all public properties are `val` and won't change after creation.
`@Stable` promises you will notify the runtime when mutable properties change (via `mutableStateOf`).

## Granular State — DO NOT collect the whole frame

```kotlin
// BAD: recomposes entire composable every frame
val frame by viewModel.currentFrame.collectAsStateWithLifecycle()
SpeedGauge(frame.speedKph)
AltitudeGauge(frame.altitudeM)
HeadingIndicator(frame.headingDeg)

// GOOD: each gauge subscribes to its own derived state
val speed by remember {
    derivedStateOf { viewModel.currentFrame.value.speedKph }
}.collectAsState()   // Wrong — derivedStateOf is for State<T>, not Flow

// CORRECT pattern: split the flow in the ViewModel
class LiveViewModel : ViewModel() {
    private val _frame = MutableStateFlow(TelemetryFrame.EMPTY)

    val speedKph: StateFlow<Float> = _frame
        .map { it.speedKph }
        .distinctUntilChanged()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), 0f)

    val headingDeg: StateFlow<Float> = _frame
        .map { it.headingDeg }
        .distinctUntilChanged()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), 0f)

    val altitudeM: StateFlow<Float> = _frame
        .map { it.altitudeM }
        .distinctUntilChanged()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), 0f)
}
```

`distinctUntilChanged()` is critical — if heading doesn't change between frames, the composable
collecting it does not recompose.

## derivedStateOf for Derived UI Values

Use `derivedStateOf` when a UI value is computed from one or more `State<T>` objects and should
only trigger recomposition when the **result** changes, not on every input change:

```kotlin
@Composable
fun SpeedWarning(speedState: State<Float>, limitKph: Float) {
    val overLimit by remember {
        derivedStateOf { speedState.value > limitKph }
    }
    if (overLimit) {
        WarningBadge()
    }
}
```

If `speedState` changes from 98 to 99 kph against a 100 kph limit, `overLimit` stays `false`
and `SpeedWarning` does NOT recompose.

## Canvas Gauge

For analog-style gauges, use `Canvas` with no intermediate state reads outside the lambda:

```kotlin
@Composable
fun ArcGauge(
    value: Float,
    min: Float,
    max: Float,
    modifier: Modifier = Modifier
) {
    val sweepAngle by remember(value, min, max) {
        derivedStateOf {
            val normalized = ((value - min) / (max - min)).coerceIn(0f, 1f)
            normalized * 240f  // 240° sweep
        }
    }

    Canvas(modifier = modifier.size(160.dp)) {
        val strokeWidth = size.width * 0.08f
        val radius = (size.minDimension / 2f) - strokeWidth

        // Background arc
        drawArc(
            color = Color.Gray.copy(alpha = 0.3f),
            startAngle = 150f,
            sweepAngle = 240f,
            useCenter = false,
            style = Stroke(width = strokeWidth, cap = StrokeCap.Round),
            topLeft = Offset(center.x - radius, center.y - radius),
            size = Size(radius * 2, radius * 2)
        )

        // Value arc
        drawArc(
            color = Color(0xFF00C853),
            startAngle = 150f,
            sweepAngle = sweepAngle,
            useCenter = false,
            style = Stroke(width = strokeWidth, cap = StrokeCap.Round),
            topLeft = Offset(center.x - radius, center.y - radius),
            size = Size(radius * 2, radius * 2)
        )
    }
}
```

Canvas lambdas run in the **Draw** phase, not the Composition phase. Reading `sweepAngle`
(a `State`) inside the lambda still triggers only the draw, not full recomposition.
For pure draw-phase reads, use `graphicsLayer` or `DrawScope`-local state.

## Live Graph (Sliding Window)

For a time-series line graph, maintain a fixed-size ring buffer in the ViewModel:

```kotlin
class GraphViewModel : ViewModel() {
    private val windowSize = 300  // 300 samples = 12 seconds at 25Hz
    private val _samples = ArrayDeque<Float>(windowSize)
    val samples: StateFlow<List<Float>> = MutableStateFlow(emptyList())

    fun onNewSample(value: Float) {
        if (_samples.size >= windowSize) _samples.removeFirst()
        _samples.addLast(value)
        (samples as MutableStateFlow).value = _samples.toList()
    }
}

@Composable
fun LineGraph(samples: List<Float>, modifier: Modifier = Modifier) {
    Canvas(modifier = modifier) {
        if (samples.size < 2) return@Canvas
        val max = samples.max()
        val min = samples.min()
        val range = (max - min).coerceAtLeast(1f)
        val xStep = size.width / (samples.size - 1)

        val path = Path().apply {
            samples.forEachIndexed { i, v ->
                val x = i * xStep
                val y = size.height - ((v - min) / range * size.height)
                if (i == 0) moveTo(x, y) else lineTo(x, y)
            }
        }
        drawPath(path, Color.Cyan, style = Stroke(width = 2.dp.toPx()))
    }
}
```

## LaunchedEffect vs collectAsStateWithLifecycle

Prefer `collectAsStateWithLifecycle` for flows driving UI state — it respects the lifecycle
and cancels collection when the composable leaves the composition:

```kotlin
// PREFER this
val speed by viewModel.speedKph.collectAsStateWithLifecycle()

// Avoid this for ongoing state — LaunchedEffect restarts on key change
LaunchedEffect(Unit) {
    viewModel.speedKph.collect { speed = it }
}
```

Add `lifecycle-runtime-compose` to use `collectAsStateWithLifecycle`:

```kotlin
implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.3")
```

## Recomposition Profiling

Enable composition tracing in debug builds to identify hot recompositions:

```kotlin
// In your debug build type
android {
    buildTypes {
        debug {
            // Enable Compose compiler metrics
        }
    }
}
```

Run with Layout Inspector → Recomposition Counts visible. Any composable recomposing >5x/second
that is **not** a real-time display widget is a bug.

## Key Patterns Summary

| Pattern | When to use |
|---|---|
| `distinctUntilChanged()` on ViewModel flows | Every derived metric exposed as `StateFlow` |
| `derivedStateOf` | Computing display values from multiple `State<T>` |
| `@Immutable` / `@Stable` | All data classes passed as Compose parameters |
| Split flows per metric | When a screen has multiple independently-updating widgets |
| Canvas for gauges/graphs | Analog dials, waveforms, maps — anything requiring custom drawing |
| `collectAsStateWithLifecycle` | All StateFlow → Compose wiring |

## Anti-Patterns

| Symptom | Root cause | Fix |
|---|---|---|
| UI thread jank at 25Hz | Collecting full frame object in one composable | Split flow per displayed metric + `distinctUntilChanged` |
| Gauge flickers | Recomposition rebuilding `Path`/`Paint` every frame | Move path allocation inside `remember { }` and update only on value change |
| `derivedStateOf` has no effect | Used on `Flow` instead of `State<T>` | Apply to `.collectAsState()` result, not the Flow itself |
| `@Immutable` data class still causes recomposition | Has a `var` or mutable collection property | Make all properties `val` with immutable types |
| `LaunchedEffect` re-runs unexpectedly | Key changes due to lambda capture | Use stable keys; prefer `collectAsStateWithLifecycle` |
