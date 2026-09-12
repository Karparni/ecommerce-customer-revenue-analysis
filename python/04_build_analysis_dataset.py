from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# 1. PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


# ---------------------------------------------------------
# 2. LOAD CLEANED DATA
# ---------------------------------------------------------

customers = pd.read_csv(
    PROCESSED_DATA_DIR / "customers_clean.csv"
)

orders = pd.read_csv(
    PROCESSED_DATA_DIR / "orders_clean.csv",
    parse_dates=[
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]
)

order_items = pd.read_csv(
    PROCESSED_DATA_DIR / "order_items_clean.csv"
)

payments = pd.read_csv(
    PROCESSED_DATA_DIR / "payments_clean.csv"
)

reviews = pd.read_csv(
    PROCESSED_DATA_DIR / "reviews_clean.csv"
)

print("Clean datasets loaded successfully.")


# ---------------------------------------------------------
# 3. AGGREGATE ORDER ITEMS
# ---------------------------------------------------------

item_summary = (
    order_items
    .groupby("order_id", as_index=False)
    .agg(
        item_count=("order_item_id", "count"),
        merchandise_value=("price", "sum"),
        freight_value=("freight_value", "sum"),
        unique_products=("product_id", "nunique"),
        unique_sellers=("seller_id", "nunique")
    )
)

print(
    f"Order-item summary created: "
    f"{len(item_summary):,} orders"
)


# ---------------------------------------------------------
# 4. AGGREGATE PAYMENTS
# ---------------------------------------------------------

payment_summary = (
    payments
    .groupby("order_id", as_index=False)
    .agg(
        payment_value=("payment_value", "sum"),
        payment_records=("payment_sequential", "count"),
        max_installments=("payment_installments", "max")
    )
)

print(
    f"Payment summary created: "
    f"{len(payment_summary):,} orders"
)


# ---------------------------------------------------------
# 5. AGGREGATE REVIEWS
# ---------------------------------------------------------

review_summary = (
    reviews
    .groupby("order_id", as_index=False)
    .agg(
        review_score=("review_score", "mean")
    )
)

print(
    f"Review summary created: "
    f"{len(review_summary):,} orders"
)


# ---------------------------------------------------------
# 6. BUILD ONE-ROW-PER-ORDER TABLE
# ---------------------------------------------------------

order_analysis = (
    orders
    .merge(
        customers,
        on="customer_id",
        how="left"
    )
    .merge(
        item_summary,
        on="order_id",
        how="left"
    )
    .merge(
        payment_summary,
        on="order_id",
        how="left"
    )
    .merge(
        review_summary,
        on="order_id",
        how="left"
    )
)


# ---------------------------------------------------------
# 7. RECREATE DELIVERY METRICS SAFELY
# ---------------------------------------------------------

order_analysis["delivery_days"] = (
    order_analysis["order_delivered_customer_date"]
    - order_analysis["order_purchase_timestamp"]
).dt.days

order_analysis["delivery_delay_days"] = (
    order_analysis["order_delivered_customer_date"]
    - order_analysis["order_estimated_delivery_date"]
).dt.days


# ---------------------------------------------------------
# 8. CREATE ACCURATE LATE-DELIVERY FLAG
# ---------------------------------------------------------

order_analysis["delivered_late"] = pd.NA

valid_delivery_dates = (
    order_analysis["order_delivered_customer_date"].notna()
    &
    order_analysis["order_estimated_delivery_date"].notna()
)

order_analysis.loc[
    valid_delivery_dates,
    "delivered_late"
] = (
    order_analysis.loc[
        valid_delivery_dates,
        "order_delivered_customer_date"
    ]
    >
    order_analysis.loc[
        valid_delivery_dates,
        "order_estimated_delivery_date"
    ]
)


# ---------------------------------------------------------
# 9. CREATE CUSTOMER PURCHASE FREQUENCY
# ---------------------------------------------------------

