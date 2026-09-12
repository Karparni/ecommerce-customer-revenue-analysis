from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# 1. PROJECT PATH
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


# ---------------------------------------------------------
# 2. LOAD CLEAN DATA
# ---------------------------------------------------------

orders = pd.read_csv(
    PROCESSED_DATA_DIR / "orders_clean.csv"
)

order_items = pd.read_csv(
    PROCESSED_DATA_DIR / "order_items_clean.csv"
)

products = pd.read_csv(
    PROCESSED_DATA_DIR / "products_clean.csv"
)

reviews = pd.read_csv(
    PROCESSED_DATA_DIR / "reviews_clean.csv"
)

print("Clean datasets loaded successfully.")


# ---------------------------------------------------------
# 3. ADD PRODUCT CATEGORY TO EACH ORDER ITEM
# ---------------------------------------------------------

item_detail = order_items.merge(
    products[
        [
            "product_id",
            "product_category_name_english"
        ]
    ],
    on="product_id",
    how="left"
)

item_detail["product_category_name_english"] = (
    item_detail["product_category_name_english"]
    .fillna("unknown")
)


# ---------------------------------------------------------
# 4. BUILD ONE ROW PER ORDER + CATEGORY
# ---------------------------------------------------------

order_category = (
    item_detail
    .groupby(
        [
            "order_id",
            "product_category_name_english"
        ],
        as_index=False
    )
    .agg(
        units_sold=("order_item_id", "count"),
        merchandise_revenue=("price", "sum"),
        freight_value=("freight_value", "sum"),
        unique_products=("product_id", "nunique")
    )
)

print(
    f"Order-category table created: "
    f"{len(order_category):,} rows"
)


# ---------------------------------------------------------
# 5. ADD ORDER INFORMATION
# ---------------------------------------------------------

order_category = order_category.merge(
    orders[
        [
            "order_id",
            "order_status",
            "delivery_days",
            "delivery_delay_days",
            "delivered_late"
        ]
    ],
    on="order_id",
    how="left"
)


# ---------------------------------------------------------
# 6. CREATE ONE REVIEW SCORE PER ORDER
# ---------------------------------------------------------

review_summary = (
    reviews
    .groupby("order_id", as_index=False)
    .agg(
        review_score=("review_score", "mean")
    )
)

order_category = order_category.merge(
    review_summary,
    on="order_id",
    how="left"
)


# ---------------------------------------------------------
# 7. KEEP DELIVERED ORDERS
# ---------------------------------------------------------

delivered_category = order_category[
    order_category["order_status"] == "delivered"
].copy()


# ---------------------------------------------------------
# 8. CATEGORY PERFORMANCE
# ---------------------------------------------------------

category_performance = (
    delivered_category
    .groupby(
        "product_category_name_english",
        as_index=False
    )
    .agg(
        orders=("order_id", "nunique"),
        units_sold=("units_sold", "sum"),
        merchandise_revenue=("merchandise_revenue", "sum"),
        freight_value=("freight_value", "sum"),
        average_review_score=("review_score", "mean"),
        average_delivery_days=("delivery_days", "mean")
    )
)

category_performance["avg_category_spend_per_order"] = (
    category_performance["merchandise_revenue"]
    / category_performance["orders"]
)


# ---------------------------------------------------------
# 9. LATE DELIVERY RATE BY CATEGORY
# ---------------------------------------------------------

valid_delivery = delivered_category[
    delivered_category["delivered_late"].notna()
].copy()

valid_delivery["delivered_late"] = (
    valid_delivery["delivered_late"]
    .astype(str)
    .str.lower()
    .map({
        "true": True,
        "false": False
    })
)

late_rate = (
    valid_delivery
    .groupby(
        "product_category_name_english",
        as_index=False
    )
    .agg(
        late_delivery_rate=("delivered_late", "mean")
    )
)

late_rate["late_delivery_rate"] *= 100

category_performance = category_performance.merge(
    late_rate,
    on="product_category_name_english",
    how="left"
)


# ---------------------------------------------------------
# 10. TOP CATEGORIES BY REVENUE
# ---------------------------------------------------------

top_revenue = (
    category_performance
    .sort_values(
        "merchandise_revenue",
        ascending=False
    )
    .head(10)
)

print("\n" + "=" * 90)
print("TOP 10 PRODUCT CATEGORIES BY MERCHANDISE REVENUE")
print("=" * 90)

print(
    top_revenue[
        [
            "product_category_name_english",
            "orders",
            "units_sold",
            "merchandise_revenue",
            "avg_category_spend_per_order",
            "average_review_score"
        ]
    ]
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 11. TOP CATEGORIES BY SALES VOLUME
# ---------------------------------------------------------

top_volume = (
    category_performance
    .sort_values(
        "units_sold",
        ascending=False
    )
    .head(10)
)

print("\n" + "=" * 90)
print("TOP 10 PRODUCT CATEGORIES BY UNITS SOLD")
print("=" * 90)

print(
    top_volume[
        [
            "product_category_name_english",
            "units_sold",
            "orders",
            "merchandise_revenue"
        ]
    ]
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 12. LOWEST REVIEWED MAJOR CATEGORIES
# ---------------------------------------------------------

major_categories = category_performance[
    category_performance["orders"] >= 500
].copy()

lowest_reviews = (
    major_categories
    .sort_values(
        "average_review_score",
        ascending=True
    )
    .head(10)
)

print("\n" + "=" * 90)
print("LOWEST REVIEWED MAJOR CATEGORIES")
print("(minimum 500 delivered orders)")
print("=" * 90)

print(
    lowest_reviews[
        [
            "product_category_name_english",
            "orders",
            "average_review_score",
            "late_delivery_rate",
            "average_delivery_days"
        ]
    ]
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 13. HIGHEST LATE-DELIVERY RATES
# ---------------------------------------------------------

highest_late_rates = (
    major_categories
    .sort_values(
        "late_delivery_rate",
        ascending=False
    )
    .head(10)
)

print("\n" + "=" * 90)
print("HIGHEST LATE-DELIVERY RATES — MAJOR CATEGORIES")
print("(minimum 500 delivered orders)")
print("=" * 90)

print(
    highest_late_rates[
        [
            "product_category_name_english",
            "orders",
            "late_delivery_rate",
            "average_review_score",
            "average_delivery_days"
        ]
    ]
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 14. SAVE RESULTS
# ---------------------------------------------------------

category_performance.to_csv(
    PROCESSED_DATA_DIR / "category_performance.csv",
    index=False
)

print("\nCategory performance file saved successfully.")
print("Product category analysis complete.")