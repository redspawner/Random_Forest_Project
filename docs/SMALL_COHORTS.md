# Few patients: how to "extrapolate a bit" safely

With a small local cohort, two different things limit the tool:

1. **Score quality:** how well the model ranks patients (AUC, calibration). External knowledge can improve
   this.
2. **Evidence for the 90 % / 95 % safety rule:** how many real patients with an LP result fall in each
   decision zone. Nothing can replace these. To prove PPV or NPV ≥ 90 % with 95 % confidence, a zone needs at
   least 29 real calls with 0 errors, 46 with 1 error, 61 with 2, and so on.

**Synthetic or external patients can help with (1). They must never count for (2).** The project is built that
way.

## What is implemented: training-only augmentation with literature-based synthetic patients

Enable it in `config.yaml`:

```yaml
augmentation:
  enabled: true
  file: data/default_training/synthetic_training_dataset.xlsx   # labelled synthetic (or external) patients
  ratio: 5.0                                                     # up to 5 x the number of real patients
```

- Every model fit (cross-validation folds, nested folds, final model) is trained on the real training patients
  **plus** the augmentation patients.
- Cross-validation splits, out-of-fold scores, threshold selection, the Clopper–Pearson proof and the nested
  estimate use the **real patients only**. The report says how many augmentation patients were used.
- `tests/test_explain_dca.py::test_augmentation_is_training_only` checks this.

### Does it help? (experiment on version-2 synthetic data, no Aβ)

Set-up:
- **Real cohort:** n patients from the version-2 generator, which plays the role of reality.
- **Augmentation:** either a *well-matched* prior (version-2 synthetic patients, other seed) or a *mismatched*
  prior (version-1 synthetic patients: older, mostly linear biology).
- **Score quality** measured on 6,000 independent patients; mean of 3 repetitions.

| Real patients | Model | Real only | + mismatched prior ×2 | + matched prior ×2 | + matched prior ×5 |
|---|---|---|---|---|---|
| 100 | Logistic Regression | AUC 0.740, Brier 0.173 | 0.769, 0.162 | 0.780, 0.155 | **0.791, 0.151** |
| 100 | XGBoost | 0.759, 0.164 | 0.764, 0.158 | 0.786, 0.151 | **0.789, 0.149** |
| 200 | Logistic Regression | 0.766, 0.161 | 0.766, 0.165 | 0.789, 0.152 | **0.797, 0.147** |
| 200 | XGBoost | 0.761, 0.161 | 0.760, 0.160 | 0.782, 0.151 | **0.797, 0.145** |
| 300 | Logistic Regression | 0.781, 0.154 | **0.765, 0.163 (worse)** | 0.790, 0.151 | **0.796, 0.147** |
| 300 | XGBoost | 0.780, 0.153 | 0.767, 0.157 (worse) | 0.790, 0.148 | **0.795, 0.145** |

(For comparison, about 0.80 is the ceiling with these variables even with 10,000 real patients.)

What this shows:

- **A good literature prior lets 100–200 real patients reach almost the score quality of 600 or more.**
- **A wrong prior helps a little with very few patients, then hurts** (300 patients: AUC 0.781 → 0.765).
  The prior must be checked against the real data, and the nested estimate (real patients only) does exactly
  that. Keep the augmentation only if it improves the nested result.
- **It does not create evidence.** With 100–300 real patients and these variables, no zone reached the 90 %
  / 95 % proof, with or without augmentation. The decision curves (net benefit) improved a little.

## Other ways to make the most of few patients

| Approach | What it does | Status |
|---|---|---|
| Training-only augmentation (above) | borrows structure from literature or external data | **implemented** |
| Simpler models | Logistic Regression or Spline LR are more stable than boosting with < 200 patients | available (switch) |
| Fewer variables | each extra variable costs data; remove those with no SHAP / permutation effect | `config.yaml` |
| **Model updating / recalibration** | pre-train on a large external or synthetic cohort, then re-estimate only the intercept and slope (2 parameters) on the local data (Steyerberg, *Clinical Prediction Models*, ch. 20) | suggested |
| **Informative (Bayesian) priors** | logistic regression whose coefficients are shrunk towards published effect sizes instead of towards 0 | suggested |
| Pooling with external cohorts | train on ADNI / other memory clinics + local; certify thresholds on local patients only | needs data-use agreements |
| Prospective accumulation | re-train every N new patients; the thresholds become certifiable once enough calls exist | process |

Approaches to avoid:

- **SMOTE / oversampling / jittered copies of real patients.** They add no information, they distort the
  prevalence, and PPV/NPV depend directly on prevalence. Copies of a patient that land in both a training and
  a test fold make the validation optimistic.
- **Relaxing the rule silently**, for example by using the point estimate instead of the confidence bound
  with few patients. If the targets are changed, do it explicitly and before looking at the results.
