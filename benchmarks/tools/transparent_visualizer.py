#!/usr/bin/env python3
"""
Enhanced Transparent Visualization System

Generates feature-by-feature performance comparison charts and reports
for transparent framework benchmarking.
"""

import json
import os
import sys
import glob
import argparse
from datetime import datetime
from typing import Dict, List, Any
import traceback

try:
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import seaborn as sns
except ImportError as e:
    print(f"❌ Required packages not installed. Install with: pip install matplotlib pandas seaborn numpy: {e}")
    sys.exit(1)

# Set matplotlib style for better looking charts
plt.style.use('default')
sns.set_palette("husl")

class TransparentBenchmarkVisualizer:
    """Enhanced visualizer for transparent feature-by-feature comparison"""

    def __init__(self, results_dir: str):
        self.results_dir = results_dir
        self.summary_data = None
        self.categories = {}

    def load_transparent_data(self) -> bool:
        """Load data from the new transparent benchmark structure"""
        try:
            summary_file = os.path.join(self.results_dir, 'benchmark_summary.json')
            if not os.path.exists(summary_file):
                print(f"❌ No benchmark summary found: {summary_file}")
                print("💡 Run benchmarks first with the enhanced runner")
                return False

            with open(summary_file, 'r') as f:
                self.summary_data = json.load(f)

            # Extract categories from new structure
            if "categories" in self.summary_data:
                self.categories = self.summary_data["categories"]
                total_results = sum(len(cat.get("results", [])) for cat in self.categories.values())
                print(f"✅ Loaded {len(self.categories)} categories with {total_results} total results")
                return True
            else:
                print("❌ No categories found in summary data")
                return False

        except Exception as e:
            print(f"❌ Error loading transparent data: {e}")
            traceback.print_exc()
            return False

    def prepare_category_dataframe(self, category: str) -> pd.DataFrame:
        """Convert category data to pandas DataFrame"""
        if category not in self.categories:
            raise ValueError(f"Category '{category}' not found")

        category_data = self.categories[category]
        results = category_data.get("results", [])

        if not results:
            raise ValueError(f"No results found for category '{category}'")

        processed_data = []
        for item in results:
            # Extract numeric RPS
            rps_str = item.get('requests_per_sec', '0')
            try:
                if 'k' in str(rps_str).lower():
                    rps = float(str(rps_str).lower().replace('k', '')) * 1000
                else:
                    rps = float(str(rps_str).replace(',', ''))
            except (ValueError, TypeError):
                rps = 0

            # Extract latency
            avg_latency_str = item.get('avg_latency', '0ms')
            try:
                avg_latency = float(str(avg_latency_str).replace('ms', '').replace('us', ''))
                if 'us' in str(avg_latency_str):
                    avg_latency = avg_latency / 1000
            except (ValueError, TypeError):
                avg_latency = 0

            processed_data.append({
                'framework': item.get('framework', 'unknown'),
                'endpoint_name': item.get('endpoint_name', 'unknown'),
                'endpoint': item.get('endpoint', '/'),
                'category': category,
                'requests_per_sec': rps,
                'avg_latency_ms': avg_latency,
                'method': item.get('method', 'GET'),
                'timestamp': item.get('timestamp', '')
            })

        return pd.DataFrame(processed_data)

    def create_category_performance_chart(self, category: str, save_path: str):
        """Create performance chart for a specific category"""
        try:
            df = self.prepare_category_dataframe(category)

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

            # RPS comparison
            pivot_rps = df.groupby(['endpoint_name', 'framework'])['requests_per_sec'].mean().unstack(fill_value=0)
            pivot_rps.plot(kind='bar', ax=ax1, width=0.8)
            ax1.set_title(f'🚀 {category.title()} - Requests per Second', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Endpoint')
            ax1.set_ylabel('Requests per Second')
            ax1.legend(title='Framework', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax1.tick_params(axis='x', rotation=45)

            # Add value labels on bars
            for container in ax1.containers:
                ax1.bar_label(container, fmt='%.0f', rotation=90, fontsize=8)

            # Latency comparison
            pivot_latency = df.groupby(['endpoint_name', 'framework'])['avg_latency_ms'].mean().unstack(fill_value=0)
            pivot_latency.plot(kind='bar', ax=ax2, width=0.8)
            ax2.set_title(f'⚡ {category.title()} - Response Latency', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Endpoint')
            ax2.set_ylabel('Latency (ms)')
            ax2.legend(title='Framework', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax2.tick_params(axis='x', rotation=45)

            # Add value labels on bars
            for container in ax2.containers:
                ax2.bar_label(container, fmt='%.1f', rotation=90, fontsize=8)

            plt.tight_layout()
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✅ Category chart saved: {save_path}")

        except Exception as e:
            print(f"❌ Error creating category chart for {category}: {e}")
            traceback.print_exc()

    def create_catzilla_advantage_chart(self, category: str, save_path: str):
        """Create chart showing Catzilla's advantage over other frameworks"""
        try:
            df = self.prepare_category_dataframe(category)

            # Calculate average RPS per framework
            framework_avg = df.groupby('framework')['requests_per_sec'].mean()

            if 'catzilla' not in framework_avg:
                print(f"⚠️  Catzilla data not found for {category}")
                return

            catzilla_rps = framework_avg['catzilla']
            advantages = {}

            for framework, rps in framework_avg.items():
                if framework != 'catzilla' and rps > 0:
                    advantage_percent = ((catzilla_rps - rps) / rps) * 100
                    advantages[framework] = advantage_percent

            if not advantages:
                print(f"⚠️  No comparison data available for {category}")
                return

            # Create advantage chart
            plt.figure(figsize=(10, 6))
            frameworks = list(advantages.keys())
            advantage_values = list(advantages.values())

            colors = ['green' if x > 0 else 'red' for x in advantage_values]
            bars = plt.bar(frameworks, advantage_values, color=colors, alpha=0.7)

            plt.title(f'🎯 Catzilla Advantage - {category.title()}', fontsize=16, fontweight='bold')
            plt.xlabel('Competing Framework')
            plt.ylabel('Performance Advantage (%)')
            plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)

            # Add value labels on bars
            for bar, value in zip(bars, advantage_values):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + (5 if height > 0 else -15),
                        f'{value:+.1f}%', ha='center', va='bottom' if height > 0 else 'top',
                        fontweight='bold')

            plt.tight_layout()
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✅ Advantage chart saved: {save_path}")

        except Exception as e:
            print(f"❌ Error creating advantage chart for {category}: {e}")
            traceback.print_exc()

    def create_overall_comparison_chart(self, save_path: str):
        """Create overall comparison across all categories"""
        try:
            all_data = []
            for category, data in self.categories.items():
                try:
                    df = self.prepare_category_dataframe(category)
                    category_avg = df.groupby('framework')['requests_per_sec'].mean().reset_index()
                    category_avg['category'] = category
                    all_data.append(category_avg)
                except Exception as e:
                    print(f"⚠️  Skipping {category}: {e}")
                    continue

            if not all_data:
                print("❌ No data available for overall comparison")
                return

            combined_df = pd.concat(all_data, ignore_index=True)

            # Create grouped bar chart
            pivot_overall = combined_df.pivot(index='category', columns='framework', values='requests_per_sec')

            plt.figure(figsize=(14, 8))
            ax = pivot_overall.plot(kind='bar', width=0.8)

            plt.title('🏆 Overall Framework Performance Comparison', fontsize=16, fontweight='bold')
            plt.xlabel('Feature Category')
            plt.ylabel('Average Requests per Second')
            plt.legend(title='Framework', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(rotation=45)

            # Add value labels
            for container in ax.containers:
                ax.bar_label(container, fmt='%.0f', rotation=90, fontsize=8)

            plt.tight_layout()
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✅ Overall comparison chart saved: {save_path}")

        except Exception as e:
            print(f"❌ Error creating overall comparison: {e}")
            traceback.print_exc()

    def generate_transparent_visualizations(self, output_dir: str = None):
        """Generate all transparent visualization charts"""
        if output_dir is None:
            output_dir = self.results_dir

        print(f"🎨 Generating transparent visualizations...")
        print(f"📁 Output directory: {output_dir}")

        if not self.load_transparent_data():
            return False

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Generate category-specific charts
        for category in self.categories.keys():
            print(f"📊 Processing {category} category...")

            # Performance comparison chart
            performance_path = os.path.join(output_dir, f"{category}_performance.png")
            self.create_category_performance_chart(category, performance_path)

            # Catzilla advantage chart
            advantage_path = os.path.join(output_dir, f"{category}_catzilla_advantage.png")
            self.create_catzilla_advantage_chart(category, advantage_path)

        # Generate overall comparison
        overall_path = os.path.join(output_dir, "overall_framework_comparison.png")
        self.create_overall_comparison_chart(overall_path)

        # Generate summary report
        self.generate_visual_summary_report(output_dir)

        print(f"\n🎉 Transparent visualizations complete!")
        print(f"📁 All charts saved to: {output_dir}")
        return True

    def generate_visual_summary_report(self, output_dir: str):
        """Generate a summary report with all visualizations"""
        report_path = os.path.join(output_dir, "transparent_benchmark_report.md")

        with open(report_path, 'w') as f:
            f.write("# 🎯 Transparent Framework Benchmark Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("This report provides transparent, feature-by-feature performance comparison ")
            f.write("between Catzilla and other Python web frameworks.\n\n")

            # Overall comparison
            f.write("## 🏆 Overall Performance Comparison\n\n")
            f.write("![Overall Comparison](overall_framework_comparison.png)\n\n")

            # Category-specific sections
            for category in self.categories.keys():
                f.write(f"## 🚀 {category.title()} Performance\n\n")
                f.write(f"### Performance Comparison\n")
                f.write(f"![{category} Performance]({category}_performance.png)\n\n")
                f.write(f"### Catzilla Advantage\n")
                f.write(f"![{category} Advantage]({category}_catzilla_advantage.png)\n\n")

            # Methodology
            f.write("## 📋 Methodology\n\n")
            f.write("- **Tool:** wrk (HTTP benchmarking tool)\n")
            f.write("- **Metrics:** Requests per second, Response latency\n")
            f.write("- **Frameworks:** Catzilla, FastAPI, Flask, Django\n")
            f.write("- **Transparency:** All results are reproducible and source code is available\n\n")

            # Categories tested
            f.write("## 🧪 Categories Tested\n\n")
            for category, data in self.categories.items():
                result_count = len(data.get("results", []))
                last_run = data.get("last_run", "Unknown")
                f.write(f"- **{category.title()}:** {result_count} endpoints (Last run: {last_run})\n")

        print(f"✅ Visual summary report saved: {report_path}")


def main():
    """Main function for transparent visualization"""
    parser = argparse.ArgumentParser(description="Generate Transparent Framework Comparison Charts")
    parser.add_argument("--results-dir", default="results",
                       help="Directory containing benchmark results")
    parser.add_argument("--output-dir",
                       help="Output directory for visualizations (default: same as results-dir)")
    parser.add_argument("--category",
                       help="Generate charts for specific category only")

    args = parser.parse_args()

    # Resolve paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    benchmarks_dir = os.path.dirname(script_dir) if 'tools' in script_dir else script_dir
    results_dir = os.path.join(benchmarks_dir, args.results_dir)
    output_dir = args.output_dir or results_dir

    print(f"🔍 Looking for results in: {results_dir}")
    print(f"💾 Saving visualizations to: {output_dir}")

    if not os.path.exists(results_dir):
        print(f"❌ Results directory not found: {results_dir}")
        print("💡 Run benchmarks first with the enhanced transparent runner")
        sys.exit(1)

    # Create visualizer and generate charts
    visualizer = TransparentBenchmarkVisualizer(results_dir)

    if args.category:
        # Generate charts for specific category
        if not visualizer.load_transparent_data():
            sys.exit(1)

        if args.category not in visualizer.categories:
            print(f"❌ Category '{args.category}' not found")
            print(f"Available categories: {', '.join(visualizer.categories.keys())}")
            sys.exit(1)

        print(f"📊 Generating charts for {args.category} category...")

        performance_path = os.path.join(output_dir, f"{args.category}_performance.png")
        visualizer.create_category_performance_chart(args.category, performance_path)

        advantage_path = os.path.join(output_dir, f"{args.category}_catzilla_advantage.png")
        visualizer.create_catzilla_advantage_chart(args.category, advantage_path)

        print(f"✅ {args.category} charts generated successfully!")
    else:
        # Generate all visualizations
        if visualizer.generate_transparent_visualizations(output_dir):
            print("✅ All transparent visualizations generated successfully!")
        else:
            print("❌ Failed to generate visualizations")
            sys.exit(1)


if __name__ == "__main__":
    main()
