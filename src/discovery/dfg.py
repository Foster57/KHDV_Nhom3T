
from pathlib import Path
import duckdb
import pandas as pd
import plotly.graph_objects as go


# ==========================================
# CONFIGURATION
# ==========================================

INPUT_PATH = Path("data/processed/event_log.parquet")
OUTPUT_DIR = Path("data/processed/discovery")
TEMP_DIR = Path("data/interim/duckdb_dfg_tmp")

MAX_GAP_SECONDS = 1800


def sql_path(path):
    return (
        str(path.resolve())
        .replace("\\", "/")
        .replace("'", "''")
    )


def build_dfg():

    if not INPUT_PATH.exists():
        raise FileNotFoundError(INPUT_PATH)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()

    try:
        con.execute("SET memory_limit = '8GB'")
        con.execute("SET threads = 4")

        con.execute(
            f"SET temp_directory = '{sql_path(TEMP_DIR)}'"
        )

        print("STEP 1: Loading Event Log...", flush=True)

        con.execute(f"""
            CREATE VIEW events AS
            SELECT
                user_session,
                event_time,
                event_type,
                product_id
            FROM read_parquet('{sql_path(INPUT_PATH)}')
        """)

        # ======================================
        # STEP 2: NODE FREQUENCIES
        # ======================================

        print("STEP 2: Counting activities...", flush=True)

        nodes = con.execute("""
            SELECT
                event_type AS activity,
                COUNT(*) AS frequency,
                COUNT(DISTINCT user_session)
                    AS sessions
            FROM events
            GROUP BY event_type
            ORDER BY frequency DESC
        """).fetchdf()

        nodes.to_csv(
            OUTPUT_DIR / "dfg_nodes.csv",
            index=False
        )

        # ======================================
        # STEP 3: DIRECTLY-FOLLOWS GRAPH
        # ======================================

        print("STEP 3: Discovering DFG...", flush=True)

        edges = con.execute("""
            WITH ordered AS (
                SELECT
                    user_session,
                    event_type AS source,

                    LEAD(event_type) OVER (
                        PARTITION BY user_session
                        ORDER BY
                            event_time,
                            event_type,
                            product_id
                    ) AS target,

                    event_time AS source_time,

                    LEAD(event_time) OVER (
                        PARTITION BY user_session
                        ORDER BY
                            event_time,
                            event_type,
                            product_id
                    ) AS target_time

                FROM events
            ),

            transitions AS (
                SELECT
                    source,
                    target,

                    DATE_DIFF(
                        'second',
                        source_time,
                        target_time
                    ) AS gap_seconds

                FROM ordered
                WHERE target IS NOT NULL
            )

            SELECT
                source,
                target,
                COUNT(*) AS frequency,

                ROUND(
                    AVG(gap_seconds), 2
                ) AS avg_gap_seconds,

                MEDIAN(gap_seconds)
                    AS median_gap_seconds,

                COUNT(*) FILTER (
                    WHERE gap_seconds <= 1800
                ) AS transitions_within_30min

            FROM transitions
            GROUP BY source, target
            ORDER BY frequency DESC
        """).fetchdf()

        edges.to_csv(
            OUTPUT_DIR / "dfg_edges.csv",
            index=False
        )

        print("\n=== DFG RESULTS ===", flush=True)
        print(edges.to_string(index=False))

        # ======================================
        # STEP 4: VISUALIZATION
        # ======================================

        print("\nSTEP 4: Creating visualization...", flush=True)

        activities = nodes["activity"].tolist()

        activity_index = {
            name: i
            for i, name in enumerate(activities)
        }

        fig = go.Figure(
            data=[
                go.Sankey(
                    arrangement="snap",
                    node=dict(
                        pad=25,
                        thickness=22,
                        label=activities
                    ),
                    link=dict(
                        source=[
                            activity_index[x]
                            for x in edges["source"]
                        ],
                        target=[
                            activity_index[x]
                            for x in edges["target"]
                        ],
                        value=edges["frequency"].tolist(),
                        customdata=[
                            f"{int(x):,} transitions"
                            for x in edges["frequency"]
                        ],
                        hovertemplate=(
                            "%{source.label} → "
                            "%{target.label}<br>"
                            "%{customdata}<extra></extra>"
                        )
                    )
                )
            ]
        )

        fig.update_layout(
            title="Customer Journey - Directly Follows Graph",
            font_size=13,
            height=650
        )

        html_path = OUTPUT_DIR / "dfg_visualization.html"

        fig.write_html(
            str(html_path),
            include_plotlyjs=True
        )

        print("\nSaved outputs:")
        print(OUTPUT_DIR / "dfg_nodes.csv")
        print(OUTPUT_DIR / "dfg_edges.csv")
        print(html_path)

        print("\nDFG completed successfully!")

    finally:
        con.close()


if __name__ == "__main__":
    build_dfg()
