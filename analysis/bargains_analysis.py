#!/usr/bin/env python3
"""
bargains_analysis.py

Analysis of bargain properties across Bahria Town precincts.

For each precinct:
1. Find latest timestamped run in data/<precinct>/
2. Load houses.xlsx
3. Extract price, size_sq_yd, calculate price_per_sq_yd
4. Compute z-score: (price_per_sq_yd - median) / std
5. Flag bargains: price_per_sq_yd < median AND z_score < -0.8
6. Export summary and detailed CSVs
7. Export lightweight JSON for portfolio frontend

Usage:
    python3 analysis/bargains_analysis.py          # Normal mode
    python3 analysis/bargains_analysis.py --verbose # Detailed output
"""

from pathlib import Path
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import json
import sys
import re

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"

# Setup logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Global verbose flag
VERBOSE = "--verbose" in sys.argv


def get_latest_timestamped_folder(precinct_dir: Path) -> Optional[Path]:
    """
    Find the latest timestamped run folder in a precinct directory.

    Assumes folder names like "2025-11-11_124325" (lexicographically sortable).
    Returns the path to the latest folder, or None if no valid folders found.
    """
    timestamp_folders = [d for d in precinct_dir.iterdir() if d.is_dir()]
    if not timestamp_folders:
        return None
    return sorted(timestamp_folders)[-1]  # Lexicographically largest


def read_excel_sheet(filepath: Path, sheet_name: str = "Properties") -> Optional[pd.DataFrame]:
    """
    Safely read an Excel sheet.

    Tries to read the specified sheet_name first.
    Falls back to the first sheet if sheet_name doesn't exist.
    Returns None if file doesn't exist or read fails.
    """
    if not filepath.exists():
        return None

    try:
        excel_file = pd.ExcelFile(filepath)

        # Try to use the specified sheet name
        if sheet_name in excel_file.sheet_names:
            return pd.read_excel(filepath, sheet_name=sheet_name)

        # Fall back to first sheet
        return pd.read_excel(filepath, sheet_name=0)

    except Exception as e:
        logger.warning(f"Failed to read {filepath.name}: {e}")
        return None


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DataFrame column names to lowercase with underscores.
    """
    df.columns = [col.lower().replace(" ", "_") for col in df.columns]
    return df


def flag_grey_structure(df: pd.DataFrame) -> pd.DataFrame:
    """Add boolean column 'is_grey_structure' based on title/description keywords."""
    if df is None or df.empty:
        return df

    cols = [c for c in df.columns]
    title_col = None
    desc_col = None
    for c in cols:
        lc = c.lower()
        if lc == "title":
            title_col = c
        if lc in ("short_description", "description", "details"):
            desc_col = c if desc_col is None else desc_col

    pattern = re.compile(r"(grey\s*structure|gray\s*structure|grey-?work|greywork|core\s*&\s*shell|core\s*and\s*shell|shell\s*only|structure\s*only|semi[-\s]?finished|unfinished|without\s*finishing)", re.IGNORECASE)

    def is_grey(row) -> bool:
        t = str(row.get(title_col, "") or "") if title_col else ""
        d = str(row.get(desc_col, "") or "") if desc_col else ""
        text = f"{t} \n {d}"
        return bool(pattern.search(text))

    try:
        df["is_grey_structure"] = df.apply(is_grey, axis=1)
    except Exception:
        df["is_grey_structure"] = False
    return df


def find_price_column(df: pd.DataFrame) -> Optional[str]:
    """
    Find the price column by looking for common naming patterns.
    Returns the actual column name from the dataframe (or None if not found).
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
    Returns the actual column name from the dataframe (or None if not found).
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


