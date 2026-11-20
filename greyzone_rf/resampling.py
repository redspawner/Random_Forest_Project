"""Training-set resampling (SMOTE, random oversampling, noise jitter) - for testing, OFF by default.

``config.yaml -> resampling: {method: none | smote | random_oversample | noise, ratio: 1.0, k: 5}``

Applied ONLY to the training part of every fit (cross-validation folds, nested folds, final model).
Test folds, out-of-fold scores, thresholds and the PPV/NPV proof always use the real, unresampled
patients, so resampling cannot inflate the safety evidence. docs/EXTRA_FACTORS.md reports whether it
helps here.

* ``random_oversample``: duplicate LP-positive (minority) patients until ``ratio`` x balance.
* ``smote``: SMOTE (Chawla 2002) for mixed data. A new minority patient lies on the line between a
  minority patient and one of its ``k`` nearest minority neighbours (continuous variables). Categorical
  and binary variables (3 or fewer distinct values) are copied from one of the two parents, and a value
  missing in the base patient stays missing.
* ``noise``: one jittered copy of every patient (continuous variables + 10 % of their SD).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

METHODS = ("none", "smote", "random_oversample", "noise")


def _categorical(X: pd.DataFrame) -> list[str]:
    return [c for c in X.columns if X[c].dropna().nunique() <= 3]


def resample(X: pd.DataFrame, y: np.ndarray, cfg: dict, seed: int) -> tuple[pd.DataFrame, np.ndarray]:
    section = cfg.get("resampling") or {}
    method = section.get("method", "none") or "none"
    if method == "none":
        return X, y
    if method not in METHODS:
        raise ValueError(f"resampling.method must be one of {METHODS}")
    rng = np.random.default_rng(seed + 7_777)
    y = np.asarray(y, int)
    X = X.reset_index(drop=True)
    minority = 1 if (y == 1).sum() <= (y == 0).sum() else 0
    idx_min = np.flatnonzero(y == minority)
    n_new = int(round(float(section.get("ratio", 1.0)) * ((y != minority).sum() - len(idx_min))))
    if method == "noise":
        cont = [c for c in X.columns if c not in _categorical(X)]
        copy = X.copy()
        sd = X[cont].std()
        copy[cont] = copy[cont] + rng.normal(0, 1, (len(X), len(cont))) * (0.10 * sd.to_numpy())
        return pd.concat([X, copy], ignore_index=True), np.r_[y, y]
    if n_new <= 0 or len(idx_min) < 2:
        return X, y
    if method == "random_oversample":
        pick = rng.choice(idx_min, n_new, replace=True)
        return pd.concat([X, X.iloc[pick]], ignore_index=True), np.r_[y, np.full(n_new, minority)]

    # SMOTE for mixed data with missing values
    cat = set(_categorical(X))
    Z = X.iloc[idx_min]
    filled = Z.fillna(Z.median())
    scaled = ((filled - filled.mean()) / filled.std().replace(0, 1)).to_numpy(float)
    k = int(min(section.get("k", 5), len(idx_min) - 1))
    dist = ((scaled[:, None, :] - scaled[None, :, :]) ** 2).sum(-1)
    np.fill_diagonal(dist, np.inf)
    neighbours = np.argsort(dist, axis=1)[:, :k]
    base = rng.integers(0, len(idx_min), n_new)
    other = neighbours[base, rng.integers(0, k, n_new)]
    gap = rng.random(n_new)
    rows = []
    zb, zo = Z.iloc[base].reset_index(drop=True), Z.iloc[other].reset_index(drop=True)
    for col in X.columns:
        a, b = zb[col].to_numpy(float), zo[col].to_numpy(float)
        if col in cat:
            value = np.where(rng.random(n_new) < 0.5, a, np.where(np.isnan(b), a, b))
        else:
            value = np.where(np.isnan(b), a, a + gap * (b - a))
        rows.append(value)
    new = pd.DataFrame(np.column_stack(rows), columns=X.columns)
    return pd.concat([X, new], ignore_index=True), np.r_[y, np.full(n_new, minority)]
