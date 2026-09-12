from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# 1. PROJECT PATH
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


# ---------------------------------------------------------
# 2. LOAD MASTER DATA
# ---------------------------------------------------------

orders = pd.read_csv(
    PROCESSED_DATA_DIR / "order_analysis.csv",
    parse_dates=["order_purchase_timestamp"]
)

print("Master analysis dataset loaded successfully.")


# ---------------------------------------------------------
# 3. KEEP DELIVERED ORDERS
# ---------------------------------------------------------

delivered = orders[
    orders["order_status"] == "delivered"
].copy()


# ---------------------------------------------------------
# 4. CREATE SNAPSHOT DATE
# ---------------------------------------------------------

snapshot_date = (
    delivered["order_purchase_timestamp"].max()
    + pd.Timedelta(days=1)
)

print(
    f"RFM snapshot date: "
    f"{snapshot_date.date()}"
)


# ---------------------------------------------------------
# 5. BUILD CUSTOMER-LEVEL RFM TABLE
# ---------------------------------------------------------

rfm = (
    delivered
    .groupby(
        "customer_unique_id",
        as_index=False
    )
    .agg(
        last_purchase=(
            "order_purchase_timestamp",
            "max"
        ),
        frequency=(
            "order_id",
            "nunique"
        ),
        monetary=(
            "payment_value",
            "sum"
        )
    )
)


rfm["recency_days"] = (
    snapshot_date
    - rfm["last_purchase"]
).dt.days


# ---------------------------------------------------------
# 6. SCORE RECENCY
# ---------------------------------------------------------

# More recent customers receive a higher score.
rfm["recency_score"] = pd.qcut(
    rfm["recency_days"],
    q=5,
    labels=[5, 4, 3, 2, 1]
).astype(int)


# ---------------------------------------------------------
# 7. SCORE MONETARY VALUE
# ---------------------------------------------------------

# Higher spending receives a higher score.
rfm["monetary_score"] = pd.qcut(
    rfm["monetary"],
    q=5,
    labels=[1, 2, 3, 4, 5]
).astype(int)


# ---------------------------------------------------------
# 8. SCORE PURCHASE FREQUENCY
# ---------------------------------------------------------

def frequency_score(order_count):

    if order_count == 1:
        return 1

    elif order_count == 2:
        return 3

    elif order_count == 3:
        return 4

    else:
        return 5


rfm["frequency_score"] = (
    rfm["frequency"]
    .apply(frequency_score)
)


# ---------------------------------------------------------
# 9. CUSTOMER SEGMENTATION
# ---------------------------------------------------------

def assign_segment(row):

    r = row["recency_score"]
    f = row["frequency_score"]
    m = row["monetary_score"]

    if r >= 4 and f >= 3 and m >= 4:
        return "Champions"

    elif f >= 3 and r >= 3:
        return "Loyal Customers"

    elif f >= 3 and r <= 2:
        return "At Risk Repeat"

    elif f == 1 and m >= 4 and r >= 3:
        return "High Value One-Time"

    elif f == 1 and r >= 4:
        return "Recent One-Time"

    elif f == 1 and m >= 4:
        return "High Value Inactive"

    else:
        return "One-Time Customer"


rfm["customer_segment"] = (
    rfm.apply(
        assign_segment,
        axis=1
    )
)


# ---------------------------------------------------------
# 10. SEGMENT SUMMARY
# ---------------------------------------------------------

segment_summary = (
    rfm
    .groupby(
        "customer_segment",
        as_index=False
    )
    .agg(
        customers=(
            "customer_unique_id",
            "nunique"
        ),
        average_recency_days=(
            "recency_days",
            "mean"
        ),
        average_orders=(
            "frequency",
            "mean"
        ),
        total_revenue=(
            "monetary",
            "sum"
        ),
        average_customer_value=(
            "monetary",
            "mean"
        )
    )
)

segment_summary["customer_share_pct"] = (
    segment_summary["customers"]
    / len(rfm)
) * 100

segment_summary["revenue_share_pct"] = (
    segment_summary["total_revenue"]
    / segment_summary["total_revenue"].sum()
) * 100

segment_summary = (
    segment_summary
    .sort_values(
        "total_revenue",
        ascending=False
    )
)


# ---------------------------------------------------------
# 11. DISPLAY SEGMENTS
# ---------------------------------------------------------

print("\n" + "=" * 95)
print("CUSTOMER SEGMENT PERFORMANCE")
print("=" * 95)

print(
    segment_summary
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 12. HIGHEST-VALUE CUSTOMERS
# ---------------------------------------------------------

top_customers = (
    rfm
    .sort_values(
        "monetary",
        ascending=False
    )
    .head(10)
)

print("\n" + "=" * 95)
print("TOP 10 CUSTOMERS BY TOTAL SPEND")
print("=" * 95)

print(
    top_customers[
        [
            "customer_unique_id",
            "frequency",
            "monetary",
            "recency_days",
            "customer_segment"
        ]
    ]
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 13. SAVE RESULTS
# ---------------------------------------------------------

rfm.to_csv(
    PROCESSED_DATA_DIR / "customer_rfm.csv",
    index=False
)

segment_summary.to_csv(
    PROCESSED_DATA_DIR / "customer_segment_summary.csv",
    index=False
)

print("\nCustomer RFM files saved successfully.")
print("RFM analysis complete.")
