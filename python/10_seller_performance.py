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

order_items = pd.read_csv(
    PROCESSED_DATA_DIR / "order_items_clean.csv"
)

orders = pd.read_csv(
    PROCESSED_DATA_DIR / "orders_clean.csv"
)

sellers = pd.read_csv(
    PROCESSED_DATA_DIR / "sellers_clean.csv"
)

reviews = pd.read_csv(
    PROCESSED_DATA_DIR / "reviews_clean.csv"
)

print("Clean datasets loaded successfully.")


# ---------------------------------------------------------
# 3. CREATE ONE ROW PER ORDER + SELLER
# ---------------------------------------------------------

seller_order = (
    order_items
    .groupby(
        ["order_id", "seller_id"],
        as_index=False
    )
    .agg(
        units_sold=("order_item_id", "count"),
        merchandise_revenue=("price", "sum"),
        freight_value=("freight_value", "sum")
    )
)

print(
    f"Order-seller table created: "
    f"{len(seller_order):,} rows"
)


# ---------------------------------------------------------
# 4. ADD ORDER INFORMATION
# ---------------------------------------------------------

seller_order = seller_order.merge(
    orders[
        [
            "order_id",
            "order_status",
            "delivery_days",
            "delivered_late"
        ]
    ],
    on="order_id",
    how="left"
)


# ---------------------------------------------------------
# 5. ADD SELLER LOCATION
# ---------------------------------------------------------

seller_order = seller_order.merge(
    sellers,
    on="seller_id",
    how="left"
)


# ---------------------------------------------------------
# 6. ADD ONE REVIEW SCORE PER ORDER
# ---------------------------------------------------------

review_summary = (
    reviews
    .groupby("order_id", as_index=False)
    .agg(
        review_score=("review_score", "mean")
    )
)

seller_order = seller_order.merge(
    review_summary,
    on="order_id",
    how="left"
)


# ---------------------------------------------------------
# 7. KEEP DELIVERED ORDERS
# ---------------------------------------------------------

delivered = seller_order[
    seller_order["order_status"] == "delivered"
].copy()


# ---------------------------------------------------------
# 8. CONVERT LATE-DELIVERY FLAG SAFELY
# ---------------------------------------------------------

delivered["delivered_late_flag"] = (
    delivered["delivered_late"]
    .astype(str)
    .str.lower()
    .map({
        "true": True,
        "false": False
    })
)


# ---------------------------------------------------------
# 9. BUILD SELLER PERFORMANCE TABLE
# ---------------------------------------------------------

seller_performance = (
    delivered
    .groupby(
        [
            "seller_id",
            "seller_city",
            "seller_state"
        ],
        as_index=False
    )
    .agg(
        orders=("order_id", "nunique"),
        units_sold=("units_sold", "sum"),
        merchandise_revenue=("merchandise_revenue", "sum"),
        average_review_score=("review_score", "mean"),
        average_delivery_days=("delivery_days", "mean"),
        late_delivery_rate=("delivered_late_flag", "mean")
    )
)

seller_performance["late_delivery_rate"] *= 100

seller_performance["revenue_per_order"] = (
    seller_performance["merchandise_revenue"]
    / seller_performance["orders"]
)


# ---------------------------------------------------------
# 10. TOP SELLERS BY REVENUE
# ---------------------------------------------------------

top_sellers = (
    seller_performance
    .sort_values(
        "merchandise_revenue",
        ascending=False
    )
    .head(10)
)

print("\n" + "=" * 100)
print("TOP 10 SELLERS BY MERCHANDISE REVENUE")
print("=" * 100)

print(
    top_sellers[
        [
            "seller_id",
            "seller_city",
            "seller_state",
            "orders",
            "units_sold",
            "merchandise_revenue",
            "revenue_per_order",
            "average_review_score"
        ]
    ]
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 11. REVENUE CONCENTRATION
# ---------------------------------------------------------

seller_performance = seller_performance.sort_values(
    "merchandise_revenue",
    ascending=False
)

total_revenue = (
    seller_performance["merchandise_revenue"].sum()
)

top_10_revenue = (
    seller_performance.head(10)["merchandise_revenue"].sum()
)

top_50_revenue = (
    seller_performance.head(50)["merchandise_revenue"].sum()
)

top_100_revenue = (
    seller_performance.head(100)["merchandise_revenue"].sum()
)

print("\n" + "=" * 100)
print("SELLER REVENUE CONCENTRATION")
print("=" * 100)

print(
    f"Total active sellers: "
    f"{len(seller_performance):,}"
)

print(
    f"Top 10 sellers revenue share: "
    f"{(top_10_revenue / total_revenue) * 100:.2f}%"
)

print(
    f"Top 50 sellers revenue share: "
    f"{(top_50_revenue / total_revenue) * 100:.2f}%"
)

print(
    f"Top 100 sellers revenue share: "
    f"{(top_100_revenue / total_revenue) * 100:.2f}%"
)


# ---------------------------------------------------------
# 12. MAJOR SELLERS ONLY
# ---------------------------------------------------------

major_sellers = seller_performance[
    seller_performance["orders"] >= 100
].copy()


# ---------------------------------------------------------
# 13. LOWEST REVIEWED MAJOR SELLERS
# ---------------------------------------------------------

lowest_reviewed = (
    major_sellers
    .sort_values(
        "average_review_score",
        ascending=True
    )
    .head(10)
)

print("\n" + "=" * 100)
print("LOWEST REVIEWED MAJOR SELLERS")
print("(minimum 100 delivered orders)")
print("=" * 100)

print(
    lowest_reviewed[
        [
            "seller_id",
            "seller_city",
            "seller_state",
            "orders",
            "merchandise_revenue",
            "average_review_score",
            "late_delivery_rate"
        ]
    ]
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 14. HIGHEST LATE-DELIVERY RATES
# ---------------------------------------------------------

highest_late = (
    major_sellers
    .sort_values(
        "late_delivery_rate",
        ascending=False
    )
    .head(10)
)

print("\n" + "=" * 100)
print("HIGHEST LATE-DELIVERY RATES — MAJOR SELLERS")
print("(minimum 100 delivered orders)")
print("=" * 100)

print(
    highest_late[
        [
            "seller_id",
            "seller_city",
            "seller_state",
            "orders",
            "late_delivery_rate",
            "average_delivery_days",
            "average_review_score"
        ]
    ]
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 15. SELLER PERFORMANCE BY STATE
# ---------------------------------------------------------

seller_state_summary = (
    delivered
    .groupby(
        "seller_state",
        as_index=False
    )
    .agg(
        sellers=("seller_id", "nunique"),
        orders=("order_id", "nunique"),
        merchandise_revenue=("merchandise_revenue", "sum")
    )
)

seller_state_summary = seller_state_summary.sort_values(
    "merchandise_revenue",
    ascending=False
)


print("\n" + "=" * 100)
print("TOP SELLER STATES BY REVENUE")
print("=" * 100)

print(
    seller_state_summary
    .head(10)
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 16. SAVE RESULTS
# ---------------------------------------------------------

seller_performance.to_csv(
    PROCESSED_DATA_DIR / "seller_performance.csv",
    index=False
)

seller_state_summary.to_csv(
    PROCESSED_DATA_DIR / "seller_state_summary.csv",
    index=False
)

print("\nSeller performance files saved successfully.")
print("Seller analysis complete.")