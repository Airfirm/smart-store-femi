"""ETL script to load prepared data into the data warehouse (SQLite database).

File: src/analytics_project/dw/etl_to_dw.py

This file assumes the following structure (yours may vary):

project_root/
│
├─ data/
│   ├─ raw/
│   ├─ prepared/
│   └─ warehouse/
│
└─ src/
    └─ analytics_project/
        ├─ data_preparation/
        ├─ dw/
        ├─ analytics/
        └─ utils_logger.py

By switching to a modern src/ layout and using __init__.py files,
we no longer need any sys.path modifications.

Remember to put __init__.py files (empty is fine) in each folder to make them packages.

NOTE on column names: This example uses inconsistent naming conventions for column names in the cleaned data.
A good business intelligence project would standardize these during data preparation.
Your names should be more standard after cleaning and pre-processing the data.

Database names generally follow snake_case conventions for SQL compatibility.
"snake_case" =  all lowercase with underscores between words.
"""

# Imports at the top

import pathlib
import sqlite3

import pandas as pd

from analytics_project.utils_logger import logger

# Global constants for paths and key directories

THIS_DIR: pathlib.Path = pathlib.Path(__file__).resolve().parent
DW_DIR: pathlib.Path = THIS_DIR  # src/analytics_project/dw/
PACKAGE_DIR: pathlib.Path = DW_DIR.parent  # src/analytics_project/
SRC_DIR: pathlib.Path = PACKAGE_DIR.parent  # src/
PROJECT_ROOT_DIR: pathlib.Path = SRC_DIR.parent  # project_root/

# Data directories
DATA_DIR: pathlib.Path = PROJECT_ROOT_DIR / "data"
RAW_DATA_DIR: pathlib.Path = DATA_DIR / "raw"
CLEAN_DATA_DIR: pathlib.Path = DATA_DIR / "salary_analysis"
WAREHOUSE_DIR: pathlib.Path = DATA_DIR / "warehouse"

# Warehouse database location (SQLite)
DB_PATH: pathlib.Path = WAREHOUSE_DIR / "salary_data_2024.db"

# Recommended - log paths and key directories for debugging

logger.info(f"THIS_DIR:            {THIS_DIR}")
logger.info(f"DW_DIR:              {DW_DIR}")
logger.info(f"PACKAGE_DIR:         {PACKAGE_DIR}")
logger.info(f"SRC_DIR:             {SRC_DIR}")
logger.info(f"PROJECT_ROOT_DIR:    {PROJECT_ROOT_DIR}")

logger.info(f"DATA_DIR:            {DATA_DIR}")
logger.info(f"RAW_DATA_DIR:        {RAW_DATA_DIR}")
logger.info(f"CLEAN_DATA_DIR:      {CLEAN_DATA_DIR}")
logger.info(f"WAREHOUSE_DIR:       {WAREHOUSE_DIR}")
logger.info(f"DB_PATH:             {DB_PATH}")


def create_schema(cursor: sqlite3.Cursor) -> None:
    """Create tables in the data warehouse if they don't exist."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salary_data_2024 (
            work_year INTEGER PRIMARY KEY,
            experience_level TEXT,
            employment_type TEXT,
            job_title TEXT,
            salary REAL,
            salary_currency TEXT,
            salary_in_usd REAL,
            employee_residence TEXT,
            remote_ratio INTEGER,
            company_location TEXT,
            company_size TEXT
        )
    """)


def delete_existing_records(cursor: sqlite3.Cursor) -> None:
    """Delete all existing records from the salary_data_2024 table."""
    cursor.execute("DELETE FROM salary_data_2024")


def insert_salary_data_2024(salary_data_2024_df: pd.DataFrame, cursor: sqlite3.Cursor) -> None:
    """Insert salary_data_2024 data into the salary_data_2024 table."""
    logger.info(f"Inserting {len(salary_data_2024_df)} salary_data_2024 rows.")
    salary_data_2024_df.to_sql(
        "salary_data_2024", cursor.connection, if_exists="replace", index=False
    )


def load_data_to_db() -> None:
    """Load clean data into the data warehouse."""
    logger.info("Starting ETL: loading clean data into the warehouse.")

    # Make sure the warehouse directory exists
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)

    # If an old database exists, remove and recreate with the latest table definitions.
    if DB_PATH.exists():
        logger.info(f"Removing existing warehouse database at: {DB_PATH}")
        DB_PATH.unlink()

    # Initialize a connection variable
    # before the try block so we can close it in finally
    conn: sqlite3.Connection | None = None

    try:
        # Connect to SQLite. Create the file if it doesn't exist
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create schema and clear existing records
        create_schema(cursor)
        delete_existing_records(cursor)

        # Load prepared data using pandas
        salary_data_2024_df = pd.read_csv(CLEAN_DATA_DIR.joinpath("salary_data_2024.csv"))

        # Insert data into the database for all tables

        insert_salary_data_2024(salary_data_2024_df, cursor)

        conn.commit()
        logger.info("ETL finished successfully. Data loaded into the warehouse.")
    finally:
        # Regardless of success or failure, close the DB connection if it exists
        if conn is not None:
            logger.info("Closing database connection.")
            conn.close()


if __name__ == "__main__":
    load_data_to_db()
