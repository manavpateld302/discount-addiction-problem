WITH eligible_customers AS (
    SELECT
        customer_unique_id,
        first_order_promotion_id,
        first_order_discount_depth,
        repeat_within_180_days,
        realized_clv_180,
        discount_dependency_score
    FROM customer_features
    WHERE has_180_day_observation_window = 1
),

discount_cohorts AS (
    SELECT
        CASE
            WHEN first_order_discount_depth = 0 THEN '0% (Full price)'
            WHEN first_order_discount_depth <= 0.10 THEN '1-10%'
            WHEN first_order_discount_depth <= 0.15 THEN '11-15%'
            WHEN first_order_discount_depth <= 0.20 THEN '16-20%'
            ELSE '20%+'
        END AS first_order_discount_band,

        customer_unique_id,
        repeat_within_180_days,
        realized_clv_180,
        discount_dependency_score
    FROM eligible_customers
)

SELECT
    first_order_discount_band,
    COUNT(*) AS eligible_customers,
    ROUND(
        100.0 * AVG(repeat_within_180_days),
        2
    ) AS repeat_rate_180_days_pct,
    ROUND(
        AVG(realized_clv_180),
        2
    ) AS average_realized_clv_180,
    ROUND(
        SUM(realized_clv_180),
        2
    ) AS total_realized_clv_180,
    ROUND(
        AVG(discount_dependency_score),
        2
    ) AS average_discount_dependency_score
FROM discount_cohorts
GROUP BY first_order_discount_band
ORDER BY
    CASE first_order_discount_band
        WHEN '0% (Full price)' THEN 1
        WHEN '1-10%' THEN 2
        WHEN '11-15%' THEN 3
        WHEN '16-20%' THEN 4
        ELSE 5
    END;