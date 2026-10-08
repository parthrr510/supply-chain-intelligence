import json
from pathlib import Path

import duckdb
import joblib
import numpy as np
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from machine_learning.ml.dataset import get_training_data
from machine_learning.ml.pipeline import get_preprocessing_pipeline, split_data


def train_and_evaluate(db_path: Path, artifact_dir: Path):
    # 1. Load data
    conn = duckdb.connect(str(db_path), read_only=True)
    df = get_training_data(conn)
    conn.close()

    # 2. Split data
    train_df, val_df, test_df = split_data(df)

    X_train = train_df.drop(columns=["target"])
    y_train = train_df["target"]

    X_val = val_df.drop(columns=["target"])
    y_val = val_df["target"]

    X_test = test_df.drop(columns=["target"])
    y_test = test_df["target"]

    # 3. Train
    pipeline = get_preprocessing_pipeline()
    pipeline.fit(X_train, y_train)

    # 4. Use validation set to tune the decision threshold for max F1
    y_val_proba = pipeline.predict_proba(X_val)[:, 1]
    best_threshold = 0.5
    best_f1 = 0.0
    for threshold in np.arange(0.1, 0.9, 0.05):
        y_val_pred = (y_val_proba >= threshold).astype(int)
        current_f1 = f1_score(y_val, y_val_pred)
        if current_f1 > best_f1:
            best_f1 = current_f1
            best_threshold = threshold

    print(f"Best validation threshold: {best_threshold:.2f} (F1: {best_f1:.4f})")

    # 5. Evaluate on untouched test set using the best threshold
    y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= best_threshold).astype(int)

    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    cm = confusion_matrix(y_test, y_pred)

    metrics = {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "best_threshold": float(best_threshold),
        "confusion_matrix": cm.tolist(),
    }

    print("Evaluation Metrics (Test Set):")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1:.4f}")
    print(f"ROC AUC: {roc_auc:.4f}")
    print(f"Confusion Matrix:\n{cm}")

    # 6. Persist
    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifact_dir / "delay_model.joblib"
    joblib.dump(pipeline, model_path)
    print(f"Model saved to {model_path}")

    # Save metrics
    with open(artifact_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    db_path = Path("data_engineering/data/curated/supply_chain.db")
    artifact_dir = Path("machine_learning/artifacts")
    train_and_evaluate(db_path, artifact_dir)
