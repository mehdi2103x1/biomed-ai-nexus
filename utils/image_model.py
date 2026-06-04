"""
utils.image_model
=================
Deep-learning image module: a pretrained MobileNetV2 CNN + Grad-CAM.

The professor's brief asks for a *demonstration* CNN that can: preprocess an
uploaded biomedical image, run inference, report class probabilities and
inference time, and explain the decision with a Grad-CAM heatmap.

TensorFlow is imported **lazily** (inside methods) so that the rest of the
Streamlit app — tabular prediction, dashboard, evaluation — keeps working even
on a machine where TensorFlow is not installed. ``tensorflow_available()`` lets
the UI show a friendly message instead of crashing.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from config import GRADCAM_LAYER, IMAGE_SIZE
from utils.logger import get_logger

log = get_logger("image_model")


def tensorflow_available() -> bool:
    """True if TensorFlow is installed on this machine (without importing it)."""
    import importlib.util
    return importlib.util.find_spec("tensorflow") is not None


@dataclass
class ImagePrediction:
    """Container for one image inference result."""

    top_labels: list[str]
    top_probs: list[float]
    inference_ms: float
    heatmap: np.ndarray | None        # HxW float [0,1], or None if Grad-CAM failed


class CNNImageClassifier:
    """Wraps a pretrained MobileNetV2 and provides Grad-CAM explanations.

    The model is built once and cached on the instance. In the Streamlit layer
    the whole object is cached with ``@st.cache_resource``.
    """

    def __init__(self) -> None:
        self._model = None
        self._preprocess = None
        self._decode = None

    # ------------------------------------------------------------------ #
    def load(self) -> "CNNImageClassifier":
        """Build MobileNetV2 (ImageNet weights). Downloads weights on first run."""
        from tensorflow.keras.applications.mobilenet_v2 import (
            MobileNetV2, preprocess_input, decode_predictions,
        )

        self._model = MobileNetV2(weights="imagenet", include_top=True)
        self._preprocess = preprocess_input
        self._decode = decode_predictions
        log.info("MobileNetV2 loaded (input=%s)", IMAGE_SIZE)
        return self

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    # ------------------------------------------------------------------ #
    def preprocess(self, image: "np.ndarray") -> np.ndarray:
        """Resize -> RGB -> MobileNetV2 normalisation. Returns a (1,224,224,3) batch.

        ``image`` is an HxWx3 uint8 RGB array (as produced by PIL/OpenCV).
        """
        import cv2

        if image.ndim == 2:                      # greyscale -> 3 channels
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        if image.shape[-1] == 4:                 # RGBA -> RGB
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        resized = cv2.resize(image, IMAGE_SIZE, interpolation=cv2.INTER_AREA)
        batch = np.expand_dims(resized.astype("float32"), axis=0)
        return self._preprocess(batch.copy())    # type: ignore[misc]

    # ------------------------------------------------------------------ #
    def predict(self, image: np.ndarray, top_k: int = 5) -> ImagePrediction:
        """Run inference + Grad-CAM and measure the inference time."""
        if not self.is_ready:
            raise RuntimeError("CNN model not loaded. Call load() first.")

        batch = self.preprocess(image)
        t0 = time.perf_counter()
        preds = self._model.predict(batch, verbose=0)   # type: ignore[union-attr]
        inference_ms = (time.perf_counter() - t0) * 1000.0

        decoded = self._decode(preds, top=top_k)[0]      # type: ignore[misc]
        labels = [d[1].replace("_", " ") for d in decoded]
        probs = [float(d[2]) for d in decoded]

        heatmap = None
        try:
            class_idx = int(np.argmax(preds[0]))
            heatmap = self._grad_cam(batch, class_idx)
        except Exception as exc:                          # pragma: no cover
            log.warning("Grad-CAM failed: %s", exc)

        return ImagePrediction(labels, probs, inference_ms, heatmap)

    # ------------------------------------------------------------------ #
    def _grad_cam(self, batch: np.ndarray, class_idx: int,
                  layer_name: str = GRADCAM_LAYER) -> np.ndarray:
        """Compute a Grad-CAM heatmap for ``class_idx`` (returns HxW in [0,1])."""
        import tensorflow as tf

        grad_model = tf.keras.models.Model(
            self._model.inputs,                           # type: ignore[union-attr]
            [self._model.get_layer(layer_name).output,    # type: ignore[union-attr]
             self._model.output],                         # type: ignore[union-attr]
        )
        with tf.GradientTape() as tape:
            conv_out, predictions = grad_model(batch)
            loss = predictions[:, class_idx]

        grads = tape.gradient(loss, conv_out)
        pooled = tf.reduce_mean(grads, axis=(0, 1, 2))
        conv_out = conv_out[0]
        heatmap = conv_out @ pooled[..., tf.newaxis]
        heatmap = tf.squeeze(heatmap)
        heatmap = tf.maximum(heatmap, 0) / (tf.reduce_max(heatmap) + 1e-8)
        return heatmap.numpy()


def overlay_heatmap(image: np.ndarray, heatmap: np.ndarray,
                    alpha: float = 0.4) -> np.ndarray:
    """Blend a Grad-CAM heatmap over the original RGB image (returns uint8 RGB)."""
    import cv2

    h, w = image.shape[:2]
    hm = cv2.resize(heatmap, (w, h))
    hm = np.uint8(255 * hm)
    hm_color = cv2.applyColorMap(hm, cv2.COLORMAP_JET)
    hm_color = cv2.cvtColor(hm_color, cv2.COLOR_BGR2RGB)
    blended = cv2.addWeighted(image.astype("uint8"), 1 - alpha, hm_color, alpha, 0)
    return blended
