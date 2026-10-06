import numpy as np
import pandas as pd

from config import PROCESSED_DATA_DIR, REPORTS_DIR


def create_quintile_score(
    values: pd.Series,
    higher_is_better: bool,
) -> pd.Series:
    """
    Convert a numeric column into a score from 1 to 5.

    A score of 5 always means better performance.
    For recency, fewer days is better.
    """
    ranked_values = values.rank(method="first", ascending=True)

    score = pd.qcut(
        ranked_values,
        q=5,
        labels=False,
    ) + 1

    if higher_is_better:
        return score.astype(int)

    return (6 - score).astype(int)


def assign_segment(
    row: pd.Series,
    median_average_order_margin: float,
) -> str:
    """Assign one business segment using documented priority rules."""

    # Rule 1: New customer.
    if row["delivered_order_count"] == 1:
        return "New / one-order customer"

    # Rule 2: At-risk repeat customer.
    if row["recency_score"] <= 2 and row["frequency_score"] <= 2:
        return "At-risk / low engagement"

    # Rule 3: Loyal full-price customer.
    if (
        row["frequency_score"] >= 4
        and row["monetary_score"] >= 3
        and row["full_price_order_share"] >= 0.80
    ):
        return "Full-price loyalist"

    # Rule 4: High discount exposure with weak margin.
    if (
        row["discount_dependency_score"] >= 60
        and row["full_price_order_share"] <= 0.50
        and row["average_order_margin"] < median_average_order_margin
    ):
        return "Discount-dependent low-margin"

    # Rule 5: Discount user with acceptable economics.
    if (
        row["discounted_order_count"] > 0
        and row["average_order_margin"] >= median_average_order_margin
    ):
        return "Deal-responsive profitable"

    # Rule 6: All remaining repeat customers.
    return "Repeat generalist"


def main():
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    customer_file = PROCESSED_DATA_DIR / "customer_features.parquet"

    if not customer_file.exists():
        raise FileNotFoundError(
            "customer_features.parquet was not found. "
            "Run build_customer_features.py first."
        )

    customers = pd.read_parquet(customer_file).copy()

    print("\n--- BUILDING CUSTOMER SEGMENTS ---\n")

    # Calculate the share of each customer's orders that were full-price.
    customers["full_price_order_share"] = np.where(
        customers["delivered_order_count"] > 0,
        customers["full_price_order_count"]
        / customers["delivered_order_count"],
        0,
    )

    # RFM scores: all scores range from 1 to 5.
    customers["recency_score"] = create_quintile_score(
        customers["recency_days"],
        higher_is_better=False,
    )

    customers["frequency_score"] = create_quintile_score(
        customers["delivered_order_count"],
        higher_is_better=True,
    )

    customers["monetary_score"] = create_quintile_score(
        customers["contribution_margin_total"],
        higher_is_better=True,
    )

    customers["rfm_score"] = (
        customers["recency_score"].astype(str)
        + customers["frequency_score"].astype(str)
        + customers["monetary_score"].astype(str)
    )

    # Use the portfolio median as the profitability threshold.
    median_average_order_margin = customers[
        "average_order_margin"
    ].median()

    customers["customer_segment"] = customers.apply(
        assign_segment,
        axis=1,
        median_average_order_margin=median_average_order_margin,
    )

    # Add a simpler discount-responsiveness label.
    customers["discount_responsiveness_tier"] = pd.cut(
        customers["discount_dependency_score"],
        bins=[-0.01, 29.99, 59.99, 100],
        labels=[
            "Discount-indifferent",
            "Discount-responsive",
            "Discount-dependent",
        ],
    )

    # Save the enriched customer-segment table automatically.
    output_path = PROCESSED_DATA_DIR / "customer_segments.parquet"
    customers.to_parquet(output_path, index=False)

    # Create an automatic segment summary for review and dashboard use.
    segment_summary = (
        customers.groupby("customer_segment", as_index=False)
        .agg(
            customer_count=("customer_unique_id", "count"),
            average_delivered_orders=("delivered_order_count", "mean"),
            average_discount_dependency_score=(
                "discount_dependency_score",
                "mean",
            ),
            average_full_price_order_share=(
                "full_price_order_share",
                "mean",
            ),
            average_order_margin=("average_order_margin", "mean"),
            total_contribution_margin=(
                "contribution_margin_total",
                "sum",
            ),
            average_realized_clv_180=("realized_clv_180", "mean"),
        )
        .sort_values(
            "total_contribution_margin",
            ascending=False,
        )
    )

    summary_path = REPORTS_DIR / "segment_summary.csv"
    segment_summary.to_csv(summary_path, index=False)

    print(f"Median average order margin: R${median_average_order_margin:,.2f}")
    print(f"Created: {output_path}")
    print(f"Created: {summary_path}")
    print("\n--- CUSTOMER SEGMENTATION COMPLETE ---\n")


if __name__ == "__main__":
    main()