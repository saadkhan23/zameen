"""
Zameen.com Real Estate Data Scraper
Focuses on Bahria Town Karachi properties
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import json
from urllib.parse import urljoin
import re
import random

class ZameenScraper:
    def __init__(self):
        self.base_url = "https://www.zameen.com"

        # Rotating user agents to avoid blocking
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        ]

        self.session = requests.Session()
        self.properties = []

    def _get_headers(self):
        """Get random headers to avoid detection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        }

    def _smart_delay(self, min_seconds=2, max_seconds=5):
        """Random delay to appear more human-like"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def get_area_url(self, area_slug, property_type="homes", purpose="buy"):
        """
        Generate URL for any Karachi area
        area_slug: URL-friendly area name (e.g., 'bahria_town_karachi', 'dha_phase_5_karachi', 'gulshan_e_iqbal_karachi')
        property_type: 'homes', 'plots', 'commercial'
        purpose: 'buy', 'rent'
        """
        return f"{self.base_url}/{property_type}-for-{purpose}-in-{area_slug}-1/"
    
    def scrape_listing_page(self, url, max_pages=5):
        """Scrape multiple pages of listings"""
        print(f"Starting scrape from: {url}")

        for page in range(1, max_pages + 1):
            page_url = f"{url}?page={page}" if page > 1 else url
            print(f"\nScraping page {page}...")

            try:
                # Use rotating headers and session for better stability
                response = self.session.get(page_url, headers=self._get_headers(), timeout=15)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Find property cards
                property_cards = soup.find_all('li', class_=re.compile('.*property.*'))

                if not property_cards:
                    print(f"No properties found on page {page}")
                    break

                print(f"Found {len(property_cards)} property cards on page {page}")

                for card in property_cards:
                    property_data = self.extract_property_data(card)
                    if property_data:
                        self.properties.append(property_data)

                # Smart random delay between requests (2-5 seconds)
                if page < max_pages:  # Don't delay after last page
                    print(f"Waiting before next page...")
                    self._smart_delay(2, 5)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                print("Retrying once after delay...")
                self._smart_delay(5, 8)
                try:
                    response = self.session.get(page_url, headers=self._get_headers(), timeout=15)
                    response.raise_for_status()
                    # Process retry response (simplified - just continue on success)
                except:
                    print(f"Retry failed for page {page}, moving on...")
                    continue

        print(f"\nTotal properties scraped: {len(self.properties)}")
        return self.properties
    
    def extract_property_data(self, card):
        """Extract data from a single property card"""
        try:
            property_data = {
                'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Extract price
            price_elem = card.find(['span', 'div'], class_=re.compile('.*price.*'))
            if price_elem:
                property_data['price'] = price_elem.get_text(strip=True)

            # Extract title
            title_elem = card.find(['h2', 'h3', 'a'], class_=re.compile('.*title.*'))
            if not title_elem:
                title_elem = card.find('a', attrs={'aria-label': True})
            if title_elem:
                property_data['title'] = title_elem.get_text(strip=True)
                # Extract URL
                link = title_elem.get('href')
                if link:
                    property_data['url'] = urljoin(self.base_url, link)

            # Extract location
            location_elem = card.find(['div', 'span'], class_=re.compile('.*location.*'))
            if location_elem:
                property_data['location'] = location_elem.get_text(strip=True)

            # Extract area/size
            area_elem = card.find(['span', 'div'], class_=re.compile('.*(area|size).*'))
            if area_elem:
                property_data['area'] = area_elem.get_text(strip=True)

            # Extract bedrooms
            bed_elem = card.find(['span', 'div'], string=re.compile('.*bed.*', re.IGNORECASE))
            if bed_elem:
                property_data['bedrooms'] = bed_elem.get_text(strip=True)

            # Extract bathrooms
            bath_elem = card.find(['span', 'div'], string=re.compile('.*bath.*', re.IGNORECASE))
            if bath_elem:
                property_data['bathrooms'] = bath_elem.get_text(strip=True)

            # Extract property type
            type_elem = card.find(['span', 'div'], class_=re.compile('.*type.*'))
            if type_elem:
                property_data['property_type'] = type_elem.get_text(strip=True)

            # Extract added/updated date and calculate days on market
            date_elem = card.find(['span', 'div'], string=re.compile('.*(added|updated).*', re.IGNORECASE))
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                property_data['listed_date'] = date_text
                property_data['days_on_market'] = self._extract_days_on_market(date_text)

            # Extract agent tier badges (Titanium, etc.)
            badge_elem = card.find(['span', 'div'], class_=re.compile('.*(badge|tier|agent).*'))
            if badge_elem:
                badge_text = badge_elem.get_text(strip=True)
                if any(tier in badge_text.upper() for tier in ['TITANIUM', 'PLATINUM', 'GOLD', 'SILVER']):
                    property_data['agent_tier'] = badge_text

            # Extract listing status badges (hot, featured, etc.)
            status_badges = []
            for badge in card.find_all(['span', 'div'], class_=re.compile('.*(featured|hot|urgent).*', re.IGNORECASE)):
                badge_text = badge.get_text(strip=True)
                if badge_text:
                    status_badges.append(badge_text)
            if status_badges:
                property_data['status_badges'] = ', '.join(status_badges)

            # Extract photo count (indicates listing quality)
            photo_indicator = card.find(['span', 'div'], string=re.compile('.*photo.*', re.IGNORECASE))
            if photo_indicator:
                photo_match = re.search(r'(\d+)', photo_indicator.get_text())
                if photo_match:
                    property_data['photo_count'] = int(photo_match.group(1))

            # Alternative: count image elements in card
            if 'photo_count' not in property_data:
                images = card.find_all('img')
                if len(images) > 0:
                    property_data['photo_count'] = len(images)

            return property_data if len(property_data) > 1 else None

        except Exception as e:
            print(f"Error extracting property data: {e}")
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

    def scrape_detail_page(self, url):
        """Scrape additional details from property detail page"""
        try:
            print(f"  Fetching details from {url[:50]}...")
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            details = {}

            # Extract built year
            built_year_elem = soup.find(string=re.compile('built.*year', re.IGNORECASE))
            if built_year_elem:
                year_match = re.search(r'(19|20)\d{2}', built_year_elem.parent.get_text())
                if year_match:
                    details['built_year'] = int(year_match.group(0))
                    details['property_age'] = datetime.now().year - details['built_year']

            # Extract possession status
            possession_elem = soup.find(string=re.compile('possession|ready|under construction', re.IGNORECASE))
            if possession_elem:
                possession_text = possession_elem.parent.get_text()
                if 'READY' in possession_text.upper():
                    details['possession_status'] = 'Ready'
                elif 'CONSTRUCTION' in possession_text.upper():
                    details['possession_status'] = 'Under Construction'

            # Extract amenities
            amenity_keywords = {
                'parking': ['parking', 'car park', 'garage'],
                'central_ac': ['central ac', 'central air', 'central heating'],
                'servant_quarter': ['servant quarter', 'servant room', 'maid room'],
                'security': ['security', 'guard', 'gated'],
                'maintenance': ['maintenance staff', 'caretaker']
            }

            page_text = soup.get_text().upper()
            for amenity, keywords in amenity_keywords.items():
                if any(keyword.upper() in page_text for keyword in keywords):
                    details[amenity] = 'Yes'

            # Extract parking count if specified
            parking_match = re.search(r'(\d+)\s*car\s*park', page_text, re.IGNORECASE)
            if parking_match:
                details['parking_spaces'] = int(parking_match.group(1))

            # Extract community features
            community_keywords = {
                'pool': ['pool', 'swimming'],
                'gym': ['gym', 'fitness'],
                'mosque': ['mosque', 'masjid'],
                'playground': ['playground', 'play area'],
                'community_center': ['community center', 'club house']
            }

            for feature, keywords in community_keywords.items():
                if any(keyword.upper() in page_text for keyword in keywords):
                    details[feature] = 'Yes'

            # Calculate amenity score
            amenity_score = 0
            amenity_score += 1 if details.get('parking') == 'Yes' else 0
            amenity_score += 1 if details.get('central_ac') == 'Yes' else 0
            amenity_score += 1 if details.get('servant_quarter') == 'Yes' else 0
            amenity_score += 1 if details.get('security') == 'Yes' else 0
            amenity_score += 1 if details.get('pool') == 'Yes' else 0
            amenity_score += 1 if details.get('gym') == 'Yes' else 0
            details['amenity_score'] = amenity_score

            return details

        except Exception as e:
            print(f"  Error scraping detail page: {e}")
            return {}

    def enrich_with_details(self, max_properties=None):
        """Enrich scraped properties with detail page data"""
        if not self.properties:
            print("No properties to enrich!")
            return

        properties_to_enrich = self.properties[:max_properties] if max_properties else self.properties

        print(f"\nEnriching {len(properties_to_enrich)} properties with detail page data...")
        print("This will take a while. Be patient!")

        for i, prop in enumerate(properties_to_enrich, 1):
            if 'url' not in prop:
                continue

            print(f"\n[{i}/{len(properties_to_enrich)}] Processing: {prop.get('title', 'Unknown')[:50]}")

            # Get detail page data
            details = self.scrape_detail_page(prop['url'])

            # Merge details into property
            prop.update(details)

            # Smart delay between detail page requests
            if i < len(properties_to_enrich):
                self._smart_delay(3, 6)  # Longer delay for detail pages

        print(f"\n✓ Enriched {len(properties_to_enrich)} properties with detailed data")

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

        # Create Excel file with formatting in data directory
        filepath = os.path.join(data_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Properties', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Properties']
            
            # Add formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D7E4BD',
                'border': 1
            })
            
            # Format header row
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                # Auto-adjust column width
                worksheet.set_column(col_num, col_num, len(str(value)) + 5)
        
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
        
        # Extract numeric prices for analysis
        if 'price' in df.columns:
            try:
                # Try to extract numeric values from price strings
                df['price_numeric'] = df['price'].str.extract(r'([\d,]+)')[0].str.replace(',', '').astype(float)
                summary['avg_price'] = f"PKR {df['price_numeric'].mean():,.0f}"
                summary['min_price'] = f"PKR {df['price_numeric'].min():,.0f}"
                summary['max_price'] = f"PKR {df['price_numeric'].max():,.0f}"
            except:
                summary['price_note'] = "Could not parse prices for statistical analysis"
        
        return summary


def main():
    """Main execution function"""
    print("=" * 60)
    print("Zameen.com Scraper - Karachi Real Estate")
    print("=" * 60)

    scraper = ZameenScraper()

    # Choose area
    print("\nSelect area to scrape:")
    print("1. Bahria Town Karachi")
    print("2. DHA Phase 5")
    print("3. Gulshan-e-Iqbal")
    print("4. Clifton")
    print("5. Custom area (you'll provide the slug)")

    area_choice = input("\nEnter choice (1-5) or press Enter for Bahria Town: ").strip()

    area_map = {
        '1': ('bahria_town_karachi', 'Bahria Town Karachi'),
        '2': ('dha_phase_5_karachi', 'DHA Phase 5'),
        '3': ('gulshan_e_iqbal_karachi', 'Gulshan-e-Iqbal'),
        '4': ('clifton_karachi', 'Clifton'),
        '': ('bahria_town_karachi', 'Bahria Town Karachi')
    }

    if area_choice == '5':
        custom_slug = input("Enter area slug (e.g., 'falcon_complex_karachi'): ").strip()
        custom_name = input("Enter area display name (e.g., 'Falcon Complex'): ").strip()
        area_slug, area_name = custom_slug, custom_name
    else:
        area_slug, area_name = area_map.get(area_choice, area_map[''])

    # Choose property type
    print("\nSelect property type:")
    print("1. Homes/Houses for Sale (default)")
    print("2. Homes/Houses for Rent")
    print("3. Plots for Sale")

    prop_choice = input("\nEnter choice (1-3) or press Enter for default: ").strip()

    prop_options = {
        '1': ('homes', 'buy'),
        '2': ('homes', 'rent'),
        '3': ('plots', 'buy'),
        '': ('homes', 'buy')
    }

    property_type, purpose = prop_options.get(prop_choice, ('homes', 'buy'))

    # Get number of pages
    max_pages = input("\nHow many pages to scrape? (default 3): ").strip()
    max_pages = int(max_pages) if max_pages.isdigit() else 3

    # Ask about detailed scraping
    print("\nScraping mode:")
    print("1. Quick (listing cards only - fast, recommended)")
    print("2. Detailed (also scrape detail pages - slow, investment metrics)")

    mode_choice = input("\nEnter choice (1-2) or press Enter for Quick: ").strip()
    detailed_mode = mode_choice == '2'

    # Generate URL and scrape
    url = scraper.get_area_url(area_slug, property_type, purpose)
    print(f"\nTarget URL: {url}")
    print(f"Will scrape {max_pages} pages from {area_name}...")

    # Perform scraping
    properties = scraper.scrape_listing_page(url, max_pages=max_pages)

    if properties:
        # Optional: enrich with detail page data
        if detailed_mode:
            print("\n" + "=" * 60)
            print("DETAILED MODE: Scraping detail pages...")
            print("=" * 60)
            max_detail = input(f"\nHow many properties to get details for? (max {len(properties)}, default 10): ").strip()
            max_detail = int(max_detail) if max_detail.isdigit() else min(10, len(properties))
            scraper.enrich_with_details(max_properties=max_detail)
        # Save to Excel with area name
        filepath = scraper.save_to_excel(area_name=area_slug)

        # Display summary
        print("\n" + "=" * 60)
        print("SUMMARY STATISTICS")
        print("=" * 60)
        summary = scraper.get_summary_statistics()
        for key, value in summary.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        print("\n" + "=" * 60)
        print(f"✓ Scraping complete!")
        print(f"✓ Data saved to: {filepath}")
        print("=" * 60)

        return filepath
    else:
        print("\n⚠ No properties were scraped. Please check the website structure.")
        return None


if __name__ == "__main__":
    main()
