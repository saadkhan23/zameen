"""
Real Estate Market Analysis Tool
Analyzes scraped data from zameen.com with focus on cost per sq yd
"""

import pandas as pd
import re
from datetime import datetime
import glob
import os
import matplotlib.pyplot as plt
import seaborn as sns

class RealEstateAnalyzer:
    def __init__(self, excel_file):
        """Load data from Excel file"""
        self.df = pd.read_excel(excel_file)
        self.clean_data()
        print(f"Loaded {len(self.df)} properties from {excel_file}")
    
    def clean_data(self):
        """Clean and prepare data for analysis"""
        # Check if we have the new format (price_pkr already exists)
        if 'price_pkr' in self.df.columns:
            # New format - data is already clean!
            # Just ensure we have the right column names
            if 'bedrooms' in self.df.columns:
                self.df['bed_count'] = self.df['bedrooms']
            if 'bathrooms' in self.df.columns:
                self.df['bath_count'] = self.df['bathrooms']
            if 'area_sqyd' not in self.df.columns and 'area' in self.df.columns:
                # Convert area to sq yd if needed
                self.df['area_sqyd'] = self.convert_area_to_sqyd(self.df['area'])
            return

        # Old format - needs cleaning
        # Extract numeric price
        if 'price' in self.df.columns:
            self.df['price_text'] = self.df['price']

            # Extract numbers from price strings
            def extract_price(price_str):
                if pd.isna(price_str):
                    return None

                # Convert to string
                price_str = str(price_str).upper()

                # Remove PKR, Rs, etc.
                price_str = re.sub(r'(PKR|RS\.?|RUPEES)', '', price_str, flags=re.IGNORECASE)

                # Extract number and multiplier
                match = re.search(r'([\d,\.]+)\s*(CRORE|CR|LAC|LAKH|THOUSAND|K|M)?', price_str)
                if match:
                    number = float(match.group(1).replace(',', ''))
                    multiplier = match.group(2)

                    # Convert to actual value
                    if multiplier:
                        multiplier = multiplier.upper()
                        if multiplier in ['CRORE', 'CR']:
                            return number * 10000000
                        elif multiplier in ['LAC', 'LAKH']:
                            return number * 100000
                        elif multiplier in ['THOUSAND', 'K']:
                            return number * 1000
                        elif multiplier == 'M':
                            return number * 1000000
                    
                    return number
                return None
            
            self.df['price_pkr'] = self.df['price'].apply(extract_price)
        
        # Extract numeric area/size and convert to Sq Yd for consistency
        if 'area' in self.df.columns:
            def extract_area_to_sq_yd(area_str):
                if pd.isna(area_str):
                    return None, None

                area_str = str(area_str).upper()

                # Extract number
                match = re.search(r'([\d,\.]+)', area_str)
                if not match:
                    return None, None

                size = float(match.group(1).replace(',', ''))

                # Convert everything to Sq Yd for consistent comparison
                size_sq_yd = None
                original_unit = 'Unknown'

                if 'MARLA' in area_str:
                    original_unit = 'Marla'
                    size_sq_yd = size * 30  # 1 Marla = 30 Sq Yd (approx)
                elif 'KANAL' in area_str:
                    original_unit = 'Kanal'
                    size_sq_yd = size * 605  # 1 Kanal = 605 Sq Yd (approx)
                elif 'YARD' in area_str or ('SQ' in area_str and 'YD' in area_str):
                    original_unit = 'Sq Yd'
                    size_sq_yd = size
                elif ('SQ' in area_str and 'FT' in area_str) or 'FEET' in area_str:
                    original_unit = 'Sq Ft'
                    size_sq_yd = size / 9  # 1 Sq Yd = 9 Sq Ft

                return size_sq_yd, original_unit

            self.df[['size_sq_yd', 'original_unit']] = self.df['area'].apply(
                lambda x: pd.Series(extract_area_to_sq_yd(x))
            )

            # Calculate cost per sq yd
            if 'price_pkr' in self.df.columns:
                self.df['cost_per_sq_yd'] = self.df.apply(
                    lambda row: row['price_pkr'] / row['size_sq_yd']
                    if pd.notna(row['price_pkr']) and pd.notna(row['size_sq_yd']) and row['size_sq_yd'] > 0
                    else None,
                    axis=1
                )
        
        # Extract bedrooms count
        if 'bedrooms' in self.df.columns:
            self.df['bed_count'] = self.df['bedrooms'].str.extract(r'(\d+)').astype(float)
        
        # Extract bathrooms count
        if 'bathrooms' in self.df.columns:
            self.df['bath_count'] = self.df['bathrooms'].str.extract(r'(\d+)').astype(float)
    
    def get_price_statistics(self):
        """Calculate price statistics"""
        if 'price_pkr' not in self.df.columns:
            return "Price data not available"
        
        df_with_price = self.df[self.df['price_pkr'].notna()]
        
        stats = {
            'Total Properties': len(self.df),
            'Properties with Price': len(df_with_price),
            'Average Price': f"PKR {df_with_price['price_pkr'].mean():,.0f}",
            'Median Price': f"PKR {df_with_price['price_pkr'].median():,.0f}",
            'Minimum Price': f"PKR {df_with_price['price_pkr'].min():,.0f}",
            'Maximum Price': f"PKR {df_with_price['price_pkr'].max():,.0f}",
            'Price Std Dev': f"PKR {df_with_price['price_pkr'].std():,.0f}"
        }
        
        return stats
    
    def get_cost_per_sq_yd_stats(self):
        """Get statistics for cost per sq yd - the key metric"""
        if 'cost_per_sq_yd' not in self.df.columns:
            return "Cost per sq yd data not available"

        df_with_cost = self.df[self.df['cost_per_sq_yd'].notna()]

        if len(df_with_cost) == 0:
            return "No properties with cost per sq yd data"

        stats = {
            'Properties Analyzed': len(df_with_cost),
            'Avg Cost/Sq Yd': f"PKR {df_with_cost['cost_per_sq_yd'].mean():,.0f}",
            'Median Cost/Sq Yd': f"PKR {df_with_cost['cost_per_sq_yd'].median():,.0f}",
            'Min Cost/Sq Yd': f"PKR {df_with_cost['cost_per_sq_yd'].min():,.0f}",
            'Max Cost/Sq Yd': f"PKR {df_with_cost['cost_per_sq_yd'].max():,.0f}",
        }

        return stats
    
    def analyze_by_bedrooms(self):
        """Analyze properties by number of bedrooms"""
        if 'bed_count' not in self.df.columns or 'price_pkr' not in self.df.columns:
            return "Bedroom or price data not available"
        
        df_with_beds = self.df[self.df['bed_count'].notna() & self.df['price_pkr'].notna()]
        
        results = []
        for beds in sorted(df_with_beds['bed_count'].unique()):
            bed_df = df_with_beds[df_with_beds['bed_count'] == beds]
            results.append({
                'Bedrooms': int(beds),
                'Count': len(bed_df),
                'Avg Price': f"PKR {bed_df['price_pkr'].mean():,.0f}",
                'Min Price': f"PKR {bed_df['price_pkr'].min():,.0f}",
                'Max Price': f"PKR {bed_df['price_pkr'].max():,.0f}"
            })
        
        return pd.DataFrame(results)
    
    def analyze_by_location(self):
        """Analyze properties by location/sector with cost per sq yd"""
        if 'location' not in self.df.columns:
            return "Location data not available"

        df_with_location = self.df[self.df['location'].notna() & self.df['price_pkr'].notna()]

        # Include cost per sq yd if available
        if 'cost_per_sq_yd' in self.df.columns:
            df_filtered = df_with_location[df_with_location['cost_per_sq_yd'].notna()]
            if len(df_filtered) > 0:
                location_stats = df_filtered.groupby('location').agg({
                    'price_pkr': 'count',
                    'cost_per_sq_yd': ['mean', 'min', 'max']
                }).round(0)

                location_stats.columns = ['Count', 'Avg Cost/Sq Yd', 'Min Cost/Sq Yd', 'Max Cost/Sq Yd']
                location_stats = location_stats.sort_values('Avg Cost/Sq Yd', ascending=False)

                # Format prices
                for col in ['Avg Cost/Sq Yd', 'Min Cost/Sq Yd', 'Max Cost/Sq Yd']:
                    location_stats[col] = location_stats[col].apply(lambda x: f"PKR {x:,.0f}")

                return location_stats.head(10)

        # Fallback if no cost per sq yd data
        location_stats = df_with_location.groupby('location').agg({
            'price_pkr': ['count', 'mean']
        }).round(0)

        location_stats.columns = ['Count', 'Avg Price']
        location_stats = location_stats.sort_values('Avg Price', ascending=False)
        location_stats['Avg Price'] = location_stats['Avg Price'].apply(lambda x: f"PKR {x:,.0f}")

        return location_stats.head(10)
    
    def find_best_value(self, budget_min=None, budget_max=None, min_beds=None, target_size=None):
        """Find best value properties based on criteria"""
        df_filtered = self.df[self.df['price_pkr'].notna()].copy()
        
        # Apply filters
        if budget_min:
            df_filtered = df_filtered[df_filtered['price_pkr'] >= budget_min]
        if budget_max:
            df_filtered = df_filtered[df_filtered['price_pkr'] <= budget_max]
        if min_beds and 'bed_count' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['bed_count'] >= min_beds]
        if target_size and 'size_numeric' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['size_numeric'] >= target_size]
        
        if len(df_filtered) == 0:
            return "No properties match your criteria"
        
        # Calculate value score (lower price per sq unit = better value)
        if 'size_numeric' in df_filtered.columns:
            df_filtered['value_score'] = df_filtered['price_pkr'] / df_filtered['size_numeric']
            df_filtered = df_filtered.sort_values('value_score')
        else:
            df_filtered = df_filtered.sort_values('price_pkr')
        
        # Select relevant columns
        columns = ['title', 'price_text', 'area', 'bedrooms', 'location', 'url']
        available_columns = [col for col in columns if col in df_filtered.columns]
        
        return df_filtered[available_columns].head(10)

    def analyze_days_on_market(self):
        """Analyze liquidity via days on market"""
        if 'days_on_market' not in self.df.columns:
            return "Days on market data not available"

        df_filtered = self.df[self.df['days_on_market'].notna()]

        if len(df_filtered) == 0:
            return "No properties with days on market data"

        # Categorize
        df_filtered['market_category'] = pd.cut(
            df_filtered['days_on_market'],
            bins=[0, 7, 30, 90, float('inf')],
            labels=['Fresh (< 1 week)', 'Recent (1-4 weeks)', 'Moderate (1-3 months)', 'Stale (> 3 months)']
        )

        category_counts = df_filtered['market_category'].value_counts().sort_index()

        stats = {
            'Avg Days on Market': f"{df_filtered['days_on_market'].mean():.1f} days",
            'Median Days on Market': f"{df_filtered['days_on_market'].median():.1f} days",
            'Fresh Listings': int(category_counts.get('Fresh (< 1 week)', 0)),
            'Recent Listings': int(category_counts.get('Recent (1-4 weeks)', 0)),
            'Moderate Listings': int(category_counts.get('Moderate (1-3 months)', 0)),
            'Stale Listings': int(category_counts.get('Stale (> 3 months)', 0))
        }

        return stats

    def analyze_amenity_scores(self):
        """Analyze properties by amenity score"""
        if 'amenity_score' not in self.df.columns:
            return "Amenity score data not available"

        df_filtered = self.df[self.df['amenity_score'].notna() & self.df['price_pkr'].notna()]

        if len(df_filtered) == 0:
            return "No properties with amenity score data"

        # Group by amenity score
        amenity_analysis = df_filtered.groupby('amenity_score').agg({
            'price_pkr': ['count', 'mean'],
            'cost_per_sq_yd': 'mean' if 'cost_per_sq_yd' in df_filtered.columns else 'count'
        }).round(0)

        return amenity_analysis

    def get_investment_insights(self):
        """Get investment-focused insights"""
        insights = {}

        # Days on market analysis
        if 'days_on_market' in self.df.columns:
            df_market = self.df[self.df['days_on_market'].notna() & self.df['price_pkr'].notna()]
            if len(df_market) > 0:
                # Properties on market > 90 days might be negotiable
                stale_props = df_market[df_market['days_on_market'] > 90]
                insights['negotiable_opportunities'] = len(stale_props)

                # Fresh listings (high demand indicator)
                fresh_props = df_market[df_market['days_on_market'] < 7]
                insights['hot_market_indicator'] = len(fresh_props)

        # Possession status analysis
        if 'possession_status' in self.df.columns:
            possession_counts = self.df['possession_status'].value_counts()
            insights['ready_properties'] = int(possession_counts.get('Ready', 0))
            insights['under_construction'] = int(possession_counts.get('Under Construction', 0))

        # High amenity properties
        if 'amenity_score' in self.df.columns:
            df_amenity = self.df[self.df['amenity_score'].notna()]
            if len(df_amenity) > 0:
                high_amenity = df_amenity[df_amenity['amenity_score'] >= 4]
                insights['premium_properties'] = len(high_amenity)

        # Agent tier analysis
        if 'agent_tier' in self.df.columns:
            tier_counts = self.df['agent_tier'].value_counts()
            if 'Titanium' in tier_counts.index:
                insights['titanium_agent_listings'] = int(tier_counts['Titanium'])

        return insights

    def create_visualizations(self, output_prefix="charts"):
        """Create simple, WhatsApp-friendly visualizations"""
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['font.size'] = 10

        # Ensure output goes to data directory
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        output_prefix = os.path.join(data_dir, output_prefix)

        created_charts = []

        # Chart 1: Cost per Sq Yd by Location
        if 'cost_per_sq_yd' in self.df.columns and 'location' in self.df.columns:
            df_chart = self.df[self.df['cost_per_sq_yd'].notna() & self.df['location'].notna()]

            if len(df_chart) > 0:
                # Get top 10 locations by average cost
                location_avg = df_chart.groupby('location')['cost_per_sq_yd'].agg(['mean', 'count']).reset_index()
                location_avg = location_avg[location_avg['count'] >= 2]  # At least 2 properties
                location_avg = location_avg.nlargest(10, 'mean')

                if len(location_avg) > 0:
                    plt.figure(figsize=(10, 6))
                    bars = plt.barh(range(len(location_avg)), location_avg['mean'], color='steelblue')
                    plt.yticks(range(len(location_avg)), location_avg['location'])
                    plt.xlabel('Cost per Sq Yd (PKR)', fontsize=12, fontweight='bold')
                    plt.title('Average Cost per Sq Yd by Location', fontsize=14, fontweight='bold')
                    plt.gca().invert_yaxis()

                    # Add value labels
                    for i, (idx, row) in enumerate(location_avg.iterrows()):
                        plt.text(row['mean'], i, f" PKR {row['mean']:,.0f}",
                                va='center', fontsize=9)

                    plt.tight_layout()
                    chart1_file = f"{output_prefix}_cost_by_location.png"
                    plt.savefig(chart1_file, dpi=150, bbox_inches='tight')
                    plt.close()
                    created_charts.append(chart1_file)
                    print(f"✓ Created: {chart1_file}")

        # Chart 2: Price Distribution
        if 'price_pkr' in self.df.columns:
            df_chart = self.df[self.df['price_pkr'].notna()]

            if len(df_chart) > 0:
                plt.figure(figsize=(10, 6))
                plt.hist(df_chart['price_pkr'] / 10000000, bins=20, color='coral', edgecolor='black', alpha=0.7)
                plt.xlabel('Price (Crores PKR)', fontsize=12, fontweight='bold')
                plt.ylabel('Number of Properties', fontsize=12, fontweight='bold')
                plt.title('Property Price Distribution', fontsize=14, fontweight='bold')
                plt.tight_layout()

                chart2_file = f"{output_prefix}_price_distribution.png"
                plt.savefig(chart2_file, dpi=150, bbox_inches='tight')
                plt.close()
                created_charts.append(chart2_file)
                print(f"✓ Created: {chart2_file}")

        # Chart 3: Summary Stats Card
        stats = self.get_price_statistics()
        cost_stats = self.get_cost_per_sq_yd_stats()

        if isinstance(stats, dict):
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.axis('off')

            # Title
            title_text = "Market Summary"
            ax.text(0.5, 0.95, title_text, ha='center', va='top',
                   fontsize=18, fontweight='bold', transform=ax.transAxes)

            # Stats
            y_pos = 0.85
            line_height = 0.08

            # Price stats
            if isinstance(stats, dict):
                ax.text(0.5, y_pos, "Price Statistics", ha='center', va='top',
                       fontsize=14, fontweight='bold', transform=ax.transAxes)
                y_pos -= line_height

                for key, value in stats.items():
                    if key != 'date_scraped':
                        ax.text(0.15, y_pos, f"{key}:", ha='left', va='top',
                               fontsize=11, transform=ax.transAxes)
                        ax.text(0.85, y_pos, f"{value}", ha='right', va='top',
                               fontsize=11, fontweight='bold', transform=ax.transAxes)
                        y_pos -= line_height * 0.8

            # Cost per sq yd stats
            if isinstance(cost_stats, dict):
                y_pos -= line_height * 0.3
                ax.text(0.5, y_pos, "Cost per Sq Yd", ha='center', va='top',
                       fontsize=14, fontweight='bold', transform=ax.transAxes)
                y_pos -= line_height

                for key, value in cost_stats.items():
                    ax.text(0.15, y_pos, f"{key}:", ha='left', va='top',
                           fontsize=11, transform=ax.transAxes)
                    ax.text(0.85, y_pos, f"{value}", ha='right', va='top',
                           fontsize=11, fontweight='bold', transform=ax.transAxes)
                    y_pos -= line_height * 0.8

            plt.tight_layout()
            chart3_file = f"{output_prefix}_summary.png"
            plt.savefig(chart3_file, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            created_charts.append(chart3_file)
            print(f"✓ Created: {chart3_file}")

        # Chart 4: Days on Market Distribution (Investment Metric)
        if 'days_on_market' in self.df.columns:
            df_chart = self.df[self.df['days_on_market'].notna()]

            if len(df_chart) > 0:
                # Categorize
                df_chart['market_category'] = pd.cut(
                    df_chart['days_on_market'],
                    bins=[0, 7, 30, 90, float('inf')],
                    labels=['Fresh\n(< 1 week)', 'Recent\n(1-4 weeks)', 'Moderate\n(1-3 mo)', 'Stale\n(> 3 mo)']
                )

                category_counts = df_chart['market_category'].value_counts().sort_index()

                if len(category_counts) > 0:
                    plt.figure(figsize=(10, 6))
                    colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']  # green to red
                    bars = plt.bar(range(len(category_counts)), category_counts.values, color=colors)
                    plt.xticks(range(len(category_counts)), category_counts.index)
                    plt.ylabel('Number of Properties', fontsize=12, fontweight='bold')
                    plt.title('Market Liquidity - Days on Market', fontsize=14, fontweight='bold')

                    # Add value labels
                    for i, v in enumerate(category_counts.values):
                        plt.text(i, v, str(v), ha='center', va='bottom', fontsize=11, fontweight='bold')

                    plt.tight_layout()
                    chart4_file = f"{output_prefix}_days_on_market.png"
                    plt.savefig(chart4_file, dpi=150, bbox_inches='tight')
                    plt.close()
                    created_charts.append(chart4_file)
                    print(f"✓ Created: {chart4_file}")

        # Chart 5: Investment Insights Card
        insights = self.get_investment_insights()

        if insights:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.axis('off')

            # Title
            ax.text(0.5, 0.95, "Investment Insights", ha='center', va='top',
                   fontsize=18, fontweight='bold', transform=ax.transAxes)

            # Insights
            y_pos = 0.85
            line_height = 0.08

            for key, value in insights.items():
                # Format key
                formatted_key = key.replace('_', ' ').title()

                ax.text(0.15, y_pos, f"{formatted_key}:", ha='left', va='top',
                       fontsize=11, transform=ax.transAxes)
                ax.text(0.85, y_pos, f"{value}", ha='right', va='top',
                       fontsize=11, fontweight='bold', transform=ax.transAxes)
                y_pos -= line_height * 0.9

            # Add interpretation
            y_pos -= line_height * 0.5
            ax.text(0.5, y_pos, "Investment Tips", ha='center', va='top',
                   fontsize=12, fontweight='bold', transform=ax.transAxes, color='#2c3e50')
            y_pos -= line_height * 0.8

            tips = []
            if insights.get('negotiable_opportunities', 0) > 0:
                tips.append(f"• {insights['negotiable_opportunities']} stale listings may accept lower offers")
            if insights.get('hot_market_indicator', 0) > 0:
                tips.append(f"• {insights['hot_market_indicator']} fresh listings indicate high demand")
            if insights.get('premium_properties', 0) > 0:
                tips.append(f"• {insights['premium_properties']} premium properties with 4+ amenities")

            for tip in tips[:3]:  # Max 3 tips
                ax.text(0.1, y_pos, tip, ha='left', va='top',
                       fontsize=9, transform=ax.transAxes, wrap=True)
                y_pos -= line_height * 0.7

            plt.tight_layout()
            chart5_file = f"{output_prefix}_investment_insights.png"
            plt.savefig(chart5_file, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            created_charts.append(chart5_file)
            print(f"✓ Created: {chart5_file}")

        return created_charts

    def generate_report(self, output_file=None):
        """Generate comprehensive analysis report"""
        # Ensure output goes to data directory
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)

        if output_file is None:
            output_file = f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        filepath = os.path.join(data_dir, output_file)
        
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            # Write original data
            self.df.to_excel(writer, sheet_name='Raw Data', index=False)

            # Price statistics
            price_stats = pd.DataFrame([self.get_price_statistics()]).T
            price_stats.to_excel(writer, sheet_name='Price Statistics')

            # Cost per sq yd statistics
            cost_stats = self.get_cost_per_sq_yd_stats()
            if isinstance(cost_stats, dict):
                cost_df = pd.DataFrame([cost_stats]).T
                cost_df.to_excel(writer, sheet_name='Cost per Sq Yd')

            # Bedroom analysis
            bedroom_analysis = self.analyze_by_bedrooms()
            if isinstance(bedroom_analysis, pd.DataFrame):
                bedroom_analysis.to_excel(writer, sheet_name='By Bedrooms', index=False)

            # Location analysis
            location_analysis = self.analyze_by_location()
            if isinstance(location_analysis, pd.DataFrame):
                location_analysis.to_excel(writer, sheet_name='By Location')

            # Format sheets
            workbook = writer.book
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BD'})

            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                worksheet.set_column('A:Z', 20)
        
        print(f"\nAnalysis report saved to: {filepath}")
        return filepath


def main():
    """Main analysis function"""
    print("=" * 60)
    print("Real Estate Market Analysis Tool")
    print("=" * 60)

    # Find Excel files in data directory
    data_dir = "data"
    excel_files = glob.glob(os.path.join(data_dir, '*.xlsx'))
    # Filter out analysis reports and temp files
    excel_files = [f for f in excel_files
                   if not os.path.basename(f).startswith('analysis_report')
                   and not os.path.basename(f).startswith('~$')]

    if not excel_files:
        print("\n⚠ No scraped data files found in 'data' folder!")
        print("Please run zameen_scraper.py first to collect data.")
        return

    # Let user choose or use most recent
    if len(excel_files) == 1:
        latest_file = excel_files[0]
    else:
        latest_file = max(excel_files, key=os.path.getmtime)

    print(f"\nAnalyzing: {latest_file}")

    # Create analyzer
    analyzer = RealEstateAnalyzer(latest_file)

    print("\n" + "=" * 60)
    print("PRICE STATISTICS")
    print("=" * 60)
    stats = analyzer.get_price_statistics()
    if isinstance(stats, dict):
        for key, value in stats.items():
            print(f"{key}: {value}")
    else:
        print(stats)

    print("\n" + "=" * 60)
    print("COST PER SQ YD ANALYSIS")
    print("=" * 60)
    cost_stats = analyzer.get_cost_per_sq_yd_stats()
    if isinstance(cost_stats, dict):
        for key, value in cost_stats.items():
            print(f"{key}: {value}")
    else:
        print(cost_stats)

    print("\n" + "=" * 60)
    print("TOP LOCATIONS")
    print("=" * 60)
    location_analysis = analyzer.analyze_by_location()
    if isinstance(location_analysis, pd.DataFrame):
        print(location_analysis.to_string())
    else:
        print(location_analysis)

    # Investment insights (if detailed data available)
    print("\n" + "=" * 60)
    print("INVESTMENT INSIGHTS")
    print("=" * 60)

    # Days on market
    market_stats = analyzer.analyze_days_on_market()
    if isinstance(market_stats, dict):
        for key, value in market_stats.items():
            print(f"{key}: {value}")
    else:
        print(market_stats)

    # General investment insights
    insights = analyzer.get_investment_insights()
    if insights:
        print("\nKey Insights:")
        for key, value in insights.items():
            formatted_key = key.replace('_', ' ').title()
            print(f"  • {formatted_key}: {value}")

    # Generate visualizations
    print("\n" + "=" * 60)
    print("Creating visualizations for WhatsApp...")
    print("=" * 60)
    charts = analyzer.create_visualizations()

    # Generate comprehensive report
    print("\n" + "=" * 60)
    print("Generating comprehensive Excel report...")
    report_file = analyzer.generate_report()

    print("\n" + "=" * 60)
    print("✓ Analysis complete!")
    print(f"✓ Excel report: {report_file}")
    if charts:
        print(f"✓ Created {len(charts)} charts:")
        for chart in charts:
            print(f"  - {chart}")
    print("\n" + "💡 Share the PNG charts on WhatsApp!")
    print("=" * 60)

    return report_file, charts


if __name__ == "__main__":
    main()
