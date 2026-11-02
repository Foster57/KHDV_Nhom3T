
from pathlib import Path
import json
import pandas as pd


BASE = Path("data/processed")

FUNNEL = BASE / "journey/funnel_stages.csv"
PERFORMANCE = BASE / "performance/performance_within_24h.csv"
CLUSTERS = BASE / "ml/cluster_profiles.csv"
MODEL = BASE / "ml/decision_tree_metrics.csv"

OUTPUT = BASE / "recommendations"


def add_recommendation(
    items, rule_id, title, evidence,
    interpretation, action, validation,
    priority
):
    items.append({
        "rule_id": rule_id,
        "title": title,
        "evidence": evidence,
        "interpretation": interpretation,
        "recommended_action": action,
        "validation_plan": validation,
        "priority": priority,
        "recommendation_type": "hypothesis_to_test"
    })


def run():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    for path in [FUNNEL, PERFORMANCE, CLUSTERS, MODEL]:
        if not path.exists():
            raise FileNotFoundError(
                f"Missing input: {path}"
            )

    print("STEP 1: Loading analytical results...", flush=True)

    funnel = pd.read_csv(FUNNEL)
    performance = pd.read_csv(PERFORMANCE)
    clusters = pd.read_csv(CLUSTERS)
    model = pd.read_csv(MODEL)

    recommendations = []

    # ==========================================
    # RULE 1: VIEW -> CART
    # ==========================================

    cart_stage = funnel.loc[
        funnel["stage"] == "Cart after View"
    ]

    if not cart_stage.empty:
        conversion = float(
            cart_stage.iloc[0][
                "conversion_from_previous_pct"
            ]
        )

        if conversion < 20:
            add_recommendation(
                recommendations,
                "R01",
                "Investigate View-to-Cart drop-off",
                f"View-to-Cart conversion: {conversion:.2f}%",
                (
                    "A relatively small share of sessions "
                    "with View reaches Cart afterward. "
                    "This does not identify the cause."
                ),
                (
                    "Review product-page information, "
                    "add-to-cart visibility, and product "
                    "availability. Prioritize usability "
                    "testing before making changes."
                ),
                (
                    "Compare product-page behavior and "
                    "run an A/B test on a selected change. "
                    "Track ordered View-to-Cart conversion."
                ),
                "high"
            )

    # ==========================================
    # RULE 2: CART -> PURCHASE
    # ==========================================

    purchase_stage = funnel.loc[
        funnel["stage"] == "Purchase after Cart"
    ]

    if not purchase_stage.empty:
        conversion = float(
            purchase_stage.iloc[0][
                "conversion_from_previous_pct"
            ]
        )

        if conversion < 20:
            add_recommendation(
                recommendations,
                "R02",
                "Investigate Cart-to-Purchase drop-off",
                f"Cart-to-Purchase conversion: {conversion:.2f}%",
                (
                    "Many sessions reaching Cart after View "
                    "do not have a later recorded Purchase."
                ),
                (
                    "Investigate shipping costs, checkout "
                    "usability, payment methods and stock "
                    "availability using additional data."
                ),
                (
                    "Collect checkout-stage events and "
                    "test one intervention at a time. "
                    "Measure Cart-to-Purchase conversion."
                ),
                "high"
            )

    # ==========================================
    # RULE 3: PERFORMANCE
    # ==========================================

    perf_row = performance.loc[
        performance["transition"] == "Cart to Purchase"
    ]

    if not perf_row.empty:
        median_seconds = float(
            perf_row.iloc[0]["median_seconds_within_24h"]
        )

        if median_seconds > 600:
            add_recommendation(
                recommendations,
                "R03",
                "Investigate Cart-to-Purchase duration",
                (
                    "Median Cart-to-Purchase duration "
                    f"within 24h: {median_seconds:.0f} seconds"
                ),
                (
                    "The observed interval is relatively "
                    "long under the configured 10-minute "
                    "screening threshold. It is not direct "
                    "evidence of checkout delay."
                ),
                (
                    "Instrument checkout steps and review "
                    "where users spend time before purchase."
                ),
                (
                    "Measure step-level checkout duration "
                    "and completion rate after instrumentation."
                ),
                "medium"
            )

    # ==========================================
    # RULE 4: CLUSTER DIFFERENCES
    # ==========================================

    if len(clusters) >= 2:
        rates = clusters[
            "purchase_session_rate"
        ].astype(float)

        difference = rates.max() - rates.min()

        if difference >= 0.10:
            add_recommendation(
                recommendations,
                "R04",
                "Study differences between session segments",
                (
                    "Purchase-session-rate difference "
                    f"between clusters: {difference:.1%}"
                ),
                (
                    "Session clusters have different "
                    "observed purchase rates. Because "
                    "purchase counts were clustering "
                    "features, this is descriptive rather "
                    "than predictive evidence."
                ),
                (
                    "Compare behavioral patterns and "
                    "product categories across clusters. "
                    "Do not target customers using these "
                    "cluster labels without further study."
                ),
                (
                    "Validate segment stability on "
                    "another period and test whether "
                    "pre-purchase features can reproduce "
                    "useful segments."
                ),
                "medium"
            )

    # ==========================================
    # RULE 5: PREDICTIVE MODEL QUALITY
    # ==========================================

    if not model.empty:
        roc_auc = float(model.iloc[0]["roc_auc"])

        if roc_auc < 0.60:
            add_recommendation(
                recommendations,
                "R05",
                "Improve predictive model before deployment",
                f"Decision Tree ROC-AUC: {roc_auc:.4f}",
                (
                    "The model has weak discrimination "
                    "and should not drive automated "
                    "customer targeting."
                ),
                (
                    "Add pre-decision product, price and "
                    "behavioral features. Compare against "
                    "a simple baseline and evaluate on "
                    "a later time period."
                ),
                (
                    "Reassess ROC-AUC, average precision, "
                    "calibration and business utility "
                    "on a held-out test set."
                ),
                "high"
            )

    # ==========================================
    # EXPORT
    # ==========================================

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2
    }

    recommendations.sort(
        key=lambda x: priority_order.get(
            x["priority"], 99
        )
    )

    df = pd.DataFrame(recommendations)

    df.to_csv(
        OUTPUT / "recommendations.csv",
        index=False,
        encoding="utf-8-sig"
    )

    with open(
        OUTPUT / "recommendations.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            recommendations,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\n=== RECOMMENDATIONS ===")

    if df.empty:
        print("No rules triggered.")
    else:
        print(
            df[
                ["rule_id", "title", "priority"]
            ].to_string(index=False)
        )

    print("\nRecommendation Engine completed!")
    print(f"Outputs saved to: {OUTPUT}")


if __name__ == "__main__":
    run()
