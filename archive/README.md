# Zameen.com Real Estate Scraper

Simple tool to scrape and analyze real estate data from Zameen.com for any area in Karachi.

## Quick Start

### 1. Install Dependencies
```bash
cd zameen
pip install -r requirements.txt
```

### 2. Scrape Data
```bash
python zameen_scraper.py
```

The scraper will ask you:
- Which area? (Bahria Town, DHA Phase 5, Gulshan-e-Iqbal, Clifton, or custom)
- What property type? (Homes for sale, rent, or plots)
- How many pages? (default: 3)
- **Quick or Detailed mode?**
  - Quick: Fast, listing cards only
  - Detailed: Slower, includes investment metrics from detail pages

**Output**: Excel file with raw scraped data (e.g., `bahria_town_karachi_20250106_120000.xlsx`)

### 3. Analyze & Visualize
```bash
python analyze_data.py
```

**Output**:
- Excel report with analysis (`analysis_report_*.xlsx`)
- Up to 5 PNG charts ready for WhatsApp:
  - Cost per Sq Yd by Location
  - Price Distribution
  - Market Summary
  - Days on Market (liquidity indicator)
  - Investment Insights Card

## Key Features

### Anti-Blocking
- Rotating user agents
- Random delays (2-5 seconds between pages)
- Session management
- Automatic retry on failures

### Scalable to Any Area
Choose from preset areas:
- Bahria Town Karachi
- DHA Phase 5
- Gulshan-e-Iqbal
- Clifton

Or provide custom area slug (e.g., `falcon_complex_karachi`)

### Focus on Cost per Sq Yd
All area measurements converted to Sq Yd for consistent comparison:
- Marla → Sq Yd (1 Marla = 30 Sq Yd)
- Kanal → Sq Yd (1 Kanal = 605 Sq Yd)
- Sq Ft → Sq Yd (9 Sq Ft = 1 Sq Yd)

### Investment Metrics (Detailed Mode)
When you enable detailed scraping, you get:

**From Listing Cards:**
- Days on market (liquidity indicator)
- Agent tier badges (Titanium/Platinum/Gold)
- Listing status (Featured, Hot)
- Photo count (quality indicator)

**From Detail Pages:**
- Built year & property age
- Possession status (Ready vs Under Construction)
- Amenities: parking, central AC, servant quarters, security
- Community features: pool, gym, mosque
- Amenity score (1-6 scale based on premium features)

**Calculated Insights:**
- Negotiable opportunities (stale listings > 90 days)
- Hot market indicators (fresh listings < 7 days)
- Premium property count (amenity score ≥ 4)

## Example Workflows

### Quick Analysis (Recommended for First Time)
```bash
# 1. Scrape Bahria Town (Quick mode)
python zameen_scraper.py
# Select: 1 (Bahria Town), 1 (Homes for Sale), 3 (pages), 1 (Quick)

# 2. Analyze the data
python analyze_data.py
# Creates Excel + charts

# 3. Share charts on WhatsApp
# Send the PNG files to your family!
```

### Investment Deep Dive (Detailed Mode)
```bash
# 1. Scrape with investment metrics
python zameen_scraper.py
# Select: 1 (Bahria Town), 1 (Homes for Sale), 2 (pages), 2 (Detailed)
# Then: 10 (get details for 10 properties)

# 2. Analyze with investment insights
python analyze_data.py
# Creates Excel + 5 charts including investment insights

# 3. Review investment opportunities
# Check Excel "Cost per Sq Yd" sheet
# Look at "days_on_market" > 90 for negotiation opportunities
# Review "amenity_score" for premium properties
```

## Files Explained

- `zameen_scraper.py` - Scrapes Zameen.com for property listings
- `analyze_data.py` - Analyzes scraped data and creates visualizations
- `requirements.txt` - Python dependencies
- `*.xlsx` - Raw data and analysis reports
- `charts_*.png` - WhatsApp-ready visualizations

## Tips

1. **Start small**: Use 2-3 pages in Quick mode first to test
2. **Peak hours**: Avoid scraping during peak hours (9am-6pm PKT)
3. **Regular updates**: Re-run weekly to track market trends
4. **Multiple areas**: Compare Bahria Town vs DHA by running scraper twice
5. **Detailed mode**: Use sparingly (10-20 properties max) to avoid blocking
6. **Investment focus**:
   - Properties > 90 days on market = negotiation leverage
   - Fresh listings (< 7 days) = hot market, act fast
   - High amenity scores (4+) = rental yield potential
   - Ready possession > Under construction for immediate ROI

## Troubleshooting

**No properties scraped?**
- Check internet connection
- Website structure may have changed
- Try reducing pages to 1-2

**Missing cost per sq yd?**
- Some listings don't include area information
- The analyzer will skip these properties

**Charts look weird?**
- Need at least 5-10 properties with complete data
- Try scraping more pages

## Legal Note

This tool is for personal research only. Respect Zameen.com's terms of service.
The scraper includes polite delays and doesn't overload their servers.
