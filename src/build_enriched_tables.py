
import numpy as np
import pandas as pd

from config import PROCESSED_DATA_DIR, REPORTS_DIR, RANDOM_SEED


# Categories used for the synthetic CATEGORY15 campaign.
CAMPAIGN_CATEGORIES = {
    "health_beauty",
    "watches_gifts",
    "toys",
    "sports_leisure",
    "bed_bath_table",
    "cool_stuff",
}

# Categories used for estimated margin assumptions.
HIGH_MARGIN_CATEGORIES = {
    "health_beauty",
    "perfumery",
    "watches_gifts",
    "stationery",
    "toys",
    "cool_stuff",
}

LOW_MARGIN_CATEGORIES = {
    "computers_accessories",
    "electronics",
    "telephony",
    "consoles_games",
    "small_appliances",
    "small_appliances_home_oven_and_coffee",
}


def load_table(file_name: str) -> pd.DataFrame:
    """Load one clean Parquet table."""
    file_path = PROCESSED_DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Could not find {file_name}. Run build_clean_tables.py first."
        )

    return pd.read_parquet(file_path)


def create_order_category_flags(order_items: pd.DataFrame) -> pd.DataFrame:
    """
    Create one category flag per order.

    An order is campaign-eligible if it contains at least one selected category.
    """
    items = order_items.copy()

    items["is_campaign_category"] = items[
        "product_category_name_english"
    ].isin(CAMPAIGN_CATEGORIES)

    category_flags = (
        items.groupby("order_id", as_index=False)
        .agg(
            order_has_campaign_category=("is_campaign_category", "max"),
            order_item_count=("order_item_id", "count"),
        )
    )

    return category_flags


