USE olist_analytics;


-- =========================================================
-- 1. TOP PRODUCT CATEGORIES BY REVENUE
-- =========================================================

WITH category_orders AS (
    SELECT
        oi.order_id,

        p.product_category_name_english AS category,

        COUNT(*) AS units_sold,

        SUM(oi.price) AS merchandise_revenue

    FROM order_items oi

    JOIN products p
        ON oi.product_id = p.product_id

    GROUP BY
        oi.order_id,
        p.product_category_name_english
),

review_summary AS (
    SELECT
        order_id,
        AVG(review_score) AS review_score

    FROM reviews

    GROUP BY order_id
)

SELECT
    co.category,

    COUNT(
        DISTINCT co.order_id
    ) AS orders,

    SUM(
        co.units_sold
    ) AS units_sold,

    ROUND(
        SUM(co.merchandise_revenue),
        2
    ) AS merchandise_revenue,

    ROUND(
        SUM(co.merchandise_revenue)
        / COUNT(DISTINCT co.order_id),
        2
    ) AS average_category_spend_per_order,

    ROUND(
        AVG(r.review_score),
        2
    ) AS average_review_score

FROM category_orders co

JOIN orders o
    ON co.order_id = o.order_id

LEFT JOIN review_summary r
    ON co.order_id = r.order_id

WHERE o.order_status = 'delivered'

GROUP BY co.category

ORDER BY merchandise_revenue DESC

LIMIT 10;



-- =========================================================
-- 2. PRODUCT CATEGORY DELIVERY + REVIEW PERFORMANCE
-- =========================================================

WITH category_orders AS (
    SELECT
        oi.order_id,

        p.product_category_name_english AS category,

        SUM(oi.price) AS merchandise_revenue

    FROM order_items oi

    JOIN products p
        ON oi.product_id = p.product_id

    GROUP BY
        oi.order_id,
        p.product_category_name_english
),

review_summary AS (
    SELECT
        order_id,
        AVG(review_score) AS review_score

    FROM reviews

    GROUP BY order_id
),

category_performance AS (
    SELECT
        co.category,

        COUNT(
            DISTINCT co.order_id
        ) AS orders,

        AVG(
            r.review_score
        ) AS average_review_score,

        AVG(
            TIMESTAMPDIFF(
                HOUR,
                o.order_purchase_timestamp,
                o.order_delivered_customer_date
            ) / 24.0
        ) AS average_delivery_days,

        AVG(
            CASE

                WHEN
                    o.order_delivered_customer_date IS NULL
                    OR o.order_estimated_delivery_date IS NULL
                THEN NULL

                WHEN
                    o.order_delivered_customer_date
                    > o.order_estimated_delivery_date
                THEN 1

                ELSE 0

            END
        ) * 100 AS late_delivery_rate

    FROM category_orders co

    JOIN orders o
        ON co.order_id = o.order_id

    LEFT JOIN review_summary r
        ON co.order_id = r.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY co.category
)

SELECT
    category,
    orders,

    ROUND(
        average_review_score,
        2
    ) AS average_review_score,

    ROUND(
        late_delivery_rate,
        2
    ) AS late_delivery_rate_pct,

    ROUND(
        average_delivery_days,
        2
    ) AS average_delivery_days

FROM category_performance

WHERE orders >= 500

ORDER BY average_review_score ASC

LIMIT 10;



-- =========================================================
-- 3. TOP SELLERS BY MERCHANDISE REVENUE
-- =========================================================

WITH seller_orders AS (
    SELECT
        oi.order_id,
        oi.seller_id,

        COUNT(*) AS units_sold,

        SUM(
            oi.price
        ) AS merchandise_revenue

    FROM order_items oi

    GROUP BY
        oi.order_id,
        oi.seller_id
),

review_summary AS (
    SELECT
        order_id,
        AVG(review_score) AS review_score

    FROM reviews

    GROUP BY order_id
)

SELECT
    so.seller_id,

    s.seller_city,

    s.seller_state,

    COUNT(
        DISTINCT so.order_id
    ) AS orders,

    SUM(
        so.units_sold
    ) AS units_sold,

    ROUND(
        SUM(so.merchandise_revenue),
        2
    ) AS merchandise_revenue,

    ROUND(
        SUM(so.merchandise_revenue)
        / COUNT(DISTINCT so.order_id),
        2
    ) AS revenue_per_order,

    ROUND(
        AVG(r.review_score),
        2
    ) AS average_review_score

