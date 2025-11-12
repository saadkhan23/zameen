"""
Zameen.com JSON Data Scraper
Extracts data from embedded JSON instead of HTML parsing
"""

from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
import time
import random
import re
import json
import os

class ZameenJSONScraper:
    def __init__(self, run_folder=None):
        self.base_url = "https://www.zameen.com"
        self.properties = []
        # Create run-specific folder if not provided
        if run_folder is None:
            self.run_folder = os.path.join("data", datetime.now().strftime('%Y-%m-%d_%H%M%S'))
        else:
            self.run_folder = run_folder
        os.makedirs(self.run_folder, exist_ok=True)

    def _smart_delay(self, min_seconds=2, max_seconds=5):
        """Random delay to appear more human-like"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def get_area_url(self, location_name, location_id, category="Homes", page=1):
        """Generate URL for Zameen listings"""
        return f"{self.base_url}/{category}/Karachi_{location_name}-{location_id}-{page}.html"

    def extract_json_data(self, page_content):
        """Extract property data from embedded JSON"""
        try:
            # Find the JSON data embedded in the page
            # It's usually in a script tag with window.__APP_STATE__ or similar
            pattern = r'"hits":\s*\[(.*?)\],"hitsPerPage"'
            match = re.search(pattern, page_content, re.DOTALL)

            if not match:
                print("  Could not find JSON data in page")
                return []

            json_str = '[' + match.group(1) + ']'

            # Parse JSON
            properties_json = json.loads(json_str)

            properties = []
            for prop in properties_json:
                try:
                    property_data = {
                        'scraped_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'id': prop.get('id'),
                        'title': prop.get('title', '').strip(),
                        'price_pkr': prop.get('price'),
                        'price': f"PKR {prop.get('price', 0):,.0f}" if prop.get('price') else 'N/A',
                        'bedrooms': prop.get('rooms'),
                        'bathrooms': prop.get('baths'),
                        'area_sqm': prop.get('area'),
                        'area_sqyd': prop.get('area', 0) * 1.19599 if prop.get('area') else None,  # Convert to sq yd
                        'property_type': None,
                        'location': None,
                        'location_detail': None,
                        'agency_name': None,
                        'agency_tier': None,
                        'contact_name': prop.get('contactName'),
                        'phone': None,
                        'photo_count': prop.get('photoCount', 0),
                        'created_date': None,
                        'updated_date': None,
                        'url': None,
                        'short_description': prop.get('shortDescription', '').strip()[:200]
                    }

                    # Extract location details
                    if 'location' in prop and isinstance(prop['location'], list):
                        # Get the most specific location (last item)
                        locations = [loc.get('name') for loc in prop['location'] if loc.get('name')]
                        if locations:
                            property_data['location'] = locations[-1]  # Most specific
                            property_data['location_detail'] = ' > '.join(locations)

                    # Extract category/property type
                    if 'category' in prop and isinstance(prop['category'], list):
                        categories = [cat.get('name') for cat in prop['category'] if cat.get('name')]
                        if categories:
                            property_data['property_type'] = categories[-1]  # Most specific

                    # Extract agency info
                    if 'agency' in prop and isinstance(prop['agency'], dict):
                        agency = prop['agency']
                        property_data['agency_name'] = agency.get('name')
                        property_data['agency_tier'] = agency.get('product')  # e.g., "premium", "titanium plus"

                    # Extract phone
                    if 'phoneNumber' in prop and isinstance(prop['phoneNumber'], dict):
                        phone_data = prop['phoneNumber']
                        property_data['phone'] = phone_data.get('mobile') or phone_data.get('phone')

                    # Extract dates
                    if 'createdAt' in prop:
                        try:
                            created_timestamp = prop['createdAt']
                            property_data['created_date'] = datetime.fromtimestamp(created_timestamp).strftime('%Y-%m-%d')
                            # Calculate days on market
                            days_on_market = (datetime.now() - datetime.fromtimestamp(created_timestamp)).days
                            property_data['days_on_market'] = days_on_market
                        except:
                            pass

                    if 'updatedAt' in prop:
                        try:
                            updated_timestamp = prop['updatedAt']
                            property_data['updated_date'] = datetime.fromtimestamp(updated_timestamp).strftime('%Y-%m-%d')
                        except:
                            pass

                    # Build URL
                    if 'slug' in prop:
                        property_data['url'] = f"{self.base_url}/Property/{prop['slug']}"

                    # Calculate cost per sq yd
                    if property_data['price_pkr'] and property_data['area_sqyd']:
                        property_data['cost_per_sq_yd'] = property_data['price_pkr'] / property_data['area_sqyd']

                    properties.append(property_data)

                except Exception as e:
                    print(f"  Error parsing property: {e}")
                    continue

            return properties

        except Exception as e:
            print(f"  Error extracting JSON data: {e}")
            return []

    def scrape_with_playwright(self, location_name, location_id, category="Homes", max_pages=3):
        """Scrape property listings using Playwright"""
        print(f"Starting JSON scraper...")
        print(f"Location: {location_name}")
        print(f"Category: {category}")
        print(f"Pages to scrape: {max_pages}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            try:
                for page_num in range(1, max_pages + 1):
                    url = self.get_area_url(location_name, location_id, category, page_num)
                    print(f"\nScraping page {page_num}: {url}")

                    # Navigate to page
                    page.goto(url, wait_until='networkidle', timeout=30000)

                    # Get page content
                    content = page.content()

                    # Extract properties from JSON
                    properties = self.extract_json_data(content)

                    if properties:
                        print(f"  ✓ Extracted {len(properties)} properties")
                        self.properties.extend(properties)
                    else:
                        print(f"  ⚠ No properties found on page {page_num}")
                        break

                    # Smart delay between pages
                    if page_num < max_pages:
                        print(f"  Waiting before next page...")
                        self._smart_delay(3, 6)

            finally:
                context.close()
                browser.close()

        print(f"\nTotal properties scraped: {len(self.properties)}")
        return self.properties

    def save_to_excel(self, filename=None, area_name="data"):
        """Save scraped data to Excel file with formatting and analysis"""
        if not self.properties:
            print("No properties to save!")
            return None

        if filename is None:
            filename = f"{area_name}.xlsx"

        filepath = os.path.join(self.run_folder, filename)
        df = pd.DataFrame(self.properties)

        # Reorder columns to put key metrics first
        priority_cols = ['price_pkr', 'price', 'area_sqm', 'area_sqyd', 'cost_per_sq_yd']
        other_cols = [col for col in df.columns if col not in priority_cols]

        # Build new column order
        new_order = []
        for col in priority_cols:
            if col in df.columns:
                new_order.append(col)
        new_order.extend(other_cols)
        df = df[new_order]

        # Calculate analysis metrics (using median to avoid skew from outliers)
        median_price_per_sqyd = df['cost_per_sq_yd'].median() if 'cost_per_sq_yd' in df.columns else None
        median_price = df['price_pkr'].median() if 'price_pkr' in df.columns else None

        # Add variance from median column
        if 'cost_per_sq_yd' in df.columns and median_price_per_sqyd:
            df['variance_from_median_sqyd'] = df['cost_per_sq_yd'] - median_price_per_sqyd
            df['pct_variance_from_median'] = ((df['cost_per_sq_yd'] - median_price_per_sqyd) / median_price_per_sqyd * 100).round(1)
            # Move these columns right after cost_per_sq_yd
            cols = df.columns.tolist()
            variance_idx = cols.index('cost_per_sq_yd') + 1
            cols.insert(variance_idx, cols.pop(cols.index('variance_from_median_sqyd')))
            cols.insert(variance_idx + 1, cols.pop(cols.index('pct_variance_from_median')))
            df = df[cols]

        # Save to Excel with formatting
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            workbook = writer.book

            # Create summary sheet
            summary_df = pd.DataFrame({
                'Metric': [
                    'Total Properties',
                    'Median Price (PKR)',
                    'Average Price (PKR)',
                    'Median Price per Sq Yd (PKR)',
                    'Average Price per Sq Yd (PKR)',
                    'Min Price (PKR)',
                    'Max Price (PKR)',
                    'Scraped Date'
                ],
                'Value': [
                    len(df),
                    f"{median_price:,.0f}" if median_price else 'N/A',
                    f"{df['price_pkr'].mean():,.0f}" if 'price_pkr' in df.columns else 'N/A',
                    f"{median_price_per_sqyd:,.0f}" if median_price_per_sqyd else 'N/A',
                    f"{df['cost_per_sq_yd'].mean():,.0f}" if 'cost_per_sq_yd' in df.columns else 'N/A',
                    f"{df['price_pkr'].min():,.0f}" if 'price_pkr' in df.columns else 'N/A',
                    f"{df['price_pkr'].max():,.0f}" if 'price_pkr' in df.columns else 'N/A',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            })

            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # Write data to main sheet
            df.to_excel(writer, sheet_name='Properties', index=False, startrow=0)

            # Get worksheet
            worksheet = writer.sheets['Properties']

            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })

            currency_format = workbook.add_format({
                'num_format': '#,##0',
                'align': 'right'
            })

            number_format = workbook.add_format({
                'num_format': '0',
                'align': 'right'
            })

            percent_format = workbook.add_format({
                'num_format': '0.0"%"',
                'align': 'right'
            })

            # Format header row
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Set column widths and formats
            for col_num, col_name in enumerate(df.columns):
                # Get max length for auto-sizing
                max_len = max(
                    df[col_name].astype(str).apply(len).max(),
                    len(col_name)
                ) + 2

                # Apply formats based on column type
                if col_name in ['price_pkr', 'cost_per_sq_yd', 'variance_from_median_sqyd']:
                    worksheet.set_column(col_num, col_num, min(max_len, 20), currency_format)
                elif col_name in ['area_sqm', 'area_sqyd', 'bedrooms', 'bathrooms']:
                    worksheet.set_column(col_num, col_num, min(max_len, 15), number_format)
                elif col_name == 'pct_variance_from_median':
                    worksheet.set_column(col_num, col_num, 18, percent_format)
                else:
                    worksheet.set_column(col_num, col_num, min(max_len, 40))

            # Format summary sheet
            summary_worksheet = writer.sheets['Summary']
            summary_worksheet.set_column(0, 0, 30)
            summary_worksheet.set_column(1, 1, 25)

            # Apply header format to summary
            for col_num, value in enumerate(summary_df.columns.values):
                summary_worksheet.write(0, col_num, value, header_format)

        print(f"\n{'=' * 60}")
        print(f"DATA SAVED: {os.path.basename(filepath)}")
        print("=" * 60)

        # Print analysis summary
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"  Total Properties: {len(df)}")
        print(f"\n💰 PRICE STATISTICS:")
        print(f"  Median Price:  PKR {median_price:,.0f}" if median_price else "  Median Price: N/A")
        print(f"  Average Price: PKR {df['price_pkr'].mean():,.0f}" if 'price_pkr' in df.columns else "  Average Price: N/A")
        print(f"  Min Price:     PKR {df['price_pkr'].min():,.0f}" if 'price_pkr' in df.columns else "  Min Price: N/A")
        print(f"  Max Price:     PKR {df['price_pkr'].max():,.0f}" if 'price_pkr' in df.columns else "  Max Price: N/A")

        print(f"\n📏 PRICE PER SQ YD:")
        print(f"  Median:  PKR {median_price_per_sqyd:,.0f}/sq yd" if median_price_per_sqyd else "  Median: N/A")
        print(f"  Average: PKR {df['cost_per_sq_yd'].mean():,.0f}/sq yd" if 'cost_per_sq_yd' in df.columns else "  Average: N/A")
        print(f"  Min:     PKR {df['cost_per_sq_yd'].min():,.0f}/sq yd" if 'cost_per_sq_yd' in df.columns else "  Min: N/A")
        print(f"  Max:     PKR {df['cost_per_sq_yd'].max():,.0f}/sq yd" if 'cost_per_sq_yd' in df.columns else "  Max: N/A")

        # Show bargain opportunities
        if 'pct_variance_from_median' in df.columns:
            bargains = df[df['pct_variance_from_median'] < -10].sort_values('pct_variance_from_median')
            if len(bargains) > 0:
                print(f"\n🎯 BARGAIN ALERTS (>10% below median):")
                print(f"  Found {len(bargains)} properties below market median!")
                print(f"\n  Top 5 Bargains:")
                for idx, (i, row) in enumerate(bargains.head(5).iterrows(), 1):
                    print(f"    {idx}. {row.get('pct_variance_from_median', 0):.1f}% below median - PKR {row.get('price_pkr', 0):,.0f} ({row.get('bedrooms', '?')} bed)")
            else:
                print(f"\n  No properties >10% below median found")

        print(f"\n{'=' * 60}")
        return filepath

    def get_summary_statistics(self):
        """Generate summary statistics"""
        if not self.properties:
            return {}

        df = pd.DataFrame(self.properties)

        summary = {
            'total_properties': len(df),
            'avg_price': f"PKR {df['price_pkr'].mean():,.0f}" if 'price_pkr' in df.columns else 'N/A',
            'median_price': f"PKR {df['price_pkr'].median():,.0f}" if 'price_pkr' in df.columns else 'N/A',
            'avg_bedrooms': f"{df['bedrooms'].mean():.1f}" if 'bedrooms' in df.columns else 'N/A',
            'date_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return summary


if __name__ == "__main__":
    scraper = ZameenJSONScraper()

    # Test with Bahria Town Precinct 8
    properties = scraper.scrape_with_playwright(
        location_name='Bahria_Town_Karachi_Bahria_Town___Precinct_8',
        location_id='10016',
        category='Homes',
        max_pages=2
    )

    if properties:
        filepath = scraper.save_to_excel(area_name='bahria_precinct_8_houses')
        print("\nSummary:")
        summary = scraper.get_summary_statistics()
        for key, value in summary.items():
            print(f"  {key}: {value}")
    else:
        print("No properties found!")
