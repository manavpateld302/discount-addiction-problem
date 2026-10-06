import pandas as pd

from config import PROCESSED_DATA_DIR, REPORTS_DIR


def load_parquet(file_name: str) -> pd.DataFrame:
    """Load one processed Parquet table."""
    file_path = PROCESSED_DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Could not find '{file_name}'. Run build_clean_tables.py first.\n"
            f"Expected location: {file_path}"
        )

    return pd.read_parquet(file_path)


def add_check(
    checks: list,
    check_name: str,
    result: str,
    value: str,
    notes: str,
) -> None:
    """Add one validation result to the checks list."""
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

    print("\n--- VALIDATING CLEAN TABLES ---\n")

    # Load automatically created clean tables.
    customers = load_parquet("customers_clean.parquet")
    orders = load_parquet("orders_clean.parquet")
    order_items = load_parquet("order_items_clean.parquet")
    products = load_parquet("products_clean.parquet")
    payments = load_parquet("payments_clean.parquet")
    reviews = load_parquet("reviews_clean.parquet")

    checks = []

    # 1. Table row counts
    for table_name, dataframe in {
        "customers_clean": customers,
        "orders_clean": orders,
        "order_items_clean": order_items,
        "products_clean": products,
        "payments_clean": payments,
        "reviews_clean": reviews,
    }.items():
        add_check(
            checks,
            check_name=f"{table_name} has rows",
            result="PASS" if len(dataframe) > 0 else "FAIL",
            value=f"{len(dataframe):,}",
            notes="A clean table should not be empty.",
        )

    # 2. Primary-key checks
    add_check(
        checks,
        check_name="orders_clean: order_id is unique",
        result="PASS" if not orders["order_id"].duplicated().any() else "FAIL",
        value=f"{orders['order_id'].duplicated().sum():,} duplicate order IDs",
        notes="There must be one row per order in orders_clean.",
    )

    item_key_duplicates = order_items.duplicated(
        subset=["order_id", "order_item_id"]
    ).sum()

    add_check(
        checks,
        check_name="order_items_clean: order_id + order_item_id is unique",
        result="PASS" if item_key_duplicates == 0 else "FAIL",
        value=f"{item_key_duplicates:,} duplicate item keys",
        notes="Each item sequence should occur only once within an order.",
    )

    add_check(
        checks,
        check_name="customers_clean: customer_id is unique",
        result="PASS" if not customers["customer_id"].duplicated().any() else "FAIL",
        value=f"{customers['customer_id'].duplicated().sum():,} duplicate customer IDs",
        notes="customer_id is an order-level customer record key.",
    )

    add_check(
        checks,
        check_name="products_clean: product_id is unique",
        result="PASS" if not products["product_id"].duplicated().any() else "FAIL",
        value=f"{products['product_id'].duplicated().sum():,} duplicate product IDs",
        notes="There must be one row per product.",
    )

    # 3. Customer join checks
    missing_customer_unique_id = orders["customer_unique_id"].isna().sum()

    add_check(
        checks,
        check_name="orders_clean: customer_unique_id populated",
        result="PASS" if missing_customer_unique_id == 0 else "WARNING",
        value=f"{missing_customer_unique_id:,} missing values",
        notes="customer_unique_id is required for repeat purchase and CLV analysis.",
    )

    # 4. Financial data checks
    negative_item_prices = (order_items["observed_item_price"] < 0).sum()
    negative_freight = (order_items["observed_freight_value"] < 0).sum()

    add_check(
        checks,
        check_name="order_items_clean: no negative observed item prices",
        result="PASS" if negative_item_prices == 0 else "FAIL",
        value=f"{negative_item_prices:,} negative values",
        notes="Negative product prices would invalidate revenue calculations.",
    )

    add_check(
        checks,
        check_name="order_items_clean: no negative freight values",
        result="PASS" if negative_freight == 0 else "FAIL",
        value=f"{negative_freight:,} negative values",
        notes="Negative freight values would invalidate cost calculations.",
    )

    # 5. Status checks
    delivered_orders = orders["is_delivered"].sum()
    canceled_orders = orders["is_canceled_or_unavailable"].sum()

    add_check(
        checks,
        check_name="delivered orders identified",
        result="PASS" if delivered_orders > 0 else "FAIL",
        value=f"{delivered_orders:,} delivered orders",
        notes="Delivered orders will be the primary population for revenue and CLV.",
    )

    add_check(
        checks,
        check_name="canceled/unavailable orders identified",
        result="PASS" if canceled_orders >= 0 else "FAIL",
        value=f"{canceled_orders:,} canceled or unavailable orders",
        notes="These orders must not be counted as successful revenue.",
    )

    # 6. Product-category check
    unknown_categories = (
        order_items["product_category_name_english"].fillna("unknown") == "unknown"
    ).sum()

    add_check(
        checks,
        check_name="order items with unknown product category",
        result="WARNING" if unknown_categories > 0 else "PASS",
        value=f"{unknown_categories:,} line items",
        notes="Unknown categories are expected for some products and will remain labeled 'unknown'.",
    )

    # 7. Review availability
    reviewed_orders = orders["review_score_mean"].notna().sum()

    add_check(
        checks,
        check_name="orders with a review score",
        result="PASS" if reviewed_orders > 0 else "WARNING",
        value=f"{reviewed_orders:,} reviewed orders",
        notes="A review is optional; missing reviews should not be treated as bad reviews.",
    )

    # 8. Create a summary of important totals.
    total_observed_item_revenue = order_items["observed_item_price"].sum()
    total_observed_freight = order_items["observed_freight_value"].sum()
    total_payment_value = payments["payment_value_total"].sum()

    add_check(
        checks,
        check_name="total observed item revenue",
        result="INFO",
        value=f"R${total_observed_item_revenue:,.2f}",
        notes="Raw Olist item-price total before synthetic promotions.",
    )

    add_check(
        checks,
        check_name="total observed freight value",
        result="INFO",
        value=f"R${total_observed_freight:,.2f}",
        notes="Raw Olist freight total.",
    )

    add_check(
        checks,
        check_name="total aggregated payment value",
        result="INFO",
        value=f"R${total_payment_value:,.2f}",
        notes="Payment value can differ from item price plus freight due to vouchers, installments, and data structure.",
    )

    # Save results automatically.
    results = pd.DataFrame(checks)
    csv_path = REPORTS_DIR / "table_validation_results.csv"
    results.to_csv(csv_path, index=False)

    # Create a readable Markdown report automatically.
    report_lines = [
        "# Clean Table Validation Report",
        "",
        "This report was generated automatically by `src/validate_clean_tables.py`.",
        "",
        "## Validation results",
        "",
        results.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "- `PASS`: the expected rule was met.",
        "- `WARNING`: investigate or document the condition; it is not necessarily an error.",
        "- `FAIL`: stop and fix the issue before moving forward.",
        "- `INFO`: descriptive business total, not a pass/fail rule.",
    ]

    markdown_path = REPORTS_DIR / "validation_report.md"
    markdown_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(results.to_string(index=False))
    print(f"\nCreated: {csv_path}")
    print(f"Created: {markdown_path}")
    print("\n--- VALIDATION COMPLETE ---\n")


if __name__ == "__main__":
    main()