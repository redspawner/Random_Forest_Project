"""Drag-and-drop interface for the grey-zone models (Random Forest, Logistic Regression, Gradient Boosting, ...).

Start it with   python run_app.py   (or: streamlit run app.py)
Everything runs locally on this computer; patient files are processed in memory.
"""

from __future__ import annotations

import datetime as dt
import io
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from greyzone_rf.config import PROJECT_ROOT, load_config
from greyzone_rf.data import DataError, load_patient_file
from greyzone_rf.compare import (calibration_figure, classify_with_all, comparison_table, paired_differences,
                                 roc_figure, same_patients, triage_figure)
from greyzone_rf.default_model import default_dir, default_status, shipped_types, train_default
from greyzone_rf.estimators import DEFAULT_TYPE, model_label
from greyzone_rf.i18n import LANG, tr
from greyzone_rf.model import TrainingError, load_bundle, model_info, save_bundle, train_model
from greyzone_rf.predict import (CHECK_DATA_TXT, DECISION_ORDER, DISCLAIMER, INCONCLUSIVE_TXT, NEGATIVE_TXT,
                                 NOT_APPLICABLE_TXT, POSITIVE_TXT, annotated_original, predict_prepared,
                                 results_to_excel, summarize)
from greyzone_rf.report import FIGURES, markdown_report, write_report
from greyzone_rf.template import build_template, dictionary_frame

MODELS_DIR = PROJECT_ROOT / "models"
SYNTHETIC_DIR = PROJECT_ROOT / "data" / "synthetic"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DECISION_COLORS = {
    POSITIVE_TXT: "background-color: #f8d7d3; color: #0b0b0b; font-weight: 600",
    NEGATIVE_TXT: "background-color: #d5ecdd; color: #0b0b0b; font-weight: 600",
    INCONCLUSIVE_TXT: "background-color: #fcebc5; color: #0b0b0b; font-weight: 600",
    NOT_APPLICABLE_TXT: "background-color: #e7e6e2; color: #0b0b0b",
    CHECK_DATA_TXT: "background-color: #e7e6e2; color: #0b0b0b",
}

