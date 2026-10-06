import pandas as pd

from config import PROCESSED_DATA_DIR, REPORTS_DIR


def add_check(checks, check_name, result, value, notes):
    checks.append(
        {
            "check_name": check_name,
            "result": result,
            "value": value,
            "notes": notes,
        }
    )


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    file_path = PROCESSED_DATA_DIR / "customer_features.parquet"

    if not file_path.exists():
        raise FileNotFoundError(
            "customer_features.parquet was not found. "
            "Run build_customer_features.py first."
        )

    customers = pd.read_parquet(file_path)

    checks = []

    # One row per permanent customer ID.
    duplicate_customers = customers["customer_unique_id"].duplicated().sum()

    add_check(
        checks,
        "customer_unique_id is unique",
        "PASS" if duplicate_customers == 0 else "FAIL",
        f"{duplicate_customers:,} duplicate customer IDs",
        "customer_features must contain one row per customer.",
    )

    # Customer order counts must be at least one.
    invalid_order_counts = (customers["delivered_order_count"] < 1).sum()

    add_check(
        checks,
        "every customer has at least one delivered order",
        "PASS" if invalid_order_counts == 0 else "FAIL",
        f"{invalid_order_counts:,} invalid customers",
        "A customer in this table should have at least one delivered order.",
    )

    # Shares must be between zero and one.
    share_columns = [
        "cancellation_rate",
        "discounted_order_share",
        "discounted_spend_share",
        "discounted_repeat_order_share",
    ]

    for column in share_columns:
        invalid_values = (
            (customers[column] < 0) | (customers[column] > 1)
        ).sum()

        add_check(
            checks,
            f"{column} is between 0 and 1",
            "PASS" if invalid_values == 0 else "FAIL",
            f"{invalid_values:,} invalid values",
            "A percentage/share cannot be below 0 or above 1.",
        )

    # Discount dependency score must be between 0 and 100.
    invalid_dependency_scores = (
        (customers["discount_dependency_score"] < 0)
        | (customers["discount_dependency_score"] > 100)
    ).sum()

    add_check(
        checks,
        "discount_dependency_score is between 0 and 100",
        "PASS" if invalid_dependency_scores == 0 else "FAIL",
        f"{invalid_dependency_scores:,} invalid scores",
        "The score is used later for discount-responsiveness segments.",
    )

    # Recency and customer age cannot be negative.
    negative_recency = (customers["recency_days"] < 0).sum()
    negative_age = (customers["customer_age_days"] < 0).sum()

    add_check(
        checks,
        "recency_days is non-negative",
        "PASS" if negative_recency == 0 else "FAIL",
        f"{negative_recency:,} invalid values",
        "Recency is the number of days since the customer's latest order.",
    )

    add_check(
        checks,
        "customer_age_days is non-negative",
        "PASS" if negative_age == 0 else "FAIL",
        f"{negative_age:,} invalid values",
        "Customer age is the number of days since first purchase.",
    )

    # Recent customers should not receive a misleading 180-day CLV value.
    eligible_180 = customers["has_180_day_observation_window"] == 1
    ineligible_180 = customers["has_180_day_observation_window"] == 0

    missing_clv_for_eligible = customers.loc[
        eligible_180,
        "realized_clv_180",
    ].isna().sum()

    clv_present_for_ineligible = customers.loc[
        ineligible_180,
        "realized_clv_180",
    ].notna().sum()

    add_check(
        checks,
        "180-day eligible customers have realized CLV",
        "PASS" if missing_clv_for_eligible == 0 else "FAIL",
        f"{missing_clv_for_eligible:,} missing CLV values",
        "Customers with a complete 180-day window should have realized_clv_180.",
    )

    add_check(
        checks,
        "recent customers do not have misleading 180-day CLV",
        "PASS" if clv_present_for_ineligible == 0 else "FAIL",
        f"{clv_present_for_ineligible:,} unexpected CLV values",
        "Customers without 180 observed days should have missing CLV.",
    )

    # Informational portfolio metrics.
    repeat_180_rate = customers.loc[
        eligible_180,
        "repeat_within_180_days",
    ].mean()

    add_check(
        checks,
        "customer count",
        "INFO",
        f"{len(customers):,}",
        "Number of unique customers with at least one delivered order.",
    )

    add_check(
        checks,
        "average delivered orders per customer",
        "INFO",
        f"{customers['delivered_order_count'].mean():.2f}",
        "Useful context before interpreting repeat behavior.",
    )

    add_check(
        checks,
        "180-day repeat rate among eligible customers",
        "INFO",
        f"{repeat_180_rate:.2%}",
        "Only customers with a complete 180-day observation window are included.",
    )

    add_check(
        checks,
        "average realized 180-day CLV among eligible customers",
        "INFO",
        f"R${customers.loc[eligible_180, 'realized_clv_180'].mean():,.2f}",
        "Scenario-based contribution-margin CLV.",
    )

    results = pd.DataFrame(checks)

    csv_path = REPORTS_DIR / "customer_feature_validation.csv"
    results.to_csv(csv_path, index=False)

    markdown_lines = [
        "# Customer Feature Validation Report",
        "",
        "This report validates the one-row-per-customer feature table.",
        "",
        results.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "- `PASS`: expected rule is correct.",
        "- `FAIL`: fix before segmentation.",
        "- `INFO`: useful descriptive context.",
    ]

    markdown_path = REPORTS_DIR / "customer_feature_validation.md"
    markdown_path.write_text("\n".join(markdown_lines), encoding="utf-8")

    print(results.to_string(index=False))
    print(f"\nCreated: {csv_path}")
    print(f"Created: {markdown_path}")


if __name__ == "__main__":
    main()