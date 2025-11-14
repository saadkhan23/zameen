#!/usr/bin/env python3
"""
construction_cost_analysis.py

Deep-dive analysis of construction costs across Bahria Town precincts.

For each precinct:
1. Find latest timestamped run in data/<precinct>/
2. Load houses.xlsx and plots.xlsx
3. Estimate implied construction cost per sq yd:
   house_price_per_sq_yd - median_plot_price_per_sq_yd
4. Summarize by percentiles (p25, median, p75)
5. Export to analysis/construction_cost_summary.csv

Usage:
    python3 analysis/construction_cost_analysis.py          # Normal mode
    python3 analysis/construction_cost_analysis.py --verbose # Detailed calculations
"""

from pathlib import Path
import logging
import pandas as pd
from typing import Dict, List, Tuple, Optional
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
    # Find candidate columns post-normalization
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


def safe_numeric(val) -> Optional[float]:
    """
    Safely convert value to float. Returns None if conversion fails.
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def analyze_precinct(precinct_dir: Path) -> Optional[Dict]:
    """
    Analyze a single precinct: compute construction costs, summarize by percentiles.

    Returns a dict with:
    {
        "precinct": str,
        "median_cost_per_sq_yd": float or None,
        "p25_cost_per_sq_yd": float or None,
        "p75_cost_per_sq_yd": float or None,
        "n_properties": int
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

    # Read plots and houses
    plots_file = latest_run / "plots.xlsx"
    houses_file = latest_run / "houses.xlsx"

    df_plots = read_excel_sheet(plots_file)
    df_houses = read_excel_sheet(houses_file)

    # Check we have houses; plots are optional (but needed for construction cost)
    if df_houses is None:
        logger.warning(f"  {precinct_name}: No houses.xlsx found. Skipping.")
        return None

    # Normalize columns and add grey flag
    df_houses = normalize_columns(df_houses)
    df_houses = flag_grey_structure(df_houses)
    grey_count = int(df_houses["is_grey_structure"].sum()) if "is_grey_structure" in df_houses.columns else 0
    # Exclude grey structures for construction cost analysis
    if "is_grey_structure" in df_houses.columns:
        df_houses = df_houses[~df_houses["is_grey_structure"]].copy()
    if df_plots is not None:
        df_plots = normalize_columns(df_plots)

    # Compute median plot price per sq yd (representative land cost)
    median_plot_price_per_sq_yd = None
    if df_plots is not None and len(df_plots) > 0:
        try:
            # Intelligently find price and size columns
            price_col = find_price_column(df_plots)
            size_col = find_size_column(df_plots)

            if price_col and size_col and price_col in df_plots.columns and size_col in df_plots.columns:
                # Convert to numeric and compute cost per sq yd
                plot_prices = pd.to_numeric(df_plots[price_col], errors="coerce")
                plot_sizes = pd.to_numeric(df_plots[size_col], errors="coerce")

                plot_cost_per_sq_yd = plot_prices / plot_sizes
                plot_cost_per_sq_yd = plot_cost_per_sq_yd.dropna()

                if len(plot_cost_per_sq_yd) > 0:
                    median_plot_price_per_sq_yd = plot_cost_per_sq_yd.median()
                    logger.info(f"  Median plot price per sq yd: {median_plot_price_per_sq_yd:,.0f} PKR")

                    if VERBOSE:
                        logger.info(f"    [Verbose] Plot stats (n={len(plot_cost_per_sq_yd)})")
                        logger.info(f"      Min: {plot_cost_per_sq_yd.min():,.0f} PKR/sq yd")
                        logger.info(f"      p25: {plot_cost_per_sq_yd.quantile(0.25):,.0f} PKR/sq yd")
                        logger.info(f"      p50: {plot_cost_per_sq_yd.median():,.0f} PKR/sq yd")
                        logger.info(f"      p75: {plot_cost_per_sq_yd.quantile(0.75):,.0f} PKR/sq yd")
                        logger.info(f"      Max: {plot_cost_per_sq_yd.max():,.0f} PKR/sq yd")
            else:
                logger.warning(f"  Could not find price/size columns in plots. Available: {df_plots.columns.tolist()}")
        except Exception as e:
            logger.warning(f"  Failed to compute median plot price: {e}")

    # If no plots data, we can't estimate construction cost
    if median_plot_price_per_sq_yd is None:
        logger.warning(f"  {precinct_name}: No plot price per sq yd available. Skipping construction cost analysis.")
        return None

    # Compute construction cost for each house
    construction_costs = []
    try:
        # Intelligently find price and size columns in houses
        price_col = find_price_column(df_houses)
        size_col = find_size_column(df_houses)

        if price_col and size_col and price_col in df_houses.columns and size_col in df_houses.columns:
            house_prices = pd.to_numeric(df_houses[price_col], errors="coerce")
            house_sizes = pd.to_numeric(df_houses[size_col], errors="coerce")

            house_cost_per_sq_yd = house_prices / house_sizes
            house_cost_per_sq_yd = house_cost_per_sq_yd.dropna()

            # Implied construction cost = house price per sq yd - median plot price per sq yd
            construction_costs = (house_cost_per_sq_yd - median_plot_price_per_sq_yd).dropna()
        else:
            logger.warning(f"  Could not find price/size columns in houses. Available: {df_houses.columns.tolist()}")

    except Exception as e:
        logger.error(f"  Failed to compute construction costs: {e}")
        return None

    if len(construction_costs) == 0:
        logger.warning(f"  {precinct_name}: No valid construction costs computed. Skipping.")
        return None

    # Compute percentiles
    median_cost = construction_costs.median()
    p25_cost = construction_costs.quantile(0.25)
    p75_cost = construction_costs.quantile(0.75)
    n_properties = len(construction_costs)

    logger.info(f"  {precinct_name} Summary:")
    logger.info(f"    Median construction cost: {median_cost:,.0f} PKR/sq yd")
    logger.info(f"    25th percentile: {p25_cost:,.0f} PKR/sq yd")
    logger.info(f"    75th percentile: {p75_cost:,.0f} PKR/sq yd")
    logger.info(f"    Properties analyzed: {n_properties}")

    if VERBOSE:
        logger.info(f"    [Verbose] House construction cost stats:")
        logger.info(f"      Min: {construction_costs.min():,.0f} PKR/sq yd")
        logger.info(f"      p10: {construction_costs.quantile(0.10):,.0f} PKR/sq yd")
        logger.info(f"      p25: {construction_costs.quantile(0.25):,.0f} PKR/sq yd")
        logger.info(f"      p50: {construction_costs.median():,.0f} PKR/sq yd")
        logger.info(f"      p75: {construction_costs.quantile(0.75):,.0f} PKR/sq yd")
        logger.info(f"      p90: {construction_costs.quantile(0.90):,.0f} PKR/sq yd")
        logger.info(f"      Max: {construction_costs.max():,.0f} PKR/sq yd")
        logger.info(f"      Std Dev: {construction_costs.std():,.0f} PKR/sq yd")
        logger.info(f"    [Verbose] Sample calculations (first 5 houses):")

        # Show first 5 house calculations
        house_prices = pd.to_numeric(df_houses[price_col], errors="coerce")
        house_sizes = pd.to_numeric(df_houses[size_col], errors="coerce")
        house_cost_per_sq_yd = house_prices / house_sizes

        for idx in range(min(5, len(house_cost_per_sq_yd))):
            h_price = house_prices.iloc[idx]
            h_size = house_sizes.iloc[idx]
            h_cost_sqyd = house_cost_per_sq_yd.iloc[idx]
            impl_cost = h_cost_sqyd - median_plot_price_per_sq_yd
            logger.info(f"      House {idx+1}: {h_price:,.0f} PKR / {h_size:.0f} sq yd = {h_cost_sqyd:,.0f} - {median_plot_price_per_sq_yd:,.0f} = {impl_cost:,.0f} PKR/sq yd")

    return {
        "precinct": precinct_name,
        "median_cost_per_sq_yd": round(median_cost, 2),
        "p25_cost_per_sq_yd": round(p25_cost, 2),
        "p75_cost_per_sq_yd": round(p75_cost, 2),
        "n_properties": n_properties,
        "n_grey_structures": grey_count
    }


def main() -> None:
    """
    Main analysis workflow:
    1. Find all precinct folders in data/
    2. Analyze each precinct
    3. Export summary CSV
    4. Print summary to stdout
    """
    logger.info("=" * 70)
    logger.info("Zameen Construction Cost Analysis")
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

    # Save to CSV
    output_path = ANALYSIS_DIR / "construction_cost_summary.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_summary.to_csv(output_path, index=False)

    logger.info("=" * 70)
    logger.info("Analysis Complete")
    logger.info("=" * 70)
    logger.info(f"\nSummary saved to: {output_path}\n")

    # Print summary table to stdout
    print("\n" + "=" * 70)
    print("Construction Cost Summary by Precinct")
    print("=" * 70)
    print(df_summary.to_string(index=False))
    print("=" * 70)


if __name__ == "__main__":
    main()
