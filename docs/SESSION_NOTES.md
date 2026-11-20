# Session notes - state of the project and decisions (for continuing the work)

Last updated 2026-11-15. Branch `claude/alzheimer-rf-prediction-pzvrf5` (GitHub redspawner/Random_Forest_Project).
All work is committed and pushed. Detailed explanations: `README.md`, `docs/PROJECT_GUIDE.md`,
`docs/VARIABLE_ANALYSIS.md`, `data/default_training/DATASET_CARD.md`.

## Goal (from the user)
A Random Forest for memory-clinic patients whose Lumipulse plasma p-tau217 is in the grey zone
**0.14–0.43 pg/mL**. The label is the lumbar-puncture (CSF) result. Each patient gets POSITIVE / NEGATIVE
when the confidence target is met; otherwise INCONCLUSIVE → lumbar puncture. The aim is fewer LPs. There is
a drag-and-drop app (Excel in, Excel out). This is a proof of concept for a class, and possibly a thesis
later with a Coimbra cohort. Answer in English. The user's own guidelines override the Gemini chat.

## Current decisions (all user-confirmed)
- **Safety rule:** PPV ≥ **90 %** and NPV ≥ **90 %**, each proven by a one-sided 95 % Clopper–Pearson
  lower bound on out-of-fold scores (`config.yaml → decision`). It started at 95 %/95 %. The user
  switched to 90 %/90 % because 95 % certified nothing with realistic data and 600 patients.
- **Model variables (10, "compact 10"):** ptau217, clinical_stage (SCD/MCI/Dementia), ab42_ab40_ratio,
  ptau217_ab42_ratio, apoe4, stroke, egfr, triglycerides, hypertension (known/medicated), anemia (WHO, from
  haemoglobin+sex).
- **Template inputs (15 columns):** patient_id, age, sex, egfr, creatinine, triglycerides, hemoglobin,
  ptau217, ab42, ab40, ab42_ab40_ratio, apoe4, hypertension, stroke, clinical_stage, atypical_features
  (red flag), plus lp_result for training.
- **Removed on request:** p-tau181 and GFAP (forced; not measured in the future cohort). NfL, heart rate,
  blood pressures, glucose, Fazekas, MoCA, MTA, BMI, LDL/HDL, diabetes, heart disease, sleep apnoea, weight
  loss and education were removed after the variable analyses and the user's one-by-one choices.
- **Aβ42/Aβ40:** treated as always measured (part of the work-up). **APOE:** usually available.
  **MRI rating availability:** uncertain, so dropped.
- **Red flag:** `atypical_features` = yes → never classified (INCONCLUSIVE). Source: the Italian 2026
  position paper.
- **Default (shipped) model:** `models/default/` (committed) with `manifest.json` (SHA-256 of the dataset).
  Trained on `data/default_training/synthetic_training_dataset.xlsx` (600 grey-zone patients; the user
  rejected 2,500 as unrealistic). `train.py --default` retrains it. The app retrains it automatically if
  it is missing or incompatible.

## Model types (added 2026-11-20)
- **Switch at the top right** of the app: Random Forest (default, unchanged), Logistic Regression,
  Gradient Boosting (HistGB), Extra Trees, SVM (Platt) and Ensemble (RF+LR+GB).
  - `greyzone_rf/estimators.py`; settings in `config.yaml → models:`; `model_types:` lists what the
    switch offers.
  - Same procedure, the same 90/90 rule with 95 % confidence, and the same safeguards for every
    model (`tests/test_models.py`).
- **Shipped models:** `models/default` (RF) and `models/default_<type>`. Each folder has
  `model_info.json`; bundles store `model_type`, `nested_scores` and `nested_decisions`. Older
  bundles load as RF.
- **Compare models tab** (`greyzone_rf/compare.py`): table, paired bootstrap differences, ROC /
  LPs-avoided / calibration figures, and every model on one file.
- **Results (synthetic):**
  - LR is best: nested 59 % of LPs avoided vs RF 38 % (19 vs 17 wrong calls);
  - GB makes the fewest errors;
  - all six meet PPV/NPV ≥ 90 % on 6,000 independent synthetic patients;
  - the generator is log-linear, so it favours LR; redo the ranking on real data.
- Full detail: `docs/MODEL_COMPARISON.md`; reproduce with `tools/benchmark_models.py`.
- **Output column changes:** `AI RF score` → `AI score`, plus `AI model`. The results key
  `rf_score` → `score`.

