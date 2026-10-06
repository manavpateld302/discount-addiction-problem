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

ELASTICITY_ORDER = [
    "Conservative",
    "Base",
    "Optimistic",
]


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    input_path = REPORTS_DIR / "discount_simulator_sensitivity.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            "discount_simulator_sensitivity.csv was not found. "
            "Run run_simulator_sensitivity.py first."
        )

    sensitivity = pd.read_csv(input_path)

    sensitivity["scenario"] = pd.Categorical(
        sensitivity["scenario"],
        categories=SCENARIO_ORDER,
        ordered=True,
    )

    sensitivity["elasticity_scenario"] = pd.Categorical(
        sensitivity["elasticity_scenario"],
        categories=ELASTICITY_ORDER,
        ordered=True,
    )

    sensitivity["scenario_label"] = sensitivity["scenario"].map(
        SCENARIO_LABELS
    )

    sensitivity = sensitivity.sort_values(
        ["scenario", "elasticity_scenario"]
    )

    sns.set_theme(style="whitegrid", palette="deep")

    fig, axes = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(17, 6),
    )

    # Chart 1: Incremental contribution margin versus no offer.
    sns.barplot(
        data=sensitivity,
        x="scenario_label",
        y="incremental_margin_vs_no_offer",
        hue="elasticity_scenario",
        ax=axes[0],
    )

    axes[0].axhline(
        y=0,
        color="black",
        linewidth=1,
    )

    axes[0].set_title(
        "Incremental Margin vs. No Offer"
    )

    axes[0].set_xlabel("Discount Policy")
    axes[0].set_ylabel("Incremental Contribution Margin (R$)")
    axes[0].legend(title="Elasticity Scenario")

    # Chart 2: Expected discount cost.
    sns.barplot(
        data=sensitivity,
        x="scenario_label",
        y="expected_discount_cost",
        hue="elasticity_scenario",
        ax=axes[1],
    )

    axes[1].set_title(
        "Expected Discount Cost"
    )

    axes[1].set_xlabel("Discount Policy")
    axes[1].set_ylabel("Expected Discount Cost (R$)")
    axes[1].legend(title="Elasticity Scenario")

    fig.suptitle(
        "Discount Simulator Sensitivity Analysis",
        fontsize=16,
        fontweight="bold",
        y=1.03,
    )

    plt.tight_layout()

    figure_path = FIGURES_DIR / "06_simulator_sensitivity.png"

    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Created: {figure_path}")


if __name__ == "__main__":
    main()