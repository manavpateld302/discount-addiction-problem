import pandas as pd

from config import RAW_DATA_DIR, REPORTS_DIR


# These are the raw Olist files we expect to find.
DATA_FILES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}


def audit_dataframe(table_name: str, df: pd.DataFrame) -> dict:
    """Create a simple quality summary for one raw table."""

    return {
        "table_name": table_name,
        "rows": len(df),
        "columns": len(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "total_missing_values": int(df.isna().sum().sum()),
        "column_names": ", ".join(df.columns.tolist()),
    }


def main():
    # Create reports folder if it does not exist.
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    summaries = []
    missing_value_reports = []

    print("\n--- OLIST RAW DATA AUDIT ---\n")

    for table_name, file_name in DATA_FILES.items():
        file_path = RAW_DATA_DIR / file_name

        if not file_path.exists():
            print(f"WARNING: File not found: {file_path}")
            continue

        # low_memory=False prevents mixed-type warnings while auditing.
        df = pd.read_csv(file_path, low_memory=False)

        summary = audit_dataframe(table_name, df)
        summaries.append(summary)

        print(f"Table: {table_name}")
        print(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
        print(f"Duplicate rows: {summary['duplicate_rows']:,}")
        print(f"Total missing values: {summary['total_missing_values']:,}")
        print("Columns:")
        print(df.columns.tolist())
        print("\nFirst 3 rows:")
        print(df.head(3))
        print("-" * 70)

        # Create a column-by-column missing-value report.
        missing = pd.DataFrame({
            "table_name": table_name,
            "column_name": df.columns,
            "data_type": df.dtypes.astype(str).values,
            "missing_values": df.isna().sum().values,
            "missing_percent": (df.isna().mean() * 100).round(2).values,
            "unique_values": df.nunique(dropna=True).values,
        })

        missing_value_reports.append(missing)

    # Create output files automatically.
    summary_df = pd.DataFrame(summaries)
    missing_df = pd.concat(missing_value_reports, ignore_index=True)

    summary_path = REPORTS_DIR / "raw_data_summary.csv"
    missing_path = REPORTS_DIR / "raw_data_missing_values.csv"

    summary_df.to_csv(summary_path, index=False)
    missing_df.to_csv(missing_path, index=False)

    print("\n--- AUDIT COMPLETE ---")
    print(f"Created: {summary_path}")
    print(f"Created: {missing_path}")


if __name__ == "__main__":
    main()