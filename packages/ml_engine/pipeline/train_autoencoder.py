from __future__ import annotations

"""
Offline training script for an Autoencoder (ML Engine v2).

This is a placeholder skeleton. You can implement it using:
  - PyTorch
  - TensorFlow/Keras
  - or even a simple sklearn-based approach

The key idea:
  - Train only on "normal" (non-fraud) transactions.
  - Use the reconstruction error as an anomaly score.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

from packages.ml_engine.features import build_features_for_events
from packages.ml_engine.schemas import MLTransactionEvent


@dataclass
class AutoencoderTrainingConfig:
    model_output_path: Path = Path("models/autoencoder_v2.bin")
    metadata_output_path: Path = Path("models/autoencoder_metadata_v2.json")


def load_normal_data() -> List[MLTransactionEvent]:
    """
    Load a list of MLTransactionEvent objects representing NORMAL behaviour.

    For now, this uses a dummy synthetic dataset.
    Later, you will:
      - pull from Postgres where label_fraud = 0
      - or curate normal-only periods
    """
    events: List[MLTransactionEvent] = []
    rng = np.random.default_rng(123)
    n_samples = 1000

    for i in range(n_samples):
        amount = float(rng.uniform(1.0, 8_000.0))

        evt = MLTransactionEvent(
            transaction_id=i,
            tenant_id=1,
            transaction_reference=f"NORM-{i}",
            account_id=f"ACC-{i % 5}",
            amount=amount,
            currency="MYR",
            direction="DEBIT",
            status="BOOKED",
            timestamp=pd.Timestamp("2025-01-01") + pd.to_timedelta(i, unit="m"),
        )
        events.append(evt)

    return events


def train_autoencoder_model(config: AutoencoderTrainingConfig) -> None:
    events = load_normal_data()

    feature_dicts = build_features_for_events(events)
    df_features = pd.DataFrame(feature_dicts)
    X = df_features.values.astype("float32")

    # TODO: implement a real autoencoder here using your framework of choice.
    # For now we just compute a simple baseline:
    #
    #   - mean vector of normal features
    #   - reconstruction error = L2 distance to this mean
    #
    mean_vector = X.mean(axis=0, keepdims=True)

    # Example of computing errors (train-time)
    diffs = X - mean_vector
    squared = diffs ** 2
    errors = np.sqrt(np.sum(squared, axis=1))
    print(f"Sample reconstruction error stats: mean={errors.mean():.4f} std={errors.std():.4f}")

    # Example of saving metadata with the mean vector + threshold
    import json

    config.model_output_path.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        "mean_vector": mean_vector.tolist(),
        "error_mean": float(errors.mean()),
        "error_std": float(errors.std()),
        "suggested_threshold": float(errors.mean() + 3 * errors.std()),
    }

    with open(config.metadata_output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved autoencoder metadata to {config.metadata_output_path}")
    print("NOTE: Implement real AE model saving here in the future.")


def main() -> None:
    config = AutoencoderTrainingConfig()
    train_autoencoder_model(config)


if __name__ == "__main__":
    main()