def analyze_precinct(precinct_dir: Path) -> Optional[Dict]:
    """
    Analyze a single precinct: identify bargain properties.

    Returns a dict with:
    {
        "precinct": str,
        "n_houses": int,
        "n_bargains": int,
        "bargain_pct": float,
        "median_price_per_sq_yd": float,
        "std_price_per_sq_yd": float,
        "min_bargain_price_per_sq_yd": float,
        "max_bargain_price_per_sq_yd": float
    }

    Returns None if analysis fails.
    """
    precinct_name = precinct_dir.name
    logger.info(f"Analyzing {precinct_name}...")

    # Get latest run
    latest_run = get_latest_timestamped_folder(precinct_dir)
    if not latest_run:
        logger.warning(f"  No timestamped runs found. Skipping.")
        return None

    logger.info(f"  Latest run: {latest_run.name}")

    # Read houses
    houses_file = latest_run / "houses.xlsx"
    df_houses = read_excel_sheet(houses_file)

    if df_houses is None:
        logger.warning(f"  {precinct_name}: No houses.xlsx found. Skipping.")
        return None

    # Normalize columns
    df_houses = normalize_columns(df_houses)
    df_houses = flag_grey_structure(df_houses)

    # Find price and size columns
    price_col = find_price_column(df_houses)
    size_col = find_size_column(df_houses)

    if not price_col or not size_col:
        logger.warning(f"  {precinct_name}: Could not find price/size columns. Skipping.")
        return None

    # Extract and clean data
    try:
        prices = pd.to_numeric(df_houses[price_col], errors="coerce")
        sizes = pd.to_numeric(df_houses[size_col], errors="coerce")

        # Remove rows with NaN
        valid_idx = prices.notna() & sizes.notna()
        prices = prices[valid_idx]
        sizes = sizes[valid_idx]

        if len(prices) == 0:
            logger.warning(f"  {precinct_name}: No valid price/size data. Skipping.")
            return None

        # Calculate price per sq yd
        price_per_sq_yd = prices / sizes

        # Exclude grey structures from statistical baseline and counts
        non_grey_mask = ~df_houses.get("is_grey_structure", pd.Series(False, index=df_houses.index))
        prices_ng = prices[non_grey_mask]
        sizes_ng = sizes[non_grey_mask]
        price_per_sq_yd_ng = price_per_sq_yd[non_grey_mask]

        # Compute median and std
        median_price = price_per_sq_yd_ng.median()
        std_price = price_per_sq_yd_ng.std()

        if std_price == 0:
            logger.warning(f"  {precinct_name}: Zero standard deviation. Skipping.")
            return None

        # Compute z-scores
        z_scores = (price_per_sq_yd - median_price) / std_price

        # Flag bargains: price_per_sq_yd < median AND z_score < -0.8
        # Bargains among finished houses only
        is_bargain = (price_per_sq_yd < median_price) & (z_scores < -0.8) & non_grey_mask

        n_bargains = int(is_bargain.sum())
        # Count houses considered (non-grey)
        n_houses = int(price_per_sq_yd_ng.shape[0])
        bargain_pct = (n_bargains / n_houses) * 100 if n_houses > 0 else 0.0
        n_grey = int((~non_grey_mask).sum())

        # Bargain price stats
        bargain_prices = price_per_sq_yd[is_bargain]
        if len(bargain_prices) > 0:
            min_bargain = bargain_prices.min()
            max_bargain = bargain_prices.max()
        else:
            min_bargain = None
            max_bargain = None

        logger.info(f"  {precinct_name} Summary:")
        logger.info(f"    Total houses (finished): {n_houses}  | Grey structures excluded: {n_grey}")
        logger.info(f"    Median price per sq yd: {median_price:,.0f} PKR/sq yd")
        logger.info(f"    Std dev: {std_price:,.0f} PKR/sq yd")
        logger.info(f"    Bargains found: {n_bargains} ({bargain_pct:.1f}%)")

        if len(bargain_prices) > 0:
            logger.info(f"    Bargain price range: {min_bargain:,.0f} - {max_bargain:,.0f} PKR/sq yd")

        if VERBOSE:
            logger.info(f"    [Verbose] Price per sq yd distribution:")
            logger.info(f"      Min: {price_per_sq_yd.min():,.0f} PKR/sq yd")
            logger.info(f"      p10: {price_per_sq_yd.quantile(0.10):,.0f} PKR/sq yd")
            logger.info(f"      p25: {price_per_sq_yd.quantile(0.25):,.0f} PKR/sq yd")
            logger.info(f"      p50: {price_per_sq_yd.median():,.0f} PKR/sq yd")
            logger.info(f"      p75: {price_per_sq_yd.quantile(0.75):,.0f} PKR/sq yd")
            logger.info(f"      Max: {price_per_sq_yd.max():,.0f} PKR/sq yd")

            if len(bargain_prices) > 0:
                logger.info(f"    [Verbose] Z-score cutoff: -0.8 (price < median AND z < -0.8)")
                logger.info(f"      Sample bargains (first 3):")
                for idx, (price_sq, z_score) in enumerate(zip(bargain_prices.head(3), z_scores[is_bargain].head(3))):
                    logger.info(f"        {idx+1}. {price_sq:,.0f} PKR/sq yd (z={z_score:.2f})")

        return {
            "precinct": precinct_name,
            "n_houses": n_houses,
            "n_bargains": int(n_bargains),
            "bargain_pct": round(bargain_pct, 2),
            "median_price_per_sq_yd": round(median_price, 2),
            "std_price_per_sq_yd": round(std_price, 2),
            "min_bargain_price_per_sq_yd": round(min_bargain, 2) if min_bargain else None,
            "max_bargain_price_per_sq_yd": round(max_bargain, 2) if max_bargain else None,
            "n_grey_structures": n_grey
        }

    except Exception as e:
        logger.error(f"  {precinct_name}: Failed to analyze: {e}")
        return None


