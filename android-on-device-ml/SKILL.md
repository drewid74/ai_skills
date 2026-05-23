---
name: android-on-device-ml
description: |
  On-device machine learning for Android: ML Kit (text recognition, object detection, pose
  estimation, face detection), TensorFlow Lite (custom model inference with GPU/NNAPI delegate),
  and MediaPipe Tasks API (gesture recognition, image classification, hand/face/pose landmarking).
  Covers model packaging, interpreter lifecycle, input/output tensor handling, Compose integration,
  and performance optimization for real-time inference.
  Use this when: running ML inference on-device without a server, integrating ML Kit APIs,
  loading a custom TFLite model, using MediaPipe for vision tasks, building a camera + ML
  pipeline, optimizing inference latency, or handling model versioning and asset delivery.
license: Apache-2.0
metadata:
  author: Drew Fairweather
  last-updated: '2026-05-10'
  based-on: https://github.com/android/skills
  keywords:
  - machine learning
  - ML Kit
  - TensorFlow Lite
  - TFLite
  - MediaPipe
  - on-device inference
  - GPU delegate
  - NNAPI
  - object detection
  - pose estimation
  - image classification
  - camera pipeline
  - model asset
---

> **Lineage:** Built upon and expanded from the official Android group skills repository at
> [github.com/android/skills](https://github.com/android/skills). That repo covers areas where
> evaluations show LLMs underperform on standard Android patterns. This skill extends that
> foundation into on-device ML inference — an area the official set does not cover.

## Overview

Three libraries, three use cases:

| Library | When to use |
|---|---|
| **ML Kit** | Google's pre-built models (OCR, face detection, barcode, pose, translation). Zero model management. |
| **TensorFlow Lite** | Custom or fine-tuned `.tflite` models. Full control over input/output tensors. |
| **MediaPipe Tasks** | Vision tasks (hand, face, pose landmarks; gesture; object detection). Higher-level API than raw TFLite, GPU-accelerated. |

## ML Kit — Text Recognition (Example)

```kotlin
// libs.versions.toml
[libraries]
mlkit-text = { group = "com.google.mlkit", name = "text-recognition", version = "16.0.1" }
```

```kotlin
fun recognizeText(image: InputImage, onResult: (String) -> Unit, onError: (Exception) -> Unit) {
    val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)

    recognizer.process(image)
        .addOnSuccessListener { result ->
            val text = result.textBlocks.joinToString("\n") { it.text }
            onResult(text)
        }
        .addOnFailureListener(onError)
}
```

Create `InputImage` from a `Bitmap`, `ByteBuffer`, `MediaImage`, or `Uri`:

```kotlin
// From Bitmap
val image = InputImage.fromBitmap(bitmap, rotationDegrees)

// From CameraX ImageProxy (use case: ImageAnalysis)
val image = InputImage.fromMediaImage(imageProxy.image!!, imageProxy.imageInfo.rotationDegrees)
```

## ML Kit — Object Detection

```kotlin
// libs.versions.toml
[libraries]
mlkit-object = { group = "com.google.mlkit", name = "object-detection", version = "17.0.2" }
```

```kotlin
val options = ObjectDetectorOptions.Builder()
    .setDetectorMode(ObjectDetectorOptions.STREAM_MODE)   // for live camera
    .enableMultipleObjects()
    .enableClassification()
    .build()

val detector = ObjectDetection.getClient(options)

// In CameraX ImageAnalysis callback:
fun analyze(imageProxy: ImageProxy) {
    val image = InputImage.fromMediaImage(imageProxy.image!!, imageProxy.imageInfo.rotationDegrees)
    detector.process(image)
        .addOnSuccessListener { objects ->
            objects.forEach { obj ->
                val box = obj.boundingBox          // Rect in image coordinates
                val label = obj.labels.firstOrNull()?.text
            }
        }
        .addOnCompleteListener { imageProxy.close() }  // MUST close
}
```

Always call `imageProxy.close()` in `addOnCompleteListener` — not in `addOnSuccessListener`.
If you close only on success, failures leak the buffer and stall the camera pipeline.

## TensorFlow Lite — Custom Model

### Asset Packaging

Place your `.tflite` file in `src/main/assets/`. Disable compression (tflite files are already
compressed — compressing twice wastes APK build time and increases size):

```kotlin
// app/build.gradle.kts
android {
    androidResources {
        noCompress += "tflite"
    }
}
```

### Dependencies

```kotlin
// libs.versions.toml
[libraries]
tflite-task-vision = { group = "org.tensorflow", name = "tensorflow-lite-task-vision", version = "0.4.4" }
tflite-gpu         = { group = "org.tensorflow", name = "tensorflow-lite-gpu-delegate-plugin", version = "0.4.4" }
tflite-support     = { group = "org.tensorflow", name = "tensorflow-lite-support", version = "0.4.4" }
```

### Interpreter Lifecycle

```kotlin
class TfliteClassifier(context: Context) : AutoCloseable {
    private val interpreter: Interpreter

    init {
        val options = Interpreter.Options().apply {
            // GPU delegate for supported ops; falls back to CPU if not supported
            addDelegate(GpuDelegate())
            setNumThreads(4)
        }
        val model = loadModelFile(context, "my_model.tflite")
        interpreter = Interpreter(model, options)
    }

    private fun loadModelFile(context: Context, fileName: String): MappedByteBuffer {
        val fileDescriptor = context.assets.openFd(fileName)
        val inputStream = FileInputStream(fileDescriptor.fileDescriptor)
        return inputStream.channel.map(
            FileChannel.MapMode.READ_ONLY,
            fileDescriptor.startOffset,
            fileDescriptor.declaredLength
        )
    }

    fun classify(bitmap: Bitmap): List<ClassificationResult> {
        // Resize bitmap to model input size
        val resized = Bitmap.createScaledBitmap(bitmap, INPUT_WIDTH, INPUT_HEIGHT, true)

        // Build TensorImage for preprocessing
        val tensorImage = TensorImage(DataType.FLOAT32).also { it.load(resized) }
        val processor = ImageProcessor.Builder()
            .add(ResizeOp(INPUT_HEIGHT, INPUT_WIDTH, ResizeOp.ResizeMethod.BILINEAR))
            .add(NormalizeOp(127.5f, 127.5f))   // normalize to [-1, 1]
            .build()
        val processedImage = processor.process(tensorImage)

        // Run inference
        val output = Array(1) { FloatArray(NUM_CLASSES) }
        interpreter.run(processedImage.buffer, output)

        return output[0].mapIndexed { i, score ->
            ClassificationResult(LABELS[i], score)
        }.sortedByDescending { it.score }
    }

    override fun close() = interpreter.close()

    companion object {
        const val INPUT_WIDTH = 224
        const val INPUT_HEIGHT = 224
        const val NUM_CLASSES = 1000
    }
}

data class ClassificationResult(val label: String, val score: Float)
```

Create one `Interpreter` instance and reuse it — creation is expensive. Close it in
`ViewModel.onCleared()` or when the owning scope is destroyed.

### NNAPI Delegate

```kotlin
val nnApiDelegate = NnApiDelegate()
val options = Interpreter.Options().addDelegate(nnApiDelegate)
// Close nnApiDelegate alongside interpreter
```

Use NNAPI for deployment on devices with dedicated NPUs (Pixel Neural Core, Snapdragon NPU).
Profile before assuming it's faster — on some devices CPU is faster for small models.

## MediaPipe Tasks — Pose Landmarking (Example)

```kotlin
// libs.versions.toml
[libraries]
mediapipe-tasks-vision = { group = "com.google.mediapipe", name = "tasks-vision", version = "0.10.14" }
```

```kotlin
class PoseLandmarker(context: Context) : AutoCloseable {
    private val landmarker: com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarker

    init {
        val options = com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarker.PoseLandmarkerOptions.builder()
            .setBaseOptions(
                BaseOptions.builder()
                    .setModelAssetPath("pose_landmarker_lite.task")   // download from MediaPipe
                    .setDelegate(Delegate.GPU)
                    .build()
            )
            .setRunningMode(RunningMode.LIVE_STREAM)
            .setNumPoses(1)
            .setResultListener { result, _ -> onResult(result) }
            .build()

        landmarker = com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarker.createFromOptions(context, options)
    }

    fun detect(imageProxy: ImageProxy) {
        val mpImage = BitmapImageBuilder(imageProxy.toBitmap()).build()
        landmarker.detectAsync(mpImage, SystemClock.uptimeMillis())
        imageProxy.close()
    }

    private fun onResult(result: PoseLandmarkerResult) {
        result.landmarks().firstOrNull()?.let { landmarks ->
            // landmarks[0] = nose, [11] = left shoulder, [12] = right shoulder, etc.
            val nose = landmarks[0]  // NormalizedLandmark: x, y, z all in [0,1]
        }
    }

    override fun close() = landmarker.close()
}
```

MediaPipe `.task` bundle files (which include the model + metadata) are downloaded from
[developers.google.com/mediapipe/solutions](https://developers.google.com/mediapipe/solutions)
and placed in `src/main/assets/`.

## CameraX + ML Pipeline

Wire CameraX `ImageAnalysis` to any ML pipeline:

```kotlin
val imageAnalysis = ImageAnalysis.Builder()
    .setTargetResolution(Size(640, 480))
    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)  // critical: drop stale frames
    .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_RGBA_8888)
    .build()
    .also { analysis ->
        analysis.setAnalyzer(Executors.newSingleThreadExecutor()) { imageProxy ->
            // call your ML Kit, TFLite, or MediaPipe detector here
            myDetector.detect(imageProxy)
            // imageProxy.close() must be called inside the detector
        }
    }

cameraProvider.bindToLifecycle(lifecycleOwner, cameraSelector, preview, imageAnalysis)
```

`STRATEGY_KEEP_ONLY_LATEST` is mandatory for real-time inference — without it, the analyzer
queue backs up and introduces multi-second latency.

## Inference on Background Thread

Never run inference on the main thread. Use a dedicated single-thread executor or `Dispatchers.Default`:

```kotlin
class InferenceViewModel : ViewModel() {
    private val inferenceExecutor = Executors.newSingleThreadExecutor()
    private val _results = MutableStateFlow<List<ClassificationResult>>(emptyList())
    val results: StateFlow<List<ClassificationResult>> = _results

    fun classify(bitmap: Bitmap) {
        inferenceExecutor.submit {
            val results = classifier.classify(bitmap)
            _results.value = results
        }
    }

    override fun onCleared() {
        inferenceExecutor.shutdown()
        classifier.close()
    }
}
```

## Model Asset Delivery (Large Models)

For models >10MB, use Play Asset Delivery to avoid bloating the APK:

```kotlin
// build.gradle.kts (asset pack module)
plugins { id("com.android.asset-pack") }
assetPack {
    packName.set("ml_models")
    dynamicDelivery {
        deliveryType.set("install-time")
    }
}
```

```kotlin
// At runtime
val assetPackManager = AssetPackManagerFactory.getInstance(context)
// Check delivery status, then read from assetPackManager.getPackLocation("ml_models")
```

## Anti-Patterns

| Symptom | Root cause | Fix |
|---|---|---|
| Camera stalls / freezes after a few seconds | `imageProxy.close()` not called | Always close in `addOnCompleteListener`, not `addOnSuccessListener` |
| High inference latency on first call | Interpreter/GPU delegate not warmed up | Run one warmup inference on an empty input at init time |
| `UnsatisfiedLinkError` on TFLite | Missing native libs in release build | Add `-keep class org.tensorflow.**` to ProGuard rules |
| ML Kit model not bundled | Using unbundled variant without download trigger | Switch to bundled dependency or trigger model download before use |
| Out of memory during inference | Large intermediate tensors | Reduce input resolution; use quantized (INT8) model variant |
| MediaPipe `.task` file not found | Placed in `res/raw/` instead of `assets/` | Must be in `src/main/assets/` and referenced by filename only |
| GPU delegate crashes on older devices | Device GPU not supported by TFLite GPU delegate | Wrap delegate creation in try/catch; fall back to CPU |
