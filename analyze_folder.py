"""
Analyze data within a specific run folder
"""

import sys
import glob
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'archive'))
from analyze_data import RealEstateAnalyzer

def analyze_file(filepath, output_folder):
    """Analyze a single file and save outputs to the same folder"""
    basename = os.path.basename(filepath)
    property_type = basename.replace('.xlsx', '').replace('_', ' ').title()

    print("\n" + "=" * 70)
    print(f"ANALYZING: {property_type}")
    print("=" * 70)
    print(f"Source: {basename}")

    analyzer = RealEstateAnalyzer(filepath)

    # Price statistics
    print("\n" + "-" * 70)
    print("PRICE STATISTICS")
    print("-" * 70)
    stats = analyzer.get_price_statistics()
    if isinstance(stats, dict):
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print(f"  {stats}")

    # Cost per sq yd
    print("\n" + "-" * 70)
    print("COST PER SQ YD ANALYSIS")
    print("-" * 70)
    cost_stats = analyzer.get_cost_per_sq_yd_stats()
    if isinstance(cost_stats, dict):
        for key, value in cost_stats.items():
            print(f"  {key}: {value}")
    else:
        print(f"  {cost_stats}")

    # Investment insights
    market_stats = analyzer.analyze_days_on_market()
    if isinstance(market_stats, dict):
        print("\n" + "-" * 70)
        print("MARKET INSIGHTS")
        print("-" * 70)
        for key, value in market_stats.items():
            print(f"  {key}: {value}")
    else:
        if market_stats:
            print(f"  {market_stats}")

    # Generate report in the same folder
    print("\n" + "-" * 70)
    print("GENERATING REPORTS...")
    print("-" * 70)

    # Get base name without extension
    base_name = os.path.splitext(basename)[0]

    # Update analyzer to save to output folder
    original_create_viz = analyzer.create_visualizations
    original_generate_report = analyzer.generate_report

    # Monkey patch to save in the correct folder
    def patched_create_viz(output_prefix="charts"):
        output_prefix = os.path.join(output_folder, f"charts_{base_name}")
        # Temporarily change the method
        data_dir_backup = None
        charts = []

        # Call original but override the path construction
        import matplotlib.pyplot as plt
        import seaborn as sns
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['font.size'] = 10

        created_charts = []

        # Chart 1: Cost per Sq Yd by Location
        if 'cost_per_sq_yd' in analyzer.df.columns and 'location' in analyzer.df.columns:
            df_chart = analyzer.df[analyzer.df['cost_per_sq_yd'].notna() & analyzer.df['location'].notna()]

            if len(df_chart) > 0:
                # Group by location and get stats
                location_stats = df_chart.groupby('location')['cost_per_sq_yd'].agg(['mean', 'count'])
                location_stats = location_stats.sort_values('mean', ascending=False).head(10)

                if len(location_stats) > 0:
                    plt.figure(figsize=(10, 6))
                    plt.bar(range(len(location_stats)), location_stats['mean'], color='steelblue')
                    plt.xlabel('Location')
                    plt.ylabel('Cost per Sq Yd (PKR)')
                    plt.title('Average Cost per Sq Yd by Location')
                    plt.xticks(range(len(location_stats)), location_stats.index, rotation=45, ha='right')
                    plt.tight_layout()
                    chart1_file = f"{output_prefix}_cost_by_location.png"
                    plt.savefig(chart1_file, dpi=150, bbox_inches='tight')
                    plt.close()
                    created_charts.append(chart1_file)
                    print(f"✓ Created: {os.path.basename(chart1_file)}")

        # Chart 2: Price Distribution
        if 'price_pkr' in analyzer.df.columns:
            df_chart = analyzer.df[analyzer.df['price_pkr'].notna()]

            if len(df_chart) > 0:
                plt.figure(figsize=(10, 6))
                plt.hist(df_chart['price_pkr'] / 1000000, bins=20, color='steelblue', edgecolor='black')
                plt.xlabel('Price (Million PKR)')
                plt.ylabel('Number of Properties')
                plt.title('Price Distribution')
                plt.tight_layout()

                chart2_file = f"{output_prefix}_price_distribution.png"
                plt.savefig(chart2_file, dpi=150, bbox_inches='tight')
                plt.close()
                created_charts.append(chart2_file)
                print(f"✓ Created: {os.path.basename(chart2_file)}")

        # Chart 3: Summary Stats Card
        stats = analyzer.get_price_statistics()
        cost_stats = analyzer.get_cost_per_sq_yd_stats()

        if isinstance(stats, dict):
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.axis('off')

            summary_text = "MARKET SUMMARY\n\n"
            summary_text += f"Total Properties: {stats.get('Total Properties', 'N/A')}\n\n"
            summary_text += f"Average Price: {stats.get('Average Price', 'N/A')}\n"
            summary_text += f"Median Price: {stats.get('Median Price', 'N/A')}\n\n"

            if isinstance(cost_stats, dict):
                summary_text += f"Avg Cost/Sq Yd: {cost_stats.get('Avg Cost/Sq Yd', 'N/A')}\n"
                summary_text += f"Median Cost/Sq Yd: {cost_stats.get('Median Cost/Sq Yd', 'N/A')}\n"

            ax.text(0.5, 0.5, summary_text,
                   ha='center', va='center',
                   fontsize=14,
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

            plt.tight_layout()
            chart3_file = f"{output_prefix}_summary.png"
            plt.savefig(chart3_file, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            created_charts.append(chart3_file)
            print(f"✓ Created: {os.path.basename(chart3_file)}")

        return created_charts

    def patched_generate_report(output_file=None):
        if output_file is None:
            output_file = f"analysis_{base_name}.xlsx"

        filepath = os.path.join(output_folder, output_file)

        import pandas as pd
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            # Write original data
            analyzer.df.to_excel(writer, sheet_name='Raw Data', index=False)

            # Price statistics
            price_stats = pd.DataFrame([analyzer.get_price_statistics()]).T
            price_stats.to_excel(writer, sheet_name='Price Statistics')

            # Cost per sq yd statistics
            cost_stats = analyzer.get_cost_per_sq_yd_stats()
            if isinstance(cost_stats, dict):
                cost_df = pd.DataFrame([cost_stats]).T
                cost_df.to_excel(writer, sheet_name='Cost per Sq Yd')

            # Bedroom analysis
            bedroom_analysis = analyzer.analyze_by_bedrooms()
            if isinstance(bedroom_analysis, pd.DataFrame):
                bedroom_analysis.to_excel(writer, sheet_name='By Bedrooms', index=False)

            # Location analysis
            location_analysis = analyzer.analyze_by_location()
            if isinstance(location_analysis, pd.DataFrame):
                location_analysis.to_excel(writer, sheet_name='By Location')

            # Construction bottom-up cost inputs (new sheet)
            construction_data = [
                ['Component',        'Unit',      'Quantity', 'Unit Cost (PKR)', 'Subtotal (PKR)',        'Notes'],
                ['Bricks',          '1000',      55,         18000,              '=C2*D2',                 'https://portal.karandaaz.com.pk/category/commodities/2012'],
                ['Cement',          '50kg bag',  350,        1388,               '=C3*D3',                 'PBS weekly, Nov 2025'],
                ['Steel',           'ton',       4.5,        230000,             '=C4*D4',                 'Estimate'],
                ['Sand',            'cubic ft',  1500,       90,                 '=C5*D5',                 'Estimate'],
                ['Crush/Gravel',    'cubic ft',  800,        135,                '=C6*D6',                 'Estimate'],
                ['Labor',           'sq ft',     1000,       450,                '=C7*D7',                 'Estimate'],
                ['Plumbing/Electric','lump sum', 1,          300000,             '=C8*D8',                 'Estimate'],
                ['Flooring/Marble', 'sq ft',     1000,       300,                '=C9*D9',                 'Estimate'],
                ['Paint/Finishing', 'sq ft',     1000,       200,                '=C10*D10',               'Estimate'],
                ['Miscellaneous',   '-',         1,          150000,             '=C11*D11',               'Contingency/Transport'],
            ]
            construction_df = pd.DataFrame(construction_data[1:], columns=construction_data[0])
            construction_df.to_excel(writer, sheet_name='Construction_Inputs', index=False)
            # Add total formula below the table
            worksheet = writer.sheets['Construction_Inputs']
            worksheet.write(f'E{len(construction_df)+2}', f'=SUM(E2:E{len(construction_df)+1})')
            worksheet.write(f'D{len(construction_df)+2}', 'TOTAL:')

        print(f"✓ Excel report: {os.path.basename(filepath)}")
        return filepath

    # Generate outputs
    report_file = patched_generate_report()
    charts = patched_create_viz()

    return {
        'type': property_type,
        'count': len(analyzer.df),
        'report': report_file,
        'charts': len(charts)
    }

def main(folder_path=None):
    print("=" * 70)
    print("ZAMEEN.COM DATA ANALYSIS - FOLDER ANALYZER")
    print("=" * 70)

    # Get folder path
    if folder_path is None:
        if len(sys.argv) > 1:
            folder_path = sys.argv[1]
        else:
            # Find most recent folder in data/
            data_folders = glob.glob("data/*/")
            if not data_folders:
                print("\n⚠ No data folders found!")
                print("Usage: python3 analyze_folder.py <folder_path>")
                return
            folder_path = max(data_folders, key=os.path.getmtime).rstrip('/')

    print(f"\nAnalyzing folder: {folder_path}")

    # Find all Excel files in the folder (except analysis reports)
    excel_files = glob.glob(os.path.join(folder_path, '*.xlsx'))
    excel_files = [f for f in excel_files
                   if not os.path.basename(f).startswith('analysis_')
                   and not os.path.basename(f).startswith('~$')]

    if not excel_files:
        print(f"\n⚠ No data files found in {folder_path}")
        return

    print(f"Found {len(excel_files)} data file(s) to analyze")

    results = []

    for filepath in excel_files:
        try:
            result = analyze_file(filepath, folder_path)
            results.append(result)
        except Exception as e:
            print(f"\n⚠ Error analyzing {os.path.basename(filepath)}: {e}")

    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    for result in results:
        print(f"\n{result['type']}:")
        print(f"  Properties: {result['count']}")
        print(f"  Report: {os.path.basename(result['report'])}")
        print(f"  Charts: {result['charts']}")

    print(f"\n✓ All outputs saved to: {folder_path}")
    print("=" * 70)

if __name__ == "__main__":
    main()