def build_detailed_csv(precinct_dirs: List[Path]) -> pd.DataFrame:
    """
    Build a comprehensive CSV with all houses and bargain flags.
    """
    all_rows = []

    for precinct_dir in sorted(precinct_dirs):
        precinct_name = precinct_dir.name
        latest_run = get_latest_timestamped_folder(precinct_dir)

        if not latest_run:
            continue

        houses_file = latest_run / "houses.xlsx"
        df_houses = read_excel_sheet(houses_file)

        if df_houses is None:
            continue

        df_houses = normalize_columns(df_houses)
        df_houses = flag_grey_structure(df_houses)
        price_col = find_price_column(df_houses)
        size_col = find_size_column(df_houses)

        if not price_col or not size_col:
            continue

        try:
            prices = pd.to_numeric(df_houses[price_col], errors="coerce")
            sizes = pd.to_numeric(df_houses[size_col], errors="coerce")

            # Calculate price per sq yd
            valid_idx = prices.notna() & sizes.notna()
            price_per_sq_yd = prices[valid_idx] / sizes[valid_idx]

            # Compute stats on non-grey houses
            non_grey_mask = ~df_houses.get("is_grey_structure", pd.Series(False, index=df_houses.index))
            non_grey_idx = valid_idx & non_grey_mask
            price_per_sq_yd_ng = price_per_sq_yd[non_grey_idx[non_grey_idx].index]

            # Compute median and std
            median_price = price_per_sq_yd_ng.median()
            std_price = price_per_sq_yd_ng.std()

            if std_price == 0:
                continue

            # Compute z-scores
            z_scores = (price_per_sq_yd - median_price) / std_price

            # Flag bargains
            # Bargains among finished houses only
            is_bargain = (price_per_sq_yd < median_price) & (z_scores < -0.8) & non_grey_mask[valid_idx]

            # Build rows
            for idx in valid_idx[valid_idx].index:
                price = prices[idx]
                size = sizes[idx]
                price_sq_yd = price / size
                z_score = (price_sq_yd - median_price) / std_price if std_price and std_price != 0 else np.nan
                bargain = bool(is_bargain[idx]) if idx in is_bargain.index else False
                
                all_rows.append({
                    "precinct": precinct_name,
                    "price": round(price, 2),
                    "size_sq_yd": round(size, 2),
                    "price_per_sq_yd": round(price_sq_yd, 2),
                    "z_score": round(z_score, 4) if not pd.isna(z_score) else None,
                    "is_bargain": 1 if bargain else 0,
                    "is_grey_structure": 1 if df_houses.get("is_grey_structure", pd.Series(False)).get(idx, False) else 0,
                })
        except Exception as e:
            logger.warning(f"Error processing {precinct_name}: {e}")
            continue

    return pd.DataFrame(all_rows)


