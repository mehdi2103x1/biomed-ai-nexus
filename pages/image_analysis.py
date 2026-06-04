"""
pages.image_analysis
====================
Deep-learning image-analysis module.

Upload an image -> automatic preprocessing (resize / normalise) -> MobileNetV2
inference (ONNX Runtime) -> class probabilities, confidence and inference time
-> an explainability heatmap (occlusion sensitivity) showing the regions that
drive the prediction.

Runs fully online: ONNX Runtime is lightweight enough for free cloud hosting.
"""
from __future__ import annotations

import numpy as np
import streamlit as st
from PIL import Image

from utils.history import append_record
from utils.image_model import CNNImageClassifier, onnx_available, overlay_heatmap
from utils.styles import hero, render_kpis, section
from utils.visualization import cnn_probability_bar


@st.cache_resource(show_spinner=False)
def _get_classifier() -> CNNImageClassifier:
    """Build + cache the MobileNetV2 ONNX session once per session."""
    return CNNImageClassifier().load()


def render(ctx: dict) -> None:
    hero("Image Analysis",
         "Pretrained MobileNetV2 CNN inference with explainable saliency mapping")

    if not onnx_available():
        st.warning(
            "The image model file is unavailable in this deployment. The full "
            "CNN pipeline (preprocessing → inference → saliency) is implemented "
            "in `utils/image_model.py`."
        )
        return

    st.markdown(
        "Upload an image (`jpg`, `jpeg`, `png`). The network performs automatic "
        "**resize → normalisation → inference**, then an **occlusion-sensitivity** "
        "heatmap highlights the regions driving the prediction."
    )

    uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if uploaded is None:
        st.info("Upload an image to run the CNN.")
        return

    image = np.array(Image.open(uploaded).convert("RGB"))

    col_img, col_cfg = st.columns([1.5, 1])
    with col_img:
        st.image(image, caption="Uploaded image", use_container_width=True)
    with col_cfg:
        top_k = st.selectbox("Classes to rank", [3, 5, 10], index=1)
        show_cam = st.checkbox("Show saliency heatmap", value=True)
        run = st.button("Run analysis", use_container_width=True)

    if not run:
        return

    progress = st.progress(0, text="Loading model…")
    with st.spinner("Running MobileNetV2 inference…"):
        clf = _get_classifier()
        progress.progress(45, text="Preprocessing & inference…")
        result = clf.predict(image, top_k=top_k, explain=show_cam)
        progress.progress(100, text="Done")
    progress.empty()

    # --- KPIs ------------------------------------------------------------- #
    section("Inference result")
    render_kpis([
        {"icon": "🏷️", "value": result.top_labels[0], "label": "Predicted class"},
        {"icon": "🎯", "value": f"{result.top_probs[0]:.1%}", "label": "Confidence"},
        {"icon": "⏱️", "value": f"{result.inference_ms:.0f} ms", "label": "Inference time"},
        {"icon": "🔢", "value": f"{top_k}", "label": "Classes ranked"},
    ])

    # --- Probability chart + saliency ------------------------------------ #
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            cnn_probability_bar(result.top_labels, result.top_probs),
            use_container_width=True,
        )
    with c2:
        if show_cam and result.heatmap is not None:
            overlay = overlay_heatmap(image, result.heatmap)
            st.image(overlay, caption="Saliency — regions driving the prediction",
                     use_container_width=True)
        elif show_cam:
            st.info("Saliency could not be computed for this image.")

    append_record({
        "source": "image",
        "prediction": result.top_labels[0],
        "probability": round(result.top_probs[0], 4),
        "confidence": round(result.top_probs[0], 4),
        "risk": "—",
        "best_model": "MobileNetV2 (ONNX)",
        "age": "",
        "gender": "",
        "details": f"{result.inference_ms:.0f}ms",
    })
    st.toast("Image inference saved to history")

    st.caption(
        "MobileNetV2 is pretrained on ImageNet (everyday objects), so labels on a "
        "true medical scan are illustrative. This module demonstrates the complete "
        "CNN pipeline — preprocessing, inference, timing and explainability — ready "
        "to be fine-tuned on a dedicated radiology dataset."
    )
