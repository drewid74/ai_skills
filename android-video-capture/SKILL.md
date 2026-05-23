---
name: android-video-capture
description: |
  Android video and photo capture using CameraX: lifecycle-aware camera setup, Compose camera
  preview, VideoCapture use case with MediaStore output, simultaneous preview + capture,
  camera selector, torch control, and recording state management.
  Use this when: building a camera screen in Compose, implementing video recording with audio,
  saving video to MediaStore (gallery), capturing photos, switching front/back cameras,
  controlling the torch/flashlight, or managing concurrent camera use cases.
license: Apache-2.0
metadata:
  author: Drew Fairweather
  last-updated: '2026-05-10'
  based-on: https://github.com/android/skills
  keywords:
  - CameraX
  - VideoCapture
  - ImageCapture
  - Compose
  - PreviewView
  - MediaStore
  - camera
  - recording
  - video
  - photo
  - torch
  - lifecycle-aware
---

> **Lineage:** Built upon and expanded from the official Android group skills repository at
> [github.com/android/skills](https://github.com/android/skills). That repo covers areas where
> evaluations show LLMs underperform on standard Android patterns. This skill extends that
> foundation into CameraX video and photo capture — an area the official set references but
> does not cover in depth.

## Overview

CameraX abstracts the raw Camera2 API into lifecycle-aware use cases. Bind use cases to the
`ProcessCameraProvider` once and let CameraX manage start/stop automatically with the Activity
or Fragment lifecycle. Do not manage `CameraDevice` or `CaptureSession` directly.

## Dependencies

```kotlin
// libs.versions.toml
[versions]
camerax = "1.3.4"

[libraries]
camerax-core    = { group = "androidx.camera", name = "camera-core",    version.ref = "camerax" }
camerax-camera2 = { group = "androidx.camera", name = "camera-camera2", version.ref = "camerax" }
camerax-lifecycle = { group = "androidx.camera", name = "camera-lifecycle", version.ref = "camerax" }
camerax-video   = { group = "androidx.camera", name = "camera-video",   version.ref = "camerax" }
camerax-view    = { group = "androidx.camera", name = "camera-view",    version.ref = "camerax" }
camerax-extensions = { group = "androidx.camera", name = "camera-extensions", version.ref = "camerax" }
```

## Permissions

```xml
<!-- AndroidManifest.xml -->
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<!-- READ_MEDIA_VIDEO only needed if reading existing videos; not needed for writing -->
```

Request at runtime before binding any use case:

```kotlin
val cameraPermissions = buildList {
    add(Manifest.permission.CAMERA)
    if (needsAudio) add(Manifest.permission.RECORD_AUDIO)
}.toTypedArray()
```

## Camera Preview in Compose

Use `AndroidView` to host a `PreviewView` inside Compose:

```kotlin
@Composable
fun CameraPreview(
    onUseCasesBound: (ProcessCameraProvider, Camera) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    AndroidView(
        modifier = modifier,
        factory = { ctx ->
            PreviewView(ctx).apply {
                scaleType = PreviewView.ScaleType.FILL_CENTER
                implementationMode = PreviewView.ImplementationMode.COMPATIBLE
            }
        },
        update = { previewView ->
            val cameraProviderFuture = ProcessCameraProvider.getInstance(context)
            cameraProviderFuture.addListener({
                val cameraProvider = cameraProviderFuture.get()
                bindCamera(cameraProvider, lifecycleOwner, previewView, onUseCasesBound)
            }, ContextCompat.getMainExecutor(context))
        }
    )
}

private fun bindCamera(
    cameraProvider: ProcessCameraProvider,
    lifecycleOwner: LifecycleOwner,
    previewView: PreviewView,
    onBound: (ProcessCameraProvider, Camera) -> Unit
) {
    val preview = Preview.Builder().build().also {
        it.setSurfaceProvider(previewView.surfaceProvider)
    }

    val recorder = Recorder.Builder()
        .setQualitySelector(QualitySelector.from(Quality.HIGHEST))
        .build()
    val videoCapture = VideoCapture.withOutput(recorder)

    val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

    cameraProvider.unbindAll()
    val camera = cameraProvider.bindToLifecycle(
        lifecycleOwner, cameraSelector, preview, videoCapture
    )
    onBound(cameraProvider, camera)
}
```

Never call `bindToLifecycle` before `unbindAll` — stale use cases cause `IllegalStateException`.

## Video Recording

```kotlin
class CameraViewModel : ViewModel() {
    private var activeRecording: Recording? = null
    private val _recordingState = MutableStateFlow<RecordingState>(RecordingState.Idle)
    val recordingState: StateFlow<RecordingState> = _recordingState

    fun startRecording(
        context: Context,
        videoCapture: VideoCapture<Recorder>
    ) {
        val name = "video_${System.currentTimeMillis()}"
        val contentValues = ContentValues().apply {
            put(MediaStore.Video.Media.DISPLAY_NAME, name)
            put(MediaStore.Video.Media.MIME_TYPE, "video/mp4")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                put(MediaStore.Video.Media.RELATIVE_PATH, "Movies/MyApp")
            }
        }

        val mediaStoreOutput = MediaStoreOutputOptions.Builder(
            context.contentResolver,
            MediaStore.Video.Media.EXTERNAL_CONTENT_URI
        ).setContentValues(contentValues).build()

        activeRecording = videoCapture.output
            .prepareRecording(context, mediaStoreOutput)
            .withAudioEnabled()   // requires RECORD_AUDIO permission
            .start(ContextCompat.getMainExecutor(context)) { event ->
                when (event) {
                    is VideoRecordEvent.Start  -> _recordingState.value = RecordingState.Recording
                    is VideoRecordEvent.Finalize -> {
                        if (event.hasError()) {
                            _recordingState.value = RecordingState.Error(event.error)
                        } else {
                            _recordingState.value = RecordingState.Saved(event.outputResults.outputUri)
                        }
                    }
                    else -> {}
                }
            }
    }

    fun stopRecording() {
        activeRecording?.stop()
        activeRecording = null
    }

    fun pauseRecording() = activeRecording?.pause()
    fun resumeRecording() = activeRecording?.resume()

    override fun onCleared() {
        super.onCleared()
        activeRecording?.stop()
    }
}

sealed class RecordingState {
    object Idle : RecordingState()
    object Recording : RecordingState()
    data class Saved(val uri: Uri) : RecordingState()
    data class Error(val errorCode: Int) : RecordingState()
}
```

Always call `stop()` in `onCleared()` — an abandoned `Recording` leaks the camera and file.

## Photo Capture

```kotlin
fun takePhoto(
    context: Context,
    imageCapture: ImageCapture,
    onSaved: (Uri) -> Unit,
    onError: (ImageCaptureException) -> Unit
) {
    val name = "photo_${System.currentTimeMillis()}"
    val contentValues = ContentValues().apply {
        put(MediaStore.Images.Media.DISPLAY_NAME, name)
        put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/MyApp")
        }
    }

    val outputOptions = ImageCapture.OutputFileOptions.Builder(
        context.contentResolver,
        MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
        contentValues
    ).build()

    imageCapture.takePicture(
        outputOptions,
        ContextCompat.getMainExecutor(context),
        object : ImageCapture.OnImageSavedCallback {
            override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                output.savedUri?.let(onSaved)
            }
            override fun onError(exc: ImageCaptureException) = onError(exc)
        }
    )
}
```

## Simultaneous Preview + Video + Photo

CameraX guarantees `Preview + VideoCapture<Recorder>` work together on all devices. Adding
`ImageCapture` may require a lower resolution on some hardware. Bind all three, but check
`CameraInfo.isUseCaseCombinationSupported()` at runtime if targeting older devices:

```kotlin
val useCases = mutableListOf<UseCase>(preview, videoCapture)
if (cameraInfo.isUseCaseCombinationSupported(preview, videoCapture, imageCapture)) {
    useCases.add(imageCapture)
}
cameraProvider.bindToLifecycle(lifecycleOwner, cameraSelector, *useCases.toTypedArray())
```

## Camera Selector

```kotlin
// Back camera (default)
val selector = CameraSelector.DEFAULT_BACK_CAMERA

// Front camera
val selector = CameraSelector.DEFAULT_FRONT_CAMERA

// Dynamic switching (e.g., on button tap)
fun flipCamera(current: CameraSelector): CameraSelector =
    if (current == CameraSelector.DEFAULT_BACK_CAMERA)
        CameraSelector.DEFAULT_FRONT_CAMERA
    else
        CameraSelector.DEFAULT_BACK_CAMERA
```

After switching, call `cameraProvider.unbindAll()` then rebind with the new selector.
Do not attempt to switch while recording — stop the recording first.

## Torch Control

```kotlin
// camera is the Camera object returned by bindToLifecycle
fun setTorch(camera: Camera, enabled: Boolean) {
    if (camera.cameraInfo.hasFlashUnit()) {
        camera.cameraControl.enableTorch(enabled)
    }
}
```

Observe torch state:

```kotlin
camera.cameraInfo.torchState.observe(lifecycleOwner) { state ->
    val isOn = state == TorchState.ON
}
```

## Quality Selection

```kotlin
val qualitySelector = QualitySelector.fromOrderedList(
    listOf(Quality.UHD, Quality.FHD, Quality.HD, Quality.SD),
    FallbackStrategy.lowerQualityOrHigherThan(Quality.SD)
)
val recorder = Recorder.Builder()
    .setQualitySelector(qualitySelector)
    .build()
```

`FallbackStrategy.lowerQualityOrHigherThan` means: try UHD→FHD→HD→SD in order; if none
are available, pick the nearest quality above SD.

## Anti-Patterns

| Symptom | Root cause | Fix |
|---|---|---|
| `IllegalStateException` on bind | Forgot `unbindAll()` before re-binding | Always call `cameraProvider.unbindAll()` first |
| Black preview in Compose | `implementationMode = PERFORMANCE` on some devices | Switch to `COMPATIBLE` mode |
| `VideoRecordEvent.Finalize` never fires | `activeRecording` goes out of scope / GC'd | Hold a strong reference in ViewModel |
| No audio in recording | `RECORD_AUDIO` permission not held at record time | Check permission before `withAudioEnabled()` |
| Recording crashes on orientation change | `startRecording` called on Activity recreate | Keep `activeRecording` in ViewModel, not Activity |
| `takePicture` and `videoCapture` conflict | Trying to capture photo mid-recording | Pause recording before capture, or use separate use case lifecycle |
| Low resolution video | Default `Recorder` picks SD | Set explicit `QualitySelector` |
