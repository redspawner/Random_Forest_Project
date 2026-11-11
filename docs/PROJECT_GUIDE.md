# Project guide - what was built, step by step, and why

This guide walks through the whole project in the order it was built. Each step says **what**
was done, **why**, and **where** it is in the code. It is meant to help you present the project
and later turn it into a thesis method section. For how to *use* the tool, see the README.

---

## Step 0 - The clinical question

Memory-clinic patients have plasma p-tau217 measured (Lumipulse). The centre already applies
two cut-offs:

- p-tau217 < 0.14 pg/mL → negative; > 0.43 pg/mL → positive;
- between them → **grey zone** → lumbar puncture (LP), whose CSF result is the reference.

**Goal:** for grey-zone patients, use the other information available **before** the LP (blood
tests, clinical data, MRI) to give a definite answer to part of them, so they can avoid the LP.

**Hard constraint:** an answer may only be given with at least **95 % confidence**. Everyone
else stays inconclusive and has the LP, exactly as today.

This translates into a **supervised binary classification** problem:

- one row per grey-zone patient;
- features = pre-LP variables;
- label = LP result (Positive/Negative);
- a three-way output: POSITIVE / NEGATIVE / INCONCLUSIVE.

## Step 1 - Choice of method: Random Forest

- **What:** scikit-learn's `RandomForestClassifier` with 500 trees, at least 3 patients per leaf,
  and √(number of variables) variables tried per split.
- **Why a Random Forest:**
  - It works well on small tabular clinical datasets with little tuning.
  - It captures non-linear effects and interactions without having to specify them, e.g. "a
    raised p-tau217 means less when eGFR is low".
  - It is robust to outliers and handles missing values natively (scikit-learn ≥ 1.4), so no
    imputation is needed.
  - This project is a proof of concept for a class; XGBoost, logistic regression and SHAP are
    the next step (README §9).
- **Settings:** the values are standard conservative defaults and were **not tuned**. Tuning on
  synthetic data would be meaningless, and tuning on real data must be done inside nested
  cross-validation (README §9).
- **Where:** `greyzone_rf/model.py` (`build_forest`), `config.yaml` (`random_forest:`).

## Step 2 - Configuration file instead of hard-coded choices

- **What:** every clinical or statistical choice lives in `config.yaml`: the grey-zone cut-offs,
  the 95 % targets, the confidence level, the validation scheme, the forest settings, the list of
  variables with units and plausible ranges, and the default model.
- **Why:**
  - You can change the cut-offs or add a variable (e.g. cystatin C) without touching Python.
  - Every model stores a copy of the configuration it was trained with, so results stay
    reproducible.
- **Where:** `config.yaml`, `greyzone_rf/config.py` (loads and validates it, e.g. that
  `ptau217` exists and that targets are between 0.5 and 1).

## Step 3 - Reading and checking the Excel file

- **What:** `greyzone_rf/data.py` reads `.xlsx` and `.csv` files (sheet "Patients", one row per
  patient). It then:
  1. **matches columns by name**, ignoring case, units in brackets and accents, and accepting
     aliases (`Idade`, `Sexo`, `p-Tau217 (pg/mL)`). Column order does not matter.
  2. **parses values:** decimal commas (`0,25`); censored values (`<0.03`, used as 0.03 and noted);
     M/F; APOE genotypes (`E3/E4` → 1 allele); Positive/Negative in English or Portuguese.
  3. **checks plausibility** against the min/max in `config.yaml`. Impossible values are never
     silently corrected: when classifying, the patient gets **CHECK DATA**; when training, the
     value is treated as missing and reported.
  4. **computes derived variables:** eGFR from creatinine with the 2021 CKD-EPI equation (only
     if age and sex are known), the Aβ42/40 ratio and the p-tau217/Aβ42 ratio.
  5. **ignores unknown columns** and lists them. This prevents, for example, a record number
     from becoming a model variable.
- **Why:** real hospital spreadsheets are messy, and a clinical tool must fail loudly, not
  silently.
