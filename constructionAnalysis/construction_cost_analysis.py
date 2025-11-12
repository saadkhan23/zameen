"""
Construction Cost Analysis for Bahria Town
Calculates implied construction costs by comparing plot and house prices
"""

import pandas as pd
import os
import glob
from datetime import datetime

class ConstructionCostAnalyzer:
    def __init__(self, data_folder=None):
        """Initialize with path to data folder"""
        if data_folder is None:
            # Get the script's directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to zameen folder
            zameen_dir = os.path.dirname(script_dir)
            data_folder = os.path.join(zameen_dir, "data")
        elif not os.path.isabs(data_folder):
            # Make relative paths absolute from script location
            script_dir = os.path.dirname(os.path.abspath(__file__))
            zameen_dir = os.path.dirname(script_dir)
            data_folder = os.path.join(zameen_dir, data_folder)

        self.data_folder = os.path.abspath(data_folder)
        self.locations = {}
        self.construction_costs = []

    def load_location_data(self, location_folder):
        """Load latest houses and plots data from a location folder"""
        location_name = os.path.basename(location_folder)

        # Find the most recent run folder
        run_folders = glob.glob(os.path.join(location_folder, "*/"))
        if not run_folders:
            print(f"  ⚠ No run folders found in {location_name}")
            return None

        latest_run = max(run_folders, key=os.path.getmtime)

        # Load houses and plots
        houses_file = os.path.join(latest_run, "houses.xlsx")
        plots_file = os.path.join(latest_run, "plots.xlsx")

        data = {}

        if os.path.exists(houses_file):
            try:
                houses_df = pd.read_excel(houses_file, sheet_name="Properties")
                data['houses'] = houses_df
                print(f"  ✓ Loaded {len(houses_df)} houses")
            except Exception as e:
                print(f"  ⚠ Error loading houses: {e}")

        if os.path.exists(plots_file):
            try:
                plots_df = pd.read_excel(plots_file, sheet_name="Properties")
                data['plots'] = plots_df
                print(f"  ✓ Loaded {len(plots_df)} plots")
            except Exception as e:
                print(f"  ⚠ Error loading plots: {e}")

        if data:
            self.locations[location_name] = data
            return data
        return None

    def load_all_locations(self):
        """Load data from all location folders"""
        print("=" * 70)
        print("LOADING DATA FROM ALL LOCATIONS")
        print("=" * 70)

        # Get all subdirectories in data folder
        location_folders = []
        for item in os.listdir(self.data_folder):
            item_path = os.path.join(self.data_folder, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                location_folders.append(item_path)

        if not location_folders:
            print(f"\n⚠ No location folders found in {self.data_folder}")
            return False

        for location_folder in sorted(location_folders):
            location_name = os.path.basename(location_folder.rstrip("/"))
            print(f"\n{location_name}:")
            self.load_location_data(location_folder)

        return len(self.locations) > 0

    def calculate_construction_costs(self):
        """Calculate implied construction costs for each location"""
        print("\n" + "=" * 70)
        print("CALCULATING CONSTRUCTION COSTS")
        print("=" * 70)

        for location_name, data in self.locations.items():
            print(f"\n{location_name}:")

            if 'houses' not in data or 'plots' not in data:
                print("  ⚠ Missing houses or plots data")
                continue

            houses = data['houses']
            plots = data['plots']

            # Calculate median values
            median_house_price = houses['price_pkr'].median()
            median_house_sqyd = houses['area_sqyd'].median()
            median_plot_price = plots['price_pkr'].median()
            median_plot_sqyd = plots['area_sqyd'].median()

            # Calculate construction cost (assuming similar sizes)
            if median_house_sqyd > 0 and median_plot_sqyd > 0:
                # Normalize to same size (use average of both)
                avg_sqyd = (median_house_sqyd + median_plot_sqyd) / 2

                # Adjust prices to same size
                adjusted_house_price = median_house_price * (avg_sqyd / median_house_sqyd)
                adjusted_plot_price = median_plot_price * (avg_sqyd / median_plot_sqyd)

                construction_cost = adjusted_house_price - adjusted_plot_price
                construction_cost_per_sqyd = construction_cost / avg_sqyd

                # Calculate house and plot costs per sq yd for comparison
                house_cost_per_sqyd = houses['cost_per_sq_yd'].median()
                plot_cost_per_sqyd = plots['cost_per_sq_yd'].median()

                result = {
                    'location': location_name,
                    'median_house_price': median_house_price,
                    'median_plot_price': median_plot_price,
                    'house_cost_per_sqyd': house_cost_per_sqyd,
                    'plot_cost_per_sqyd': plot_cost_per_sqyd,
                    'implied_construction_cost': construction_cost,
                    'construction_cost_per_sqyd': construction_cost_per_sqyd,
                    'house_count': len(houses),
                    'plot_count': len(plots),
                    'avg_normalized_sqyd': avg_sqyd
                }

                self.construction_costs.append(result)

                print(f"  Median House Price: PKR {median_house_price:,.0f}")
                print(f"  Median Plot Price:  PKR {median_plot_price:,.0f}")
                print(f"  House Cost/Sq Yd:   PKR {house_cost_per_sqyd:,.0f}")
                print(f"  Plot Cost/Sq Yd:    PKR {plot_cost_per_sqyd:,.0f}")
                print(f"  Implied Construction Cost: PKR {construction_cost:,.0f}")
                print(f"  Construction Cost/Sq Yd:   PKR {construction_cost_per_sqyd:,.0f}")

    def print_comparison(self):
        """Print side-by-side comparison of all locations"""
        if not self.construction_costs:
            print("\n⚠ No construction cost data to compare")
            return

        print("\n" + "=" * 70)
        print("LOCATION COMPARISON")
        print("=" * 70)

        df = pd.DataFrame(self.construction_costs)

        # Sort by construction cost per sq yd
        df = df.sort_values('construction_cost_per_sqyd', ascending=False)

        print("\n📊 Construction Costs Ranked (Highest to Lowest):")
        print("-" * 70)

        for idx, row in df.iterrows():
            print(f"\n{row['location'].replace('_', ' ').title()}:")
            print(f"  House Median Price:     PKR {row['median_house_price']:>12,.0f}")
            print(f"  Plot Median Price:      PKR {row['median_plot_price']:>12,.0f}")
            print(f"  Construction Cost:      PKR {row['implied_construction_cost']:>12,.0f}")
            print(f"  ├─ Per Sq Yd:          PKR {row['construction_cost_per_sqyd']:>12,.0f}")
            print(f"  ├─ House Cost/Sq Yd:   PKR {row['house_cost_per_sqyd']:>12,.0f}")
            print(f"  └─ Plot Cost/Sq Yd:    PKR {row['plot_cost_per_sqyd']:>12,.0f}")
            print(f"  Data: {row['house_count']} houses, {row['plot_count']} plots")

        # Key insights
        print("\n" + "=" * 70)
        print("KEY INSIGHTS")
        print("=" * 70)

        max_construction = df.iloc[0]
        min_construction = df.iloc[-1]

        print(f"\n💰 Most Expensive Construction:")
        print(f"  {max_construction['location'].replace('_', ' ').title()}")
        print(f"  PKR {max_construction['construction_cost_per_sqyd']:,.0f}/sq yd")

        print(f"\n💰 Least Expensive Construction:")
        print(f"  {min_construction['location'].replace('_', ' ').title()}")
        print(f"  PKR {min_construction['construction_cost_per_sqyd']:,.0f}/sq yd")

        price_diff = max_construction['construction_cost_per_sqyd'] - min_construction['construction_cost_per_sqyd']
        pct_diff = (price_diff / min_construction['construction_cost_per_sqyd']) * 100

        print(f"\n📈 Difference: PKR {price_diff:,.0f}/sq yd ({pct_diff:.1f}%)")

        # House vs Plot cost comparison
        print(f"\n🏠 House/Plot Cost Ratio by Location:")
        df['house_plot_ratio'] = df['house_cost_per_sqyd'] / df['plot_cost_per_sqyd']
        for idx, row in df.sort_values('house_plot_ratio', ascending=False).iterrows():
            print(f"  {row['location'].replace('_', ' ').title()}: {row['house_plot_ratio']:.2f}x")

        return df

    def save_analysis(self, output_file="construction_cost_analysis.csv"):
        """Save analysis to CSV with readable formatting"""
        if not self.construction_costs:
            print("⚠ No data to save")
            return

        df = pd.DataFrame(self.construction_costs)

        # Format location names (remove underscores, title case)
        df['location'] = df['location'].str.replace('_', ' ').str.title()

        # Reorder columns for clarity
        df = df[['location', 'house_count', 'plot_count', 'median_house_price',
                 'median_plot_price', 'house_cost_per_sqyd', 'plot_cost_per_sqyd',
                 'implied_construction_cost', 'construction_cost_per_sqyd', 'avg_normalized_sqyd']]

        # Round numeric columns for readability
        df['median_house_price'] = df['median_house_price'].round(0).astype(int).apply(lambda x: f"{x:,}")
        df['median_plot_price'] = df['median_plot_price'].round(0).astype(int).apply(lambda x: f"{x:,}")
        df['house_cost_per_sqyd'] = df['house_cost_per_sqyd'].round(0).astype(int).apply(lambda x: f"{x:,}")
        df['plot_cost_per_sqyd'] = df['plot_cost_per_sqyd'].round(0).astype(int).apply(lambda x: f"{x:,}")
        df['implied_construction_cost'] = df['implied_construction_cost'].round(0).astype(int).apply(lambda x: f"{x:,}")
        df['construction_cost_per_sqyd'] = df['construction_cost_per_sqyd'].round(0).astype(int).apply(lambda x: f"{x:,}")
        df['avg_normalized_sqyd'] = df['avg_normalized_sqyd'].round(1)

        df.to_csv(output_file, index=False)
        print(f"\n✓ Analysis saved to: {output_file}")
        print(f"\nCSV Preview:")
        print(df.to_string(index=False))
        return df

def main():
    print("=" * 70)
    print("BAHRIA TOWN CONSTRUCTION COST ANALYSIS")
    print("=" * 70)

    analyzer = ConstructionCostAnalyzer()

    # Load all location data
    if not analyzer.load_all_locations():
        print("\n⚠ No data found. Please run scraper first.")
        return

    # Calculate construction costs
    analyzer.calculate_construction_costs()

    # Print comparison
    comparison_df = analyzer.print_comparison()

    # Save to CSV in constructionAnalysis folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "construction_cost_analysis.csv")
    analyzer.save_analysis(csv_path)

    print("\n" + "=" * 70)
    print("✓ Analysis complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
