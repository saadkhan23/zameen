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
from typing import Optional, Dict, Any

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_latest_timestamped_folder(precinct_dir: Path) -> Optional[Path]:
    timestamp_folders = [d for d in precinct_dir.iterdir() if d.is_dir()]
    if not timestamp_folders:
        return None
    return sorted(timestamp_folders)[-1]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [col.lower().replace(" ", "_") for col in df.columns]
    return df


def find_price_column(df: pd.DataFrame) -> Optional[str]:
    normalized_cols = {col.lower(): col for col in df.columns}
    for pattern in ("price_pkr", "price", "asking_price", "cost"):
        if pattern in normalized_cols:
            return normalized_cols[pattern]
    for lower_col, actual_col in normalized_cols.items():
        if "price" in lower_col or "cost" in lower_col:
            return actual_col
    return None


def find_size_column(df: pd.DataFrame) -> Optional[str]:
    normalized_cols = {col.lower(): col for col in df.columns}
    for pattern in ("area_sqyd", "size_sq_yd", "size", "area_sqm", "area"):
        if pattern in normalized_cols:
            return normalized_cols[pattern]
    for lower_col, actual_col in normalized_cols.items():
        if "size" in lower_col or "area" in lower_col or "sq" in lower_col:
            return actual_col
    return None


def median_plot_price_per_sq_yd(precinct_dir: Path) -> Optional[float]:
    latest = get_latest_timestamped_folder(precinct_dir)
    if not latest:
        return None
    plots_file = latest / "plots.xlsx"
    if not plots_file.exists():
        return None
    try:
        x = pd.ExcelFile(plots_file)
        sheet = "Properties" if "Properties" in x.sheet_names else x.sheet_names[0]
        df = pd.read_excel(plots_file, sheet_name=sheet)
        df = normalize_columns(df)
        pcol = find_price_column(df)
        scol = find_size_column(df)
        if not pcol or not scol:
            return None
        prices = pd.to_numeric(df[pcol], errors="coerce")
        sizes = pd.to_numeric(df[scol], errors="coerce")
        cpsq = (prices / sizes).dropna()
        if cpsq.empty:
            return None
        return float(cpsq.median())
    except Exception:
        return None


def load_implied_construction_summary() -> Dict[str, float]:
    """Return median implied construction cost per sq yd per precinct from existing analysis CSV."""
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
    # Defaults and assumptions
    defaults = {
        "plot_size_sq_yd": 280,
        "floors": 2,
        "coverage_ratio": 0.70,
        "cost_per_sq_ft_low": 5000,
        "cost_per_sq_ft_high": 5500,
        "soft_cost_pct": 0.03,
        "contingency_pct": 0.10,
        "utilities_fixed": 300000,
        "hoa_monthly": 7000,
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

        plot_sq_ft = plot_size * 9
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

