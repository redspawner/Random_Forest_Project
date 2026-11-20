# Example files (SYNTHETIC patients - not real data)

| File | Use |
|---|---|
| `example_1_training_file.xlsx` | **Training** (identical to the default dataset `data/default_training/synthetic_training_dataset.xlsx`): 600 grey-zone patients with all variables **and** `lp_result` (Positive/Negative). Drop it in the *Train model* tab, or run `python train.py examples/example_1_training_file.xlsx`. |
| `example_2_new_patients_file.xlsx` | **Classifying a sample**: 43 new patients **without** `lp_result`. 40 are in the grey zone, plus 3 test rows: `NEW-LOW` (p-tau217 below the grey zone), `NEW-HIGH` (above it) and `NEW-TYPO` (haemoglobin = 45 g/dL, an impossible value). Drop it in the *Classify new patients* tab. |
| `example_3_output_with_predictions.xlsx` | **Output**: file 2 returned by *Download my file with the predictions added*, with the columns `AI decision`, `AI model`, `AI score`, `AI explanation`, `AI missing variables`, `AI notes` and the sheet `AI prediction info`. |

The true LP results of the new patients are in `data/synthetic/synthetic_new_patients_answer_key.xlsx`.

## Test sample (current 13-column format, no Aβ)

| File | Use |
|---|---|
| `test_sample_56_patients.xlsx` | **New patients to classify**: 50 grey-zone patients plus 6 special cases. Drop it in *Classify new patients*. |
| `test_sample_56_patients_answer_key.xlsx` | Their true LP results (sheet *LP results*) and what each special case tests (sheet *Special cases*). |

Special cases and the expected decision:

| patient_id | Tests | Expected |
|---|---|---|
| TEST-LOW | p-tau217 below 0.14 | NOT APPLICABLE (Stage-1 negative) |
| TEST-HIGH | p-tau217 above 0.43 | NOT APPLICABLE (Stage-1 positive) |
| TEST-TYPO | eGFR = 950 (impossible) | CHECK DATA |
| TEST-REDFLAG | atypical_features = 1 | INCONCLUSIVE (red flag) |
| TEST-MISSING | 80 % of variables blank | INCONCLUSIVE (insufficient data) |
| TEST-COMMA | p-tau217 written as `0,2xx` | read correctly and classified |

Expected result with the default model (realistic version-2 data, no Aβ, strict 90 %/90 % rule):
0 POSITIVE, 0 NEGATIVE, 53 INCONCLUSIVE, 2 NOT APPLICABLE, 1 CHECK DATA. With these variables and 600 training
patients no threshold can be certified, so every grey-zone patient goes to LP (see docs/MODEL_COMPARISON.md). The
safety checks still behave as listed above, and the scores and SHAP explanations show what the model learnt.
