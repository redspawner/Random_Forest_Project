# Example files (SYNTHETIC patients - not real data)

| File | Use |
|---|---|
| `example_1_training_file.xlsx` | **Training**: 600 grey-zone patients with all variables **and** `lp_result` (Positive/Negative). Drop it in the *Train model* tab, or run `python train.py examples/example_1_training_file.xlsx`. |
| `example_2_new_patients_file.xlsx` | **Classifying a sample**: 43 new patients **without** `lp_result`. 40 are in the grey zone, plus 3 test rows: `NEW-LOW` (p-tau217 below the grey zone), `NEW-HIGH` (above it) and `NEW-TYPO` (MoCA = 34, an impossible value). Drop it in the *Classify new patients* tab. |
| `example_3_output_with_predictions.xlsx` | **Output**: file 2 returned by *Download my file with the predictions added*, with the columns `AI decision`, `AI RF score`, `AI explanation`, `AI missing variables`, `AI notes` and the sheet `AI prediction info`. |

The true LP results of the new patients are in `data/synthetic/synthetic_new_patients_answer_key.xlsx`.
