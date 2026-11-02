
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
import joblib

from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    average_precision_score
)

INPUT = Path("data/processed/event_log.parquet")
OUTPUT = Path("data/processed/ml")
TEMP = Path("data/interim/duckdb_tree_tmp")

FEATURES = [
    "views_before_cart",
    "products_viewed_before_cart",
    "seconds_before_cart"
]


def sql_path(path):
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def run():
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()

    try:
        con.execute("SET memory_limit='8GB'")
        con.execute("SET threads=4")
        con.execute(
            f"SET temp_directory='{sql_path(TEMP)}'"
        )

        print("STEP 1: Preparing prediction dataset...", flush=True)

        con.execute(f"""
            CREATE VIEW events AS
            SELECT
                user_session,
                event_time,
                event_type,
                product_id
            FROM read_parquet('{sql_path(INPUT)}')
        """)

        # One observation per session.
        # Prediction point: first recorded cart event.
        con.execute("""
            CREATE TEMP TABLE cart_cases AS
            SELECT
                user_session,
                MIN(event_time) FILTER (
                    WHERE event_type = 'cart'
                ) AS first_cart_time,
                MIN(event_time) AS session_start
            FROM events
            GROUP BY user_session
            HAVING COUNT(*) FILTER (
                WHERE event_type = 'cart'
            ) > 0
        """)

        # Features use only events strictly BEFORE first cart.
        # Label uses purchase strictly AFTER first cart.
        con.execute("""
            CREATE TEMP TABLE training_cases AS
            SELECT
                c.user_session,
                c.first_cart_time,

                COUNT(*) FILTER (
                    WHERE e.event_type = 'view'
                      AND e.event_time < c.first_cart_time
                ) AS views_before_cart,

                COUNT(DISTINCT e.product_id) FILTER (
                    WHERE e.event_type = 'view'
                      AND e.event_time < c.first_cart_time
                ) AS products_viewed_before_cart,

                DATE_DIFF(
                    'second',
                    c.session_start,
                    c.first_cart_time
                ) AS seconds_before_cart,

                CAST(
                    COUNT(*) FILTER (
                        WHERE e.event_type = 'purchase'
                          AND e.event_time > c.first_cart_time
                    ) > 0 AS INTEGER
                ) AS target

            FROM cart_cases c
            JOIN events e
                ON c.user_session = e.user_session
            GROUP BY
                c.user_session,
                c.first_cart_time,
                c.session_start
        """)

        print("STEP 2: Sampling cases...", flush=True)

        df = con.execute("""
            SELECT *
            FROM training_cases
            WHERE HASH(user_session, 42) % 10000 < 2500
        """).fetchdf()

    finally:
        con.close()

    if len(df) < 100:
        raise ValueError("Insufficient training data.")

    df["first_cart_time"] = pd.to_datetime(
        df["first_cart_time"], utc=True
    )

    df = df.sort_values(
        ["first_cart_time", "user_session"]
    ).reset_index(drop=True)

    for col in FEATURES:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        ).fillna(0).clip(lower=0)

    print(f"Sampled cart sessions: {len(df):,}")
    print(f"Positive rate: {df['target'].mean():.4f}")

    # Chronological split reduces future-to-past leakage.
    # A later purchase can still occur after the split
    # because the dataset does not define a prediction horizon.
    split = int(len(df) * 0.8)

    train = df.iloc[:split]
    test = df.iloc[split:]

    X_train = train[FEATURES]
    y_train = train["target"]

    X_test = test[FEATURES]
    y_test = test["target"]

    print("STEP 3: Training Decision Tree...", flush=True)

    model = DecisionTreeClassifier(
        max_depth=5,
        min_samples_leaf=200,
        class_weight="balanced",
        random_state=42
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    print("\n=== MODEL EVALUATION ===")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    print("Confusion matrix:")
    print(confusion_matrix(y_test, predictions))

    if y_test.nunique() == 2:
        roc_auc = roc_auc_score(
            y_test, probabilities
        )
        pr_auc = average_precision_score(
            y_test, probabilities
        )
    else:
        roc_auc = np.nan
        pr_auc = np.nan

    baseline = float(y_test.mean())

    metrics = pd.DataFrame([{
        "train_sessions": len(train),
        "test_sessions": len(test),
        "test_purchase_rate": baseline,
        "roc_auc": roc_auc,
        "average_precision": pr_auc,
        "random_baseline_ap": baseline
    }])

    metrics.to_csv(
        OUTPUT / "decision_tree_metrics.csv",
        index=False
    )

    importance = pd.DataFrame({
        "feature": FEATURES,
        "importance": model.feature_importances_
    }).sort_values(
        "importance", ascending=False
    )

    importance.to_csv(
        OUTPUT / "decision_tree_importance.csv",
        index=False
    )

    results = test[
        ["user_session", "first_cart_time", "target"]
        + FEATURES
    ].copy()

    results["predicted_purchase"] = predictions
    results["purchase_probability"] = probabilities

    results.to_csv(
        OUTPUT / "decision_tree_predictions.csv",
        index=False
    )

    joblib.dump(
        {
            "model": model,
            "features": FEATURES,
            "prediction_point": "first_cart"
        },
        OUTPUT / "decision_tree_model.joblib"
    )

    print("\n=== SUMMARY ===")
    print(metrics.to_string(index=False))

    print("\n=== FEATURE IMPORTANCE ===")
    print(importance.to_string(index=False))

    print("\nDecision Tree completed successfully!")
    print(f"Outputs saved to: {OUTPUT}")


if __name__ == "__main__":
    run()
