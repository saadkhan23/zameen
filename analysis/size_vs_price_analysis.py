#!/usr/bin/env python3
"""
size_vs_price_analysis.py

Analysis of property size vs price relationship across Bahria Town precincts.

For each precinct:
1. Find latest timestamped run in data/<precinct>/
2. Load houses.xlsx
3. Extract price, size_sq_yd, calculate price_per_sq_yd
4. Fit a simple linear regression: price = a * size + b
5. Export detailed CSV with fitted prices
6. Export lightweight JSON summary for portfolio frontend

Usage:
    python3 analysis/size_vs_price_analysis.py          # Normal mode
    python3 analysis/size_vs_price_analysis.py --verbose # Detailed output
"""

from pathlib import Path
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import json
import sys

# Import shared utilities
from utils import (
    get_latest_timestamped_folder,
    read_excel_sheet,
    normalize_columns,
    flag_grey_structure,
    find_price_column,
    find_size_column,
)

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"

# Setup logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Global verbose flag
VERBOSE = "--verbose" in sys.argv


def fit_linear_regression(
    prices: pd.Series, sizes: pd.Series
) -> Tuple[float, float]:
    """
    Fit a simple linear regression: price = a * size + b

    Args:
        prices: Series of property prices
        sizes: Series of property sizes

    Returns:
        Tuple of (slope, intercept) coefficients for the linear model
    """
    # Remove NaN values
    valid_idx = prices.notna() & sizes.notna()
    prices_clean = prices[valid_idx].values
    sizes_clean = sizes[valid_idx].values

    if len(prices_clean) < 2:
        return (0, 0)

    # Fit polynomial of degree 1
    coeffs = np.polyfit(sizes_clean, prices_clean, 1)
    return (coeffs[0], coeffs[1])  # (slope, intercept)


def analyze_precinct(precinct_dir: Path) -> Optional[Dict[str, Union[str, int, float]]]:
    """
    Analyze a single precinct: extract size/price data, fit regression.

    Args:
        precinct_dir: Path to precinct directory

    Returns:
        Dict with keys:
        - precinct (str)
        - n_houses (int)
        - median_size_sq_yd (float)
        - median_price (float)
        - median_price_per_sq_yd (float)
        - slope (float): regression coefficient
        - intercept (float): regression intercept
        - r_squared (float): R² value
        - n_grey_structures (int)

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
        try:
            prices = pd.to_numeric(df_houses[price_col], errors="coerce")
            sizes = pd.to_numeric(df_houses[size_col], errors="coerce")

            # Remove rows with NaN
            valid_idx = prices.notna() & sizes.notna()
            prices = prices[valid_idx]
            sizes = sizes[valid_idx]

            # Exclude grey structures for size vs price analysis
            non_grey_mask = ~df_houses.get("is_grey_structure", pd.Series(False, index=df_houses.index))
            prices = prices[non_grey_mask]
            sizes = sizes[non_grey_mask]

            if len(prices) == 0:
                logger.warning(f"  {precinct_name}: No valid price/size data. Skipping.")
                return None

            # Calculate price per sq yd
            price_per_sq_yd = prices / sizes

            # Fit regression
            slope, intercept = fit_linear_regression(prices, sizes)
        except (ValueError, TypeError, ZeroDivisionError) as e:
            logger.error(f"  {precinct_name}: Failed to process price/size data: {e}")
            return None

        # Calculate R² (coefficient of determination)
        fitted_prices = slope * sizes + intercept
        ss_res = np.sum((prices - fitted_prices) ** 2)
        ss_tot = np.sum((prices - prices.mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Summary statistics
        median_size = sizes.median()
        median_price = prices.median()
        median_price_per_sq_yd = price_per_sq_yd.median()
        n_houses = len(prices)
        n_grey = int(df_houses.get("is_grey_structure", pd.Series(False)).sum())

        logger.info(f"  {precinct_name} Summary:")
        logger.info(f"    Houses analyzed: {n_houses}")
        logger.info(f"    Median size: {median_size:.0f} sq yd")
        logger.info(f"    Median price: {median_price:,.0f} PKR")
        logger.info(f"    Median price per sq yd: {median_price_per_sq_yd:,.0f} PKR/sq yd")
        logger.info(f"    Regression: price = {slope:,.0f} * size + {intercept:,.0f}")
        logger.info(f"    R²: {r_squared:.4f}")

        if VERBOSE:
            logger.info(f"    [Verbose] Size stats:")
            logger.info(f"      Min: {sizes.min():.0f} sq yd")
            logger.info(f"      p25: {sizes.quantile(0.25):.0f} sq yd")
            logger.info(f"      p50: {sizes.median():.0f} sq yd")
            logger.info(f"      p75: {sizes.quantile(0.75):.0f} sq yd")
            logger.info(f"      Max: {sizes.max():.0f} sq yd")

            logger.info(f"    [Verbose] Price stats:")
            logger.info(f"      Min: {prices.min():,.0f} PKR")
            logger.info(f"      p25: {prices.quantile(0.25):,.0f} PKR")
            logger.info(f"      p50: {prices.median():,.0f} PKR")
            logger.info(f"      p75: {prices.quantile(0.75):,.0f} PKR")
            logger.info(f"      Max: {prices.max():,.0f} PKR")

            logger.info(f"    [Verbose] Sample fitted vs actual (first 5):")
            for idx in range(min(5, len(prices))):
                actual = prices.iloc[idx]
                fitted = slope * sizes.iloc[idx] + intercept
                error = actual - fitted
                logger.info(f"      House {idx+1}: Actual={actual:,.0f} PKR, Fitted={fitted:,.0f} PKR, Error={error:,.0f} PKR")

        return {
            "precinct": precinct_name,
            "n_houses": n_houses,
            "median_size_sq_yd": round(median_size, 2),
            "median_price": round(median_price, 2),
            "median_price_per_sq_yd": round(median_price_per_sq_yd, 2),
            "slope": round(slope, 2),
            "intercept": round(intercept, 2),
            "r_squared": round(r_squared, 4),
            "n_grey_structures": n_grey
        }

    except (ValueError, TypeError) as e:
        logger.error(f"  {precinct_name}: Data processing error: {e}")
        return None
    except Exception as e:
        logger.error(f"  {precinct_name}: Unexpected error during analysis: {e}")
        return None


def build_detailed_csv(precinct_dirs: List[Path]) -> pd.DataFrame:
    """
    Build a comprehensive CSV with all houses and their fitted prices.
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
        price_col = find_price_column(df_houses)
        size_col = find_size_column(df_houses)

        if not price_col or not size_col:
            continue

        try:
            prices = pd.to_numeric(df_houses[price_col], errors="coerce")
            sizes = pd.to_numeric(df_houses[size_col], errors="coerce")

            # Fit regression on finished houses only
            non_grey_mask = ~df_houses.get("is_grey_structure", pd.Series(False, index=df_houses.index))
            prices_ng = prices[non_grey_mask]
            sizes_ng = sizes[non_grey_mask]
            slope, intercept = fit_linear_regression(prices_ng, sizes_ng)

            # Build rows
            valid_idx = prices.notna() & sizes.notna()
            for idx in valid_idx[valid_idx].index:
                price = prices[idx]
                size = sizes[idx]
                price_per_sq_yd = price / size
                fitted_price = slope * size + intercept
                
                all_rows.append({
                    "precinct": precinct_name,
                    "price": round(price, 2),
                    "size_sq_yd": round(size, 2),
                    "price_per_sq_yd": round(price_per_sq_yd, 2),
                    "fitted_price": round(fitted_price, 2),
                    "is_grey_structure": 1 if df_houses.get("is_grey_structure", pd.Series(False)).get(idx, False) else 0,
                })
        except Exception as e:
            logger.warning(f"Error processing {precinct_name}: {e}")
            continue

    return pd.DataFrame(all_rows)


