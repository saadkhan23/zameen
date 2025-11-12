# Quick Start Guide - Zameen Scraper

## ✅ All Your Requested Improvements Implemented

### 1. Excel Formatting ✓
- ✅ Currency columns (price_pkr, cost_per_sq_yd) formatted with commas, no decimals
- ✅ Area columns (sq yd, sq ft) formatted with 0 decimal places
- ✅ Key columns (price, area, cost) moved to the beginning
- ✅ Professional header styling (blue background, white text)

### 2. Analysis Metrics ✓
- ✅ **Summary Sheet** added at the top with:
  - Median Price (to avoid skew from outliers) ⭐
  - Average Price
  - Median Price per Sq Yd ⭐
  - Average Price per Sq Yd
  - Min/Max prices
  - Total properties count
- ✅ **Variance Columns** added to identify bargains:
  - `variance_from_median_sqyd` - PKR difference from median
  - `pct_variance_from_median` - Percentage difference (negative = below median = bargain!)

### 3. Location Configuration ✓
- ✅ Easy to change location in `scrape.py`
- ✅ Quick presets for common locations
- ✅ Reference guide in `LOCATIONS.md`

### 4. Organized Folder Structure ✓
```
data/
└── bahria_town_precinct_8/          ← Location folder
    └── 2025-11-10_170840/           ← Date/time folder
        ├── houses.xlsx              ← Scraped data with analysis
        ├── plots.xlsx               ← Scraped data with analysis
        └── README.txt               ← Run info
```

### 5. Scraping Settings ✓
- ✅ Max pages set to 8 (default)
- ✅ Anti-scraping measures built-in:
  - Random delays (3-6 seconds between pages)
  - User agent rotation
  - Headless browser (Playwright)
  - Network idle waiting
  - Polite scraping pace

---

## 🚀 How to Use

### Scrape a Location

1. **Edit location in `scrape.py`:**
   ```python
   # For Precinct 6:
   LOCATION_NAME = 'Bahria_Town_Karachi_Bahria_Town___Precinct_6'
   LOCATION_ID = '10014'
   LOCATION_DISPLAY = 'bahria_town_precinct_6'
   ```

2. **Run the scraper:**
   ```bash
   python3 scrape.py
   ```

3. **Check your data:**
   ```
   data/bahria_town_precinct_6/2025-11-10_HHMMSS/
   ├── houses.xlsx    ← Open this!
   └── plots.xlsx     ← Open this!
   ```

---

## 📊 Using the Excel Files

### Summary Sheet (Top of Excel)
- **Median Price per Sq Yd** - Use this to identify fair market value (avoids skew)
- All key metrics at a glance

### Properties Sheet
**Key Columns:**
1. `price_pkr` - Property price (formatted with commas)
2. `area_sqyd` - Area in square yards (no decimals)
3. `cost_per_sq_yd` - Price per sq yd (formatted with commas)
4. `variance_from_median_sqyd` - Difference from median ⭐
5. `pct_variance_from_median` - % difference ⭐

**Finding Bargains:**
- Sort by `pct_variance_from_median` (ascending)
- **Negative values** = below median price = potential bargains!
- Example: `-15.5%` means 15.5% cheaper than median

---

## 🎯 Common Locations

See `LOCATIONS.md` for complete list.

**Quick Examples:**
- **Precinct 6:** ID `10014`
- **Precinct 10:** ID `10018`
- **DHA Phase 5:** ID `2`

---

## 🔧 Settings

Edit these in `scrape.py`:

```python
MAX_PAGES = 8           # How many pages to scrape
SCRAPE_HOUSES = True    # Scrape houses?
SCRAPE_PLOTS = True     # Scrape plots?
```

---

## 📁 Folder Organization

```
data/
├── bahria_town_precinct_6/
│   ├── 2025-11-10_120000/
│   │   ├── houses.xlsx
│   │   └── plots.xlsx
│   └── 2025-11-15_140000/    ← Run again later
│       ├── houses.xlsx
│       └── plots.xlsx
└── bahria_town_precinct_8/
    └── 2025-11-10_170000/
        ├── houses.xlsx
        └── plots.xlsx
```

**Benefits:**
- Compare same location over time (price trends)
- Compare different locations side-by-side
- Easy auditing - each run is self-contained
- No file name conflicts

---

## ⚡ Tips

1. **Finding Best Deals:**
   - Open houses.xlsx → Properties sheet
   - Sort by `pct_variance_from_median` (A→Z)
   - Properties with negative % are below market median

2. **Comparing Locations:**
   - Scrape Precinct 6 and Precinct 8
   - Compare median prices in Summary sheets
   - Look at variance distributions

3. **Tracking Over Time:**
   - Run scraper weekly for same location
   - Compare median prices across dates
   - Identify price trends

4. **Build vs Buy Analysis:**
   - Check plots.xlsx median price per sq yd
   - Check houses.xlsx median price per sq yd
   - Calculate: (House price/sq yd) - (Plot price/sq yd) = Construction cost/sq yd

---

## 🛠️ Anti-Scraping Features

Already built-in:
- ✅ 3-6 second random delays between pages
- ✅ User agent rotation (looks like different browsers)
- ✅ Headless Playwright (handles JavaScript)
- ✅ Waits for page to fully load
- ✅ Polite pace (not aggressive)

**Recommendation:** Keep MAX_PAGES ≤ 8 to stay polite

---

## 📞 Next Steps

1. Try scraping Precinct 6 to compare with Precinct 8
2. Open the Excel files and explore the variance columns
3. Sort by variance to find the best deals!

Happy house hunting! 🏡
