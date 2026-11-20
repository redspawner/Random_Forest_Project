# Training report - grey-zone Support Vector Machine

*Trained 2026-11-20T11:57:08* - source: `synthetic_training_dataset.xlsx`

## Cohort
- Rows in file: 600; excluded: 0 without LP result, 0 without p-tau217, 0 outside the grey zone [0.14-0.43 pg/mL].
- **Training patients: 600** (188 LP-positive, 412 LP-negative; prevalence 31.3%).
- Model: **Support Vector Machine** (C=0.5, gamma=scale, class_weight=None, log_transform=True).
- Variables used (10): egfr, triglycerides, anemia, ptau217, apoe4, hypertension, stroke, clinical_stage, bmi, sleep_apnea.

## Discrimination (repeated cross-validation)
- Support Vector Machine AUC: **0.788** (95% CI 0.747-0.831); 5-fold x 5 repeats, AUC per repeat 0.779-0.792.
- p-tau217 alone (inside the grey zone): AUC 0.771 (95% CI 0.725-0.818).

## Decision thresholds used for new patients
Rule: PPV >= 90% for POSITIVE calls and NPV >= 90% for NEGATIVE calls, using the one-sided 95% Clopper-Pearson lower bound >= target.

| Call | Threshold on score | Training calls | Correct | Estimate | Lower bound |
|---|---|---|---|---|---|
| POSITIVE | **none could be certified** | - | - | - | - |
| NEGATIVE | **none could be certified** | - | - | - | - |

Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**.

## Honest estimate for NEW patients (nested cross-validation)
The whole procedure (cross-validation, threshold selection, final model) was repeated in 5 outer folds and applied to patients it had never seen:

- **Lumbar punctures avoided (patients resolved): 0.0% (95% CI 0.0%-0.6%; 0/600)**
- PPV of POSITIVE calls: n/a (no calls)
- NPV of NEGATIVE calls: n/a (no calls)
- Wrong calls: 0 (0 false positive, 0 false negative) out of 600 grey-zone patients
- Remaining INCONCLUSIVE (sent to LP): 600
- Thresholds chosen in each outer fold: pos none / neg none; pos none / neg none; pos none / neg none; pos none / neg none; pos none / neg none

## How many patients does the 95% rule need?
To prove PPV/NPV >= 90% with 95% confidence, a threshold must classify at least: 29 patients with 0 error(s), 46 patients with 1 error(s), 61 patients with 2 error(s), 76 patients with 3 error(s).

## Most informative variables (permutation importance)

1. ptau217 (AUC drop 0.205)
2. egfr (AUC drop 0.027)
3. bmi (AUC drop 0.021)
4. sleep_apnea (AUC drop 0.011)
5. anemia (AUC drop 0.011)
6. triglycerides (AUC drop 0.010)
7. apoe4 (AUC drop 0.002)
8. hypertension (AUC drop 0.001)

## Warnings

- No threshold reached the safety target for POSITIVE (rule-in) calls with the current data: the model will never call a patient POSITIVE. More patients are needed.
- No threshold reached the safety target for NEGATIVE (rule-out) calls with the current data: the model will never call a patient NEGATIVE. More patients are needed.

---
Research prototype - not a medical device. Validate on an independent cohort before any clinical use.