st.set_page_config(page_title=tr("Grey-zone AD triage"), layout="wide")
if LANG == "pt":
    # Streamlit's own file-uploader texts are English only: replace them visually.
    st.markdown("""<style>
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] p { font-size: 0; }
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] p::after {
  content: "Carregar"; font-size: 14px; }
[data-testid="stFileUploaderDropzoneInstructions"] > div > span { font-size: 0; }
[data-testid="stFileUploaderDropzoneInstructions"] > div > span::after {
  content: "ou arraste o ficheiro para aqui \\2022  máx. 50 MB \\2022  XLSX, XLSM, CSV"; font-size: 14px; }
</style>""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Model handling
# ---------------------------------------------------------------------------
def available_models(kind: str | None = None) -> list[Path]:
    """Trained model folders (newest first); only those of ``kind`` when given."""
    if not MODELS_DIR.exists():
        return []
    dirs = [p for p in MODELS_DIR.iterdir() if (p / "model.joblib").exists()]
    if kind is not None:
        dirs = [p for p in dirs if model_info(p).get("model_type", DEFAULT_TYPE) == kind]
    return sorted(dirs, key=lambda p: (p / "model.joblib").stat().st_mtime, reverse=True)


@st.cache_resource(show_spinner=tr("Loading model ..."))
def cached_bundle(path: str, mtime: float) -> dict:  # mtime makes the cache refresh after re-training
    return load_bundle(path)


def load_folder(folder: Path) -> dict:
    return cached_bundle(str(folder), (folder / "model.joblib").stat().st_mtime)


def ensure_default_model(kind: str) -> None:
    """Out-of-the-box model: re-train it from the preserved dataset if it is missing or unusable."""
    cfg = load_config()
    if not (cfg.get("default_model") or {}).get("auto_train_if_missing", True):
        return
    status = default_status(cfg, kind)
    failed = st.session_state.setdefault("default_training_failed", set())
    if status["loadable"] or not status["data_exists"] or kind in failed:
        return
    reason = tr("not found") if not status["model_exists"] else tr("not compatible with this installation")
    with st.spinner(tr("The default {model} model is {reason}: training it from {name} (about 1 minute, only "
                       "once) ...", model=model_label(kind), reason=reason, name=status["data_path"].name)):
        try:
            train_default(cfg, kind=kind)
        except Exception as exc:
            failed.add(kind)
            st.sidebar.error(tr("Could not train the default model: {exc}", exc=exc))


def current_bundle(kind: str) -> tuple[dict | None, Path | None]:
    ensure_default_model(kind)
    models = available_models(kind)
    if not models:
        return None, None
    names = [p.name for p in models]
    preferred = st.session_state.get(f"model_name_{kind}")
    default_name = default_dir(load_config(), kind).name
    index = names.index(preferred) if preferred in names else (names.index(default_name) if default_name in names else 0)
    name = st.sidebar.selectbox(tr("Trained model"), names, index=index,
                                help=tr("Trained models of this type found in the 'models' folder."))
    st.session_state[f"model_name_{kind}"] = name
    folder = MODELS_DIR / name
    try:
        return load_folder(folder), folder
    except Exception as exc:  # corrupted or incompatible file
        st.sidebar.error(tr("Could not load this model: {exc}", exc=exc))
        return None, folder


def fmt_threshold(value) -> str:
    return tr("none") if value is None else f"{value:.2f}"


# ---------------------------------------------------------------------------
# Header with the model switch (top right)
# ---------------------------------------------------------------------------
TYPES = shipped_types(load_config())
head_left, head_right = st.columns([3, 1], vertical_alignment="bottom")
head_left.title(tr("Grey-zone AD triage"))
if "model_type" not in st.session_state or st.session_state["model_type"] not in TYPES:
    st.session_state["model_type"] = DEFAULT_TYPE if DEFAULT_TYPE in TYPES else TYPES[0]
MODEL_TYPE = head_right.selectbox(
    tr("ML model"), TYPES, key="model_type", format_func=model_label,
    help=tr("Algorithm that computes the score. Every model uses the same training procedure, the same "
            "{ppv:.0%} PPV / {npv:.0%} NPV rule with {conf:.0%} confidence and the same safety checks. "
            "See the tab 'Compare models'.", ppv=load_config()["decision"]["target_ppv"],
            npv=load_config()["decision"]["target_npv"], conf=load_config()["decision"]["confidence_level"]))
MODEL_LABEL = model_label(MODEL_TYPE)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title(MODEL_LABEL)
st.sidebar.caption(tr("{model} on plasma and clinical data of patients with p-tau217 in the grey zone.",
                      model=MODEL_LABEL))
bundle, model_dir = current_bundle(MODEL_TYPE)
if bundle:
    rep = bundle["report"]
    gz = bundle["config"]["grey_zone"]
    st.sidebar.markdown(tr(
        "**Trained:** {created}  \n**Training patients:** {n}  \n**Grey zone:** {lo}-{hi} pg/mL  \n"
        "**POSITIVE if score >=** {pos}  \n**NEGATIVE if score <=** {neg}",
        created=bundle["created"].replace("T", " "), n=rep["cohort"]["n_train"], lo=gz["ptau217_lower"],
        hi=gz["ptau217_upper"], pos=fmt_threshold(bundle["thresholds"]["positive"]),
        neg=fmt_threshold(bundle["thresholds"]["negative"])))
    if rep.get("nested"):
        m = rep["nested"]["metrics"]
        st.sidebar.markdown(tr("**Expected LPs avoided:** {v:.0%} (nested CV, {e} wrong calls / {n})",
                               v=m["resolved"]["value"], e=m["errors"], n=m["n"]))
    if model_dir is not None and (model_dir / "manifest.json").exists():
        info = default_status(kind=MODEL_TYPE)
        manifest = info["manifest"] or {}
        st.sidebar.markdown(tr("**Default model** trained on `{file}`  \nSHA-256 `{sha}...`",
                               file=manifest.get("training_file", "?"),
                               sha=manifest.get("training_file_sha256", "")[:12]))
        if info["dataset_matches"] is False and info["model_dir"] == model_dir:
            st.sidebar.error(tr("The default dataset file has changed since this model was trained. "
                                "Re-train it: python train.py --default"))
    if "synthetic" in (rep.get("source_file") or "").lower():
        st.sidebar.warning(tr("This model was trained on SYNTHETIC data (demo only)."))
else:
    st.sidebar.info(tr("No trained model yet - use the 'Train model' tab."))
st.sidebar.divider()
st.sidebar.caption(tr("Runs locally: files are processed in memory on this computer and are not sent anywhere."))
st.sidebar.caption(DISCLAIMER)

tab_predict, tab_train, tab_report, tab_compare, tab_help = st.tabs(
    [tr("Classify new patients"), tr("Train model"), tr("Model report"), tr("Compare models"),
     tr("Template & help")])


def read_upload(upload, cfg: dict):
    """Parse an uploaded patient file, showing the error in the page if it cannot be used."""
    try:
        return load_patient_file(upload.getvalue(), cfg, filename=upload.name)
    except DataError as exc:
        st.error(tr("The file could not be used: {exc}", exc=exc))
    except Exception as exc:  # unreadable/corrupted file
        st.error(tr("The file could not be read ({kind}: {exc}). Is it a valid .xlsx/.csv file?",
                    kind=type(exc).__name__, exc=exc))
    return None


def show_predictions(upload, bundle: dict) -> None:
    prepared = read_upload(upload, bundle["config"])
    if prepared is None:
        return

    results = predict_prepared(bundle, prepared)
    counts = summarize(results)
    grey_n = counts[POSITIVE_TXT] + counts[NEGATIVE_TXT] + counts[INCONCLUSIVE_TXT]
    resolved = counts[POSITIVE_TXT] + counts[NEGATIVE_TXT]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(tr("POSITIVE"), counts[POSITIVE_TXT])
    c2.metric(tr("NEGATIVE"), counts[NEGATIVE_TXT])
    c3.metric(tr("INCONCLUSIVE -> LP"), counts[INCONCLUSIVE_TXT])
    c4.metric(tr("Outside grey zone"), counts[NOT_APPLICABLE_TXT])
    c5.metric(tr("Check data"), counts[CHECK_DATA_TXT])
    if grey_n:
        st.info(tr("**{r} of {n} grey-zone patients ({p:.0%}) received a definite answer; {i} remain inconclusive "
                   "and should have a lumbar puncture.**", r=resolved, n=grey_n, p=resolved / grey_n,
                   i=counts[INCONCLUSIVE_TXT]))
    if counts[CHECK_DATA_TXT]:
        st.error(tr("{n} patient(s) have implausible or invalid values and were NOT classified. Correct the file "
                    "and upload it again.", n=counts[CHECK_DATA_TXT]))
    if prepared.messages:
        with st.expander(tr("File notes ({n})", n=len(prepared.messages))):
            for message in prepared.messages:
                st.write("- " + message)

    shown = st.multiselect(tr("Show decisions"), DECISION_ORDER, default=DECISION_ORDER)
    view = results[results["decision"].isin(shown)]
    styled = view.style.map(lambda v: DECISION_COLORS.get(v, ""), subset=["decision"])
    st.dataframe(
        styled, hide_index=True,
        column_config={
            "patient_id": st.column_config.TextColumn(tr("Patient"), width="small"),
            "decision": st.column_config.TextColumn(tr("Decision"), width="medium"),
            "score": st.column_config.ProgressColumn(tr("Score"), min_value=0.0, max_value=1.0,
                                                        format="%.3f", width="small"),
            "ptau217": st.column_config.NumberColumn("p-tau217 (pg/mL)", format="%.3f", width="small"),
            "explanation": st.column_config.TextColumn(tr("Why"), width="large"),
            "missing_variables": st.column_config.TextColumn(tr("Missing variables")),
            "notes": st.column_config.TextColumn(tr("Notes")),
        },
    )
    stem = Path(upload.name).stem
    d1, d2 = st.columns(2)
    d1.download_button(tr("Download my file with the predictions added"), type="primary",
                       data=annotated_original(results, prepared, bundle),
                       file_name=f"{stem}{tr('_with_predictions')}.xlsx", mime=XLSX_MIME,
                       help=tr("Your uploaded file, unchanged, with extra columns on each patient row: AI decision, "
                               "model, score, explanation, missing variables and notes. A sheet 'AI prediction info' "
                               "describes the model used."))
    d2.download_button(tr("Download results report (Excel)"), data=results_to_excel(results, prepared, bundle),
                       file_name=f"{stem}{tr('_results')}.xlsx", mime=XLSX_MIME,
                       help=tr("Separate workbook: results table, summary and a copy of the input."))


# ---------------------------------------------------------------------------
# 1. Prediction
# ---------------------------------------------------------------------------
with tab_predict:
    st.header(tr("Classify new grey-zone patients"))
    st.caption(tr("Model in use: **{model}** (change it at the top right).", model=MODEL_LABEL))
    _dec = (bundle or {}).get("config", load_config())["decision"]
    st.write(tr("Drag and drop an Excel (.xlsx) or CSV file with one row per patient, in the layout of the "
                "template (see *Template & help*). Each patient is classified as **POSITIVE**, **NEGATIVE** or "
                "**INCONCLUSIVE - refer to LP**. A definite answer is only given when the model has demonstrated "
                "at least {ppv:.0%} PPV / {npv:.0%} NPV for patients with that score; everybody else stays "
                "inconclusive.", ppv=_dec["target_ppv"], npv=_dec["target_npv"]))
    if bundle is None:
        st.warning(tr("No trained model available. Go to **Train model** first "
                      "(the synthetic demo file can be used to try the tool)."))
    upload = st.file_uploader(tr("Drag and drop the patient file here"), type=["xlsx", "xlsm", "csv"],
                              key="predict_upload", disabled=bundle is None)
    if upload is not None and bundle is not None:
        show_predictions(upload, bundle)


# ---------------------------------------------------------------------------
# 2. Training
# ---------------------------------------------------------------------------
with tab_train:
    st.header(tr("Train a new model"))
    st.write(tr("Drag and drop the **training file**: grey-zone patients with their variables **and** the "
                "lumbar-puncture result in the column `lp_result` (Positive/Negative). Settings (grey-zone "
                "cut-offs, PPV/NPV targets, model parameters, list of variables) are read from "
                "`config.yaml`."))
    cfg_now = load_config()
    train_upload = st.file_uploader(tr("Drag and drop the training file here"), type=["xlsx", "xlsm", "csv"],
                                    key="train_upload")
    col_a, col_b = st.columns([2, 1])
    nested = col_a.checkbox(tr("Honest validation with nested cross-validation (recommended, ~1 minute)"),
                            value=bool(cfg_now["validation"]["nested_cv"]))
    train_all = col_a.checkbox(tr("Train every model type on this file (needed for a fair comparison)"),
                               value=False)
    default_name = "model_" + dt.datetime.now().strftime("%Y%m%d_%H%M")
    model_name = col_b.text_input(tr("Model name"), value=default_name)
    kinds = TYPES if train_all else [MODEL_TYPE]
    st.caption(tr("Will train: {models}", models=", ".join(model_label(k) for k in kinds)))
    if st.button(tr("Train model"), type="primary", disabled=train_upload is None):
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", model_name.strip()) or default_name
        trained = []
        try:
            prepared = load_patient_file(train_upload.getvalue(), cfg_now, require_label=True,
                                         filename=train_upload.name)
            for kind in kinds:
                bar = st.progress(0.0, text=f"{model_label(kind)}: " + tr("Starting ..."))
                new_bundle = train_model(prepared, cfg_now, nested=nested, source_name=train_upload.name,
                                         model_type_name=kind,
                                         progress=lambda f, m, k=kind, b=bar: b.progress(f, text=f"{model_label(k)}: {m}"))
                folder = safe_name if len(kinds) == 1 else f"{safe_name}_{kind}"
                save_bundle(new_bundle, MODELS_DIR / folder)
                write_report(new_bundle, MODELS_DIR / folder)
                bar.progress(1.0, text=f"{model_label(kind)}: " + tr("Done"))
                trained.append((kind, folder, new_bundle))
        except (DataError, TrainingError) as exc:
            st.error(str(exc))
        for kind, folder, new_bundle in trained:
            st.session_state[f"model_name_{kind}"] = folder
            t = new_bundle["thresholds"]
            st.success(tr("{model} saved to `models/{name}`: POSITIVE if score >= **{pos}**, NEGATIVE if score <= "
                          "**{neg}**.", model=model_label(kind), name=folder, pos=fmt_threshold(t["positive"]),
                          neg=fmt_threshold(t["negative"])))
            for message in new_bundle["report"]["messages"]:
                st.warning(f"{model_label(kind)}: {message}")
        if trained:
            st.info(tr("Click **Use the new model now** (or select it in the sidebar) to classify patients with it; "
                       "details are in **Model report** and **Compare models**."))
            st.button(tr("Use the new model now"))  # triggers a rerun that refreshes the sidebar


# ---------------------------------------------------------------------------
# 3. Report
# ---------------------------------------------------------------------------
with tab_report:
    if bundle is None:
        st.info(tr("No model selected."))
    else:
        st.caption(tr("Report of the **{model}** model `{name}` (change the model at the top right).",
                      model=MODEL_LABEL, name=model_dir.name))
        missing_figs = any(not (model_dir / f).exists() for k, f in FIGURES.items()
                           if k != "importance" or bundle["report"].get("importance"))
        if missing_figs:
            write_report(bundle, model_dir)
        st.markdown(markdown_report(bundle))
        st.subheader(tr("Figures"))
        st.image(str(model_dir / FIGURES["scores"]), width="stretch",
                 caption=tr("Out-of-fold scores of the training patients, by LP result, with the three zones."))
        left, right = st.columns(2)
        left.image(str(model_dir / FIGURES["roc"]), width="stretch")
        if bundle["report"].get("importance"):
            right.image(str(model_dir / FIGURES["importance"]), width="stretch")
        st.image(str(model_dir / FIGURES["safety"]), width="stretch",
                 caption=tr("How the thresholds were chosen: predictive value and its lower confidence bound "
                            "for every candidate threshold."))
        pred_file = model_dir / "training_predictions.xlsx"
        if pred_file.exists():
            st.download_button(tr("Download out-of-fold predictions of the training patients"),
                               data=pred_file.read_bytes(), file_name=f"{model_dir.name}_training_predictions.xlsx",
                               mime=XLSX_MIME)


# ---------------------------------------------------------------------------
# 4. Comparison of the models
# ---------------------------------------------------------------------------
def compare_name(folder: Path, kind: str) -> str:
    label = model_label(kind)
    return label if folder == default_dir(load_config(), kind) else f"{label} · {folder.name}"


@st.cache_data(show_spinner=tr("Comparing the models ..."))
def cached_comparison(keys: tuple, reference: str) -> dict:
    """Figures and tables for the selected model folders (keys = (name, folder, mtime) tuples)."""
    bundles = {name: load_folder(Path(folder)) for name, folder, _ in keys}
    out = {"table": comparison_table(bundles), "roc": roc_figure(bundles), "triage": triage_figure(bundles),
           "calibration": calibration_figure(bundles), "paired": None, "same": same_patients(bundles)}
    if out["same"] and len(bundles) > 1:
        out["paired"] = paired_differences(bundles, reference, n_boot=1000)
    return out


with tab_compare:
    st.header(tr("Compare the models"))
    st.write(tr("All models are trained with the same procedure, on the same patients and the same random splits, "
                "and must meet the same rule (PPV >= {ppv:.0%} and NPV >= {npv:.0%}, proven with {conf:.0%} "
                "confidence) before they may call a patient POSITIVE or NEGATIVE. The best model is the one that "
                "**avoids the most lumbar punctures in nested validation without more wrong calls**; AUC only "
                "measures how well the scores are ordered.", ppv=load_config()["decision"]["target_ppv"],
                npv=load_config()["decision"]["target_npv"], conf=load_config()["decision"]["confidence_level"]))
    folders = {}
    found = [(folder, model_info(folder).get("model_type", DEFAULT_TYPE)) for folder in available_models()]
    order = {k: i for i, k in enumerate(TYPES)}
    for folder, kind in sorted(found, key=lambda fk: (fk[0] != default_dir(load_config(), fk[1]),
                                                      order.get(fk[1], 99))):
        folders[compare_name(folder, kind)] = (folder, kind)
    defaults = [n for n, (f, k) in folders.items() if f == default_dir(load_config(), k)]
    chosen = st.multiselect(tr("Models to compare"), list(folders), default=defaults,
                            help=tr("By default the shipped models of every type, all trained on the same "
                                    "dataset. To compare models on your own data, train them with 'Train every "
                                    "model type' in the Train model tab."))
    if not chosen:
        st.info(tr("Select at least one model."))
    else:
        reference = st.selectbox(tr("Reference model for the paired differences"), chosen,
                                 index=next((i for i, n in enumerate(chosen) if folders[n][1] == DEFAULT_TYPE), 0))
        keys = tuple((n, str(folders[n][0]), (folders[n][0] / "model.joblib").stat().st_mtime) for n in chosen)
        try:
            comp = cached_comparison(keys, reference)
        except Exception as exc:
            st.error(tr("Could not load this model: {exc}", exc=exc))
            comp = None
        if comp is not None:
            st.subheader(tr("Results"))
            st.dataframe(comp["table"], hide_index=True)
            st.caption(tr("LPs avoided, wrong calls, PPV and NPV come from nested cross-validation (patients never "
                          "used to build or tune the model): this is the honest estimate for new patients. Brier "
                          "score: mean squared error of the score as a probability (lower = better calibrated)."))
            left, right = st.columns(2)
            left.image(comp["triage"], width="stretch")
            right.image(comp["roc"], width="stretch")
            left.image(comp["calibration"], width="stretch")
            with right:
                st.markdown(tr("**How to read this page**\n\n"
                               "- **LPs avoided** is what matters clinically: patients spared a lumbar puncture "
                               "while every POSITIVE/NEGATIVE call stays within the safety rule.\n"
                               "- Overlapping confidence intervals mean the models cannot be told apart with these "
                               "patients.\n"
                               "- A model can have a similar AUC but avoid fewer LPs: what counts is how many "
                               "patients fall in the zones where the safety rule is proven.\n"
                               "- Choosing the best of several models on the same data is slightly optimistic: "
                               "confirm the choice on an independent cohort."))
            if comp["paired"] is not None and not comp["paired"].empty:
                st.subheader(tr("Paired differences versus {model}", model=reference))
                st.dataframe(comp["paired"], hide_index=True)
                st.caption(tr("Same patients, same folds; 95% bootstrap confidence intervals (1000 resamples). "
                              "'Significant' means the interval excludes zero."))
            elif not comp["same"]:
                st.warning(tr("These models were not trained on the same patients, so paired differences cannot "
                              "be computed. Train them together with 'Train every model type'."))

            st.subheader(tr("Classify a file with every model"))
            cmp_upload = st.file_uploader(tr("Drag and drop the patient file here"), type=["xlsx", "xlsm", "csv"],
                                          key="compare_upload")
            if cmp_upload is not None:
                bundles = {n: load_folder(folders[n][0]) for n in chosen}
                prepared = read_upload(cmp_upload, next(iter(bundles.values()))["config"])
                if prepared is not None:
                    wide = classify_with_all(bundles, prepared)
                    agree = (wide[tr("All models agree")] == tr("yes")).mean()
                    st.info(tr("The models agree on {p:.0%} of the patients.", p=agree))
                    st.dataframe(wide, hide_index=True)
                    buffer = io.BytesIO()
                    wide.to_excel(buffer, index=False)
                    st.download_button(tr("Download the comparison (Excel)"), data=buffer.getvalue(),
                                       file_name=f"{Path(cmp_upload.name).stem}{tr('_model_comparison')}.xlsx",
                                       mime=XLSX_MIME)


# ---------------------------------------------------------------------------
# 5. Template & help
# ---------------------------------------------------------------------------
with tab_help:
    cfg_now = load_config()
    st.header(tr("Input file layout"))
    st.write(tr("One row per patient in a sheet called **Patients**. Column names must match the list below (units "
                "in brackets are optional, upper/lower case does not matter). Blank cell = missing value. "
                "Only `ptau217` is mandatory."))
    st.download_button(tr("Download the Excel template"), data=build_template(cfg_now),
                       file_name=tr("patient_data_template.xlsx"), mime=XLSX_MIME, type="primary")
    st.dataframe(dictionary_frame(cfg_now), hide_index=True)

    st.subheader(tr("Synthetic demo files"))
    st.write(tr("Artificial patients, generated by `make_demo_data.py`, to try the tool. **Not real data.**"))
    demo_cols = st.columns(3)
    for col, (fname, label) in zip(demo_cols, [
            ("../default_training/synthetic_training_dataset.xlsx", tr("Default training dataset (with LP)")),
            ("synthetic_new_patients.xlsx", tr("New patients (without LP)")),
            ("synthetic_new_patients_answer_key.xlsx", tr("Answer key of the new patients"))]):
        path = SYNTHETIC_DIR / fname
        if path.exists():
            col.download_button(label, data=path.read_bytes(), file_name=Path(fname).name, mime=XLSX_MIME)

    st.subheader(tr("How the decision is made"))
    dec = cfg_now["decision"]
    bound = (tr("It requires the **lower bound of the one-sided {conf:.0%} confidence interval** to reach the "
                "target, so the target is demonstrated statistically, not just observed.",
                conf=dec["confidence_level"])
             if dec["use_confidence_bound"] else
             tr("Only the point estimate must reach the target (exploratory mode)."))
    st.markdown(tr("""
1. **Stage 1 (already done at the centre):** plasma p-tau217 < {lo} pg/mL is negative, > {hi} pg/mL is
   positive. Only patients in between are analysed here.
2. **Model ({model}, chosen at the top right):** combines all variables into a score between 0 and 1. Missing
   values are handled inside the trees (Random Forest, Extra Trees, Gradient Boosting) or replaced by the training
   median plus a "was missing" indicator (Logistic Regression, SVM).
3. **Safety thresholds:** during training every patient receives a cross-validated score (from models that never
   saw them). The tool then finds the lowest score above which at least {ppv:.0%} of patients were LP-positive
   (PPV) and the highest score below which at least {npv:.0%} were LP-negative (NPV). {bound}
4. **Everything in between stays INCONCLUSIVE** and is referred to lumbar puncture, exactly as before.
5. **Safety checks:** patients outside the grey zone are not classified by the model; implausible values
   (e.g. haemoglobin = 45 g/dL) block the classification; patients with a red flag (atypical features) or missing
   more than {miss:.0%} of the variables stay inconclusive.
""", lo=cfg_now["grey_zone"]["ptau217_lower"], hi=cfg_now["grey_zone"]["ptau217_upper"],
                   model=MODEL_LABEL, ppv=dec["target_ppv"], npv=dec["target_npv"],
                   bound=bound, miss=dec["max_missing_fraction"]))
