#!/usr/bin/env python3
"""
bottom_up_calculator.py

Produce a bottom-up construction estimate JSON using simple, transparent assumptions
and cross-check it against implied construction costs derived from listing data.

Outputs: analysis/bottom_up_calculator.json

Defaults (can be adjusted in-code):
- Plot size: 280 sq yd (10 marla)
- Floors: 2
- Coverage ratio: 0.70 (portion of plot covered per floor)
- Cost per sq ft (finished, "good" grade): 5,000–5,500 PKR
- Soft costs: 3% of build
- Contingency: 10% of build
- Utilities/connect fees (fixed): 300,000 PKR (assumption; user to validate)
- HOA/monthly: 7,000 PKR (not included in build cost; documented for context)
"""

from pathlib import Path
import logging
import pandas as pd
import json
from typing import Optional, Dict, Any, Union

# Import shared utilities
from utils import (
    get_latest_timestamped_folder,
    read_excel_sheet,
    normalize_columns,
    find_price_column,
    find_size_column,
)

# Import constants
from constants import (
    DEFAULT_PLOT_SIZE_SQ_YD,
    DEFAULT_NUM_FLOORS,
    DEFAULT_COVERAGE_RATIO,
    CONSTRUCTION_COST_PER_SQ_FT_LOW,
    CONSTRUCTION_COST_PER_SQ_FT_HIGH,
    SOFT_COST_PERCENTAGE,
    CONTINGENCY_PERCENTAGE,
    UTILITIES_CONNECTION_FIXED_COST,
    HOA_MONTHLY_MAINTENANCE,
    SQ_YD_TO_SQ_FT,
)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def median_plot_price_per_sq_yd(precinct_dir: Path) -> Optional[float]:
    """
    Calculate median plot price per square yard for a precinct.

    Args:
        precinct_dir: Path to precinct directory

    Returns:
        Median price per sq yd (float), or None if calculation fails
    """
    latest = get_latest_timestamped_folder(precinct_dir)
    if not latest:
        logger.debug(f"No timestamped folder found for {precinct_dir.name}")
        return None
    plots_file = latest / "plots.xlsx"

    df = read_excel_sheet(plots_file)
    if df is None:
        logger.debug(f"Could not read plots file: {plots_file}")
        return None

    try:
        df = normalize_columns(df)
        pcol = find_price_column(df)
        scol = find_size_column(df)
        if not pcol or not scol:
            logger.warning(f"Could not find price/size columns in {plots_file.name}")
            return None

        try:
            prices = pd.to_numeric(df[pcol], errors="coerce")
            sizes = pd.to_numeric(df[scol], errors="coerce")
            cpsq = (prices / sizes).dropna()
            if cpsq.empty:
                logger.warning(f"No valid price/size data in {plots_file.name}")
                return None
            return float(cpsq.median())
        except (ValueError, TypeError, ZeroDivisionError) as e:
            logger.warning(f"Failed to compute median plot price: {e}")
            return None
    except Exception as e:
        logger.error(f"Unexpected error computing median plot price: {e}")
        return None


def load_implied_construction_summary() -> Dict[str, Optional[float]]:
    """
    Load median implied construction costs from existing analysis CSV.

    Reads from analysis/construction_cost_summary.csv if it exists.

    Returns:
        Dict mapping precinct name to median construction cost per sq yd,
        or None if value not available
    """
    out: Dict[str, float] = {}
    csv_path = ANALYSIS_DIR / "construction_cost_summary.csv"
    if not csv_path.exists():
        return out
    try:
        df = pd.read_csv(csv_path)
        if "precinct" in df.columns and "median_cost_per_sq_yd" in df.columns:
            for _, row in df.iterrows():
                out[str(row["precinct"])]= float(row["median_cost_per_sq_yd"]) if pd.notna(row["median_cost_per_sq_yd"]) else None
    except Exception:
        pass
    return out


