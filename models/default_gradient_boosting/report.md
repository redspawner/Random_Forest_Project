# Training report - grey-zone Gradient Boosting

*Trained 2026-11-20T10:25:24* - source: `synthetic_training_dataset.xlsx`

## Cohort
- Rows in file: 600; excluded: 0 without LP result, 0 without p-tau217, 0 outside the grey zone [0.14-0.43 pg/mL].
- **Training patients: 600** (218 LP-positive, 382 LP-negative; prevalence 36.3%).
- Model: **Gradient Boosting** (learning_rate=0.03, max_iter=150, max_leaf_nodes=4, min_samples_leaf=20, l2_regularization=1.0, class_weight=None).
- Variables used (10): egfr, triglycerides, anemia, ptau217, ab42_ab40_ratio, ptau217_ab42_ratio, apoe4, hypertension, stroke, clinical_stage.

## Discrimination (repeated cross-validation)
- Gradient Boosting AUC: **0.883** (95% CI 0.853-0.912); 5-fold x 5 repeats, AUC per repeat 0.873-0.885.
- p-tau217 alone (inside the grey zone): AUC 0.753 (95% CI 0.712-0.795).

## Decision thresholds used for new patients
Rule: PPV >= 90% for POSITIVE calls and NPV >= 90% for NEGATIVE calls, using the one-sided 95% Clopper-Pearson lower bound >= target.

| Call | Threshold on score | Training calls | Correct | Estimate | Lower bound |
|---|---|---|---|---|---|
| POSITIVE | >= 0.88 | 36 | 36 | PPV 100.0% | 92.0% |
| NEGATIVE | <= 0.19 | 256 | 239 | NPV 93.4% | 90.2% |

Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**.

## Honest estimate for NEW patients (nested cross-validation)
The whole procedure (cross-validation, threshold selection, final model) was repeated in 5 outer folds and applied to patients it had never seen:

- **Lumbar punctures avoided (patients resolved): 39.7% (95% CI 35.7%-43.7%; 238/600)**
- PPV of POSITIVE calls: 94.1% (95% CI 71.3%-99.9%; 16/17)
- NPV of NEGATIVE calls: 92.8% (95% CI 88.5%-95.8%; 205/221)
- Wrong calls: 17 (1 false positive, 16 false negative) out of 600 grey-zone patients
- Remaining INCONCLUSIVE (sent to LP): 362
- Thresholds chosen in each outer fold: pos 0.84 / neg 0.13; pos none / neg 0.13; pos none / neg 0.13; pos none / neg 0.20; pos none / neg 0.16

## How many patients does the 95% rule need?
To prove PPV/NPV >= 90% with 95% confidence, a threshold must classify at least: 29 patients with 0 error(s), 46 patients with 1 error(s), 61 patients with 2 error(s), 76 patients with 3 error(s).

## Most informative variables (permutation importance)

1. clinical_stage (AUC drop 0.099)
2. ab42_ab40_ratio (AUC drop 0.052)
3. ptau217 (AUC drop 0.034)
4. apoe4 (AUC drop 0.018)
5. ptau217_ab42_ratio (AUC drop 0.009)
6. anemia (AUC drop 0.002)
7. stroke (AUC drop 0.002)
8. hypertension (AUC drop -0.000)

---
Research prototype - not a medical device. Validate on an independent cohort before any clinical use.