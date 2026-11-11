# Training report - grey-zone Random Forest

*Trained 2026-11-11T16:28:57* - source: `synthetic_training_dataset.xlsx`

## Cohort
- Rows in file: 600; excluded: 0 without LP result, 0 without p-tau217, 0 outside the grey zone [0.14-0.43 pg/mL].
- **Training patients: 600** (278 LP-positive, 322 LP-negative; prevalence 46.3%).
- Variables used (23): age, sex, education_years, bmi, egfr, triglycerides, hemoglobin, anemia, glucose, ldl, hdl, ptau217, ptau181, ab42, ab40, ab42_ab40_ratio, ptau217_ab42_ratio, gfap, nfl, apoe4, moca, mta_score, fazekas.

## Discrimination (repeated cross-validation)
- Random Forest AUC: **0.934** (95% CI 0.915-0.952); 5-fold x 5 repeats, AUC per repeat 0.929-0.934.
- p-tau217 alone (inside the grey zone): AUC 0.807 (95% CI 0.771-0.842).

## Decision thresholds used for new patients
Rule: PPV >= 95% for POSITIVE calls and NPV >= 95% for NEGATIVE calls, using the one-sided 95% Clopper-Pearson lower bound >= target.

| Call | Threshold on RF score | Training calls | Correct | Estimate | Lower bound |
|---|---|---|---|---|---|
| POSITIVE | >= 0.78 | 112 | 111 | PPV 99.1% | 95.8% |
| NEGATIVE | <= 0.25 | 187 | 183 | NPV 97.9% | 95.2% |

Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**.

## Honest estimate for NEW patients (nested cross-validation)
The whole procedure (cross-validation, threshold selection, final model) was repeated in 5 outer folds and applied to patients it had never seen:

- **Lumbar punctures avoided (patients resolved): 37.8% (95% CI 33.9%-41.8%; 227/600)**
- PPV of POSITIVE calls: 94.4% (95% CI 87.4%-98.2%; 84/89)
- NPV of NEGATIVE calls: 97.1% (95% CI 92.7%-99.2%; 134/138)
- Wrong calls: 9 (5 false positive, 4 false negative) out of 600 grey-zone patients
- Remaining INCONCLUSIVE (sent to LP): 373
- Thresholds chosen in each outer fold: pos 0.75 / neg 0.22; pos none / neg none; pos none / neg 0.28; pos 0.71 / neg 0.23; pos 0.74 / neg 0.25

## How many patients does the 95% rule need?
To prove PPV/NPV >= 95% with 95% confidence, a threshold must classify at least: 59 patients with 0 error(s), 93 patients with 1 error(s), 124 patients with 2 error(s), 153 patients with 3 error(s).

## Most informative variables (permutation importance)

1. ptau217_ab42_ratio (AUC drop 0.042)
2. ptau217 (AUC drop 0.028)
3. ptau181 (AUC drop 0.020)
4. egfr (AUC drop 0.020)
5. ab42_ab40_ratio (AUC drop 0.017)
6. apoe4 (AUC drop 0.015)
7. gfap (AUC drop 0.015)
8. moca (AUC drop 0.014)

---
Research prototype - not a medical device. Validate on an independent cohort before any clinical use.