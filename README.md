# Grey-zone p-tau217 triage with a Random Forest

A teaching proof of concept that uses machine learning to resolve **plasma p-tau217 grey-zone**
results in memory-clinic patients without a lumbar puncture (LP), **when it can be done
safely**.

```
                         Stage 1 (already in use)
 plasma p-tau217  ─────────────────────────────────────────────────────────────
   < 0.14 pg/mL   → NEGATIVE           (model not applied)
   > 0.43 pg/mL   → POSITIVE           (model not applied)
   0.14 – 0.43    → GREY ZONE ──► Stage 2: Random Forest on blood + clinical + MRI variables
                                       │
                                       ├─ score ≥ T_pos → POSITIVE   (PPV ≥ 95 %, proven with 95 % confidence)
                                       ├─ score ≤ T_neg → NEGATIVE   (NPV ≥ 95 %, proven with 95 % confidence)
                                       └─ otherwise     → INCONCLUSIVE → lumbar puncture (as before)
```

The LP result is the label used to train the model. Everything else (age, sex, eGFR, BMI,
triglycerides, p-tau217, p-tau181, Aβ42, Aβ40, GFAP, NfL, APOE, MoCA, MRI MTA and Fazekas
scores, and any variable you add) is a feature.

> **Research prototype, not a medical device.** Every number shown by the demo comes from
> **synthetic (artificial) patients**. Before any clinical use, the procedure must be validated
> on a real, independent cohort and approved by the ethics committee and regulators.

---

## 1. Installation

