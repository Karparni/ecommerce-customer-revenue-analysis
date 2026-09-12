USE olist_analytics;


-- =========================================================
-- 1. REPEAT VS ONE-TIME CUSTOMER PERFORMANCE
-- =========================================================

WITH payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value
    FROM payments
    GROUP BY order_id
),

customer_orders AS (
    SELECT
        c.customer_unique_id,

        COUNT(
            DISTINCT o.order_id
        ) AS orders,

        SUM(
            p.payment_value
        ) AS total_spend

    FROM orders o

    JOIN customers c
        ON o.customer_id = c.customer_id

    LEFT JOIN payment_totals p
        ON o.order_id = p.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY c.customer_unique_id
)

SELECT
    CASE
        WHEN orders > 1
        THEN 'Repeat Customer'
        ELSE 'One-Time Customer'
    END AS customer_type,

    COUNT(*) AS customers,

    SUM(orders) AS orders,

    ROUND(
        SUM(total_spend),
        2
    ) AS revenue,

    ROUND(
        AVG(total_spend),
        2
    ) AS average_customer_spend

FROM customer_orders

GROUP BY
    CASE
        WHEN orders > 1
        THEN 'Repeat Customer'
        ELSE 'One-Time Customer'
    END

ORDER BY revenue DESC;



-- =========================================================
-- 2. CUSTOMER PURCHASE FREQUENCY DISTRIBUTION
-- =========================================================

WITH customer_orders AS (
    SELECT
        c.customer_unique_id,

        COUNT(
            DISTINCT o.order_id
        ) AS order_count

    FROM orders o

    JOIN customers c
        ON o.customer_id = c.customer_id

    WHERE o.order_status = 'delivered'

    GROUP BY c.customer_unique_id
)

SELECT
    order_count,
    COUNT(*) AS customers

FROM customer_orders

GROUP BY order_count

ORDER BY order_count;



-- =========================================================
-- 3. TOP 20 CUSTOMERS BY TOTAL SPEND
-- =========================================================

WITH payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS payment_value
    FROM payments
    GROUP BY order_id
),

customer_value AS (
    SELECT
        c.customer_unique_id,

        COUNT(
            DISTINCT o.order_id
        ) AS orders,

        SUM(
            p.payment_value
        ) AS total_spend,

        MAX(
            o.order_purchase_timestamp
        ) AS last_purchase

    FROM orders o

    JOIN customers c
        ON o.customer_id = c.customer_id

    LEFT JOIN payment_totals p
        ON o.order_id = p.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY c.customer_unique_id
),

ranked_customers AS (
    SELECT
        customer_unique_id,
        orders,
        total_spend,
        last_purchase,

        DENSE_RANK() OVER (
            ORDER BY total_spend DESC
        ) AS spend_rank

    FROM customer_value
)

SELECT
    spend_rank,
    customer_unique_id,
    orders,

    ROUND(
        total_spend,
        2
    ) AS total_spend,

    last_purchase

FROM ranked_customers

WHERE spend_rank <= 20

ORDER BY spend_rank;



-- =========================================================
-- 4. CUSTOMER COHORT RETENTION
-- =========================================================

-- A cohort is a group of customers whose first
-- delivered purchase happened in the same month.


-- First, get every month each customer made
-- at least one delivered purchase.
WITH customer_purchases AS (
    SELECT DISTINCT
        c.customer_unique_id,

        DATE_FORMAT(
            o.order_purchase_timestamp,
            '%Y-%m-01'
        ) AS purchase_month

    FROM orders o

    JOIN customers c
        ON o.customer_id = c.customer_id

    WHERE o.order_status = 'delivered'
),


-- Find each customer's TRUE first purchase month.
first_purchase AS (
    SELECT
        customer_unique_id,

        MIN(
            purchase_month
        ) AS cohort_month

    FROM customer_purchases

    GROUP BY customer_unique_id
),


-- Compare every later purchase month with
-- that customer's first purchase month.
cohort_activity AS (
    SELECT
        cp.customer_unique_id,

        fp.cohort_month,

        cp.purchase_month,

        TIMESTAMPDIFF(
            MONTH,
            fp.cohort_month,
            cp.purchase_month
        ) AS cohort_index

    FROM customer_purchases cp

    JOIN first_purchase fp
        ON cp.customer_unique_id
        = fp.customer_unique_id
),


-- Count how many unique customers from each
-- cohort were active in each later month.
cohort_counts AS (
    SELECT
        cohort_month,
        cohort_index,

        COUNT(
            DISTINCT customer_unique_id
        ) AS active_customers

    FROM cohort_activity

    GROUP BY
        cohort_month,
        cohort_index
),


-- Month 0 contains the original size
-- of each cohort.
cohort_sizes AS (
    SELECT
        cohort_month,

        active_customers AS cohort_size

    FROM cohort_counts

    WHERE cohort_index = 0
)


SELECT
    cc.cohort_month,

    cc.cohort_index,

    cc.active_customers,

    cs.cohort_size,

    ROUND(
        cc.active_customers
        / cs.cohort_size
        * 100,
        2
    ) AS retention_rate_pct

FROM cohort_counts cc

JOIN cohort_sizes cs
    ON cc.cohort_month
    = cs.cohort_month

WHERE
    cc.cohort_index <= 5

    -- We calculate true first purchases using
    -- all available data, but only DISPLAY
    -- cohorts starting from 2017.
    AND cc.cohort_month >= '2017-01-01'

ORDER BY
    cc.cohort_month,
    cc.cohort_index;