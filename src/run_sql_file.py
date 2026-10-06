import sys

import duckdb

from config import PROJECT_ROOT, REPORTS_DIR


def main():
    if len(sys.argv) != 2:
        raise ValueError(
            "Usage: python src/run_sql_file.py <sql_file_name>\n"
            "Example: python src/run_sql_file.py 01_first_order_discount_cohort.sql"
        )

    sql_file_name = sys.argv[1]

    sql_path = PROJECT_ROOT / "sql" / sql_file_name
    database_path = PROJECT_ROOT / "data" / "discount_addiction.duckdb"

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    if not database_path.exists():
        raise FileNotFoundError(
            "DuckDB database not found. Run load_duckdb.py first."
        )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    sql_query = sql_path.read_text(encoding="utf-8")

    connection = duckdb.connect(str(database_path))

    result = connection.execute(sql_query).df()

    connection.close()

    output_file_name = f"sql_{sql_path.stem}.csv"
    output_path = REPORTS_DIR / output_file_name

    result.to_csv(output_path, index=False)

    print("\n--- SQL QUERY COMPLETE ---\n")
    print(result.to_string(index=False))
    print(f"\nCreated: {output_path}")


if __name__ == "__main__":
    main()