def assign_synthetic_promotions(
    orders: pd.DataFrame,
    category_flags: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create one synthetic promotion assignment per order.

    Promotion rules:
    - First delivered order: eligible for WELCOME10
    - Delivered order after 60+ inactive days: eligible for LAPSED20
    - November/December campaign-category order: eligible for CATEGORY15
    - 70% of eligible orders receive the promotion
    - 30% remain FULL_PRICE synthetic holdouts
    """
    promo_orders = orders.copy()

    promo_orders = promo_orders.merge(
        category_flags,
        on="order_id",
        how="left",
        validate="1:1",
    )

    promo_orders["order_has_campaign_category"] = (
        promo_orders["order_has_campaign_category"]
        .fillna(False)
        .astype(bool)
    )

    promo_orders["order_item_count"] = (
        promo_orders["order_item_count"]
        .fillna(0)
        .astype(int)
    )

    # Default fields for all orders.
    promo_orders["promotion_eligible_type"] = "NOT_ELIGIBLE"
    promo_orders["promotion_id"] = "FULL_PRICE"
    promo_orders["discount_pct"] = 0.0
    promo_orders["promotion_offer_assigned"] = 0

    # Promotions apply only to delivered orders.
    delivered = promo_orders[
        promo_orders["is_delivered"] == 1
    ].copy()

    delivered = delivered.sort_values(
        [
            "customer_unique_id",
            "order_purchase_timestamp",
            "order_id",
        ]
    )

    # These features use only previous orders for the same customer.
    delivered["delivered_order_number"] = (
        delivered.groupby("customer_unique_id").cumcount() + 1
    )

    delivered["previous_delivered_order_date"] = (
        delivered
        .groupby("customer_unique_id")["order_purchase_timestamp"]
        .shift(1)
    )

    delivered["days_since_previous_delivered_order"] = (
        delivered["order_purchase_timestamp"]
        - delivered["previous_delivered_order_date"]
    ).dt.total_seconds() / 86400

    delivered["purchase_month"] = (
        delivered["order_purchase_timestamp"].dt.month
    )

    # Priority is intentional: welcome > lapsed > category promotion.
    first_order_mask = (
        delivered["delivered_order_number"] == 1
    )

    lapsed_mask = (
        ~first_order_mask
        & (
            delivered["days_since_previous_delivered_order"]
            >= 60
        )
    )

    category_campaign_mask = (
        ~first_order_mask
        & ~lapsed_mask
        & delivered["purchase_month"].isin([11, 12])
        & delivered["order_has_campaign_category"]
    )

    delivered.loc[
        first_order_mask,
        "promotion_eligible_type",
    ] = "WELCOME10"

    delivered.loc[
        lapsed_mask,
        "promotion_eligible_type",
    ] = "LAPSED20"

    delivered.loc[
        category_campaign_mask,
        "promotion_eligible_type",
    ] = "CATEGORY15"

    # Reproducible 70% offer / 30% holdout assignment.
    random_generator = np.random.default_rng(RANDOM_SEED)

    eligible_mask = (
        delivered["promotion_eligible_type"]
        != "NOT_ELIGIBLE"
    )

    delivered["promotion_random_number"] = (
        random_generator.random(len(delivered))
    )

    delivered["promotion_offer_assigned"] = (
        eligible_mask
        & (
            delivered["promotion_random_number"]
            < 0.70
        )
    ).astype(int)

    # Assign discount levels only to eligible customers selected for treatment.
    welcome_assigned = (
        (
            delivered["promotion_eligible_type"]
            == "WELCOME10"
        )
        & (
            delivered["promotion_offer_assigned"]
            == 1
        )
    )

    lapsed_assigned = (
        (
            delivered["promotion_eligible_type"]
            == "LAPSED20"
        )
        & (
            delivered["promotion_offer_assigned"]
            == 1
        )
    )

    category_assigned = (
        (
            delivered["promotion_eligible_type"]
            == "CATEGORY15"
        )
        & (
            delivered["promotion_offer_assigned"]
            == 1
        )
    )

    delivered.loc[
        welcome_assigned,
        "promotion_id",
    ] = "WELCOME10"

    delivered.loc[
        welcome_assigned,
        "discount_pct",
    ] = 0.10

    delivered.loc[
        lapsed_assigned,
        "promotion_id",
    ] = "LAPSED20"

    delivered.loc[
        lapsed_assigned,
        "discount_pct",
    ] = 0.20

    delivered.loc[
        category_assigned,
        "promotion_id",
    ] = "CATEGORY15"

    delivered.loc[
        category_assigned,
        "discount_pct",
    ] = 0.15

    # Put the calculated promotion fields back into all orders.
    promotion_columns = [
        "order_id",
        "promotion_eligible_type",
        "promotion_id",
        "discount_pct",
        "promotion_offer_assigned",
        "delivered_order_number",
        "days_since_previous_delivered_order",
    ]

    promotion_result = delivered[
        promotion_columns
    ]

    promo_orders = promo_orders.drop(
        columns=[
            "promotion_eligible_type",
            "promotion_id",
            "discount_pct",
            "promotion_offer_assigned",
        ]
    )

    promo_orders = promo_orders.merge(
        promotion_result,
        on="order_id",
        how="left",
        validate="1:1",
    )

    # Non-delivered orders and non-eligible orders remain full-price.
    promo_orders["promotion_eligible_type"] = (
        promo_orders["promotion_eligible_type"]
        .fillna("NOT_ELIGIBLE")
    )

    promo_orders["promotion_id"] = (
        promo_orders["promotion_id"]
        .fillna("FULL_PRICE")
    )

    promo_orders["discount_pct"] = (
        promo_orders["discount_pct"]
        .fillna(0.0)
    )

    promo_orders["promotion_offer_assigned"] = (
        promo_orders["promotion_offer_assigned"]
        .fillna(0)
        .astype(int)
    )

    return promo_orders


def assign_cost_rate(category_name: str) -> tuple[str, float]:
    """Return a margin tier and estimated product cost rate."""
    if category_name in HIGH_MARGIN_CATEGORIES:
        return "high_margin", 0.45

    if category_name in LOW_MARGIN_CATEGORIES:
        return "low_margin", 0.75

    return "medium_margin", 0.60


def build_enriched_order_items(
    order_items: pd.DataFrame,
    orders_with_promotions: pd.DataFrame,
) -> pd.DataFrame:
    """Add promotion and estimated-cost fields to every order item."""
    items = order_items.copy()

    order_columns = [
        "order_id",
        "is_delivered",
        "is_canceled_or_unavailable",
        "promotion_eligible_type",
        "promotion_id",
        "discount_pct",
        "promotion_offer_assigned",
        "delivered_order_number",
        "days_since_previous_delivered_order",
    ]

    items = items.merge(
        orders_with_promotions[order_columns],
        on="order_id",
        how="left",
        validate="m:1",
    )

    # Olist observed price becomes the project's synthetic baseline list price.
    items["baseline_list_price"] = (
        items["observed_item_price"]
    )

    # Calculate synthetic pricing.
    items["discount_amount"] = (
        items["baseline_list_price"]
        * items["discount_pct"]
    )

    items["synthetic_paid_price"] = (
        items["baseline_list_price"]
        - items["discount_amount"]
    )

    items["is_discounted"] = (
        items["discount_pct"] > 0
    ).astype(int)

    # Assign the documented cost rate by category.
    cost_assignments = (
        items["product_category_name_english"]
        .apply(assign_cost_rate)
    )

    items["margin_tier"] = (
        cost_assignments.apply(lambda x: x[0])
    )

    items["estimated_cost_rate"] = (
        cost_assignments.apply(lambda x: x[1])
    )

    # Economic values apply only to delivered orders.
    delivered_flag = (
        items["is_delivered"].astype(int)
    )

    items["synthetic_merchandise_revenue"] = (
        items["synthetic_paid_price"]
        * delivered_flag
    )

    items["estimated_cogs"] = (
        items["baseline_list_price"]
        * items["estimated_cost_rate"]
        * delivered_flag
    )

    items["estimated_payment_fee"] = (
        items["synthetic_merchandise_revenue"]
        * 0.03
    )

    # Variable fulfillment cost; fixed order cost is allocated later.
    items["estimated_variable_fulfillment_cost"] = (
        items["observed_freight_value"]
        * 0.20
        * delivered_flag
    )

    return items


def build_enriched_orders(
    orders_with_promotions: pd.DataFrame,
    enriched_items: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate enriched item economics to one row per order."""

    order_economics = (
        enriched_items
        .groupby("order_id", as_index=False)
        .agg(
            baseline_merchandise_value=(
                "baseline_list_price",
                "sum",
            ),
            discount_amount=(
                "discount_amount",
                "sum",
            ),
            synthetic_merchandise_revenue=(
                "synthetic_merchandise_revenue",
                "sum",
            ),
            freight_revenue=(
                "observed_freight_value",
                "sum",
            ),
            estimated_cogs=(
                "estimated_cogs",
                "sum",
            ),
            estimated_payment_fee=(
                "estimated_payment_fee",
                "sum",
            ),
            estimated_variable_fulfillment_cost=(
                "estimated_variable_fulfillment_cost",
                "sum",
            ),
            order_item_count=(
                "order_item_id",
                "count",
            ),
        )
    )

    # --------------------------------------------------------
    # FIX:
    #
    # orders_with_promotions already contains order_item_count
    # because it was created in create_order_category_flags().
    #
    # order_economics also creates order_item_count.
    #
    # Remove the old copy before merging so the authoritative
    # order_item_count comes from order_economics.
    # --------------------------------------------------------

    orders_base = orders_with_promotions.drop(
        columns=["order_item_count"],
        errors="ignore",
    )

    enriched_orders = orders_base.merge(
        order_economics,
        on="order_id",
        how="left",
        validate="1:1",
    )

    numeric_columns = [
        "baseline_merchandise_value",
        "discount_amount",
        "synthetic_merchandise_revenue",
        "freight_revenue",
        "estimated_cogs",
        "estimated_payment_fee",
        "estimated_variable_fulfillment_cost",
        "order_item_count",
    ]

    for column in numeric_columns:
        enriched_orders[column] = (
            enriched_orders[column]
            .fillna(0)
        )

    # Fixed fulfillment cost applies only to delivered orders.
    enriched_orders[
        "estimated_fixed_fulfillment_cost"
    ] = (
        5.00
        * enriched_orders["is_delivered"]
    )

    enriched_orders[
        "estimated_fulfillment_cost"
    ] = (
        enriched_orders[
            "estimated_variable_fulfillment_cost"
        ]
        + enriched_orders[
            "estimated_fixed_fulfillment_cost"
        ]
    )

    # Olist does not contain true returns, so no return cost is applied yet.
    enriched_orders[
        "estimated_return_cost"
    ] = 0.0

    enriched_orders[
        "estimated_contribution_margin"
    ] = (
        enriched_orders[
            "synthetic_merchandise_revenue"
        ]
        + (
            enriched_orders[
                "freight_revenue"
            ]
            * enriched_orders[
                "is_delivered"
            ]
        )
        - enriched_orders[
            "estimated_cogs"
        ]
        - enriched_orders[
            "estimated_payment_fee"
        ]
        - enriched_orders[
            "estimated_fulfillment_cost"
        ]
        - enriched_orders[
            "estimated_return_cost"
        ]
    )

    # Revenue-weighted order-level discount depth.
    enriched_orders[
        "discount_depth"
    ] = np.where(
        enriched_orders[
            "baseline_merchandise_value"
        ] > 0,
        enriched_orders[
            "discount_amount"
        ]
        / enriched_orders[
            "baseline_merchandise_value"
        ],
        0.0,
    )

    # Add the fixed fulfillment cost back to items equally,
    # so item margins sum exactly to order contribution margin.
    fixed_cost_per_item = np.where(
        enriched_orders[
            "order_item_count"
        ] > 0,
        enriched_orders[
            "estimated_fixed_fulfillment_cost"
        ]
        / enriched_orders[
            "order_item_count"
        ],
        0.0,
    )

    fixed_cost_lookup = enriched_orders[
        ["order_id"]
    ].copy()

    fixed_cost_lookup[
        "estimated_fixed_fulfillment_cost_per_item"
    ] = fixed_cost_per_item

    enriched_items = enriched_items.merge(
        fixed_cost_lookup,
        on="order_id",
        how="left",
        validate="m:1",
    )

    enriched_items[
        "estimated_item_contribution_margin"
    ] = (
        enriched_items[
            "synthetic_merchandise_revenue"
        ]
        + (
            enriched_items[
                "observed_freight_value"
            ]
            * enriched_items[
                "is_delivered"
            ]
        )
        - enriched_items[
            "estimated_cogs"
        ]
        - enriched_items[
            "estimated_payment_fee"
        ]
        - enriched_items[
            "estimated_variable_fulfillment_cost"
        ]
        - enriched_items[
            "estimated_fixed_fulfillment_cost_per_item"
        ]
    )

    return enriched_orders, enriched_items


def main():
    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "\n--- BUILDING ENRICHED TABLES ---\n"
    )

    orders_clean = load_table(
        "orders_clean.parquet"
    )

    order_items_clean = load_table(
        "order_items_clean.parquet"
    )

    category_flags = create_order_category_flags(
        order_items_clean
    )

    orders_with_promotions = (
        assign_synthetic_promotions(
            orders_clean,
            category_flags,
        )
    )

    order_items_enriched = (
        build_enriched_order_items(
            order_items_clean,
            orders_with_promotions,
        )
    )

    orders_enriched, order_items_enriched = (
        build_enriched_orders(
            orders_with_promotions,
            order_items_enriched,
        )
    )

    # Save the two key analytics tables automatically.
    items_path = (
        PROCESSED_DATA_DIR
        / "order_items_enriched.parquet"
    )

    orders_path = (
        PROCESSED_DATA_DIR
        / "orders_enriched.parquet"
    )

    order_items_enriched.to_parquet(
        items_path,
        index=False,
    )

    orders_enriched.to_parquet(
        orders_path,
        index=False,
    )

    # Create an automatic summary report.
    enrichment_summary = (
        orders_enriched
        .groupby(
            "promotion_id",
            as_index=False,
        )
        .agg(
            orders=(
                "order_id",
                "count",
            ),
            delivered_orders=(
                "is_delivered",
                "sum",
            ),
            average_discount_depth=(
                "discount_depth",
                "mean",
            ),
            total_discount_amount=(
                "discount_amount",
                "sum",
            ),
            total_synthetic_revenue=(
                "synthetic_merchandise_revenue",
                "sum",
            ),
            total_contribution_margin=(
                "estimated_contribution_margin",
                "sum",
            ),
        )
        .sort_values("promotion_id")
    )

    summary_path = (
        REPORTS_DIR
        / "enrichment_summary.csv"
    )

    enrichment_summary.to_csv(
        summary_path,
        index=False,
    )

    print(
        f"Created: {items_path}"
    )

    print(
        f"Created: {orders_path}"
    )

    print(
        f"Created: {summary_path}"
    )

    print(
        "\n--- ENRICHMENT COMPLETE ---\n"
    )


if __name__ == "__main__":
    main()

