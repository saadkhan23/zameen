# Zameen Real Estate Analysis

A practical project for understanding Pakistan's real estate market. This is a data pipeline that scrapes property listings, analyzes them, and surfaces patterns that aren't obvious at first glance.

## Why This Exists

Real estate in Pakistan is a huge market. Billions of rupees flow through it every year. Yet most investment decisions are made on hunches, broker advice, or "what other people are doing."

The question was simple: what if we looked at the data directly? Can we reduce the noise and find where actual value sits?

This project started as an attempt to answer that.

---

## What It Does

At its core, this pipeline has three jobs:

**1. Collect Data**
- Visits Zameen.com (Pakistan's largest real estate marketplace)
- Pulls information about houses and plots across different precincts
- Does this automatically, without disrupting the website

**2. Organize & Analyze**
- Takes the raw data and makes sense of it
- Calculates what construction actually costs (by subtracting land price from total price)
- Normalizes everything by size so we compare apples to apples
- Finds properties that seem underpriced relative to the market

**3. Share Insights**
- Exports results to Excel with clean formatting
- Shows summary statistics and detailed breakdowns
- Flags opportunities worth investigating further

---

## The Technical Approach

### How We Get the Data

Zameen.com uses JavaScript to load property listings dynamically. Traditional scraping tools don't work because the data isn't in the HTML when the page first loads—it's rendered in the browser.

Solution: Use Playwright (a tool that controls a real browser) to load the full page, then extract the data once it's rendered.

We also built in protections:
- Random delays between page requests (so we're not hammering their servers)
- Identify ourselves as an automated bot (transparent, not deceptive)
- Keep the number of pages reasonable (~8 pages per run)

### How We Analyze It

**Median vs. Average**
If most homes in an area cost 50M PKR but one costs 500M, the average gets pulled up dramatically. The median (middle value when sorted) gives a more honest picture of what a "typical" property costs.

**Normalizing by Size**
A 300-square-yard property will cost less than a 600-square-yard property. To compare fairly, we divide price by size to get "cost per square yard." Now we can ask: do expensive precincts actually charge more per unit, or are they just selling bigger properties?

**Finding Bargains**
We calculate how far each property's price sits from the median. Properties more than 10% below the median get flagged—they might be worth a closer look.

### Construction Cost Estimation

Here's the key insight:
```
Construction Cost = (House Price) - (Plot Price)
```

The plot price is what the land alone is worth. The difference tells us how much was spent building on it. By normalizing this across different property sizes, we can compare construction costs fairly.

**Example**: Precinct 5 has 1.8x higher construction costs in absolute terms than Precinct 6, but only 23% higher per square yard. Why? Because P5 properties are 1.8x larger on average. This tells us it's market segmentation, not construction price differences.

---

## Project Structure

```
zameen/
├── README.md                           ← You are here
├── QUICK_START.md                      ← Step-by-step guide
├── LOCATIONS.md                        ← Reference for all available areas
├── requirements.txt                    ← Python dependencies
│
├── scrape.py                           ← Main entry point
├── zameen_json_scraper.py              ← Core scraping logic
├── analyze_folder.py                   ← Analyze existing data
│
├── constructionAnalysis/
│   └── construction_cost_analysis.py   ← Compare multiple precincts
│
├── data/
│   ├── bahria_town_precinct_5/
│   │   └── 2025-11-11_HHMMSS/
│   │       ├── houses.xlsx
│   │       └── plots.xlsx
│   └── [more precincts...]
│
└── archive/
    └── [earlier versions of the code]
```

Each scrape gets its own dated folder so you can track how prices change over time.

---

## Getting Started

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run a scrape
```bash
python3 scrape.py
```

This scrapes Bahria Town Precinct 5 by default (takes 2-3 minutes). Look in the `data/` folder for your results.

### Change location
Edit the top of `scrape.py` and update:
- `LOCATION_NAME`
- `LOCATION_ID`
- `LOCATION_DISPLAY`

See `LOCATIONS.md` for all available options.

### Compare multiple precincts
After scraping at least two different precincts, run:
```bash
python3 constructionAnalysis/construction_cost_analysis.py
```

This creates a CSV comparing construction costs across locations.

---

## What the Output Looks Like

### Excel File (houses.xlsx)

**Summary Sheet** shows at-a-glance statistics:
```
Total Properties: 62
Median Price: PKR 50,000,000
Median Price per Sq Yd: PKR 100,000
Min-Max Range: PKR 35M - 85M
```

**Properties Sheet** lists every property with:
- Price in PKR
- Size in square yards
- Cost per square yard
- How far it is from the median (variance)
- Percentage variance

The variance column is the interesting one—negative percentages are potential bargains.

### Terminal Output

As the script runs, it prints key findings:
```
🎯 BARGAIN ALERTS (>10% below median):
Found 8 properties below market median!

Top 5 Bargains:
  1. -15.5% below median - PKR 42,300,000
  2. -14.2% below median - PKR 42,900,000
  ...
```

---

## Key Findings (Bahria Town Karachi)

After analyzing 202 properties across 3 precincts (P5, P6, P8):

**Precinct 5**: Premium segment
- Average size: 500 square yards
- Median price: PKR 50M
- Construction cost: PKR 79,000 per square yard

**Precincts 6 & 8**: Mid-range segment
- Average size: 272 square yards
- Median prices: PKR 25.6M - 29M
- Construction costs: PKR 70-80,000 per square yard

**The insight**: Construction costs per square yard are nearly identical across precincts (75-85k range). The price differences are driven by property size and buyer segmentation, not construction economics.

This contradicts the intuition that premium locations cost more to build on. Instead, they attract buyers who want larger properties.

---

## Real-World Uses

- **Investment screening**: Identify underpriced properties in a market
- **Market monitoring**: Run monthly to track price trends
- **Location comparison**: See which precinct matches your budget and preferences
- **Construction cost benchmarking**: Understand labor and material costs in different areas

---

## Technical Skills Demonstrated

- **Web technologies**: Handling JavaScript-rendered content, HTML parsing
- **Data engineering**: ETL pipeline design, validation, error handling
- **Data analysis**: Statistical methods (median, variance), normalization
- **Python**: Object-oriented design, configuration management, logging
- **Strategic thinking**: Problem decomposition, insight generation, communication

---

## Ethical Considerations

This scraper:
- Uses public data from a public website
- Includes delays to avoid overloading servers
- Identifies itself as a bot (transparent)
- Is used for personal analysis, not redistribution
- Respects Zameen.com's terms of service

Scraping gets a bad reputation when done disrespectfully. This project does it the right way.

---

## Documentation

- **QUICK_START.md**: Step-by-step walkthrough
- **LOCATIONS.md**: Full reference of supported areas
- **Code comments**: Detailed explanations in the source

---

## Next Steps

**Phase 2: Time-Series Tracking**
- Run monthly to monitor price movements
- Detect market heating/cooling
- Identify emerging opportunities

**Phase 3: Geographic Expansion**
- Apply to other developments in Karachi
- Extend to other Pakistani cities
- Compare markets systematically

**Phase 4: Automation**
- Schedule monthly runs automatically
- Email alerts when bargains appear
- REST API for programmatic access

---

## Questions or Feedback?

The simplest way to see what this does: clone the repo, run it, and open the Excel file. The whole pipeline is designed to be immediately useful, not just theoretical.

---

## License

For personal and educational use. The data comes from Zameen.com and is publicly available.
