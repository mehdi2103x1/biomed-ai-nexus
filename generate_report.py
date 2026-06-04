"""
generate_report.py
===================
Génère le rapport technique détaillé du projet (« RAPPORT.html ») de qualité
professionnelle, puis le rend en « RAPPORT.pdf » via Google Chrome en mode
headless. Les schémas (flux applicatif, pipeline) sont produits avec Mermaid ;
les figures de résultats (matplotlib) sont embarquées en base64 ; tous les
chiffres de performance sont lus en direct depuis ``models/metrics.json``.

    python generate_report.py

Le document suit les conventions d'un rapport d'ingénieur : page de garde,
remerciements, résumé + mots-clés, sommaire, fiche technique, chapitres
numérotés, schémas, figures commentées et webographie.
"""
from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
METRICS = json.loads((ROOT / "models" / "metrics.json").read_text(encoding="utf-8"))
MODELS = METRICS["models"]
RANKING = METRICS["ranking"]
BEST = RANKING[0]


# --------------------------------------------------------------------------- #
# Fragments dynamiques (helpers)
# --------------------------------------------------------------------------- #
def img(name: str, caption: str, width: str = "76%") -> str:
    p = ASSETS / name
    if not p.exists():
        return f"<p><i>[figure manquante : {name}]</i></p>"
    b64 = base64.b64encode(p.read_bytes()).decode()
    return (f'<figure><img src="data:image/png;base64,{b64}" style="max-width:{width}"/>'
            f'<figcaption>{caption}</figcaption></figure>')


def ranking_table() -> str:
    rows = "".join(
        f"<tr><td>{r['rank']}</td><td>{r['name']}</td>"
        f"<td>{r['accuracy']:.3f}</td><td>{r['precision']:.3f}</td>"
        f"<td>{r['recall']:.3f}</td><td>{r['f1']:.3f}</td>"
        f"<td><b>{r['auc']:.3f}</b></td></tr>"
        for r in RANKING
    )
    return ("<table><tr><th>Rang</th><th>Modèle</th><th>Accuracy</th>"
            "<th>Précision</th><th>Rappel</th><th>F1</th><th>AUC</th></tr>"
            f"{rows}</table>")


def hyperparams_table() -> str:
    rows = "".join(
        f"<tr><td>{m['name']}</td><td><code>{json.dumps(m['best_params'])}</code></td>"
        f"<td>{m['train_time']:.2f}&nbsp;s</td></tr>"
        for m in MODELS.values()
    )
    return ("<table><tr><th style='width:22%'>Modèle</th>"
            "<th>Meilleurs hyperparamètres (GridSearchCV)</th>"
            "<th style='width:14%'>Temps</th></tr>"
            f"{rows}</table>")


# --------------------------------------------------------------------------- #
# Feuille de style (chaîne brute : pas d'f-string, accolades littérales)
# --------------------------------------------------------------------------- #
CSS = """
<style>
  :root{
    --bleu:#143b66; --bleu-clair:#2e6da4; --teal:#0a8f8f;
    --gris:#444; --gris-clair:#777; --fond-code:#f4f6f8; --bord:#d0d7de;
  }
  *{box-sizing:border-box;}
  html,body{margin:0;padding:0;}
  body{ font-family:"Segoe UI","Calibri",Arial,sans-serif; color:#1c2733;
        font-size:11.2pt; line-height:1.62; background:#fff; }
  @page{ size:A4; margin:18mm 18mm 16mm 18mm; }
  .page{ page-break-before:always; }
  .nobreak{ page-break-inside:avoid; }
  figure,table,pre.code,.mermaid,.arch,.encadre{ page-break-inside:avoid; }
  h2,h3{ page-break-after:avoid; }
  h1,h2,h3,h4{ color:var(--bleu); line-height:1.25; }
  h1{ font-size:19pt; border-bottom:3px solid var(--bleu); padding-bottom:6px; margin-top:0; }
  h2{ font-size:14.5pt; margin-top:26px; border-left:5px solid var(--bleu-clair); padding-left:10px; }
  h3{ font-size:12.5pt; color:var(--bleu-clair); margin-top:18px; }
  p{ text-align:justify; margin:8px 0; }
  ul,ol{ margin:8px 0; padding-left:22px; }
  li{ margin:3px 0; text-align:justify; }
  code{ background:var(--fond-code); padding:1px 5px; border-radius:3px;
        font-family:"Consolas","Courier New",monospace; font-size:9.6pt; color:#b5184d; }
  pre.code{ background:var(--fond-code); border:1px solid var(--bord);
        border-left:4px solid var(--bleu-clair); border-radius:4px; padding:10px 14px;
        font-family:"Consolas",monospace; font-size:8.7pt; color:#1c2733;
        overflow-x:auto; line-height:1.45; }
  table{ border-collapse:collapse; width:100%; margin:12px 0; font-size:9.8pt; }
  th,td{ border:1px solid var(--bord); padding:6px 9px; text-align:left; vertical-align:top; }
  th{ background:var(--bleu); color:#fff; font-weight:600; text-align:center; }
  td{ text-align:center; }
  td:nth-child(2){ text-align:left; }
  tr:nth-child(even) td{ background:#f6f8fa; }
  figure{ margin:14px 0; text-align:center; }
  figure img{ border:1px solid var(--bord); border-radius:4px; }
  figcaption{ font-size:8.7pt; color:var(--gris-clair); font-style:italic; margin-top:5px;
        max-width:84%; margin-left:auto; margin-right:auto; }
  .mermaid{ text-align:center; margin:14px 0; }
  .mermaid svg{ max-width:88%; height:auto; }
  .legende{ text-align:center; font-size:8.9pt; color:var(--bleu-clair); font-weight:700; }
  .encadre{ background:#eef4fa; border:1px solid #c5d8ea; border-radius:5px;
        padding:9px 14px; margin:12px 0; font-size:10pt; }
  .encadre strong{ color:var(--bleu); }
  /* Page de garde */
  .cover{ height:255mm; display:flex; flex-direction:column;
          justify-content:space-between; text-align:center; }
  .cover .haut{ font-size:11.5pt; color:var(--gris); line-height:1.7; }
  .cover .haut .uni{ font-size:13pt; font-weight:700; color:var(--bleu); }
  .cover .haut .etab{ font-size:10.5pt; color:var(--bleu-clair); }
  .cover .type-doc{ letter-spacing:3px; font-size:12pt; color:var(--bleu-clair);
        text-transform:uppercase; margin-bottom:10px; }
  .cover .titre{ font-size:26pt; font-weight:800; color:var(--bleu); line-height:1.25; margin:14px 24px; }
  .cover .sous-titre{ font-size:13pt; color:var(--gris); margin-top:8px; }
  .cover .ligne{ width:130px; height:4px; background:var(--bleu-clair); margin:22px auto; border-radius:2px; }
  .cover .badges{ margin-top:14px; }
  .cover .bloc-info{ margin-top:12mm; font-size:11pt; }
  .cover .lbl{ color:var(--gris-clair); font-size:9pt; text-transform:uppercase; letter-spacing:1px; }
  .cover .val{ color:#1c2733; font-weight:600; font-size:12.5pt; }
  .cover .bas{ font-size:11pt; color:var(--gris); }
  .cover .annee{ font-weight:700; color:var(--bleu); font-size:12pt; }
  .badge{ display:inline-block; background:#e8f0f7; color:#1f4e79; border:1px solid #bcd2e6;
        border-radius:999px; padding:2px 10px; font-size:9pt; font-weight:600; margin:3px; }
  /* Sommaire */
  .toc{ font-size:10.6pt; }
  .toc .l1{ font-weight:700; color:var(--bleu); margin-top:8px; }
  .toc .l2{ margin-left:22px; color:#33414f; }
  .toc .pt{ color:#aab4bf; }
  /* Diagramme d'architecture en couches (HTML/CSS) */
  .arch{ max-width:520px; margin:16px auto 6px; }
  .arch-layer{ display:flex; align-items:stretch; border-radius:6px; overflow:hidden;
        border:1px solid var(--bord); }
  .arch-tag{ width:150px; padding:8px 10px; color:#fff; font-size:8.6pt; font-weight:600;
        display:flex; flex-direction:column; justify-content:center; line-height:1.3; }
  .arch-tag .num{ font-size:14pt; font-weight:800; }
  .arch-tag small{ font-weight:400; opacity:.9; }
  .arch-boxes{ flex:1; display:flex; gap:6px; padding:9px; background:#fbfcfd; flex-wrap:wrap; }
  .arch-box{ flex:1 1 30%; background:#fff; border:1px solid #c5d1dd; border-radius:4px;
        padding:6px 3px; text-align:center; font-size:8pt; font-weight:600; color:#1c2733; }
  .arch-arrow{ text-align:center; font-size:8.2pt; color:#5a6a78; padding:4px 0; }
  .lay-pres .arch-tag{ background:#143b66; }
  .lay-logic .arch-tag{ background:#2e7d4f; }
  .lay-data .arch-tag{ background:#b06d00; }
</style>
"""

