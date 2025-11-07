"""
scripts/data_preparation/prepare_products.py

This script reads customer data from the data/raw folder, cleans the data,
and writes the cleaned version to the data/prepared folder.

Tasks:
- Remove duplicates
- Handle missing values
- Remove outliers
- Ensure consistent formatting
"""

#####################################
# Import Modules
#####################################

import pathlib
import sys
import pandas as pd

# Ensure project root is in sys.path for local imports
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))

# Import local modules
from utils.logger import logger
from utils.data_scrubber import DataScrubber


#####################################
# Paths
#####################################

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent  # go one level higher
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PREPARED_DATA_DIR = DATA_DIR / "prepared"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PREPARED_DATA_DIR.mkdir(parents=True, exist_ok=True)

#####################################
# Helper Functions
#####################################


def read_raw_data(file_name: str) -> pd.DataFrame:
    """Read raw CSV data safely."""
    file_path = RAW_DATA_DIR / file_name
    try:
        logger.info(f"READING: {file_path}")
        df = pd.read_csv(file_path)
        if df.empty:
            logger.warning(f"{file_path} is empty — continuing with empty DataFrame.")
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return pd.DataFrame()


def save_prepared_data(df: pd.DataFrame, file_name: str) -> None:
    """Save cleaned data to CSV."""
    file_path = PREPARED_DATA_DIR / file_name
    df.to_csv(file_path, index=False)
    logger.info(f"✅ Data saved to {file_path}")


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    logger.info(f"Removing duplicates from DataFrame with shape {df.shape}")
    if df.empty:
        logger.warning("DataFrame is empty — skipping duplicate removal.")
        return df
    return DataScrubber(df).remove_duplicate_records()


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    logger.info(f"Handling missing values for DataFrame shape {df.shape}")
    if df.empty:
        logger.warning("DataFrame is empty — skipping missing value handling.")
        return df

    missing_before = df.isna().sum().sum()
    logger.info(f"Missing values before: {missing_before}")

    if "SupplierName" in df.columns:
        df.dropna(subset=["SupplierName"], inplace=True)

    missing_after = df.isna().sum().sum()
    logger.info(f"Missing values after: {missing_after}")
    return df


def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Removing outliers...")
    if df.empty:
        logger.warning("DataFrame is empty — skipping outlier removal.")
        return df

    initial_count = len(df)
    if "SatisfactionScore" in df.columns:
        df = df[(df["SatisfactionScore"] >= 1) & (df["SatisfactionScore"] <= 10)]
    logger.info(f"Removed {initial_count - len(df)} outliers.")
    return df


#####################################
# Main Script
#####################################


def main():
    logger.info("==================================")
    logger.info("STARTING prepare_products_data.py")
    logger.info("==================================")

    logger.info(f"Root         : {PROJECT_ROOT}")
    logger.info(f"data/raw     : {RAW_DATA_DIR}")
    logger.info(f"data/prepared: {PREPARED_DATA_DIR}")

    input_file = "products_data.csv"
    output_file = "products_prepared.csv"

    df = read_raw_data(input_file)

    if df.empty:
        logger.error("No data loaded. Exiting early.")
        return

    # Clean column names safely
    df.columns = df.columns.astype(str).str.strip()

    df = remove_duplicates(df)
    df = handle_missing_values(df)
    df = remove_outliers(df)

    save_prepared_data(df, output_file)

    logger.info("==================================")
    logger.info(f"✅ Finished cleaning. Final shape: {df.shape}")
    logger.info("==================================")
    logger.info("FINISHED prepare_products_data.py")
    logger.info("==================================")


if __name__ == "__main__":
    main()
