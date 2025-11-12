"""
Configurable Zameen.com Scraper
Easily change location and scraping parameters
"""

from zameen_json_scraper import ZameenJSONScraper
from datetime import datetime
import os

# ============================================================================
# CONFIGURATION - EDIT THESE VALUES
# ============================================================================

# Location to scrape
LOCATION_NAME = 'Bahria_Town_Karachi_Bahria_Town___Precinct_5'  # URL-friendly location name
LOCATION_ID = '10013'  # Zameen.com location ID
LOCATION_DISPLAY = 'bahria_town_precinct_5'  # Folder name (use lowercase, underscores)

# Scraping settings
MAX_PAGES = 8  # Maximum pages to scrape per category (default: 8)

# Property types to scrape (set to True/False)
SCRAPE_HOUSES = True
SCRAPE_PLOTS = True

# ============================================================================
# LOCATION QUICK PRESETS (uncomment to use)
# ============================================================================

# Precinct 6
# LOCATION_NAME = 'Bahria_Town_Karachi_Bahria_Town___Precinct_6'
# LOCATION_ID = '10014'
# LOCATION_DISPLAY = 'bahria_town_precinct_6'

# Precinct 10
# LOCATION_NAME = 'Bahria_Town_Karachi_Bahria_Town___Precinct_10'
# LOCATION_ID = '10018'
# LOCATION_DISPLAY = 'bahria_town_precinct_10'

# General Bahria Town Karachi
# LOCATION_NAME = 'Bahria_Town_Karachi'
# LOCATION_ID = '8298'
# LOCATION_DISPLAY = 'bahria_town_karachi'

# DHA Phase 5
# LOCATION_NAME = 'DHA_Phase_5'
# LOCATION_ID = '2'
# LOCATION_DISPLAY = 'dha_phase_5'

# ============================================================================
# SCRAPER EXECUTION (don't modify below unless you know what you're doing)
# ============================================================================

def main():
    print("=" * 70)
    print("ZAMEEN.COM SCRAPER")
    print("=" * 70)

    # Create folder structure: data/location/date_time/
    location_folder = os.path.join("data", LOCATION_DISPLAY)
    run_folder = os.path.join(location_folder, datetime.now().strftime('%Y-%m-%d_%H%M%S'))
    os.makedirs(run_folder, exist_ok=True)

    print(f"\nLocation: {LOCATION_DISPLAY.replace('_', ' ').title()}")
    print(f"Run folder: {run_folder}")
    print(f"Max pages per category: {MAX_PAGES}")

    # Build task list based on settings
    tasks = []
    if SCRAPE_HOUSES:
        tasks.append({
            'name': 'Houses',
            'category': 'Homes',
            'filename': 'houses'
        })
    if SCRAPE_PLOTS:
        tasks.append({
            'name': 'Residential Plots',
            'category': 'Plots',
            'filename': 'plots'
        })

    if not tasks:
        print("\n⚠ No property types selected! Set SCRAPE_HOUSES or SCRAPE_PLOTS to True.")
        return

    all_results = []

    for task in tasks:
        print(f"\n{'=' * 70}")
        print(f"SCRAPING: {task['name']}")
        print("=" * 70)

        scraper = ZameenJSONScraper(run_folder=run_folder)

        properties = scraper.scrape_with_playwright(
            location_name=LOCATION_NAME,
            location_id=LOCATION_ID,
            category=task['category'],
            max_pages=MAX_PAGES
        )

        if properties:
            filepath = scraper.save_to_excel(area_name=task['filename'])

            print(f"\n{'-' * 70}")
            print(f"SUMMARY: {task['name']}")
            print("-" * 70)

            summary = scraper.get_summary_statistics()
            for key, value in summary.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")

            all_results.append({
                'type': task['name'],
                'count': len(properties),
                'file': filepath
            })
        else:
            print(f"\n⚠ No properties found for {task['name']}")

    # Final summary
    print(f"\n{'=' * 70}")
    print("FINAL SUMMARY")
    print("=" * 70)

    total_properties = 0
    for result in all_results:
        print(f"\n{result['type']}:")
        print(f"  Properties scraped: {result['count']}")
        print(f"  Saved to: {os.path.basename(result['file'])}")
        total_properties += result['count']

    print(f"\n{'-' * 70}")
    print(f"Total properties: {total_properties}")
    print("=" * 70)
    print("\n✓ Scraping complete!")
    print(f"✓ All data saved to: {run_folder}")

    # Create a README file in the run folder
    readme_path = os.path.join(run_folder, "README.txt")
    with open(readme_path, 'w') as f:
        f.write(f"Zameen.com Scraper Run\n")
        f.write(f"=" * 50 + "\n\n")
        f.write(f"Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Location: {LOCATION_DISPLAY.replace('_', ' ').title()}\n")
        f.write(f"Location ID: {LOCATION_ID}\n")
        f.write(f"Pages Scraped: {MAX_PAGES} per category\n\n")
        f.write(f"Results:\n")
        for result in all_results:
            f.write(f"  - {result['type']}: {result['count']} properties\n")
        f.write(f"\nTotal Properties: {total_properties}\n")

    print(f"\n✓ README created: README.txt")
    print(f"\nNext step: python3 analyze_folder.py {run_folder}")
    print("=" * 70)

    return run_folder

if __name__ == "__main__":
    main()
