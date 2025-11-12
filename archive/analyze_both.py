"""
Analyze both Houses and Plots data
"""

from analyze_data import RealEstateAnalyzer
import os

def analyze_file(filepath, property_type):
    """Analyze a single file"""
    print("\n" + "=" * 70)
    print(f"ANALYZING: {property_type}")
    print("=" * 70)
    print(f"File: {os.path.basename(filepath)}")

    analyzer = RealEstateAnalyzer(filepath)

    # Price statistics
    print("\n" + "-" * 70)
    print("PRICE STATISTICS")
    print("-" * 70)
    stats = analyzer.get_price_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Cost per sq yd
    print("\n" + "-" * 70)
    print("COST PER SQ YD ANALYSIS")
    print("-" * 70)
    cost_stats = analyzer.get_cost_per_sq_yd_stats()
    if isinstance(cost_stats, dict):
        for key, value in cost_stats.items():
            print(f"  {key}: {value}")

    # Investment insights
    market_stats = analyzer.analyze_days_on_market()
    if isinstance(market_stats, dict):
        print("\n" + "-" * 70)
        print("MARKET INSIGHTS")
        print("-" * 70)
        for key, value in market_stats.items():
            print(f"  {key}: {value}")

    # Generate report
    print("\n" + "-" * 70)
    print("GENERATING REPORTS...")
    print("-" * 70)

    # Customize output names
    base_name = os.path.basename(filepath).replace('.xlsx', '')
    report_file = analyzer.generate_report(output_file=f"analysis_{base_name}.xlsx")
    charts = analyzer.create_visualizations(output_prefix=f"charts_{base_name}")

    print(f"  ✓ Excel report: {report_file}")
    print(f"  ✓ Created {len(charts)} charts")

    return {
        'type': property_type,
        'count': len(analyzer.df),
        'report': report_file,
        'charts': len(charts)
    }

def main():
    print("=" * 70)
    print("ZAMEEN.COM DATA ANALYSIS - BAHRIA TOWN PRECINCT 8")
    print("=" * 70)

    data_dir = "data"

    files_to_analyze = [
        (os.path.join(data_dir, 'precinct_8_houses_20251110_152922.xlsx'), 'Houses'),
        (os.path.join(data_dir, 'precinct_8_plots_20251110_152955.xlsx'), 'Residential Plots')
    ]

    results = []

    for filepath, prop_type in files_to_analyze:
        if os.path.exists(filepath):
            result = analyze_file(filepath, prop_type)
            results.append(result)
        else:
            print(f"\n⚠ File not found: {filepath}")

    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    for result in results:
        print(f"\n{result['type']}:")
        print(f"  Properties analyzed: {result['count']}")
        print(f"  Report saved: {result['report']}")
        print(f"  Charts created: {result['charts']}")

    print("\n" + "=" * 70)
    print("✓ All analysis complete!")
    print("✓ Check the 'data/' folder for:")
    print("  - Excel reports (analysis_*.xlsx)")
    print("  - PNG charts (charts_*.png)")
    print("=" * 70)

if __name__ == "__main__":
    main()
