"""
utils.image_model
=================
Deep-learning image module: a pretrained **MobileNetV2** CNN served through
**ONNX Runtime**.

Why ONNX Runtime instead of TensorFlow? The image brief asks for a pretrained
CNN with preprocessing, inference, class probabilities, an inference-time
read-out and an explainability heatmap. TensorFlow is too heavy for free cloud
hosting (it broke the build). ONNX Runtime (~a few MB) runs the very same
MobileNetV2 architecture, so the full pipeline works online *and* locally.

Explainability uses **occlusion sensitivity**: patches of the image are masked
one at a time and the drop in the predicted-class probability is measured,
producing a heatmap of the regions the network relies on (a model-agnostic
cousin of Grad-CAM that needs no gradients).
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from config import IMAGE_SIZE, MODELS_DIR
from utils.logger import get_logger

log = get_logger("image_model")

_MODEL_PATH = MODELS_DIR / "cnn" / "mobilenetv2.onnx"
_LABELS_PATH = MODELS_DIR / "cnn" / "imagenet_classes.txt"

# torchvision-style ImageNet normalisation expected by the ONNX MobileNetV2.
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def onnx_available() -> bool:
    """True if ONNX Runtime is installed and the model file is present."""
    import importlib.util
    return (importlib.util.find_spec("onnxruntime") is not None
            and _MODEL_PATH.exists())


@dataclass
class ImagePrediction:
    """Container for one image inference result."""

    top_labels: list[str]
    top_probs: list[float]
    inference_ms: float
    heatmap: np.ndarray | None        # HxW float [0,1], or None if it failed


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


class CNNImageClassifier:
    """Pretrained MobileNetV2 (ONNX) with occlusion-based explainability.

    Cached on the Streamlit side with ``@st.cache_resource`` so the model is
    built only once per session.
    """

    def __init__(self) -> None:
        self._session = None
        self._input_name: str = ""
        self._labels: list[str] = []

    # ------------------------------------------------------------------ #
    def load(self) -> "CNNImageClassifier":
        """Create the ONNX Runtime session and load the ImageNet labels."""
        import onnxruntime as ort

        self._session = ort.InferenceSession(
            str(_MODEL_PATH), providers=["CPUExecutionProvider"]
        )
        self._input_name = self._session.get_inputs()[0].name
        self._labels = _LABELS_PATH.read_text(encoding="utf-8").splitlines()
        log.info("MobileNetV2 (ONNX) loaded — %d classes", len(self._labels))
        return self

    @property
    def is_ready(self) -> bool:
        return self._session is not None

    # ------------------------------------------------------------------ #
    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """RGB uint8 HxWx3 -> normalised (1,3,224,224) float32 batch."""
        import cv2

        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        if image.shape[-1] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        resized = cv2.resize(image, IMAGE_SIZE, interpolation=cv2.INTER_AREA)
        x = resized.astype(np.float32) / 255.0
        x = (x - _MEAN) / _STD
        x = np.transpose(x, (2, 0, 1))[np.newaxis, ...]   # HWC -> NCHW
        return np.ascontiguousarray(x, dtype=np.float32)

    def _run(self, batch: np.ndarray) -> np.ndarray:
        """Forward pass -> softmax probabilities (N, 1000)."""
        logits = self._session.run(None, {self._input_name: batch})[0]
        return _softmax(logits)

    # ------------------------------------------------------------------ #
    def predict(self, image: np.ndarray, top_k: int = 5,
                explain: bool = True) -> ImagePrediction:
        """Run inference (timed) and, optionally, an occlusion heatmap."""
        if not self.is_ready:
            raise RuntimeError("CNN model not loaded. Call load() first.")

        batch = self._preprocess(image)
        t0 = time.perf_counter()
        probs = self._run(batch)[0]
        inference_ms = (time.perf_counter() - t0) * 1000.0

        order = np.argsort(probs)[::-1][:top_k]
        labels = [self._labels[i] if i < len(self._labels) else str(i) for i in order]
        top_probs = [float(probs[i]) for i in order]

        heatmap = None
        if explain:
            try:
                heatmap = self._occlusion_saliency(image, int(order[0]),
                                                   float(probs[order[0]]))
            except Exception as exc:                      # pragma: no cover
                log.warning("Occlusion saliency failed: %s", exc)

        return ImagePrediction(labels, top_probs, inference_ms, heatmap)

    # ------------------------------------------------------------------ #
    def _occlusion_saliency(self, image: np.ndarray, class_idx: int,
                            base_prob: float, grid: int = 8) -> np.ndarray:
        """Mask each cell of a grid and measure the drop in class probability.

        All occluded variants are batched into a single ONNX call for speed.
        Returns a ``grid x grid`` heatmap normalised to [0, 1].
        """
        base = self._preprocess(image)[0]                 # (3,224,224)
        h, w = base.shape[1], base.shape[2]
        cell_h, cell_w = h // grid, w // grid

        variants = np.repeat(base[np.newaxis, ...], grid * grid, axis=0)
        for r in range(grid):
            for c in range(grid):
                variants[r * grid + c, :,
                         r * cell_h:(r + 1) * cell_h,
                         c * cell_w:(c + 1) * cell_w] = 0.0   # mask (mean ~ 0)

        probs = self._run(np.ascontiguousarray(variants))[:, class_idx]
        drop = np.clip(base_prob - probs, 0, None).reshape(grid, grid)
        if drop.max() > 0:
            drop = drop / drop.max()
        return drop


def overlay_heatmap(image: np.ndarray, heatmap: np.ndarray,
                    alpha: float = 0.45) -> np.ndarray:
    """Blend a saliency heatmap over the original RGB image (uint8 RGB out)."""
    import cv2

    h, w = image.shape[:2]
    hm = cv2.resize(heatmap.astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
    hm = np.clip(hm, 0, 1)
    hm_color = cv2.applyColorMap(np.uint8(255 * hm), cv2.COLORMAP_JET)
    hm_color = cv2.cvtColor(hm_color, cv2.COLOR_BGR2RGB)
    blended = cv2.addWeighted(image.astype("uint8"), 1 - alpha, hm_color, alpha, 0)
    return blended
