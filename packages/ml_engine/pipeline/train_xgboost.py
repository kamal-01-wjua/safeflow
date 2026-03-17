from __future__ import annotations

"""
Offline training script for XGBoost (ML Engine v2).

This file is NOT imported by the FastAPI app at runtime.
You run it manually in a training environment where xgboost,
pandas, and scikit-learn are installed.

Example usage (from project root, in a venv with xgboost installed):

    python -m packages.ml_engine.pipeline.train_xgboost

Later we can:
  - Load data from Postgres
  - Log metrics to MLflow or a similar tool
  - Save model + feature schema to disk (e.g. models/xgboost_v2.json)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

# NOTE: xgboost must be installed in the environment where you run this script.
# It is intentionally not used anywhere in the FastAPI runtime path.
import xgboost as xgb

from packages.ml_engine.features import build_features_for_events
from packages.ml_engine.schemas import MLTransactionEvent


# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

@dataclass
class XGBoostTrainingConfig:
    test_size: float = 0.2
    random_state: int = 42
    model_output_path: Path = Path("models/xgboost_v2.json")
    feature_schema_output_path: Path = Path("models/feature_schema_v2.json")


# -----------------------------------------------------------------------------
# Data loading helpers (to be customized for your environment)
# -----------------------------------------------------------------------------


def load_training_data() -> Tuple[List[MLTransactionEvent], np.ndarray]:
    """
    Load and return:
      - a list of MLTransactionEvent objects
      - a numpy array of labels (0/1 for fraud)

    For now this is a placeholder using a fake in-memory dataset.
    Later, replace with real data loaded from Postgres or Parquet.
    """
    # TODO: replace this with REAL data fetching logic.
    # Example structure:
    #   df = pd.read_sql("SELECT ... FROM training_view", engine)
    #
    # For now, we create a tiny dummy dataset.

    events: List[MLTransactionEvent] = []
    labels: List[int] = []

    rng = np.random.default_rng(42)
    n_samples = 1000

    for i in range(n_samples):
        amount = float(rng.uniform(1.0, 20_000.0))
        is_fraud = 1 if amount > 15_000 else 0

        evt = MLTransactionEvent(
            transaction_id=i,
            tenant_id=1,
            transaction_reference=f"TXN-{i}",
            account_id=f"ACC-{i % 10}",
            amount=amount,
            currency="MYR",
            direction="DEBIT",
            status="BOOKED",
            timestamp=pd.Timestamp("2025-01-01") + pd.to_timedelta(i, unit="m"),
        )
        events.append(evt)
        labels.append(is_fraud)

    y = np.array(labels, dtype=int)
    return events, y


# -----------------------------------------------------------------------------
# Training logic
# -----------------------------------------------------------------------------


def train_xgboost_model(config: XGBoostTrainingConfig) -> None:
    events, labels = load_training_data()

    # Build features with the SAME logic as the API
    feature_dicts = build_features_for_events(events)
    df_features = pd.DataFrame(feature_dicts)

    X = df_features.values
    y = labels

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.test_size,
        random_state=config.random_state,
        stratify=y,
    )

    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)

    params = {
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "max_depth": 5,
        "eta": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "tree_method": "hist",
    }

    evals = [(dtrain, "train"), (dtest, "valid")]

    print("Training XGBoost model...")
    booster = xgb.train(
        params=params,
        dtrain=dtrain,
        num_boost_round=200,
        evals=evals,
        verbose_eval=20,
    )

    # Evaluate AUROC on test set
    y_pred_proba = booster.predict(dtest)
    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"Test AUROC: {auc:.4f}")

    # Save model
    config.model_output_path.parent.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(config.model_output_path))
    print(f"Saved model to {config.model_output_path}")

    # Save feature schema (column ordering)
    feature_names = list(df_features.columns)
    schema_df = pd.DataFrame({"feature_name": feature_names})
    schema_df.to_json(config.feature_schema_output_path, orient="records", indent=2)
    print(f"Saved feature schema to {config.feature_schema_output_path}")


def main() -> None:
    config = XGBoostTrainingConfig()
    train_xgboost_model(config)


if __name__ == "__main__":
    main()
