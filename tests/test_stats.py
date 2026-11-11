import math

import numpy as np

from greyzone_rf.stats import (INCONCLUSIVE, NEGATIVE, POSITIVE, apply_thresholds, cp_interval, cp_lower_bound,
                               minimum_calls_needed, select_threshold, triage_metrics)


def test_clopper_pearson_lower_bound_all_correct():
    # with n/n correct the one-sided lower bound is alpha**(1/n)
    for n in (10, 59, 100):
        assert math.isclose(cp_lower_bound(n, n, 0.95), 0.05 ** (1 / n), rel_tol=1e-9)
    assert cp_lower_bound(0, 10) == 0.0
    assert cp_lower_bound(0, 0) == 0.0


def test_clopper_pearson_interval_contains_estimate():
    lo, hi = cp_interval(45, 50)
    assert lo < 0.9 < hi
    assert cp_interval(50, 50)[1] == 1.0
    assert cp_interval(0, 50)[0] == 0.0


def test_minimum_calls_needed_rule_of_three():
    need = minimum_calls_needed(0.95, 0.95, 3)
    assert need[0] == 59          # 0.95**59 < 0.05 <= 0.95**58
    assert need[0] < need[1] < need[2] < need[3]


def test_select_threshold_requires_enough_evidence():
    rng = np.random.default_rng(0)
    y = np.r_[np.zeros(300, int), np.ones(300, int)]
    scores = np.r_[rng.uniform(0, 0.6, 300), rng.uniform(0.4, 1.0, 300)]
    pos = select_threshold(scores, y, "positive", 0.95)
    neg = select_threshold(scores, y, "negative", 0.95)
    assert pos["chosen"] is not None and neg["chosen"] is not None
    assert pos["chosen"]["lower_bound"] >= 0.95 and neg["chosen"]["lower_bound"] >= 0.95
    assert neg["chosen"]["threshold"] < pos["chosen"]["threshold"]
    # the same separation with only 20 patients cannot be certified
    small = select_threshold(scores[::30], y[::30], "positive", 0.95)
    assert small["chosen"] is None


def test_point_estimate_mode_is_more_permissive():
    rng = np.random.default_rng(1)
    y = rng.integers(0, 2, 120)
    scores = np.clip(y * 0.5 + rng.normal(0.25, 0.15, 120), 0, 1)
    strict = select_threshold(scores, y, "positive", 0.95, use_bound=True)
    loose = select_threshold(scores, y, "positive", 0.95, use_bound=False)
    assert loose["chosen"] is not None
    if strict["chosen"] is not None:
        assert loose["chosen"]["threshold"] <= strict["chosen"]["threshold"]


def test_apply_thresholds_and_metrics():
    scores = np.array([0.05, 0.5, 0.95, 0.9, 0.1])
    d = apply_thresholds(scores, 0.8, 0.2)
    assert list(d) == [NEGATIVE, INCONCLUSIVE, POSITIVE, POSITIVE, NEGATIVE]
    assert list(apply_thresholds(scores, None, None)) == [INCONCLUSIVE] * 5
    m = triage_metrics(np.array([0, 1, 1, 0, 1]), d)
    assert m["true_positive"] == 1 and m["false_positive"] == 1
    assert m["true_negative"] == 1 and m["false_negative"] == 1
    assert m["inconclusive"] == 1 and m["resolved"]["k"] == 4
