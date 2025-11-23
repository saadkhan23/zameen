#!/usr/bin/env python3
"""
utils.py

Shared utility functions for Zameen analysis modules.

This module consolidates duplicate utility functions that were previously
scattered across multiple analysis files:
- construction_cost_analysis.py
- size_vs_price_analysis.py
- bargains_analysis.py
- bottom_up_calculator.py

Functions extract and normalize data, find columns, and work with timestamped folders.
"""

from pathlib import Path
import logging
import pandas as pd
import re
from typing import Optional, Union

logger = logging.getLogger(__name__)


def get_latest_timestamped_folder(precinct_dir: Path) -> Optional[Path]:
    """
    Find the latest timestamped run folder in a precinct directory.

    Assumes folder names like "2025-11-11_124325" (lexicographically sortable).
    Returns the path to the latest folder, or None if no valid folders found.

    Args:
        precinct_dir: Path to precinct directory containing timestamped subdirectories

    Returns:
        Path to the latest timestamped folder, or None if not found
    """
    timestamp_folders = [d for d in precinct_dir.iterdir() if d.is_dir()]
    if not timestamp_folders:
        return None
    return sorted(timestamp_folders)[-1]  # Lexicographically largest


def read_excel_sheet(
    filepath: Path, sheet_name: str = "Properties"
) -> Optional[pd.DataFrame]:
    """
    Safely read an Excel sheet.

    Tries to read the specified sheet_name first.
    Falls back to the first sheet if sheet_name doesn't exist.
    Returns None if file doesn't exist or read fails.

    Args:
        filepath: Path to Excel file
        sheet_name: Name of sheet to read (default: "Properties")

    Returns:
        DataFrame with sheet contents, or None if file doesn't exist or read fails
    """
    if not filepath.exists():
        logger.debug(f"Excel file not found: {filepath}")
        return None

    try:
        excel_file = pd.ExcelFile(filepath)

        # Try to use the specified sheet name
        if sheet_name in excel_file.sheet_names:
            return pd.read_excel(filepath, sheet_name=sheet_name)

        # Fall back to first sheet
        return pd.read_excel(filepath, sheet_name=0)

    except FileNotFoundError as e:
        logger.warning(f"Excel file not found: {filepath}")
        return None
    except (KeyError, ValueError) as e:
        logger.warning(f"Invalid sheet name '{sheet_name}' in {filepath.name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to read {filepath.name}: {e}")
        return None


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DataFrame column names to lowercase with underscores.

    Converts spaces to underscores and lowercases all characters for
    consistent column naming across different data sources.

    Args:
        df: Input DataFrame with potentially mixed-case column names

    Returns:
        DataFrame with normalized lowercase underscore-separated column names
    """
    df.columns = [col.lower().replace(" ", "_") for col in df.columns]
    return df


def flag_grey_structure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add boolean column 'is_grey_structure' based on title/description keywords.

    Searches title and description columns for keywords indicating grey structure
    (unfinished or shell properties). Adds a new 'is_grey_structure' boolean column.

    Grey structure keywords include:
    - grey structure, gray structure
    - grey-work, greywork
    - core & shell, core and shell
    - shell only, structure only
    - semi-finished, unfinished
    - without finishing

    Args:
        df: Input DataFrame with 'title' and/or description columns

    Returns:
        DataFrame with added 'is_grey_structure' boolean column (default False if unable to determine)
    """
    if df is None or df.empty:
        return df

    cols = [c for c in df.columns]
    title_col = None
    desc_col = None

    # Find candidate columns post-normalization
    for c in cols:
        lc = c.lower()
        if lc == "title":
            title_col = c
        if lc in ("short_description", "description", "details"):
            desc_col = c if desc_col is None else desc_col

    # Regex pattern for grey structure keywords
    pattern = re.compile(
        r"(grey\s*structure|gray\s*structure|grey-?work|greywork|core\s*&\s*shell|"
        r"core\s*and\s*shell|shell\s*only|structure\s*only|semi[-\s]?finished|"
        r"unfinished|without\s*finishing)",
        re.IGNORECASE,
    )

    def is_grey(row) -> bool:
        t = str(row.get(title_col, "") or "") if title_col else ""
        d = str(row.get(desc_col, "") or "") if desc_col else ""
        text = f"{t} \n {d}"
        return bool(pattern.search(text))

    try:
        df["is_grey_structure"] = df.apply(is_grey, axis=1)
    except (ValueError, TypeError, KeyError) as e:
        logger.warning(f"Failed to flag grey structures: {e}")
        df["is_grey_structure"] = False
    except Exception as e:
        logger.error(f"Unexpected error flagging grey structures: {e}")
        df["is_grey_structure"] = False

    return df


def find_price_column(df: pd.DataFrame) -> Optional[str]:
    """
    Find the price column by looking for common naming patterns.

    Tries common price column patterns, then falls back to any column
    containing "price" or "cost". Returns the actual column name from
    the dataframe (or None if not found).

    Common patterns checked (in order):
    - price_pkr
    - price
    - asking_price
    - cost

    Args:
        df: Input DataFrame

    Returns:
        Name of price column found, or None if no suitable column found
    """
    normalized_cols = {col.lower(): col for col in df.columns}

    # Try common patterns
    patterns = ["price_pkr", "price", "asking_price", "cost"]
    for pattern in patterns:
        if pattern in normalized_cols:
            return normalized_cols[pattern]

    # Try columns that contain "price" or "cost"
    for lower_col, actual_col in normalized_cols.items():
        if "price" in lower_col or "cost" in lower_col:
            return actual_col

    return None


def find_size_column(df: pd.DataFrame) -> Optional[str]:
    """
    Find the size column by looking for common naming patterns.

    Tries common size column patterns, then falls back to any column
    containing "size", "area", or "sq". Returns the actual column name
    from the dataframe (or None if not found).

    Common patterns checked (in order):
    - area_sqyd
    - size_sq_yd
    - size
    - area_sqm
    - area

    Args:
        df: Input DataFrame

    Returns:
        Name of size column found, or None if no suitable column found
    """
    normalized_cols = {col.lower(): col for col in df.columns}

    # Try common patterns
    patterns = ["area_sqyd", "size_sq_yd", "size", "area_sqm", "area"]
    for pattern in patterns:
        if pattern in normalized_cols:
            return normalized_cols[pattern]

    # Try columns that contain "size" or "area" or "sq"
    for lower_col, actual_col in normalized_cols.items():
        if "size" in lower_col or "area" in lower_col or "sq" in lower_col:
            return actual_col

    return None


def safe_numeric(val) -> Optional[float]:
    """
    Safely convert value to float. Returns None if conversion fails.

    Handles None, NaN, and invalid string values gracefully.

    Args:
        val: Value to convert to float

    Returns:
        Float value, or None if conversion fails
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