delivered_orders = order_analysis[
    order_analysis["order_status"] == "delivered"
].copy()

customer_order_counts = (
    delivered_orders
    .groupby("customer_unique_id")
    .size()
    .rename("customer_delivered_orders")
)

order_analysis = order_analysis.merge(
    customer_order_counts,
    on="customer_unique_id",
    how="left"
)

order_analysis["customer_delivered_orders"] = (
    order_analysis["customer_delivered_orders"]
    .fillna(0)
    .astype(int)
)

order_analysis["is_repeat_customer"] = (
    order_analysis["customer_delivered_orders"] > 1
)


# ---------------------------------------------------------
# 10. BASIC VALIDATION
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("ANALYSIS TABLE VALIDATION")
print("=" * 70)

print(
    f"Rows in orders table:        "
    f"{len(orders):,}"
)

print(
    f"Rows in analysis table:      "
    f"{len(order_analysis):,}"
)

print(
    f"Unique order IDs:            "
    f"{order_analysis['order_id'].nunique():,}"
)

print(
    f"Duplicate order IDs:         "
    f"{order_analysis['order_id'].duplicated().sum():,}"
)

print(
    f"Orders with item data:       "
    f"{order_analysis['item_count'].notna().sum():,}"
)

print(
    f"Orders with payment data:    "
    f"{order_analysis['payment_value'].notna().sum():,}"
)

print(
    f"Orders with review data:     "
    f"{order_analysis['review_score'].notna().sum():,}"
)


# ---------------------------------------------------------
# 11. FIRST BUSINESS KPIs
# ---------------------------------------------------------

delivered = order_analysis[
    order_analysis["order_status"] == "delivered"
].copy()

total_orders = len(delivered)

unique_customers = (
    delivered["customer_unique_id"].nunique()
)

total_merchandise_revenue = (
    delivered["merchandise_value"].sum()
)

total_customer_payments = (
    delivered["payment_value"].sum()
)

average_order_value = (
    total_customer_payments / total_orders
)

repeat_customers = (
    delivered.loc[
        delivered["is_repeat_customer"],
        "customer_unique_id"
    ]
    .nunique()
)

repeat_customer_rate = (
    repeat_customers / unique_customers
) * 100


# Only include orders where both dates exist
valid_delivery = delivered[
    delivered["delivered_late"].notna()
].copy()

late_delivery_rate = (
    valid_delivery["delivered_late"]
    .astype(bool)
    .mean()
) * 100

average_review_score = (
    delivered["review_score"].mean()
)


print("\n" + "=" * 70)
print("FIRST BUSINESS KPIs — DELIVERED ORDERS")
print("=" * 70)

print(
    f"Delivered orders:             "
    f"{total_orders:,}"
)

print(
    f"Unique customers:             "
    f"{unique_customers:,}"
)

print(
    f"Merchandise revenue:          "
    f"R$ {total_merchandise_revenue:,.2f}"
)

print(
    f"Total customer payments:      "
    f"R$ {total_customer_payments:,.2f}"
)

print(
    f"Average order value:          "
    f"R$ {average_order_value:,.2f}"
)

print(
    f"Repeat customers:             "
    f"{repeat_customers:,}"
)

print(
    f"Repeat customer rate:         "
    f"{repeat_customer_rate:.2f}%"
)

print(
    f"Late delivery rate:           "
    f"{late_delivery_rate:.2f}%"
)

print(
    f"Average review score:         "
    f"{average_review_score:.2f} / 5"
)


# ---------------------------------------------------------
# 12. SAVE MASTER ANALYSIS TABLE
# ---------------------------------------------------------

order_analysis.to_csv(
    PROCESSED_DATA_DIR / "order_analysis.csv",
    index=False
)

print(
    "\nMaster analysis dataset saved as:"
)

print(
    "data/processed/order_analysis.csv"
)

print("\nAnalysis dataset build complete.")