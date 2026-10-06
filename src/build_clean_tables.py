import pandas as pd

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, REPORTS_DIR


def load_csv(file_name: str) -> pd.DataFrame:
    """Load one Olist CSV file from the raw-data folder."""
    file_path = RAW_DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Could not find '{file_name}'. Expected location: {file_path}"
        )

    return pd.read_csv(file_path, low_memory=False)


def clean_customers() -> pd.DataFrame:
    """Load and clean customer records."""
    customers = load_csv("olist_customers_dataset.csv")

    # Customer IDs should always be text, not numbers.
    customers["customer_id"] = customers["customer_id"].astype("string")
    customers["customer_unique_id"] = customers["customer_unique_id"].astype("string")

    # Remove exact duplicate rows, if any.
    customers = customers.drop_duplicates()

    # There should be one row per order-level customer ID.
    if customers["customer_id"].duplicated().any():
        raise ValueError("customers: customer_id should be unique but duplicates were found.")

    return customers


def clean_orders() -> pd.DataFrame:
    """Load and clean order records."""
    orders = load_csv("olist_orders_dataset.csv")

    timestamp_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]

    for column in timestamp_columns:
        orders[column] = pd.to_datetime(orders[column], errors="coerce")

    orders["order_id"] = orders["order_id"].astype("string")
    orders["customer_id"] = orders["customer_id"].astype("string")
    orders["order_status"] = orders["order_status"].astype("string")

    orders = orders.drop_duplicates()

    if orders["order_id"].duplicated().any():
        raise ValueError("orders: order_id should be unique but duplicates were found.")

    # Clear operational flags. These are observed fields derived from order status.
    orders["is_delivered"] = (orders["order_status"] == "delivered").astype("int8")

    orders["is_canceled_or_unavailable"] = (
        orders["order_status"].isin(["canceled", "unavailable"])
    ).astype("int8")

    # Delivery duration only applies to delivered orders with both timestamps present.
    orders["delivery_days"] = (
        orders["order_delivered_customer_date"] - orders["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    # Late delivery is evaluated only where the relevant delivery dates exist.
    orders["is_late_delivery"] = (
        orders["order_delivered_customer_date"]
        > orders["order_estimated_delivery_date"]
    ).astype("Int64")

    return orders


def clean_products() -> pd.DataFrame:
    """Load products and add English product-category labels."""
    products = load_csv("olist_products_dataset.csv")
    translations = load_csv("product_category_name_translation.csv")

    products["product_id"] = products["product_id"].astype("string")
    translations["product_category_name"] = (
        translations["product_category_name"].astype("string")
    )

    products = products.drop_duplicates()
    translations = translations.drop_duplicates(subset=["product_category_name"])

    products = products.merge(
        translations,
        on="product_category_name",
        how="left",
        validate="m:1",
    )

    # Give missing category values a readable, consistent label.
    products["product_category_name"] = (
        products["product_category_name"].fillna("unknown")
    )

    products["product_category_name_english"] = (
        products["product_category_name_english"].fillna("unknown")
    )

    if products["product_id"].duplicated().any():
        raise ValueError("products: product_id should be unique but duplicates were found.")

    return products


def clean_order_items(products: pd.DataFrame) -> pd.DataFrame:
    """Load order items and attach product/category information."""
    items = load_csv("olist_order_items_dataset.csv")

    items["order_id"] = items["order_id"].astype("string")
    items["product_id"] = items["product_id"].astype("string")
    items["seller_id"] = items["seller_id"].astype("string")

    items["shipping_limit_date"] = pd.to_datetime(
        items["shipping_limit_date"],
        errors="coerce",
    )

    items = items.drop_duplicates()

    # Each Olist line item is one purchased item.
    items["quantity"] = 1

    # Make financial names clearer for later calculations.
    items = items.rename(
        columns={
            "price": "observed_item_price",
            "freight_value": "observed_freight_value",
        }
    )

    # Join product attributes and English category names.
    product_columns = [
        "product_id",
        "product_category_name",
        "product_category_name_english",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ]

    items = items.merge(
        products[product_columns],
        on="product_id",
        how="left",
        validate="m:1",
    )

    items["product_category_name_english"] = (
        items["product_category_name_english"].fillna("unknown")
    )

    # One order can contain several item IDs, but each pair must be unique.
    if items.duplicated(subset=["order_id", "order_item_id"]).any():
        raise ValueError(
            "order_items: duplicate order_id + order_item_id combinations were found."
        )

    return items


def aggregate_payments() -> pd.DataFrame:
    """Aggregate multiple payment records to one row per order."""
    payments = load_csv("olist_order_payments_dataset.csv")

    payments["order_id"] = payments["order_id"].astype("string")

    payment_summary = (
        payments.groupby("order_id", as_index=False)
        .agg(
            payment_value_total=("payment_value", "sum"),
            payment_installments_max=("payment_installments", "max"),
            payment_record_count=("payment_sequential", "count"),
        )
    )

    return payment_summary


def aggregate_reviews() -> pd.DataFrame:
    """Aggregate reviews to one row per order."""
    reviews = load_csv("olist_order_reviews_dataset.csv")

    reviews["order_id"] = reviews["order_id"].astype("string")
    reviews["review_creation_date"] = pd.to_datetime(
        reviews["review_creation_date"],
        errors="coerce",
    )

    review_summary = (
        reviews.groupby("order_id", as_index=False)
        .agg(
            review_score_mean=("review_score", "mean"),
            review_count=("review_id", "count"),
            first_review_date=("review_creation_date", "min"),
        )
    )

    return review_summary


def build_orders_clean(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    payments: pd.DataFrame,
    reviews: pd.DataFrame,
) -> pd.DataFrame:
    """Build one clean row per order."""
    orders_clean = orders.merge(
        customers[
            [
                "customer_id",
                "customer_unique_id",
                "customer_city",
                "customer_state",
            ]
        ],
        on="customer_id",
        how="left",
        validate="m:1",
    )

    orders_clean = orders_clean.merge(
        payments,
        on="order_id",
        how="left",
        validate="1:1",
    )

    orders_clean = orders_clean.merge(
        reviews,
        on="order_id",
        how="left",
        validate="1:1",
    )

    return orders_clean


def save_table(df: pd.DataFrame, file_name: str) -> None:
    """Save a DataFrame as a Parquet file."""
    output_path = PROCESSED_DATA_DIR / file_name
    df.to_parquet(output_path, index=False)
    print(f"Created: {output_path}")


def main():
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("\n--- BUILDING CLEAN BASE TABLES ---\n")

    customers = clean_customers()
    orders = clean_orders()
    products = clean_products()
    order_items = clean_order_items(products)
    payments = aggregate_payments()
    reviews = aggregate_reviews()

    orders_clean = build_orders_clean(
        orders=orders,
        customers=customers,
        payments=payments,
        reviews=reviews,
    )

    # Save automatically generated clean tables.
    save_table(customers, "customers_clean.parquet")
    save_table(products, "products_clean.parquet")
    save_table(order_items, "order_items_clean.parquet")
    save_table(orders_clean, "orders_clean.parquet")
    save_table(payments, "payments_clean.parquet")
    save_table(reviews, "reviews_clean.parquet")

    # Create a simple row-count report automatically.
    cleaning_summary = pd.DataFrame(
        {
            "table_name": [
                "customers_clean",
                "products_clean",
                "order_items_clean",
                "orders_clean",
                "payments_clean",
                "reviews_clean",
            ],
            "row_count": [
                len(customers),
                len(products),
                len(order_items),
                len(orders_clean),
                len(payments),
                len(reviews),
            ],
            "column_count": [
                len(customers.columns),
                len(products.columns),
                len(order_items.columns),
                len(orders_clean.columns),
                len(payments.columns),
                len(reviews.columns),
            ],
        }
    )

    summary_path = REPORTS_DIR / "cleaning_summary.csv"
    cleaning_summary.to_csv(summary_path, index=False)

    print(f"Created: {summary_path}")
    print("\n--- CLEAN BASE TABLES COMPLETE ---\n")


if __name__ == "__main__":
    main()