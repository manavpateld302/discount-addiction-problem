import numpy as np
import pandas as pd

from config import PROCESSED_DATA_DIR, REPORTS_DIR


EXPECTED_DISCOUNTS = {
    "FULL_PRICE": 0.00,
    "WELCOME10": 0.10,
    "CATEGORY15": 0.15,
    "LAPSED20": 0.20,
}


def load_table(file_name: str) -> pd.DataFrame:
    """Load one processed Parquet table."""
    file_path = PROCESSED_DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Could not find {file_name}. Run build_enriched_tables.py first."
        )

    return pd.read_parquet(file_path)


def add_check(checks, check_name, result, value, notes):
    """Add one validation row."""
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

    print("\n--- VALIDATING ENRICHED TABLES ---\n")

    orders = load_table("orders_enriched.parquet")
    items = load_table("order_items_enriched.parquet")

    checks = []

    # 1. Grain checks
    duplicate_orders = orders["order_id"].duplicated().sum()

    add_check(
        checks,
        "orders_enriched: order_id is unique",
        "PASS" if duplicate_orders == 0 else "FAIL",
        f"{duplicate_orders:,} duplicate order IDs",
        "There must be exactly one row per order.",
    )

    duplicate_items = items.duplicated(
        subset=["order_id", "order_item_id"]
    ).sum()

    add_check(
        checks,
        "order_items_enriched: item key is unique",
        "PASS" if duplicate_items == 0 else "FAIL",
        f"{duplicate_items:,} duplicate item keys",
        "Each order_id + order_item_id pair must occur once.",
    )

    # 2. Promotion discount mapping checks
    for promotion_id, expected_discount in EXPECTED_DISCOUNTS.items():
        promotion_orders = orders[
            orders["promotion_id"] == promotion_id
        ]

        if len(promotion_orders) == 0:
            add_check(
                checks,
                f"{promotion_id}: promotion exists",
                "WARNING",
                "0 orders",
                "This promotion may have no eligible orders under the current rules.",
            )
            continue

        incorrect_discount_count = (
            ~np.isclose(
                promotion_orders["discount_pct"],
                expected_discount,
            )
        ).sum()

        add_check(
            checks,
            f"{promotion_id}: correct discount percentage",
            "PASS" if incorrect_discount_count == 0 else "FAIL",
            f"{incorrect_discount_count:,} incorrect orders",
            f"Expected discount_pct = {expected_discount:.0%}.",
        )

    # 3. Discount arithmetic checks
    expected_discount_amount = (
        orders["baseline_merchandise_value"] * orders["discount_depth"]
    )

    discount_difference = (
        orders["discount_amount"] - expected_discount_amount
    ).abs()

    incorrect_discount_math = (discount_difference > 0.01).sum()

    add_check(
        checks,
        "order discount arithmetic is correct",
        "PASS" if incorrect_discount_math == 0 else "FAIL",
        f"{incorrect_discount_math:,} orders differ by more than R$0.01",
        "discount_amount should equal baseline_merchandise_value × discount_depth.",
    )

    # 4. Check that discounts occur only on delivered orders.
    discounted_non_delivered = (
        (orders["is_delivered"] == 0)
        & (orders["discount_amount"] > 0)
    ).sum()

    add_check(
        checks,
        "discounts apply only to delivered orders",
        "PASS" if discounted_non_delivered == 0 else "FAIL",
        f"{discounted_non_delivered:,} non-delivered discounted orders",
        "Canceled/unavailable orders should not receive scenario discounts.",
    )

    # 5. Check non-negative values.
    negative_paid_price = (items["synthetic_paid_price"] < 0).sum()

    add_check(
        checks,
        "synthetic paid prices are non-negative",
        "PASS" if negative_paid_price == 0 else "FAIL",
        f"{negative_paid_price:,} negative prices",
        "A synthetic paid price cannot be negative.",
    )

    negative_cogs = (items["estimated_cogs"] < 0).sum()

    add_check(
        checks,
        "estimated COGS is non-negative",
        "PASS" if negative_cogs == 0 else "FAIL",
        f"{negative_cogs:,} negative COGS values",
        "Estimated COGS cannot be negative.",
    )

    # 6. Reconcile item contribution margin to order contribution margin.
    item_margin_by_order = (
        items.groupby("order_id", as_index=False)
        .agg(
            item_margin_total=(
                "estimated_item_contribution_margin",
                "sum",
            )
        )
    )

    reconciliation = orders[
        ["order_id", "estimated_contribution_margin"]
    ].merge(
        item_margin_by_order,
        on="order_id",
        how="left",
        validate="1:1",
    )

    reconciliation["margin_difference"] = (
        reconciliation["estimated_contribution_margin"]
        - reconciliation["item_margin_total"]
    ).abs()

    non_reconciling_orders = (
        reconciliation["margin_difference"] > 0.01
    ).sum()

    add_check(
        checks,
        "item margin reconciles to order margin",
        "PASS" if non_reconciling_orders == 0 else "FAIL",
        f"{non_reconciling_orders:,} orders differ by more than R$0.01",
        "Summed item contribution margin should equal order contribution margin.",
    )

    # 7. Business totals for later reference.
    delivered_orders = orders[orders["is_delivered"] == 1]

    add_check(
        checks,
        "delivered order count",
        "INFO",
        f"{len(delivered_orders):,}",
        "Primary population for revenue, repeat, and CLV analysis.",
    )

    add_check(
        checks,
        "total synthetic discount cost",
        "INFO",
        f"R${orders['discount_amount'].sum():,.2f}",
        "Total scenario discount amount across all orders.",
    )

    add_check(
        checks,
        "total estimated contribution margin",
        "INFO",
        f"R${orders['estimated_contribution_margin'].sum():,.2f}",
        "Scenario-based contribution margin; not observed Olist profit.",
    )

    negative_margin_orders = (
        delivered_orders["estimated_contribution_margin"] < 0
    ).sum()

    add_check(
        checks,
        "delivered orders with negative contribution margin",
        "INFO",
        f"{negative_margin_orders:,}",
        "Negative-margin orders are possible and important to analyze.",
    )

    # Save reports automatically.
    results = pd.DataFrame(checks)

    csv_path = REPORTS_DIR / "enriched_validation_results.csv"
    results.to_csv(csv_path, index=False)

    markdown_lines = [
        "# Enriched Table Validation Report",
        "",
        "This report validates synthetic promotions, discount calculations, and estimated margin calculations.",
        "",
        results.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "- `PASS`: calculation or structural rule is correct.",
        "- `WARNING`: review and document if needed.",
        "- `FAIL`: stop and fix before analysis.",
        "- `INFO`: descriptive total, not a pass/fail condition.",
    ]

    markdown_path = REPORTS_DIR / "enriched_validation_report.md"
    markdown_path.write_text("\n".join(markdown_lines), encoding="utf-8")

    print(results.to_string(index=False))
    print(f"\nCreated: {csv_path}")
    print(f"Created: {markdown_path}")
    print("\n--- ENRICHED VALIDATION COMPLETE ---\n")


if __name__ == "__main__":
    main()