FROM seller_orders so

JOIN orders o
    ON so.order_id = o.order_id

JOIN sellers s
    ON so.seller_id = s.seller_id

LEFT JOIN review_summary r
    ON so.order_id = r.order_id

WHERE o.order_status = 'delivered'

GROUP BY
    so.seller_id,
    s.seller_city,
    s.seller_state

ORDER BY merchandise_revenue DESC

LIMIT 10;



-- =========================================================
-- 4. SELLER REVENUE CONCENTRATION
-- =========================================================

WITH seller_revenue AS (
    SELECT
        oi.seller_id,

        SUM(
            oi.price
        ) AS merchandise_revenue

    FROM order_items oi

    JOIN orders o
        ON oi.order_id = o.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY oi.seller_id
),

ranked_sellers AS (
    SELECT
        seller_id,
        merchandise_revenue,

        ROW_NUMBER() OVER (
            ORDER BY merchandise_revenue DESC
        ) AS seller_rank,

        SUM(
            merchandise_revenue
        ) OVER () AS total_revenue

    FROM seller_revenue
)

SELECT
    COUNT(*) AS active_sellers,

    ROUND(
        SUM(
            CASE
                WHEN seller_rank <= 10
                THEN merchandise_revenue
                ELSE 0
            END
        )
        / MAX(total_revenue)
        * 100,
        2
    ) AS top_10_revenue_share_pct,

    ROUND(
        SUM(
            CASE
                WHEN seller_rank <= 50
                THEN merchandise_revenue
                ELSE 0
            END
        )
        / MAX(total_revenue)
        * 100,
        2
    ) AS top_50_revenue_share_pct,

    ROUND(
        SUM(
            CASE
                WHEN seller_rank <= 100
                THEN merchandise_revenue
                ELSE 0
            END
        )
        / MAX(total_revenue)
        * 100,
        2
    ) AS top_100_revenue_share_pct

FROM ranked_sellers;



-- =========================================================
-- 5. MAJOR SELLERS WITH HIGHEST LATE-DELIVERY RATES
-- =========================================================

WITH seller_orders AS (
    SELECT DISTINCT
        order_id,
        seller_id

    FROM order_items
),

review_summary AS (
    SELECT
        order_id,
        AVG(review_score) AS review_score

    FROM reviews

    GROUP BY order_id
),

seller_performance AS (
    SELECT
        so.seller_id,

        s.seller_city,

        s.seller_state,

        COUNT(
            DISTINCT so.order_id
        ) AS orders,

        AVG(
            CASE

                WHEN
                    o.order_delivered_customer_date IS NULL
                    OR o.order_estimated_delivery_date IS NULL
                THEN NULL

                WHEN
                    o.order_delivered_customer_date
                    > o.order_estimated_delivery_date
                THEN 1

                ELSE 0

            END
        ) * 100 AS late_delivery_rate,

        AVG(
            TIMESTAMPDIFF(
                HOUR,
                o.order_purchase_timestamp,
                o.order_delivered_customer_date
            ) / 24.0
        ) AS average_delivery_days,

        AVG(
            r.review_score
        ) AS average_review_score

    FROM seller_orders so

    JOIN orders o
        ON so.order_id = o.order_id

    JOIN sellers s
        ON so.seller_id = s.seller_id

    LEFT JOIN review_summary r
        ON so.order_id = r.order_id

    WHERE o.order_status = 'delivered'

    GROUP BY
        so.seller_id,
        s.seller_city,
        s.seller_state
)

SELECT
    seller_id,
    seller_city,
    seller_state,
    orders,

    ROUND(
        late_delivery_rate,
        2
    ) AS late_delivery_rate_pct,

    ROUND(
        average_delivery_days,
        2
    ) AS average_delivery_days,

    ROUND(
        average_review_score,
        2
    ) AS average_review_score

FROM seller_performance

WHERE orders >= 100

ORDER BY late_delivery_rate DESC

LIMIT 10;