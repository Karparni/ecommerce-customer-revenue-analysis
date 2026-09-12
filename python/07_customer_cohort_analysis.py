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
# 4. CREATE PURCHASE MONTH
# ---------------------------------------------------------

delivered["purchase_month"] = (
    delivered["order_purchase_timestamp"]
    .dt.to_period("M")
    .dt.to_timestamp()
)


# ---------------------------------------------------------
# 5. FIND EACH CUSTOMER'S FIRST PURCHASE MONTH
# ---------------------------------------------------------

delivered["cohort_month"] = (
    delivered
    .groupby("customer_unique_id")["purchase_month"]
    .transform("min")
)


# ---------------------------------------------------------
# 6. CALCULATE MONTHS SINCE FIRST PURCHASE
# ---------------------------------------------------------

delivered["cohort_index"] = (
    (
        delivered["purchase_month"].dt.year
        - delivered["cohort_month"].dt.year
    ) * 12
    +
    (
        delivered["purchase_month"].dt.month
        - delivered["cohort_month"].dt.month
    )
)


# ---------------------------------------------------------
# 7. COUNT ACTIVE CUSTOMERS BY COHORT
# ---------------------------------------------------------

cohort_counts = (
    delivered
    .groupby(
        ["cohort_month", "cohort_index"]
    )["customer_unique_id"]
    .nunique()
    .reset_index(name="active_customers")
)


# ---------------------------------------------------------
# 8. GET ORIGINAL COHORT SIZE
# ---------------------------------------------------------

cohort_sizes = (
    cohort_counts[
        cohort_counts["cohort_index"] == 0
    ]
    [["cohort_month", "active_customers"]]
    .rename(
        columns={
            "active_customers": "cohort_size"
        }
    )
)

cohort_counts = cohort_counts.merge(
    cohort_sizes,
    on="cohort_month",
    how="left"
)


# ---------------------------------------------------------
# 9. CALCULATE RETENTION RATE
# ---------------------------------------------------------

cohort_counts["retention_rate"] = (
    cohort_counts["active_customers"]
    / cohort_counts["cohort_size"]
) * 100


# ---------------------------------------------------------
# 10. CREATE RETENTION MATRIX
# ---------------------------------------------------------

retention_matrix = (
    cohort_counts
    .pivot(
        index="cohort_month",
        columns="cohort_index",
        values="retention_rate"
    )
)

retention_matrix.index = (
    retention_matrix.index
    .strftime("%Y-%m")
)


# ---------------------------------------------------------
# 11. DISPLAY COHORT SIZES
# ---------------------------------------------------------

print("\n" + "=" * 85)
print("CUSTOMER COHORT SIZES")
print("=" * 85)

display_sizes = cohort_sizes.copy()

display_sizes["cohort_month"] = (
    display_sizes["cohort_month"]
    .dt.strftime("%Y-%m")
)

print(
    display_sizes
    .to_string(index=False)
)


# ---------------------------------------------------------
# 12. DISPLAY FIRST 6 MONTHS OF RETENTION
# ---------------------------------------------------------

print("\n" + "=" * 85)
print("CUSTOMER RETENTION MATRIX (%)")
print("Month 0 = acquisition month")
print("=" * 85)

columns_to_show = [
    column
    for column in range(6)
    if column in retention_matrix.columns
]

print(
    retention_matrix[
        columns_to_show
    ]
    .round(2)
    .to_string()
)


# ---------------------------------------------------------
# 13. OVERALL RETURN BEHAVIOUR
# ---------------------------------------------------------

customer_purchase_counts = (
    delivered
    .groupby("customer_unique_id")
    ["order_id"]
    .nunique()
)

one_time_customers = (
    customer_purchase_counts == 1
).sum()

repeat_customers = (
    customer_purchase_counts > 1
).sum()

three_plus_customers = (
    customer_purchase_counts >= 3
).sum()


print("\n" + "=" * 85)
print("CUSTOMER RETURN BEHAVIOUR")
print("=" * 85)

print(
    f"One-time customers:       "
    f"{one_time_customers:,}"
)

print(
    f"Repeat customers:         "
    f"{repeat_customers:,}"
)

print(
    f"Customers with 3+ orders: "
    f"{three_plus_customers:,}"
)


# ---------------------------------------------------------
# 14. SAVE RESULTS
# ---------------------------------------------------------

cohort_counts.to_csv(
    PROCESSED_DATA_DIR / "cohort_retention_long.csv",
    index=False
)

retention_matrix.to_csv(
    PROCESSED_DATA_DIR / "cohort_retention_matrix.csv"
)

print("\nCohort analysis files saved successfully.")
print("Customer cohort analysis complete.")