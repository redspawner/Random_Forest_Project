# Training report - grey-zone Extra Trees

*Trained 2026-11-20T10:25:49* - source: `synthetic_training_dataset.xlsx`

## Cohort
- Rows in file: 600; excluded: 0 without LP result, 0 without p-tau217, 0 outside the grey zone [0.14-0.43 pg/mL].
- **Training patients: 600** (218 LP-positive, 382 LP-negative; prevalence 36.3%).
- Model: **Extra Trees** (n_estimators=500, min_samples_leaf=3, max_features=sqrt, class_weight=None).
- Variables used (10): egfr, triglycerides, anemia, ptau217, ab42_ab40_ratio, ptau217_ab42_ratio, apoe4, hypertension, stroke, clinical_stage.

## Discrimination (repeated cross-validation)
- Extra Trees AUC: **0.894** (95% CI 0.866-0.921); 5-fold x 5 repeats, AUC per repeat 0.886-0.897.
- p-tau217 alone (inside the grey zone): AUC 0.753 (95% CI 0.712-0.795).

## Decision thresholds used for new patients
Rule: PPV >= 90% for POSITIVE calls and NPV >= 90% for NEGATIVE calls, using the one-sided 95% Clopper-Pearson lower bound >= target.

| Call | Threshold on score | Training calls | Correct | Estimate | Lower bound |
|---|---|---|---|---|---|
| POSITIVE | >= 0.72 | 99 | 95 | PPV 96.0% | 91.0% |
| NEGATIVE | <= 0.24 | 262 | 245 | NPV 93.5% | 90.4% |

Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**.

## Honest estimate for NEW patients (nested cross-validation)
The whole procedure (cross-validation, threshold selection, final model) was repeated in 5 outer folds and applied to patients it had never seen:

- **Lumbar punctures avoided (patients resolved): 59.7% (95% CI 55.6%-63.6%; 358/600)**
- PPV of POSITIVE calls: 97.0% (95% CI 91.4%-99.4%; 96/99)
- NPV of NEGATIVE calls: 92.7% (95% CI 88.8%-95.5%; 240/259)
- Wrong calls: 22 (3 false positive, 19 false negative) out of 600 grey-zone patients
- Remaining INCONCLUSIVE (sent to LP): 242
- Thresholds chosen in each outer fold: pos 0.70 / neg 0.19; pos 0.73 / neg 0.19; pos 0.73 / neg 0.25; pos 0.72 / neg 0.25; pos 0.72 / neg 0.26

## How many patients does the 95% rule need?
To prove PPV/NPV >= 90% with 95% confidence, a threshold must classify at least: 29 patients with 0 error(s), 46 patients with 1 error(s), 61 patients with 2 error(s), 76 patients with 3 error(s).

## Most informative variables (permutation importance)

1. clinical_stage (AUC drop 0.137)
2. ptau217 (AUC drop 0.034)
3. apoe4 (AUC drop 0.023)
4. ab42_ab40_ratio (AUC drop 0.023)
5. ptau217_ab42_ratio (AUC drop 0.016)
6. anemia (AUC drop 0.005)
7. stroke (AUC drop 0.005)
8. hypertension (AUC drop 0.004)

---
Research prototype - not a medical device. Validate on an independent cohort before any clinical use.