from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# 1. PROJECT PATH
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


# ---------------------------------------------------------
# 2. LOAD DATA
# ---------------------------------------------------------

orders = pd.read_csv(
    PROCESSED_DATA_DIR / "order_analysis.csv"
)

payments = pd.read_csv(
    PROCESSED_DATA_DIR / "payments_clean.csv"
)

print("Datasets loaded successfully.")


# ---------------------------------------------------------
# 3. KEEP ONLY PAYMENTS FOR DELIVERED ORDERS
# ---------------------------------------------------------

delivered_order_ids = (
    orders.loc[
        orders["order_status"] == "delivered",
        ["order_id"]
    ]
)

delivered_payments = payments.merge(
    delivered_order_ids,
    on="order_id",
    how="inner"
)


# ---------------------------------------------------------
# 4. PAYMENT METHOD PERFORMANCE
# ---------------------------------------------------------

payment_method_summary = (
    delivered_payments
    .groupby("payment_type", as_index=False)
    .agg(
        payment_records=("payment_sequential", "count"),
        orders_using_method=("order_id", "nunique"),
        payment_value=("payment_value", "sum")
    )
)

payment_method_summary["avg_payment_per_order"] = (
    payment_method_summary["payment_value"]
    / payment_method_summary["orders_using_method"]
)

total_payment_value = (
    payment_method_summary["payment_value"].sum()
)

payment_method_summary["payment_value_share_pct"] = (
    payment_method_summary["payment_value"]
    / total_payment_value
) * 100

payment_method_summary = (
    payment_method_summary
    .sort_values(
        "payment_value",
        ascending=False
    )
)


print("\n" + "=" * 85)
print("PAYMENT METHOD PERFORMANCE")
print("=" * 85)

print(
    payment_method_summary
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 5. CREDIT CARD INSTALLMENT ANALYSIS
# ---------------------------------------------------------

credit_card = delivered_payments[
    delivered_payments["payment_type"] == "credit_card"
].copy()


# Reduce to one row per order
credit_card_orders = (
    credit_card
    .groupby("order_id", as_index=False)
    .agg(
        installments=("payment_installments", "max"),
        payment_value=("payment_value", "sum")
    )
)


# ---------------------------------------------------------
# 6. CREATE INSTALLMENT GROUPS
# ---------------------------------------------------------

def installment_group(x):

    if x <= 1:
        return "1 installment"

    elif x <= 3:
        return "2-3 installments"

    elif x <= 6:
        return "4-6 installments"

    elif x <= 12:
        return "7-12 installments"

    else:
        return "13+ installments"


credit_card_orders["installment_group"] = (
    credit_card_orders["installments"]
    .apply(installment_group)
)


installment_summary = (
    credit_card_orders
    .groupby("installment_group", as_index=False)
    .agg(
        orders=("order_id", "nunique"),
        total_payment_value=("payment_value", "sum"),
        average_order_value=("payment_value", "mean")
    )
)


# Logical display order
installment_order = [
    "1 installment",
    "2-3 installments",
    "4-6 installments",
    "7-12 installments",
    "13+ installments"
]

installment_summary["installment_group"] = pd.Categorical(
    installment_summary["installment_group"],
    categories=installment_order,
    ordered=True
)

installment_summary = (
    installment_summary
    .sort_values("installment_group")
)


print("\n" + "=" * 85)
print("CREDIT CARD INSTALLMENT BEHAVIOUR")
print("=" * 85)

print(
    installment_summary
    .round(2)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 7. INSTALLMENT DISTRIBUTION
# ---------------------------------------------------------

installment_distribution = (
    credit_card_orders["installments"]
    .value_counts()
    .sort_index()
    .reset_index()
)

installment_distribution.columns = [
    "installments",
    "orders"
]


print("\n" + "=" * 85)
print("CREDIT CARD ORDERS BY NUMBER OF INSTALLMENTS")
print("=" * 85)

print(
    installment_distribution
    .to_string(index=False)
)


# ---------------------------------------------------------
# 8. SAVE RESULTS
# ---------------------------------------------------------

payment_method_summary.to_csv(
    PROCESSED_DATA_DIR / "payment_method_summary.csv",
    index=False
)

installment_summary.to_csv(
    PROCESSED_DATA_DIR / "installment_summary.csv",
    index=False
)

installment_distribution.to_csv(
    PROCESSED_DATA_DIR / "installment_distribution.csv",
    index=False
)

print("\nPayment analysis files saved successfully.")
print("Payment behaviour analysis complete.")