USE olist_analytics;


-- =========================================================
-- 1. PAYMENT METHOD PERFORMANCE
-- =========================================================

SELECT
    p.payment_type,

    COUNT(*) AS payment_records,

    COUNT(
        DISTINCT p.order_id
    ) AS orders_using_method,

    ROUND(
        SUM(p.payment_value),
        2
    ) AS payment_value,

    ROUND(
        SUM(p.payment_value)
        / COUNT(DISTINCT p.order_id),
        2
    ) AS average_payment_per_order,

    ROUND(
        SUM(p.payment_value)
        /
        SUM(
            SUM(p.payment_value)
        ) OVER ()
        * 100,
        2
    ) AS payment_value_share_pct

FROM payments p

JOIN orders o
    ON p.order_id = o.order_id

WHERE o.order_status = 'delivered'

GROUP BY p.payment_type

ORDER BY payment_value DESC;



-- =========================================================
-- 2. CREDIT CARD INSTALLMENT PERFORMANCE
-- =========================================================

WITH credit_card_orders AS (
    SELECT
        p.order_id,

        MAX(
            p.payment_installments
        ) AS installments,

        SUM(
            p.payment_value
        ) AS payment_value

    FROM payments p

    JOIN orders o
        ON p.order_id = o.order_id

    WHERE
        o.order_status = 'delivered'
        AND p.payment_type = 'credit_card'

    GROUP BY p.order_id
),

installment_groups AS (
    SELECT
        order_id,
        installments,
        payment_value,

        CASE
            WHEN installments <= 1
                THEN '1 installment'

            WHEN installments <= 3
                THEN '2-3 installments'

            WHEN installments <= 6
                THEN '4-6 installments'

            WHEN installments <= 12
                THEN '7-12 installments'

            ELSE '13+ installments'
        END AS installment_group,

        CASE
            WHEN installments <= 1 THEN 1
            WHEN installments <= 3 THEN 2
            WHEN installments <= 6 THEN 3
            WHEN installments <= 12 THEN 4
            ELSE 5
        END AS sort_order

    FROM credit_card_orders
)

SELECT
    installment_group,

    COUNT(*) AS orders,

    ROUND(
        SUM(payment_value),
        2
    ) AS total_payment_value,

    ROUND(
        AVG(payment_value),
        2
    ) AS average_order_value

FROM installment_groups

GROUP BY
    installment_group,
    sort_order

ORDER BY sort_order;



-- =========================================================
-- 3. ON-TIME VS LATE DELIVERY CUSTOMER SATISFACTION
-- =========================================================

WITH review_summary AS (
    SELECT
        order_id,

        AVG(
            review_score
        ) AS review_score

    FROM reviews

    GROUP BY order_id
)

SELECT
    CASE

        WHEN
            o.order_delivered_customer_date
            > o.order_estimated_delivery_date
        THEN 'Late'

        ELSE 'On Time'

    END AS delivery_status,

    COUNT(
        DISTINCT o.order_id
    ) AS orders,

    ROUND(
        AVG(r.review_score),
        2
    ) AS average_review_score,

    ROUND(
        AVG(
            TIMESTAMPDIFF(
                HOUR,
                o.order_purchase_timestamp,
                o.order_delivered_customer_date
            ) / 24.0
        ),
        2
    ) AS average_delivery_days

FROM orders o

LEFT JOIN review_summary r
    ON o.order_id = r.order_id

WHERE
    o.order_status = 'delivered'

    AND o.order_delivered_customer_date
        IS NOT NULL

    AND o.order_estimated_delivery_date
        IS NOT NULL

GROUP BY
    CASE

        WHEN
            o.order_delivered_customer_date
            > o.order_estimated_delivery_date
        THEN 'Late'

        ELSE 'On Time'

    END;



-- =========================================================
-- 4. DELIVERY PERFORMANCE BY CUSTOMER STATE
-- =========================================================

WITH review_summary AS (
    SELECT
        order_id,

        AVG(
            review_score
        ) AS review_score

    FROM reviews

    GROUP BY order_id
)

SELECT
    c.customer_state,

    COUNT(
        DISTINCT o.order_id
    ) AS delivered_orders,

    ROUND(
        AVG(
            TIMESTAMPDIFF(
                HOUR,
                o.order_purchase_timestamp,
                o.order_delivered_customer_date
            ) / 24.0
        ),
        2
    ) AS average_delivery_days,

    ROUND(
        AVG(
            CASE

                WHEN
                    o.order_delivered_customer_date
                    > o.order_estimated_delivery_date
                THEN 1

                ELSE 0

            END
        ) * 100,
        2
    ) AS late_delivery_rate_pct,

    ROUND(
        AVG(r.review_score),
        2
    ) AS average_review_score

FROM orders o

JOIN customers c
    ON o.customer_id = c.customer_id

LEFT JOIN review_summary r
    ON o.order_id = r.order_id

WHERE
    o.order_status = 'delivered'

    AND o.order_delivered_customer_date
        IS NOT NULL

    AND o.order_estimated_delivery_date
        IS NOT NULL

GROUP BY c.customer_state

HAVING delivered_orders >= 500

ORDER BY late_delivery_rate_pct DESC;