from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# 1. PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# 2. LOAD DATA
# ---------------------------------------------------------

customers = pd.read_csv(
    RAW_DATA_DIR / "olist_customers_dataset.csv"
)

geolocation = pd.read_csv(
    RAW_DATA_DIR / "olist_geolocation_dataset.csv"
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

orders = pd.read_csv(
    RAW_DATA_DIR / "olist_orders_dataset.csv"
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

print("Raw datasets loaded successfully.")


# ---------------------------------------------------------
# 3. CONVERT DATE COLUMNS
# ---------------------------------------------------------

order_date_columns = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]

for column in order_date_columns:
    orders[column] = pd.to_datetime(
        orders[column],
        errors="coerce"
    )

order_items["shipping_limit_date"] = pd.to_datetime(
    order_items["shipping_limit_date"],
    errors="coerce"
)

reviews["review_creation_date"] = pd.to_datetime(
    reviews["review_creation_date"],
    errors="coerce"
)

reviews["review_answer_timestamp"] = pd.to_datetime(
    reviews["review_answer_timestamp"],
    errors="coerce"
)


# ---------------------------------------------------------
# 4. STANDARDIZE TEXT COLUMNS
# ---------------------------------------------------------

customers["customer_city"] = (
    customers["customer_city"]
    .str.strip()
    .str.lower()
)

customers["customer_state"] = (
    customers["customer_state"]
    .str.strip()
    .str.upper()
)

sellers["seller_city"] = (
    sellers["seller_city"]
    .str.strip()
    .str.lower()
)

sellers["seller_state"] = (
    sellers["seller_state"]
    .str.strip()
    .str.upper()
)


# ---------------------------------------------------------
# 5. CLEAN PRODUCT CATEGORIES
# ---------------------------------------------------------

products["product_category_name"] = (
    products["product_category_name"]
    .fillna("unknown")
)

category_translation["product_category_name"] = (
    category_translation["product_category_name"]
    .str.strip()
)

category_translation["product_category_name_english"] = (
    category_translation["product_category_name_english"]
    .str.strip()
)

products = products.merge(
    category_translation,
    on="product_category_name",
    how="left"
)

products["product_category_name_english"] = (
    products["product_category_name_english"]
    .fillna(products["product_category_name"])
)


# ---------------------------------------------------------
# 6. CLEAN GEOLOCATION
# ---------------------------------------------------------

original_geo_rows = len(geolocation)

geolocation = geolocation.drop_duplicates()

geo_duplicates_removed = (
    original_geo_rows - len(geolocation)
)

print(
    f"Exact geolocation duplicates removed: "
    f"{geo_duplicates_removed:,}"
)

geo_lookup = (
    geolocation
    .groupby(
        "geolocation_zip_code_prefix",
        as_index=False
    )
    .agg({
        "geolocation_lat": "median",
        "geolocation_lng": "median",
        "geolocation_city": "first",
        "geolocation_state": "first"
    })
)


# ---------------------------------------------------------
# 7. CREATE USEFUL ORDER FEATURES
# ---------------------------------------------------------

orders["purchase_year"] = (
    orders["order_purchase_timestamp"].dt.year
)

orders["purchase_month"] = (
    orders["order_purchase_timestamp"].dt.month
)

orders["purchase_year_month"] = (
    orders["order_purchase_timestamp"]
    .dt.to_period("M")
    .astype(str)
)

orders["purchase_day_of_week"] = (
    orders["order_purchase_timestamp"]
    .dt.day_name()
)

orders["delivery_days"] = (
    orders["order_delivered_customer_date"]
    - orders["order_purchase_timestamp"]
).dt.days

orders["estimated_delivery_days"] = (
    orders["order_estimated_delivery_date"]
    - orders["order_purchase_timestamp"]
).dt.days

orders["delivery_delay_days"] = (
    orders["order_delivered_customer_date"]
    - orders["order_estimated_delivery_date"]
).dt.days


# ---------------------------------------------------------
# 8. CREATE ACCURATE LATE-DELIVERY FLAG
# ---------------------------------------------------------

orders["delivered_late"] = pd.NA

valid_delivery_dates = (
    orders["order_delivered_customer_date"].notna()
    &
    orders["order_estimated_delivery_date"].notna()
)

orders.loc[
    valid_delivery_dates,
    "delivered_late"
] = (
    orders.loc[
        valid_delivery_dates,
        "order_delivered_customer_date"
    ]
    >
    orders.loc[
        valid_delivery_dates,
        "order_estimated_delivery_date"
    ]
)


# ---------------------------------------------------------
# 9. CREATE DELIVERED-ORDER FLAG
# ---------------------------------------------------------

orders["is_delivered"] = (
    orders["order_status"] == "delivered"
)


# ---------------------------------------------------------
# 10. SAVE CLEANED TABLES
# ---------------------------------------------------------

customers.to_csv(
    PROCESSED_DATA_DIR / "customers_clean.csv",
    index=False
)

orders.to_csv(
    PROCESSED_DATA_DIR / "orders_clean.csv",
    index=False
)

order_items.to_csv(
    PROCESSED_DATA_DIR / "order_items_clean.csv",
    index=False
)

payments.to_csv(
    PROCESSED_DATA_DIR / "payments_clean.csv",
    index=False
)

reviews.to_csv(
    PROCESSED_DATA_DIR / "reviews_clean.csv",
    index=False
)

products.to_csv(
    PROCESSED_DATA_DIR / "products_clean.csv",
    index=False
)

sellers.to_csv(
    PROCESSED_DATA_DIR / "sellers_clean.csv",
    index=False
)

geo_lookup.to_csv(
    PROCESSED_DATA_DIR / "geolocation_lookup.csv",
    index=False
)


# ---------------------------------------------------------
# 11. QUALITY CHECKS
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("CLEANING SUMMARY")
print("=" * 70)

print(f"Customers:             {len(customers):,}")
print(f"Orders:                {len(orders):,}")
print(f"Order items:           {len(order_items):,}")
print(f"Payments:              {len(payments):,}")
print(f"Reviews:               {len(reviews):,}")
print(f"Products:              {len(products):,}")
print(f"Sellers:               {len(sellers):,}")
print(f"Geolocation ZIP codes: {len(geo_lookup):,}")

print("\nOrder date range:")
print(
    orders["order_purchase_timestamp"].min(),
    "to",
    orders["order_purchase_timestamp"].max()
)

print("\nDelivered orders:")
print(
    orders["is_delivered"].value_counts()
)

print("\nLate-delivery flag:")
print(
    orders.loc[
        orders["is_delivered"],
        "delivered_late"
    ].value_counts(dropna=False)
)

print("\nClean datasets saved successfully.")