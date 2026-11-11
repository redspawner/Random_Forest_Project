# Training report - grey-zone Random Forest

*Trained 2026-11-11T15:29:24* - source: `synthetic_training_dataset.xlsx`

## Cohort
- Rows in file: 600; excluded: 0 without LP result, 0 without p-tau217, 0 outside the grey zone [0.14-0.43 pg/mL].
- **Training patients: 600** (293 LP-positive, 307 LP-negative; prevalence 48.8%).
- Variables used (18): age, sex, education_years, bmi, egfr, triglycerides, ptau217, ptau181, ab42, ab40, ab42_ab40_ratio, ptau217_ab42_ratio, gfap, nfl, apoe4, moca, mta_score, fazekas.

## Discrimination (repeated cross-validation)
- Random Forest AUC: **0.944** (95% CI 0.925-0.961); 5-fold x 5 repeats, AUC per repeat 0.936-0.946.
- p-tau217 alone (inside the grey zone): AUC 0.806 (95% CI 0.769-0.839).

## Decision thresholds used for new patients
Rule: PPV >= 95% for POSITIVE calls and NPV >= 95% for NEGATIVE calls, using the one-sided 95% Clopper-Pearson lower bound >= target.

| Call | Threshold on RF score | Training calls | Correct | Estimate | Lower bound |
|---|---|---|---|---|---|
| POSITIVE | >= 0.76 | 158 | 155 | PPV 98.1% | 95.2% |
| NEGATIVE | <= 0.20 | 141 | 139 | NPV 98.6% | 95.6% |

Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**.

## Honest estimate for NEW patients (nested cross-validation)
The whole procedure (cross-validation, threshold selection, final model) was repeated in 5 outer folds and applied to patients it had never seen:

- **Lumbar punctures avoided (patients resolved): 42.8% (95% CI 38.8%-46.9%; 257/600)**
- PPV of POSITIVE calls: 97.0% (95% CI 92.4%-99.2%; 128/132)
- NPV of NEGATIVE calls: 99.2% (95% CI 95.6%-100.0%; 124/125)
- Wrong calls: 5 (4 false positive, 1 false negative) out of 600 grey-zone patients
- Remaining INCONCLUSIVE (sent to LP): 343
- Thresholds chosen in each outer fold: pos 0.80 / neg 0.16; pos 0.79 / neg 0.17; pos 0.75 / neg 0.15; pos 0.79 / neg 0.17; pos 0.87 / neg 0.19

## How many patients does the 95% rule need?
To prove PPV/NPV >= 95% with 95% confidence, a threshold must classify at least: 59 patients with 0 error(s), 93 patients with 1 error(s), 124 patients with 2 error(s), 153 patients with 3 error(s).

## Most informative variables (permutation importance)

1. ptau181 (AUC drop 0.036)
2. ptau217 (AUC drop 0.035)
3. ptau217_ab42_ratio (AUC drop 0.031)
4. gfap (AUC drop 0.027)
5. egfr (AUC drop 0.018)
6. ab42_ab40_ratio (AUC drop 0.018)
7. moca (AUC drop 0.012)
8. apoe4 (AUC drop 0.008)

---
Research prototype - not a medical device. Validate on an independent cohort before any clinical use.