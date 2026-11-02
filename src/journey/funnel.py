
from pathlib import Path
import duckdb

INPUT_PATH = Path("data/processed/event_log.parquet")
OUTPUT_DIR = Path("data/processed/journey")
TEMP_DIR = Path("data/interim/duckdb_funnel_tmp")


def sql_path(path):
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def build_funnel():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing: {INPUT_PATH}")

    con = duckdb.connect()

    try:
        con.execute("SET memory_limit='8GB'")
        con.execute("SET threads=4")
        con.execute(
            f"SET temp_directory='{sql_path(TEMP_DIR)}'"
        )

        print("STEP 1: Loading events...", flush=True)

        con.execute(f"""
            CREATE VIEW events AS
            SELECT
                user_session,
                event_time,
                event_type
            FROM read_parquet('{sql_path(INPUT_PATH)}')
        """)

        # Presence funnel: a session contains each event type.
        print("STEP 2: Computing session funnel...", flush=True)

        con.execute("""
            CREATE TEMP TABLE session_flags AS
            SELECT
                user_session,
                COUNT(*) AS n_events,
                COUNT(*) FILTER (
                    WHERE event_type = 'view'
                ) AS n_views,
                COUNT(*) FILTER (
                    WHERE event_type = 'cart'
                ) AS n_carts,
                COUNT(*) FILTER (
                    WHERE event_type = 'purchase'
                ) AS n_purchases
            FROM events
            GROUP BY user_session
        """)

        summary = con.execute("""
            SELECT
                COUNT(*) AS total_sessions,
                COUNT(*) FILTER (
                    WHERE n_views > 0
                ) AS view_sessions,
                COUNT(*) FILTER (
                    WHERE n_carts > 0
                ) AS cart_sessions,
                COUNT(*) FILTER (
                    WHERE n_purchases > 0
                ) AS purchase_sessions,
                COUNT(*) FILTER (
                    WHERE n_views > 0 AND n_carts > 0
                ) AS view_and_cart_sessions,
                COUNT(*) FILTER (
                    WHERE n_views > 0
                      AND n_carts > 0
                      AND n_purchases > 0
                ) AS all_three_sessions
            FROM session_flags
        """).fetchdf()

        summary.to_csv(
            OUTPUT_DIR / "funnel_summary.csv",
            index=False
        )

        print("\n=== SESSION FUNNEL ===")
        print(summary.to_string(index=False))

        # Ordered funnel using event timestamps.
        # Equal timestamps are not assumed to have a known order.
        print(
            "\nSTEP 3: Computing ordered funnel...",
            flush=True
        )

        ordered = con.execute("""
            WITH first_view AS (
                SELECT
                    user_session,
                    MIN(event_time) AS view_time
                FROM events
                WHERE event_type = 'view'
                GROUP BY user_session
            ),
            first_cart_after_view AS (
                SELECT
                    e.user_session,
                    MIN(e.event_time) AS cart_time
                FROM events e
                JOIN first_view v
                    ON e.user_session = v.user_session
                WHERE e.event_type = 'cart'
                  AND e.event_time > v.view_time
                GROUP BY e.user_session
            ),
            first_purchase_after_cart AS (
                SELECT
                    e.user_session,
                    MIN(e.event_time) AS purchase_time
                FROM events e
                JOIN first_cart_after_view c
                    ON e.user_session = c.user_session
                WHERE e.event_type = 'purchase'
                  AND e.event_time > c.cart_time
                GROUP BY e.user_session
            )
            SELECT
                (SELECT COUNT(*) FROM session_flags)
                    AS total_sessions,
                (SELECT COUNT(*) FROM first_view)
                    AS reached_view,
                (SELECT COUNT(*) FROM first_cart_after_view)
                    AS reached_cart_after_view,
                (SELECT COUNT(*) FROM first_purchase_after_cart)
                    AS reached_purchase_after_cart
        """).fetchdf()

        ordered.to_csv(
            OUTPUT_DIR / "ordered_funnel.csv",
            index=False
        )

        print("\n=== ORDERED FUNNEL ===")
        print(ordered.to_string(index=False))

        # Dashboard-friendly stage table
        print("\nSTEP 4: Exporting dashboard data...", flush=True)

        values = ordered.iloc[0]
        total = int(values["total_sessions"])

        stages = [
            ("View", int(values["reached_view"])),
            ("Cart after View", int(values["reached_cart_after_view"])),
            (
                "Purchase after Cart",
                int(values["reached_purchase_after_cart"])
            ),
        ]

        import pandas as pd

        rows = []
        previous = None

        for stage, count in stages:
            rows.append({
                "stage": stage,
                "sessions": count,
                "percentage_of_all_sessions": round(
                    count / total * 100, 2
                ) if total else 0,
                "conversion_from_previous_pct": round(
                    count / previous * 100, 2
                ) if previous else None
            })
            previous = count

        stage_df = pd.DataFrame(rows)
        stage_df.to_csv(
            OUTPUT_DIR / "funnel_stages.csv",
            index=False
        )

        print("\n=== FUNNEL STAGES ===")
        print(stage_df.to_string(index=False))

        print("\nFunnel Analysis completed successfully!")
        print(f"Outputs saved to: {OUTPUT_DIR}")

    finally:
        con.close()


if __name__ == "__main__":
    build_funnel()
