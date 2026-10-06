import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from config import PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    input_path = PROCESSED_DATA_DIR / "customer_features.parquet"

    if not input_path.exists():
        raise FileNotFoundError(
            "customer_features.parquet was not found. "
            "Run build_customer_features.py first."
        )

    customers = pd.read_parquet(input_path)

    # Keep only customers with a full 180-day observation window.
    # This prevents recent customers being incorrectly counted as non-repeaters.
    cohort = customers[
        customers["has_180_day_observation_window"] == 1
    ].copy()

    # Create first-order discount groups.
    bins = [-0.01, 0.001, 0.10, 0.15, 0.20, 1.00]

    labels = [
        "0% (Full price)",
        "1–10%",
        "11–15%",
        "16–20%",
        "20%+",
    ]

    cohort["first_order_discount_band"] = pd.cut(
        cohort["first_order_discount_depth"],
        bins=bins,
        labels=labels,
        include_lowest=True,
    )

    # Calculate customer-level cohort results.
    summary = (
        cohort.groupby(
            "first_order_discount_band",
            observed=True,
        )
        .agg(
            customer_count=("customer_unique_id", "count"),
            repeat_rate_180_days=(
                "repeat_within_180_days",
                "mean",
            ),
            average_realized_clv_180=(
                "realized_clv_180",
                "mean",
            ),
            median_realized_clv_180=(
                "realized_clv_180",
                "median",
            ),
            average_discount_dependency_score=(
                "discount_dependency_score",
                "mean",
            ),
        )
        .reset_index()
    )

    # Calculate an approximate 95% confidence interval for repeat rate.
    summary["repeat_rate_standard_error"] = np.sqrt(
        (
            summary["repeat_rate_180_days"]
            * (1 - summary["repeat_rate_180_days"])
        )
        / summary["customer_count"]
    )

    summary["repeat_rate_ci_95"] = (
        1.96 * summary["repeat_rate_standard_error"]
    )

    summary_path = REPORTS_DIR / "first_order_cohort_summary.csv"
    summary.to_csv(summary_path, index=False)

    # Create the charts.
    sns.set_theme(style="whitegrid", palette="deep")

    fig, axes = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(15, 6),
    )

    # Chart 1: repeat rate with approximate 95% confidence intervals.
    axes[0].bar(
        summary["first_order_discount_band"].astype(str),
        summary["repeat_rate_180_days"] * 100,
        yerr=summary["repeat_rate_ci_95"] * 100,
        capsize=5,
        color="#4C78A8",
    )

    axes[0].set_title("180-Day Repeat Rate by First-Order Discount")
    axes[0].set_xlabel("First-Order Discount Depth")
    axes[0].set_ylabel("Repeat Rate (%)")
    axes[0].set_ylim(0, max(5, summary["repeat_rate_180_days"].max() * 130))

    for index, row in summary.iterrows():
        axes[0].text(
            index,
            row["repeat_rate_180_days"] * 100 + 1,
            f"n={int(row['customer_count']):,}",
            ha="center",
            fontsize=9,
        )

    # Chart 2: average realized contribution-margin CLV.
    sns.barplot(
        data=summary,
        x="first_order_discount_band",
        y="average_realized_clv_180",
        ax=axes[1],
        color="#54A24B",
    )

    axes[1].set_title("Average Realized 180-Day CLV")
    axes[1].set_xlabel("First-Order Discount Depth")
    axes[1].set_ylabel("Estimated Contribution Margin (R$)")
    axes[1].tick_params(axis="x", rotation=20)

    fig.suptitle(
        "Customer Value by First-Order Discount Cohort",
        fontsize=16,
        fontweight="bold",
        y=1.03,
    )

    plt.tight_layout()

    figure_path = (
        FIGURES_DIR / "02_first_order_discount_retention_clv.png"
    )

    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Customers with 180-day observation: {len(cohort):,}")
    print(f"Created: {summary_path}")
    print(f"Created: {figure_path}")


if __name__ == "__main__":
    main()