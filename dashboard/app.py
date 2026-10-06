import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

st.set_page_config(
    page_title="The Discount Addiction Problem",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }

    h1 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
    }

    h2 {
        margin-top: 2rem !important;
    }

    h3 {
        margin-top: 1.5rem !important;
    }

    [data-testid="stMetric"] {
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.25);
    }

    section[data-testid="stSidebar"] {
        padding-top: 2rem;
    }

    div[data-testid="stExpander"] {
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# LOAD SIMULATOR RESULTS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SIMULATOR_FILE = (
    PROJECT_ROOT
    / "reports"
    / "discount_simulator_summary.csv"
)

if not SIMULATOR_FILE.exists():
    st.error(
        f"Simulator output not found: {SIMULATOR_FILE}"
    )
    st.stop()

simulator_df = pd.read_csv(SIMULATOR_FILE)

required_summary_columns = {
    "scenario",
    "customers_offered",
    "expected_orders",
    "expected_discount_cost",
    "expected_contribution_margin",
    "incremental_margin_vs_no_offer"
}

missing_summary_columns = (
    required_summary_columns
    - set(simulator_df.columns)
)

if missing_summary_columns:
    st.error(
        "Simulator summary is missing required columns: "
        + ", ".join(sorted(missing_summary_columns))
    )
    st.stop()

# ---------------------------------------------------------
# LOAD SEGMENT ECONOMICS
# ---------------------------------------------------------

SEGMENT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "segment_economics_summary.csv"
)

if not SEGMENT_FILE.exists():
    st.error(
        f"Segment economics file not found: {SEGMENT_FILE}"
    )
    st.stop()

segment_df = pd.read_csv(SEGMENT_FILE)

# ---------------------------------------------------------
# LOAD FIRST-ORDER COHORT RESULTS
# ---------------------------------------------------------

COHORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "first_order_cohort_summary.csv"
)

if not COHORT_FILE.exists():
    st.error(
        f"Cohort analysis file not found: {COHORT_FILE}"
    )
    st.stop()

cohort_df = pd.read_csv(COHORT_FILE)

# ---------------------------------------------------------
# LOAD SIMULATOR SENSITIVITY RESULTS
# ---------------------------------------------------------

SENSITIVITY_FILE = (
    PROJECT_ROOT
    / "reports"
    / "discount_simulator_sensitivity.csv"
)

if not SENSITIVITY_FILE.exists():
    st.error(
        f"Simulator sensitivity file not found: {SENSITIVITY_FILE}"
    )
    st.stop()

sensitivity_df = pd.read_csv(SENSITIVITY_FILE)

required_sensitivity_columns = {
    "elasticity_scenario",
    "scenario",
    "customers_offered",
    "expected_orders",
    "expected_discount_cost",
    "expected_contribution_margin",
    "incremental_margin_vs_no_offer"
}

missing_sensitivity_columns = (
    required_sensitivity_columns
    - set(sensitivity_df.columns)
)

if missing_sensitivity_columns:
    st.error(
        "Simulator sensitivity output is missing required columns: "
        + ", ".join(sorted(missing_sensitivity_columns))
    )
    st.stop()

expected_scenarios = {
    "Conservative",
    "Base",
    "Optimistic"
}

actual_scenarios = set(
    sensitivity_df["elasticity_scenario"].dropna().unique()
)

if not expected_scenarios.issubset(actual_scenarios):
    st.warning(
        "One or more expected elasticity scenarios are missing."
    )

expected_policies = {
    "NO_OFFER",
    "TARGETED15",
    "BLANKET30"
}

actual_policies = set(
    sensitivity_df["scenario"].dropna().unique()
)

if not expected_policies.issubset(actual_policies):
    st.warning(
        "One or more expected discount policies are missing."
    )

targeted = sensitivity_df[
    (sensitivity_df["elasticity_scenario"] == "Base")
    & (sensitivity_df["scenario"] == "TARGETED15")
].iloc[0]

full_price_cohort = cohort_df[
    cohort_df["first_order_discount_band"] == "0% (Full price)"
]

discounted_cohorts = cohort_df[
    cohort_df["first_order_discount_band"] != "0% (Full price)"
]

full_price_repeat = full_price_cohort[
    "repeat_rate_180_days"
].iloc[0]

full_price_clv = full_price_cohort[
    "average_realized_clv_180"
].iloc[0]

discounted_repeat = (
    discounted_cohorts["repeat_rate_180_days"]
    * discounted_cohorts["customer_count"]
).sum() / discounted_cohorts["customer_count"].sum()

