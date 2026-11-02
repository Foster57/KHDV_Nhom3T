
from pathlib import Path
import duckdb

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
INTERIM_DIR = Path("data/interim")

FILES = [
    "2019-Oct.csv",
    "2019-Nov.csv",
    "2019-Dec.csv",
    "2020-Jan.csv",
    "2020-Feb.csv",
]

SAMPLE_TARGET = 20000
SEED = 42


def sql_path(path):
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def run_pipeline():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)

    paths = [RAW_DIR / name for name in FILES]

    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Missing: {path}")

    conn = duckdb.connect()
    conn.execute("SET memory_limit = '8GB'")
    conn.execute("SET threads = 4")
    conn.execute(
        f"SET temp_directory = '{sql_path(INTERIM_DIR / 'duckdb_tmp')}'"
    )

    try:
        # 1. Đọc toàn bộ CSV bằng DuckDB
        file_list = ", ".join(
            f"'{sql_path(path)}'" for path in paths
        )

        print("STEP 1: Reading 5 months...", flush=True)

        conn.execute(f"""
            CREATE OR REPLACE VIEW raw_events AS
            SELECT *
            FROM read_csv(
                [{file_list}],
                header = true,
                union_by_name = true,
                all_varchar = true
            )
        """)

        # 2. Chuẩn hóa Event Log
        print("STEP 2: Cleaning events...", flush=True)

        event_log = PROCESSED_DIR / "event_log.parquet"

        conn.execute(f"""
            COPY (
                WITH parsed AS (
                    SELECT
                        TRY_CAST(event_time AS TIMESTAMPTZ)
                            AS event_time,
                        LOWER(TRIM(event_type))
                            AS event_type,
                        NULLIF(TRIM(user_session), '')
                            AS user_session,
                        TRY_CAST(user_id AS BIGINT)
                            AS user_id,
                        TRY_CAST(product_id AS BIGINT)
                            AS product_id,
                        TRY_CAST(category_id AS BIGINT)
                            AS category_id,
                        category_code,
                        brand,
                        TRY_CAST(price AS DOUBLE)
                            AS price
                    FROM raw_events
                )
                SELECT *
                FROM parsed
                WHERE event_time IS NOT NULL
                  AND user_session IS NOT NULL
                  AND event_type IN (
                      'view',
                      'cart',
                      'remove_from_cart',
                      'purchase'
                  )
            )
            TO '{sql_path(event_log)}'
            (FORMAT PARQUET, COMPRESSION ZSTD)
        """)

        conn.execute(f"""
            CREATE OR REPLACE VIEW events AS
            SELECT * FROM read_parquet('{sql_path(event_log)}')
        """)

        # 3. Xây dựng đặc trưng theo phiên
        print("STEP 3: Building session features...", flush=True)

        features = PROCESSED_DIR / "session_features.parquet"

        conn.execute(f"""
            COPY (
                SELECT
                    user_session,
                    MIN(event_time) AS session_start,
                    MAX(event_time) AS session_end,
                    COUNT(*) AS n_events,
                    COUNT(*) FILTER (
                        WHERE event_type = 'view'
                    ) AS n_views,
                    COUNT(*) FILTER (
                        WHERE event_type = 'cart'
                    ) AS n_carts,
                    COUNT(*) FILTER (
                        WHERE event_type = 'remove_from_cart'
                    ) AS n_removes,
                    COUNT(*) FILTER (
                        WHERE event_type = 'purchase'
                    ) AS n_purchases,
                    COUNT(DISTINCT product_id)
                        AS n_products,
                    DATE_DIFF(
                        'second',
                        MIN(event_time),
                        MAX(event_time)
                    ) AS duration_seconds,
                    MAX(
                        CASE WHEN event_type = 'purchase'
                        THEN 1 ELSE 0 END
                    ) AS has_purchase
                FROM events
                GROUP BY user_session
            )
            TO '{sql_path(features)}'
            (FORMAT PARQUET, COMPRESSION ZSTD)
        """)

        # 4. Lấy mẫu theo phiên, không cắt ngang trace
        print("STEP 4: Sampling complete sessions...", flush=True)

        sample_path = PROCESSED_DIR / "event_log_sample.csv"

        conn.execute(f"""
            CREATE OR REPLACE TEMP TABLE selected_sessions AS
            WITH ranked AS (
                SELECT
                    user_session,
                    n_events,
                    SUM(n_events) OVER (
                        ORDER BY HASH(user_session, {SEED}),
                                 user_session
                        ROWS BETWEEN UNBOUNDED PRECEDING
                        AND CURRENT ROW
                    ) AS cumulative_events
                FROM read_parquet('{sql_path(features)}')
            )
            SELECT user_session
            FROM ranked
            WHERE cumulative_events - n_events < {SAMPLE_TARGET}
        """)

        conn.execute(f"""
            COPY (
                SELECT e.*
                FROM events e
                INNER JOIN selected_sessions s
                    ON e.user_session = s.user_session
                ORDER BY e.user_session, e.event_time
            )
            TO '{sql_path(sample_path)}'
            (HEADER, DELIMITER ',')
        """)

        # 5. Báo cáo chất lượng
        print("STEP 5: Generating quality report...", flush=True)

        quality_path = PROCESSED_DIR / "data_quality.csv"

        conn.execute(f"""
            COPY (
                SELECT
                    STRFTIME(event_time, '%Y-%m') AS month,
                    event_type,
                    COUNT(*) AS n_events,
                    COUNT(DISTINCT user_session)
                        AS n_sessions
                FROM events
                GROUP BY 1, 2
                ORDER BY 1, 2
            )
            TO '{sql_path(quality_path)}'
            (HEADER, DELIMITER ',')
        """)

        # 6. Kiểm tra kết quả
        print("\n=== PIPELINE REPORT ===")

        result = conn.execute(f"""
            SELECT
                COUNT(*) AS total_events,
                COUNT(DISTINCT user_session)
                    AS total_sessions,
                COUNT(*) FILTER (
                    WHERE event_type = 'purchase'
                ) AS purchases
            FROM events
        """).fetchone()

        print(f"Total valid events: {result[0]:,}")
        print(f"Total sessions: {result[1]:,}")
        print(f"Purchase events: {result[2]:,}")

        sample_result = conn.execute("""
            SELECT
                COUNT(*) AS n_events,
                COUNT(DISTINCT user_session) AS n_sessions
            FROM read_csv_auto(?)
        """, [str(sample_path)]).fetchone()

        print(f"Sample events: {sample_result[0]:,}")
        print(f"Sample sessions: {sample_result[1]:,}")
        print("\nPipeline completed successfully!")

    finally:
        conn.close()


if __name__ == "__main__":
    run_pipeline()
