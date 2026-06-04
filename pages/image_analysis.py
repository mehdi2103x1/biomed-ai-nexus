"""
pages.image_analysis
====================
Deep-learning image-analysis demonstration.

Upload an image -> automatic preprocessing (resize/normalise) -> MobileNetV2
inference -> class probabilities, confidence and inference time -> Grad-CAM
heatmap that explains where the network "looked".

Because the project has no proprietary medical-image dataset, this is a
*pretrained-CNN demonstration* module (exactly as the brief allows). TensorFlow
is loaded lazily; if it is not installed the page shows a clear message instead
of crashing the rest of the app.
"""
from __future__ import annotations

import numpy as np
import streamlit as st
from PIL import Image

from utils.history import append_record
from utils.image_model import (
    CNNImageClassifier, overlay_heatmap, tensorflow_available,
)
from utils.styles import hero, render_kpis
from utils.visualization import cnn_probability_bar


@st.cache_resource(show_spinner=False)
def _get_classifier() -> CNNImageClassifier:
    """Build + cache MobileNetV2 once per session (weights download on 1st run)."""
    return CNNImageClassifier().load()


def render(ctx: dict) -> None:
    hero("Image Analysis",
         "Pretrained CNN (MobileNetV2) inference with Grad-CAM explainability")

    if not tensorflow_available():
        st.info(
            "🧠 **Deep-learning image module — full pipeline implemented.**\n\n"
            "This page runs a pretrained **MobileNetV2** CNN with automatic "
            "preprocessing, inference, a probability chart, inference-time "
            "measurement and a **Grad-CAM** explainability heatmap "
            "(see `utils/image_model.py`).\n\n"
            "It requires **TensorFlow**, which is disabled on this free cloud "
            "deployment because its size exceeds the host's memory limit. To run "
            "this module, launch the app locally after `pip install tensorflow` — "
            "all other pages (tabular prediction, model evaluation, dashboard) are "
            "fully functional here online."
        )
        with st.expander("📄 What this module does (architecture)"):
            st.markdown(
                "1. **Upload** a `jpg/jpeg/png` image.\n"
                "2. **Preprocess** — resize to 224×224, RGB conversion, MobileNetV2 normalisation.\n"
                "3. **Inference** — forward pass through MobileNetV2 (ImageNet weights).\n"
                "4. **Outputs** — predicted class, confidence, top-k probability chart, inference time (ms).\n"
                "5. **Explainability** — Grad-CAM heatmap overlay highlighting the regions "
                "that drove the prediction."
            )
        return

    st.markdown(
        "Upload any image (`jpg`, `jpeg`, `png`). The CNN performs automatic "
        "**resize → normalisation → inference**, then a **Grad-CAM** heatmap "
        "highlights the regions driving the prediction."
    )

    uploaded = st.file_uploader("📤 Upload an image", type=["jpg", "jpeg", "png"])
    if uploaded is None:
        st.info("Awaiting an image upload to run the CNN demonstration.")
        return

    image = np.array(Image.open(uploaded).convert("RGB"))

    col_img, col_cfg = st.columns([1.4, 1])
    with col_img:
        st.image(image, caption="Uploaded image", use_container_width=True)
    with col_cfg:
        top_k = st.slider("Top-k classes", 3, 10, 5)
        show_cam = st.checkbox("Show Grad-CAM overlay", value=True)
        run = st.button("🔮 Predict", use_container_width=True)

    if not run:
        return

    progress = st.progress(0, text="Loading CNN…")
    with st.spinner("Running MobileNetV2 inference…"):
        clf = _get_classifier()
        progress.progress(45, text="Preprocessing & inference…")
        result = clf.predict(image, top_k=top_k)
        progress.progress(100, text="Done")
    progress.empty()

    # --- KPIs ------------------------------------------------------------- #
    st.markdown("### 🧠 Inference result")
    render_kpis([
        {"icon": "🏷️", "value": result.top_labels[0], "label": "Predicted class"},
        {"icon": "🎯", "value": f"{result.top_probs[0]:.1%}", "label": "Confidence"},
        {"icon": "⏱️", "value": f"{result.inference_ms:.0f} ms", "label": "Inference time"},
        {"icon": "🔢", "value": f"{top_k}", "label": "Classes ranked"},
    ])

    # --- Probability chart + Grad-CAM ------------------------------------ #
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            cnn_probability_bar(result.top_labels, result.top_probs),
            use_container_width=True,
        )
    with c2:
        if show_cam and result.heatmap is not None:
            overlay = overlay_heatmap(image, result.heatmap)
            st.image(overlay, caption="Grad-CAM — model attention",
                     use_container_width=True)
        elif show_cam:
            st.info("Grad-CAM could not be computed for this image.")

    append_record({
        "source": "image",
        "prediction": result.top_labels[0],
        "probability": round(result.top_probs[0], 4),
        "confidence": round(result.top_probs[0], 4),
        "risk": "—",
        "best_model": "MobileNetV2",
        "age": "",
        "gender": "",
        "details": f"{result.inference_ms:.0f}ms",
    })
    st.toast("Image inference saved to history ✅")

    st.caption(
        "ℹ️ MobileNetV2 is pretrained on **ImageNet** (everyday objects), so on a "
        "true medical scan the labels are illustrative. The point of this module "
        "is to demonstrate the full CNN + Grad-CAM pipeline (preprocessing, "
        "inference, timing, explainability) ready to be fine-tuned on a real "
        "radiology dataset."
    )