discounted_clv = (
    discounted_cohorts["average_realized_clv_180"]
    * discounted_cohorts["customer_count"]
).sum() / discounted_cohorts["customer_count"].sum()

largest_segment = segment_df.loc[
    segment_df["total_contribution_margin"].idxmax()
]

highest_margin_segment = segment_df.loc[
    segment_df["average_order_margin"].idxmax()
]



# ---------------------------------------------------------
# DASHBOARD HEADER
# ---------------------------------------------------------

st.title("The Discount Addiction Problem")

st.markdown(
    """
    **A product and business analytics case study on discount economics,
    customer behavior, and incremental contribution margin.**
    """
)

st.subheader(
    "Do discounts create long-term customer value, "
    "or do they train customers to wait for the next markdown?"
)

st.caption(
    "Olist Brazilian E-Commerce dataset | Scenario-based discount simulator"
)

st.markdown(
    """
    This dashboard evaluates discount strategy using the Olist
    Brazilian E-Commerce dataset as the transaction-data foundation.

    Because Olist does not contain historical promotion campaigns,
    observed discounts, product cost, or explicit return events,
    discount, promotion, and margin fields are modeled as a
    documented synthetic scenario layer.
    """
)

st.warning(
    """
    **Important methodology note:** Simulator, discount, promotion,
    and margin results are scenario-based estimates. Cohort and
    regression results are descriptive and do not establish causal
    discount impact. A randomized holdout experiment is required
    before implementing the recommendation in a real business.
    """
)

with st.expander("How to use this dashboard"):
    st.markdown(
        """
        **1. Executive Summary**  
        Review the recommended discount policy and headline economics.

        **2. Policy Simulator**  
        Select an elasticity scenario and discount policy to explore
        expected orders, discount cost, and incremental contribution margin.

        **3. Segment Economics**  
        Compare customer segments based on size, discount dependency,
        order margin, and total contribution margin.

        **4. Cohort Analysis**  
        Compare first-order discount groups using 180-day repeat rate
        and realized CLV.

        **5. Sensitivity Analysis**  
        Evaluate whether the targeted discount recommendation remains
        attractive under conservative, base, and optimistic assumptions.
        """
    )

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------

st.sidebar.title("Discount Analytics")

st.sidebar.caption(
    "Product & Business Analytics Case Study"
)

page = st.sidebar.radio(
    "Navigate to",
    [
        "Executive Summary",
        "Policy Simulator",
        "Segment Economics",
        "Cohort Analysis",
        "Sensitivity Analysis",
        "Data & Methodology"
    ]
)

st.sidebar.divider()

st.sidebar.markdown(
    """
    ### About

    **Dataset:** Olist Brazilian E-Commerce

    **Core question:**  
    Do discounts create incremental long-term customer value?

    **Method:**  
    Descriptive analysis + segmentation +
    scenario simulation.

    **Important:**  
    Discount and margin fields are synthetic
    scenario inputs because historical Olist
    promotion data is unavailable.
    """
)

with st.sidebar.expander("Source & Assumptions"):
    st.markdown(
        """
        **Data foundation**

        Olist Brazilian E-Commerce dataset.

        **Observed**

        Customer, order, product, payment, and transaction data.

        **Synthetic / estimated**

        Discount, promotion, margin, and elasticity inputs.

        **Primary business metric**

        Incremental contribution margin.

        **Validation**

        Randomized experiment with a no-offer control and
        targeted treatment.
        """
    )

st.divider()

