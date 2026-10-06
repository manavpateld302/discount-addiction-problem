import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from config import PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR


def main():
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    input_path = PROCESSED_DATA_DIR / "orders_enriched.parquet"

    if not input_path.exists():
        raise FileNotFoundError(
            "orders_enriched.parquet was not found. "
            "Run build_enriched_tables.py first."
        )

    orders = pd.read_parquet(input_path)

    # Revenue and margin analysis includes completed/delivered orders only.
    delivered_orders = orders[
        orders["is_delivered"] == 1
    ].copy()

    # Create readable discount-depth bands.
    discount_bins = [-0.01, 0.001, 0.10, 0.15, 0.20, 1.00]

    discount_labels = [
        "0% (Full price)",
        "1–10%",
        "11–15%",
        "16–20%",
        "20%+",
    ]

    delivered_orders["discount_band"] = pd.cut(
        delivered_orders["discount_depth"],
        bins=discount_bins,
        labels=discount_labels,
        include_lowest=True,
    )

    # Aggregate business metrics by discount band.
    discount_summary = (
        delivered_orders.groupby(
            "discount_band",
            observed=False,
        )
        .agg(
            order_count=("order_id", "count"),
            baseline_merchandise_value=(
                "baseline_merchandise_value",
                "sum",
            ),
            synthetic_revenue=(
                "synthetic_merchandise_revenue",
                "sum",
            ),
            total_discount_cost=("discount_amount", "sum"),
            total_contribution_margin=(
                "estimated_contribution_margin",
                "sum",
            ),
            average_contribution_margin=(
                "estimated_contribution_margin",
                "mean",
            ),
        )
        .reset_index()
    )

    # Save the numbers behind the chart automatically.
    summary_path = REPORTS_DIR / "discount_band_summary.csv"
    discount_summary.to_csv(summary_path, index=False)

    # Set a clean portfolio style.
    sns.set_theme(style="whitegrid", palette="deep")

    fig, axes = plt.subplots(
        nrows=1,
        ncols=3,
        figsize=(18, 6),
    )

    # Chart 1: baseline merchandise value.
    sns.barplot(
        data=discount_summary,
        x="discount_band",
        y="baseline_merchandise_value",
        ax=axes[0],
        color="#4C78A8",
    )

    axes[0].set_title("Baseline Merchandise Value")
    axes[0].set_xlabel("Discount Depth")
    axes[0].set_ylabel("Value (R$)")
    axes[0].tick_params(axis="x", rotation=25)

    # Chart 2: total discount cost.
    sns.barplot(
        data=discount_summary,
        x="discount_band",
        y="total_discount_cost",
        ax=axes[1],
        color="#F58518",
    )

    axes[1].set_title("Synthetic Discount Cost")
    axes[1].set_xlabel("Discount Depth")
    axes[1].set_ylabel("Discount Cost (R$)")
    axes[1].tick_params(axis="x", rotation=25)

    # Chart 3: total contribution margin.
    sns.barplot(
        data=discount_summary,
        x="discount_band",
        y="total_contribution_margin",
        ax=axes[2],
        color="#54A24B",
    )

    axes[2].set_title("Estimated Contribution Margin")
    axes[2].set_xlabel("Discount Depth")
    axes[2].set_ylabel("Contribution Margin (R$)")
    axes[2].tick_params(axis="x", rotation=25)

    fig.suptitle(
        "Discount Economics by Discount Depth",
        fontsize=16,
        fontweight="bold",
        y=1.03,
    )

    plt.tight_layout()

    figure_path = FIGURES_DIR / "01_discount_economics_by_depth.png"
    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Created: {summary_path}")
    print(f"Created: {figure_path}")


if __name__ == "__main__":
    main()