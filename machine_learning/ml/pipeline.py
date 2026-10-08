import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def get_preprocessing_pipeline() -> Pipeline:
    categorical_features = [
        "origin_port",
        "destination_port",
        "vessel_id",
        "cargo_type",
    ]
    numeric_features = [
        "container_count",
        "weight_tons",
        "planned_transit_days",
        "origin_congestion_score",
        "destination_congestion_score",
        "booking_month",
        "booking_day_of_week",
    ]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42)),
        ]
    )

    return pipeline


def split_data(df: pd.DataFrame):
    """
    Splits the dataframe chronologically into 70% train, 15% validation, 15% test.
    The dataframe should already be sorted chronologically by the query.
    """
    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    train_df = df.iloc[:train_end]
    val_df = df.iloc[train_end:val_end]
    test_df = df.iloc[val_end:]

    return train_df, val_df, test_df
