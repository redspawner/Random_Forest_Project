"""Drag-and-drop interface for the grey-zone Random Forest.

Start it with   python run_app.py   (or: streamlit run app.py)
Everything runs locally on this computer; patient files are processed in memory.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from greyzone_rf.config import PROJECT_ROOT, load_config
from greyzone_rf.data import DataError, load_patient_file
from greyzone_rf.model import TrainingError, load_bundle, save_bundle, train_model
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

st.set_page_config(page_title="Grey-zone AD triage (Random Forest)", layout="wide")


# ---------------------------------------------------------------------------
# Model handling
# ---------------------------------------------------------------------------
def available_models() -> list[Path]:
    if not MODELS_DIR.exists():
        return []
    dirs = [p for p in MODELS_DIR.iterdir() if (p / "model.joblib").exists()]
    return sorted(dirs, key=lambda p: (p / "model.joblib").stat().st_mtime, reverse=True)


@st.cache_resource(show_spinner="Loading model ...")
def cached_bundle(path: str, mtime: float) -> dict:  # mtime makes the cache refresh after re-training
    return load_bundle(path)


def current_bundle() -> tuple[dict | None, Path | None]:
    models = available_models()
    if not models:
        return None, None
    names = [p.name for p in models]
    preferred = st.session_state.get("model_name")
    index = names.index(preferred) if preferred in names else (names.index("rf_model") if "rf_model" in names else 0)
    name = st.sidebar.selectbox("Model", names, index=index, help="Trained models found in the 'models' folder.")
    st.session_state["model_name"] = name
    folder = MODELS_DIR / name
    try:
        return cached_bundle(str(folder), (folder / "model.joblib").stat().st_mtime), folder
    except Exception as exc:  # corrupted or incompatible file
        st.sidebar.error(f"Could not load this model: {exc}")
        return None, folder


def fmt_threshold(value) -> str:
    return "none" if value is None else f"{value:.2f}"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("Grey-zone AD triage")
st.sidebar.caption("Random Forest on plasma, clinical and MRI data of patients with p-tau217 in the grey zone.")
bundle, model_dir = current_bundle()
if bundle:
    rep = bundle["report"]
    gz = bundle["config"]["grey_zone"]
    st.sidebar.markdown(
        f"**Trained:** {bundle['created'].replace('T', ' ')}  \n"
        f"**Training patients:** {rep['cohort']['n_train']}  \n"
        f"**Grey zone:** {gz['ptau217_lower']}-{gz['ptau217_upper']} pg/mL  \n"
        f"**POSITIVE if score >=** {fmt_threshold(bundle['thresholds']['positive'])}  \n"
        f"**NEGATIVE if score <=** {fmt_threshold(bundle['thresholds']['negative'])}"
    )
    if rep.get("nested"):
        m = rep["nested"]["metrics"]
        st.sidebar.markdown(f"**Expected LPs avoided:** {m['resolved']['value']:.0%} "
                            f"(nested CV, {m['errors']} wrong calls / {m['n']})")
    if "synthetic" in (rep.get("source_file") or "").lower():
        st.sidebar.warning("This model was trained on SYNTHETIC data (demo only).")
else:
    st.sidebar.info("No trained model yet - use the 'Train model' tab.")
st.sidebar.divider()
st.sidebar.caption("Runs locally: files are processed in memory on this computer and are not sent anywhere.")
st.sidebar.caption(DISCLAIMER)

tab_predict, tab_train, tab_report, tab_help = st.tabs(
    ["Classify new patients", "Train model", "Model report", "Template & help"])


def show_predictions(upload, bundle: dict) -> None:
    try:
        prepared = load_patient_file(upload.getvalue(), bundle["config"], filename=upload.name)
    except DataError as exc:
        st.error(f"The file could not be used: {exc}")
        return
    except Exception as exc:  # unreadable/corrupted file
        st.error(f"The file could not be read ({type(exc).__name__}: {exc}). Is it a valid .xlsx/.csv file?")
        return

    results = predict_prepared(bundle, prepared)
    counts = summarize(results)
    grey_n = counts[POSITIVE_TXT] + counts[NEGATIVE_TXT] + counts[INCONCLUSIVE_TXT]
    resolved = counts[POSITIVE_TXT] + counts[NEGATIVE_TXT]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("POSITIVE", counts[POSITIVE_TXT])
    c2.metric("NEGATIVE", counts[NEGATIVE_TXT])
    c3.metric("INCONCLUSIVE -> LP", counts[INCONCLUSIVE_TXT])
    c4.metric("Outside grey zone", counts[NOT_APPLICABLE_TXT])
    c5.metric("Check data", counts[CHECK_DATA_TXT])
    if grey_n:
        st.info(f"**{resolved} of {grey_n} grey-zone patients ({resolved / grey_n:.0%}) received a definite "
                f"answer; {counts[INCONCLUSIVE_TXT]} remain inconclusive and should have a lumbar puncture.**")
    if counts[CHECK_DATA_TXT]:
        st.error(f"{counts[CHECK_DATA_TXT]} patient(s) have implausible or invalid values and were NOT "
                 "classified. Correct the file and upload it again.")
    if prepared.messages:
        with st.expander(f"File notes ({len(prepared.messages)})"):
            for message in prepared.messages:
                st.write("- " + message)

    shown = st.multiselect("Show decisions", DECISION_ORDER, default=DECISION_ORDER)
    view = results[results["decision"].isin(shown)]
    styled = view.style.map(lambda v: DECISION_COLORS.get(v, ""), subset=["decision"])
    st.dataframe(
        styled, hide_index=True,
        column_config={
            "patient_id": st.column_config.TextColumn("Patient", width="small"),
            "decision": st.column_config.TextColumn("Decision", width="medium"),
            "rf_score": st.column_config.ProgressColumn("RF score", min_value=0.0, max_value=1.0,
                                                        format="%.3f", width="small"),
            "ptau217": st.column_config.NumberColumn("p-tau217 (pg/mL)", format="%.3f", width="small"),
            "explanation": st.column_config.TextColumn("Why", width="large"),
            "missing_variables": st.column_config.TextColumn("Missing variables"),
            "notes": st.column_config.TextColumn("Notes"),
        },
    )
    stem = Path(upload.name).stem
    d1, d2 = st.columns(2)
    d1.download_button("Download my file with the predictions added", type="primary",
                       data=annotated_original(results, prepared, bundle),
                       file_name=f"{stem}_with_predictions.xlsx", mime=XLSX_MIME,
                       help="Your uploaded file, unchanged, with extra columns on each patient row: AI decision, "
                            "RF score, explanation, missing variables and notes. A sheet 'AI prediction info' "
                            "describes the model used.")
    d2.download_button("Download results report (Excel)", data=results_to_excel(results, prepared, bundle),
                       file_name=f"{stem}_results.xlsx", mime=XLSX_MIME,
                       help="Separate workbook: results table, summary and a copy of the input.")


# ---------------------------------------------------------------------------
# 1. Prediction
# ---------------------------------------------------------------------------
with tab_predict:
    st.header("Classify new grey-zone patients")
    st.write("Drag and drop an Excel (.xlsx) or CSV file with one row per patient, in the layout of the template "
             "(see *Template & help*). Each patient is classified as **POSITIVE**, **NEGATIVE** or "
             "**INCONCLUSIVE - refer to LP**. A definite answer is only given when the model has demonstrated "
             "at least 95% PPV/NPV for patients with that score; everybody else stays inconclusive.")
    if bundle is None:
        st.warning("No trained model available. Go to **Train model** first "
                   "(the synthetic demo file can be used to try the tool).")
    upload = st.file_uploader("Drag and drop the patient file here", type=["xlsx", "xlsm", "csv"],
                              key="predict_upload", disabled=bundle is None)
    if upload is not None and bundle is not None:
        show_predictions(upload, bundle)


# ---------------------------------------------------------------------------
# 2. Training
# ---------------------------------------------------------------------------
with tab_train:
    st.header("Train a new model")
    st.write("Drag and drop the **training file**: grey-zone patients with their variables **and** the "
             "lumbar-puncture result in the column `lp_result` (Positive/Negative). Settings (grey-zone cut-offs, "
             "95% targets, Random-Forest parameters, list of variables) are read from `config.yaml`.")
    cfg_now = load_config()
    train_upload = st.file_uploader("Drag and drop the training file here", type=["xlsx", "xlsm", "csv"],
                                    key="train_upload")
    col_a, col_b = st.columns([2, 1])
    nested = col_a.checkbox("Honest validation with nested cross-validation (recommended, ~1 minute)",
                            value=bool(cfg_now["validation"]["nested_cv"]))
    default_name = "rf_" + dt.datetime.now().strftime("%Y%m%d_%H%M")
    model_name = col_b.text_input("Model name", value=default_name)
    if st.button("Train model", type="primary", disabled=train_upload is None):
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", model_name.strip()) or default_name
        try:
            prepared = load_patient_file(train_upload.getvalue(), cfg_now, require_label=True,
                                         filename=train_upload.name)
            bar = st.progress(0.0, text="Starting ...")
            new_bundle = train_model(prepared, cfg_now, nested=nested, source_name=train_upload.name,
                                     progress=lambda f, m: bar.progress(f, text=m))
            out_dir = MODELS_DIR / safe_name
            save_bundle(new_bundle, out_dir)
            write_report(new_bundle, out_dir)
            bar.progress(1.0, text="Done")
        except (DataError, TrainingError) as exc:
            st.error(str(exc))
        else:
            st.session_state["model_name"] = safe_name
            st.success(f"Model saved to `models/{safe_name}`. Click **Use the new model now** (or select it in the "
                       "sidebar) to classify patients with it; details are in **Model report**.")
            t = new_bundle["thresholds"]
            st.write(f"POSITIVE if score >= **{fmt_threshold(t['positive'])}**, "
                     f"NEGATIVE if score <= **{fmt_threshold(t['negative'])}**.")
            for message in new_bundle["report"]["messages"]:
                st.warning(message)
            st.button("Use the new model now")  # triggers a rerun that refreshes the sidebar


# ---------------------------------------------------------------------------
# 3. Report
# ---------------------------------------------------------------------------
with tab_report:
    if bundle is None:
        st.info("No model selected.")
    else:
        missing_figs = any(not (model_dir / f).exists() for k, f in FIGURES.items()
                           if k != "importance" or bundle["report"].get("importance"))
        if missing_figs:
            write_report(bundle, model_dir)
        st.markdown(markdown_report(bundle))
        st.subheader("Figures")
        st.image(str(model_dir / FIGURES["scores"]), width="stretch",
                 caption="Out-of-fold RF scores of the training patients, by LP result, with the three zones.")
        left, right = st.columns(2)
        left.image(str(model_dir / FIGURES["roc"]), width="stretch")
        if bundle["report"].get("importance"):
            right.image(str(model_dir / FIGURES["importance"]), width="stretch")
        st.image(str(model_dir / FIGURES["safety"]), width="stretch",
                 caption="How the thresholds were chosen: predictive value and its lower confidence bound for "
                         "every candidate threshold.")
        pred_file = model_dir / "training_predictions.xlsx"
        if pred_file.exists():
            st.download_button("Download out-of-fold predictions of the training patients",
                               data=pred_file.read_bytes(), file_name=f"{model_dir.name}_training_predictions.xlsx",
                               mime=XLSX_MIME)


# ---------------------------------------------------------------------------
# 4. Template & help
# ---------------------------------------------------------------------------
with tab_help:
    cfg_now = load_config()
    st.header("Input file layout")
    st.write("One row per patient in a sheet called **Patients**. Column names must match the list below (units in "
             "brackets are optional, upper/lower case does not matter). Blank cell = missing value. "
             "Only `ptau217` is mandatory.")
    st.download_button("Download the Excel template", data=build_template(cfg_now),
                       file_name="patient_data_template.xlsx", mime=XLSX_MIME, type="primary")
    st.dataframe(dictionary_frame(cfg_now), hide_index=True)

    st.subheader("Synthetic demo files")
    st.write("Artificial patients, generated by `make_demo_data.py`, to try the tool. **Not real data.**")
    demo_cols = st.columns(3)
    for col, (fname, label) in zip(demo_cols, [
            ("synthetic_training_cohort.xlsx", "Training cohort (with LP)"),
            ("synthetic_new_patients.xlsx", "New patients (without LP)"),
            ("synthetic_new_patients_answer_key.xlsx", "Answer key of the new patients")]):
        path = SYNTHETIC_DIR / fname
        if path.exists():
            col.download_button(label, data=path.read_bytes(), file_name=fname, mime=XLSX_MIME)

    st.subheader("How the decision is made")
    dec = cfg_now["decision"]
    st.markdown(f"""
