import duckdb
import pandas as pd

from config import PROJECT_ROOT, PROCESSED_DATA_DIR, REPORTS_DIR


TABLES_TO_LOAD = {
    "orders_enriched": "orders_enriched.parquet",
    "order_items_enriched": "order_items_enriched.parquet",
    "customer_features": "customer_features.parquet",
    "customer_segments": "customer_segments.parquet",
}


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    database_path = PROJECT_ROOT / "data" / "discount_addiction.duckdb"

    # Connect creates the database file automatically if it does not exist.
    connection = duckdb.connect(str(database_path))

    load_summary = []

    print("\n--- LOADING TABLES INTO DUCKDB ---\n")

    for table_name, file_name in TABLES_TO_LOAD.items():
        parquet_path = PROCESSED_DATA_DIR / file_name

        if not parquet_path.exists():
            raise FileNotFoundError(
                f"Could not find {parquet_path}. "
                "Run the relevant build script first."
            )

        # DuckDB reads the Parquet file and creates a persistent SQL table.
        safe_parquet_path = str(parquet_path).replace("\\", "/")

        connection.execute(
            f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT *
            FROM read_parquet('{safe_parquet_path}')
            """
        )

        row_count = connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        column_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            """
        ).fetchone()[0]

        load_summary.append(
            {
                "table_name": table_name,
                "source_file": file_name,
                "row_count": row_count,
                "column_count": column_count,
            }
        )

        print(
            f"Loaded {table_name}: "
            f"{row_count:,} rows, {column_count} columns"
        )

    connection.close()

    summary_df = pd.DataFrame(load_summary)

    summary_path = REPORTS_DIR / "duckdb_load_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    print(f"\nCreated database: {database_path}")
    print(f"Created report: {summary_path}")
    print("\n--- DUCKDB LOAD COMPLETE ---\n")


if __name__ == "__main__":
    main()