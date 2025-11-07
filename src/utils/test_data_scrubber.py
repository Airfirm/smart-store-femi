"""
utils/data_scrubber.py

A robust and reusable DataScrubber class for cleaning, validating,
and preparing datasets for analytics, BI, and ETL workflows.

Features:
- Standard data cleaning (duplicates, whitespace, columns)
- Missing value handling
- Numeric and datetime conversion
- Outlier detection via IQR
- Category standardization
- Data validation (ID checks, email formats, future dates)
"""

import pandas as pd
import numpy as np
import re
from typing import List, Optional
from datetime import datetime


class DataScrubber:
    """Reusable class for general-purpose data cleaning and validation."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    # -------------------------------------------------------------------------
    # BASIC CLEANING
    # -------------------------------------------------------------------------
    def clean_column_names(self) -> "DataScrubber":
        """Standardize column names (lowercase, underscores, stripped)."""
        self.df.columns = (
            self.df.columns.str.strip()
            .str.lower()
            .str.replace(r"[^\w\s]", "", regex=True)
            .str.replace(r"\s+", "_", regex=True)
        )
        return self

    def trim_whitespace(self) -> "DataScrubber":
        """Remove leading/trailing whitespace from text columns."""
        for col in self.df.select_dtypes(include=["object", "string"]).columns:
            self.df[col] = self.df[col].astype(str).str.strip()
        return self

    def remove_duplicate_records(self) -> "DataScrubber":
        """Remove duplicate rows."""
        before = len(self.df)
        self.df.drop_duplicates(inplace=True)
        after = len(self.df)
        print(f"✅ Removed {before - after} duplicate rows.")
        return self

    # -------------------------------------------------------------------------
    # MISSING VALUES
    # -------------------------------------------------------------------------
    def fill_missing(
        self, strategy: str = "mean", columns: Optional[List[str]] = None
    ) -> "DataScrubber":
        """
        Fill missing numeric values based on strategy.
        Options: mean, median, mode, zero.
        """
        cols = columns or self.df.select_dtypes(include=[np.number]).columns
        for col in cols:
            if self.df[col].isna().any():
                if strategy == "mean":
                    self.df[col].fillna(self.df[col].mean(), inplace=True)
                elif strategy == "median":
                    self.df[col].fillna(self.df[col].median(), inplace=True)
                elif strategy == "mode":
                    self.df[col].fillna(self.df[col].mode().iloc[0], inplace=True)
                elif strategy == "zero":
                    self.df[col].fillna(0, inplace=True)
        return self

    def drop_missing(self, threshold: float = 0.5) -> "DataScrubber":
        """Drop rows or columns exceeding missing threshold."""
        self.df.dropna(axis=1, thresh=int(len(self.df) * (1 - threshold)), inplace=True)
        self.df.dropna(axis=0, thresh=int(self.df.shape[1] * (1 - threshold)), inplace=True)
        return self

    # -------------------------------------------------------------------------
    # DATA TYPE FIXES
    # -------------------------------------------------------------------------
    def convert_to_numeric(self, columns: Optional[List[str]] = None) -> "DataScrubber":
        """Convert numeric-like columns safely."""
        cols = columns or self.df.columns
        for col in cols:
            try:
                self.df[col] = (
                    self.df[col]
                    .astype(str)
                    .str.replace(r"[^\d\.\-]", "", regex=True)
                    .replace("", np.nan)
                )
                try:
                    self.df[col] = pd.to_numeric(self.df[col])
                except Exception:
                    pass
            except Exception as e:
                print(f"⚠️ Could not convert {col} to numeric: {e}")
        return self

    def convert_to_datetime(
        self, columns: Optional[List[str]] = None, date_format: Optional[str] = None
    ) -> "DataScrubber":
        """Convert date-like columns safely."""
        cols = columns or [c for c in self.df.columns if "date" in c.lower()]
        for col in cols:
            try:
                self.df[col] = pd.to_datetime(self.df[col], format=date_format, errors="coerce")
            except Exception as e:
                print(f"⚠️ Could not convert {col} to datetime: {e}")
        return self

    # -------------------------------------------------------------------------
    # OUTLIER DETECTION
    # -------------------------------------------------------------------------
    def remove_outliers_iqr(
        self, columns: Optional[List[str]] = None, factor: float = 1.5
    ) -> "DataScrubber":
        """Remove numeric outliers using the IQR method."""
        cols = columns or self.df.select_dtypes(include=[np.number]).columns
        for col in cols:
            if self.df[col].dtype.kind in "biufc":  # numeric types
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower, upper = Q1 - factor * IQR, Q3 + factor * IQR
                before = len(self.df)
                self.df = self.df[(self.df[col] >= lower) & (self.df[col] <= upper)]
                print(f"✅ {col}: removed {before - len(self.df)} outliers.")
        return self

    # -------------------------------------------------------------------------
    # CATEGORICAL CLEANING
    # -------------------------------------------------------------------------
    def standardize_categories(self, columns: Optional[List[str]] = None) -> "DataScrubber":
        """Lowercase and strip punctuation from categorical text."""
        cols = columns or self.df.select_dtypes(include=["object", "string"]).columns
        for col in cols:
            self.df[col] = (
                self.df[col]
                .astype(str)
                .str.lower()
                .str.replace(r"[^a-z0-9\s]", "", regex=True)
                .str.strip()
            )
        return self

    # -------------------------------------------------------------------------
    # VALIDATION RULES
    # -------------------------------------------------------------------------
    def validate_unique_id(self, id_col: str) -> bool:
        """Check if an ID column is unique and positive."""
        if id_col not in self.df.columns:
            print(f"⚠️ Column {id_col} not found.")
            return False
        unique_ratio = self.df[id_col].nunique() / len(self.df)
        all_positive = (self.df[id_col] > 0).all()
        print(
            f"🔍 {id_col}: {unique_ratio:.2%} unique | "
            f"{'✅ All positive' if all_positive else '❌ Contains negatives'}"
        )
        return unique_ratio == 1.0 and all_positive

    def validate_email(self, email_col: str) -> None:
        """Validate email formats using regex."""
        if email_col not in self.df.columns:
            print(f"⚠️ Column {email_col} not found.")
            return
        invalid_emails = self.df[
            ~self.df[email_col].astype(str).str.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", na=False)
        ]
        print(f"📧 Invalid emails: {len(invalid_emails)}")
        if not invalid_emails.empty:
            print(invalid_emails[email_col].head())
        return

    def validate_no_future_dates(self, date_cols: Optional[List[str]] = None) -> None:
        """Flag dates that are in the future."""
        cols = date_cols or [
            c for c in self.df.columns if "date" in c.lower() or "dob" in c.lower()
        ]
        today = pd.Timestamp(datetime.now().date())
        for col in cols:
            if col in self.df.columns and pd.api.types.is_datetime64_any_dtype(self.df[col]):
                invalid = self.df[self.df[col] > today]
                print(f"🕒 {col}: {len(invalid)} future dates found.")
        return

    def validate_numeric_range(self, col: str, min_val: float, max_val: float) -> None:
        """Check for numeric values outside an acceptable range."""
        if col not in self.df.columns:
            print(f"⚠️ Column {col} not found.")
            return
        invalid = self.df[(self.df[col] < min_val) | (self.df[col] > max_val)]
        print(f"📏 {col}: {len(invalid)} values outside range [{min_val}, {max_val}]")
        return

    # -------------------------------------------------------------------------
    # UTILITIES
    # -------------------------------------------------------------------------
    def summary(self) -> None:
        """Print a data summary."""
        print("\n=== 🧹 DATA SCRUBBER SUMMARY ===")
        print(f"Shape: {self.df.shape}")
        print("Missing values per column:")
        print(self.df.isna().sum())
        print("================================\n")

    def get_data(self) -> pd.DataFrame:
        """Return cleaned DataFrame."""
        return self.df
