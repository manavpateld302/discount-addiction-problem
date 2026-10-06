WITH delivered_orders AS (
    SELECT
        o.customer_unique_id,
        o.order_id,
        DATE_TRUNC(
            'month',
            o.order_purchase_timestamp
        ) AS order_month,
        c.first_order_promotion_id
    FROM orders_enriched AS o
    INNER JOIN customer_features AS c
        ON o.customer_unique_id = c.customer_unique_id
    WHERE o.is_delivered = 1
),

customer_cohorts AS (
    SELECT
        customer_unique_id,
        MIN(order_month) AS cohort_month,
        MAX(first_order_promotion_id) AS first_order_promotion_id
    FROM delivered_orders
    GROUP BY
        customer_unique_id
),

cohort_sizes AS (
    SELECT
        cohort_month,
        first_order_promotion_id,
        COUNT(DISTINCT customer_unique_id) AS cohort_size
    FROM customer_cohorts
    GROUP BY
        cohort_month,
        first_order_promotion_id
),

analysis_end AS (
    SELECT
        MAX(order_month) AS analysis_end_month
    FROM delivered_orders
),

month_numbers AS (
    SELECT 0 AS months_since_first_order
    UNION ALL
    SELECT 1
    UNION ALL
    SELECT 2
    UNION ALL
    SELECT 3
    UNION ALL
    SELECT 4
    UNION ALL
    SELECT 5
    UNION ALL
    SELECT 6
),

cohort_month_grid AS (
    SELECT
        c.cohort_month,
        c.first_order_promotion_id,
        c.cohort_size,
        m.months_since_first_order
    FROM cohort_sizes AS c
    CROSS JOIN month_numbers AS m
),

cohort_activity AS (
    SELECT DISTINCT
        c.customer_unique_id,
        c.cohort_month,
        c.first_order_promotion_id,
        DATE_DIFF(
            'month',
            c.cohort_month,
            d.order_month
        ) AS months_since_first_order
    FROM customer_cohorts AS c
    INNER JOIN delivered_orders AS d
        ON c.customer_unique_id = d.customer_unique_id
),

valid_activity AS (
    SELECT
        a.*
    FROM cohort_activity AS a
    CROSS JOIN analysis_end AS e
    WHERE a.months_since_first_order BETWEEN 0 AND 6
      AND DATE_DIFF(
          'month',
          a.cohort_month,
          e.analysis_end_month
      ) >= a.months_since_first_order
),

retention_counts AS (
    SELECT
        cohort_month,
        first_order_promotion_id,
        months_since_first_order,
        COUNT(DISTINCT customer_unique_id) AS active_customers
    FROM valid_activity
    GROUP BY
        cohort_month,
        first_order_promotion_id,
        months_since_first_order
)

SELECT
    g.cohort_month,
    g.first_order_promotion_id,
    g.months_since_first_order,
    g.cohort_size,

    COALESCE(
        r.active_customers,
        0
    ) AS active_customers,

    ROUND(
        100.0
        * COALESCE(
            r.active_customers,
            0
        )
        / NULLIF(
            g.cohort_size,
            0
        ),
        2
    ) AS retention_rate_pct

FROM cohort_month_grid AS g

LEFT JOIN retention_counts AS r
    ON g.cohort_month = r.cohort_month
    AND g.first_order_promotion_id =
        r.first_order_promotion_id
    AND g.months_since_first_order =
        r.months_since_first_order

-- Do not show months that cannot yet be observed.
CROSS JOIN analysis_end AS e

WHERE DATE_DIFF(
    'month',
    g.cohort_month,
    e.analysis_end_month
) >= g.months_since_first_order

ORDER BY
    g.cohort_month,
    g.first_order_promotion_id,
    g.months_since_first_order;