def main() -> None:
    """
    Main workflow for bottom-up construction cost estimation.

    Steps:
    1. Load median plot prices per precinct from data
    2. Calculate construction costs under different scenarios
    3. Compare with implied costs from listing analysis
    4. Export JSON with assumptions and scenarios

    Returns:
        None. Output written to analysis/bottom_up_calculator.json
    """
    # Defaults and assumptions
    defaults: Dict[str, Union[int, float, str]] = {
        "plot_size_sq_yd": DEFAULT_PLOT_SIZE_SQ_YD,
        "floors": DEFAULT_NUM_FLOORS,
        "coverage_ratio": DEFAULT_COVERAGE_RATIO,
        "cost_per_sq_ft_low": CONSTRUCTION_COST_PER_SQ_FT_LOW,
        "cost_per_sq_ft_high": CONSTRUCTION_COST_PER_SQ_FT_HIGH,
        "soft_cost_pct": SOFT_COST_PERCENTAGE,
        "contingency_pct": CONTINGENCY_PERCENTAGE,
        "utilities_fixed": UTILITIES_CONNECTION_FIXED_COST,
        "hoa_monthly": HOA_MONTHLY_MAINTENANCE,
        "currency": "PKR"
    }

    if not DATA_DIR.exists():
        logger.error(f"Data directory not found: {DATA_DIR}")
        return

    precinct_dirs = [d for d in DATA_DIR.iterdir() if d.is_dir()]
    if not precinct_dirs:
        logger.error("No precinct folders found in data/")
        return

    implied = load_implied_construction_summary()

    scenarios = []
    for precinct_dir in sorted(precinct_dirs):
        p_name = precinct_dir.name
        plot_ppsy = median_plot_price_per_sq_yd(precinct_dir)
        if plot_ppsy is None:
            continue

        plot_size = defaults["plot_size_sq_yd"]
        floors = defaults["floors"]
        coverage = defaults["coverage_ratio"]
        cpsf_low = defaults["cost_per_sq_ft_low"]
        cpsf_high = defaults["cost_per_sq_ft_high"]
        soft_pct = defaults["soft_cost_pct"]
        cont_pct = defaults["contingency_pct"]
        utilities_fixed = defaults["utilities_fixed"]

        plot_sq_ft = plot_size * SQ_YD_TO_SQ_FT
        covered_area_sq_ft = plot_sq_ft * coverage * floors

        build_low = covered_area_sq_ft * cpsf_low
        build_high = covered_area_sq_ft * cpsf_high

        soft_low = build_low * soft_pct
        soft_high = build_high * soft_pct

        cont_low = build_low * cont_pct
        cont_high = build_high * cont_pct

        total_build_low = build_low + soft_low + cont_low + utilities_fixed
        total_build_high = build_high + soft_high + cont_high + utilities_fixed

        land_cost = plot_size * plot_ppsy

        scenarios.append({
            "precinct": p_name,
            "median_plot_price_per_sq_yd": round(plot_ppsy, 2),
            "plot_size_sq_yd": plot_size,
            "covered_area_sq_ft": round(covered_area_sq_ft, 2),
            "build_cost_low": round(build_low, 0),
            "build_cost_high": round(build_high, 0),
            "soft_cost_low": round(soft_low, 0),
            "soft_cost_high": round(soft_high, 0),
            "contingency_low": round(cont_low, 0),
            "contingency_high": round(cont_high, 0),
            "utilities_fixed": utilities_fixed,
            "total_build_low": round(total_build_low, 0),
            "total_build_high": round(total_build_high, 0),
            "land_cost": round(land_cost, 0),
            "total_project_low": round(total_build_low + land_cost, 0),
            "total_project_high": round(total_build_high + land_cost, 0),
            "build_cost_per_sq_yd_low": round(total_build_low / plot_size, 2),
            "build_cost_per_sq_yd_high": round(total_build_high / plot_size, 2),
            "implied_construction_cost_per_sq_yd_median": implied.get(p_name)
        })

    output = {
        "defaults": defaults,
        "assumptions_notes": {
            "coverage_ratio": "Share of plot covered per floor (user to validate)",
            "cost_per_sq_ft": "Finished, good grade; excludes land; range from contractor quote",
            "soft_cost_pct": "Design/approvals/fees allowance",
            "contingency_pct": "Unforeseen costs allowance",
            "utilities_fixed": "Connection/ancillary fixed allowance (assumed)",
            "hoa_monthly": "BTK monthly maintenance context (not in build)"
        },
        "per_precinct_scenarios": scenarios,
        "currency": "PKR"
    }

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ANALYSIS_DIR / "bottom_up_calculator.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    logger.info(f"Bottom-up calculator JSON saved: {out_path}")


if __name__ == "__main__":
    main()

