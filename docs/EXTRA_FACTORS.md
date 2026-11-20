# Extra routine factors, SMOTE and other improvements (version-3 synthetic data)

All results come from **synthetic patients** (generator version 3 = the default version-2 biology plus the
factors below). A factor can only help here as much as the assumed effect size allows, so treat the tables as
"what to expect *if* the literature effect sizes are right". Re-run them on the Coimbra data. Reproduce:
the scripts in this document's "How to reproduce" section.

## The factors (screenshot from the Gemini research + routine memory-clinic data)

| Factor | Effect on plasma p-tau217 in the simulation | Evidence | Routinely available? |
|---|---|---|---|
| Kidney function (eGFR) | rises below eGFR ~70, steeply below 45 (hinge); **slightly lower above 90 (hyperfiltration)** | strong for CKD (Mielke 2022, Pichet Binette 2023, JAMA Neurol 2026); hyperfiltration weak | yes (creatinine) |
| BMI | about 2 % lower per kg/m² (haemodilution); underweight raises | moderate (JAMA Neurol 2026, Martino-Adami 2026) | yes (weight/height) |
| Anaemia | +25 % (cut-off ratio about 1.4) | moderate (JAMA Neurol 2026) | yes (blood count) |
| Age | +0.7 % per year independently of amyloid | moderate | yes |
| Stroke / cardiovascular events (MI, heart failure) | +10 % | moderate (Mielke 2022) | yes |
| **Thyroid disease** (hypo/hyper, levothyroxine) and **TSH** | +10 % with thyroid disease (assumed) | **weak / inconsistent** | yes: TSH is part of the standard dementia blood screen |
| Obstructive sleep apnoea | −13 % (more false negatives) | limited (Shir 2026) | often known |
| Triglycerides | modest inverse association (−8 % per log unit) | weak | yes (lipid panel) |
| **MRI MTA** (Scheltens 0–4) | not a p-tau217 confounder: higher with age, clinical stage and tau in amyloid-positive patients | strong for AD-type neurodegeneration (Wahlund 2017, Persson 2017) | **sometimes** (rating present in about 1/3–1/2) |
| MRI Fazekas (0–3) | vascular burden (age, hypertension, diabetes, stroke); no direct amyloid effect | strong for vascular disease | sometimes |
| **MMSE** (0–30) | by stage; about 1 point lower in amyloid-positive patients with tau | moderate (ADNI-type differences) | **yes, at every memory-clinic visit** |

The thyroid, sleep-apnoea, triglyceride and hyperfiltration effect sizes are **assumptions**: their direction
comes from the literature summary, their size does not. The library in `data/synthetic/training_sets/` has a
weak-evidence (×0.5) and a strong-evidence (×1.5) version so you can see how much this matters.

RESULTS_PLACEHOLDER
