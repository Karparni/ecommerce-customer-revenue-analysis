CREATE DATABASE olist_analytics;

USE olist_analytics;

ALTER USER 'olist_user'@'localhost'
IDENTIFIED BY 'Karisov1';

FLUSH PRIVILEGES;

USE olist_analytics;

-- ---------------------------------------------------------
-- FIX ID DATA TYPES
-- ---------------------------------------------------------

ALTER TABLE customers
    MODIFY customer_id CHAR(32) NOT NULL,
    MODIFY customer_unique_id CHAR(32) NOT NULL;

ALTER TABLE orders
    MODIFY order_id CHAR(32) NOT NULL,
    MODIFY customer_id CHAR(32) NOT NULL;

ALTER TABLE order_items
    MODIFY order_id CHAR(32) NOT NULL,
    MODIFY product_id CHAR(32) NOT NULL,
    MODIFY seller_id CHAR(32) NOT NULL;

ALTER TABLE payments
    MODIFY order_id CHAR(32) NOT NULL;

ALTER TABLE reviews
    MODIFY order_id CHAR(32) NOT NULL;

ALTER TABLE products
    MODIFY product_id CHAR(32) NOT NULL;

ALTER TABLE sellers
    MODIFY seller_id CHAR(32) NOT NULL;


-- ---------------------------------------------------------
-- PRIMARY KEYS
-- ---------------------------------------------------------

ALTER TABLE customers
    ADD PRIMARY KEY (customer_id);

ALTER TABLE orders
    ADD PRIMARY KEY (order_id);

ALTER TABLE products
    ADD PRIMARY KEY (product_id);

ALTER TABLE sellers
    ADD PRIMARY KEY (seller_id);


-- ---------------------------------------------------------
-- INDEXES FOR JOINS
-- ---------------------------------------------------------

CREATE INDEX idx_customers_unique_id
ON customers(customer_unique_id);

CREATE INDEX idx_orders_customer_id
ON orders(customer_id);

CREATE INDEX idx_order_items_order_id
ON order_items(order_id);

CREATE INDEX idx_order_items_product_id
ON order_items(product_id);

CREATE INDEX idx_order_items_seller_id
ON order_items(seller_id);

CREATE INDEX idx_payments_order_id
ON payments(order_id);

CREATE INDEX idx_reviews_order_id
ON reviews(order_id);

SHOW INDEX FROM orders;