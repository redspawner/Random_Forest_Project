# data/

* `synthetic/` - artificial patients created by `make_demo_data.py` (safe to share, **not real data**).
* Put real cohort files in another sub-folder of `data/` (e.g. `data/real/`). Everything in `data/`
  except `synthetic/` is excluded from git by `.gitignore`, so patient data cannot be committed by accident.
  Use pseudonymised identifiers only.
