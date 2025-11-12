"""
Scrape Bahria Town Precinct 8 - Houses and Residential Plots
"""

from zameen_json_scraper import ZameenJSONScraper
from datetime import datetime
import os

def main():
    print("=" * 70)
    print("ZAMEEN.COM SCRAPER - BAHRIA TOWN PRECINCT 8")
    print("=" * 70)

    # Create a single run folder for this scraping session
    run_folder = os.path.join("data", datetime.now().strftime('%Y-%m-%d_%H%M%S'))
    os.makedirs(run_folder, exist_ok=True)
    print(f"\nRun folder: {run_folder}")

    # Configuration
    location_name = 'Bahria_Town_Karachi_Bahria_Town___Precinct_8'
    location_id = '10016'
    max_pages = 3

    tasks = [
        {
            'name': 'Houses in Precinct 8',
            'category': 'Homes',
            'filename': 'houses'
        },
        {
            'name': 'Residential Plots in Precinct 8',
            'category': 'Plots',
            'filename': 'plots'
        }
    ]

    all_results = []

    for task in tasks:
        print(f"\n{'=' * 70}")
        print(f"SCRAPING: {task['name']}")
        print("=" * 70)

        scraper = ZameenJSONScraper(run_folder=run_folder)

        properties = scraper.scrape_with_playwright(
            location_name=location_name,
            location_id=location_id,
            category=task['category'],
            max_pages=max_pages
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
        print(f"  Saved to: {result['file']}")
        total_properties += result['count']

    print(f"\n{'-' * 70}")
    print(f"Total properties across all categories: {total_properties}")
    print("=" * 70)
    print("\n✓ Scraping complete!")
    print(f"✓ All data saved to: {run_folder}")

    # Create a README file in the run folder
    readme_path = os.path.join(run_folder, "README.txt")
    with open(readme_path, 'w') as f:
        f.write(f"Zameen.com Scraper Run\n")
        f.write(f"=" * 50 + "\n\n")
        f.write(f"Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Location: Bahria Town Karachi - Precinct 8\n")
        f.write(f"Pages Scraped: {max_pages} per category\n\n")
        f.write(f"Results:\n")
        for result in all_results:
            f.write(f"  - {result['type']}: {result['count']} properties\n")
        f.write(f"\nTotal Properties: {total_properties}\n")

    print(f"\nNext step: python3 analyze_folder.py {run_folder}")
    print("=" * 70)

    return run_folder

if __name__ == "__main__":
    main()
