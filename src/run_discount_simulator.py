
import numpy as np
import pandas as pd

from config import PROJECT_ROOT, PROCESSED_DATA_DIR, REPORTS_DIR


TARGETABLE_SEGMENTS = {
    "Deal-responsive profitable",
    "Discount-dependent low-margin",
    "At-risk / low engagement",
}


def load_parquet(file_name: str) -> pd.DataFrame:
    """Load a processed Parquet file."""
    file_path = PROCESSED_DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Could not find {file_name}. "
            "Run the earlier build scripts first."
        )

    return pd.read_parquet(file_path)


def calculate_expected_metrics(
    dataframe: pd.DataFrame,
    discount_column: str,
) -> pd.DataFrame:
    """
    Calculate expected purchase probability and expected economics.

    Uses the constant-elasticity formula documented in:
    docs/elasticity_methodology.md
    """
    results = dataframe.copy()

    results["scenario_discount_pct"] = results[
        discount_column
    ]

    # Synthetic discounted price for one expected future order.
    results["expected_paid_merchandise_value"] = (
        results["average_baseline_merchandise_value"]
        * (1 - results["scenario_discount_pct"])
    )

    results["expected_discount_amount_per_order"] = (
        results["average_baseline_merchandise_value"]
        - results["expected_paid_merchandise_value"]
    )

    # Constant-elasticity demand multiplier.
    results["demand_multiplier"] = (
        (1 - results["scenario_discount_pct"])
        ** results["elasticity_base"]
    )

    # Purchase probability cannot be above 95%.
    results["expected_purchase_probability_90d"] = np.minimum(
        results["base_purchase_probability_90d"]
        * results["demand_multiplier"],
        0.95,
    )

    # Payment fee changes when discounted price changes.
    results["expected_payment_fee"] = (
        results["expected_paid_merchandise_value"]
        * 0.03
    )

    # Expected contribution margin if a purchase occurs.
    results["expected_margin_per_purchased_order"] = (
        results["expected_paid_merchandise_value"]
        + results["average_freight_value"]
        - results["average_estimated_cogs"]
        - results["expected_payment_fee"]
        - results["average_fulfillment_cost"]
    )

    # Expected contribution margin per eligible customer.
    results["expected_contribution_margin_per_customer"] = (
        results["expected_purchase_probability_90d"]
        * results["expected_margin_per_purchased_order"]
    )

    # Expected revenue per eligible customer.
    results["expected_revenue_per_customer"] = (
        results["expected_purchase_probability_90d"]
        * results["expected_paid_merchandise_value"]
    )

    # Expected discount cost per eligible customer.
    results["expected_discount_cost_per_customer"] = (
        results["expected_purchase_probability_90d"]
        * results["expected_discount_amount_per_order"]
    )

    return results


