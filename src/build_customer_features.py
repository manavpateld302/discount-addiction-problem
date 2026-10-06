import numpy as np
import pandas as pd

from config import PROCESSED_DATA_DIR, REPORTS_DIR


def load_table(file_name: str) -> pd.DataFrame:
    """Load a processed Parquet table."""
    file_path = PROCESSED_DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Could not find {file_name}. Run the previous build scripts first."
        )

    return pd.read_parquet(file_path)


def calculate_repeat_metrics(
    delivered_orders: pd.DataFrame,
    analysis_end_date: pd.Timestamp,
) -> pd.DataFrame:
    """
    Calculate repeat-purchase and realized CLV metrics.

    A customer receives a 180-day metric only if their first order
    occurred at least 180 days before the final observed order date.
    """
    transactions = delivered_orders.copy()

    transactions = transactions.sort_values(
        ["customer_unique_id", "order_purchase_timestamp", "order_id"]
    )

    transactions["purchase_sequence"] = (
        transactions.groupby("customer_unique_id").cumcount() + 1
    )

    transactions["first_purchase_date"] = transactions.groupby(
        "customer_unique_id"
    )["order_purchase_timestamp"].transform("min")

    transactions["days_from_first_purchase"] = (
        transactions["order_purchase_timestamp"]
        - transactions["first_purchase_date"]
    ).dt.total_seconds() / 86400

    # Find each customer's second delivered purchase, if it exists.
    second_orders = transactions[
        transactions["purchase_sequence"] == 2
    ][
        [
            "customer_unique_id",
            "order_purchase_timestamp",
            "promotion_id",
        ]
    ].rename(
        columns={
            "order_purchase_timestamp": "second_purchase_date",
            "promotion_id": "second_purchase_promotion_id",
        }
    )

    # Repeat orders mean every delivered purchase after the first one.
    repeat_orders = transactions[
        transactions["purchase_sequence"] > 1
    ].copy()

    repeat_orders["is_discounted_repeat_order"] = (
        repeat_orders["discount_depth"] > 0
    ).astype(int)

    repeat_summary = (
        repeat_orders.groupby("customer_unique_id", as_index=False)
        .agg(
            repeat_order_count=("order_id", "count"),
            discounted_repeat_order_count=(
                "is_discounted_repeat_order",
                "sum",
            ),
        )
    )

    # Create observed 30-, 90-, and 180-day windows.
    customer_window_metrics = (
        transactions.groupby("customer_unique_id", as_index=False)
        .agg(
            orders_within_30_days=(
                "days_from_first_purchase",
                lambda x: (x <= 30).sum(),
            ),
            orders_within_90_days=(
                "days_from_first_purchase",
                lambda x: (x <= 90).sum(),
            ),
            orders_within_180_days=(
                "days_from_first_purchase",
                lambda x: (x <= 180).sum(),
            ),
            clv_180_raw=(
                "estimated_contribution_margin",
                lambda x: x.sum(),
            ),
        )
    )

    # The aggregation above includes all history for clv_180_raw,
    # so calculate correct 180-day CLV separately.
    clv_180 = (
        transactions[transactions["days_from_first_purchase"] <= 180]
        .groupby("customer_unique_id", as_index=False)
        .agg(
            realized_clv_180=(
                "estimated_contribution_margin",
                "sum",
            )
        )
    )

    first_dates = (
        transactions.groupby("customer_unique_id", as_index=False)
        .agg(
            first_purchase_date=("first_purchase_date", "min"),
        )
    )

    repeat_metrics = first_dates.merge(
        customer_window_metrics,
        on="customer_unique_id",
        how="left",
        validate="1:1",
    )

    repeat_metrics = repeat_metrics.merge(
        clv_180,
        on="customer_unique_id",
        how="left",
        validate="1:1",
    )

    repeat_metrics = repeat_metrics.merge(
        repeat_summary,
        on="customer_unique_id",
        how="left",
        validate="1:1",
    )

    repeat_metrics = repeat_metrics.merge(
        second_orders,
        on="customer_unique_id",
        how="left",
        validate="1:1",
    )

    numeric_columns = [
        "repeat_order_count",
        "discounted_repeat_order_count",
        "orders_within_30_days",
        "orders_within_90_days",
        "orders_within_180_days",
    ]

    for column in numeric_columns:
        repeat_metrics[column] = repeat_metrics[column].fillna(0).astype(int)

    # Customers must have enough observed time for each repeat metric.
    repeat_metrics["has_30_day_observation_window"] = (
        repeat_metrics["first_purchase_date"]
        <= analysis_end_date - pd.Timedelta(days=30)
    ).astype(int)

    repeat_metrics["has_90_day_observation_window"] = (
        repeat_metrics["first_purchase_date"]
        <= analysis_end_date - pd.Timedelta(days=90)
    ).astype(int)

    repeat_metrics["has_180_day_observation_window"] = (
        repeat_metrics["first_purchase_date"]
        <= analysis_end_date - pd.Timedelta(days=180)
    ).astype(int)

    # A repeat purchase means two or more completed orders in the window.
    repeat_metrics["repeat_within_30_days"] = np.where(
        repeat_metrics["has_30_day_observation_window"] == 1,
        (repeat_metrics["orders_within_30_days"] >= 2).astype(int),
        np.nan,
    )

    repeat_metrics["repeat_within_90_days"] = np.where(
        repeat_metrics["has_90_day_observation_window"] == 1,
        (repeat_metrics["orders_within_90_days"] >= 2).astype(int),
        np.nan,
    )

    repeat_metrics["repeat_within_180_days"] = np.where(
        repeat_metrics["has_180_day_observation_window"] == 1,
        (repeat_metrics["orders_within_180_days"] >= 2).astype(int),
        np.nan,
    )

    # Do not give recent customers a misleading zero CLV.
    repeat_metrics.loc[
        repeat_metrics["has_180_day_observation_window"] == 0,
        "realized_clv_180",
    ] = np.nan

    repeat_metrics["days_to_second_purchase"] = (
        repeat_metrics["second_purchase_date"]
        - repeat_metrics["first_purchase_date"]
    ).dt.total_seconds() / 86400

    repeat_metrics["second_order_is_full_price"] = np.where(
        repeat_metrics["second_purchase_date"].notna(),
        (
            repeat_metrics["second_purchase_promotion_id"] == "FULL_PRICE"
        ).astype(int),
        np.nan,
    )

    return repeat_metrics


