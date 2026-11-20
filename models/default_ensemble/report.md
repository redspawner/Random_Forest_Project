# Training report - grey-zone Ensemble (RF + LR + GB)

*Trained 2026-11-20T10:26:30* - source: `synthetic_training_dataset.xlsx`

## Cohort
- Rows in file: 600; excluded: 0 without LP result, 0 without p-tau217, 0 outside the grey zone [0.14-0.43 pg/mL].
- **Training patients: 600** (218 LP-positive, 382 LP-negative; prevalence 36.3%).
- Model: **Ensemble (RF + LR + GB)** (members=['random_forest', 'logistic_regression', 'gradient_boosting']).
- Variables used (10): egfr, triglycerides, anemia, ptau217, ab42_ab40_ratio, ptau217_ab42_ratio, apoe4, hypertension, stroke, clinical_stage.

## Discrimination (repeated cross-validation)
- Ensemble (RF + LR + GB) AUC: **0.895** (95% CI 0.866-0.922); 5-fold x 5 repeats, AUC per repeat 0.890-0.896.
- p-tau217 alone (inside the grey zone): AUC 0.753 (95% CI 0.712-0.795).

## Decision thresholds used for new patients
Rule: PPV >= 90% for POSITIVE calls and NPV >= 90% for NEGATIVE calls, using the one-sided 95% Clopper-Pearson lower bound >= target.

| Call | Threshold on score | Training calls | Correct | Estimate | Lower bound |
|---|---|---|---|---|---|
| POSITIVE | >= 0.76 | 99 | 95 | PPV 96.0% | 91.0% |
| NEGATIVE | <= 0.18 | 257 | 241 | NPV 93.8% | 90.7% |

Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**.

## Honest estimate for NEW patients (nested cross-validation)
The whole procedure (cross-validation, threshold selection, final model) was repeated in 5 outer folds and applied to patients it had never seen:

- **Lumbar punctures avoided (patients resolved): 51.8% (95% CI 47.8%-55.9%; 311/600)**
- PPV of POSITIVE calls: 97.8% (95% CI 88.2%-99.9%; 44/45)
- NPV of NEGATIVE calls: 92.1% (95% CI 88.2%-95.0%; 245/266)
- Wrong calls: 22 (1 false positive, 21 false negative) out of 600 grey-zone patients
- Remaining INCONCLUSIVE (sent to LP): 289
- Thresholds chosen in each outer fold: pos 0.84 / neg 0.17; pos 0.83 / neg 0.17; pos none / neg 0.17; pos 0.88 / neg 0.24; pos 0.91 / neg 0.17

## How many patients does the 95% rule need?
To prove PPV/NPV >= 90% with 95% confidence, a threshold must classify at least: 29 patients with 0 error(s), 46 patients with 1 error(s), 61 patients with 2 error(s), 76 patients with 3 error(s).

## Most informative variables (permutation importance)

1. clinical_stage (AUC drop 0.095)
2. ab42_ab40_ratio (AUC drop 0.053)
3. ptau217 (AUC drop 0.045)
4. apoe4 (AUC drop 0.017)
5. ptau217_ab42_ratio (AUC drop 0.006)
6. anemia (AUC drop 0.006)
7. egfr (AUC drop 0.004)
8. triglycerides (AUC drop 0.004)

---
Research prototype - not a medical device. Validate on an independent cohort before any clinical use.