if page == "Executive Summary":
    # ---------------------------------------------------------
    # DASHBOARD STATUS
    # ---------------------------------------------------------

    st.info(
        """
        This dashboard is currently under development.

        The next stages will connect the dashboard to the project's
        existing analysis outputs, customer segmentation results,
        discount simulator, and sensitivity analysis.
        """
    )

    st.header("Executive Summary")

    st.caption(
        "Decision status: Scenario recommendation - experimental validation pending"
    )

    st.markdown(
        """
        ### Business Decision

        Under the current modeled scenarios, **TARGETED15** produces
        the highest estimated incremental contribution margin.
        """
    )

    # ---------------------------------------------------------
    # EXECUTIVE KPIs
    # ---------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Recommended Policy",
            targeted["scenario"]
        )

    with col2:
        st.metric(
            "Incremental Margin",
            f'R${targeted["incremental_margin_vs_no_offer"]:,.2f}'
        )

    with col3:
        st.metric(
            "Customers Targeted",
            f'{int(targeted["customers_offered"]):,}'
        )

    with col4:
        st.metric(
            "Discount Cost",
            f'R${targeted["expected_discount_cost"]:,.2f}'
        )

    st.divider()

    st.subheader("Why TARGETED15?")

    summary_comparison = simulator_df[
        simulator_df["scenario"].isin(
            ["NO_OFFER", "BLANKET30", "TARGETED15"]
        )
    ].copy()

    summary_comparison["policy_label"] = summary_comparison[
        "scenario"
    ].map({
        "NO_OFFER": "No Offer",
        "TARGETED15": "Targeted 15%",
        "BLANKET30": "Blanket 30%"
    })

    fig_summary = px.bar(
        summary_comparison,
        x="policy_label",
        y="expected_contribution_margin",
        text="expected_contribution_margin",
        title="Expected Contribution Margin - Base Case",
        labels={
            "policy_label": "Discount Policy",
            "expected_contribution_margin":
                "Expected Contribution Margin (R$)"
        }
    )

    fig_summary.update_traces(
        texttemplate="R$%{text:,.0f}",
        textposition="outside"
    )

    fig_summary.update_layout(
        height=500,
        showlegend=False
    )

    st.plotly_chart(
        fig_summary,
        width="stretch"
    )

    st.success(
        """
        **Key finding:** TARGETED15 slightly outperforms the no-offer
        baseline in the base-case simulation, while BLANKET30 produces
        a large negative incremental contribution margin.

        This suggests that discounting should be selective rather than
        broadly applied.
        """
    )

    st.subheader("Most Important Customer Economics")

    insight_col1, insight_col2 = st.columns(2)

    with insight_col1:
        st.metric(
            "Largest Contribution Segment",
            largest_segment["customer_segment"]
        )

        st.write(
            """
            This segment represents the largest customer population and
            therefore contributes the largest total contribution margin.
            """
        )

    with insight_col2:
        st.metric(
            "Highest Average Order Margin",
            highest_margin_segment["customer_segment"]
        )

        st.write(
            """
            This segment has substantially higher average order margin
            and is more economically attractive for targeted intervention.
            """
        )

    st.divider()

    st.subheader("Customer Value Signal")

    cohort_col1, cohort_col2 = st.columns(2)

    with cohort_col1:
        st.metric(
            "Full-Price 180-Day CLV",
            f"R${full_price_clv:,.2f}"
        )

    with cohort_col2:
        st.metric(
            "Discounted 180-Day CLV",
            f"R${discounted_clv:,.2f}"
        )

    st.info(
        """
        Customers with discounted first orders show lower average
        realized 180-day CLV than the full-price cohort in the observed
        data. This is a descriptive cohort difference and should not be
        interpreted as evidence that discounts caused the lower CLV.
        """
    )

    st.divider()

    st.subheader("Recommended Next Action")

    st.warning(
        """
        **Do not deploy TARGETED15 directly from this analysis.**

        Validate the recommendation through a randomized experiment with:

        - No-offer control
        - 30% blanket discount treatment
        - 15% targeted discount treatment
        - Targeted holdout

        Use **incremental 90-day contribution margin per eligible
        customer** as the primary decision metric.
        """
    )

    st.divider()

    st.subheader("From Scenario Model to Real Business Decision")

    st.markdown(
        """
        Under the modeled Conservative, Base, and Optimistic scenarios,
        **TARGETED15** produces the highest estimated incremental
        contribution margin.

        However, the simulator cannot determine whether discounts
        actually caused the observed or simulated customer outcomes.

        The next step is therefore a **randomized controlled experiment**.
        """
    )

    experiment_col1, experiment_col2 = st.columns(2)

    with experiment_col1:
        st.markdown("### Test Groups")

        st.markdown(
            """
            **Control**

            No discount offer.

            **Treatment 1**

            30% blanket discount.

            **Treatment 2**

            15% targeted discount.

            **Targeted Holdout**

            Eligible customers who do not receive the targeted offer.
            """
        )

    with experiment_col2:
        st.markdown("### Primary Decision Metric")

        st.metric(
            "Primary Metric",
            "90-Day Contribution Margin / Eligible Customer"
        )

        st.markdown(
            """
            The experiment should evaluate **incremental contribution
            margin**, rather than relying only on conversion rate,
            order volume, or revenue.

            This prevents a discount from appearing successful simply
            because it generates more orders while reducing profitability.
            """
        )

    st.markdown("### Decision Framework")

    decision_table = pd.DataFrame({
        "Experiment Result": [
            "Targeted15 improves contribution margin",
            "Targeted15 increases orders but reduces margin",
            "No meaningful difference",
            "Blanket30 performs worse"
        ],
        "Business Interpretation": [
            "Consider targeted discount deployment",
            "Do not optimize for orders alone",
            "Retain the simpler policy until stronger evidence exists",
            "Avoid broad discounting"
        ]
    })

    st.dataframe(
        decision_table,
        width="stretch",
        hide_index=True
    )

    st.success(
        """
        **Current recommendation:** Treat TARGETED15 as the leading
        hypothesis, not as a proven causal strategy.

        The business decision should be made only after randomized
        experimental evidence confirms positive incremental contribution
        margin.
        """
    )

    st.success(
        """
        ### Current Decision

        **Use TARGETED15 as the leading experimental hypothesis.**

        Do not deploy it solely from the simulator. Validate whether it
        produces positive incremental 90-day contribution margin per
        eligible customer through randomized experimentation.
        """
    )

