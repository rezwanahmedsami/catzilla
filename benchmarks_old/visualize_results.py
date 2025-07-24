#!/usr/bin/env python3
"""
Catzilla Benchmark Results Visualizer

This script processes benchmark results and generates performance comparison charts
showing how Catzilla performs against other Python web frameworks.
"""

import json
import os
import sys
import glob
from datetime import datetime
from typing import Dict, List, Any
import argparse

try:
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import seaborn as sns
except ImportError:
    print("❌ Required packages not installed. Install with: pip install matplotlib pandas seaborn")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error importing libraries: {e}")
    sys.exit(1)

# Set matplotlib style
plt.style.use('default')
sns.set_palette("husl")

class BenchmarkVisualizer:
    """Visualizes benchmark results and generates performance comparison charts"""

    def __init__(self, results_dir: str):
        self.results_dir = results_dir
        self.data = []
        self.summary_data = None

    def load_data(self) -> bool:
        """Load benchmark results from JSON files"""
        try:
            # Try to load summary file first
            summary_file = os.path.join(self.results_dir, 'benchmark_summary.json')
            if os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    self.summary_data = json.load(f)
                    self.data = self.summary_data.get('results', [])
                    print(f"✅ Loaded {len(self.data)} results from summary file")
                    return True

            # Fall back to individual JSON files
            json_files = glob.glob(os.path.join(self.results_dir, '*.json'))
            json_files = [f for f in json_files if 'summary' not in f]

            for json_file in json_files:
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        self.data.append(data)
                except Exception as e:
                    print(f"⚠️  Warning: Failed to load {json_file}: {e}")

            print(f"✅ Loaded {len(self.data)} benchmark results")
            return len(self.data) > 0

        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def prepare_dataframe(self) -> pd.DataFrame:
        """Convert raw data to pandas DataFrame for analysis"""
        if not self.data:
            raise ValueError("No data loaded")

        # Process the data
        processed_data = []

        for item in self.data:
            # Extract numeric value from requests_per_sec
            rps_str = item.get('requests_per_sec', '0')
            try:
                # Handle formats like "15234.56" or "15.23k"
                if 'k' in str(rps_str).lower():
                    rps = float(str(rps_str).lower().replace('k', '')) * 1000
                else:
                    rps = float(str(rps_str).replace(',', ''))
            except (ValueError, TypeError):
                rps = 0

            # Extract latency values (remove 'ms' suffix)
            avg_latency_str = item.get('avg_latency', '0ms')
            try:
                avg_latency = float(str(avg_latency_str).replace('ms', '').replace('us', ''))
                # Convert microseconds to milliseconds if needed
                if 'us' in str(avg_latency_str):
                    avg_latency = avg_latency / 1000
            except (ValueError, TypeError):
                avg_latency = 0

            processed_data.append({
                'framework': item.get('framework', 'unknown'),
                'endpoint_name': item.get('endpoint_name', 'unknown'),
                'endpoint': item.get('endpoint', '/'),
                'requests_per_sec': rps,
                'avg_latency_ms': avg_latency,
                'connections': item.get('connections', 100),
                'duration': item.get('duration', '10s')
            })

        return pd.DataFrame(processed_data)

    def create_requests_per_second_chart(self, df: pd.DataFrame, save_path: str):
        """Create requests per second comparison chart"""
        plt.figure(figsize=(14, 8))

        # Group by framework and endpoint for better visualization
        pivot_data = df.pivot(index='endpoint_name', columns='framework', values='requests_per_sec')

        # Create grouped bar chart
        ax = pivot_data.plot(kind='bar', width=0.8, figsize=(14, 8))

        plt.title('🚀 Requests per Second by Framework and Endpoint', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Endpoint Type', fontsize=12)
        plt.ylabel('Requests per Second', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Framework', bbox_to_anchor=(1.05, 1), loc='upper left')

        # Add value labels on bars
        for container in ax.containers:
            ax.bar_label(container, fmt='%.0f', rotation=90, padding=3)

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Requests per second chart saved: {save_path}")

    def create_latency_chart(self, df: pd.DataFrame, save_path: str):
        """Create average latency comparison chart"""
        plt.figure(figsize=(14, 8))

        # Group by framework and endpoint
        pivot_data = df.pivot(index='endpoint_name', columns='framework', values='avg_latency_ms')

        # Create grouped bar chart
        ax = pivot_data.plot(kind='bar', width=0.8, figsize=(14, 8))

        plt.title('⚡ Average Response Latency by Framework and Endpoint', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Endpoint Type', fontsize=12)
        plt.ylabel('Average Latency (ms)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Framework', bbox_to_anchor=(1.05, 1), loc='upper left')

        # Add value labels on bars
        for container in ax.containers:
            ax.bar_label(container, fmt='%.2f', rotation=90, padding=3)

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Latency chart saved: {save_path}")

    def create_overall_performance_chart(self, df: pd.DataFrame, save_path: str):
        """Create overall performance summary chart"""
        # Calculate average performance across all endpoints
        framework_stats = df.groupby('framework').agg({
            'requests_per_sec': 'mean',
            'avg_latency_ms': 'mean'
        }).round(2)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Requests per second
        frameworks = framework_stats.index
        rps_values = framework_stats['requests_per_sec']

        bars1 = ax1.bar(frameworks, rps_values, color=['#e74c3c', '#3498db', '#2ecc71', '#f39c12'])
        ax1.set_title('Average Requests per Second', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Requests/sec')
        ax1.tick_params(axis='x', rotation=45)

        # Add value labels
        for bar, value in zip(bars1, rps_values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(rps_values)*0.01,
                    f'{value:.0f}', ha='center', va='bottom', fontweight='bold')

        # Average latency
        latency_values = framework_stats['avg_latency_ms']
        bars2 = ax2.bar(frameworks, latency_values, color=['#e74c3c', '#3498db', '#2ecc71', '#f39c12'])
        ax2.set_title('Average Response Latency', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Latency (ms)')
        ax2.tick_params(axis='x', rotation=45)

        # Add value labels
        for bar, value in zip(bars2, latency_values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(latency_values)*0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontweight='bold')

        plt.suptitle('🏆 Overall Performance Comparison', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Overall performance chart saved: {save_path}")

    def create_performance_matrix(self, df: pd.DataFrame, save_path: str):
        """Create a heatmap showing performance across frameworks and endpoints"""
        plt.figure(figsize=(12, 8))

        # Create pivot table for heatmap
        pivot_data = df.pivot(index='endpoint_name', columns='framework', values='requests_per_sec')

        # Create heatmap
        sns.heatmap(pivot_data, annot=True, fmt='.0f', cmap='YlOrRd',
                   cbar_kws={'label': 'Requests per Second'})

        plt.title('🔥 Performance Heatmap: Requests per Second', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Framework', fontsize=12)
        plt.ylabel('Endpoint Type', fontsize=12)

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Performance heatmap saved: {save_path}")

    def generate_performance_report(self, df: pd.DataFrame, save_path: str):
        """Generate a comprehensive performance report"""
        # Calculate statistics
        framework_stats = df.groupby('framework').agg({
            'requests_per_sec': ['mean', 'max', 'min', 'std'],
            'avg_latency_ms': ['mean', 'max', 'min', 'std']
        }).round(2)

        # Find the best performing framework
        best_rps_framework = df.groupby('framework')['requests_per_sec'].mean().idxmax()
        best_latency_framework = df.groupby('framework')['avg_latency_ms'].mean().idxmin()

        # Calculate performance improvements
        catzilla_avg_rps = df[df['framework'] == 'catzilla']['requests_per_sec'].mean()

        report = f"""# 🚀 Catzilla Performance Benchmark Report

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Executive Summary

"""

        if 'catzilla' in df['framework'].values:
            report += f"- **Best Overall RPS Framework**: {best_rps_framework}\n"
            report += f"- **Best Overall Latency Framework**: {best_latency_framework}\n"

            for framework in df['framework'].unique():
                if framework != 'catzilla':
                    other_avg_rps = df[df['framework'] == framework]['requests_per_sec'].mean()
                    if other_avg_rps > 0:
                        improvement = ((catzilla_avg_rps - other_avg_rps) / other_avg_rps) * 100
                        report += f"- **Catzilla vs {framework.title()}**: {improvement:+.1f}% requests/sec\n"

        report += f"\n## 📈 Detailed Framework Statistics\n\n"

        for framework in framework_stats.index:
            stats = framework_stats.loc[framework]
            report += f"### {framework.title()}\n"
            report += f"- **Avg RPS**: {stats[('requests_per_sec', 'mean')]:.0f} (±{stats[('requests_per_sec', 'std')]:.0f})\n"
            report += f"- **Max RPS**: {stats[('requests_per_sec', 'max')]:.0f}\n"
            report += f"- **Avg Latency**: {stats[('avg_latency_ms', 'mean')]:.2f}ms (±{stats[('avg_latency_ms', 'std')]:.2f})\n"
            report += f"- **Min Latency**: {stats[('avg_latency_ms', 'min')]:.2f}ms\n\n"

        # Endpoint performance breakdown
        report += "## 🎯 Endpoint Performance Breakdown\n\n"

        for endpoint in df['endpoint_name'].unique():
            endpoint_data = df[df['endpoint_name'] == endpoint]
            report += f"### {endpoint.replace('_', ' ').title()}\n"

            endpoint_stats = endpoint_data.groupby('framework')['requests_per_sec'].mean().sort_values(ascending=False)
            for i, (framework, rps) in enumerate(endpoint_stats.items()):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "
                report += f"{medal} **{framework.title()}**: {rps:.0f} req/s\n"
            report += "\n"

        # Test configuration
        if self.summary_data and 'benchmark_info' in self.summary_data:
            info = self.summary_data['benchmark_info']
            report += f"## ⚙️ Test Configuration\n\n"
            report += f"- **Duration**: {info.get('duration', 'N/A')}\n"
            report += f"- **Connections**: {info.get('connections', 'N/A')}\n"
            report += f"- **Threads**: {info.get('threads', 'N/A')}\n"
            report += f"- **Tool**: {info.get('tool', 'wrk')}\n\n"

        # Save report
        with open(save_path, 'w') as f:
            f.write(report)

        print(f"✅ Performance report saved: {save_path}")
        return report

    def generate_all_visualizations(self, output_dir: str = None):
        """Generate all performance visualizations and reports"""
        if output_dir is None:
            output_dir = self.results_dir

        if not self.load_data():
            print("❌ Failed to load benchmark data")
            return False

        try:
            df = self.prepare_dataframe()
            print(f"📊 Processing {len(df)} benchmark results")

            # Create visualizations
            self.create_requests_per_second_chart(df, os.path.join(output_dir, 'requests_per_second.png'))
            self.create_latency_chart(df, os.path.join(output_dir, 'latency_comparison.png'))
            self.create_overall_performance_chart(df, os.path.join(output_dir, 'overall_performance.png'))
            self.create_performance_matrix(df, os.path.join(output_dir, 'performance_heatmap.png'))

            # Generate report
            report = self.generate_performance_report(df, os.path.join(output_dir, 'performance_report.md'))

            print("\n" + "="*60)
            print("🎉 All visualizations generated successfully!")
            print(f"📁 Output directory: {output_dir}")
            print("📊 Generated files:")
            print("  - requests_per_second.png")
            print("  - latency_comparison.png")
            print("  - overall_performance.png")
            print("  - performance_heatmap.png")
            print("  - performance_report.md")
            print("="*60)

            return True

        except Exception as e:
            print(f"❌ Error generating visualizations: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function to run the visualizer"""
    parser = argparse.ArgumentParser(description="Visualize Catzilla benchmark results")
    parser.add_argument("--results-dir", default="results",
                       help="Directory containing benchmark results (default: results)")
    parser.add_argument("--output-dir",
                       help="Output directory for visualizations (default: same as results-dir)")

    args = parser.parse_args()

    # Resolve paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, args.results_dir)
    output_dir = args.output_dir or results_dir

    if not os.path.exists(results_dir):
        print(f"❌ Results directory not found: {results_dir}")
        print("💡 Run the benchmark first: ./benchmarks/run_all.sh")
        sys.exit(1)

    print(f"🔍 Looking for results in: {results_dir}")
    print(f"💾 Saving visualizations to: {output_dir}")

    # Create visualizer and generate charts
    visualizer = BenchmarkVisualizer(results_dir)

    if visualizer.generate_all_visualizations(output_dir):
        print("✅ Visualization complete!")
        sys.exit(0)
    else:
        print("❌ Visualization failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
