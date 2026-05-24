---
name: migrate-xml-views-to-jetpack-compose
description: "Use this when: migrate XML layout to Compose, convert XML View to Jetpack Compose, replace XML UI with Compose, interop XML and Compose, ComposeView in XML, AndroidView in Compose. Provides a structured workflow for migrating an Android XML View to Jetpack
  Compose. This skill details the step-by-step process, from planning and dependency
  setup, to theming and layout migration, validation and XML cleanup. Use this skill
  when you need to migrate an XML View to Jetpack Compose in an Android project. It
  solves the problem of converting the UI of a legacy XML View into modern, declarative
  Compose components while maintaining interoperability."
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-05-06'
  keywords:
  - Jetpack Compose
  - migration
  - XML
  - Views
  - interoperability
  - incremental adoption
  - UI development
---

This skill guides through the process of migrating an existing Android XML View
to Jetpack Compose. It performs a stable, safe and visually consistent
transition by following a structured, 10-step methodology. This skill migrates
UI (XML to Jetpack Compose) only.

## ROUTING

| User signal | Start at |
|-------------|----------|
| Specifies a target XML layout to migrate | → Step 2 (Analyze project and layout) |
| Asks "which screen should I migrate first?" / no target named | → Step 1 (Identify optimal candidate) |
| Already started, asks about Compose setup / dependencies | → Step 5 |
| Already started, asks about theming | → Step 6 |
| Has Compose version, asks how to validate visual parity | → Step 8 (Validate the migration) |
| Migration done, asks how to remove old XML | → Step 10 (XML code removal) |
| Asks about XML→Compose interop / hybrid screens | → Step 7 + reference on interop |

## Objective

To systematically convert a single legacy XML layout into modern, declarative
Jetpack Compose UI while maintaining pixel-perfect visual parity and functional
integrity.

## Summary of the 10-step migration process

1. **Identify the optimal XML candidate for migration**
2. **Analyze the project and layout**
3. **Create a plan**
4. **Capture the XML View UI**
5. **Set up Compose dependencies and compiler**
6. **Set up Compose theming**
7. **Migrate the XML layout to Compose**
8. **Validate the migration**
9. **Replace usages**
10. **XML code removal**

## Detailed steps

### Step 1: Identify the optimal XML candidate for migration

If the user has explicitly specified a target XML layout, proceed to Step 2.
Otherwise, analyze the codebase to identify the best candidate for migration by
following the logic in [references/identify-optimal-xml-candidate.md](references/identify-optimal-xml-candidate.md).

### Step 2: Analyze the project and layout

Analyze the identified XML View's structure, hierarchy, and implementation
details.
Use [references/analysis-of-the-project-and-layout.md](references/analysis-of-the-project-and-layout.md) to
guide your technical audit of the layout and surrounding project context.

### Step 3: Create a plan

Using the outputs and analysis done in the Step 1 and 2, generate a
step-by-step plan for the migration. If you support user interaction, present
to the user and ask for approval before proceeding. If user interaction is not
supported, proceed to Step 4 following the generated plan.

### Step 4: Capture the XML View UI

**IF** you support user interaction, ask the user to upload a screenshot of the
XML View UI or provide an absolute path to a file. Use this image as a visual
reference for the layout migration in Step 7.
**ELSE IF** you are able to run an Android emulator, locate an existing
screenshot test for the XML candidate. If none exists, create one using the
existing project testing framework. If no framework exists,
use **UI Automator** or **Espresso** to create a screenshot test with minimum
required setup. Run the test and take a baseline screenshot of the XML UI.
**ELSE** proceed to Step 5.

### Step 5: Set up Compose dependencies and compiler

Check `build.gradle` or `libs.versions.toml` for Compose dependencies and
compiler setup. If missing, use
[Setup Compose Dependencies and Compiler](references/android/develop/ui/compose/setup-compose-dependencies-and-compiler.md).
Run a sync to ensure dependencies resolve without errors.

### Step 6: Set up Compose theming

If the project already has Compose theming set up, proceed to Step 7. If Compose
theming is missing, initialize it. For Material-based projects, follow
[Material 3 migration guidelines](references/android/develop/ui/compose/designsystems/migrate-xml-theme-to-compose.md).
For custom design systems, apply expert judgment to migrate XML theming and
match existing styles.
**Constraints:** Do not migrate the entire theme. Implement only the minimum
theming required for the specific XML candidate. Maintain original XML themes
for interoperability. Maintain existing project code conventions, patterns,
names and values.

### Step 7: Migrate the XML View to Compose

Convert the XML candidate to Jetpack Compose code, referencing
[references/xml-layout-migration.md](references/xml-layout-migration.md) and the image from Step 4.
You must include a **Compose Preview** for the newly created composable to
facilitate visual verification.

### Step 8: Replace usages

Replace the usages of the migrated XML layout to use the new Compose component.

- To add Compose in Views, use [Compose in Views](references/android/develop/ui/compose/migrate/interoperability-apis/compose-in-views.md).
- To add Views in Compose, use [Views in Compose](references/android/develop/ui/compose/migrate/interoperability-apis/views-in-compose.md).

### Step 9: Validate the migration

Compare the baseline screenshot image from Step 4 with the rendered Compose
Preview of the new composable. Ignore string content; focus on layout and
styling. Iterate on the Compose code until visual parity is achieved. Once
verified, write a Compose UI test for the new composable.

### Step 10: XML code removal

Delete the migrated XML file and its associated legacy tests. **Caution:** Only
remove code and resources that are not referenced by other parts of the project.

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