if page == "Policy Simulator":
    # ---------------------------------------------------------
    # INTERACTIVE POLICY SIMULATOR
    # ---------------------------------------------------------

    st.divider()

    st.header("Interactive Discount Policy Simulator")

    st.write(
        """
        Explore how the estimated economics change under different
        discount policies and elasticity assumptions.
        """
    )

    control_col1, control_col2 = st.columns([1, 1])

    policy_labels = {
        "NO_OFFER": "No Offer",
        "TARGETED15": "Targeted 15%",
        "BLANKET30": "Blanket 30%"
    }

    policy_lookup = {
        label: policy
        for policy, label in policy_labels.items()
    }

    with control_col1:
        selected_scenario = st.selectbox(
            "Elasticity Scenario",
            [
                "Conservative",
                "Base",
                "Optimistic"
            ],
            index=1
        )

    with control_col2:
        selected_policy_label = st.selectbox(
            "Discount Policy",
            [
                "No Offer",
                "Targeted 15%",
                "Blanket 30%"
            ],
            index=1
        )

    selected_policy = policy_lookup[selected_policy_label]

    selected_result = sensitivity_df[
        (sensitivity_df["elasticity_scenario"] == selected_scenario)
        & (sensitivity_df["scenario"] == selected_policy)
    ]

    if selected_result.empty:
        st.warning("No simulator result found for this combination.")
    else:
        result = selected_result.iloc[0]

        metric1, metric2, metric3, metric4 = st.columns(4)

        with metric1:
            st.metric(
                "Customers Offered",
                f"{int(result['customers_offered']):,}"
            )

        with metric2:
            st.metric(
                "Expected Orders",
                f"{result['expected_orders']:,.2f}"
            )

        with metric3:
            st.metric(
                "Discount Cost",
                f"R${result['expected_discount_cost']:,.2f}"
            )

        with metric4:
            st.metric(
                "Incremental Margin",
                f"R${result['incremental_margin_vs_no_offer']:,.2f}"
            )

        st.info(
            """
            **How to interpret this result:** The simulator estimates the
            economic outcome under a specified elasticity scenario. It does
            not represent an observed historical promotion result.
            """
        )

        st.subheader("Selected Policy Result")

        if selected_policy == "NO_OFFER":
            st.info(
                f"""
                **No Offer** is the baseline scenario.

                Under the **{selected_scenario}** elasticity assumption,
                estimated contribution margin is
                **R${result['expected_contribution_margin']:,.2f}**.
                """
            )

        elif selected_policy == "TARGETED15":
            st.success(
                f"""
                **Targeted 15% discounting** offers discounts only to the
                selected eligible customers.

                Under the **{selected_scenario}** elasticity assumption,
                estimated incremental contribution margin versus no offer is
                **R${result['incremental_margin_vs_no_offer']:,.2f}**.
                """
            )

        elif selected_policy == "BLANKET30":
            st.warning(
                f"""
                **Blanket 30% discounting** applies the discount broadly.

                Under the **{selected_scenario}** elasticity assumption,
                estimated incremental contribution margin versus no offer is
                **R${result['incremental_margin_vs_no_offer']:,.2f}**.
                """
            )

    # ---------------------------------------------------------
    # POLICY COMPARISON CHART
    # ---------------------------------------------------------

    st.divider()

    st.header("Discount Policy Comparison")

    st.write(
        f"""
        Estimated incremental contribution margin under the
        **{selected_scenario}** elasticity scenario.
        """
    )

    comparison_df = sensitivity_df[
        sensitivity_df["elasticity_scenario"] == selected_scenario
    ].copy()

    comparison_df["policy_label"] = comparison_df["scenario"].map({
        "NO_OFFER": "No Offer",
        "TARGETED15": "Targeted 15%",
        "BLANKET30": "Blanket 30%"
    })

    fig = px.bar(
        comparison_df,
        x="policy_label",
        y="incremental_margin_vs_no_offer",
        text="incremental_margin_vs_no_offer",
        title=f"Incremental Contribution Margin - {selected_scenario} Scenario",
        labels={
            "policy_label": "Discount Policy",
            "incremental_margin_vs_no_offer":
                "Incremental Contribution Margin (R$)"
        }
    )

    fig.update_traces(
        texttemplate="R$%{text:,.2f}",
        textposition="outside"
    )

    fig.add_hline(
        y=0,
        line_dash="dash"
    )

    fig.update_layout(
        height=500,
        showlegend=False
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

    # ---------------------------------------------------------
    # DISCOUNT POLICY SIMULATOR
    # ---------------------------------------------------------

    st.divider()

    st.header("Discount Policy Simulator")

    st.markdown(
        """
        The simulator compares alternative discount policies using
        expected orders, discount cost, and contribution margin.
        """
    )

    # Sort policies into a consistent order
    policy_order = [
        "NO_OFFER",
        "BLANKET30",
        "TARGETED15"
    ]

    policy_df = simulator_df.copy()

    policy_df["scenario"] = pd.Categorical(
        policy_df["scenario"],
        categories=policy_order,
        ordered=True
    )

    policy_df = policy_df.sort_values("scenario")

    # ---------------------------------------------------------
    # CONTRIBUTION MARGIN CHART
    # ---------------------------------------------------------

    st.subheader("Expected Contribution Margin by Discount Policy")

    margin_chart = policy_df.set_index("scenario")[
        "expected_contribution_margin"
    ]

    st.bar_chart(
        margin_chart,
        width="stretch"
    )

if page == "Segment Economics":
    # ---------------------------------------------------------
    # CUSTOMER SEGMENT ECONOMICS
    # ---------------------------------------------------------

    st.divider()

    st.header("Customer Segment Economics")

    st.markdown(
        """
        Customer segments are evaluated using discount dependency,
        average order margin, and total contribution margin.
        """
    )

    # ---------------------------------------------------------
    # SEGMENT CONTRIBUTION MARGIN
    # ---------------------------------------------------------

    st.subheader("Customer Segment Contribution Margin")

    segment_margin_chart = segment_df.set_index(
        "customer_segment"
    )["total_contribution_margin"]

    st.bar_chart(
        segment_margin_chart,
        width="stretch"
    )

    # ---------------------------------------------------------
    # AVERAGE ORDER MARGIN
    # ---------------------------------------------------------

    st.subheader("Average Order Margin by Customer Segment")

    segment_margin_per_order = segment_df.set_index(
        "customer_segment"
    )["average_order_margin"]

    st.bar_chart(
        segment_margin_per_order,
        width="stretch"
    )

    # ---------------------------------------------------------
    # SEGMENT ECONOMICS TABLE
    # ---------------------------------------------------------

    st.subheader("Segment Economics Detail")

    display_segments = segment_df[
        [
            "customer_segment",
            "customer_count",
            "average_discount_dependency_score",
            "average_order_margin",
            "total_contribution_margin"
        ]
    ].rename(
        columns={
            "customer_segment": "Customer Segment",
            "customer_count": "Customer Count",
            "average_discount_dependency_score":
                "Avg Discount Dependency Score",
            "average_order_margin": "Average Order Margin (R$)",
            "total_contribution_margin":
                "Total Contribution Margin (R$)"
        }
    )

    st.dataframe(
        display_segments,
        width="stretch",
        hide_index=True
    )

    st.info(
        """
        **Business interpretation:** Segment size and segment profitability
        are not the same thing. The New / one-order customer segment
        contributes the largest total contribution margin because of its
        large population, while Deal-responsive profitable customers have
        the highest average order margin among the listed segments.
        """
    )

    st.warning(
        """
        **Targeting caution:** Discount-dependent low-margin customers have
        high discount dependency but relatively low average order margin.
        Discounting this segment broadly may destroy contribution margin.
        """
    )

if page == "Cohort Analysis":
    # ---------------------------------------------------------
    # FIRST-ORDER DISCOUNT & RETENTION
    # ---------------------------------------------------------

    st.divider()

    st.header("First-Order Discount, Retention & CLV")

    st.markdown(
        """
        This analysis compares customers based on the discount applied
        to their first order and examines their observed 180-day repeat
        rate and realized customer lifetime value.
        """
    )

    st.subheader("180-Day Repeat Rate by First-Order Discount")

    repeat_rate_chart = cohort_df.set_index(
        "first_order_discount_band"
    )["repeat_rate_180_days"]

    st.bar_chart(
        repeat_rate_chart,
        width="stretch"
    )

    st.subheader("180-Day Realized CLV (R$) by First-Order Discount")

    clv_chart = cohort_df.set_index(
        "first_order_discount_band"
    )["average_realized_clv_180"]

    st.bar_chart(
        clv_chart,
        width="stretch"
    )

    st.subheader("Cohort Results")

    display_cohort = cohort_df.rename(
        columns={
            "first_order_discount_band": "First-Order Discount Band",
            "customer_count": "Customer Count",
            "repeat_rate_180_days": "180-Day Repeat Rate (%)",
            "average_realized_clv_180": "Average Realized 180-Day CLV (R$)",
            "median_realized_clv_180": "Median Realized 180-Day CLV (R$)",
            "average_discount_dependency_score":
                "Avg Discount Dependency Score",
            "repeat_rate_standard_error": "Repeat Rate Standard Error",
            "repeat_rate_ci_95": "Repeat Rate 95% CI"
        }
    ).copy()

    display_cohort["180-Day Repeat Rate (%)"] = (
        display_cohort["180-Day Repeat Rate (%)"] * 100
    )

    st.dataframe(
        display_cohort,
        width="stretch",
        hide_index=True
    )

    # ---------------------------------------------------------
    # FULL-PRICE VS DISCOUNTED COMPARISON
    # ---------------------------------------------------------

    st.subheader("Full-Price vs Discounted First Orders")

    comparison_col1, comparison_col2 = st.columns(2)

    with comparison_col1:
        st.metric(
            "Full-Price 180-Day Repeat Rate (%)",
            f"{full_price_repeat * 100:.2f}%"
        )

        st.metric(
            "Full-Price 180-Day CLV (R$)",
            f"R${full_price_clv:,.2f}"
        )

    with comparison_col2:
        st.metric(
            "Discounted 180-Day Repeat Rate (%)",
            f"{discounted_repeat * 100:.2f}%"
        )

        st.metric(
            "Discounted 180-Day CLV (R$)",
            f"R${discounted_clv:,.2f}"
        )

    st.info(
        """
        **Interpretation:** The cohort results are descriptive rather than
        causal. Differences between full-price and discounted customers may
        reflect underlying customer-selection effects rather than the causal
        effect of the discount itself.
        """
    )

if page == "Sensitivity Analysis":
    # ---------------------------------------------------------
    # SENSITIVITY ANALYSIS
    # ---------------------------------------------------------

    st.divider()

    st.header("Sensitivity Analysis")

    st.markdown(
        """
        This analysis tests whether the discount-policy recommendation
        changes under conservative, base-case, and optimistic elasticity
        assumptions.
        """
    )

    st.info(
        """
        **Interpretation:** The sensitivity scenarios represent modeled
        assumptions about discount responsiveness. They are not observed
        historical elasticity estimates.
        """
    )

    sensitivity_page_df = sensitivity_df.copy()

    sensitivity_page_df["policy_label"] = sensitivity_page_df[
        "scenario"
    ].map({
        "NO_OFFER": "No Offer",
        "TARGETED15": "Targeted 15%",
        "BLANKET30": "Blanket 30%"
    })

    st.subheader("Incremental Contribution Margin Across Scenarios")

    fig_sensitivity = px.bar(
        sensitivity_page_df,
        x="elasticity_scenario",
        y="incremental_margin_vs_no_offer",
        color="policy_label",
        barmode="group",
        text="incremental_margin_vs_no_offer",
        labels={
            "elasticity_scenario": "Elasticity Scenario",
            "incremental_margin_vs_no_offer":
                "Incremental Contribution Margin (R$)",
            "policy_label": "Discount Policy"
        },
        title="Policy Performance Under Different Elasticity Assumptions"
    )

    fig_sensitivity.update_traces(
        texttemplate="R$%{text:,.0f}",
        textposition="outside"
    )

    fig_sensitivity.add_hline(
        y=0,
        line_dash="dash"
    )

    fig_sensitivity.update_layout(
        height=550
    )

    st.plotly_chart(
        fig_sensitivity,
        width="stretch"
    )

    st.subheader("Scenario Results")

    sensitivity_display = sensitivity_page_df[
        [
            "elasticity_scenario",
            "policy_label",
            "customers_offered",
            "expected_orders",
            "expected_discount_cost",
            "expected_contribution_margin",
            "incremental_margin_vs_no_offer"
        ]
    ].rename(
        columns={
            "elasticity_scenario": "Elasticity Scenario",
            "policy_label": "Discount Policy",
            "customers_offered": "Customers Offered",
            "expected_orders": "Expected Orders",
            "expected_discount_cost": "Expected Discount Cost (R$)",
            "expected_contribution_margin":
                "Expected Contribution Margin (R$)",
            "incremental_margin_vs_no_offer":
                "Incremental Contribution Margin (R$)"
        }
    )

    st.dataframe(
        sensitivity_display,
        width="stretch",
        hide_index=True
    )

    st.subheader("Best Policy by Scenario")

    best_policy_rows = []

    for scenario_name in sensitivity_page_df[
        "elasticity_scenario"
    ].unique():
        scenario_rows = sensitivity_page_df[
            sensitivity_page_df["elasticity_scenario"] == scenario_name
        ]

        best_row = scenario_rows.loc[
            scenario_rows[
                "incremental_margin_vs_no_offer"
            ].idxmax()
        ]

        best_policy_rows.append({
            "elasticity_scenario": scenario_name,
            "best_policy": best_row["policy_label"],
            "incremental_margin_vs_no_offer":
                best_row["incremental_margin_vs_no_offer"]
        })

    best_policy_df = pd.DataFrame(best_policy_rows)

    best_policy_df = best_policy_df.rename(
        columns={
            "elasticity_scenario": "Elasticity Scenario",
            "best_policy": "Best Policy",
            "incremental_margin_vs_no_offer":
                "Incremental Contribution Margin (R$)"
        }
    )

    st.dataframe(
        best_policy_df,
        width="stretch",
        hide_index=True
    )

    st.success(
        """
        **Sensitivity conclusion:** TARGETED15 remains the highest-margin
        policy across the Conservative, Base, and Optimistic scenarios
        in the current simulator.

        However, the absolute incremental margin changes substantially
        across assumptions. The result should therefore be treated as
        decision support rather than causal evidence.
        """
    )

    st.warning(
        """
        **Validation required:** Before deployment, test the targeted
        discount policy through a randomized experiment with a no-offer
        control and appropriate holdout groups. Measure incremental
        contribution margin rather than conversion or order volume alone.
        """
    )

if page == "Data & Methodology":
    st.header("Data & Methodology")

    st.markdown(
        """
        This section explains the analytical foundation of the
        **Discount Addiction Problem** project and distinguishes
        observed transaction data from modeled scenario inputs.
        """
    )

    st.divider()

    st.subheader("Data Source")

    st.markdown(
        """
        The project uses the **Olist Brazilian E-Commerce dataset**
        as the transaction-data foundation.

        The dataset provides historical e-commerce transaction
        information that can be used to analyze customers, orders,
        products, payments, and purchasing behavior.
        """
    )

    st.subheader("Observed / Transaction-Based Data")

    observed_data = pd.DataFrame({
        "Data Area": [
            "Customers",
            "Orders",
            "Order items",
            "Products",
            "Payments",
            "Order timestamps",
            "Customer purchase history"
        ],
        "Used For": [
            "Customer-level analysis",
            "Order and cohort analysis",
            "Order economics",
            "Product-level context",
            "Transaction context",
            "Cohort timing",
            "Repeat-purchase analysis"
        ]
    })

    st.dataframe(
        observed_data,
        width="stretch",
        hide_index=True
    )

    st.subheader("Synthetic Scenario Layer")

    st.warning(
        """
        Olist does not contain observed historical promotion campaigns,
        explicit discount assignments, true product cost, or explicit
        return events.

        Therefore, discount, promotion, margin, and elasticity-related
        fields used by the simulator are documented synthetic or
        estimated scenario inputs.
        """
    )

    st.subheader("Observed, Derived, and Modeled Components")

    methodology_df = pd.DataFrame({
        "Component": [
            "Olist transactions",
            "Customer behavior",
            "First-order cohorts",
            "Discount fields",
            "Promotion assignments",
            "Margin fields",
            "Elasticity assumptions",
            "Policy simulator"
        ],
        "Status": [
            "Observed dataset",
            "Derived from transaction data",
            "Derived analytical view",
            "Synthetic / estimated",
            "Synthetic scenario",
            "Synthetic / estimated",
            "Scenario assumption",
            "Scenario model"
        ]
    })

    st.dataframe(
        methodology_df,
        width="stretch",
        hide_index=True
    )

    st.subheader("Analytical Workflow")

    st.markdown(
        """
        ### 1. Transaction data

        Historical Olist transaction data provides the foundation
        for customer and order-level analysis.

        ### 2. Customer features

        Customer purchase behavior is transformed into analytical
        features such as order frequency, order history, and
        discount-dependency indicators.

        ### 3. Customer segmentation

        Customers are grouped into economically meaningful segments
        based on their observed and derived behavior.

        ### 4. Cohort analysis

        Customers are grouped according to first-order discount bands
        to compare subsequent repeat behavior and realized 180-day CLV.

        ### 5. Scenario simulation

        Synthetic discount and elasticity assumptions are used to
        estimate the economics of different discount policies.

        ### 6. Sensitivity analysis

        Conservative, Base, and Optimistic scenarios test whether
        the modeled recommendation changes under different assumptions.

        ### 7. Experiment design

        A randomized experiment is proposed to determine whether the
        modeled recommendation produces genuine incremental value.
        """
    )

    st.subheader("What This Analysis Can Tell Us")

    st.markdown(
        """
        The analysis can be used to:

        - Compare customer segments economically.
        - Describe differences in repeat behavior across first-order
          discount cohorts.
        - Estimate the economics of alternative discount policies
          under explicit assumptions.
        - Identify which policy performs best within the modeled
          scenarios.
        - Define a real-world experiment for validating the recommendation.
        """
    )

    st.subheader("What This Analysis Cannot Prove")

    st.error(
        """
        The analysis does **not** establish that discounts cause lower
        customer lifetime value or that TARGETED15 will necessarily
        increase long-term profitability in a real business.

        Cohort comparisons are descriptive, and the simulator is
        scenario-based.

        Causal validation requires randomized experimentation.
        """
    )

    st.subheader("Key Modeling Assumptions")

    assumptions = pd.DataFrame({
        "Assumption": [
            "Discount response",
            "Discount cost",
            "Contribution margin",
            "Customer eligibility",
            "Scenario elasticity",
            "Long-term customer value"
        ],
        "Treatment": [
            "Modeled through scenario assumptions",
            "Estimated synthetic discount cost",
            "Estimated synthetic contribution margin",
            "Defined by the project eligibility logic",
            "Conservative / Base / Optimistic",
            "Estimated from observed customer behavior"
        ]
    })

    st.dataframe(
        assumptions,
        width="stretch",
        hide_index=True
    )

    st.divider()

    st.subheader("Validation Requirement")

    st.success(
        """
        The simulator should be treated as a **decision-support tool**
        rather than a causal model.

        Before implementing a discount strategy, the company should run
        a randomized experiment and evaluate **incremental 90-day
        contribution margin per eligible customer**.
        """
    )

    st.markdown(
        """
        ### Detailed Experiment Design

        The complete experiment methodology is documented separately,
        including treatment groups, randomization, primary metrics,
        statistical analysis, guardrails, and decision rules.
        """
    )

    st.code(
        "docs/experiment_design.md",
        language="text"
    )

if page == "Executive Summary":
    # ---------------------------------------------------------
    # DASHBOARD SECTIONS
    # ---------------------------------------------------------

    st.header("Dashboard Sections")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            ### Customer Economics

            - Customer segments
            - Discount dependency
            - Order margin
            - Contribution margin
            """
        )

    with col2:
        st.markdown(
            """
            ### Discount & Retention

            - First-order discount bands
            - 180-day repeat rate
            - 180-day CLV
            - Cohort retention
            """
        )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            ### Discount Policy Simulator

            - No offer
            - Blanket 30%
            - Targeted 15%
            - Incremental contribution margin
            """
        )

    with col2:
        st.markdown(
            """
            ### Sensitivity Analysis

            - Conservative scenario
            - Base scenario
            - Optimistic scenario
            - Policy stability
            """
        )

    st.divider()

    st.caption(
        "Scenario-based analytical dashboard — not causal evidence of discount effectiveness."
    )

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption(
    """
    **The Discount Addiction Problem** | Product & Business Analytics Case Study
    """
)

st.caption(
    """
    Data foundation: Olist Brazilian E-Commerce dataset |
    Discount, promotion, margin, and elasticity fields are synthetic
    or scenario-based where explicitly documented.
    """
)

st.caption(
    """
    This dashboard provides scenario-based decision support and does not
    establish causal discount impact. Randomized experimentation is required
    before implementation.
    """
)