## Data
- **Hybrid synthetic dataset:**
  - real clinical covariates from the **Cardiovascular Health Study MRI sub-study** (n = 735; rigr /
    CardioDataSets via Rdatasets, vendored in `data/external/`);
  - APOE frequencies from the **Knight ADRC** CSF study;
  - simulated amyloid/LP label and biomarkers, calibrated to published values (p-tau217 AUC 0.95, ratio
    0.97, Aβ42/40 0.72–0.85, +12 % p-tau217 per 10 mL/min lower eGFR, anaemia cut-off ratio 1.40, etc.).
- **Literature inputs** included a user-supplied VeraHealth summary. Its DOIs were not opened (network
  blocks nature.com, springer, PMC and python.org; only GitHub raw, PyPI and NuGet are reachable).
- **Examples:** `examples/` holds the training file, the new-patient file and the output. There is also
  a **test sample** `test_sample_56_patients.xlsx` with an answer key: 50 grey-zone patients plus 6
  special cases. Expected result: 7 POS / 18 NEG / 28 INC / 2 N/A / 1 CHECK DATA.

## Key results (synthetic, default model)
- AUC 0.887 (p-tau217 alone 0.753). Thresholds: POSITIVE ≥ 0.76, NEGATIVE ≤ 0.18.
- **Nested CV:** 38 % of LPs avoided, 17/600 wrong calls (mostly false negatives).
- **6,000 independent synthetic patients:** 53 % avoided, PPV 92.8 % (CI 91.1–94.3), NPV 95.6 %.
- **Why the earlier build looked better:**
  - removing p-tau181/GFAP: LPs avoided 37 % → 16 %;
  - real CHS covariates (older, worse kidney function, more vascular disease, lower grey-zone
    prevalence): 37 % → 16 %;
  - both together: 3 %.
- **Sample size:**
  - fewer than about 300 grey-zone patients gives unstable results; at n = 75 one run had a true NPV
    of 0.84;
  - at 95 %/95 % the realistic model needed 1,500–2,500 patients for rule-out only.
- **Publication view:**
  - feasible if the Coimbra grey zone has ≥ 300–500 patients with LP **and** temporal or external
    validation;
  - must compare against the p-tau217/Aβ42 ratio with two cut-offs and logistic regression;
  - follow TRIPOD+AI;
  - with about 100–150 grey-zone patients → a feasibility/pilot paper.

## Code map
`greyzone_rf/`:
- `config` – config loading; feature types numeric / sex / apoe4 / binary / stage.
- `data` – parsing, plausibility checks, CKD-EPI 2021, anaemia_who, ratios.
- `stats` – Clopper–Pearson and threshold selection.
- `model` – repeated CV, nested CV, joblib parallel.
- `predict` – red flags, missing > 50 % → INC, "your file with predictions added" (AI columns).
- `report`, `template`.
- `synthetic` – generator; `real=True` uses CHS.
- `ablation` – leave-one-out and forward selection.
- `default_model`.

CLIs: `train.py` (`--default`), `predict.py`, `analyze_variables.py`, `make_demo_data.py`
(`--overwrite-default`), `run_app.py` (waits for health, uses 127.0.0.1, free port fallback).

App: `app.py` (Streamlit). There are 27 pytest tests.

## Windows
- **Normal install:** `install.bat` → `run_app.bat`.
- **Portable bundle (works for the user):**
  - built by `tools/build_portable.py`: NuGet Python 3.13.17 + win_amd64 wheels of
    `requirements-pinned.txt`;
  - `START_APP.bat`; zip of about 162 MB;
  - not in git (`dist/` is ignored; over the 100 MB limit). It is built and tested on every push by
    `.github/workflows/portable-windows.yml`; download it from Actions → Artifacts (kept 30 days).
    A GitHub Release is suggested for a permanent link.
- **Open issue last seen:** "Port 8501 is not available" came from the user running the OLD bundle while
  another copy was still open. The new launcher picks the next port. The user should end old python.exe
  processes and use the latest zip.
- **Portuguese version (pt-PT):**
  - `config.yaml → language: pt` (or `GREYZONE_LANG=pt`). Texts are in `greyzone_rf/i18n_pt.py`;
    `tests/test_i18n.py` checks that every text has a translation;
  - the portable bundle is `tools/build_portable.py --lang pt` → `TriagemZonaCinzenta_portatil_win64.zip`
    with `INICIAR_APLICACAO.bat`. CI builds and tests both languages;
  - the long documentation (README, guide) stays in English.
- The GitHub account billing lock was resolved by the user adding a card. The $0 budgets can stay.
