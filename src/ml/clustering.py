
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd

from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import joblib


INPUT = Path("data/processed/session_features.parquet")
OUTPUT = Path("data/processed/ml")
TEMP = Path("data/interim/duckdb_ml_tmp")

MAX_SESSIONS = 200_000
RANDOM_STATE = 42

FEATURES = [
    "n_views",
    "n_carts",
    "n_removes",
    "n_purchases",
    "n_products",
    "duration_seconds"
]


def sql_path(path):
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def run():
    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)

    print("STEP 1: Loading session sample...", flush=True)

    con = duckdb.connect()
    try:
        con.execute("SET memory_limit='8GB'")
        con.execute("SET threads=4")
        con.execute(
            f"SET temp_directory='{sql_path(TEMP)}'"
        )

        # Deterministic hash sampling, without sorting
        # all 4.5 million sessions.
        df = con.execute(f"""
            SELECT
                user_session,
                n_views,
                n_carts,
                n_removes,
                n_purchases,
                n_products,
                duration_seconds,
                has_purchase
            FROM read_parquet('{sql_path(INPUT)}')
            WHERE HASH(user_session, 42) % 10000 < 440
        """).fetchdf()
    finally:
        con.close()

    if len(df) > MAX_SESSIONS:
        df = df.sample(
            n=MAX_SESSIONS,
            random_state=RANDOM_STATE
        ).reset_index(drop=True)

    print(f"Sampled sessions: {len(df):,}", flush=True)

    if len(df) < 100:
        raise ValueError("Not enough sampled sessions.")

    # Handle nulls and invalid numerical values.
    for col in FEATURES:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        ).replace(
            [np.inf, -np.inf], np.nan
        ).fillna(0).clip(lower=0)

    # Log transform reduces the influence
    # of extremely large event counts/durations.
    X_raw = np.log1p(df[FEATURES].to_numpy(dtype=float))

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    print("STEP 2: Selecting K...", flush=True)

    rng = np.random.default_rng(RANDOM_STATE)
    eval_size = min(5000, len(X))
    eval_indices = rng.choice(
        len(X), size=eval_size, replace=False
    )

    results = []
    best_score = -1
    best_model = None
    best_k = None

    for k in range(2, 7):
        model = MiniBatchKMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            batch_size=4096,
            n_init=5,
            max_iter=100
        )

        labels = model.fit_predict(X)

        # Silhouette on a small evaluation sample.
        eval_labels = labels[eval_indices]

        if len(np.unique(eval_labels)) < 2:
            score = -1.0
        else:
            score = silhouette_score(
                X[eval_indices],
                eval_labels,
                sample_size=min(2000, eval_size),
                random_state=RANDOM_STATE
            )

        results.append({
            "k": k,
            "silhouette_score": round(float(score), 4),
            "inertia": round(float(model.inertia_), 2)
        })

        print(
            f"K={k}, silhouette={score:.4f}",
            flush=True
        )

        if score > best_score:
            best_score = score
            best_model = model
            best_k = k

    scores = pd.DataFrame(results)
    scores.to_csv(
        OUTPUT / "clustering_scores.csv",
        index=False
    )

    print(
        f"\nSelected K = {best_k}",
        flush=True
    )

    print("STEP 3: Building cluster profiles...", flush=True)

    df["cluster"] = best_model.predict(X)

    # Cluster-level descriptive statistics.
    profile = df.groupby("cluster").agg(
        sessions=("user_session", "count"),
        avg_views=("n_views", "mean"),
        avg_carts=("n_carts", "mean"),
        avg_removes=("n_removes", "mean"),
        avg_purchases=("n_purchases", "mean"),
        avg_products=("n_products", "mean"),
        median_duration_seconds=(
            "duration_seconds", "median"
        ),
        purchase_session_rate=(
            "has_purchase", "mean"
        )
    ).reset_index()

    numeric_cols = profile.select_dtypes(
        include="number"
    ).columns.difference(["cluster", "sessions"])

    profile[numeric_cols] = profile[numeric_cols].round(3)

    profile["share_pct"] = (
        profile["sessions"] / len(df) * 100
    ).round(2)

    profile.to_csv(
        OUTPUT / "cluster_profiles.csv",
        index=False
    )

    # Keep session assignments for drill-down
    # and visualization in the dashboard.
    df.to_parquet(
        OUTPUT / "session_clusters.parquet",
        index=False
    )

    joblib.dump(
        {
            "model": best_model,
            "scaler": scaler,
            "features": FEATURES,
            "log_transform": True,
            "selected_k": best_k
        },
        OUTPUT / "clustering_model.joblib"
    )

    print("\n=== CLUSTER PROFILES ===")
    print(profile.to_string(index=False))

    print("\nClustering completed successfully!")
    print(f"Outputs saved to: {OUTPUT}")


if __name__ == "__main__":
    run()
