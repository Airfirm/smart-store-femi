import os
import shutil
import pandas as pd


# ---------- Helpers ----------
def clean_numeric(series):
    """Coerce numbers from messy strings like '$1,234.56' or '1 234' or with stray chars."""
    s = series.astype(str).str.replace(r"[^\d\.\-]", "", regex=True)
    return pd.to_numeric(s, errors="coerce")


def first_existing_column(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


# ---------- Paths ----------
# Script is now in: src/analytics_project/
# Project root is 2 levels up from this file
BASE_PATH = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # .../smart-femi-store
RAW_DATA_PATH = os.path.join(BASE_PATH, "data", "raw")
RESULTS_PATH = os.path.join(RAW_DATA_PATH, "analysis_results")

# Fresh results folder
if os.path.exists(RESULTS_PATH):
    shutil.rmtree(RESULTS_PATH)
os.makedirs(RESULTS_PATH, exist_ok=True)

# ---------- Load data ----------
customers_df = pd.read_csv(os.path.join(RAW_DATA_PATH, "customers_data.csv"))
products_df = pd.read_csv(os.path.join(RAW_DATA_PATH, "products_data.csv"))
sales_df = pd.read_csv(os.path.join(RAW_DATA_PATH, "sales_data.csv"))

# ---------- Columns we will use ----------
# Location: try several common names
location_col = first_existing_column(
    customers_df, ["location", "Location", "City", "CityName", "CustomerCity", "State", "Country"]
)

# Price: you confirmed this is UnitPrice
price_col = "UnitPrice"

# Sales amount: you confirmed this is SaleAmount
sales_amt_col = "SaleAmount"

# ---------- Compute answers ----------
# 1) Most common customer location
if location_col:
    common_location = customers_df[location_col].mode(dropna=True)
    common_location = common_location.iloc[0] if not common_location.empty else "No mode (all NA?)"
else:
    common_location = "Location column not found"

# 2) Highest/Lowest product price (clean to numeric first)
price_non_num_ct = 0
if price_col in products_df.columns:
    price_clean = clean_numeric(products_df[price_col])
    price_non_num_ct = price_clean.isna().sum()
    highest_price = price_clean.max()
    lowest_price = price_clean.min()
else:
    highest_price = None
    lowest_price = None

# 3) Sales summary (avg, min, max) — clean to numeric
sales_non_num_ct = 0
if sales_amt_col in sales_df.columns:
    sale_clean = clean_numeric(sales_df[sales_amt_col])
    sales_non_num_ct = sale_clean.isna().sum()
    avg_sales = sale_clean.mean()
    min_sales = sale_clean.min()
    max_sales = sale_clean.max()
else:
    avg_sales = min_sales = max_sales = None

# 4) Data issues
data_issues = []


def basic_issues(name, df):
    issues = []
    miss = int(df.isna().sum().sum())
    dups = int(df.duplicated().sum())
    if miss > 0:
        issues.append(f"{name}: {miss} missing values")
    if dups > 0:
        issues.append(f"{name}: {dups} duplicate rows")
    return issues


data_issues += basic_issues("customers_data", customers_df)
data_issues += basic_issues("products_data", products_df)
data_issues += basic_issues("sales_data", sales_df)

if price_col in products_df.columns and price_non_num_ct > 0:
    data_issues.append(
        f"products_data.{price_col}: {price_non_num_ct} values coerced to NaN during numeric cleaning"
    )

if sales_amt_col in sales_df.columns and sales_non_num_ct > 0:
    data_issues.append(
        f"sales_data.{sales_amt_col}: {sales_non_num_ct} values coerced to NaN during numeric cleaning"
    )

if not data_issues:
    data_issues.append("No obvious data issues found")

# ---------- Save results ----------
results = {
    "Common Customer Location": [common_location],
    "Highest Product Price": [highest_price],
    "Lowest Product Price": [lowest_price],
    "Average Sales Amount": [avg_sales],
    "Minimum Sales Amount": [min_sales],
    "Maximum Sales Amount": [max_sales],
    "Data Issues Found": ["; ".join(data_issues)],
}

out_df = pd.DataFrame(results)
out_path = os.path.join(RESULTS_PATH, "analysis_results.csv")
out_df.to_csv(out_path, index=False)

print(f"✅ Analysis complete. Results saved to: {out_path}")