- **Where:** `greyzone_rf/data.py`; tests in `tests/test_data.py`.

## Step 4 - Training only on grey-zone patients

- **What:** rows without an LP result, without p-tau217, or with p-tau217 outside 0.14–0.43 are
  excluded from training, and the exclusions are counted in the report.
- **Why:**
  - The model is meant to answer one question: "for this grey-zone patient, what will the LP
    show?"
  - Patients outside the zone are already resolved by Stage 1. Including them would make the
    model look better than it is on the hard cases.
  - For the same reason, new patients outside the grey zone get **NOT APPLICABLE**, because the
    model must not extrapolate.
- **Where:** `model.py` (`_select_training_rows`), `predict.py`.

## Step 5 - Out-of-fold scores (repeated cross-validation)

- **What:** the data are split into 5 stratified folds, 5 times with different random splits.
  Every patient receives a score from forests that **never saw that patient**. The 5 scores per
  patient are averaged.
- **Why:**
  - A forest's score on its own training patients is far too optimistic.
  - "Stratified" keeps the positive/negative proportion equal in every fold.
  - Repeating the split makes the scores stable.
- **Where:** `model.py` (`out_of_fold_scores`). Fits run in parallel on all CPU cores.

## Step 6 - The 95 % rule: choosing the two thresholds

- **What:** on the out-of-fold scores, the tool searches thresholds from 0.50 to 1.00 for
  rule-in, and from 0.00 to 0.50 for rule-out:
  - **T_pos** = the lowest score such that, among training patients scoring ≥ T_pos, the PPV
    (fraction truly LP-positive) is ≥ 95 %.
  - **T_neg** = the highest score such that, among patients scoring ≤ T_neg, the NPV is ≥ 95 %.
  - By default it is not enough for the *observed* PPV/NPV to reach 95 %. The **one-sided 95 %
    Clopper–Pearson lower confidence bound** must reach 95 %, which means "95 % PPV, demonstrated
    with 95 % statistical confidence".
  - If no threshold qualifies, that side is switched off: the model never calls anyone
    POSITIVE (or NEGATIVE).
- **Why this rule:** "95 % confidence" for the patient means *if the tool says positive, it is
  right at least 95 % of the time*. That is PPV (and NPV for negatives).
- **Why not Gemini's conformal prediction:** standard conformal prediction guarantees 95 %
  coverage over *all* patients. Inconclusive patients count as covered, so the patients who do
  get an answer can be wrong more than 5 % of the time.
- **Why the lower bound:** with few patients, an observed 100 % PPV (e.g. 10/10) is weak
  evidence. The bound requires at least 59 correct calls with no error, or 93 with one error,
  before it accepts a threshold.
- **Where:** `greyzone_rf/stats.py` (`cp_lower_bound`, `select_threshold`,
  `minimum_calls_needed`); tests in `tests/test_stats.py`.

## Step 7 - The final model

- **What:** after the thresholds are chosen, one forest is trained on **all** training patients.
  New patients are scored with it and compared with T_pos/T_neg.
- **Why:** the final model learns from 100 % of the data. Gemini's alternative, averaging the 5
  fold models, is also valid, but this approach is simpler and standard.
- **Where:** `model.py` (`fit_procedure`).

## Step 8 - Honest validation: nested cross-validation

- **What:** the whole procedure of steps 5–7 (inner CV, threshold choice, final model) is
  repeated inside 5 outer folds. Each time it is applied to the outer patients it never saw. The
  report shows, with exact 95 % confidence intervals:
  - % of patients resolved, which is the share of LPs avoided;
  - real PPV and NPV;
  - number of wrong calls;
  - the thresholds chosen in each fold.
