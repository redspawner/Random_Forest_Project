# Training report - grey-zone Random Forest

*Trained 2026-11-11T17:19:59* - source: `synthetic_training_dataset.xlsx`

## Cohort
- Rows in file: 600; excluded: 0 without LP result, 0 without p-tau217, 0 outside the grey zone [0.14-0.43 pg/mL].
- **Training patients: 600** (218 LP-positive, 382 LP-negative; prevalence 36.3%).
- Variables used (10): egfr, triglycerides, anemia, ptau217, ab42_ab40_ratio, ptau217_ab42_ratio, apoe4, hypertension, stroke, clinical_stage.

## Discrimination (repeated cross-validation)
- Random Forest AUC: **0.887** (95% CI 0.857-0.915); 5-fold x 5 repeats, AUC per repeat 0.880-0.889.
- p-tau217 alone (inside the grey zone): AUC 0.753 (95% CI 0.712-0.795).

## Decision thresholds used for new patients
Rule: PPV >= 95% for POSITIVE calls and NPV >= 95% for NEGATIVE calls, using the one-sided 95% Clopper-Pearson lower bound >= target.

| Call | Threshold on RF score | Training calls | Correct | Estimate | Lower bound |
|---|---|---|---|---|---|
| POSITIVE | **none could be certified** | - | - | - | - |
| NEGATIVE | **none could be certified** | - | - | - | - |

Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**.

## Honest estimate for NEW patients (nested cross-validation)
The whole procedure (cross-validation, threshold selection, final model) was repeated in 5 outer folds and applied to patients it had never seen:

- **Lumbar punctures avoided (patients resolved): 3.2% (95% CI 1.9%-4.9%; 19/600)**
- PPV of POSITIVE calls: n/a (no calls)
- NPV of NEGATIVE calls: 94.7% (95% CI 74.0%-99.9%; 18/19)
- Wrong calls: 1 (0 false positive, 1 false negative) out of 600 grey-zone patients
- Remaining INCONCLUSIVE (sent to LP): 581
- Thresholds chosen in each outer fold: pos none / neg none; pos none / neg none; pos none / neg 0.05; pos none / neg none; pos none / neg none

## How many patients does the 95% rule need?
To prove PPV/NPV >= 95% with 95% confidence, a threshold must classify at least: 59 patients with 0 error(s), 93 patients with 1 error(s), 124 patients with 2 error(s), 153 patients with 3 error(s).

## Most informative variables (permutation importance)

1. clinical_stage (AUC drop 0.087)
2. ab42_ab40_ratio (AUC drop 0.051)
3. ptau217 (AUC drop 0.032)
4. ptau217_ab42_ratio (AUC drop 0.018)
5. apoe4 (AUC drop 0.012)
6. egfr (AUC drop 0.004)
7. triglycerides (AUC drop 0.004)
8. hypertension (AUC drop 0.002)

## Warnings

- No threshold reached the safety target for POSITIVE (rule-in) calls with the current data: the model will never call a patient POSITIVE. More patients are needed.
- No threshold reached the safety target for NEGATIVE (rule-out) calls with the current data: the model will never call a patient NEGATIVE. More patients are needed.

---
Research prototype - not a medical device. Validate on an independent cohort before any clinical use.