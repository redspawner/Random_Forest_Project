# Model comparison: Random Forest vs Logistic Regression, Gradient Boosting and others

The app has a **model switch at the top right** and a **Compare models** tab. Every model type goes
through exactly the same procedure as the original Random Forest:

- repeated stratified cross-validation (5 folds × 5 repeats; same random splits for every model);
- the safety rule: POSITIVE only where **PPV ≥ 90 %** and NEGATIVE only where **NPV ≥ 90 %**, each
  **proven with a one-sided 95 % Clopper–Pearson lower bound**, with at least 10 calls per side;
  everyone else is INCONCLUSIVE → lumbar puncture;
- nested cross-validation (5 outer folds) for an honest estimate on patients never used to build
  or tune the model;
- the same safeguards for new patients: CHECK DATA (implausible values), NOT APPLICABLE (outside
  the grey zone), red flag → INCONCLUSIVE, more than 50 % of the variables missing → INCONCLUSIVE,
  and a note when a value lies outside the training range.

`tests/test_models.py` checks all of this for every model type.

All numbers below come from **synthetic data** (`data/default_training/`, 600 grey-zone patients).
They show that the pipeline works and how the models behave; they are not evidence of clinical
performance. Reproduce them with `python tools/benchmark_models.py --external 6000`.

## The models

| Model | What it is | Missing values | Settings (config.yaml) |
|---|---|---|---|
| Random Forest | 500 bagged decision trees (unchanged) | native | min_samples_leaf 3, max_features sqrt |
| Logistic Regression | linear model on log-transformed skewed lab values, standardised | median + "was missing" indicator | C = 0.5 (L2) |
| Gradient Boosting | scikit-learn HistGradientBoosting, many small trees in sequence | native | learning rate 0.03, 150 rounds, 4 leaves, ≥ 20 patients per leaf, L2 1.0 |
| Extra Trees | 500 extremely randomised trees | native | min_samples_leaf 3, max_features sqrt |
| Support Vector Machine | RBF kernel, Platt-scaled (5-fold) to a 0–1 score | median + indicator | C = 0.5 |
| Ensemble | average of the Random Forest, Logistic Regression and Gradient Boosting scores | per member | — |

## Final results (shipped models)

"Nested" = honest estimate on the 600 training patients. "Ext." = the trained model applied to
**6,000 new independent synthetic patients** from the same generator (another random seed). The
external check measures the true PPV/NPV directly, so it tests whether the 90 % guarantee really
holds.

| Model | AUC (CV) | POS ≥ | NEG ≤ | LPs avoided (nested) | Wrong (nested, of 600) | PPV / NPV (nested) | LPs avoided (ext.) | PPV ext. (95 % CI) | NPV ext. (95 % CI) | Wrong per 1000 (ext.) |
|---|---|---|---|---|---|---|---|---|---|---|
| Random Forest | 0.887 | 0.76 | 0.18 | 37.7 % | 17 | 97.1 % / 91.6 % | 51.3 % | 92.8 % (91.0–94.3) | 95.7 % (94.7–96.5) | 27 |
| **Logistic Regression** | **0.899** | 0.86 | 0.18 | **59.2 %** | 19 | 97.6 % / 93.7 % | **58.8 %** | 95.2 % (93.6–96.4) | 95.9 % (95.0–96.6) | 26 |
| Gradient Boosting | 0.883 | 0.88 | 0.19 | 39.7 % | 17 | 94.1 % / 92.8 % | 46.7 % | **98.4 %** (96.8–99.3) | 95.3 % (94.4–96.2) | **19** |
| Extra Trees | 0.894 | 0.72 | 0.24 | 59.7 % | 22 | 97.0 % / 92.7 % | 57.8 % | 91.9 % (90.1–93.5) | 94.7 % (93.7–95.5) | 36 |
| Support Vector Machine | 0.881 | 0.85 | 0.18 | 53.3 % | 19 | 98.5 % / 92.9 % | 54.4 % | 93.1 % (91.2–94.6) | 95.2 % (94.3–96.0) | 29 |
| Ensemble (RF + LR + GB) | 0.895 | 0.76 | 0.18 | 51.8 % | 22 | 97.8 % / 92.1 % | 57.0 % | 93.1 % (91.5–94.5) | **96.1 %** (95.2–96.8) | 28 |

p-tau217 alone inside the grey zone: AUC 0.753.

**Every shipped model meets the 90 % PPV and 90 % NPV target on the 6,000 independent patients,
including the lower end of the 95 % confidence interval.**

### Paired comparison with the Random Forest (same patients, same folds; bootstrap 95 % CI)

| Model | AUC difference | LPs avoided difference (nested) | Wrong-call difference |
|---|---|---|---|
| Logistic Regression | +0.013 (+0.001 to +0.025) | **+21.5 % (+17.5 to +25.7)** | +2 (−5 to +9) |
| Gradient Boosting | −0.004 (−0.012 to +0.003) | +2.0 % (−1.2 to +5.2) | 0 (−5 to +5) |
| Extra Trees | +0.007 (−0.003 to +0.017) | +22.0 % (+18.5 to +25.7) | +5 (0 to +11) |
| Support Vector Machine | −0.006 (−0.019 to +0.008) | +15.7 % (+12.0 to +19.3) | +2 (−4 to +8) |
| Ensemble | +0.008 (+0.002 to +0.014) | +14.2 % (+11.0 to +17.2) | +5 (−1 to +11) |

