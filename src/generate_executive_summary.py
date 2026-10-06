import pandas as pd

from config import REPORTS_DIR


def load_csv(file_name: str) -> pd.DataFrame:
    """Load one report CSV."""
    file_path = REPORTS_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Could not find {file_name}. "
            "Complete the previous analysis steps first."
        )

    return pd.read_csv(file_path)


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    simulator = load_csv("discount_simulator_summary.csv")
    segments = load_csv("segment_economics_summary.csv")
    cohorts = load_csv("first_order_cohort_summary.csv")

    # Find the policy with the highest estimated incremental margin.
    recommended_policy = simulator.loc[
        simulator["incremental_margin_vs_no_offer"].idxmax()
    ]

    # Find the segment with the largest total contribution margin.
    top_margin_segment = segments.loc[
        segments["total_contribution_margin"].idxmax()
    ]

    # Get first-order cohort values, when available.
    full_price_cohort = cohorts[
        cohorts["first_order_discount_band"] == "0% (Full price)"
    ]

    discounted_cohort = cohorts[
        cohorts["first_order_discount_band"] != "0% (Full price)"
    ]

    if not full_price_cohort.empty:
        full_price_repeat_rate = (
            full_price_cohort.iloc[0]["repeat_rate_180_days"]
        )

        full_price_clv = (
            full_price_cohort.iloc[0]["average_realized_clv_180"]
        )
    else:
        full_price_repeat_rate = None
        full_price_clv = None

    if not discounted_cohort.empty:
        weighted_discount_repeat_rate = (
            (
                discounted_cohort["repeat_rate_180_days"]
                * discounted_cohort["customer_count"]
            ).sum()
            / discounted_cohort["customer_count"].sum()
        )

        weighted_discount_clv = (
            (
                discounted_cohort["average_realized_clv_180"]
                * discounted_cohort["customer_count"]
            ).sum()
            / discounted_cohort["customer_count"].sum()
        )
    else:
        weighted_discount_repeat_rate = None
        weighted_discount_clv = None

    simulator_display = simulator[
        [
            "scenario",
            "customers_offered",
            "expected_orders",
            "expected_discount_cost",
            "expected_contribution_margin",
            "incremental_margin_vs_no_offer",
        ]
    ].copy()

    simulator_display = simulator_display.round(2)

    segment_display = segments[
        [
            "customer_segment",
            "customer_count",
            "average_discount_dependency_score",
            "average_order_margin",
            "total_contribution_margin",
        ]
    ].copy()

    segment_display = segment_display.round(2)

    cohort_display = cohorts[
        [
            "first_order_discount_band",
            "customer_count",
            "repeat_rate_180_days",
            "average_realized_clv_180",
        ]
    ].copy()

    cohort_display["repeat_rate_180_days"] = (
        cohort_display["repeat_rate_180_days"] * 100
    ).round(2)

    cohort_display["average_realized_clv_180"] = (
        cohort_display["average_realized_clv_180"].round(2)
    )

    summary_lines = [
        "# Executive Summary Draft",
        "",
        "## Business question",
        "",
        "Do discounts create incremental long-term customer value, or do they primarily subsidize purchases that would otherwise happen at full price?",
        "",
        "## Draft recommendation",
        "",
        f"Under the base-case scenario, **{recommended_policy['scenario']}** produces the highest estimated incremental contribution margin versus no offer.",
        "",
        f"- Expected incremental margin versus no offer: **R${recommended_policy['incremental_margin_vs_no_offer']:,.2f}**",
        f"- Expected discount cost: **R${recommended_policy['expected_discount_cost']:,.2f}**",
        f"- Customers offered: **{int(recommended_policy['customers_offered']):,}**",
        "",
        "This recommendation should be treated as a scenario-based decision input and validated with a randomized holdout experiment.",
        "",
        "## First-order cohort comparison",
        "",
    ]

    if full_price_repeat_rate is not None:
        summary_lines.extend(
            [
                f"- Full-price first-order cohort: **{full_price_repeat_rate:.2%}** 180-day repeat rate; **R${full_price_clv:,.2f}** average realized 180-day CLV.",
                f"- Discounted first-order cohorts combined: **{weighted_discount_repeat_rate:.2%}** 180-day repeat rate; **R${weighted_discount_clv:,.2f}** average realized 180-day CLV.",
                "",
            ]
        )

    summary_lines.extend(
        [
            "## Most valuable segment",
            "",
            f"**{top_margin_segment['customer_segment']}** generates the largest total estimated contribution margin:",
            "",
            f"- Customers: **{int(top_margin_segment['customer_count']):,}**",
            f"- Average order margin: **R${top_margin_segment['average_order_margin']:,.2f}**",
            f"- Total contribution margin: **R${top_margin_segment['total_contribution_margin']:,.2f}**",
            "",
            "## Simulator results",
            "",
            simulator_display.to_markdown(index=False),
            "",
            "## Segment economics",
            "",
            segment_display.to_markdown(index=False),
            "",
            "## First-order cohort results",
            "",
            cohort_display.to_markdown(index=False),
            "",
            "## Key limitations",
            "",
            "- Olist does not contain observed historical promotion campaigns, true product cost, or explicit return events.",
            "- Discount, promotion, and margin fields are documented synthetic/estimated scenario fields.",
            "- The cohort and regression outputs are descriptive; they do not establish causal discount impact.",
            "- The simulator depends on transparent elasticity assumptions and should be tested through a real randomized experiment.",
            "",
            "## Recommended next action",
            "",
            "Run a randomized test with no-offer control, 30% blanket treatment, 15% targeted treatment, and a targeted holdout. Use incremental 90-day contribution margin per eligible customer as the primary decision metric.",
        ]
    )

    output_path = REPORTS_DIR / "executive_summary_draft.md"

    output_path.write_text(
        "\n".join(summary_lines),
        encoding="utf-8",
    )

    print(f"Created: {output_path}")


if __name__ == "__main__":
    main()