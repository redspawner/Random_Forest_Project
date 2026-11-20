# Training report - grey-zone Logistic Regression

*Trained 2026-11-20T10:25:18* - source: `synthetic_training_dataset.xlsx`

## Cohort
- Rows in file: 600; excluded: 0 without LP result, 0 without p-tau217, 0 outside the grey zone [0.14-0.43 pg/mL].
- **Training patients: 600** (218 LP-positive, 382 LP-negative; prevalence 36.3%).
- Model: **Logistic Regression** (C=0.5, class_weight=None, log_transform=True).
- Variables used (10): egfr, triglycerides, anemia, ptau217, ab42_ab40_ratio, ptau217_ab42_ratio, apoe4, hypertension, stroke, clinical_stage.

## Discrimination (repeated cross-validation)
- Logistic Regression AUC: **0.899** (95% CI 0.871-0.924); 5-fold x 5 repeats, AUC per repeat 0.893-0.901.
- p-tau217 alone (inside the grey zone): AUC 0.753 (95% CI 0.712-0.795).

## Decision thresholds used for new patients
Rule: PPV >= 90% for POSITIVE calls and NPV >= 90% for NEGATIVE calls, using the one-sided 95% Clopper-Pearson lower bound >= target.

| Call | Threshold on score | Training calls | Correct | Estimate | Lower bound |
|---|---|---|---|---|---|
| POSITIVE | >= 0.86 | 89 | 86 | PPV 96.6% | 91.5% |
| NEGATIVE | <= 0.18 | 276 | 258 | NPV 93.5% | 90.5% |

Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**.

## Honest estimate for NEW patients (nested cross-validation)
The whole procedure (cross-validation, threshold selection, final model) was repeated in 5 outer folds and applied to patients it had never seen:

- **Lumbar punctures avoided (patients resolved): 59.2% (95% CI 55.1%-63.1%; 355/600)**
- PPV of POSITIVE calls: 97.6% (95% CI 91.8%-99.7%; 83/85)
- NPV of NEGATIVE calls: 93.7% (95% CI 90.1%-96.3%; 253/270)
- Wrong calls: 19 (2 false positive, 17 false negative) out of 600 grey-zone patients
- Remaining INCONCLUSIVE (sent to LP): 245
- Thresholds chosen in each outer fold: pos 0.87 / neg 0.13; pos 0.85 / neg 0.09; pos 0.93 / neg 0.23; pos 0.88 / neg 0.20; pos 0.87 / neg 0.18

## How many patients does the 95% rule need?
To prove PPV/NPV >= 90% with 95% confidence, a threshold must classify at least: 29 patients with 0 error(s), 46 patients with 1 error(s), 61 patients with 2 error(s), 76 patients with 3 error(s).

## Most informative variables (permutation importance)

1. clinical_stage (AUC drop 0.096)
2. ptau217 (AUC drop 0.071)
3. ab42_ab40_ratio (AUC drop 0.054)
4. apoe4 (AUC drop 0.020)
5. anemia (AUC drop 0.008)
6. egfr (AUC drop 0.004)
7. hypertension (AUC drop 0.004)
8. stroke (AUC drop 0.003)

---
Research prototype - not a medical device. Validate on an independent cohort before any clinical use.