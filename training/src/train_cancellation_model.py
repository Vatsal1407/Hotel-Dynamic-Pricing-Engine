"""
Training script for the XGBoost cancellation-prediction model.

Produces artifacts in ``training/artifacts/``:
  - model_v1.joblib          (fitted XGBoost model)
  - encoders_v1.joblib       (dict of fitted LabelEncoders)
  - feature_metadata_v1.json (adr constants + segment-season lookup + threshold)
  - metrics_v1.json          (test-set evaluation + git hash + timestamp)

Design decisions:
  - StandardScaler removed (XGBoost is scale-invariant; no scaler artifact)
  - No SMOTE: class imbalance handled solely via XGBoost's scale_pos_weight
    (avoids breaking derived-feature consistency and fake categorical codes)
  - Optuna objective: ROC-AUC instead of accuracy (avoids majority-class bias)
  - Optuna trials: 30
  - Early stopping (50 rounds) on both baseline and final model
  - Threshold tuning on validation set; best threshold saved to metadata
  - Two interaction features (39 total)

Usage (from project root):
    python training/src/train_cancellation_model.py
"""
from __future__ import annotations

import os
import json
import warnings

import numpy as np
import joblib
import optuna
import xgboost as xgb
from sklearn.metrics import roc_auc_score
# No SMOTE — class imbalance handled by XGBoost's scale_pos_weight parameter

from data_loader import load_data
from clean import clean_data
from features import (
    engineer_features,
    compute_feature_constants,
    compute_segment_season_avg_adr,
    FEATURE_NAMES,
)
from evaluate import evaluate_model, find_best_threshold

warnings.filterwarnings("ignore", category=FutureWarning)

# ── paths ────────────────────────────────────────────────────────────────────

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")

# ── helpers ──────────────────────────────────────────────────────────────────


def temporal_split(df, train_frac=0.70, val_frac=0.15):
    """
    Temporal split -- sort chronologically then cut 70 / 15 / 15.
    Intentional: pricing model must generalise to *future* bookings.
    """
    df = df.sort_values(
        ["arrival_date_year", "arrival_date_week_number"]
    ).reset_index(drop=True)

    n  = len(df)
    t1 = int(n * train_frac)
    t2 = int(n * (train_frac + val_frac))
    return df.iloc[:t1], df.iloc[t1:t2], df.iloc[t2:]


# ── main ─────────────────────────────────────────────────────────────────────


