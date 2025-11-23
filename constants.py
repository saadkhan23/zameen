#!/usr/bin/env python3
"""
constants.py

Global constants for the Zameen real estate analysis project.

This module centralizes all hardcoded configuration values, thresholds,
and magic numbers used throughout the project. Keeping constants in one
place makes it easy to adjust behavior without code diving.

Categories:
- ANALYSIS THRESHOLDS: Statistical thresholds for data analysis
- CONSTRUCTION ESTIMATION: Parameters for bottom-up cost estimation
- SCRAPING CONFIGURATION: Web scraping timing and delays
- DATA VALIDATION: Acceptable ranges for property data
- LOGGING CONFIGURATION: Logging levels and formats
"""

# ============================================================================
# ANALYSIS THRESHOLDS
# ============================================================================

# Bargain Detection (bargains_analysis.py)
# Z-score threshold for identifying bargain properties
# Properties with z_score < this value AND price < median are considered bargains
BARGAIN_Z_SCORE_THRESHOLD: float = -0.8

# Quantile levels for statistical summaries
QUANTILE_P10: float = 0.10
QUANTILE_P25: float = 0.25
QUANTILE_P50: float = 0.50  # Median
QUANTILE_P75: float = 0.75
QUANTILE_P90: float = 0.90

# ============================================================================
# CONSTRUCTION COST ESTIMATION
# ============================================================================

# Default assumptions for bottom-up construction cost calculation
# (bottom_up_calculator.py)

# Plot size in square yards (10 marla = 280 sq yd)
DEFAULT_PLOT_SIZE_SQ_YD: int = 280

# Number of floors in standard estimation
DEFAULT_NUM_FLOORS: int = 2

# Coverage ratio: portion of plot covered per floor
# Range: 0.60 (60% coverage) to 0.80 (80% coverage)
# 0.70 is typical for mid-range residential construction
DEFAULT_COVERAGE_RATIO: float = 0.70

# Construction costs per square foot (finished, good grade)
# These are market rates for mid-range residential construction in Pakistan
CONSTRUCTION_COST_PER_SQ_FT_LOW: int = 5000    # Budget/economy grade (PKR)
CONSTRUCTION_COST_PER_SQ_FT_HIGH: int = 5500   # Mid-range grade (PKR)

# Cost allocation as percentage of build cost
SOFT_COST_PERCENTAGE: float = 0.03    # Design, approvals, fees, etc.
CONTINGENCY_PERCENTAGE: float = 0.10  # Unforeseen costs allowance

# Fixed costs (not affected by plot size)
UTILITIES_CONNECTION_FIXED_COST: int = 300000  # Connection fees, ancillary (PKR)

# Property maintenance (not included in build cost, for reference)
HOA_MONTHLY_MAINTENANCE: int = 7000  # Monthly HOA charge (PKR)

# Conversion factors
SQ_YD_TO_SQ_FT: int = 9  # 1 sq yd = 9 sq ft

# ============================================================================
# SCRAPING CONFIGURATION
# ============================================================================

# Web scraping delays (zameen_json_scraper.py)
# Random delays between requests to appear human-like and respect server load

# Initial page request delays (seconds)
SCRAPE_INITIAL_DELAY_MIN: int = 2
SCRAPE_INITIAL_DELAY_MAX: int = 5

# Detail page request delays (longer to be more respectful)
SCRAPE_DETAIL_DELAY_MIN: int = 3
SCRAPE_DETAIL_DELAY_MAX: int = 6

# Page load timeout (milliseconds)
SCRAPE_PAGE_LOAD_TIMEOUT_MS: int = 30000

# Browser configuration
SCRAPE_BROWSER_HEADLESS: bool = True
SCRAPE_BROWSER_WAIT_UNTIL: str = "networkidle"  # Wait for network to be idle

# ============================================================================
# DATA VALIDATION RANGES
# ============================================================================

# Acceptable ranges for property data (for outlier detection)
# These help identify potentially invalid data

# Price range (PKR)
MIN_PROPERTY_PRICE: int = 1_000_000        # 1M PKR minimum
MAX_PROPERTY_PRICE: int = 10_000_000_000   # 10B PKR maximum

# Size range (square yards)
MIN_PROPERTY_SIZE_SQ_YD: float = 10      # Minimum 10 sq yd
MAX_PROPERTY_SIZE_SQ_YD: float = 10_000  # Maximum 10,000 sq yd

# Price per square yard range (PKR/sq yd)
MIN_PRICE_PER_SQ_YD: int = 1_000       # Minimum 1,000 PKR/sq yd
MAX_PRICE_PER_SQ_YD: int = 1_000_000   # Maximum 1M PKR/sq yd

# ============================================================================
# GREY STRUCTURE DETECTION
# ============================================================================

# Keywords used to identify grey/unfinished structures
GREY_STRUCTURE_KEYWORDS: list = [
    "grey structure",
    "gray structure",
    "grey-work",
    "greywork",
    "core & shell",
    "core and shell",
    "shell only",
    "structure only",
    "semi-finished",
    "semi finished",
    "unfinished",
    "without finishing",
]

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Log format string
LOG_FORMAT: str = "[%(levelname)s] %(message)s"

# Default logging level
LOG_LEVEL: str = "INFO"

# ============================================================================
# CURRENCY AND UNITS
# ============================================================================

CURRENCY: str = "PKR"  # Pakistani Rupee
UNIT_AREA: str = "sq yd"  # Square yard for property area
UNIT_COST: str = "PKR/sq yd"  # Price per square yard

# ============================================================================
# FILE AND DIRECTORY NAMING
# ============================================================================

# Timestamp format for timestamped output directories
TIMESTAMP_FORMAT: str = "%Y-%m-%d_%H%M%S"

# Default sheet names in Excel files
DEFAULT_EXCEL_SHEET_NAME: str = "Properties"

# ============================================================================
# API ENDPOINTS (For future use if integrating with Zameen API)
# ============================================================================

ZAMEEN_BASE_URL: str = "https://www.zameen.com"
ZAMEEN_API_BASE_URL: str = "https://www.zameen.com/api"  # If available in future
