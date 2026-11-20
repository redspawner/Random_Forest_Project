# Training report - grey-zone Support Vector Machine

*Trained 2026-11-20T10:25:56* - source: `synthetic_training_dataset.xlsx`

## Cohort
- Rows in file: 600; excluded: 0 without LP result, 0 without p-tau217, 0 outside the grey zone [0.14-0.43 pg/mL].
- **Training patients: 600** (218 LP-positive, 382 LP-negative; prevalence 36.3%).
- Model: **Support Vector Machine** (C=0.5, gamma=scale, class_weight=None, log_transform=True).
- Variables used (10): egfr, triglycerides, anemia, ptau217, ab42_ab40_ratio, ptau217_ab42_ratio, apoe4, hypertension, stroke, clinical_stage.

## Discrimination (repeated cross-validation)
- Support Vector Machine AUC: **0.881** (95% CI 0.851-0.908); 5-fold x 5 repeats, AUC per repeat 0.875-0.884.
- p-tau217 alone (inside the grey zone): AUC 0.753 (95% CI 0.712-0.795).

## Decision thresholds used for new patients
Rule: PPV >= 90% for POSITIVE calls and NPV >= 90% for NEGATIVE calls, using the one-sided 95% Clopper-Pearson lower bound >= target.

| Call | Threshold on score | Training calls | Correct | Estimate | Lower bound |
|---|---|---|---|---|---|
| POSITIVE | >= 0.85 | 78 | 75 | PPV 96.2% | 90.4% |
| NEGATIVE | <= 0.18 | 251 | 234 | NPV 93.2% | 90.0% |

Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**.

## Honest estimate for NEW patients (nested cross-validation)
The whole procedure (cross-validation, threshold selection, final model) was repeated in 5 outer folds and applied to patients it had never seen:

- **Lumbar punctures avoided (patients resolved): 53.3% (95% CI 49.3%-57.4%; 320/600)**
- PPV of POSITIVE calls: 98.5% (95% CI 91.8%-100.0%; 65/66)
- NPV of NEGATIVE calls: 92.9% (95% CI 89.0%-95.7%; 236/254)
- Wrong calls: 19 (1 false positive, 18 false negative) out of 600 grey-zone patients
- Remaining INCONCLUSIVE (sent to LP): 280
- Thresholds chosen in each outer fold: pos 0.90 / neg 0.14; pos 0.83 / neg 0.16; pos 0.95 / neg 0.18; pos 0.86 / neg 0.23; pos 0.90 / neg 0.17

## How many patients does the 95% rule need?
To prove PPV/NPV >= 90% with 95% confidence, a threshold must classify at least: 29 patients with 0 error(s), 46 patients with 1 error(s), 61 patients with 2 error(s), 76 patients with 3 error(s).

## Most informative variables (permutation importance)

1. clinical_stage (AUC drop 0.095)
2. ab42_ab40_ratio (AUC drop 0.042)
3. ptau217 (AUC drop 0.030)
4. ptau217_ab42_ratio (AUC drop 0.018)
5. apoe4 (AUC drop 0.016)
6. anemia (AUC drop 0.008)
7. stroke (AUC drop 0.008)
8. triglycerides (AUC drop 0.003)

---
Research prototype - not a medical device. Validate on an independent cohort before any clinical use.