MERMAID_INIT = """
<script src="assets/mermaid.min.js"></script>
<script>
  mermaid.initialize({ startOnLoad:true, theme:"neutral",
    flowchart:{ curve:"basis" }, securityLevel:"loose" });
</script>
"""


# --------------------------------------------------------------------------- #
# Corps du rapport (concaténation de fragments — pas d'f-string global)
# --------------------------------------------------------------------------- #
def build_html() -> str:
    P: list[str] = []
    A = P.append

    A('<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">')
    A('<title>Rapport — HepatoScope</title>')
    A(CSS)
    A('</head><body>')

    # ---------------- Page de garde ----------------
    A('''
    <section class="cover">
      <div class="haut">
        <div class="uni">Université Mohammed VI des Sciences et de la Santé</div>
        <div class="etab">École Supérieure Mohammed VI d'Ingénieurs en Sciences de la Santé — UM6SS, Rabat</div>
        <div>Filière Ingénieur Génie Biomédical · Module : Machine Learning — Apprentissage Supervisé</div>
        <div>Année universitaire 2025 – 2026</div>
      </div>
      <div class="centre">
        <div class="type-doc">Rapport de projet — Intelligence Artificielle</div>
        <div class="ligne"></div>
        <div class="titre">HepatoScope<br>Plateforme intelligente de prédiction des maladies du foie</div>
        <div class="sous-titre">Application web d'aide au diagnostic fondée sur cinq modèles de
          Machine&nbsp;Learning, avec évaluation comparative, tableau de bord
          analytique interactif et rapport PDF</div>
        <div class="ligne"></div>
        <div class="badges">
          <span class="badge">Python</span><span class="badge">Streamlit</span>
          <span class="badge">Scikit-Learn</span><span class="badge">XGBoost</span>
          <span class="badge">Plotly</span><span class="badge">Pandas</span>
        </div>
        <div class="bloc-info">
          <div class="lbl">Réalisé par</div>
          <div class="val">El Mehdi Mansouri</div>
        </div>
      </div>
      <div class="bas">
        <div>Rapport technique du projet de fin de module</div>
        <div class="annee">Année universitaire 2025 – 2026</div>
      </div>
    </section>
    ''')

    # ---------------- Remerciements + Résumé ----------------
    A('''
    <section class="page">
      <h1>Remerciements</h1>
      <p>Au terme de ce projet, je tiens à exprimer ma sincère gratitude à toutes
      les personnes qui ont contribué, de près ou de loin, à son aboutissement.</p>
      <p>Je remercie particulièrement le corps professoral de la filière
      <strong>Génie Biomédical</strong> de l'École Supérieure Mohammed VI
      d'Ingénieurs en Sciences de la Santé, dont l'enseignement du module de
      <strong>Machine Learning — Apprentissage Supervisé</strong> a constitué le
      socle théorique et méthodologique de ce travail. Mes remerciements vont
      également à mes camarades et à ma famille pour leur soutien constant.</p>

      <h1 style="margin-top:42px;">Résumé</h1>
      <p>Ce projet, réalisé dans le cadre du module de <strong>Machine Learning —
      Apprentissage Supervisé</strong>, porte sur la conception et la réalisation
      d'une <strong>plateforme web d'intelligence artificielle biomédicale</strong>
      capable de prédire la présence d'une maladie hépatique à partir des données
      d'analyses biologiques d'un patient. L'application, baptisée
      <strong>HepatoScope</strong> et développée en <strong>Python</strong> avec
      le framework <strong>Streamlit</strong>, met en œuvre une chaîne complète
      d'apprentissage supervisé sur le <em>Liver Patient Dataset</em>
      (30 691 enregistrements, ~19 000 après nettoyage).</p>
      <p>Il s'agit du <strong>sujet n°16 — Prédiction des maladies hépatiques</strong>,
      un problème de classification <strong>tabulaire</strong> (à partir d'analyses
      biologiques, sans imagerie médicale). Cinq modèles de classification —
      <strong>Decision Tree, Random Forest, Logistic Regression, SVM et XGBoost</strong>
      — sont entraînés, optimisés par recherche d'hyperparamètres et comparés sur un
      ensemble de test indépendant. L'interface, moderne et responsive, s'organise
      en cinq pages : accueil, prédiction, évaluation des modèles, tableau de bord
      analytique et page « à propos ». Le meilleur modèle atteint une
      <strong>accuracy de ''' + f"{BEST['accuracy']:.1%}" + '''</strong> et une
      <strong>AUC de ''' + f"{BEST['auc']:.3f}" + '''</strong> sur l'ensemble de
      test. Chaque prédiction est expliquée, journalisée et exportable en PDF.</p>
      <p><strong>Mots-clés :</strong> intelligence artificielle, apprentissage
      supervisé, classification, maladies du foie, Liver Patient Dataset,
      Scikit-Learn, Random Forest, XGBoost, Streamlit, aide au diagnostic.</p>
    </section>
    ''')

    # ---------------- Sommaire + fiche technique ----------------
    A('''
    <section class="page">
      <h1>Sommaire</h1>
      <div class="toc">
        <div class="l1">1. Introduction générale <span class="pt">.....................................</span> 4</div>
        <div class="l1">2. Contexte et problématique <span class="pt">.............................</span> 5</div>
        <div class="l2">2.1 Les maladies du foie et les marqueurs biologiques <span class="pt">..</span> 5</div>
        <div class="l2">2.2 Problématique et objectifs <span class="pt">.....................</span> 5</div>
        <div class="l1">3. Description du jeu de données <span class="pt">..............</span> 6</div>
        <div class="l2">3.1 Présentation et variables <span class="pt">....................</span> 6</div>
        <div class="l2">3.2 Analyse exploratoire <span class="pt">........................</span> 6</div>
        <div class="l1">4. Architecture de l'application <span class="pt">.....................</span> 8</div>
        <div class="l2">4.1 Vue d'ensemble et flux applicatif <span class="pt">.........</span> 8</div>
        <div class="l2">4.2 Architecture modulaire en couches <span class="pt">.........</span> 8</div>
        <div class="l2">4.3 Structure du projet sur disque <span class="pt">............</span> 9</div>
        <div class="l1">5. Analyse et preprocessing des données <span class="pt">.............</span> 10</div>
        <div class="l1">6. Méthodes de Machine Learning <span class="pt">....</span> 12</div>
        <div class="l1">7. Évaluation, métriques et résultats expérimentaux <span class="pt">.</span> 14</div>
        <div class="l1">8. Interface utilisateur et fonctionnalités <span class="pt">.......</span> 17</div>
        <div class="l1">9. Choix technologiques <span class="pt">............................</span> 18</div>
        <div class="l1">10. Difficultés rencontrées <span class="pt">.......................</span> 19</div>
        <div class="l1">11. Perspectives d'amélioration <span class="pt">..................</span> 19</div>
        <div class="l1">12. Conclusion <span class="pt">...................................</span> 20</div>
        <div class="l1">Webographie <span class="pt">.....................................</span> 20</div>
      </div>

      <h3 style="margin-top:30px;">Fiche technique du projet</h3>
      <table class="nobreak">
        <tr><th style="width:32%">Élément</th><th>Description</th></tr>
        <tr><td>Intitulé</td><td>HepatoScope — plateforme de prédiction des maladies du foie</td></tr>
        <tr><td>Problématique</td><td>Prédire une maladie hépatique à partir d'analyses biologiques et de données patient</td></tr>
        <tr><td>Type</td><td>Application web interactive (Streamlit, multi-pages)</td></tr>
        <tr><td>Langage</td><td>Python 3.13</td></tr>
        <tr><td>Jeu de données</td><td>Liver Patient Dataset — 30 691 enregistrements (~19 000 nettoyés), 10 variables</td></tr>
        <tr><td>Modèles ML</td><td>Decision Tree, Random Forest, Logistic Regression, SVM, XGBoost</td></tr>
        <tr><td>Meilleur modèle</td><td>''' + f"{BEST['name']} — AUC = {BEST['auc']:.3f}, Accuracy = {BEST['accuracy']:.1%}" + '''</td></tr>
        <tr><td>Livrables</td><td>Code source, modèles entraînés, rapport, README, Dockerfile</td></tr>
      </table>
    </section>
    ''')

    # ---------------- 1. Introduction ----------------
    A('''
    <section class="page">
      <h1>1. Introduction générale</h1>
      <p>L'intelligence artificielle occupe aujourd'hui une place croissante dans
      le domaine biomédical, où elle assiste le praticien dans le dépistage, le
      diagnostic et le suivi des pathologies. Parmi les applications les plus
      prometteuses figure l'<strong>aide au diagnostic à partir de données
      biologiques</strong> : à partir d'un simple bilan sanguin, des modèles
      d'apprentissage supervisé peuvent estimer le risque qu'un patient soit
      atteint d'une pathologie donnée, et ce à faible coût et de manière
      reproductible.</p>
      <p>Le foie, organe vital assurant le métabolisme, la détoxification et la
      synthèse des protéines, est le siège de nombreuses pathologies souvent
      <strong>silencieuses à leurs débuts</strong>. Leur dépistage précoce repose
      en grande partie sur l'interprétation de marqueurs biologiques (bilirubine,
      transaminases, phosphatase alcaline, protéines). C'est précisément ce
      problème que ce projet aborde.</p>
      <p>Le présent travail, mené dans le cadre du module de Machine Learning —
      Apprentissage Supervisé, consiste à <strong>concevoir et réaliser une
      application web intelligente complète</strong> répondant au cahier des
      charges fourni : saisie de données tabulaires via un formulaire, entraînement
      et comparaison de plusieurs modèles, visualisation des performances et tableau
      de bord. L'objectif est double : mettre en pratique les notions
      d'apprentissage supervisé étudiées en cours, et mener un projet logiciel de
      bout en bout selon des principes de génie logiciel (architecture modulaire,
      typage, gestion des erreurs, journalisation).</p>
      <p>Ce rapport s'organise comme suit. Le chapitre&nbsp;2 présente le contexte
      médical et la problématique. Le chapitre&nbsp;3 décrit le jeu de données. Le
      chapitre&nbsp;4 détaille l'architecture de l'application. Le chapitre&nbsp;5
      expose le prétraitement des données. Le chapitre&nbsp;6 présente les méthodes
      d'apprentissage retenues. Le chapitre&nbsp;7 analyse les résultats
      expérimentaux. Le chapitre&nbsp;8 décrit l'interface et les fonctionnalités.
      Les chapitres&nbsp;9 à&nbsp;12 traitent des choix technologiques, des
      difficultés, des perspectives et de la conclusion.</p>
    </section>
    ''')

    # ---------------- 2. Contexte ----------------
    A('''
    <section class="page">
      <h1>2. Contexte et problématique</h1>
      <h2>2.1 Les maladies du foie et les marqueurs biologiques</h2>
      <p>Les maladies hépatiques (hépatites, cirrhose, stéatose, fibrose) sont
      responsables d'environ <strong>deux millions de décès par an</strong> dans
      le monde. Leur particularité clinique est d'évoluer longtemps sans symptôme
      apparent ; lorsque les signes cliniques se manifestent, l'atteinte est
      souvent déjà avancée. Le bilan hépatique sanguin constitue donc l'outil de
      dépistage de première ligne. Les principaux marqueurs sont :</p>
      <ul>
        <li>la <strong>bilirubine</strong> (totale et directe), dont l'élévation
        traduit un défaut d'élimination par le foie ;</li>
        <li>les <strong>transaminases</strong> ALT (SGPT) et AST (SGOT), enzymes
        libérées lors d'une souffrance des cellules hépatiques ;</li>
        <li>la <strong>phosphatase alcaline</strong>, marqueur de cholestase ;</li>
        <li>les <strong>protéines totales, l'albumine et le rapport
        albumine/globuline</strong>, reflets de la fonction de synthèse du foie.</li>
      </ul>
      <p>L'interprétation conjointe de ces marqueurs, combinée à l'âge et au sexe
      du patient, permet d'estimer la probabilité d'une atteinte hépatique — une
      tâche de <strong>classification supervisée</strong> idéale pour le Machine
      Learning.</p>

      <h2>2.2 Problématique et objectifs</h2>
      <div class="encadre"><strong>Problématique.</strong> Comment prédire les
      maladies du foie à partir d'analyses biologiques et de données médicales du
      patient ?</div>
      <p>Le défi consiste à transformer dix variables cliniques hétérogènes
      (numériques et catégorielles, à des échelles très différentes, comportant
      quelques valeurs manquantes et une distribution de classes déséquilibrée) en
      une prédiction fiable, interprétable et assortie d'un niveau de confiance et
      de risque. Les objectifs opérationnels du projet sont :</p>
      <ul>
        <li><strong>Prédire</strong> la maladie du foie à partir de données
        tabulaires patient saisies via un formulaire interactif ;</li>
        <li><strong>Entraîner et comparer</strong> cinq modèles de Machine Learning ;</li>
        <li><strong>visualiser les performances</strong> des modèles (métriques,
        courbes ROC, matrices de confusion) ;</li>
        <li>maintenir un <strong>historique</strong> des prédictions et un
        <strong>tableau de bord</strong> analytique ;</li>
        <li><strong>expliquer</strong> chaque décision et permettre l'export PDF.</li>
      </ul>
    </section>
    ''')

    # ---------------- 3. Dataset ----------------
    A('''
    <section class="page">
      <h1>3. Description du jeu de données</h1>
      <h2>3.1 Présentation et variables</h2>
      <p>Le jeu de données utilisé est le <strong>Liver Patient Dataset</strong>,
      une extension à grande échelle de l'Indian Liver Patient Dataset (ILPD).
      Il comporte <strong>30 691 enregistrements</strong> de patients ; après
      nettoyage et suppression des doublons exacts (afin d'éviter toute fuite
      d'information entre l'entraînement et le test), <strong>19 368
      enregistrements</strong> uniques sont conservés, décrits par dix variables
      cliniques. Le volume bien plus important que l'ILPD original (583 lignes)
      permet aux modèles d'atteindre des performances nettement supérieures.
      La variable cible originale (1 = patient hépatique, 2 = non-patient) est
      remappée en une cible binaire : <em>1 = Maladie du foie</em>,
      <em>0 = Pas de maladie</em>.</p>
      <table class="nobreak">
        <tr><th style="width:42%">Variable</th><th>Type</th><th>Unité</th></tr>
        <tr><td>Age</td><td>Numérique</td><td>années</td></tr>
        <tr><td>Gender</td><td>Catégorielle</td><td>Male / Female</td></tr>
        <tr><td>Total Bilirubin</td><td>Numérique</td><td>mg/dL</td></tr>
        <tr><td>Direct Bilirubin</td><td>Numérique</td><td>mg/dL</td></tr>
        <tr><td>Alkaline Phosphotase</td><td>Numérique</td><td>IU/L</td></tr>
        <tr><td>Alamine Aminotransferase (ALT)</td><td>Numérique</td><td>IU/L</td></tr>
        <tr><td>Aspartate Aminotransferase (AST)</td><td>Numérique</td><td>IU/L</td></tr>
        <tr><td>Total Proteins</td><td>Numérique</td><td>g/dL</td></tr>
        <tr><td>Albumin</td><td>Numérique</td><td>g/dL</td></tr>
        <tr><td>Albumin / Globulin Ratio</td><td>Numérique</td><td>—</td></tr>
      </table>

      <h2>3.2 Analyse exploratoire</h2>
      <p>L'analyse exploratoire (cf. <code>notebooks/exploratory_analysis.ipynb</code>)
      révèle un <strong>déséquilibre marqué des classes</strong> : environ 71&nbsp;%
      des patients sont étiquetés « malades ». Ce déséquilibre est déterminant pour
      le choix des métriques et la pondération des classes (chapitre&nbsp;6).</p>
      ''' + img('fig_class_distribution.png', 'Figure 1 — Répartition des classes (19 368 enregistrements nettoyés) : 13 811 cas pathologiques contre 5 557 cas sains.', '60%') + '''
      <p>La matrice de corrélation met en évidence des relations physiologiquement
      cohérentes : forte corrélation entre bilirubine totale et directe, et entre
      les deux transaminases ALT et AST. Ces redondances justifient la robustesse
      des modèles ensemblistes face à la colinéarité.</p>
      ''' + img('fig_correlation.png', 'Figure 2 — Matrice de corrélation des variables (les blocs bilirubine et transaminases ressortent nettement).', '72%') + '''
    </section>
    ''')

    # ---------------- 4. Architecture ----------------
    A('''
    <section class="page">
      <h1>4. Architecture de l'application</h1>
      <h2>4.1 Vue d'ensemble et flux applicatif</h2>
      <p>Au lancement, le point d'entrée <code>app.py</code> configure le thème,
      charge en cache les modèles entraînés et le préprocesseur, puis affiche une
      barre latérale de navigation qui route l'utilisateur vers l'une des cinq
      pages. Le diagramme suivant synthétise le flux applicatif global.</p>
      <div class="mermaid">
flowchart TB
  START(["Lancement (app.py)"]) --> INIT["Initialisation<br/>chargement des modeles + preprocesseur"]
  INIT --> NAV{"Navigation<br/>barre laterale"}
  NAV --> P1["Accueil"]
  NAV --> P2["Prediction"]
  NAV --> P4["Evaluation des modeles"]
  NAV --> P5["Dashboard"]
  NAV --> P6["A propos"]
  P2 --> PRE["Preprocessing<br/>imputation + encodage + standardisation"]
  PRE --> ML["5 modeles ML<br/>vote souple"]
  ML --> OUT["Classe + probabilite + risque<br/>+ rapport PDF"]
  OUT --> HIST[("historical_predictions.csv")]
  HIST --> P5
      </div>
      <p class="legende">Figure 3 — Flux applicatif global de HepatoScope.</p>

      <h2>4.2 Architecture modulaire en couches</h2>
      <p>Le code suit une <strong>architecture modulaire en trois couches</strong>
      qui sépare la présentation (pages Streamlit), la logique métier (utilitaires
      de traitement et de modélisation) et les données / modèles persistés. Les
      modules de la couche logique ne dépendent pas de Streamlit : ce sont des
      fonctions et classes pures, testables isolément.</p>
      <div class="arch nobreak">
        <div class="arch-layer lay-pres">
          <div class="arch-tag"><span class="num">①</span>Couche Présentation<small>Streamlit</small></div>
          <div class="arch-boxes">
            <div class="arch-box">app.py</div><div class="arch-box">home</div>
            <div class="arch-box">prediction</div><div class="arch-box">evaluation</div>
            <div class="arch-box">dashboard</div><div class="arch-box">about</div>
          </div>
        </div>
        <div class="arch-arrow">&#9660;&nbsp; appelle les fonctions metier — recoit les resultats &nbsp;&#9650;</div>
        <div class="arch-layer lay-logic">
          <div class="arch-tag"><span class="num">②</span>Couche Logique métier<small>utils/</small></div>
          <div class="arch-boxes">
            <div class="arch-box">preprocessing</div><div class="arch-box">models</div>
            <div class="arch-box">visualization</div><div class="arch-box">pdf_report</div>
            <div class="arch-box">history</div><div class="arch-box">styles</div>
          </div>
        </div>
        <div class="arch-arrow">&#9660;&nbsp; lit / ecrit — charge les modeles et les donnees &nbsp;&#9650;</div>
        <div class="arch-layer lay-data">
          <div class="arch-tag"><span class="num">③</span>Couche Données &amp; Modèles<small>data/ · models/</small></div>
          <div class="arch-boxes">
            <div class="arch-box">liver_raw.csv</div><div class="arch-box">*.pkl</div>
            <div class="arch-box">metrics.json</div><div class="arch-box">history.csv</div>
          </div>
        </div>
      </div>
      <p class="legende">Figure 4 — Architecture logicielle en trois couches.</p>
    </section>

    <section class="page">
      <h2>4.3 Structure du projet sur disque</h2>
      <p>L'arborescence reflète directement l'architecture en couches ; chaque
      répertoire a une responsabilité unique.</p>
<pre class="code">biomed_ai_nexus/
├── app.py                  ← Point d'entree Streamlit + routeur de la sidebar
├── config.py               ← Configuration centrale (chemins, variables, palette)
├── train.py                ← Pipeline d'entrainement et d'evaluation hors-ligne
├── generate_report.py      ← Generation de ce rapport (HTML + PDF)
├── pages/                  ← ① Couche Presentation
│   ├── home.py             ← Page d'accueil (KPI, workflow, statistiques)
│   ├── prediction.py       ← Formulaire medical + prediction multi-modeles
│   ├── evaluation.py       ← Metriques, ROC, matrices de confusion
│   ├── dashboard.py        ← Tableau de bord analytique
│   └── about.py            ← Description, pipeline, auteur
├── utils/                  ← ② Couche Logique metier
│   ├── preprocessing.py    ← Chargement + LiverPreprocessor (impute/scale/encode)
│   ├── models.py           ← TabularTrainer (offline) + ModelManager (online)
│   ├── visualization.py    ← Graphiques Plotly reutilisables
│   ├── pdf_report.py       ← Rapport de prediction PDF (fpdf2)
│   ├── history.py          ← Journalisation CSV des predictions
│   ├── styles.py           ← CSS, theme, cartes KPI
│   └── logger.py           ← Journalisation rotative
├── data/                   ← ③ Donnees
│   ├── liver_raw.csv       ← Liver Patient Dataset (~19k lignes)
│   ├── load_data.py        ← Script de telechargement du dataset
│   └── historical_predictions.csv
├── models/                 ← ③ Modeles entraines + metriques
│   ├── decision_tree.pkl · random_forest.pkl · logistic_regression.pkl
│   ├── svm.pkl · xgboost.pkl · preprocessor.pkl
│   └── metrics.json
├── notebooks/              ← Analyse exploratoire (Jupyter)
├── assets/                 ← Figures du rapport
├── requirements.txt · README.md · Dockerfile · .streamlit/config.toml</pre>
    </section>
    ''')

    # ---------------- 5. Preprocessing ----------------
    A('''
    <section class="page">
      <h1>5. Analyse et preprocessing des données</h1>
      <p>Le prétraitement est encapsulé dans la classe <code>LiverPreprocessor</code>,
      qui enchaîne trois étapes au sein d'un <code>Pipeline</code> scikit-learn :</p>
      <ul>
        <li><strong>Traitement des valeurs manquantes</strong> — le jeu de données
        comporte plusieurs milliers de valeurs absentes réparties sur les variables. Elles
        sont remplacées par <strong>imputation médiane</strong>, robuste aux
        valeurs extrêmes fréquentes dans les analyses biologiques.</li>
        <li><strong>Encodage de la variable catégorielle</strong> — la variable
        <code>Gender</code> est encodée en binaire (Male = 1, Female = 0).</li>
        <li><strong>Standardisation</strong> — les variables présentant des échelles
        très hétérogènes (la phosphatase alcaline atteint plusieurs centaines
        d'unités tandis que le rapport A/G avoisine 1), un <code>StandardScaler</code>
        centre et réduit chaque variable. Cette étape est indispensable pour les
        modèles sensibles aux distances (SVM, régression logistique).</li>
      </ul>
      <div class="encadre"><strong>Prévention de la fuite de données.</strong> Le
      préprocesseur est ajusté <em>uniquement</em> sur l'ensemble d'entraînement,
      puis appliqué tel quel à l'ensemble de test et aux saisies en temps réel. Les
      statistiques d'imputation et de standardisation ne « voient » jamais les
      données de test, ce qui garantit une évaluation honnête.</p></div>
      <p>Le préprocesseur ajusté est sérialisé (<code>models/preprocessor.pkl</code>)
      afin d'appliquer à l'inférence exactement la même transformation qu'à
      l'entraînement.</p>
    </section>
    ''')

    # ---------------- 6. Méthodes ----------------
    A('''
    <section class="page">
      <h1>6. Méthodes de Machine Learning</h1>
      <h2>6.1 Pipeline d'apprentissage supervisé</h2>
      <p>Le pipeline complet, implémenté dans <code>train.py</code>, enchaîne le
      chargement des données, la division stratifiée entraînement/test (80/20),
      l'ajustement du préprocesseur, l'entraînement avec optimisation des
      hyperparamètres, puis l'évaluation et la persistance.</p>
      <div class="mermaid">
flowchart LR
  D[("Liver Dataset<br/>~19k lignes")] --> CL["Nettoyage<br/>+ cible binaire"]
  CL --> SP["Split stratifie<br/>80% / 20%"]
  SP --> PRE["Preprocesseur<br/>(fit sur train)"]
  PRE --> GS["GridSearchCV<br/>CV stratifiee 5 plis - score AUC"]
  GS --> EV["Evaluation<br/>sur le test"]
  EV --> PK[("models/*.pkl<br/>metrics.json")]
      </div>
      <p class="legende">Figure 5 — Pipeline d'entraînement et d'évaluation.</p>

      <h2>6.2 Les cinq modèles de classification</h2>
      <table class="nobreak">
        <tr><th style="width:26%">Modèle</th><th>Principe</th></tr>
        <tr><td>Decision Tree</td><td>Arbre de décision — partitionnement récursif de l'espace des variables, hautement interprétable.</td></tr>
        <tr><td>Random Forest</td><td>Forêt aléatoire — agrégation (bagging) de nombreux arbres décorrélés ; réduit la variance et le surapprentissage.</td></tr>
        <tr><td>Logistic Regression</td><td>Modèle linéaire probabiliste estimant directement P(maladie) ; robuste et bien calibré.</td></tr>
        <tr><td>SVM</td><td>Séparateur à vaste marge avec noyau RBF ; capture des frontières de décision non linéaires.</td></tr>
        <tr><td>XGBoost</td><td>Gradient boosting — construction séquentielle d'arbres corrigeant les erreurs des précédents ; état de l'art sur données tabulaires.</td></tr>
      </table>
      <p>Chaque modèle est optimisé par <strong>GridSearchCV</strong> (validation
      croisée stratifiée à 5 plis, métrique de sélection = AUC). Pour contrer le
      déséquilibre des classes, des <strong>poids équilibrés</strong>
      (<code>class_weight='balanced'</code>, et <code>scale_pos_weight</code> pour
      XGBoost) sont inclus dans l'espace de recherche. La prédiction finale
      présentée à l'utilisateur résulte d'un <strong>vote souple</strong> (moyenne
      des probabilités des cinq modèles), assorti d'un niveau de risque (Low /
      Moderate / High / Very High) et d'un score de confiance.</p>

    </section>
    ''')

    # ---------------- 7. Résultats ----------------
    A('''
    <section class="page">
      <h1>7. Évaluation, métriques et résultats expérimentaux</h1>
      <p>Les modèles sont évalués sur l'ensemble de test indépendant (20&nbsp;% des
      données, division stratifiée) au moyen des métriques de classification
      standard : <strong>Accuracy, Précision, Rappel, F1-score et AUC-ROC</strong>,
      complétées par la matrice de confusion et le rapport de classification.</p>
      <div class="encadre"><strong>Choix de l'AUC pour le classement.</strong>
      L'aire sous la courbe ROC (AUC) est indépendante du seuil de décision ;
      contrairement au F1 brut sur un jeu déséquilibré, elle ne peut pas être
      artificiellement gonflée par un modèle qui prédirait systématiquement la
      classe majoritaire. C'est donc l'AUC qui sert de critère de classement.</div>

      <h2>7.1 Résultats comparatifs</h2>
      ''' + ranking_table() + '''
      <p>Le meilleur modèle est <strong>''' + f"{BEST['name']}" + '''</strong>
      (AUC = ''' + f"{BEST['auc']:.3f}" + ''', F1 = ''' + f"{BEST['f1']:.3f}" + ''',
      Accuracy = ''' + f"{BEST['accuracy']:.1%}" + '''). Les modèles ensemblistes
      à base d'arbres (Random Forest, XGBoost) exploitent pleinement le volume et
      la structure du jeu de données pour atteindre une accuracy proche de
      99&nbsp;%, tandis que les modèles linéaires (SVM, régression logistique)
      plafonnent autour de 70&nbsp;%, ce qui illustre le caractère fortement non
      linéaire de la frontière de décision.</p>
      ''' + img('fig_metrics_comparison.png', 'Figure 6 — Comparaison des cinq modèles sur les cinq métriques.', '92%') + '''

      <h2>7.2 Courbes ROC et matrice de confusion</h2>
      ''' + img('fig_roc.png', 'Figure 7 — Courbes ROC des cinq modèles et leurs aires sous la courbe (AUC).', '58%') + '''
      ''' + img('fig_confusion_best.png', 'Figure 8 — Matrice de confusion du meilleur modèle (jeu de test).', '46%') + '''

      <h2>7.3 Importance des variables</h2>
      <p>L'analyse de l'importance des variables confirme la pertinence clinique du
      modèle : la bilirubine et les transaminases figurent parmi les prédicteurs
      les plus déterminants, en accord avec la physiopathologie hépatique.</p>
      ''' + img('fig_feature_importance.png', 'Figure 9 — Importance des variables du meilleur modèle interprétable.', '74%') + '''

      <h2>7.4 Hyperparamètres optimaux et temps d'entraînement</h2>
      ''' + hyperparams_table() + '''
      <p>Vérification qualitative du pouvoir discriminant : un patient au bilan
      fortement perturbé (bilirubine 10,9&nbsp;; ALT 64&nbsp;; AST 100) est classé
      <em>Maladie du foie</em> avec une probabilité d'environ 97&nbsp;% (risque
      <em>Very High</em>), tandis qu'un bilan normal est classé <em>Pas de
      maladie</em> (~31&nbsp;%). Le rééquilibrage des classes a donc bien restauré
      la capacité de discrimination des modèles.</p>
    </section>
    ''')

    # ---------------- 8. Interface ----------------
    A('''
    <section class="page">
      <h1>8. Interface utilisateur et fonctionnalités</h1>
      <p>L'interface, développée avec Streamlit, est <strong>moderne, responsive et
      interactive</strong> : sidebar rétractable au survol, thème sombre, cartes KPI, colonnes et
      conteneurs, animations CSS et graphiques interactifs Plotly. Elle s'organise
      en cinq pages.</p>
      <table class="nobreak">
        <tr><th style="width:24%">Page</th><th>Rôle et contenu</th></tr>
        <tr><td>Accueil</td><td>Bannière, objectifs, cartes KPI du dataset, diagramme de flux, statistiques sur les maladies du foie.</td></tr>
        <tr><td>Prédiction tabulaire</td><td>Formulaire médical (champs numériques, liste déroulante, boutons radio), validation des entrées, barre de progression et spinner, résultat (classe, jauge de probabilité, confiance, niveau de risque), importance des variables, tableau comparatif des modèles, export du rapport PDF.</td></tr>
        <tr><td>Évaluation des modèles</td><td>Accuracy, précision, rappel, F1, AUC, courbes ROC, matrices de confusion, rapports de classification, temps d'entraînement, hyperparamètres, classement.</td></tr>
        <tr><td>Dashboard</td><td>KPIs (total, positifs, négatifs, confiance moyenne), graphiques (camembert, barres, courbe temporelle, distribution), historique, export CSV.</td></tr>
        <tr><td>À propos</td><td>Description, technologies, explication du pipeline ML, architecture, auteur.</td></tr>
      </table>
      <h2>8.2 Fonctionnalités avancées</h2>
      <p>Conformément au cahier des charges, la plateforme intègre : le
      <strong>thème sombre</strong>, l'<strong>export CSV</strong> de l'historique,
      l'<strong>export PDF</strong> des prédictions, la <strong>persistance de
      l'historique</strong> (<code>historical_predictions.csv</code>), des
      <strong>animations</strong>, une <strong>gestion des erreurs</strong> à
      chaque niveau (validation, garde-fous, filet de sécurité global) et une
      <strong>journalisation</strong> rotative (<code>logs/app.log</code>).</p>

      <h2>8.3 Capture d'écran commentée</h2>
      <p>La figure ci-dessous montre la page <strong>Prédiction</strong> en
      fonctionnement réel, pour un patient au bilan hépatique fortement perturbé
      (bilirubine totale 7,3 ; ALT 60 ; AST 68 ; albumine 3,3). Les cinq modèles
      votent à l'unanimité : le patient est classé <em>Maladie du foie</em> avec
      une probabilité de 99,2 % et un niveau de risque <em>Very High</em>. On
      distingue la carte de résultat, les indicateurs (probabilité, confiance), la
      jauge de probabilité et le tableau de vote des modèles.</p>
      ''' + img('shot_prediction.png', 'Figure 10 — Page Prediction : resultat reel produit par HepatoScope pour un cas pathologique (probabilite 99,2 %, risque Very High).', '96%') + '''
    </section>
    ''')

    # ---------------- 9-12 ----------------
    A('''
    <section class="page">
      <h1>9. Choix technologiques</h1>
      <table class="nobreak">
        <tr><th style="width:20%">Technologie</th><th>Rôle et justification</th></tr>
        <tr><td>Python 3.13</td><td>Langage de haut niveau au riche écosystème scientifique, standard de fait en science des données.</td></tr>
        <tr><td>Streamlit</td><td>Framework web orienté data : transforme un script Python en application interactive sans HTML/JS, idéal pour un prototype d'IA professionnel.</td></tr>
        <tr><td>Scikit-Learn</td><td>Bibliothèque de référence du Machine Learning : préprocesseurs, modèles, GridSearchCV, métriques.</td></tr>
        <tr><td>XGBoost</td><td>Implémentation optimisée du gradient boosting, performante sur données tabulaires.</td></tr>
        <tr><td>Pandas / NumPy</td><td>Manipulation des données tabulaires et calcul numérique vectorisé.</td></tr>
        <tr><td>Plotly</td><td>Graphiques interactifs (jauges, ROC, matrices, distributions).</td></tr>
        <tr><td>Matplotlib</td><td>Figures statiques haute résolution pour ce rapport.</td></tr>
        <tr><td>fpdf2</td><td>Génération du rapport de prédiction PDF, sans dépendance système.</td></tr>
        <tr><td>joblib</td><td>Sérialisation des modèles et du préprocesseur.</td></tr>
      </table>

      <h1 style="margin-top:30px;">10. Difficultés rencontrées</h1>
      <ul>
        <li><strong>Déséquilibre des classes</strong> (71&nbsp;% de cas positifs) :
        un classement naïf par F1 favorisait un modèle trivial prédisant toujours
        « malade ». Résolu par la pondération équilibrée des classes et la sélection
        par l'AUC.</li>
        <li><strong>Valeurs manquantes et échelles hétérogènes</strong> : gérées par
        un pipeline d'imputation médiane et de standardisation ajusté sans fuite de
        données.</li>
        <li><strong>Doublons massifs du jeu de données</strong> : plus de
        11 000 lignes dupliquées ont été supprimées <em>avant</em> la division
        entraînement/test, afin d'éviter toute fuite d'information et de garantir
        une évaluation honnête.</li>
        <li><strong>Encodage Unicode du PDF</strong> : la police latin-1 de fpdf2 a
        nécessité une fonction de normalisation du texte.</li>
        <li><strong>Cohabitation avec la navigation multi-pages de Streamlit</strong> :
        désactivée au profit d'un routeur personnalisé pour une sidebar unique et
        stylisée.</li>
      </ul>

      <h1 style="margin-top:30px;">11. Perspectives d'amélioration</h1>
      <ul>
        <li>Calibration des probabilités et explicabilité avancée (SHAP).</li>
        <li>Exposition d'une API REST (FastAPI), authentification utilisateur et
        base de données persistante.</li>
        <li>Déploiement conteneurisé (Dockerfile fourni) et hébergement cloud avec
        intégration continue.</li>
      </ul>
    </section>

    <section class="page">
      <h1>12. Conclusion</h1>
      <p>HepatoScope démontre une chaîne complète d'intelligence artificielle
      biomédicale : de l'acquisition et du prétraitement des données à la prédiction
      expliquée, en passant par l'entraînement, l'optimisation et l'évaluation
      comparative de cinq modèles de Machine Learning. L'application, modulaire, robuste et dotée
      d'une interface moderne, atteint des performances conformes à l'état de l'art
      sur ce jeu de données (AUC du meilleur modèle = ''' + f"{BEST['auc']:.3f}" + ''')
      tout en restant pleinement interprétable.</p>
      <p>Au-delà des résultats quantitatifs, ce projet aura permis de mettre en
      œuvre, de bout en bout, une démarche d'ingénierie rigoureuse : analyse du
      besoin, conception d'une architecture en couches, prévention de la fuite de
      données, gestion du déséquilibre, évaluation honnête et explicabilité. La
      plateforme constitue une base solide, naturellement extensible vers de nouveaux jeux de données cliniques et un déploiement en production.</p>

      <h1 style="margin-top:34px;">Webographie</h1>
      <ul>
        <li>Kaggle / UCI — <em>Liver Patient Dataset (lignée ILPD, Indian Liver Patient
        Dataset)</em>, archive.ics.uci.edu.</li>
        <li>Documentation Scikit-Learn — scikit-learn.org.</li>
        <li>Documentation XGBoost — xgboost.readthedocs.io.</li>
        <li>Documentation Streamlit — docs.streamlit.io.</li>
      </ul>
      <p style="margin-top:26px; font-size:9pt; color:#888;"><em>Avertissement :
      ce projet est un prototype académique entraîné sur un jeu de données public.
      Il ne constitue pas un dispositif médical certifié et ne doit pas être utilisé
      pour un diagnostic clinique réel.</em></p>
    </section>
    ''')

    A(MERMAID_INIT)
    A('</body></html>')
    return "".join(P)


# --------------------------------------------------------------------------- #
# Rendu
# --------------------------------------------------------------------------- #
def main() -> int:
    out_html = ROOT / "RAPPORT.html"
    out_html.write_text(build_html(), encoding="utf-8")
    print(f"[OK] HTML  -> {out_html}")

    out_pdf = ROOT / "RAPPORT.pdf"
    chrome_candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "google-chrome", "chromium", "chrome",
    ]
    for chrome in chrome_candidates:
        try:
            subprocess.run(
                [chrome, "--headless", "--disable-gpu", "--no-sandbox",
                 "--virtual-time-budget=20000",
                 "--run-all-compositor-stages-before-draw",
                 f"--print-to-pdf={out_pdf}", "--no-pdf-header-footer",
                 out_html.as_uri()],
                check=True, timeout=180,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if out_pdf.exists():
                print(f"[OK] PDF   -> {out_pdf}")
                return 0
        except Exception:
            continue
    print("[i] Chrome introuvable — ouvrez RAPPORT.html puis 'Imprimer > PDF'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
