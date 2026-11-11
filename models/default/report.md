# Training report - grey-zone Random Forest

*Trained 2026-11-11T17:47:52* - source: `synthetic_training_dataset.xlsx`

## Cohort
- Rows in file: 600; excluded: 0 without LP result, 0 without p-tau217, 0 outside the grey zone [0.14-0.43 pg/mL].
- **Training patients: 600** (218 LP-positive, 382 LP-negative; prevalence 36.3%).
- Variables used (10): egfr, triglycerides, anemia, ptau217, ab42_ab40_ratio, ptau217_ab42_ratio, apoe4, hypertension, stroke, clinical_stage.

## Discrimination (repeated cross-validation)
- Random Forest AUC: **0.887** (95% CI 0.857-0.915); 5-fold x 5 repeats, AUC per repeat 0.880-0.889.
- p-tau217 alone (inside the grey zone): AUC 0.753 (95% CI 0.712-0.795).

## Decision thresholds used for new patients
Rule: PPV >= 90% for POSITIVE calls and NPV >= 90% for NEGATIVE calls, using the one-sided 95% Clopper-Pearson lower bound >= target.

| Call | Threshold on RF score | Training calls | Correct | Estimate | Lower bound |
|---|---|---|---|---|---|
| POSITIVE | >= 0.76 | 89 | 85 | PPV 95.5% | 90.0% |
| NEGATIVE | <= 0.18 | 236 | 221 | NPV 93.6% | 90.4% |

Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**.

## Honest estimate for NEW patients (nested cross-validation)
The whole procedure (cross-validation, threshold selection, final model) was repeated in 5 outer folds and applied to patients it had never seen:

- **Lumbar punctures avoided (patients resolved): 37.7% (95% CI 33.8%-41.7%; 226/600)**
- PPV of POSITIVE calls: 97.1% (95% CI 85.1%-99.9%; 34/35)
- NPV of NEGATIVE calls: 91.6% (95% CI 86.8%-95.1%; 175/191)
- Wrong calls: 17 (1 false positive, 16 false negative) out of 600 grey-zone patients
- Remaining INCONCLUSIVE (sent to LP): 374
- Thresholds chosen in each outer fold: pos 0.75 / neg none; pos none / neg 0.15; pos none / neg 0.19; pos 0.87 / neg 0.23; pos 0.87 / neg 0.17

## How many patients does the 95% rule need?
To prove PPV/NPV >= 90% with 95% confidence, a threshold must classify at least: 29 patients with 0 error(s), 46 patients with 1 error(s), 61 patients with 2 error(s), 76 patients with 3 error(s).

## Most informative variables (permutation importance)

1. clinical_stage (AUC drop 0.087)
2. ab42_ab40_ratio (AUC drop 0.051)
3. ptau217 (AUC drop 0.032)
4. ptau217_ab42_ratio (AUC drop 0.018)
5. apoe4 (AUC drop 0.012)
6. egfr (AUC drop 0.004)
7. triglycerides (AUC drop 0.004)
8. hypertension (AUC drop 0.002)

---
Research prototype - not a medical device. Validate on an independent cohort before any clinical use.