def main() -> None:
    """
    Main analysis workflow:
    1. Find all precinct folders in data/
    2. Analyze each precinct for bargains
    3. Export summary CSV (per precinct)
    4. Export detailed CSV (all properties)
    5. Export lightweight JSON for portfolio
    6. Print summary to stdout
    """
    logger.info("=" * 70)
    logger.info("Zameen Bargains Analysis")
    logger.info("=" * 70)

    if not DATA_DIR.exists():
        logger.error(f"Data directory not found: {DATA_DIR}")
        return

    # Find all precinct folders
    precinct_dirs = [d for d in DATA_DIR.iterdir() if d.is_dir()]
    if not precinct_dirs:
        logger.error("No precinct folders found in data/")
        return

    logger.info(f"Found {len(precinct_dirs)} precinct(s). Starting analysis...\n")

    # Analyze each precinct
    results: List[Dict] = []
    for precinct_dir in sorted(precinct_dirs):
        result = analyze_precinct(precinct_dir)
        if result:
            results.append(result)

    if not results:
        logger.error("No precincts analyzed successfully.")
        return

    # Create summary DataFrame
    df_summary = pd.DataFrame(results)

    # Build detailed CSV with all properties
    logger.info("\nBuilding detailed CSV with bargain flags...")
    df_detailed = build_detailed_csv(precinct_dirs)

    if df_detailed.empty:
        logger.error("Failed to build detailed CSV.")
        return

    # Save summary CSV
    summary_csv_path = ANALYSIS_DIR / "bargains_summary.csv"
    summary_csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_summary.to_csv(summary_csv_path, index=False)
    logger.info(f"Summary CSV saved: {summary_csv_path}")

    # Save detailed CSV
    detailed_csv_path = ANALYSIS_DIR / "bargains_detailed.csv"
    df_detailed.to_csv(detailed_csv_path, index=False)
    logger.info(f"Detailed CSV saved: {detailed_csv_path}")

    # Build lightweight JSON for portfolio frontend
    portfolio_json = []
    for _, row in df_summary.iterrows():
        portfolio_json.append({
            "precinct": row["precinct"],
            "n_houses": int(row["n_houses"]),
            "n_bargains": int(row["n_bargains"]),
            "bargain_pct": row["bargain_pct"],
            "median_price_per_sq_yd": row["median_price_per_sq_yd"],
            "std_price_per_sq_yd": row["std_price_per_sq_yd"],
            "bargain_price_range": {
                "min": row["min_bargain_price_per_sq_yd"],
                "max": row["max_bargain_price_per_sq_yd"]
            }
        })

    json_path = ANALYSIS_DIR / "bargains_summary.json"
    with open(json_path, "w") as f:
        json.dump(portfolio_json, f, indent=2)
    logger.info(f"Portfolio JSON saved: {json_path}")

    logger.info("=" * 70)
    logger.info("Analysis Complete")
    logger.info("=" * 70)

    # Print summary table to stdout
    print("\n" + "=" * 70)
    print("Bargains Summary by Precinct")
    print("=" * 70)
    print(df_summary.to_string(index=False))
    print("=" * 70)

    # Count total bargains
    total_bargains = df_summary["n_bargains"].sum()
    total_houses = df_summary["n_houses"].sum()
    overall_bargain_pct = (total_bargains / total_houses * 100) if total_houses > 0 else 0

    print(f"\nTotal Properties: {total_houses}")
    print(f"Total Bargains: {total_bargains} ({overall_bargain_pct:.1f}%)")
    print(f"\nDetailed data exported to: bargains_detailed.csv ({len(df_detailed)} rows)")
    print(f"Portfolio summary exported to: bargains_summary.json")


if __name__ == "__main__":
    main()
