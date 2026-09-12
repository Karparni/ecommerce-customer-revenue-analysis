USE olist_analytics;


-- =========================================================
-- 1. OVERALL BUSINESS KPIs
-- =========================================================

WITH item_totals AS (
    SELECT
        order_id,
        SUM(price) AS merchandise_value,
        SUM(freight_value) AS freight_value,
        COUNT(*) AS items_sold
    FROM order_items
    GROUP BY order_id
),

payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value
    FROM payments
    GROUP BY order_id
),

review_totals AS (
    SELECT
        order_id,
        AVG(review_score) AS review_score
    FROM reviews
    GROUP BY order_id
)

SELECT
    COUNT(DISTINCT o.order_id) AS delivered_orders,

    COUNT(DISTINCT c.customer_unique_id) AS unique_customers,

    ROUND(
        SUM(i.merchandise_value),
        2
    ) AS merchandise_revenue,

    ROUND(
        SUM(p.payment_value),
        2
    ) AS customer_payments,

    ROUND(
        SUM(p.payment_value)
        / COUNT(DISTINCT o.order_id),
        2
    ) AS average_order_value,

    ROUND(
        AVG(r.review_score),
        2
    ) AS average_review_score,

    ROUND(
        AVG(
            CASE
                WHEN o.order_delivered_customer_date
                     > o.order_estimated_delivery_date
                THEN 1
                ELSE 0
            END
        ) * 100,
        2
    ) AS late_delivery_rate_pct

FROM orders o

JOIN customers c
    ON o.customer_id = c.customer_id

LEFT JOIN item_totals i
    ON o.order_id = i.order_id

LEFT JOIN payment_totals p
    ON o.order_id = p.order_id

LEFT JOIN review_totals r
    ON o.order_id = r.order_id

WHERE o.order_status = 'delivered';



-- =========================================================
-- 2. REPEAT CUSTOMER RATE
-- =========================================================

WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS delivered_orders
    FROM orders o

    JOIN customers c
        ON o.customer_id = c.customer_id

    WHERE o.order_status = 'delivered'

    GROUP BY c.customer_unique_id
)

SELECT
    COUNT(*) AS total_customers,

    SUM(
        CASE
            WHEN delivered_orders > 1
            THEN 1
            ELSE 0
        END
    ) AS repeat_customers,

    ROUND(
        SUM(
            CASE
                WHEN delivered_orders > 1
                THEN 1
                ELSE 0
            END
        )
        / COUNT(*) * 100,
        2
    ) AS repeat_customer_rate_pct

FROM customer_orders;



-- =========================================================
-- 3. MONTHLY REVENUE + MONTH-OVER-MONTH GROWTH
-- =========================================================

WITH payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value
    FROM payments
    GROUP BY order_id
),

monthly_sales AS (
    SELECT
        DATE_FORMAT(
            o.order_purchase_timestamp,
            '%Y-%m'
        ) AS purchase_month,

        COUNT(DISTINCT o.order_id) AS orders,

        COUNT(
            DISTINCT c.customer_unique_id
        ) AS customers,

        SUM(p.payment_value) AS revenue

    FROM orders o

    JOIN customers c
        ON o.customer_id = c.customer_id

    LEFT JOIN payment_totals p
        ON o.order_id = p.order_id

    WHERE
        o.order_status = 'delivered'
        AND o.order_purchase_timestamp >= '2017-01-01'
        AND o.order_purchase_timestamp < '2018-09-01'

    GROUP BY
        DATE_FORMAT(
            o.order_purchase_timestamp,
            '%Y-%m'
        )
),

monthly_growth AS (
    SELECT
        purchase_month,
        orders,
        customers,
        revenue,

        LAG(revenue) OVER (
            ORDER BY purchase_month
        ) AS previous_month_revenue

    FROM monthly_sales
)

SELECT
    purchase_month,
    orders,
    customers,

    ROUND(
        revenue,
        2
    ) AS revenue,

    ROUND(
        revenue / orders,
        2
    ) AS average_order_value,

    ROUND(
        (
            revenue
            - previous_month_revenue
        )
        / NULLIF(
            previous_month_revenue,
            0
        ) * 100,
        2
    ) AS revenue_growth_pct

FROM monthly_growth

ORDER BY purchase_month;



-- =========================================================
-- 4. TOP CUSTOMER STATES BY REVENUE
-- =========================================================

WITH payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value
    FROM payments
    GROUP BY order_id
)

SELECT
    c.customer_state,

    COUNT(
        DISTINCT o.order_id
    ) AS orders,

    COUNT(
        DISTINCT c.customer_unique_id
    ) AS customers,

    ROUND(
        SUM(p.payment_value),
        2
    ) AS revenue,

    ROUND(
        SUM(p.payment_value)
        / COUNT(DISTINCT o.order_id),
        2
    ) AS average_order_value

FROM orders o

JOIN customers c
    ON o.customer_id = c.customer_id

LEFT JOIN payment_totals p
    ON o.order_id = p.order_id

WHERE o.order_status = 'delivered'

GROUP BY c.customer_state

ORDER BY revenue DESC

LIMIT 10;