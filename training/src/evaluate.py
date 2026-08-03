"""
Model evaluation module.

Evaluates the cancellation model on a held-out temporal test set and
produces a metrics dict that can be saved as ``metrics_v1.json``.

Supports both a tuned probability threshold (saved from val-set optimisation)
and the default 0.5 threshold, reporting both in the output.
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    precision_recall_curve,
)


def _git_commit_hash() -> str:
    """Return the current git commit hash, or ``'N/A'``."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "N/A"


def find_best_threshold(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    target: str = "f1",
) -> tuple[float, float]:
    """
    Find the probability threshold that maximises the target metric on a
    *validation* set.  Call this on val data, apply result to test data.

    Parameters
    ----------
    target : ``'f1'`` or ``'recall_at_70prec'``
        - ``'f1'``              : maximise F1 (balanced)
        - ``'recall_at_70prec'``: maximise recall subject to precision >= 0.70

    Returns
    -------
    (best_threshold, best_score)
    """
    prec_arr, rec_arr, thresholds = precision_recall_curve(y_true, y_proba)
    # Note: precision_recall_curve returns one extra point with threshold=1.0
    # so len(thresholds) == len(prec_arr) - 1
    prec_arr = prec_arr[:-1]
    rec_arr  = rec_arr[:-1]

    if target == "f1":
        f1s = 2 * prec_arr * rec_arr / (prec_arr + rec_arr + 1e-8)
        idx = int(np.argmax(f1s))
        return float(thresholds[idx]), float(f1s[idx])

    if target == "recall_at_70prec":
        mask = prec_arr >= 0.70
        if not mask.any():
            # fall back to f1 maximisation
            return find_best_threshold(y_true, y_proba, target="f1")
        idx = int(np.argmax(rec_arr * mask))
        score = float(rec_arr[idx])
        return float(thresholds[idx]), score

    raise ValueError(f"Unknown target: {target!r}")


def evaluate_model(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: list[str] | None = None,
    threshold: float = 0.5,
) -> dict:
    """
    Evaluate ``model`` on the test arrays and return a metrics dict.

    Reports metrics at both the default 0.5 threshold and the supplied
    (val-set-tuned) ``threshold``.

    The dict is ready to be serialised to ``metrics_v1.json``.
    """
    y_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_proba)

    def _metrics_at(thresh: float) -> dict:
        y_pred = (y_proba >= thresh).astype(int)
        cm = confusion_matrix(y_test, y_pred)
        return {
            "threshold":  round(thresh, 4),
            "accuracy":   round(float(accuracy_score(y_test, y_pred)), 4),
            "precision":  round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "recall":     round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
            "f1_score":   round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
            "confusion_matrix": cm.tolist(),
        }

    at_default = _metrics_at(0.5)
    at_tuned   = _metrics_at(threshold)

    def _print_block(label: str, m: dict):
        cm = m["confusion_matrix"]
        print(f"  [{label}]  threshold = {m['threshold']}")
        print(f"    Accuracy : {m['accuracy']*100:7.2f} %")
        print(f"    Precision: {m['precision']*100:7.2f} %")
        print(f"    Recall   : {m['recall']*100:7.2f} %")
        print(f"    F1-Score : {m['f1_score']*100:7.2f} %")
        print(f"    TN={cm[0][0]:>6,}  FP={cm[0][1]:>6,}  "
              f"FN={cm[1][0]:>6,}  TP={cm[1][1]:>6,}")

    print()
    print("=" * 60)
    print("  MODEL EVALUATION  (temporal test set)")
    print("=" * 60)
    print(f"  ROC-AUC: {auc * 100:.2f} %")
    print()
    _print_block("Default  0.50", at_default)
    print()
    _print_block("Tuned  ", at_tuned)
    print("=" * 60)
    print()

    # Primary metrics (at tuned threshold) for backward compat keys
    return {
        # Top-level = tuned threshold metrics (used by frontend/API)
        "accuracy":         at_tuned["accuracy"],
        "precision":        at_tuned["precision"],
        "recall":           at_tuned["recall"],
        "f1_score":         at_tuned["f1_score"],
        "roc_auc":          round(float(auc), 4),
        "threshold":        round(threshold, 4),
        "confusion_matrix": at_tuned["confusion_matrix"],
        # Also store both sets for reference
        "metrics_at_default_threshold": at_default,
        "metrics_at_tuned_threshold":   at_tuned,
        "git_commit":  _git_commit_hash(),
        "timestamp":   datetime.now(timezone.utc).isoformat(),
    }
