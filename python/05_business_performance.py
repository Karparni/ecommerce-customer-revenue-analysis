from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# 1. PROJECT PATH
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


# ---------------------------------------------------------
# 2. LOAD MASTER ANALYSIS DATA
# ---------------------------------------------------------

orders = pd.read_csv(
    PROCESSED_DATA_DIR / "order_analysis.csv",
    parse_dates=[
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]
)

print("Master analysis dataset loaded successfully.")


# ---------------------------------------------------------
# 3. KEEP DELIVERED ORDERS FOR SALES ANALYSIS
# ---------------------------------------------------------

delivered = orders[
    orders["order_status"] == "delivered"
].copy()


# ---------------------------------------------------------
# 4. MONTHLY BUSINESS PERFORMANCE
# ---------------------------------------------------------

monthly_performance = (
    delivered
    .groupby("purchase_year_month", as_index=False)
    .agg(
        orders=("order_id", "nunique"),
        customers=("customer_unique_id", "nunique"),
        revenue=("payment_value", "sum"),
        merchandise_value=("merchandise_value", "sum"),
        average_review_score=("review_score", "mean")
    )
)

monthly_performance["average_order_value"] = (
    monthly_performance["revenue"]
    / monthly_performance["orders"]
)

monthly_performance["revenue_growth_pct"] = (
    monthly_performance["revenue"]
    .pct_change() * 100
)


print("\n" + "=" * 80)
print("MONTHLY BUSINESS PERFORMANCE")
print("=" * 80)

print(
    monthly_performance[
        [
            "purchase_year_month",
            "orders",
            "customers",
            "revenue",
            "average_order_value",
            "revenue_growth_pct"
        ]
    ]
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 5. TOP REVENUE MONTHS
# ---------------------------------------------------------

top_months = (
    monthly_performance
    .sort_values(
        "revenue",
        ascending=False
    )
    .head(5)
)

print("\n" + "=" * 80)
print("TOP 5 MONTHS BY REVENUE")
print("=" * 80)

print(
    top_months[
        [
            "purchase_year_month",
            "orders",
            "customers",
            "revenue",
            "average_order_value"
        ]
    ]
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 6. CUSTOMER GEOGRAPHY
# ---------------------------------------------------------

state_performance = (
    delivered
    .groupby("customer_state", as_index=False)
    .agg(
        orders=("order_id", "nunique"),
        customers=("customer_unique_id", "nunique"),
        revenue=("payment_value", "sum")
    )
)

state_performance["average_order_value"] = (
    state_performance["revenue"]
    / state_performance["orders"]
)

state_performance = (
    state_performance
    .sort_values(
        "revenue",
        ascending=False
    )
)


print("\n" + "=" * 80)
print("TOP 10 STATES BY REVENUE")
print("=" * 80)

print(
    state_performance.head(10)
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 7. REPEAT VS ONE-TIME CUSTOMERS
# ---------------------------------------------------------

customer_summary = (
    delivered
    .groupby("customer_unique_id", as_index=False)
    .agg(
        orders=("order_id", "nunique"),
        total_spend=("payment_value", "sum")
    )
)

customer_summary["customer_type"] = (
    customer_summary["orders"]
    .apply(
        lambda x: "Repeat Customer"
        if x > 1
        else "One-Time Customer"
    )
)

customer_type_summary = (
    customer_summary
    .groupby("customer_type", as_index=False)
    .agg(
        customers=("customer_unique_id", "nunique"),
        orders=("orders", "sum"),
        revenue=("total_spend", "sum"),
        average_customer_spend=("total_spend", "mean")
    )
)


print("\n" + "=" * 80)
print("CUSTOMER TYPE PERFORMANCE")
print("=" * 80)

print(
    customer_type_summary
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 8. DELIVERY PERFORMANCE
# ---------------------------------------------------------

delivered_with_dates = delivered[
    delivered["delivery_days"].notna()
].copy()

average_delivery_days = (
    delivered_with_dates["delivery_days"].mean()
)

median_delivery_days = (
    delivered_with_dates["delivery_days"].median()
)

late_orders = delivered[
    delivered["delivered_late"]
    .astype(str)
    .str.lower()
    == "true"
]

on_time_orders = delivered[
    delivered["delivered_late"]
    .astype(str)
    .str.lower()
    == "false"
]

late_review_score = (
    late_orders["review_score"].mean()
)

on_time_review_score = (
    on_time_orders["review_score"].mean()
)


print("\n" + "=" * 80)
print("DELIVERY PERFORMANCE")
print("=" * 80)

print(
    f"Average delivery time: "
    f"{average_delivery_days:.2f} days"
)

print(
    f"Median delivery time:  "
    f"{median_delivery_days:.2f} days"
)

print(
    f"Average review - on-time orders: "
    f"{on_time_review_score:.2f} / 5"
)

print(
    f"Average review - late orders:    "
    f"{late_review_score:.2f} / 5"
)


# ---------------------------------------------------------
# 9. SAVE BUSINESS SUMMARY TABLES
# ---------------------------------------------------------

monthly_performance.to_csv(
    PROCESSED_DATA_DIR / "monthly_performance.csv",
    index=False
)

state_performance.to_csv(
    PROCESSED_DATA_DIR / "state_performance.csv",
    index=False
)

customer_type_summary.to_csv(
    PROCESSED_DATA_DIR / "customer_type_summary.csv",
    index=False
)


print("\nBusiness summary files saved successfully.")
print("Business performance analysis complete.")