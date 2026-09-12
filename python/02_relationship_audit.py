from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# PROJECT PATH
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


# ---------------------------------------------------------
# LOAD THE TABLES NEEDED FOR RELATIONSHIP TESTING
# ---------------------------------------------------------

customers = pd.read_csv(
    RAW_DATA_DIR / "olist_customers_dataset.csv"
)

orders = pd.read_csv(
    RAW_DATA_DIR / "olist_orders_dataset.csv"
)

order_items = pd.read_csv(
    RAW_DATA_DIR / "olist_order_items_dataset.csv"
)

payments = pd.read_csv(
    RAW_DATA_DIR / "olist_order_payments_dataset.csv"
)

reviews = pd.read_csv(
    RAW_DATA_DIR / "olist_order_reviews_dataset.csv"
)

products = pd.read_csv(
    RAW_DATA_DIR / "olist_products_dataset.csv"
)

sellers = pd.read_csv(
    RAW_DATA_DIR / "olist_sellers_dataset.csv"
)

category_translation = pd.read_csv(
    RAW_DATA_DIR / "product_category_name_translation.csv"
)


# ---------------------------------------------------------
# HELPER FUNCTION
# ---------------------------------------------------------

def check_key(df, column, table_name):
    """
    Show whether a column behaves like a primary key.
    """

    total_rows = len(df)
    unique_values = df[column].nunique()
    missing_values = df[column].isna().sum()
    duplicate_values = df[column].duplicated().sum()

    print(f"\n{table_name}.{column}")
    print("-" * 50)
    print(f"Rows:             {total_rows:,}")
    print(f"Unique values:    {unique_values:,}")
    print(f"Missing values:   {missing_values:,}")
    print(f"Duplicate values: {duplicate_values:,}")


# ---------------------------------------------------------
# 1. TEST LIKELY PRIMARY KEYS
# ---------------------------------------------------------

print("=" * 70)
print("PRIMARY KEY CHECKS")
print("=" * 70)

check_key(customers, "customer_id", "customers")
check_key(orders, "order_id", "orders")
check_key(products, "product_id", "products")
check_key(sellers, "seller_id", "sellers")
check_key(
    category_translation,
    "product_category_name",
    "category_translation"
)


# ---------------------------------------------------------
# 2. TEST CUSTOMER IDENTITY
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("CUSTOMER IDENTITY")
print("=" * 70)

print(f"Customer rows:             {len(customers):,}")
print(
    f"Unique customer_id:        "
    f"{customers['customer_id'].nunique():,}"
)
print(
    f"Unique customer_unique_id: "
    f"{customers['customer_unique_id'].nunique():,}"
)

repeat_customer_records = (
    customers["customer_unique_id"]
    .value_counts()
)

print(
    f"Customers appearing more than once: "
    f"{(repeat_customer_records > 1).sum():,}"
)

print("\nMost frequent customers:")
print(repeat_customer_records.head(10))


# ---------------------------------------------------------
# 3. TEST ONE-TO-MANY ORDER RELATIONSHIPS
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("ORDER RELATIONSHIPS")
print("=" * 70)

items_per_order = order_items.groupby("order_id").size()

print(f"Orders represented in order_items: {items_per_order.size:,}")
print(f"Maximum items in one order:        {items_per_order.max():,}")
print(f"Average items per order:           {items_per_order.mean():.2f}")

payments_per_order = payments.groupby("order_id").size()

print(f"\nOrders represented in payments: {payments_per_order.size:,}")
print(
    f"Maximum payment records/order:  "
    f"{payments_per_order.max():,}"
)
print(
    f"Average payment records/order:  "
    f"{payments_per_order.mean():.2f}"
)


# ---------------------------------------------------------
# 4. CHECK FOREIGN-KEY COVERAGE
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("FOREIGN KEY COVERAGE")
print("=" * 70)

orders_without_customer = (
    ~orders["customer_id"].isin(customers["customer_id"])
).sum()

items_without_order = (
    ~order_items["order_id"].isin(orders["order_id"])
).sum()

items_without_product = (
    ~order_items["product_id"].isin(products["product_id"])
).sum()

items_without_seller = (
    ~order_items["seller_id"].isin(sellers["seller_id"])
).sum()

payments_without_order = (
    ~payments["order_id"].isin(orders["order_id"])
).sum()

reviews_without_order = (
    ~reviews["order_id"].isin(orders["order_id"])
).sum()


print(f"Orders without matching customer: {orders_without_customer:,}")
print(f"Items without matching order:     {items_without_order:,}")
print(f"Items without matching product:   {items_without_product:,}")
print(f"Items without matching seller:    {items_without_seller:,}")
print(f"Payments without matching order:  {payments_without_order:,}")
print(f"Reviews without matching order:   {reviews_without_order:,}")


# ---------------------------------------------------------
# 5. ORDER STATUS DISTRIBUTION
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("ORDER STATUS DISTRIBUTION")
print("=" * 70)

status_counts = (
    orders["order_status"]
    .value_counts()
)

print(status_counts)


print("\nRelationship audit complete.")