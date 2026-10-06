import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from config import PROCESSED_DATA_DIR, REPORTS_DIR


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    input_path = PROCESSED_DATA_DIR / "customer_features.parquet"

    if not input_path.exists():
        raise FileNotFoundError(
            "customer_features.parquet was not found. "
            "Run build_customer_features.py first."
        )

    customers = pd.read_parquet(input_path).copy()

    # Keep only customers with a full 180-day observation window.
    # Recent customers cannot fairly be labeled as repeaters/non-repeaters.
    model_data = customers[
        customers["has_180_day_observation_window"] == 1
    ].copy()

    # Treatment-style feature: first order had any synthetic discount.
    model_data["first_order_discounted"] = (
        model_data["first_order_discount_depth"] > 0
    ).astype(int)

    # Pre-treatment control: baseline value before synthetic discount.
    # Do NOT use first_order_contribution_margin here because discount affects it.
    model_data["log_first_order_baseline_value"] = np.log1p(
        model_data["first_order_baseline_value"]
    )

    # Calendar month controls help reduce seasonality bias.
    model_data["first_purchase_month"] = pd.to_datetime(
        model_data["first_purchase_date"]
    ).dt.strftime("%Y-%m")

    # Keep only complete records required by the model.
    model_data = model_data.dropna(
        subset=[
            "repeat_within_180_days",
            "first_order_discounted",
            "log_first_order_baseline_value",
            "first_purchase_month",
        ]
    )

    # Logistic regression:
    # Outcome = whether customer repeated within 180 days.
    #
    # C(first_purchase_month) creates one indicator/control per acquisition month.
    formula = """
        repeat_within_180_days
        ~ first_order_discounted
        + log_first_order_baseline_value
        + C(first_purchase_month)
    """

    model = smf.logit(
        formula=formula,
        data=model_data,
    ).fit(disp=False)

    # Build a recruiter-friendly coefficient table.
    confidence_intervals = model.conf_int()
    confidence_intervals.columns = ["ci_lower", "ci_upper"]

    coefficients = pd.DataFrame(
        {
            "term": model.params.index,
            "coefficient_log_odds": model.params.values,
            "odds_ratio": np.exp(model.params.values),
            "p_value": model.pvalues.values,
            "ci_lower_log_odds": confidence_intervals["ci_lower"].values,
            "ci_upper_log_odds": confidence_intervals["ci_upper"].values,
            "ci_lower_odds_ratio": np.exp(
                confidence_intervals["ci_lower"].values
            ),
            "ci_upper_odds_ratio": np.exp(
                confidence_intervals["ci_upper"].values
            ),
        }
    )

    coefficient_path = (
        REPORTS_DIR / "logistic_repeat_model_coefficients.csv"
    )

    coefficients.to_csv(coefficient_path, index=False)

    # Save the full technical model output automatically.
    summary_path = REPORTS_DIR / "logistic_repeat_model_summary.txt"

    summary_text = (
        "LOGISTIC REGRESSION: 180-DAY REPEAT PURCHASE\n"
        "================================================\n\n"
        "Outcome: repeat_within_180_days\n"
        "Main predictor: first_order_discounted\n"
        "Controls: log first-order baseline value and first purchase month\n\n"
        "IMPORTANT: This is an observational synthetic-scenario model. "
        "It does not prove that a discount caused repeat behavior.\n\n"
        + model.summary().as_text()
    )

    summary_path.write_text(summary_text, encoding="utf-8")

    # Create an easy-to-read predicted-probability comparison.
    typical_order_value = model_data[
        "log_first_order_baseline_value"
    ].median()

    typical_month = model_data["first_purchase_month"].mode().iloc[0]

    prediction_data = pd.DataFrame(
        {
            "scenario": [
                "First order: full price",
                "First order: discounted",
            ],
            "first_order_discounted": [0, 1],
            "log_first_order_baseline_value": [
                typical_order_value,
                typical_order_value,
            ],
            "first_purchase_month": [
                typical_month,
                typical_month,
            ],
        }
    )

    prediction_data["predicted_repeat_probability_180_days"] = (
        model.predict(prediction_data)
    )

    prediction_path = (
        REPORTS_DIR / "logistic_repeat_model_predictions.csv"
    )

    prediction_data.to_csv(prediction_path, index=False)

    print("\n--- LOGISTIC REPEAT MODEL COMPLETE ---\n")
    print(f"Customers used in model: {len(model_data):,}")
    print(f"Created: {coefficient_path}")
    print(f"Created: {summary_path}")
    print(f"Created: {prediction_path}")

    print("\nMain discount coefficient:")
    print(
        coefficients[
            coefficients["term"] == "first_order_discounted"
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()