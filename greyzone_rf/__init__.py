"""Grey-zone plasma p-tau217 triage with a Random Forest (teaching prototype).

Modules
-------
config     load/validate config.yaml
data       read and check Excel/CSV patient files
stats      Clopper-Pearson bounds, safe threshold selection, triage metrics
model      cross-validation, threshold selection, nested validation, save/load
predict    apply a trained model to new patients
report     training report (Markdown, figures, Excel)
template   Excel template generation
synthetic  artificial memory-clinic cohort for testing
"""

__version__ = "0.1.0"
