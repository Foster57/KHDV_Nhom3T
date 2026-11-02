
from pathlib import Path
import duckdb


# ==========================================
# 1. CONFIGURATION
# ==========================================

DATA_PATH = Path("data/processed/event_log.parquet")
FEATURES_PATH = Path("data/processed/session_features.parquet")
REPORT_DIR = Path("data/processed/validation")
TEMP_DIR = Path("data/interim/duckdb_validation_tmp")


def sql_path(path):
    return (
        str(path.resolve())
        .replace("\\", "/")
        .replace("'", "''")
    )


def export_query(con, query, output_path):
    """Export SQL query result to CSV."""
    con.execute(f"""
        COPY (
            {query}
        )
        TO '{sql_path(output_path)}'
        (HEADER, DELIMITER ',')
    """)


def validate():

    # ======================================
    # 2. CHECK INPUT FILES
    # ======================================

    if not DATA_PATH.is_file():
        raise FileNotFoundError(
            f"Missing event log: {DATA_PATH}"
        )

    if not FEATURES_PATH.is_file():
        raise FileNotFoundError(
            f"Missing session features: {FEATURES_PATH}"
        )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    TEMP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    con = duckdb.connect()

    try:
        con.execute("SET memory_limit = '8GB'")
        con.execute("SET threads = 4")

        con.execute(
            f"SET temp_directory = '{sql_path(TEMP_DIR)}'"
        )

        con.execute(f"""
            CREATE VIEW events AS
            SELECT *
            FROM read_parquet('{sql_path(DATA_PATH)}')
        """)

        con.execute(f"""
            CREATE VIEW sessions AS
            SELECT *
            FROM read_parquet('{sql_path(FEATURES_PATH)}')
        """)

        print(
            "\n=== DATA VALIDATION REPORT ===",
            flush=True
        )

        # ======================================
        # 3. SESSION DURATION
        # ======================================

        print(
            "\n[1] SESSION DURATION",
            flush=True
        )

        duration = con.execute("""
            SELECT
                COUNT(*) AS total_sessions,

                COUNT(*) FILTER (
                    WHERE n_events = 1
                ) AS single_event_sessions,

                COUNT(*) FILTER (
                    WHERE duration_seconds > 86400
                ) AS sessions_over_24h,

                COUNT(*) FILTER (
                    WHERE duration_seconds > 604800
                ) AS sessions_over_7d,

                MAX(duration_seconds)
                    AS max_duration_seconds,

                MEDIAN(duration_seconds)
                    AS median_duration_seconds,

                QUANTILE_CONT(
                    duration_seconds, 0.95
                ) AS p95_duration_seconds

            FROM sessions
        """).fetchdf()

        print(
            duration.to_string(index=False),
            flush=True
        )

        duration.to_csv(
            REPORT_DIR / "duration_summary.csv",
            index=False
        )

        # ======================================
        # 4. PURCHASE CONVERSION
        # ======================================

        print(
            "\n[2] PURCHASE CONVERSION",
            flush=True
        )

        conversion = con.execute("""
            SELECT
                COUNT(*) AS total_sessions,

                COUNT(*) FILTER (
                    WHERE has_purchase = 1
                ) AS purchase_sessions,

                ROUND(
                    100.0 *
                    COUNT(*) FILTER (
                        WHERE has_purchase = 1
                    )
                    / NULLIF(COUNT(*), 0),
                    2
                ) AS purchase_session_rate_pct

            FROM sessions
        """).fetchdf()

        print(
            conversion.to_string(index=False),
            flush=True
        )

        conversion.to_csv(
            REPORT_DIR / "conversion_summary.csv",
            index=False
        )

        # ======================================
        # 5. EVENT DISTRIBUTION
        # ======================================

        print(
            "\n[3] EVENT DISTRIBUTION",
            flush=True
        )

        event_distribution = con.execute("""
            SELECT
                event_type,

                COUNT(*) AS n_events,

                ROUND(
                    100.0 * COUNT(*)
                    / NULLIF(
                        SUM(COUNT(*)) OVER (), 0
                    ),
                    2
                ) AS percentage

            FROM events
            GROUP BY event_type
            ORDER BY n_events DESC
        """).fetchdf()

        print(
            event_distribution.to_string(index=False),
            flush=True
        )

        event_distribution.to_csv(
            REPORT_DIR / "event_distribution.csv",
            index=False
        )

        # ======================================
        # 6. SESSION / USER CONSISTENCY
        # ======================================

        print(
            "\n[4] SESSION / USER CONSISTENCY",
            flush=True
        )

        multi_user_query = """
            SELECT
                user_session,
                COUNT(DISTINCT user_id)
                    AS distinct_users,
                COUNT(*) AS n_events,
                MIN(event_time) AS first_event,
                MAX(event_time) AS last_event

            FROM events
            WHERE user_id IS NOT NULL
            GROUP BY user_session
            HAVING COUNT(DISTINCT user_id) > 1
        """

        multi_user_count = con.execute(f"""
            SELECT COUNT(*)
            FROM ({multi_user_query}) t
        """).fetchone()[0]

        print(
            "Sessions with multiple user IDs:",
            multi_user_count,
            flush=True
        )

        export_query(
            con,
            multi_user_query + """
                ORDER BY distinct_users DESC,
                         n_events DESC
            """,
            REPORT_DIR / "multi_user_sessions.csv"
        )

        # ======================================
        # 7. EXACT DUPLICATE ROWS
        # ======================================

        print(
            "\n[5] EXACT DUPLICATE ROWS",
            flush=True
        )

        # Explicit grouping is essential.
        # GROUP BY ALL with only COUNT(*) would
        # incorrectly group the entire dataset.

        duplicate_count = con.execute("""
            SELECT
                COALESCE(SUM(n - 1), 0)
                    AS duplicate_rows

            FROM (
                SELECT
                    event_time,
                    event_type,
                    user_session,
                    user_id,
                    product_id,
                    category_id,
                    category_code,
                    brand,
                    price,
                    COUNT(*) AS n

                FROM events

                GROUP BY
                    event_time,
                    event_type,
                    user_session,
                    user_id,
                    product_id,
                    category_id,
                    category_code,
                    brand,
                    price

                HAVING COUNT(*) > 1
            ) t
        """).fetchone()[0]

        print(
            "Exact duplicate rows:",
            duplicate_count,
            flush=True
        )

        # ======================================
        # 8. LONG SESSION ANALYSIS
        # ======================================

        print(
            "\n[6] LONG SESSION ANALYSIS",
            flush=True
        )

        long_sessions_query = """
            SELECT
                user_session,
                session_start,
                session_end,
                n_events,
                duration_seconds,
                n_views,
                n_carts,
                n_removes,
                n_purchases,
                has_purchase

            FROM sessions

            WHERE duration_seconds > 86400

            ORDER BY duration_seconds DESC
        """

        export_query(
            con,
            long_sessions_query,
            REPORT_DIR / "long_sessions.csv"
        )

        print(
            "Exported sessions longer than 24h.",
            flush=True
        )

        # ======================================
        # 9. MONTHLY DISTRIBUTION
        # ======================================

        print(
            "\n[7] MONTHLY EVENT DISTRIBUTION",
            flush=True
        )

        monthly_query = """
            SELECT
                STRFTIME(event_time, '%Y-%m')
                    AS month,

                event_type,

                COUNT(*) AS n_events,

                COUNT(DISTINCT user_session)
                    AS n_sessions

            FROM events
            GROUP BY 1, 2
            ORDER BY 1, 2
        """

        monthly = con.execute(
            monthly_query
        ).fetchdf()

        print(
            monthly.to_string(index=False),
            flush=True
        )

        monthly.to_csv(
            REPORT_DIR / "monthly_distribution.csv",
            index=False
        )

        # ======================================
        # 10. FINAL SUMMARY
        # ======================================

        print(
            "\n=== VALIDATION SUMMARY ===",
            flush=True
        )

        print(
            f"Total sessions: "
            f"{int(duration['total_sessions'].iloc[0]):,}"
        )

        print(
            f"Single-event sessions: "
            f"{int(duration['single_event_sessions'].iloc[0]):,}"
        )

        print(
            f"Sessions over 24h: "
            f"{int(duration['sessions_over_24h'].iloc[0]):,}"
        )

        print(
            f"Sessions with multiple users: "
            f"{multi_user_count:,}"
        )

        print(
            f"Exact duplicate rows: "
            f"{duplicate_count:,}"
        )

        print(
            "\nValidation completed successfully!",
            flush=True
        )

        print(
            f"Reports saved to: {REPORT_DIR}",
            flush=True
        )

    finally:
        con.close()


if __name__ == "__main__":
    validate()
