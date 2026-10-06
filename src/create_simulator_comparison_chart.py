import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from config import REPORTS_DIR, FIGURES_DIR


SCENARIO_ORDER = [
    "NO_OFFER",
    "BLANKET30",
    "TARGETED15",
]

SCENARIO_LABELS = {
    "NO_OFFER": "No offer",
    "BLANKET30": "30% blanket",
    "TARGETED15": "15% targeted",
}


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    input_path = REPORTS_DIR / "discount_simulator_summary.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            "discount_simulator_summary.csv was not found. "
            "Run run_discount_simulator.py first."
        )

    summary = pd.read_csv(input_path)

    # Ensure scenarios appear in a business-friendly order.
    summary["scenario"] = pd.Categorical(
        summary["scenario"],
        categories=SCENARIO_ORDER,
        ordered=True,
    )

    summary = summary.sort_values("scenario")

    summary["scenario_label"] = summary["scenario"].map(
        SCENARIO_LABELS
    )

    sns.set_theme(style="whitegrid", palette="deep")

    fig, axes = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(16, 6),
    )

    # Left chart: expected contribution margin.
    sns.barplot(
        data=summary,
        x="scenario_label",
        y="expected_contribution_margin",
        ax=axes[0],
        palette=["#4C78A8", "#F58518", "#54A24B"],
        hue="scenario_label",
        legend=False,
    )

    axes[0].set_title("Expected Contribution Margin by Policy")
    axes[0].set_xlabel("Discount Policy")
    axes[0].set_ylabel("Expected Contribution Margin (R$)")

    for index, row in summary.reset_index(drop=True).iterrows():
        axes[0].text(
            index,
            row["expected_contribution_margin"],
            f"R${row['expected_contribution_margin']:,.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # Right chart: incremental margin relative to no offer.
    sns.barplot(
        data=summary,
        x="scenario_label",
        y="incremental_margin_vs_no_offer",
        ax=axes[1],
        palette=["#A0A0A0", "#E45756", "#54A24B"],
        hue="scenario_label",
        legend=False,
    )

    axes[1].axhline(
        y=0,
        color="black",
        linewidth=1,
    )

    axes[1].set_title("Incremental Margin vs. No Offer")
    axes[1].set_xlabel("Discount Policy")
    axes[1].set_ylabel("Incremental Contribution Margin (R$)")

    for index, row in summary.reset_index(drop=True).iterrows():
        value = row["incremental_margin_vs_no_offer"]

        vertical_alignment = "bottom" if value >= 0 else "top"

        axes[1].text(
            index,
            value,
            f"R${value:,.0f}",
            ha="center",
            va=vertical_alignment,
            fontsize=9,
        )

    fig.suptitle(
        "Discount Allocation Simulator: Base-Case Scenario",
        fontsize=16,
        fontweight="bold",
        y=1.03,
    )

    plt.tight_layout()

    figure_path = FIGURES_DIR / "05_discount_policy_simulator.png"

    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Created: {figure_path}")


if __name__ == "__main__":
    main()