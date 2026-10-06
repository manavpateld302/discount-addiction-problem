import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from config import REPORTS_DIR, FIGURES_DIR


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    input_path = REPORTS_DIR / "sql_03_monthly_cohort_retention.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            "sql_03_monthly_cohort_retention.csv was not found. "
            "Run 03_monthly_cohort_retention.sql first."
        )

    retention = pd.read_csv(input_path)

    retention["cohort_month"] = pd.to_datetime(
        retention["cohort_month"]
    )

    # Create a readable label such as 2017-01.
    retention["cohort_label"] = retention[
        "cohort_month"
    ].dt.strftime("%Y-%m")

    # In first-order analysis, FULL_PRICE and WELCOME10 are the key groups.
    promotion_order = [
        "FULL_PRICE",
        "WELCOME10",
        "CATEGORY15",
        "LAPSED20",
    ]

    available_promotions = [
        promotion
        for promotion in promotion_order
        if promotion in retention["first_order_promotion_id"].unique()
    ]

    if len(available_promotions) == 0:
        raise ValueError(
            "No promotion cohorts were found in the retention output."
        )

    sns.set_theme(style="white")

    figure_width = 8 * len(available_promotions)

    fig, axes = plt.subplots(
        nrows=1,
        ncols=len(available_promotions),
        figsize=(figure_width, 8),
        squeeze=False,
    )

    for index, promotion_id in enumerate(available_promotions):
        axis = axes[0][index]

        promotion_data = retention[
            retention["first_order_promotion_id"] == promotion_id
        ].copy()

        heatmap_data = promotion_data.pivot(
            index="cohort_label",
            columns="months_since_first_order",
            values="retention_rate_pct",
        )

        # Keep cohorts in chronological order.
        heatmap_data = heatmap_data.sort_index()

        sns.heatmap(
            heatmap_data,
            annot=True,
            fmt=".1f",
            cmap="Blues",
            vmin=0,
            vmax=100,
            linewidths=0.5,
            linecolor="white",
            cbar=True,
            cbar_kws={"label": "Retention Rate (%)"},
            ax=axis,
        )

        axis.set_title(
            f"Monthly Retention: {promotion_id}",
            fontsize=13,
            fontweight="bold",
        )

        axis.set_xlabel("Months Since First Order")
        axis.set_ylabel("First Purchase Cohort")

    fig.suptitle(
        "Customer Retention Cohorts by First-Order Promotion",
        fontsize=16,
        fontweight="bold",
        y=1.02,
    )

    plt.tight_layout()

    figure_path = (
        FIGURES_DIR / "04_monthly_cohort_retention_heatmap.png"
    )

    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Created: {figure_path}")


if __name__ == "__main__":
    main()