### Test sample (`examples/test_sample_56_patients.xlsx`)

| Model | POSITIVE | NEGATIVE | INCONCLUSIVE | NOT APPLICABLE | CHECK DATA | Definite answers correct |
|---|---|---|---|---|---|---|
| Random Forest | 7 | 18 | 28 | 2 | 1 | 23/25 |
| Logistic Regression | 7 | 25 | 21 | 2 | 1 | 30/32 |
| Gradient Boosting | 2 | 20 | 31 | 2 | 1 | 20/22 |
| Extra Trees | 7 | 21 | 25 | 2 | 1 | 26/28 |
| Support Vector Machine | 10 | 21 | 22 | 2 | 1 | 29/31 |
| Ensemble | 10 | 20 | 23 | 2 | 1 | 27/30 |

## Interpretation

- **Logistic Regression is the best overall here.** It avoids about 59 % of grey-zone lumbar
  punctures against 38 % for the Random Forest (nested), a difference that is statistically clear,
  with no significant increase in wrong calls. On the independent patients it has the highest AUC
  and the best PPV/NPV balance.
- **Gradient Boosting is the most cautious.** It makes the fewest errors (19 per 1000, PPV 98 %),
  but it answers fewer patients (47 %).
- **Extra Trees and the Ensemble** avoid many LPs, but they make more wrong calls. Extra Trees has
  the lowest external PPV (91.9 %), still above 90 %.
- **The AUCs are all within about 0.02 of each other.** The large differences in LPs avoided come
  from how many patients end up in the zones where the 90 %/95 % rule is proven, not from the
  ranking. This is why the comparison page ranks models by LPs avoided and wrong calls, not by
  AUC.
- **Why Logistic Regression wins on this data, and a caution:** the synthetic generator builds the
  LP result from mostly additive, log-linear effects (log p-tau217, Aβ42/40 ratio, APOE, stage,
  eGFR). That favours a logistic model. Real data can contain interactions and non-linear effects
  that favour the tree models. **The ranking must be redone on the Coimbra cohort**: train every
  model type at once and use the Compare models tab.

## How the settings were chosen

Each candidate went through the full procedure, including nested validation. A few standard,
conservative settings were tried per model; the round-1 and round-2 results are below. The
selection favoured settings that keep the nested PPV and NPV above 90 %, not only the largest
share of LPs avoided. The final check on 6,000 independent patients was run once, after the
choice.

| Candidate | AUC | LPs avoided (nested) | Wrong | PPV / NPV (nested) |
|---|---|---|---|---|
| LR C = 0.1 / 0.2 / 0.5 / 2 (log) | 0.899–0.900 | 58–60 % | 19–22 | 97–98 % / 93–94 % |
| LR C = 0.5 without log | 0.899 | 58 % | 18 | 100 % / 93.6 % |
| GB lr 0.05, 150 rounds, 8 leaves | 0.880 | 23 % | 15 | 92 % / **88 %** |
| GB lr 0.05, 300 rounds, 8 leaves | 0.874 | 22 % | 14 | 95 % / **87 %** |
| **GB lr 0.03, 150 rounds, 4 leaves** (chosen) | 0.883 | 40 % | 17 | 94 % / 93 % |
| GB stumps (2 leaves) | 0.880–0.885 | 35–39 % | 15–18 | no POSITIVE calls |
| ET leaf 5, 50 % of variables | 0.888 | 54 % | 19 | 98 % / 93 % |
| **ET leaf 3, sqrt** (chosen) | 0.894 | 60 % | 22 | 97 % / 93 % |
| ET leaf 10, all variables | 0.878 | 33 % | 11 | 98 % / 93 % |
| **SVM C = 0.5** (chosen) / C = 2 | 0.881 / 0.874 | 53 % / 45 % | 19 / 20 | 98 % / 93 % · 95 % / 92 % |
| Ensemble LR + RF | 0.898 | 59 % | 23 | 97 % / 93 % |
| **Ensemble RF + LR + GB** (chosen) | 0.895 | 52 % | 22 | 98 % / 92 % |

Lessons from the tuning:

- **More flexible gradient boosting over-fits:** larger trees or more rounds pushed its nested NPV
  below 90 % (87–88 %). The threshold rule protects the training data, but an over-confident model
  can still miss the target on new patients. Small, slowly learning trees fixed this.
- **Logistic Regression is insensitive to its setting:** any C between 0.1 and 2 gives the same
  result.

## Limitations of this comparison

- Synthetic data only, from a generator that favours additive effects (see above).
- Choosing settings and then the best model on the same 600 patients is slightly optimistic. The
  independent test reduces this concern but uses the same generator.
- With few POSITIVE calls (Gradient Boosting), the PPV confidence interval is wide.
- The SVM and Logistic Regression replace missing values by the median plus a missing indicator.
  If values are missing for clinical reasons in the real cohort, this behaves differently from the
  tree models.

## Possible upgrades

- **SHAP explanations per patient**: which variables pushed this patient's score up or down. This
  needs the `shap` package.
- **Calibration of the final score** (isotonic or Platt), so the score can be read as a
  probability. Thresholds would not change, since they use only the order of the scores.
- **Decision-curve analysis** (net benefit), a standard figure for diagnostic models in TRIPOD+AI
  papers.
- **XGBoost / LightGBM**: usually similar to HistGradientBoosting on data of this size; they add
  dependencies to the portable bundle.
- Comparison with the **p-tau217/Aβ42 ratio with two cut-offs** as a simple non-ML benchmark.
