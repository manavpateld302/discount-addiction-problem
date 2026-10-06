import numpy as np
import pandas as pd

from config import PROJECT_ROOT, PROCESSED_DATA_DIR, REPORTS_DIR
from run_discount_simulator import (
    TARGETABLE_SEGMENTS,
    calculate_expected_metrics,
)


def load_parquet(file_name: str) -> pd.DataFrame:
    file_path = PROCESSED_DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Could not find {file_name}. "
            "Run the earlier build scripts first."
        )

    return pd.read_parquet(file_path)


def create_simulator_base() -> pd.DataFrame:
    customers = load_parquet("customer_segments.parquet")
    orders = load_parquet("orders_enriched.parquet")

    elasticity_path = (
        PROJECT_ROOT
        / "data"
        / "external"
        / "segment_elasticity_assumptions.csv"
    )

    if not elasticity_path.exists():
        raise FileNotFoundError(
            "segment_elasticity_assumptions.csv was not found."
        )

    elasticity = pd.read_csv(elasticity_path)

    delivered_orders = orders[
        orders["is_delivered"] == 1
    ].copy()

    customer_order_economics = (
        delivered_orders.groupby(
            "customer_unique_id",
            as_index=False,
        )
        .agg(
            average_baseline_merchandise_value=(
                "baseline_merchandise_value",
                "mean",
            ),
            average_freight_value=("freight_revenue", "mean"),
            average_estimated_cogs=("estimated_cogs", "mean"),
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

    if simulator_base["elasticity_base"].isna().any():
        missing_segments = simulator_base.loc[
            simulator_base["elasticity_base"].isna(),
            "customer_segment",
        ].unique()

        raise ValueError(
            "Missing elasticity assumptions for: "
            + ", ".join(missing_segments)
        )

    eligible_for_90d = simulator_base[
        simulator_base["has_90_day_observation_window"] == 1
    ].copy()

    segment_probability = (
        eligible_for_90d.groupby(
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

    overall_probability = eligible_for_90d[
        "repeat_within_90_days"
    ].mean()

    simulator_base = simulator_base.merge(
        segment_probability,
        on="customer_segment",
        how="left",
        validate="m:1",
    )

    simulator_base["base_purchase_probability_90d"] = (
        simulator_base["base_purchase_probability_90d"].fillna(
            overall_probability
        )
    )

    return simulator_base


def run_three_policies(simulator_base: pd.DataFrame) -> pd.DataFrame:

    # ================================================================
    # 1. NO OFFER
    # ================================================================

    no_offer = simulator_base.copy()

    no_offer["scenario"] = "NO_OFFER"
    no_offer["candidate_discount_pct"] = 0.0
    no_offer["offer_sent"] = 0

    no_offer = calculate_expected_metrics(
        no_offer,
        discount_column="candidate_discount_pct",
    )

    # Store only the baseline margin separately.
    no_offer_margin = no_offer[
        [
            "customer_unique_id",
            "expected_contribution_margin_per_customer",
        ]
    ].rename(
        columns={
            "expected_contribution_margin_per_customer":
                "no_offer_expected_margin"
        }
    )

    # ================================================================
    # 2. BLANKET 30%
    # ================================================================

    blanket = simulator_base.copy()

    blanket["scenario"] = "BLANKET30"
    blanket["candidate_discount_pct"] = 0.30
    blanket["offer_sent"] = 1

    blanket = calculate_expected_metrics(
        blanket,
        discount_column="candidate_discount_pct",
    )

    # ================================================================
    # 3. TARGETED 15%
    # ================================================================

    targeted = simulator_base.copy()

    targeted["scenario"] = "TARGETED15"

    targeted["is_targetable_segment"] = targeted[
        "customer_segment"
    ].isin(TARGETABLE_SEGMENTS)

    targeted["candidate_discount_pct"] = np.where(
        targeted["is_targetable_segment"],
        np.minimum(
            0.15,
            targeted["maximum_discount_pct"],
        ),
        0.0,
    )

    targeted_trial = calculate_expected_metrics(
        targeted,
        discount_column="candidate_discount_pct",
    )

    # Add baseline margin only for the targeting decision.
    targeted_trial = targeted_trial.merge(
        no_offer_margin,
        on="customer_unique_id",
        how="left",
        validate="1:1",
    )

    targeted_trial["expected_incremental_margin"] = (
        targeted_trial[
            "expected_contribution_margin_per_customer"
        ]
        - targeted_trial[
            "no_offer_expected_margin"
        ]
    )

    targeted_trial["offer_sent"] = (
        targeted_trial["is_targetable_segment"]
        & (
            targeted_trial["expected_incremental_margin"]
            > 0
        )
    ).astype(int)

    targeted_trial["candidate_discount_pct"] = np.where(
        targeted_trial["offer_sent"] == 1,
        targeted_trial["candidate_discount_pct"],
        0.0,
    )

    targeted = calculate_expected_metrics(
        targeted_trial,
        discount_column="candidate_discount_pct",
    )

    # Remove the temporary baseline column.
    if "no_offer_expected_margin" in targeted.columns:
        targeted = targeted.drop(
            columns=["no_offer_expected_margin"]
        )

    # ================================================================
    # COMBINE POLICIES
    # ================================================================

    results = pd.concat(
        [
            no_offer,
            blanket,
            targeted,
        ],
        ignore_index=True,
    )

    # ================================================================
    # ADD ONE CLEAN BASELINE COLUMN
    # ================================================================

    results = results.merge(
        no_offer_margin,
        on="customer_unique_id",
        how="left",
        validate="m:1",
    )

    results["incremental_margin_vs_no_offer"] = (
        results[
            "expected_contribution_margin_per_customer"
        ]
        - results[
            "no_offer_expected_margin"
        ]
    )

    return results


def main():

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "\n--- RUNNING SIMULATOR SENSITIVITY ANALYSIS ---\n"
    )

    simulator_base = create_simulator_base()

    elasticity_scenarios = {
        "Conservative": "elasticity_conservative",
        "Base": "elasticity_base",
        "Optimistic": "elasticity_optimistic",
    }

    all_summaries = []

    for scenario_name, elasticity_column in (
        elasticity_scenarios.items()
    ):

        print(
            f"Running elasticity scenario: "
            f"{scenario_name}"
        )

        scenario_base = simulator_base.copy()

        # The calculation function expects elasticity_base.
        scenario_base["elasticity_base"] = (
            scenario_base[elasticity_column]
        )

        policy_results = run_three_policies(
            scenario_base
        )

        policy_summary = (
            policy_results.groupby(
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
        )

        policy_summary[
            "elasticity_scenario"
        ] = scenario_name

        all_summaries.append(
            policy_summary
        )

    sensitivity_results = pd.concat(
        all_summaries,
        ignore_index=True,
    )

    sensitivity_results = sensitivity_results[
        [
            "elasticity_scenario",
            "scenario",
            "eligible_customers",
            "customers_offered",
            "expected_orders",
            "expected_synthetic_revenue",
            "expected_discount_cost",
            "expected_contribution_margin",
            "incremental_margin_vs_no_offer",
        ]
    ]

    output_path = (
        REPORTS_DIR
        / "discount_simulator_sensitivity.csv"
    )

    sensitivity_results.to_csv(
        output_path,
        index=False,
    )

    print(
        f"\nCreated: {output_path}"
    )

    print(
        "\n--- SENSITIVITY ANALYSIS COMPLETE ---\n"
    )


if __name__ == "__main__":
    main()