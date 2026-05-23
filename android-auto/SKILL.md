---
name: android-auto
description: |
  Android Auto and Automotive OS app development using the Car App Library: template-based UI
  architecture, voice interaction, safety restrictions (distraction optimization), session
  and screen lifecycle, navigation templates, media playback integration, and place list/map
  templates. Covers both the phone-projection (Android Auto) and native (AAOS) deployment targets.
  Use this when: building an Android Auto app, porting a phone app to the car screen, implementing
  voice commands for Auto, handling driving safety restrictions, building navigation or POI
  features for car, or targeting Android Automotive OS natively.
license: Apache-2.0
metadata:
  author: Drew Fairweather
  last-updated: '2026-05-10'
  based-on: https://github.com/android/skills
  keywords:
  - Android Auto
  - Android Automotive OS
  - AAOS
  - Car App Library
  - CarAppService
  - template
  - voice
  - safety
  - distraction optimization
  - navigation
  - media
  - PlaceListMapTemplate
  - NavigationTemplate
---

> **Lineage:** Built upon and expanded from the official Android group skills repository at
> [github.com/android/skills](https://github.com/android/skills). That repo covers areas where
> evaluations show LLMs underperform on standard Android patterns. This skill extends that
> foundation into Android Auto / Automotive OS development — an area the official set does not
> cover.

## Overview

Android Auto (phone projection) and Android Automotive OS (native in-vehicle) share the **Car
App Library** (CAL). CAL enforces a template-based UI model — apps cannot draw arbitrary views
on the car screen. Every screen must use one of the provided templates (`ListTemplate`,
`NavigationTemplate`, `PlaceListMapTemplate`, `MessageTemplate`, etc.).

The library enforces **Distraction Optimization (DO)** automatically: limits list lengths,
text lengths, and interaction depth while driving. Design for these constraints from the start.

## Dependencies

```kotlin
// libs.versions.toml
[versions]
car-app = "1.4.0"

[libraries]
car-app-automotive = { group = "androidx.car.app", name = "app-automotive", version.ref = "car-app" }
car-app-projected  = { group = "androidx.car.app", name = "app",            version.ref = "car-app" }  // phone side
car-app-testing    = { group = "androidx.car.app", name = "app-testing",    version.ref = "car-app" }
```

Use `app-automotive` for AAOS native apps; `app` for phone-projection (Android Auto) apps.
The API surface is identical — the difference is the deployment target.

## Manifest Setup

```xml
<!-- For phone-projection (Android Auto) -->
<service
    android:name=".MyCarAppService"
    android:exported="true">
    <intent-filter>
        <action android:name="androidx.car.app.CarAppService" />
        <category android:name="androidx.car.app.category.NAVIGATION" />
        <!-- or: POI, PARKING, CHARGING, IOT, WEATHER -->
    </intent-filter>
</service>

<!-- Declare min Car API level -->
<meta-data
    android:name="androidx.car.app.minCarApiLevel"
    android:value="3" />

<!-- automotive_app_desc.xml for AAOS -->
<meta-data
    android:name="com.android.automotive"
    android:resource="@xml/automotive_app_desc" />
```

```xml
<!-- res/xml/automotive_app_desc.xml -->
<automotiveApp>
    <uses name="template" />
</automotiveApp>
```

## CarAppService and Session

```kotlin
class MyCarAppService : CarAppService() {
    override fun createHostValidator() = HostValidator.ALLOW_ALL_HOSTS_VALIDATOR  // dev only
    // Production: use HostValidator.Builder().addAllowedHosts(CarAppHostInfo).build()

    override fun onCreateSession(): Session = MyCarSession()
}

class MyCarSession : Session() {
    override fun onCreateScreen(intent: Intent): Screen {
        // intent carries the launch Intent (e.g., from a map app or voice command)
        return HomeScreen(carContext)
    }
}
```

`Session` = one connection to the car host. `Screen` = one visible screen (analogous to
Activity/Fragment). The car host manages the back stack of Screens.

## Screen and Templates

```kotlin
class HomeScreen(carContext: CarContext) : Screen(carContext) {

    override fun onGetTemplate(): Template {
        val listBuilder = ItemList.Builder()

        listBuilder.addItem(
            Row.Builder()
                .setTitle("Start Session")
                .addText("Begin recording")
                .setOnClickListener { screenManager.push(SessionScreen(carContext)) }
                .build()
        )

        listBuilder.addItem(
            Row.Builder()
                .setTitle("Session History")
                .addText("View past sessions")
                .setOnClickListener { screenManager.push(HistoryScreen(carContext)) }
                .build()
        )

        return ListTemplate.Builder()
            .setTitle("My App")
            .setSingleList(listBuilder.build())
            .setHeaderAction(Action.APP_ICON)
            .build()
    }
}
```

Key rules:
- `onGetTemplate()` is called on the **main thread** — never do I/O here.
- Call `invalidate()` when data changes to trigger a fresh `onGetTemplate()` call.
- `screenManager.push()` to navigate forward; `screenManager.pop()` to go back.

## Navigation Template (Turn-by-Turn)

For apps in the NAVIGATION category, use `NavigationTemplate` while routing is active:

```kotlin
class NavigationScreen(carContext: CarContext) : Screen(carContext), SurfaceCallback {

    override fun onGetTemplate(): Template {
        val navigationInfo = TravelEstimate.create(
            Distance.create(1.2, Distance.UNIT_KILOMETERS),
            DateTimeWithZone.create(Instant.now().plusSeconds(300), ZoneId.systemDefault())
        )

        val maneuver = Maneuver.Builder(Maneuver.TYPE_TURN_LEFT)
            .setRoundaboutExitNumber(0)
            .build()

        val step = Step.Builder("Turn left onto Main Street")
            .setManeuver(maneuver)
            .setRoad("Main Street")
            .build()

        return NavigationTemplate.Builder()
            .setNavigationInfo(
                RoutingInfo.Builder()
                    .setCurrentStep(step, Distance.create(300, Distance.UNIT_METERS))
                    .setNextStep(nextStep)
                    .build()
            )
            .setDestinationTravelEstimate(navigationInfo)
            .setActionStrip(
                ActionStrip.Builder()
                    .addAction(Action.Builder().setTitle("Stop").setOnClickListener { endNavigation() }.build())
                    .build()
            )
            .build()
    }
}
```

## Voice Interaction

Respond to voice queries by registering a `SearchTemplate` or handling intents in `onCreateScreen`:

```kotlin
override fun onCreateScreen(intent: Intent): Screen {
    // CarContext.ACTION_NAVIGATE fires when user says "Navigate to X via MyApp"
    if (intent.action == CarContext.ACTION_NAVIGATE) {
        val address = intent.getStringExtra(CarContext.EXTRA_NAVIGATE_INTENT_ADDRESS)
        return NavigationScreen(carContext, destinationAddress = address)
    }
    return HomeScreen(carContext)
}
```

For voice search within your app:

```kotlin
class SearchScreen(carContext: CarContext) : Screen(carContext) {
    private var results: List<SearchResult> = emptyList()

    override fun onGetTemplate(): Template =
        SearchTemplate.Builder(object : SearchTemplate.SearchCallback {
            override fun onSearchTextChanged(searchText: String) {
                performSearch(searchText)
            }
            override fun onSearchSubmitted(searchText: String) {
                performSearch(searchText)
            }
        })
        .setHeaderAction(Action.BACK)
        .setShowKeyboardByDefault(false)  // DO: don't auto-show keyboard while driving
        .setItemList(buildResultsList())
        .build()

    private fun performSearch(query: String) {
        // Launch coroutine, update results, then invalidate()
        lifecycleScope.launch {
            results = repository.search(query)
            invalidate()
        }
    }
}
```

## Distraction Optimization Rules

The car host enforces these automatically, but design for them:

- **List items**: max 6 while `DrivingStatus.MOVING`; unlimited while parked
- **Row text**: 2 lines max
- **Input**: no free-text input while driving — use search template with auto-complete
- **Actions**: max 4 in an `ActionStrip`
- **Screen push depth**: max 5 screens on the back stack

Check driving state in your UI logic:

```kotlin
val drivingState = carContext.getCarService(AppManager::class.java)
// Or via CarInfo
val carInfo = carContext.getCarService(CarInfo::class.java)
carInfo.fetchModel(carContext.mainExecutor) { model -> /* use model info */ }
```

## Map Surface (Custom Drawing)

For drawing on the car map surface (NavigationTemplate):

```kotlin
class MyNavigationScreen(carContext: CarContext) : Screen(carContext), SurfaceCallback {

    override fun onSurfaceAvailable(surfaceContainer: SurfaceContainer) {
        val surface = surfaceContainer.surface ?: return
        // Draw custom overlays on the surface
    }

    override fun onSurfaceDestroyed(surfaceContainer: SurfaceContainer) {
        // Release drawing resources
    }
}
```

Register via `AppManager`:

```kotlin
carContext.getCarService(AppManager::class.java).setSurfaceCallback(this)
```

## Testing

Use `SessionController` and `ScreenController` from `car-app-testing`:

```kotlin
@Test
fun homeScreen_showsStartSession() {
    val carContext = TestCarContext.createCarContext(ApplicationProvider.getApplicationContext())
    val screen = HomeScreen(carContext)
    val controller = ScreenController.of(screen)

    controller.create().start().resume()
    val template = controller.get().onGetTemplate() as ListTemplate
    val items = template.singleList?.items ?: emptyList()

    assertThat(items).hasSize(2)
    assertThat(items[0].title?.toString()).isEqualTo("Start Session")
}
```

## Anti-Patterns

| Symptom | Root cause | Fix |
|---|---|---|
| App not visible in Android Auto | Missing `<category>` in service intent-filter | Add correct `androidx.car.app.category.*` |
| Template rejected by host | I/O or slow work in `onGetTemplate()` | Move all data loading off the main thread; call `invalidate()` after |
| List items truncated to 6 while driving | DO enforcement | Expected behavior; design for 6-item lists |
| Voice intent not received | Missing `ACTION_NAVIGATE` handling | Handle in `onCreateScreen(intent)` |
| Screen push fails | Back stack depth > 5 | Pop screens before pushing when deep in navigation |
| `SurfaceCallback` never called | Forgot `setSurfaceCallback` in `onCreateScreen` | Call `AppManager.setSurfaceCallback(this)` in `onStart` |
| AAOS app not installing | Missing `automotive_app_desc.xml` or wrong meta-data key | Verify both `<meta-data>` entries in manifest |