You need Python 3.10 or newer ([python.org](https://www.python.org/downloads/); on Windows, tick
*"Add Python to PATH"* when installing).

**Windows:** double-click `install.bat`, then `run_app.bat`.
The install scripts create a private environment (`.venv`), install the libraries, generate the
synthetic demo files, and train a demo model, so the app is ready the first time it opens.

**macOS / Linux:**

```bash
./install.sh
```

```bash
./run_app.sh
```

Manual installation (any system):

```bash
python -m venv .venv
```

```bash
.venv/bin/python -m pip install -r requirements.txt
```

(On Windows the interpreter is `.venv\Scripts\python`.)

Libraries installed (`requirements.txt`): numpy, pandas, scipy, **scikit-learn ≥ 1.4** (Random
Forest with native missing-value handling), joblib, openpyxl (Excel), pyyaml (configuration),
matplotlib (figures), **streamlit** (drag-and-drop interface), jinja2, pytest (tests).

## 2. Quick start with the synthetic demo

If you used the install scripts, run the commands below with the environment's Python:
`.venv\Scripts\python` on Windows, `.venv/bin/python` on macOS/Linux (e.g.
`.venv/bin/python train.py ...`). You can do everything from the app instead.

```bash
python make_demo_data.py
```

This creates the Excel template and three **synthetic** files in `data/synthetic/`. Next, train the model:

```bash
python train.py data/synthetic/synthetic_training_cohort.xlsx
```

Then open the drag-and-drop interface:

```bash
python run_app.py
```

The browser opens at <http://localhost:8501>. The app has four tabs:

| Tab | What it does |
|---|---|
| **Classify new patients** | Drag and drop an Excel/CSV file → each patient gets POSITIVE / NEGATIVE / INCONCLUSIVE - refer to LP, with the reason. Download the results as Excel. |
| **Train model** | Drag and drop a training file with LP results → trains, validates and saves a new model. |
| **Model report** | Cohort, AUC, chosen thresholds, honest (nested) estimate of LPs avoided and errors, figures. |
| **Template & help** | Download the Excel template and the demo files, see the data dictionary. |

You can also predict without the app:

```bash
python predict.py data/synthetic/synthetic_new_patients.xlsx
```

Everything runs **locally**. Files are processed in memory, the app only listens on `localhost`,
and Streamlit telemetry is switched off in `.streamlit/config.toml`.

## 3. Input file (Excel)

Download `templates/patient_data_template.xlsx` (or use the button in the app). Each patient goes on one row of the sheet
**Patients**:

| column | unit | notes |
|---|---|---|
| `patient_id` | text | pseudonymised ID only |
| `age` | years | |
| `sex` | M / F | |
| `education_years` | years | |
| `bmi` | kg/m² | |
| `egfr` | mL/min/1.73 m² | if blank, computed from `creatinine` (CKD-EPI 2021) |
| `creatinine` | mg/dL | only used to compute eGFR |
| `triglycerides` | mg/dL | |
| `ptau217` | pg/mL | **required**; defines the grey zone |
| `ptau181`, `ab42`, `ab40`, `gfap`, `nfl` | pg/mL | |
| `ab42_ab40_ratio` | ratio | if blank, computed from ab42/ab40 (`ptau217/ab42` is also computed) |
| `apoe4` | 0/1/2 or `E3/E4` | number of ε4 alleles |
| `moca` | 0–30 | |
| `mta_score` | 0–4 | Scheltens MTA, worse side |
| `fazekas` | 0–3 | |
| `lp_result` | Positive / Negative | **training file only** (leave blank or delete for new patients) |

The reader is forgiving and records every correction in the output:

- Header case does not matter, and units in brackets are ignored. Aliases are accepted (`p-Tau217 (pg/mL)`, `Idade`, `Sexo`, `IMC`, …).
- Decimal commas are accepted (`0,25`). Censored values such as `<0.03` are used as 0.03 and noted.
- A blank cell is a missing value. The Random Forest handles missing values natively (scikit-learn ≥ 1.4), without imputation.
- Implausible values (e.g. MoCA = 34, eGFR = 900) are **never silently changed**. When classifying, that patient gets **CHECK DATA** and is not classified. During training, the value is treated as missing and a warning is shown.
- Patients with p-tau217 outside the grey zone get **NOT APPLICABLE**, together with their Stage-1 result. The model was trained only on grey-zone patients, so it must not extrapolate.
- Patients missing more than 50 % of the model variables stay **INCONCLUSIVE**.
- Columns that are not defined in `config.yaml` are ignored and listed. This applies to any column, so a hospital record number can never become a model variable by accident.

**Adding a new variable** (e.g. homocysteine) needs no code. Add a block under `features:` in
`config.yaml` (name, unit, plausible min/max), add the column to the Excel file, and retrain.

## 4. How the "95 % confidence" decision works

The Random Forest (500 trees, ≥ 3 patients per leaf) turns each patient's variables into a
score between 0 and 1. The score alone is not a guarantee, so the thresholds are chosen
statistically:

1. **Out-of-fold scores.** Repeated stratified 5-fold cross-validation (5 × 5) gives every
   training patient a score from models that never saw that patient.
2. **Rule-in threshold `T_pos`.** This is the lowest score such that the PPV of all patients
   at or above it is at least 95 %. By default, the **one-sided 95 % Clopper–Pearson lower bound**
   of that PPV must reach 95 %, not just the observed percentage.
3. **Rule-out threshold `T_neg`.** The same rule, with NPV, for patients at or below it.
4. **Everything in between is INCONCLUSIVE → LP.** If no threshold reaches the target, the
   model never makes that call. With small cohorts this is the expected, safe behavior.
5. The final model is trained on all patients. New patients are classified with that model and
   the thresholds above.

All of these settings are in `config.yaml` (`decision:`): the targets, the confidence level, and
`use_confidence_bound: false` for an exploratory mode that uses point estimates only.

### Honest validation (nested cross-validation)

The thresholds are chosen on the same patients they are evaluated on, so the PPV/NPV at the
chosen thresholds are optimistic by construction. The training report therefore also runs
**nested cross-validation**. The whole procedure (inner CV, threshold selection, final model) is
repeated in 5 outer folds and applied to the held-out patients. This answers the questions that
matter: *what fraction of grey-zone patients would avoid an LP, and how often would the tool be
wrong?* On the synthetic demo cohort (600 patients):

| | in-sample (optimistic) | nested CV (honest) |
|---|---|---|
| patients resolved (LPs avoided) | 47 % | **31 %** |
| PPV of POSITIVE calls | 98 % | 97 % (57/59) |
| NPV of NEGATIVE calls | 100 % | 98 % (126/129) |

## 5. How many patients do you need?

This is the most important practical point. To *prove* PPV ≥ 95 % with 95 % confidence, a
threshold must classify at least:

| wrong calls among them | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| patients classified on that side | **59** | 93 | 124 | 153 | 181 | 208 |

I simulated this with the synthetic generator: train on *n* grey-zone patients, then check the
chosen thresholds on 6,000 independent synthetic patients.

| training grey-zone patients | share resolved without LP | true PPV / NPV of the calls |
|---|---|---|
| 150 | **0 %** (no threshold could be certified) | – |
| 500 | 21 – 41 % | ≥ 96 % in every run |
| 1000 | 39 – 64 % | ≥ 96 % in every run |

The synthetic data are easier than reality, so real numbers will be lower. **The lesson holds
anyway: with ~100 grey-zone patients the safe answer is "inconclusive for everyone".** The
statistics need several hundred grey-zone patients with LP before the tool can safely spare a
meaningful share of LPs. That is a strong argument for a multicenter or prospective design, and a
useful result to show in class.

## 6. Review of the Gemini suggestions

I kept the overall architecture: a Stage-2 reflex model on top of the existing p-tau217 cut-offs,
de-confounding variables (eGFR, BMI, triglycerides), stratified CV, and native missing-value
handling. I changed the following:

| Suggestion | What I did and why |
|---|---|
| Inductive conformal prediction with α = 0.05 "guarantees 95 %" / "zero clinical risk" | **Changed.** Standard conformal prediction guarantees *marginal* coverage. Inconclusive patients receive the set {Positive, Negative}, which always counts as "covered", so the error rate among patients who receive a single answer can be well above 5 %. Your requirement is about the patient who receives an answer, i.e. PPV/NPV. That is what this code controls, with an explicit confidence bound and an honest nested-CV check. No method gives zero risk. |
| 60–120 grey-zone patients are "completely viable" | **Corrected.** That is enough to estimate an AUC, but not to certify 95 % PPV/NPV (see §5). |
| Reported PPV/NPV at the chosen thresholds | **Added nested CV**, because thresholds selected and evaluated on the same data are optimistic. |
| 5 fold models: average them or retrain on 100 % | **Retrain on 100 %.** Thresholds come from out-of-fold scores. |
| "Trees discover interactions" | True, but with a few hundred patients a forest finds only strong interactions. Ratios that matter biologically (Aβ42/40, p-tau217/Aβ42) are therefore computed explicitly. |
| XGBoost handles missing values, RF does not | scikit-learn's Random Forest also routes missing values natively (since 1.4), so no imputation is needed. |
| MoCA may bias against pre-clinical patients | **Valid concern, kept as optional.** Because the label is the LP (biology), MoCA does not exclude anyone directly. But if A+ patients with normal MoCA are rare in training, the model can learn "high MoCA → negative". Before trusting NEGATIVE calls, check NPV in the high-MoCA / SCD subgroup (the training-predictions Excel file makes this easy), or retrain without `moca`. |
| ±14–30 day window between routine labs and plasma | Good data-curation rule. Apply it when building the spreadsheet. |
| Specific literature figures, the GRAD paper versions, "90–95 % probability of publication" | **Not verified.** Language models can produce confident but wrong citations and numbers. Check every reference and number in the primary source before citing it. |

## 7. Project structure

```
config.yaml              all settings: grey zone, 95 % targets, RF parameters, variable list
app.py                   drag-and-drop interface (Streamlit)
run_app.py / .bat / .sh  start the interface
train.py                 command-line training  → models/<name>/
predict.py               command-line prediction → <file>_results.xlsx
make_demo_data.py        template + synthetic demo files
install.bat / .sh        one-click installation
greyzone_rf/
  config.py              configuration loading/validation
  data.py                Excel/CSV reading, checks, eGFR (CKD-EPI 2021), ratios
  stats.py               Clopper–Pearson bounds, threshold selection, triage metrics
  model.py               cross-validation, thresholds, nested validation, save/load
  predict.py             classification of new patients, results Excel
  report.py              training report and figures
  template.py            Excel template
  synthetic.py           synthetic memory-clinic cohort (testing only)
templates/               Excel template
data/synthetic/          synthetic demo files (real data in data/ are git-ignored)
models/                  trained models (git-ignored)
tests/                   pytest suite:  python -m pytest
```

A trained model folder contains `model.joblib`, `report.md`, `report.json`, the figures, and
`training_predictions.xlsx` (the out-of-fold score and decision of every training patient, useful
for subgroup analyses). A model stores a copy of the configuration it was trained with, so later
edits to `config.yaml` do not change existing models. Only load `model.joblib` files you created
yourself, because pickle files can execute code.

## 8. Limitations and next steps (thesis)

- Validate on an **independent cohort** (temporal or external). Nested CV is internal validation only.
- PPV/NPV depend on the **prevalence in the grey zone**. If the referral population changes, re-check them.
- Next steps from the Gemini discussion: compare against L2-logistic regression and XGBoost on
  the same folds, add SHAP explanations per patient, and add decision-curve analysis.
- Optional variant: control sensitivity/specificity instead of PPV/NPV (the dual-cut-off convention of some papers).
- Pre-analytical factors (time to centrifugation, freeze–thaw cycles, assay lot) can be added as variables or used as exclusion criteria.
