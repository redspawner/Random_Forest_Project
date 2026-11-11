# Training report - grey-zone Random Forest

*Trained 2026-11-11T16:51:24* - source: `synthetic_training_dataset.xlsx`

## Cohort
- Rows in file: 600; excluded: 0 without LP result, 0 without p-tau217, 0 outside the grey zone [0.14-0.43 pg/mL].
- **Training patients: 600** (244 LP-positive, 356 LP-negative; prevalence 40.7%).
- Variables used (25): age, sex, education_years, bmi, egfr, triglycerides, hemoglobin, anemia, ldl, hdl, ptau217, ptau181, ab42_ab40_ratio, ptau217_ab42_ratio, gfap, apoe4, hypertension, diabetes, stroke, cardiovascular_disease, sleep_apnea, weight_loss, clinical_stage, moca, mta_score.

## Discrimination (repeated cross-validation)
- Random Forest AUC: **0.950** (95% CI 0.934-0.965); 5-fold x 5 repeats, AUC per repeat 0.946-0.952.
- p-tau217 alone (inside the grey zone): AUC 0.774 (95% CI 0.733-0.811).

## Decision thresholds used for new patients
Rule: PPV >= 95% for POSITIVE calls and NPV >= 95% for NEGATIVE calls, using the one-sided 95% Clopper-Pearson lower bound >= target.

| Call | Threshold on RF score | Training calls | Correct | Estimate | Lower bound |
|---|---|---|---|---|---|
| POSITIVE | >= 0.82 | 66 | 66 | PPV 100.0% | 95.6% |
| NEGATIVE | <= 0.25 | 234 | 228 | NPV 97.4% | 95.0% |

Everything between the two thresholds is **INCONCLUSIVE -> lumbar puncture**.

## Honest estimate for NEW patients (nested cross-validation)
The whole procedure (cross-validation, threshold selection, final model) was repeated in 5 outer folds and applied to patients it had never seen:

- **Lumbar punctures avoided (patients resolved): 34.2% (95% CI 30.4%-38.1%; 205/600)**
- PPV of POSITIVE calls: n/a (no calls)
- NPV of NEGATIVE calls: 97.6% (95% CI 94.4%-99.2%; 200/205)
- Wrong calls: 5 (0 false positive, 5 false negative) out of 600 grey-zone patients
- Remaining INCONCLUSIVE (sent to LP): 395
- Thresholds chosen in each outer fold: pos none / neg 0.25; pos none / neg 0.22; pos none / neg 0.26; pos none / neg 0.22; pos none / neg 0.18

## How many patients does the 95% rule need?
To prove PPV/NPV >= 95% with 95% confidence, a threshold must classify at least: 59 patients with 0 error(s), 93 patients with 1 error(s), 124 patients with 2 error(s), 153 patients with 3 error(s).

## Most informative variables (permutation importance)

1. ptau217_ab42_ratio (AUC drop 0.035)
2. ptau181 (AUC drop 0.031)
3. ab42_ab40_ratio (AUC drop 0.030)
4. clinical_stage (AUC drop 0.021)
5. egfr (AUC drop 0.017)
6. gfap (AUC drop 0.017)
7. ptau217 (AUC drop 0.014)
8. moca (AUC drop 0.005)

---
Research prototype - not a medical device. Validate on an independent cohort before any clinical use.