- **Why:** thresholds chosen on a dataset look perfect on that same dataset. Only patients
  outside the procedure give an honest estimate. On the default synthetic data:

  | | Optimistic, same patients | Nested CV, unseen patients |
  |---|---|---|
  | Patients resolved | 50 % | 38 % |
  | PPV of POSITIVE calls | 99 % | 94 % (84/89) |
  | Wrong calls | – | 9 of 600 |

  The honest PPV (94 %) is slightly *below* the 95 % target. Its confidence interval (87–98 %) still
  includes 95 %, but this is exactly why the honest estimate must be reported, not the in-sample one.

- **Where:** `model.py` (`nested_evaluation`).

## Step 9 - Classifying new patients (with safety checks)

Each new patient goes through these checks in order (`greyzone_rf/predict.py`):

1. An implausible or invalid value → **CHECK DATA** (not classified).
2. p-tau217 outside the grey zone → **NOT APPLICABLE**, with the Stage-1 result.
3. More than 50 % of the variables missing → **INCONCLUSIVE** (insufficient data).
4. Otherwise: score ≥ T_pos → **POSITIVE**; score ≤ T_neg → **NEGATIVE**; else
   **INCONCLUSIVE – refer to LP**.

Every patient gets a one-line explanation (score, threshold, demonstrated PPV/NPV), the list of
missing variables, and notes, for example "eGFR computed from creatinine" or "value outside the
range seen in training".

## Step 10 - Outputs

- **Training report** (`report.py`): `report.md`, `report.json`, four figures, and
  `training_predictions.xlsx` with every training patient's out-of-fold score and decision.
  - **Score distribution:** scores by LP result, with the three zones.
  - **ROC curve:** the model vs p-tau217 alone.
  - **Safety curves:** how the thresholds were chosen.
  - **Permutation importance:** the drop in AUC when each variable is shuffled.
- **Results report:** a separate Excel with results, summary and input.
- **Your file with predictions added:** the uploaded workbook unchanged, plus five `AI ...`
  columns after the last used column and a sheet "AI prediction info". Re-annotating overwrites
  these columns instead of duplicating them.

## Step 11 - The drag-and-drop app

- **What:** a Streamlit web app (`app.py`) that runs locally on your computer. It has four tabs:
  - **Classify new patients:** drop a file, see colored decisions, download.
  - **Train model:** drop a training file and train a new model.
  - **Model report.**
  - **Template & help.**
- **Privacy:** it listens only on `localhost`, telemetry is off, and files are processed in
  memory.
- **Launch:** `install.bat` / `install.sh` once, then `run_app.bat` / `run_app.sh`.
- **Command-line equivalents:** `train.py`, `predict.py`.

## Step 12 - Synthetic data calibrated to the literature

- **What:** `greyzone_rf/synthetic.py` simulates a memory-clinic population with a causal
  structure:
  1. APOE ε4 and age → amyloid status (the LP label) and a latent tau burden;
  2. those → plasma p-tau217, p-tau181, Aβ42/40, GFAP, NfL, MoCA, MTA;
  3. kidney function (eGFR), BMI and triglycerides **distort** the plasma levels. This is the
     peripheral confounding that the model can learn to correct.

  Grey-zone patients are then selected with the 0.14/0.43 cut-offs, and realistic missing values
  are added.
- **Calibration:** the parameters were tuned so that the simulated population reproduces
  published values. The table, sources and assumptions are in
  `data/default_training/DATASET_CARD.md`:

  | Quantity | Published | Simulated |
  |---|---|---|
  | p-tau217 AUC vs CSF | 0.95 | 0.954 |
  | p-tau217/Aβ42 ratio AUC | 0.97 | 0.962 |
  | Aβ42/40 AUC | 0.72–0.85 | 0.79 |
  | Grey-zone fraction | 15–30 % | 32 % |
  | p-tau217 increase per 10 mL/min lower eGFR | +12 % | +12 % |
  | Age share of NfL variance | 26 % | 27 % |
  | Age share of GFAP variance | 12 % | 12 % |
  | p-tau217 ratio, anaemic vs not | 1.40 | 1.42 |