def main() -> None:
    """
    Main analysis workflow.

    Steps:
    1. Find all precinct folders in data/
    2. Analyze each precinct
    3. Export summary CSV with all houses and fitted prices
    4. Export lightweight JSON summary for portfolio
    5. Print summary to stdout

    Returns:
        None. Outputs written to:
        - analysis/size_vs_price_sample.csv
        - analysis/size_vs_price_summary.json
    """
    logger.info("=" * 70)
    logger.info("Zameen Size vs Price Analysis")
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

    # Build detailed CSV with all houses
    logger.info("\nBuilding detailed CSV with fitted prices...")
    df_detailed = build_detailed_csv(precinct_dirs)

    if df_detailed.empty:
        logger.error("Failed to build detailed CSV.")
        return

    # Save detailed CSV
    detailed_csv_path = ANALYSIS_DIR / "size_vs_price_sample.csv"
    detailed_csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_detailed.to_csv(detailed_csv_path, index=False)
    logger.info(f"Detailed CSV saved: {detailed_csv_path}")

    # Build lightweight JSON for portfolio frontend
    portfolio_json = []
    for _, row in df_summary.iterrows():
        portfolio_json.append({
            "precinct": row["precinct"],
            "n_houses": int(row["n_houses"]),
            "median_size_sq_yd": row["median_size_sq_yd"],
            "median_price": row["median_price"],
            "median_price_per_sq_yd": row["median_price_per_sq_yd"],
            "regression_slope": row["slope"],
            "regression_intercept": row["intercept"],
            "r_squared": row["r_squared"]
        })

    json_path = ANALYSIS_DIR / "size_vs_price_summary.json"
    with open(json_path, "w") as f:
        json.dump(portfolio_json, f, indent=2)
    logger.info(f"Portfolio JSON saved: {json_path}")

    logger.info("=" * 70)
    logger.info("Analysis Complete")
    logger.info("=" * 70)

    # Print summary table to stdout
    print("\n" + "=" * 70)
    print("Size vs Price Summary by Precinct")
    print("=" * 70)
    print(df_summary.to_string(index=False))
    print("=" * 70)
    print(f"\nDetailed data exported to: size_vs_price_sample.csv ({len(df_detailed)} rows)")
    print(f"Portfolio summary exported to: size_vs_price_summary.json")


if __name__ == "__main__":
    main()