def main():
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("\n--- BUILDING CUSTOMER FEATURES ---\n")

    orders = load_table("orders_enriched.parquet")

    # Use delivered orders for revenue, repeat behavior, and CLV.
    delivered_orders = orders[
        orders["is_delivered"] == 1
    ].copy()

    delivered_orders = delivered_orders.sort_values(
        ["customer_unique_id", "order_purchase_timestamp", "order_id"]
    )

    analysis_end_date = delivered_orders["order_purchase_timestamp"].max()

    # Add order sequence for customer-history metrics.
    delivered_orders["purchase_sequence"] = (
        delivered_orders.groupby("customer_unique_id").cumcount() + 1
    )

    delivered_orders["is_discounted"] = (
        delivered_orders["discount_depth"] > 0
    ).astype(int)

    delivered_orders["is_full_price"] = (
        delivered_orders["promotion_id"] == "FULL_PRICE"
    ).astype(int)

    # First-order promotion is useful for cohort comparisons.
    first_orders = delivered_orders[
        delivered_orders["purchase_sequence"] == 1
    ][
        [
            "customer_unique_id",
            "promotion_id",
            "discount_depth",
            "baseline_merchandise_value",
            "estimated_contribution_margin",
        ]
    ].rename(
        columns={
            "promotion_id": "first_order_promotion_id",
            "discount_depth": "first_order_discount_depth",
            "baseline_merchandise_value": "first_order_baseline_value",
            "estimated_contribution_margin": "first_order_contribution_margin",
        }
    )

    # Core customer features calculated from all delivered orders.
    customer_features = (
        delivered_orders.groupby("customer_unique_id", as_index=False)
        .agg(
            first_purchase_date=("order_purchase_timestamp", "min"),
            last_purchase_date=("order_purchase_timestamp", "max"),
            delivered_order_count=("order_id", "count"),
            baseline_merchandise_value_total=(
                "baseline_merchandise_value",
                "sum",
            ),
            synthetic_revenue_total=(
                "synthetic_merchandise_revenue",
                "sum",
            ),
            discount_amount_total=("discount_amount", "sum"),
            contribution_margin_total=(
                "estimated_contribution_margin",
                "sum",
            ),
            discounted_order_count=("is_discounted", "sum"),
            full_price_order_count=("is_full_price", "sum"),
            average_discount_depth=("discount_depth", "mean"),
            average_order_value=(
                "synthetic_merchandise_revenue",
                "mean",
            ),
            average_order_margin=(
                "estimated_contribution_margin",
                "mean",
            ),
        )
    )

    # Add all-order cancellation information separately.
    customer_cancellations = (
        orders.groupby("customer_unique_id", as_index=False)
        .agg(
            all_order_count=("order_id", "count"),
            canceled_or_unavailable_order_count=(
                "is_canceled_or_unavailable",
                "sum",
            ),
        )
    )

    customer_features = customer_features.merge(
        customer_cancellations,
        on="customer_unique_id",
        how="left",
        validate="1:1",
    )

    customer_features["cancellation_rate"] = np.where(
        customer_features["all_order_count"] > 0,
        customer_features["canceled_or_unavailable_order_count"]
        / customer_features["all_order_count"],
        0,
    )

    # Discount-dependency components.
    customer_features["discounted_order_share"] = np.where(
        customer_features["delivered_order_count"] > 0,
        customer_features["discounted_order_count"]
        / customer_features["delivered_order_count"],
        0,
    )

    customer_features["discounted_spend_share"] = np.where(
        customer_features["synthetic_revenue_total"] > 0,
        customer_features["discount_amount_total"]
        / customer_features["baseline_merchandise_value_total"],
        0,
    )

    # Add first-order fields.
    customer_features = customer_features.merge(
        first_orders,
        on="customer_unique_id",
        how="left",
        validate="1:1",
    )

    # Add repeat and CLV metrics.
    repeat_metrics = calculate_repeat_metrics(
        delivered_orders=delivered_orders,
        analysis_end_date=analysis_end_date,
    )

    customer_features = customer_features.merge(
        repeat_metrics.drop(columns=["first_purchase_date"]),
        on="customer_unique_id",
        how="left",
        validate="1:1",
    )

    # Discount dependency score: 0 to 100.
    # It is an operational segmentation score, not proof of causality.
    customer_features["discounted_repeat_order_share"] = np.where(
        customer_features["repeat_order_count"] > 0,
        customer_features["discounted_repeat_order_count"]
        / customer_features["repeat_order_count"],
        0,
    )

    customer_features["discount_dependency_score"] = (
        100
        * (
            0.50 * customer_features["discounted_order_share"]
            + 0.30 * customer_features["discounted_spend_share"]
            + 0.20 * customer_features["discounted_repeat_order_share"]
        )
    ).round(2)

    # RFM feature: recency is calculated against the final observed date.
    customer_features["analysis_end_date"] = analysis_end_date

    customer_features["recency_days"] = (
        analysis_end_date - customer_features["last_purchase_date"]
    ).dt.total_seconds() / 86400

    customer_features["customer_age_days"] = (
        analysis_end_date - customer_features["first_purchase_date"]
    ).dt.total_seconds() / 86400

    # Sort for readability.
    customer_features = customer_features.sort_values(
        "contribution_margin_total",
        ascending=False,
    )

    # Save the customer feature table automatically.
    output_path = PROCESSED_DATA_DIR / "customer_features.parquet"
    customer_features.to_parquet(output_path, index=False)

    # Create a small summary report automatically.
    customer_summary = pd.DataFrame(
        {
            "metric": [
                "analysis_end_date",
                "customer_count",
                "delivered_order_count",
                "customers_with_repeat_order",
                "customers_eligible_for_180_day_metric",
                "average_discount_dependency_score",
                "total_contribution_margin",
            ],
            "value": [
                str(analysis_end_date.date()),
                len(customer_features),
                int(customer_features["delivered_order_count"].sum()),
                int((customer_features["delivered_order_count"] >= 2).sum()),
                int(
                    customer_features[
                        "has_180_day_observation_window"
                    ].sum()
                ),
                round(
                    customer_features["discount_dependency_score"].mean(),
                    2,
                ),
                round(
                    customer_features["contribution_margin_total"].sum(),
                    2,
                ),
            ],
        }
    )

    summary_path = REPORTS_DIR / "customer_features_summary.csv"
    customer_summary.to_csv(summary_path, index=False)

    print(f"Analysis end date: {analysis_end_date.date()}")
    print(f"Created: {output_path}")
    print(f"Created: {summary_path}")
    print("\n--- CUSTOMER FEATURES COMPLETE ---\n")


if __name__ == "__main__":
    main()