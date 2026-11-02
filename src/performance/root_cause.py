
from pathlib import Path
import duckdb

INPUT = Path("data/processed/event_log.parquet")
OUTPUT = Path("data/processed/performance")
TEMP = Path("data/interim/duckdb_performance_tmp")


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

        print("STEP 1: Loading events...", flush=True)

        con.execute(f"""
            CREATE VIEW events AS
            SELECT
                user_session,
                event_time,
                event_type
            FROM read_parquet('{sql_path(INPUT)}')
            WHERE event_type IN ('view', 'cart', 'purchase')
        """)

        print("STEP 2: Finding funnel timestamps...", flush=True)

        con.execute("""
            CREATE TEMP TABLE first_view AS
            SELECT user_session, MIN(event_time) AS view_time
            FROM events
            WHERE event_type = 'view'
            GROUP BY user_session
        """)

        con.execute("""
            CREATE TEMP TABLE first_cart AS
            SELECT
                e.user_session,
                v.view_time,
                MIN(e.event_time) AS cart_time
            FROM events e
            JOIN first_view v USING (user_session)
            WHERE e.event_type = 'cart'
              AND e.event_time > v.view_time
            GROUP BY e.user_session, v.view_time
        """)

        con.execute("""
            CREATE TEMP TABLE first_purchase AS
            SELECT
                e.user_session,
                c.cart_time,
                MIN(e.event_time) AS purchase_time
            FROM events e
            JOIN first_cart c USING (user_session)
            WHERE e.event_type = 'purchase'
              AND e.event_time > c.cart_time
            GROUP BY e.user_session, c.cart_time
        """)

        print("STEP 3: Computing stage durations...", flush=True)

        con.execute("""
            CREATE TEMP TABLE durations AS
            SELECT
                'View to Cart' AS transition,
                DATE_DIFF(
                    'second', view_time, cart_time
                ) AS duration_seconds
            FROM first_cart

            UNION ALL

            SELECT
                'Cart to Purchase' AS transition,
                DATE_DIFF(
                    'second', cart_time, purchase_time
                ) AS duration_seconds
            FROM first_purchase
        """)

        summary = con.execute("""
            SELECT
                transition,
                COUNT(*) AS sessions,
                ROUND(AVG(duration_seconds), 2)
                    AS avg_seconds,
                MEDIAN(duration_seconds)
                    AS median_seconds,
                ROUND(
                    QUANTILE_CONT(duration_seconds, 0.90), 2
                ) AS p90_seconds,
                COUNT(*) FILTER (
                    WHERE duration_seconds > 86400
                ) AS over_24h
            FROM durations
            GROUP BY transition
            ORDER BY transition
        """).fetchdf()

        summary.to_csv(
            OUTPUT / "performance_summary.csv",
            index=False
        )

        print("\n=== PERFORMANCE SUMMARY ===")
        print(summary.to_string(index=False))

        print("\nSTEP 4: Computing 24h sensitivity...", flush=True)

        bounded = con.execute("""
            SELECT
                transition,
                COUNT(*) AS sessions_within_24h,
                ROUND(AVG(duration_seconds), 2)
                    AS avg_seconds_within_24h,
                MEDIAN(duration_seconds)
                    AS median_seconds_within_24h,
                ROUND(
                    QUANTILE_CONT(duration_seconds, 0.90), 2
                ) AS p90_seconds_within_24h
            FROM durations
            WHERE duration_seconds <= 86400
            GROUP BY transition
            ORDER BY transition
        """).fetchdf()

        bounded.to_csv(
            OUTPUT / "performance_within_24h.csv",
            index=False
        )

        print("\n=== PERFORMANCE WITHIN 24H ===")
        print(bounded.to_string(index=False))

        print("\nPerformance Analysis completed!")
        print(f"Outputs saved to: {OUTPUT}")

    finally:
        con.close()


if __name__ == "__main__":
    run()
