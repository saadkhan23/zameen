"""
Zameen.com Real Estate Data Scraper - Playwright Version
Handles JavaScript-rendered content
"""

from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
import time
import random
import re
from bs4 import BeautifulSoup

class ZameenScraperPlaywright:
    def __init__(self, headless=True):
        self.base_url = "https://www.zameen.com"
        self.headless = headless
        self.properties = []

        # Rotating user agents
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        ]

    def _smart_delay(self, min_seconds=2, max_seconds=5):
        """Random delay to appear more human-like"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def get_area_url(self, location_name, location_id, page=1):
        """
        Generate URL for Zameen listings
        Format: /Homes/Karachi_{LOCATION_NAME}-{LOCATION_ID}-{PAGE}.html

        Examples:
        - Bahria Town: location_name='Bahria_Town_Karachi', location_id='10016'
        - DHA Phase 5: location_name='DHA_Phase_5_Karachi', location_id='2'
        """
        return f"{self.base_url}/Homes/Karachi_{location_name}-{location_id}-{page}.html"

    def scrape_with_playwright(self, url, max_pages=3):
        """Scrape property listings using Playwright"""
        print(f"Starting Playwright scraper...")
        print(f"Target: {url}")
        print(f"Pages to scrape: {max_pages}")

        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=self.headless)

            # Create context with random user agent
            context = browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1920, 'height': 1080}
            )

            page = context.new_page()

            try:
                for page_num in range(1, max_pages + 1):
                    # Construct page URL
                    if page_num == 1:
                        page_url = url
                    else:
                        # Update page number in URL
                        page_url = re.sub(r'-\d+\.html$', f'-{page_num}.html', url)

                    print(f"\nScraping page {page_num}: {page_url}")

                    # Navigate to page
                    page.goto(page_url, wait_until='networkidle', timeout=30000)

                    # Wait for property listings to load
                    try:
                        page.wait_for_selector('a[href*="/Property/"]', timeout=10000)
                    except:
                        print(f"  No property listings found on page {page_num}")
                        break

                    # Get page content
                    content = page.content()

                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(content, 'html.parser')

                    # Find property links
                    property_links = soup.find_all('a', href=re.compile(r'/Property/.*\.html'))

                    if not property_links:
                        print(f"  No property cards found on page {page_num}")
                        break

                    print(f"  Found {len(property_links)} property links")

                    # Extract property data from cards
                    processed_urls = set()
                    for link in property_links:
                        prop_url = link.get('href')
                        if prop_url and prop_url not in processed_urls:
                            processed_urls.add(prop_url)

                            # Find the parent card container
                            card = link.find_parent(['div', 'article', 'li'])
                            if card:
                                property_data = self.extract_property_data(card, prop_url)
                                if property_data:
                                    self.properties.append(property_data)

                    print(f"  Extracted {len([p for p in self.properties if 'page_{}'.format(page_num) in str(p)])} properties from this page")

                    # Smart delay between pages
                    if page_num < max_pages:
                        print(f"  Waiting before next page...")
                        self._smart_delay(3, 6)

            finally:
                context.close()
                browser.close()

        print(f"\nTotal properties scraped: {len(self.properties)}")
        return self.properties

    def extract_property_data(self, card, prop_url):
        """Extract data from a property card"""
        try:
            property_data = {
                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'url': f"{self.base_url}{prop_url}" if not prop_url.startswith('http') else prop_url
            }

            # Extract all text from card
            card_text = card.get_text(' ', strip=True)

            # Extract price - look for PKR, Crore, Lac patterns
            price_match = re.search(r'PKR\s*[\d,.]+\s*(?:Crore|Lac|Lakh)?', card_text, re.IGNORECASE)
            if price_match:
                property_data['price'] = price_match.group(0)

            # Extract title
            title_elem = card.find(['h2', 'h3', 'h4', 'a'])
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                if len(title_text) > 10 and len(title_text) < 200:  # Reasonable title length
                    property_data['title'] = title_text

            # Extract area/size - look for Marla, Kanal, Sq patterns
            area_match = re.search(r'(\d+)\s*(Marla|Kanal|Sq\.?\s*(?:Yd|Ft|Yard|Feet))', card_text, re.IGNORECASE)
            if area_match:
                property_data['area'] = f"{area_match.group(1)} {area_match.group(2)}"

            # Extract bedrooms
            bed_match = re.search(r'(\d+)\s*Bed', card_text, re.IGNORECASE)
            if bed_match:
                property_data['bedrooms'] = f"{bed_match.group(1)} Beds"

            # Extract bathrooms
            bath_match = re.search(r'(\d+)\s*Bath', card_text, re.IGNORECASE)
            if bath_match:
                property_data['bathrooms'] = f"{bath_match.group(1)} Baths"

            # Extract location - usually contains "Bahria Town", "DHA", etc.
            location_patterns = [
                r'(Bahria Town[^,]*Precinct\s*\d+)',
                r'(DHA Phase\s*\d+)',
                r'(Gulshan-e-Iqbal[^,]*Block\s*\d+)',
            ]
            for pattern in location_patterns:
                loc_match = re.search(pattern, card_text, re.IGNORECASE)
                if loc_match:
                    property_data['location'] = loc_match.group(1)
                    break

            # Extract time/date added
            time_patterns = [
                r'(?:Added|Updated):\s*(\d+\s*(?:day|week|month|hour)s?\s*ago)',
                r'(\d+\s*(?:day|week|month|hour)s?\s*ago)',
            ]
            for pattern in time_patterns:
                time_match = re.search(pattern, card_text, re.IGNORECASE)
                if time_match:
                    property_data['listed_date'] = time_match.group(1)
                    property_data['days_on_market'] = self._extract_days_on_market(time_match.group(1))
                    break

            # Return only if we have essential data
            if 'price' in property_data and 'area' in property_data:
                return property_data

            return None

        except Exception as e:
            print(f"  Error extracting property data: {e}")
            return None

    def _extract_days_on_market(self, date_text):
        """Convert 'Added: 2 weeks ago' or 'Updated: 1 day ago' to days"""
        try:
            date_text = date_text.upper()

            # Extract number
            match = re.search(r'(\d+)', date_text)
            if not match:
                return None

            number = int(match.group(1))

            # Determine unit
            if 'WEEK' in date_text:
                return number * 7
            elif 'MONTH' in date_text:
                return number * 30
            elif 'DAY' in date_text:
                return number
            elif 'HOUR' in date_text:
                return 0  # Less than a day
            elif 'YEAR' in date_text:
                return number * 365

            return None
        except:
            return None

    def save_to_excel(self, filename=None, area_name="data"):
        """Save scraped data to Excel file"""
        if not self.properties:
            print("No properties to save!")
            return None

        # Create data directory if it doesn't exist
        import os
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)

        if filename is None:
            filename = f"{area_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        df = pd.DataFrame(self.properties)

        # Save to Excel in data directory
        filepath = os.path.join(data_dir, filename)
        df.to_excel(filepath, index=False, engine='openpyxl')

        print(f"\nData saved to: {filepath}")
        return filepath

    def get_summary_statistics(self):
        """Generate summary statistics of scraped data"""
        if not self.properties:
            return "No data available for analysis"

        df = pd.DataFrame(self.properties)

        summary = {
            'total_properties': len(df),
            'unique_locations': df['location'].nunique() if 'location' in df.columns else 0,
            'date_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return summary


def main():
    """Main execution function"""
    print("=" * 60)
    print("Zameen.com Scraper - Playwright Version")
    print("=" * 60)

    scraper = ZameenScraperPlaywright(headless=True)

    # Bahria Town Karachi configuration
    location_name = 'Bahria_Town_Karachi'
    location_id = '10016'
    max_pages = 2  # Start with 2 pages for testing

    print(f"\nTarget: Bahria Town Karachi")
    print(f"Pages: {max_pages}")

    # Generate URL
    url = scraper.get_area_url(location_name, location_id)

    # Perform scraping
    properties = scraper.scrape_with_playwright(url, max_pages=max_pages)

    if properties:
        # Save to Excel
        filepath = scraper.save_to_excel(area_name='bahria_town_karachi')

        # Display summary
        print("\n" + "=" * 60)
        print("SUMMARY STATISTICS")
        print("=" * 60)
        summary = scraper.get_summary_statistics()
        for key, value in summary.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        print("\n" + "=" * 60)
        print(f"✓ Scraping complete!")
        print(f"✓ Data saved to Excel file")
        print("=" * 60)
        print("\nNext: Run 'python3 analyze_data.py' to create visuals!")

        return filepath
    else:
        print("\n⚠ No properties were scraped.")
        return None


if __name__ == "__main__":
    main()
