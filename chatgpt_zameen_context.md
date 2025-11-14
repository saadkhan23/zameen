# Zameen Real Estate Analysis Project - AI Context Document

## 1. What the Project Does

**Zameen Real Estate Market Analysis** is a data engineering project that scrapes property listings from Zameen.com (Pakistan's largest real estate marketplace), analyzes market patterns, and identifies investment opportunities through statistical analysis.

The pipeline collects property data (houses and plots), calculates construction costs by subtracting land values, identifies underpriced properties, and exports insights to Excel for investment screening.

**Key Question:** Where can investors find underpriced properties in Pakistan's luxury real estate market?

**Key Finding:** Construction costs are consistent across premium precincts (75-85k PKR per sq yard), but property prices vary by size and buyer segmentation, not construction economics.

**Current Focus:** Bahria Town Karachi (precincts 1, 5, 6, 8)

---

## Audience & Scope (Stable)

- **Primary audience**: Overseas Pakistanis new to Karachi/BTK; some local readers.
- **Use case focus**: Buy-to-live and buy-to-invest. Rental analysis deferred (see Backlog).
- **Geographic scope (current)**: Bahria Town Karachi, starting with Precincts 5, 6, 8.
- **Geographic scope (future)**: Expand to additional BTK precincts, then other Karachi areas.

## Assumptions & Inputs (Stable)

- **HOA/maintenance fees**: Assume PKR 7,000/month (BTK range reportedly 6k–8k; 6k private builds, 8k Bahria-built).
- **Construction cost (finished, “good” grade)**: PKR 5,000–5,500 per sq ft (per-floor rate; typical houses are 2 floors).
- **Covered area model** (for bottom-up estimates):
  - Plot in sq yd × 9 = plot sq ft
  - Covered sq ft = plot sq ft × coverage_ratio × floors
  - Defaults to document later; expose as parameters in calculator.


## 2. Architecture

### Overall Pipeline
```
Zameen.com (JavaScript-rendered marketplace)
  ↓
  ├─ Property listings (houses and plots)
  ├─ Price, size, location data
  └─ Pagination (8 pages per location)
  ↓
Playwright Browser Automation
  ├─ Launch headless Chromium
  ├─ Navigate to location URL
  ├─ Wait for JavaScript to render
  ├─ Extract JSON data from page
  └─ Rate limiting (2-5s between pages)
  ↓
JSON Parsing & Data Extraction
  ├─ Extract "hits" array from page JavaScript
  ├─ Parse property JSON objects
  ├─ Collect: price, size, location, condition
  └─ Handle pagination automatically
  ↓
Data Transformation (Python/Pandas)
  ├─ Separate houses and plots
  ├─ Clean price and size columns
  ├─ Calculate cost per square yard
  ├─ Identify bargains (>10% below median)
  └─ Create summary statistics
  ↓
Excel Export (openpyxl/xlsxwriter)
  ├─ Summary sheet (key statistics)
  ├─ Properties sheet (all listings with analysis)
  ├─ Color formatting (green for bargains, red for outliers)
  └─ File: data/[location]/[timestamp]/houses.xlsx
  ↓
Data Storage (Timestamped Folders)
  └─ data/bahria_town_precinct_5/2025-11-11_124325/
      ├─ houses.xlsx
      ├─ plots.xlsx
      └─ README.txt
```

### Directory Structure
```
zameen/
├── scrape.py                         # Main entry point (configurable)
├── zameen_json_scraper.py            # Core scraping logic (17 KB)
├── analyze_folder.py                 # Analyze existing data (11.5 KB)
│
├── constructionAnalysis/
│   └── construction_cost_analysis.py # Compare multiple precincts
│
├── data/                             # Scraped data organized by location/date
│   ├── bahria_town_precinct_1/
│   │   └── 2025-11-11_124243/
│   │       ├── houses.xlsx
│   │       └── plots.xlsx
│   ├── bahria_town_precinct_5/       # Multiple timestamped folders
│   │   ├── 2025-11-11_124325/
│   │   │   ├── houses.xlsx
│   │   │   └── plots.xlsx
│   │   ├── 2025-11-10_170200/       # Earlier run
│   │   └── ... (historical data)
│   ├── bahria_town_precinct_6/
│   └── bahria_town_precinct_8/
│
├── gpt4.1_construction_estimate/
│   ├── analysis_houses.xlsx          # GPT-4 analysis
│   └── analysis_plots.xlsx           # GPT-4 analysis
│
├── archive/                          # Earlier versions of code
│   ├── README.md
│   ├── GETTING_STARTED.md
│   ├── BUILD_VS_BUY_GUIDE.md
│   ├── PROJECT_SUMMARY.md
│   ├── scrape_precinct_8.py
│   ├── zameen_scraper_playwright.py  # Earlier version
│   ├── zameen_scraper.py             # Original HTTP-based (failed)
│   └── analyze_*.py                  # Earlier analysis scripts
│
├── requirements.txt                  # Python dependencies
├── .gitignore                        # Git patterns (excludes data/ archive/)
├── .git/                             # Git repository (public on GitHub)
│
├── README.md                         # Main overview (8.5 KB)
├── QUICK_START.md                    # Quick setup guide (5 KB)
├── LOCATIONS.md                      # Available locations reference (4.7 KB)
├── METHODOLOGY.md                    # Technical approach (16.7 KB)
├── PORTFOLIO_CHECKLIST.md            # Investment screening checklist (10.8 KB)
│
└── venv/                             # Python virtual environment
    ├── bin/
    └── lib/python3.13/site-packages/
```

### Scraper Architecture (zameen_json_scraper.py)

#### Class Design
```python
class ZameenJSONScraper:
    def __init__(self, location_id, location_name, headless=True):
        self.location_id = location_id
        self.location_name = location_name
        self.headless = headless
        self.browser = None
        self.data = {'houses': [], 'plots': []}
    
    def scrape_location(self, property_type, max_pages=8):
        # Main scraping logic
        
    def _smart_delay(self, min_seconds=2, max_seconds=5):
        # Random delay between requests
        
    def _extract_json_from_page(self, page_content):
        # Parse JSON from page JavaScript
        
    def _clean_data(self):
        # Data validation and cleaning
        
    def export_to_excel(self, output_path):
        # Create Excel files with formatting
```

#### Key Methods
1. **scrape_location()** - Navigate to URL, paginate, extract data
2. **_extract_json_from_page()** - Parse JSON using regex pattern
3. **_smart_delay()** - Random 2-5s delays (human-like)
4. **_clean_data()** - Validate prices, sizes, remove duplicates
5. **export_to_excel()** - Create formatted Excel files

#### Web Scraping Evolution
```
Iteration 1: HTTP Requests (❌ Failed)
  Problem: Zameen uses Cloudflare DDoS protection
  Result: 503 errors when non-browser requests detected

Iteration 2: Playwright (✅ Works, but fragile)
  Advantage: Real browser, passes Cloudflare
  Problem: HTML structure changes frequently, CSS selectors break

Iteration 3: Playwright + JSON Extraction (✅ Current, robust)
  Method: Extract JSON directly from page using regex
  Advantage: Schema is stable, immune to HTML changes
  Pattern: r'"hits":\s*\[(.*?)\],\"hitsPerPage\"'
  Result: Maintainable, resilient to website changes
```

### Configuration System (scrape.py)
```python
# User-editable configuration
LOCATION_NAME = 'Bahria_Town_Karachi_Bahria_Town___Precinct_5'
LOCATION_ID = '10013'
LOCATION_DISPLAY = 'bahria_town_precinct_5'
MAX_PAGES = 8
SCRAPE_HOUSES = True
SCRAPE_PLOTS = True

# Quick presets (uncommented to use)
# LOCATION_NAME = 'Bahria_Town_Karachi_Bahria_Town___Precinct_6'
# LOCATION_ID = '10014'
# LOCATION_DISPLAY = 'bahria_town_precinct_6'
```

### Analysis Pipeline (analyze_folder.py)
```python
1. Load XLSX files from timestamped folder
2. Parse property data into DataFrame
3. Calculate statistics:
   - Median price
   - Mean price per sq yard
   - Outliers (>2 std dev from mean)
   - Bargains (>10% below median)
4. Generate summary report
5. Export findings
```

### Data Flow
```
User edits scrape.py
  ↓
Runs: python3 scrape.py
  ↓
ZameenJSONScraper instance created
  ↓
  ├─ Launch Playwright browser
  ├─ Navigate to Zameen location
  ├─ Loop through pages (max 8)
  │   ├─ Wait for content to load (networkidle)
  │   ├─ Extract page content
  │   ├─ Parse JSON data
  │   ├─ Append to data array
  │   └─ Random delay (2-5s)
  ├─ Close browser
  ├─ Clean data (validation)
  └─ Export to Excel
  ↓
Output: data/[location]/[timestamp]/houses.xlsx
         data/[location]/[timestamp]/plots.xlsx
  ↓
User runs analyze_folder.py
  ↓
Loads Excel files
  ↓
Generates summary statistics
  ↓
Identifies bargains and outliers
```

---

## 3. Known Risks / Fragilities

- **JSON schema dependency**: Scraper relies on Zameen's `"hits"` array pattern in page JavaScript. Any change in that schema will break `_extract_json_from_page()`.
- **Anti-bot detection**: Depends on Playwright and headless Chromium; Zameen's anti-bot or Cloudflare configuration could block scraping.
- **Hardcoded location IDs**: Location IDs (e.g., '10013' for Precinct 5) are hardcoded. If Zameen changes internal IDs, those must be updated manually.
- **Construction cost estimation**: Method assumes `house_price − plot_price ≈ construction_cost`, which may not hold across all cases (different build qualities, land prep, etc.).
- **Terms of service**: Legal tolerance for scraping could change. Continued use depends on Zameen.com's policies and terms of service.
- **Data staleness**: Some listings may be sold (outdated in the scraped data). Manual filtering recommended before investment decisions.

---

## 4. Tech Stack

### Language & Environment
- **Python 3.13** - Primary language
- **Virtual Environment:** `venv/` (isolated dependencies)
- **Jupyter:** Not used (CLI scripts only)

### Web Scraping
- **Playwright 1.40+** - Browser automation
  - Headless Chromium browser
  - JavaScript rendering (waits for network idle)
  - Cookie/session management
  - User-agent configuration
  
- **requests 2.31+** - HTTP client (fallback)
  
- **beautifulsoup4 4.12+** - HTML/XML parsing
  - Parse comment nodes
  - Extract specific elements if needed
  
- **lxml 4.9+** - Fast C-based parser

### Data Processing
- **pandas 2.0+** - DataFrames and analysis
  - Read XLSX files
  - Filter, group, aggregate
  - Calculate statistics
  - Export to CSV/Excel
  
- **openpyxl 3.1+** - Read/write Excel files
  - Load existing Excel
  - Modify formatting
  - Cell styling (colors, fonts)
  
- **xlsxwriter 3.1+** - Create Excel files from scratch
  - Format summary sheets
  - Add charts (future)
  - Color coding (green for bargains, red for outliers)

### Data Visualization (Future)
- **matplotlib 3.7+** - Static plots
- **seaborn 0.12+** - Enhanced plots
- **plotly** - Interactive charts (if building dashboard)

### Version Control
- **git** - Local repository
- **GitHub** - Public repo (https://github.com/saadkhan23/zameen.git)

### Utilities
- **random** - Random delays for anti-detection
- **time** - Sleep between requests
- **json** - Parse JSON from page
- **datetime** - Timestamp folders
- **regex (re)** - Extract JSON from page content
- **os, pathlib** - File system operations

---

## 5. Data Status

### Current Data Structure
- **Location:** `data/[location_name]/[timestamp]/`
- **Timestamp Format:** `2025-11-11_124325` (YYYY-MM-DD_HHMMSS)
- **Files:** `houses.xlsx`, `plots.xlsx`

### Data Locations Scraped
```
Precinct 1:
  - 1 dated folder (2025-11-11_124243)
  
Precinct 5 (Primary):
  - 3+ dated folders (tracking price changes over time)
  
Precinct 6:
  - 2+ dated folders
  
Precinct 8:
  - 2+ dated folders
```

### Excel File Structure

#### Summary Sheet
```
Total Properties: 62
Median Price: PKR 50,000,000
Median Price per Sq Yd: PKR 100,000
Average Price per Sq Yd: PKR 101,234
Min Price: PKR 35,000,000
Max Price: PKR 85,000,000
Std Dev: PKR 8,500,000

Bargains (>10% below median): 8 properties
```

#### Properties Sheet
```
Columns:
  - Price (PKR)
  - Size (Sq Yd)
  - Cost per Sq Yd (PKR/yd²)
  - Distance from Median (PKR)
  - Percentage Variance (%)
  - Address/Location
  - Condition
  
Example Row:
  Price: 42,300,000
  Size: 450
  Cost/Yd: 94,000
  Variance: -7,700,000
  %: -15.4%
```

### Data Fields Captured
- **Price** - Property asking price (PKR)
- **Size** - Property size in square yards
- **Type** - House or Plot
- **Location** - Precinct and block (if available)
- **Condition** - New, under construction, etc.
- **Features** - Bedrooms, bathrooms (varies)

### Known Data Issues
- **Incomplete Features:** Not all properties have bedroom/bathroom counts
- **Stale Data:** Some listings may be sold (old data)
- **Price Format:** Some entries may have typos (validation needed)
- **Size Variations:** Some sizes may be approximate

### Data Quality Measures
- **Deduplication:** Remove duplicate listings by address
- **Validation:** Check price and size are numeric
- **Outlier Detection:** Flag properties >2 std dev from mean
- **Missing Data:** Handle null values gracefully

### Raw Data Exports for AI Analysis

**Location:** `chatgpt_data/` folder

**Files Created (12 total):**
- `precinct_5_houses.csv` / `.json` (8 summary metrics)
- `precinct_5_plots.csv` / `.json` (8 summary metrics)
- `precinct_6_houses.csv` / `.json` (8 summary metrics)
- `precinct_6_plots.csv` / `.json` (8 summary metrics)
- `precinct_8_houses.csv` / `.json` (8 summary metrics)
- `precinct_8_plots.csv` / `.json` (8 summary metrics)

**Content:** Each file contains key statistics (total properties, median/average price, price per sq yd, min/max, scraped date)

**Purpose:** Share raw analysis data with ChatGPT/Claude for additional insights and narrative suggestions

---

## 6. Pending Tasks / Backlog

### High Priority (Core Functionality)
- [ ] Create historical time-series visualization (price trends)
- [ ] Add properties with price change detection across scrapes
- [ ] Implement construction cost calculation export
- [ ] Build comparison dashboard across precincts
- [ ] Document location IDs for all areas (expand LOCATIONS.md)

### Medium Priority (Analysis & Insights)
- [ ] Add market trend analysis (is market heating up?)
- [ ] Implement ROI estimation (for investors)
- [ ] Create bargain alert system (email notifications)
- [ ] Build property recommendation engine
- [ ] Add neighborhood comparison (safety, amenities)

### Feature Expansion
- [ ] Geographic expansion (other Karachi developments, other cities)
- [ ] Add rental yield analysis
- [ ] Integrate with property listing APIs (for automation)
- [ ] Build REST API for programmatic access
- [ ] Create web dashboard (Streamlit or Flask)

### Automation & Deployment
- [ ] Schedule monthly scrapes (cron job or GitHub Actions)
- [ ] Automated email reports
- [ ] Database backend (SQLite or PostgreSQL)
- [ ] Cost estimation refinement (actual construction data)
- [ ] Outlier investigation system

### Documentation
- [ ] Complete investment screening checklist
- [ ] Add case studies (example: "Should I buy this property?")
- [ ] Build FAQ for common questions
- [ ] Create video walkthrough
- [ ] Document decision tree for property selection

---

## 7. Design Principles

### Web Scraping Ethics
- **Transparency:** Headless browser identifies as automated (in User-Agent)
- **Respect:** Random 2-5 second delays between requests (human-like)
- **Moderation:** 8 pages per location (~150 properties), not mass harvesting
- **Legal:** Public data from public website, no authentication bypass
- **Responsible:** Includes rate limiting, respects server load
- **Terms:** Complies with Zameen.com ToS (review before use)

### Code Organization
- **Entry Point:** `scrape.py` (user-editable configuration)
- **Core Logic:** `zameen_json_scraper.py` (ZameenJSONScraper class)
- **Analysis:** `analyze_folder.py` (standalone analysis tool)
- **Comparison:** `constructionAnalysis/` (cross-location analysis)
- **Naming:** snake_case, descriptive names, clear intent

### Data Design
- **Time-Series:** Timestamped folders enable tracking over months/years
- **Separation:** Houses and plots in separate Excel files (different analysis)
- **Normalization:** Cost per square yard for fair comparison
- **Outlier Handling:** Flag but don't remove (for investigation)

### Analysis Approach
- **Statistical:** Use median, not average (resistant to outliers)
- **Normalized:** Always divide by size (apples-to-apples comparison)
- **Contextual:** Show full distribution (min, max, percentiles)
- **Visual:** Charts in Excel for quick insight
- **Transparent:** Document methodology in README

### Investment Principles
- **Risk Identification:** Flag outliers and anomalies
- **Bargain Detection:** Properties >10% below median
- **Market Segmentation:** Understand price differences (size vs location)
- **Due Diligence:** Investors verify independently
- **No Guarantees:** Data is historical, not predictive

---

## 8. Current Findings Snapshot (as of 2025-11-11)

These findings are based on the data and analysis methods as of 2025-11-11. They may change as more data is scraped or methodology is refined.

- **Construction costs** in Bahria Town precincts range approximately **75–85k PKR per sq yard** across all precincts studied.
- **Price differences** are driven more by **property size and buyer segmentation** than by construction economics alone.
- **Market segmentation**: Precinct 5 targets larger properties (premium segment), while Precincts 6 & 8 target mid-range buyers.
- **Bargain opportunities**: Properties **10-15% below the median normalized price** may represent relatively good value, though further due diligence is needed.
- **Normalization method** (cost per square yard) proves more reliable than raw price comparisons for identifying outliers and bargains.
- **Outliers flagged** for investigation; some properties appear significantly below market norms.

---

## 9. Questions for AI Helper

### Expansion & Growth
1. **Geographic Expansion Strategy?**
   - Should I scrape other Karachi developments (DHA, Clifton)?
   - Expand to other Pakistani cities (Lahore, Islamabad)?
   - What's the priority order?

2. **Market Monitoring Timeline?**
   - How often to re-scrape for price tracking?
   - Monthly, quarterly, or as-needed?
   - How many months of history before analyzing trends?

3. **Investment Screening?**
   - What metrics matter most (ROI, price/size, location safety)?
   - Should I build a scoring system?
   - How to weight different factors?

### Technical Direction
4. **Database vs CSV/Excel?**
   - Currently: timestamped folders with XLSX
   - Should I move to SQLite for easier querying?
   - When would that be necessary?

5. **Web Dashboard Priority?**
   - Build Streamlit app for exploration?
   - Or remain CLI/Excel-based?
   - Who is the primary user?

6. **Real-time Updates?**
   - Should I continuously monitor for new listings?
   - Or periodic batch scrapes?
   - What's the business value of real-time?

### Data Enhancement
7. **Complementary Data Sources?**
   - Add crime statistics by area?
   - Schools, hospitals, shopping nearby?
   - Traffic/commute data?
   - Weather/climate patterns?

8. **Construction Cost Validation?**
   - Current method: house price - plot price
   - Should I verify with actual builder quotes?
   - Compare to market labor + material costs?

9. **Investor Profiles?**
   - Build profiles for different investor types?
   - First-time buyer vs portfolio investor?
   - Long-term hold vs flip?

### Business & Monetization
10. **Use Cases Beyond Personal?**
    - Subscription alerts service?
    - Real estate agency partnership?
    - Investment fund formation?
    - Market research reports?

11. **Legal & Compliance?**
    - Should I get explicit permission from Zameen.com?
    - Privacy concerns (listing owners)?
    - Liability for investment recommendations?

---

## Backlog / Next Steps (Actionable)

- Grey-structure filtering: detect titles/descriptions with keywords ("grey/gray structure", "shell", "semi-finished", "unfinished"); add `is_grey_structure` flag; exclude from pricing medians and implied construction cost; report counts per precinct.
- Precinct metrics: publish bargain rate, median price/sq yd, dispersion (p25–p75), size→price discipline (R²), and grey-structure share.
- Bottom-up build calculator: parameterize `coverage_ratio`, `floors` (default 2), `cost_per_sq_ft` (5k–5.5k), `soft_cost_pct`, `contingency_pct`, and utilities/connect fees; export JSON for portfolio UI scenarios (e.g., 280 sq yd example).
- Implied vs bottom-up cross-check: compare implied construction cost to calculator outputs; quantify gaps by precinct and finishing grade assumptions.
- Portfolio data extension: include new metrics in `/data/zameen/*.json` for front-end (grey share, size bands, cross-check deltas, worked examples).
- Scope expansion: after P5/P6/P8 write-up, add more BTK precincts; later consider other Karachi geographies (DHA, Clifton) — keep BTK focus for current release.
- Rental analysis (future): integrate Zameen rent listings for yields; add rent-to-price and gross yield summaries (deferred by design).


## Setup & Development Guide

### Prerequisites
- Python 3.13 (already installed)
- Virtual environment `venv/` (already created)
- Playwright browser (installed via pip)

### Installation & Setup
```bash
# Navigate to project
cd /Users/saadkhan/Documents/zameen

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (one-time)
playwright install chromium

# Verify installation
python3 -c "from playwright.sync_api import sync_playwright; print('OK')"
```

### Running the Scraper

#### Basic Usage (Default Location)
```bash
source venv/bin/activate
python3 scrape.py
# Scrapes Bahria Town Precinct 5 (default)
# Output: data/bahria_town_precinct_5/2025-11-11_HHMMSS/
# Takes: 2-3 minutes (8 pages * 20+ seconds per page)
```

#### Change Location
1. Edit `scrape.py`
2. Uncomment desired location preset:
   ```python
   # Precinct 6
   LOCATION_NAME = 'Bahria_Town_Karachi_Bahria_Town___Precinct_6'
   LOCATION_ID = '10014'
   LOCATION_DISPLAY = 'bahria_town_precinct_6'
   ```
3. Run: `python3 scrape.py`

#### Adjust Scraping Depth
```python
MAX_PAGES = 8  # Default: 8 pages (~150 properties)
MAX_PAGES = 4  # Quick test: 4 pages (~75 properties)
MAX_PAGES = 20 # Deep analysis: 20 pages (~400+ properties)
```

### Running Analysis

#### Analyze Recent Scrape
```bash
python3 analyze_folder.py
# Prompts for folder path
# Or edit script to specify folder directly
```

#### Compare Multiple Precincts
```bash
python3 constructionAnalysis/construction_cost_analysis.py
# Requires: houses.xlsx from 2+ different precincts
# Creates: construction_cost_comparison.csv
```

### Common Workflows

#### Time-Series Tracking (Monthly)
```bash
# Week 1 of each month
source venv/bin/activate

# Scrape latest data
python3 scrape.py                    # Precinct 5
python3 scrape.py  # After editing for Precinct 6
python3 scrape.py  # After editing for Precinct 8

# Analyze and compare
python3 constructionAnalysis/construction_cost_analysis.py

# Check: data/bahria_town_precinct_5/ for multiple folders
# Compare folder-to-folder to see price trends
```

#### Market Analysis
```python
# Script to compare across time and location
import pandas as pd
from pathlib import Path

# Load latest Precinct 5 data
latest_p5 = sorted(Path('data/bahria_town_precinct_5').glob('*'))[-1]
df_p5 = pd.read_excel(latest_p5 / 'houses.xlsx', sheet_name='Properties')

# Load latest Precinct 6 data
latest_p6 = sorted(Path('data/bahria_town_precinct_6').glob('*'))[-1]
df_p6 = pd.read_excel(latest_p6 / 'houses.xlsx', sheet_name='Properties')

# Compare
print(f"P5 Median: {df_p5['Price'].median():,.0f}")
print(f"P6 Median: {df_p6['Price'].median():,.0f}")
print(f"P5 Cost/Yd: {(df_p5['Price'] / df_p5['Size']).median():,.0f}")
print(f"P6 Cost/Yd: {(df_p6['Price'] / df_p6['Size']).median():,.0f}")
```

---

## Statistical Methods & Analysis Approach

- **Median:** More robust than average (resistant to outliers)
- **Per Square Yard Normalization:** Allows fair comparison across properties
- **Variance Analysis:** Identifies bargains (>10% below median)
- **Outlier Detection:** Flags suspicious listings for investigation
- **Time-Series Tracking:** Multiple dated scrapes enable price trend monitoring

---

## File Reference

| File | Purpose | When to Edit |
|------|---------|---|
| `scrape.py` | Main entry point | When changing location or pages |
| `zameen_json_scraper.py` | Core scraping logic | If Zameen changes JSON structure |
| `analyze_folder.py` | Data analysis tool | Rarely (logic is stable) |
| `constructionAnalysis/*.py` | Cross-location analysis | When adding new precincts |
| `requirements.txt` | Python dependencies | When adding new libraries |
| `LOCATIONS.md` | Location ID reference | When discovering new areas |
| `README.md` | Main documentation | Update findings regularly |
| `METHODOLOGY.md` | Technical approach | Reference only |
| `data/` | Timestamped scrapes | Auto-generated (don't edit) |

---

## GitHub Repository

- **URL:** https://github.com/saadkhan23/zameen.git
- **Status:** Public repository
- **Recent Updates:**
  - Hide archive folder (keep code visible, data private)
  - Rewrite README (human-friendly style)
  - Initial commit (core functionality)

### Pushing Updates
```bash
# Make changes locally
git add .
git commit -m "Description of changes"
git push origin main
```

---

## Summary

This project demonstrates:
- **Advanced Web Scraping** (Playwright for JavaScript rendering)
- **Data Engineering** (ETL pipeline design, error handling)
- **Statistical Analysis** (median analysis, outlier detection)
- **Data Transformation** (normalization, calculation)
- **Excel Automation** (programmatic formatting)
- **Ethical Considerations** (respectful scraping)

The pipeline is production-ready, maintainable, and extensible. The main opportunities are:
1. Time-series price tracking (monthly scrapes)
2. Geographic expansion (other locations)
3. Web dashboard for exploration
4. Automated investment alerts

---

## Changelog
- **2025-11-14** — Implemented grey-structure filtering across analysis (construction cost, bargains, size-vs-price); added counts per precinct; created `analysis/bottom_up_calculator.py` with defaults (floors=2, coverage=0.70, 5k–5.5k PKR/sq ft, soft 3%, contingency 10%, utilities 300k PKR, HOA 7k/month) and exported `bottom_up_calculator.json`; extended portfolio sync to publish it.
- **2025-11-14** — Added Audience & Scope, Assumptions (HOA 7k/month; finished cost 5–5.5k PKR/sq ft), and Backlog/Next Steps (grey-structure filtering, bottom-up calculator, implied vs bottom-up cross-check, portfolio JSON extensions, rental yields later, BTK-first scope). Aligns documentation with planned analysis and target audience.
- **2025-11-13** — Created chatgpt_data folder with 12 raw data exports (CSV/JSON) for each precinct/type combination. Added "Raw Data Exports for AI Analysis" section to Data Status.
- **2025-11-13** — Initialized Multi-AI Coordination Policy. Added Known Risks/Fragilities section and moved volatile findings to dated Current Findings Snapshot section.
