from pathlib import Path
import pandas as pd


# ---------------------------------------------------------
# 1. DISPLAY SETTINGS
# ---------------------------------------------------------

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 150)


# ---------------------------------------------------------
# 2. PROJECT PATHS
# ---------------------------------------------------------

# This file lives inside the "notebooks" folder.
# parents[1] moves one level up to the main project folder.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Create the processed folder if it does not already exist.
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# 3. DEFINE THE DATASETS
# ---------------------------------------------------------

data_files = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv"
}


# ---------------------------------------------------------
# 4. CHECK THAT EVERY FILE EXISTS
# ---------------------------------------------------------

missing_files = []

for filename in data_files.values():
    file_path = RAW_DATA_DIR / filename

    if not file_path.exists():
        missing_files.append(filename)

if missing_files:
    raise FileNotFoundError(
        f"The following files are missing from data/raw:\n{missing_files}"
    )

print("All required CSV files were found.\n")


# ---------------------------------------------------------
# 5. LOAD ALL DATASETS
# ---------------------------------------------------------

datasets = {}

for table_name, filename in data_files.items():

    file_path = RAW_DATA_DIR / filename

    print(f"Loading {table_name}...")

    datasets[table_name] = pd.read_csv(file_path)

print("\nAll datasets loaded successfully.\n")


# ---------------------------------------------------------
# 6. CREATE A TABLE-LEVEL DATA OVERVIEW
# ---------------------------------------------------------

summary_rows = []

for table_name, df in datasets.items():

    summary_rows.append({
        "table": table_name,
        "rows": len(df),
        "columns": len(df.columns),
        "duplicate_rows": df.duplicated().sum(),
        "missing_values": df.isna().sum().sum()
    })

data_summary = pd.DataFrame(summary_rows)

# Largest tables first
data_summary = data_summary.sort_values(
    by="rows",
    ascending=False
).reset_index(drop=True)


print("=" * 80)
print("DATASET OVERVIEW")
print("=" * 80)

print(data_summary.to_string(index=False))


# ---------------------------------------------------------
# 7. CREATE A COLUMN-LEVEL DATA INVENTORY
# ---------------------------------------------------------

column_inventory_rows = []

for table_name, df in datasets.items():

    for column in df.columns:

        missing_count = df[column].isna().sum()

        column_inventory_rows.append({
            "table": table_name,
            "column": column,
            "data_type": str(df[column].dtype),
            "missing_values": missing_count,
            "missing_percent": round(
                (missing_count / len(df)) * 100, 2
            ),
            "unique_values": df[column].nunique()
        })


column_inventory = pd.DataFrame(column_inventory_rows)


# ---------------------------------------------------------
# 8. SAVE THE INVENTORY FILES
# ---------------------------------------------------------

data_summary.to_csv(
    PROCESSED_DATA_DIR / "dataset_summary.csv",
    index=False
)

column_inventory.to_csv(
    PROCESSED_DATA_DIR / "column_inventory.csv",
    index=False
)


print("\n" + "=" * 80)
print("FILES CREATED")
print("=" * 80)

print("data/processed/dataset_summary.csv")
print("data/processed/column_inventory.csv")


# ---------------------------------------------------------
# 9. SHOW THE COLUMNS IN EACH TABLE
# ---------------------------------------------------------

print("\n" + "=" * 80)
print("TABLE STRUCTURE")
print("=" * 80)

for table_name, df in datasets.items():

    print(f"\n{table_name.upper()}")
    print("-" * 40)

    for column in df.columns:
        print(column)


print("\nData overview complete.")