def train() -> None:
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    # 1. Load & clean ─────────────────────────────────────────────────────
    print("\n[1/9] Loading data ...")
    raw_df = load_data()
    print(f"        Raw shape: {raw_df.shape}")

    print("[2/9] Cleaning data ...")
    clean_df = clean_data(raw_df)
    print(f"        Clean shape: {clean_df.shape}")

    # 2. Temporal split ───────────────────────────────────────────────────
    print("[3/9] Temporal split ...")
    train_df, val_df, test_df = temporal_split(clean_df)
    print(f"        Train {len(train_df):,}  Val {len(val_df):,}  Test {len(test_df):,}")

    # 3. Compute constants from training data ─────────────────────────────
    print("[4/9] Computing feature constants from training data ...")
    constants = compute_feature_constants(train_df)
    seg_avg   = compute_segment_season_avg_adr(train_df)

    # 4. Engineer features ────────────────────────────────────────────────
    print("[5/8] Engineering features ...")
    y_train = train_df["is_canceled"].values
    y_val   = val_df["is_canceled"].values
    y_test  = test_df["is_canceled"].values

    X_train, encoders = engineer_features(train_df, constants, fit_encoders=True)
    X_val, _          = engineer_features(val_df,   constants, encoders=encoders)
    X_test, _         = engineer_features(test_df,  constants, encoders=encoders)
    print(f"        Shapes -- train {X_train.shape}  val {X_val.shape}  test {X_test.shape}")

    enc_path = os.path.join(ARTIFACTS_DIR, "encoders_v1.joblib")
    joblib.dump(encoders, enc_path)
    print(f"        -> {enc_path}")

    # NOTE: No StandardScaler -- XGBoost is a tree model (scale-invariant).
    # NOTE: No SMOTE -- class imbalance is handled solely by XGBoost's
    #   scale_pos_weight parameter (tuned by Optuna). This avoids:
    #   (a) breaking derived-feature consistency (e.g. SMOTE interpolates
    #       lead_time and lead_time_squared independently, producing rows
    #       where squared != lead_time^2),
    #   (b) creating fake categorical codes (LabelEncoded country values
    #       interpolated to non-integer "between" countries), and
    #   (c) double-correcting for imbalance (SMOTE + scale_pos_weight).

    X_train_arr = X_train.values
    X_val_arr   = X_val.values
    X_test_arr  = X_test.values

    cancel_rate = y_train.mean()
    print(f"        Training cancel rate: {cancel_rate*100:.1f}%")

    # 5. Optuna hyper-parameter search (30 trials, maximise ROC-AUC) ──────
    print("[6/8] Optuna optimisation (30 trials, objective=ROC-AUC)...")

    def objective(trial: optuna.Trial) -> float:
        params = dict(
            n_estimators     = trial.suggest_int("n_estimators", 300, 1500),
            max_depth        = trial.suggest_int("max_depth", 4, 12),
            learning_rate    = trial.suggest_float("learning_rate", 0.005, 0.1, log=True),
            subsample        = trial.suggest_float("subsample", 0.6, 1.0),
            colsample_bytree = trial.suggest_float("colsample_bytree", 0.6, 1.0),
            min_child_weight = trial.suggest_int("min_child_weight", 1, 10),
            gamma            = trial.suggest_float("gamma", 0, 1.0),
            reg_alpha        = trial.suggest_float("reg_alpha", 0, 2.0),
            reg_lambda       = trial.suggest_float("reg_lambda", 0, 2.0),
            scale_pos_weight = trial.suggest_float("scale_pos_weight", 1.0, 3.0),
            random_state     = 42,
            n_jobs           = -1,
            eval_metric      = "auc",    # AUC for early-stopping monitor
        )
        m = xgb.XGBClassifier(
            **params,
            early_stopping_rounds=30,   # speeds up each Optuna trial
        )
        m.fit(
            X_train_arr, y_train,
            eval_set=[(X_val_arr, y_val)],
            verbose=0,
        )
        y_proba = m.predict_proba(X_val_arr)[:, 1]
        return roc_auc_score(y_val, y_proba)

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=42),
    )
    study.optimize(objective, n_trials=30, show_progress_bar=True)

    best_auc = study.best_trial.value
    best_params = study.best_trial.params
    print(f"        Best val ROC-AUC: {best_auc * 100:.2f} %")
    print(f"        Best params: {best_params}")

    # 6. Final model with best params + early stopping ─────────────────────
    print("[7/8] Training final model ...")
    final_params = {
        **best_params,
        "random_state": 42,
        "n_jobs": -1,
        "eval_metric": "auc",
        "early_stopping_rounds": 50,   # stop when val-AUC stops improving
    }
    final = xgb.XGBClassifier(**final_params)
    final.fit(
        X_train_arr, y_train,
        eval_set=[(X_val_arr, y_val)],
        verbose=100,
    )
    print(f"        Stopped at iteration: {final.best_iteration}")

    model_path = os.path.join(ARTIFACTS_DIR, "model_v1.joblib")
    joblib.dump(final, model_path)
    print(f"        -> {model_path}")

    # 7. Threshold tuning on VALIDATION set ────────────────────────────────
    print("[8/8] Tuning decision threshold on validation set ...")
    y_val_proba = final.predict_proba(X_val_arr)[:, 1]

    # Maximise F1 (balanced precision/recall trade-off)
    best_thresh_f1, best_f1 = find_best_threshold(y_val, y_val_proba, target="f1")
    # Also compute recall-constrained threshold (useful reference)
    best_thresh_rec, best_rec = find_best_threshold(
        y_val, y_val_proba, target="recall_at_70prec"
    )

    print(f"        Threshold (max F1):             {best_thresh_f1:.3f}  (val F1={best_f1*100:.2f}%)")
    print(f"        Threshold (recall@prec>=0.70):  {best_thresh_rec:.3f}  (val recall={best_rec*100:.2f}%)")

    # Use F1-optimised threshold as primary
    best_threshold = best_thresh_f1

    # 8. Save metadata (constants + threshold + seg averages) ──────────────
    metadata = {
        **constants,
        "segment_season_avg_adr": seg_avg,
        "best_threshold":         round(best_threshold, 4),
        "threshold_f1":           round(best_thresh_f1, 4),
        "threshold_recall70prec": round(best_thresh_rec, 4),
        "n_features":             len(FEATURE_NAMES),
        "feature_names":          FEATURE_NAMES,
    }
    meta_path = os.path.join(ARTIFACTS_DIR, "feature_metadata_v1.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"        -> {meta_path}")

    # 9. Evaluate on temporal test set at tuned threshold ─────────────────
    metrics = evaluate_model(final, X_test_arr, y_test, FEATURE_NAMES,
                             threshold=best_threshold)
    met_path = os.path.join(ARTIFACTS_DIR, "metrics_v1.json")
    with open(met_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"        -> {met_path}")

    print("\n[DONE] Training complete -- artifacts saved to", ARTIFACTS_DIR)


if __name__ == "__main__":
    train()