1. **Stage 1 (already done at the centre):** plasma p-tau217 < {cfg_now['grey_zone']['ptau217_lower']} pg/mL is
   negative, > {cfg_now['grey_zone']['ptau217_upper']} pg/mL is positive. Only patients in between are analysed here.
2. **Random Forest:** {cfg_now['random_forest']['n_estimators']} decision trees combine all variables into a score
   between 0 and 1 (missing values are handled inside the trees).
3. **Safety thresholds:** during training every patient receives a cross-validated score (from models that never saw
   them). The tool then finds the lowest score above which at least {dec['target_ppv']:.0%} of patients were
   LP-positive (PPV) and the highest score below which at least {dec['target_npv']:.0%} were LP-negative (NPV).
   {"It requires the **lower bound of the one-sided " + format(dec['confidence_level'], '.0%') +
    " confidence interval** to reach the target, so the 95% is demonstrated statistically, not just observed."
    if dec['use_confidence_bound'] else "Only the point estimate must reach the target (exploratory mode)."}
4. **Everything in between stays INCONCLUSIVE** and is referred to lumbar puncture, exactly as before.
5. **Safety checks:** patients outside the grey zone are not classified by the model; implausible values
   (e.g. MoCA = 34) block the classification; patients missing more than
   {dec['max_missing_fraction']:.0%} of the variables stay inconclusive.
""")
