WITH delivered_orders AS (
    SELECT
        o.order_id,
        o.customer_unique_id,
        o.promotion_id,
        o.discount_depth,
        o.discount_amount,
        o.synthetic_merchandise_revenue,
        o.estimated_contribution_margin,
        s.customer_segment,
        s.discount_responsiveness_tier
    FROM orders_enriched AS o
    INNER JOIN customer_segments AS s
        ON o.customer_unique_id = s.customer_unique_id
    WHERE o.is_delivered = 1
)

SELECT
    customer_segment,
    discount_responsiveness_tier,
    promotion_id,

    COUNT(DISTINCT customer_unique_id) AS unique_customers,
    COUNT(*) AS delivered_orders,

    ROUND(
        100.0 * AVG(discount_depth),
        2
    ) AS average_discount_depth_pct,

    ROUND(
        SUM(discount_amount),
        2
    ) AS total_discount_cost,

    ROUND(
        SUM(synthetic_merchandise_revenue),
        2
    ) AS total_synthetic_revenue,

    ROUND(
        SUM(estimated_contribution_margin),
        2
    ) AS total_contribution_margin,

    ROUND(
        AVG(estimated_contribution_margin),
        2
    ) AS average_order_margin

FROM delivered_orders
GROUP BY
    customer_segment,
    discount_responsiveness_tier,
    promotion_id
ORDER BY
    total_contribution_margin DESC;