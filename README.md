# 🩺 HepatoScope — Liver Disease Prediction Platform

A modern, interactive **biomedical AI web application** built with Streamlit that
predicts **liver disease** from routine blood-panel biomarkers, demonstrates a
**deep-learning image-analysis** pipeline (MobileNetV2 via ONNX + saliency), compares five
machine-learning models, and explains every prediction.

> **Module:** Machine Learning — Supervised Learning · **Programme:** Ingénieur Génie Biomédical (UM6SS)
> **Problem statement:** *How can liver diseases be predicted from biological analyses and patient medical data?*

---

## ✨ Features

| Page | What it does |
|------|--------------|
| 🏠 **Home** | Landing page, objectives, KPI cards, workflow diagram, dataset overview |
| 🔬 **Liver Disease Prediction** | Medical form (number inputs, dropdown, radio) → preprocessing → 5-model soft-vote → class, probability gauge, confidence, risk level, feature importance, model-comparison table, **PDF report** |
| 🖼️ **Image Analysis** | Upload image → MobileNetV2 (ONNX) inference → top-k probabilities, inference time, **saliency** heatmap |
| 📊 **Model Evaluation** | Accuracy / Precision / Recall / F1 / AUC, ROC curves, confusion matrices, classification reports, training time, best hyper-parameters, ranking |
| 📈 **Dashboard** | KPIs (total / positive / negative / avg confidence), pie + bar + line + distribution charts, full history table, CSV export |
| ℹ️ **About** | Description, tech stack, ML pipeline, architecture, author |

**Advanced features:** dark mode · CSV export · PDF export · prediction history · animations · error handling · rotating-file logging.

---

## 🧬 Dataset

**Liver Patient Dataset** — 30,691 records (≈19,000 after de-duplication), 10
clinical features (Age, Gender, Total/Direct Bilirubin, Alkaline Phosphotase,
ALT, AST, Total Proteins, Albumin, A/G Ratio). Target: *Liver Disease* vs
*No Liver Disease*. This large dataset (an extension of the Indian Liver Patient
Dataset) lets the ensemble models reach ~99% accuracy.

The dataset is bundled at `data/liver_raw.csv`.

---

## 📁 Project structure

```
biomed_ai_nexus/
├── app.py                  # Streamlit entry-point + sidebar router
├── config.py               # central configuration
├── train.py                # offline training & evaluation pipeline
├── requirements.txt
├── README.md
├── .streamlit/config.toml  # theme + disables auto multipage nav
├── pages/                  # home, prediction, image_analysis, evaluation, dashboard, about
├── utils/                  # preprocessing, models, visualization, image_model,
│                           #   pdf_report, history, styles, logger
├── data/                   # liver_raw.csv, load_data.py, historical_predictions.csv
├── models/                 # *.pkl estimators, preprocessor.pkl, metrics.json
├── notebooks/              # exploratory_analysis.ipynb
├── assets/                 # generated figures for the report
└── logs/                   # app.log (rotating)
```

---

## 🚀 Quick start (local)

```bash
# 1. (optional) create a virtual environment
python -m venv .venv
# Windows:  .venv\Scripts\activate     |  macOS/Linux:  source .venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt

# 3. (only needed once) train the models — produces models/*.pkl + metrics.json
python train.py            # add --fast to skip hyper-parameter tuning

# 4. launch the app
streamlit run app.py
```

Then open **http://localhost:8501**.

> The repository already ships with trained models in `models/`, so you can run
> step 4 directly. Re-run `train.py` only if you change the data or models.

### Image module
The Image Analysis page runs MobileNetV2 through **ONNX Runtime** (lightweight),
so the full CNN pipeline — preprocessing, inference, timing and a saliency
heatmap — works both locally and on free cloud hosting. No TensorFlow needed.

---

## ☁️ Deploy to the cloud (share a link with your professor)

The easiest free option is **Streamlit Community Cloud** — it gives you a public
URL like `https://biomed-ai-nexus.streamlit.app` that anyone can open in a browser.

### Step 1 — push the project to GitHub
```bash
cd biomed_ai_nexus
git init
git add .
git commit -m "HepatoScope"
git branch -M main
git remote add origin https://github.com/<your-username>/biomed-ai-nexus.git
git push -u origin main
```

### Step 2 — deploy
1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. Click **“Create app”** → select your repository, branch `main`, main file `app.py`.
3. Click **Deploy**. First build takes a few minutes.
4. Copy the generated URL and send it to your professor.

### Cloud notes
- The trained `models/*.pkl` are committed, so the app runs immediately online —
  no training needed on the server.
- **Lightweight:** the app uses ONNX Runtime (not TensorFlow), so it builds and
  runs comfortably within the free tier's limits — all pages work online.
- `historical_predictions.csv` on the free tier is **ephemeral** (resets when the
  app sleeps). That is fine for a demo.

### Alternative — Docker / any VPS
```bash
docker build -t biomed-ai-nexus .
docker run -p 8501:8501 biomed-ai-nexus
```
(A ready-to-use `Dockerfile` is included.)

### Alternative — Hugging Face Spaces
Create a new **Streamlit** Space, push the same files; it auto-deploys and gives
a public URL too.

---

## 🧪 How it was tested
- `python train.py` trains + evaluates all 5 models and writes `metrics.json`.
- Every `utils` function (preprocessing, prediction, PDF, history, visualisation)
  was exercised with a smoke test.
- Every page was rendered headlessly with Streamlit’s `AppTest` framework with
  **zero exceptions**.
- The server boots and passes the `/_stcore/health` check.

---

## ⚕️ Disclaimer
This is an **academic prototype** trained on a public dataset. It is **not** a
certified medical device and must not be used for real clinical diagnosis.

**Author:** El Mehdi Mansouri — Ingénieur Génie Biomédical, UM6SS.