- **Honesty note:** these are synthetic patients, and the simulation is cleaner than reality.
  The model's AUC of 0.93 in the grey zone is higher than the 0.75–0.88 reported for real
  gray-zone models, so real performance will be lower. ADNI is the real dataset to request next.

## Step 12b - Routine blood-panel variables

- **What:** haemoglobin (with a computed WHO anaemia flag), fasting glucose, LDL and HDL were added
  to `config.yaml`, the template and the synthetic generator. All come from a standard blood count
  and routine biochemistry.
- **Why:** anaemia and kidney function raise plasma p-tau217 without more brain amyloid (JAMA
  Neurology 2026). Diabetes and lipids mark vascular and metabolic causes of cognitive decline.
- **What it changed:**
  - In the simulation, glucose, LDL and HDL were given no effect on p-tau217, because the
    published evidence is mixed or null. They therefore carry no information, and their
    permutation importance is about 0.
  - Haemoglobin carries a small amount of information.
  - With 23 instead of 18 variables, the honest share of LPs avoided went from 43 % to 38 %, and
    the honest PPV from 97 % to 94 %. Part of this is a different random sample. Part is that
    uninformative variables add noise.
- **Lesson:** add a variable only if it is likely to carry information. With real data, check its
  permutation importance and the nested results with and without it.

## Step 13 - Sample-size experiments

I trained the procedure on synthetic cohorts of different sizes, then checked the chosen
thresholds on 6,000 independent synthetic patients:

| Grey-zone patients in training | LPs avoided | True PPV/NPV of the calls |
|---|---|---|
| 150 | 0 % (nothing could be proven) | – |
| 300 | 0–31 % | ≥ 97 % |
| 500 | 21–41 % | ≥ 96 % |
| 1,000 | 39–64 % | ≥ 96 % |

Without p-tau181, Aβ42/40, GFAP and NfL, only 0–29 % were resolved even with 1,000 patients.
The most valuable extra marker is plasma **Aβ42/40**. The conclusion: the safety rule always
held, but it needs **several hundred grey-zone patients with LP** before it can spare a
meaningful share of LPs.

## Step 14 - The default, pre-trained model and its preserved dataset

- **What:**
  - The dataset the shipped model is trained on is kept as a file:
    `data/default_training/synthetic_training_dataset.xlsx`, described in `DATASET_CARD.md`.
  - The trained model is committed in `models/default/`, with a `manifest.json` that records
    the dataset's SHA-256 fingerprint.
  - The app selects this model automatically, re-trains it if it is missing or incompatible
    (fixed seeds give an identical model), and warns if the dataset file changes.
- **Why:**
  - It is always clear which data produced the model you present.
  - Moving to real life is one change: point `default_model.training_file` to the real cohort,
    run `python train.py --default`, and ship `models/default/`.
- **Where:** `config.yaml` (`default_model:`), `greyzone_rf/default_model.py`,
  `train.py --default`, `tests/test_default_model.py`; README §3, including the data-protection
  rules for real data.

## Step 15 - Quality assurance

- **25 automated tests** (`python -m pytest`) cover:
  - the statistics, e.g. the rule-of-three value 59;
  - file parsing (decimal commas, aliases, semicolon CSVs, impossible values, eGFR);
  - the full train→predict pipeline;
  - the Excel annotation (blank rows, extra sheets, unnamed columns, re-uploads);
  - the consistency of the default model with its dataset.
- The app was driven in a real (headless) browser for each tab: upload, training, download, and
  automatic re-training.
- A fresh installation from `requirements.txt` was tested end to end.

## Step 16 - What remains for the thesis

1. Get real data: your centre's cohort, and/or ADNI under its data-use agreement.
2. Compare Random Forest vs L2-logistic regression vs XGBoost on the same nested folds.
3. Add SHAP per-patient explanations and decision-curve analysis.
4. Run subgroup checks, e.g. NPV in patients with normal MoCA, CKD, or high BMI.
5. Validate externally on a cohort from a different time or centre before any clinical use.
