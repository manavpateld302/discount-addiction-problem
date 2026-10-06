import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from config import PROCESSED_DATA_DIR, REPORTS_DIR, FIGURES_DIR


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    input_path = PROCESSED_DATA_DIR / "customer_segments.parquet"

    if not input_path.exists():
        raise FileNotFoundError(
            "customer_segments.parquet was not found. "
            "Run build_customer_segments.py first."
        )

    customers = pd.read_parquet(input_path)

    # Build a segment-level business summary.
    segment_summary = (
        customers.groupby("customer_segment", as_index=False)
        .agg(
            customer_count=("customer_unique_id", "count"),
            average_discount_dependency_score=(
                "discount_dependency_score",
                "mean",
            ),
            average_full_price_order_share=(
                "full_price_order_share",
                "mean",
            ),
            average_order_margin=("average_order_margin", "mean"),
            average_delivered_orders=("delivered_order_count", "mean"),
            total_contribution_margin=(
                "contribution_margin_total",
                "sum",
            ),
            average_realized_clv_180=(
                "realized_clv_180",
                "mean",
            ),
        )
        .sort_values(
            "total_contribution_margin",
            ascending=False,
        )
    )

    summary_path = REPORTS_DIR / "segment_economics_summary.csv"
    segment_summary.to_csv(summary_path, index=False)

    sns.set_theme(style="whitegrid", palette="deep")

    fig, axes = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(18, 7),
    )

    # Chart 1: Total contribution margin by segment.
    sns.barplot(
        data=segment_summary,
        y="customer_segment",
        x="total_contribution_margin",
        ax=axes[0],
        color="#54A24B",
    )

    axes[0].set_title("Total Contribution Margin by Customer Segment")
    axes[0].set_xlabel("Estimated Contribution Margin (R$)")
    axes[0].set_ylabel("Customer Segment")

    # Chart 2: Discount dependency versus margin.
    scatter = axes[1].scatter(
        segment_summary["average_discount_dependency_score"],
        segment_summary["average_order_margin"],
        s=segment_summary["customer_count"] / 4,
        c=segment_summary["average_full_price_order_share"],
        cmap="viridis",
        alpha=0.75,
        edgecolors="black",
    )

    for _, row in segment_summary.iterrows():
        axes[1].annotate(
            row["customer_segment"],
            (
                row["average_discount_dependency_score"],
                row["average_order_margin"],
            ),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
        )

    axes[1].axhline(
        y=0,
        color="red",
        linestyle="--",
        linewidth=1,
    )

    axes[1].set_title("Discount Dependency vs. Average Order Margin")
    axes[1].set_xlabel("Average Discount Dependency Score")
    axes[1].set_ylabel("Average Order Margin (R$)")

    colorbar = fig.colorbar(scatter, ax=axes[1])
    colorbar.set_label("Average Full-Price Order Share")

    fig.suptitle(
        "Customer Segment Economics",
        fontsize=16,
        fontweight="bold",
        y=1.03,
    )

    plt.tight_layout()

    figure_path = FIGURES_DIR / "03_segment_economics.png"

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