def main():
    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "\n--- RUNNING BASE-CASE DISCOUNT SIMULATOR ---\n"
    )

    # Load customer segments and historical order economics.
    customers = load_parquet(
        "customer_segments.parquet"
    )

    orders = load_parquet(
        "orders_enriched.parquet"
    )

    elasticity_path = (
        PROJECT_ROOT
        / "data"
        / "external"
        / "segment_elasticity_assumptions.csv"
    )

    if not elasticity_path.exists():
        raise FileNotFoundError(
            "segment_elasticity_assumptions.csv was not found. "
            "Complete Step 21 first."
        )

    elasticity = pd.read_csv(
        elasticity_path
    )

    # Use delivered historical orders to estimate a typical future order.
    delivered_orders = orders[
        orders["is_delivered"] == 1
    ].copy()

    customer_order_economics = (
        delivered_orders
        .groupby(
            "customer_unique_id",
            as_index=False,
        )
        .agg(
            average_baseline_merchandise_value=(
                "baseline_merchandise_value",
                "mean",
            ),
            average_freight_value=(
                "freight_revenue",
                "mean",
            ),
            average_estimated_cogs=(
                "estimated_cogs",
                "mean",
            ),
            average_fulfillment_cost=(
                "estimated_fulfillment_cost",
                "mean",
            ),
        )
    )

    simulator_base = customers.merge(
        customer_order_economics,
        on="customer_unique_id",
        how="inner",
        validate="1:1",
    )

    simulator_base = simulator_base.merge(
        elasticity,
        on="customer_segment",
        how="left",
        validate="m:1",
    )

    if simulator_base[
        "elasticity_base"
    ].isna().any():

        missing_segments = simulator_base.loc[
            simulator_base[
                "elasticity_base"
            ].isna(),
            "customer_segment",
        ].unique()

        raise ValueError(
            "Missing elasticity assumptions for: "
            + ", ".join(missing_segments)
        )

    # Segment-level historical 90-day repeat rate becomes base probability.
    eligible_for_90d = simulator_base[
        simulator_base[
            "has_90_day_observation_window"
        ] == 1
    ].copy()

    segment_base_probability = (
        eligible_for_90d
        .groupby(
            "customer_segment",
            as_index=False,
        )
        .agg(
            base_purchase_probability_90d=(
                "repeat_within_90_days",
                "mean",
            )
        )
    )

    overall_base_probability = (
        eligible_for_90d[
            "repeat_within_90_days"
        ].mean()
    )

    simulator_base = simulator_base.merge(
        segment_base_probability,
        on="customer_segment",
        how="left",
        validate="m:1",
    )

    simulator_base[
        "base_purchase_probability_90d"
    ] = (
        simulator_base[
            "base_purchase_probability_90d"
        ].fillna(
            overall_base_probability
        )
    )

    # ------------------------------------------------------------
    # Scenario 1: No offer.
    # ------------------------------------------------------------
    no_offer = simulator_base.copy()

    no_offer["scenario"] = "NO_OFFER"
    no_offer["candidate_discount_pct"] = 0.0
    no_offer["offer_sent"] = 0

    no_offer = calculate_expected_metrics(
        no_offer,
        discount_column="candidate_discount_pct",
    )

    no_offer_margin = (
        no_offer[
            [
                "customer_unique_id",
                "expected_contribution_margin_per_customer",
            ]
        ]
        .rename(
            columns={
                "expected_contribution_margin_per_customer":
                    "no_offer_expected_margin",
            }
        )
    )

    # ------------------------------------------------------------
    # Scenario 2: Blanket 30% discount.
    # ------------------------------------------------------------
    blanket_30 = simulator_base.copy()

    blanket_30["scenario"] = "BLANKET30"
    blanket_30["candidate_discount_pct"] = 0.30
    blanket_30["offer_sent"] = 1

    blanket_30 = calculate_expected_metrics(
        blanket_30,
        discount_column="candidate_discount_pct",
    )

    # ------------------------------------------------------------
    # Scenario 3: Targeted 15% discount.
    #
    # First, test a 15% offer for selected price-sensitive segments.
    # Then send it only when expected margin is higher than no offer.
    # ------------------------------------------------------------
    targeted_15 = simulator_base.copy()

    targeted_15["scenario"] = "TARGETED15"

    targeted_15["is_targetable_segment"] = (
        targeted_15[
            "customer_segment"
        ].isin(TARGETABLE_SEGMENTS)
    )

    # Respect the documented maximum-discount cap by segment.
    targeted_15[
        "candidate_discount_pct"
    ] = np.where(
        targeted_15[
            "is_targetable_segment"
        ],
        np.minimum(
            0.15,
            targeted_15[
                "maximum_discount_pct"
            ],
        ),
        0.0,
    )

    targeted_trial = calculate_expected_metrics(
        targeted_15,
        discount_column="candidate_discount_pct",
    )

    # Compare the targeted offer against the no-offer baseline.
    targeted_trial = targeted_trial.merge(
        no_offer_margin,
        on="customer_unique_id",
        how="left",
        validate="1:1",
    )

    targeted_trial[
        "expected_incremental_margin"
    ] = (
        targeted_trial[
            "expected_contribution_margin_per_customer"
        ]
        - targeted_trial[
            "no_offer_expected_margin"
        ]
    )

    # Offer is sent only when it is both targetable and margin-positive.
    targeted_trial["offer_sent"] = (
        targeted_trial[
            "is_targetable_segment"
        ]
        & (
            targeted_trial[
                "expected_incremental_margin"
            ] > 0
        )
    ).astype(int)

    targeted_trial[
        "candidate_discount_pct"
    ] = np.where(
        targeted_trial["offer_sent"] == 1,
        targeted_trial[
            "candidate_discount_pct"
        ],
        0.0,
    )

    # Recalculate expected economics using the final discount.
    targeted_15 = calculate_expected_metrics(
        targeted_trial,
        discount_column="candidate_discount_pct",
    )

    # ------------------------------------------------------------
    # FIX:
    #
    # targeted_15 already contains no_offer_expected_margin
    # because it was merged during the targeting decision.
    #
    # Therefore, do NOT merge no_offer_margin into the combined
    # results again. Instead, add the baseline column only to
    # scenarios that do not already contain it.
    # ------------------------------------------------------------

    # Remove the temporary targeting-only baseline from targeted_15
    # before combining all policies.
    #
    # The baseline will be added once, after concatenation.
    if "no_offer_expected_margin" in targeted_15.columns:
        targeted_15 = targeted_15.drop(
            columns=["no_offer_expected_margin"]
        )

    # Combine results from all three policies.
    simulator_results = pd.concat(
        [
            no_offer,
            blanket_30,
            targeted_15,
        ],
        ignore_index=True,
    )

    # Add the no-offer baseline exactly once to every scenario.
    simulator_results = simulator_results.merge(
        no_offer_margin,
        on="customer_unique_id",
        how="left",
        validate="m:1",
    )

    simulator_results[
        "incremental_margin_vs_no_offer"
    ] = (
        simulator_results[
            "expected_contribution_margin_per_customer"
        ]
        - simulator_results[
            "no_offer_expected_margin"
        ]
    )

    # Save detailed customer-level scenario results automatically.
    detailed_path = (
        PROCESSED_DATA_DIR
        / "discount_simulator_customer_results.parquet"
    )

    simulator_results.to_parquet(
        detailed_path,
        index=False,
    )

    # Create policy-level business summary automatically.
    summary = (
        simulator_results
        .groupby(
            "scenario",
            as_index=False,
        )
        .agg(
            eligible_customers=(
                "customer_unique_id",
                "count",
            ),
            customers_offered=(
                "offer_sent",
                "sum",
            ),
            expected_orders=(
                "expected_purchase_probability_90d",
                "sum",
            ),
            expected_synthetic_revenue=(
                "expected_revenue_per_customer",
                "sum",
            ),
            expected_discount_cost=(
                "expected_discount_cost_per_customer",
                "sum",
            ),
            expected_contribution_margin=(
                "expected_contribution_margin_per_customer",
                "sum",
            ),
            incremental_margin_vs_no_offer=(
                "incremental_margin_vs_no_offer",
                "sum",
            ),
        )
        .sort_values("scenario")
    )

    summary_path = (
        REPORTS_DIR
        / "discount_simulator_summary.csv"
    )

    summary.to_csv(
        summary_path,
        index=False,
    )

    # Save the exact assumptions used by this base-case run.
    assumption_columns = [
        "customer_segment",
        "elasticity_base",
        "maximum_discount_pct",
        "reason",
    ]

    assumptions_used = elasticity[
        assumption_columns
    ].copy()

    assumptions_path = (
        REPORTS_DIR
        / "discount_simulator_assumptions_used.csv"
    )

    assumptions_used.to_csv(
        assumptions_path,
        index=False,
    )

    print(
        f"Customers in simulator: "
        f"{len(simulator_base):,}"
    )

    print(
        f"Created: {detailed_path}"
    )

    print(
        f"Created: {summary_path}"
    )

    print(
        f"Created: {assumptions_path}"
    )

    print(
        "\n--- BASE-CASE SIMULATOR COMPLETE ---\n"
    )


if __name__ == "__main__":
    main()

