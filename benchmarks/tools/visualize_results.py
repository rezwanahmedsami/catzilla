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
    import traceback
except ImportError as e:
    print(f"❌ Required packages not installed. Install with: pip install matplotlib pandas seaborn numpy: {e}")
    print("Attempting to install missing packages...")
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
        self.categories = set()

    @staticmethod
    def worker_file_suffix(worker_mode: str, workers: int) -> str:
        return f"{worker_mode}_{workers}w"

    @staticmethod
    def worker_label(worker_mode: str, workers: int) -> str:
        unit = "worker" if workers == 1 else "workers"
        return f"{worker_mode.title()} / {workers} {unit}"

    def get_worker_signatures(self, df: pd.DataFrame) -> List[tuple]:
        signatures = []
        unique_rows = (
            df[["worker_mode", "workers"]]
            .drop_duplicates()
            .sort_values(by=["worker_mode", "workers"])
        )
        for row in unique_rows.itertuples(index=False):
            signatures.append((str(row.worker_mode), int(row.workers)))
        return signatures

    def load_data(self) -> bool:
        """Load benchmark results from JSON files"""
        try:
            # Try to load new enhanced summary file first
            summary_file = os.path.join(self.results_dir, 'benchmark_summary.json')
            if os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    self.summary_data = json.load(f)

                    # Check if it's the new framework-keyed format (v3.0)
                    if "categories" in self.summary_data and self.summary_data.get("metadata", {}).get("version") == "3.0":
                        # New framework-keyed format
                        self.data = []
                        for category_name, category_data in self.summary_data["categories"].items():
                            self.categories.add(category_name)
                            # Extract results from framework-keyed structure
                            results_dict = category_data.get("results", {})
                            for framework, framework_results in results_dict.items():
                                if isinstance(framework_results, list):
                                    self.data.extend(framework_results)
                        print(f"✅ Loaded {len(self.data)} results from framework-keyed summary file (v3.0)")
                        print(f"📊 Found categories: {', '.join(sorted(self.categories))}")
                        return True
                    elif "categories" in self.summary_data:
                        # Old category-based format (v2.0)
                        self.data = []
                        for category_name, category_data in self.summary_data["categories"].items():
                            self.categories.add(category_name)
                            self.data.extend(category_data.get("results", []))
                        print(f"✅ Loaded {len(self.data)} results from enhanced summary file (v2.0)")
                        print(f"📊 Found categories: {', '.join(sorted(self.categories))}")
                        return True
                    else:
                        # Old flat format (v1.0)
                        self.data = self.summary_data.get('results', [])
                        # Extract categories from benchmark_type field
                        for item in self.data:
                            if "benchmark_type" in item:
                                self.categories.add(item["benchmark_type"])
                            elif "category" in item:
                                self.categories.add(item["category"])
                        print(f"✅ Loaded {len(self.data)} results from flat summary file (v1.0)")
                        return True

            # Fall back to backward-compatible flat summary
            flat_summary_file = os.path.join(self.results_dir, 'benchmark_summary_flat.json')
            if os.path.exists(flat_summary_file):
                with open(flat_summary_file, 'r') as f:
                    self.summary_data = json.load(f)
                    self.data = self.summary_data.get('results', [])
                    for item in self.data:
                        if "benchmark_type" in item:
                            self.categories.add(item["benchmark_type"])
                    print(f"✅ Loaded {len(self.data)} results from flat summary file")
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
                'benchmark_type': item.get('benchmark_type', 'unknown'),
                'worker_mode': item.get('worker_mode', 'single'),
                'workers': int(item.get('workers', 1) or 1),
                'requests_per_sec': rps,
                'avg_latency_ms': avg_latency,
                'peak_memory_mb': float(item.get('peak_memory_mb', 0) or 0),
                'connections': item.get('connections', 100),
                'duration': item.get('duration', '10s')
            })

        return pd.DataFrame(processed_data)

    def create_requests_per_second_chart(self, df: pd.DataFrame, save_path: str, title_suffix: str = ""):
        """Create requests per second comparison chart"""
        plt.figure(figsize=(14, 8))

        # Group by framework and endpoint for better visualization, handling duplicates
        pivot_data = df.groupby(['endpoint_name', 'framework'])['requests_per_sec'].mean().unstack(fill_value=0)

        # Create grouped bar chart
        ax = pivot_data.plot(kind='bar', width=0.8, figsize=(14, 8))

        title = '🚀 Requests per Second by Framework and Endpoint'
        if title_suffix:
            title = f'{title} ({title_suffix})'
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
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

    def create_latency_chart(self, df: pd.DataFrame, save_path: str, title_suffix: str = ""):
        """Create average latency comparison chart"""
        plt.figure(figsize=(14, 8))

        # Group by framework and endpoint
        pivot_data = df.groupby(['endpoint_name', 'framework'])['avg_latency_ms'].mean().unstack(fill_value=0)

        # Create grouped bar chart
        ax = pivot_data.plot(kind='bar', width=0.8, figsize=(14, 8))

        title = '⚡ Average Response Latency by Framework and Endpoint'
        if title_suffix:
            title = f'{title} ({title_suffix})'
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
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

    def create_memory_chart(self, df: pd.DataFrame, save_path: str, title_suffix: str = ""):
        """Create peak memory comparison chart"""
        plt.figure(figsize=(14, 8))

        pivot_data = df.groupby(['endpoint_name', 'framework'])['peak_memory_mb'].mean().unstack(fill_value=0)

        ax = pivot_data.plot(kind='bar', width=0.8, figsize=(14, 8))

        title = '💾 Peak Memory by Framework and Endpoint'
        if title_suffix:
            title = f'{title} ({title_suffix})'
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Endpoint Type', fontsize=12)
        plt.ylabel('Peak Memory (MB)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Framework', bbox_to_anchor=(1.05, 1), loc='upper left')

        for container in ax.containers:
            ax.bar_label(container, fmt='%.2f', rotation=90, padding=3)

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Memory chart saved: {save_path}")

    def create_overall_performance_chart(self, df: pd.DataFrame, save_path: str, title_suffix: str = ""):
        """Create overall performance summary chart"""
        # Calculate average performance across all endpoints
        framework_stats = df.groupby('framework').agg({
            'requests_per_sec': 'mean',
            'avg_latency_ms': 'mean',
            'peak_memory_mb': 'mean'
        }).round(2)

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(22, 6))

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

        memory_values = framework_stats['peak_memory_mb']
        bars3 = ax3.bar(frameworks, memory_values, color=['#e74c3c', '#3498db', '#2ecc71', '#f39c12'])
        ax3.set_title('Average Peak Memory', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Peak Memory (MB)')
        ax3.tick_params(axis='x', rotation=45)

        for bar, value in zip(bars3, memory_values):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(memory_values)*0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontweight='bold')

        title = '🏆 Overall Performance Comparison'
        if title_suffix:
            title = f'{title} ({title_suffix})'
        plt.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Overall performance chart saved: {save_path}")

    def create_performance_matrix(self, df: pd.DataFrame, save_path: str, title_suffix: str = ""):
        """Create a heatmap showing performance across frameworks and endpoints"""
        plt.figure(figsize=(12, 8))

        # Create pivot table for heatmap - handle duplicates by averaging
        pivot_data = df.groupby(['endpoint_name', 'framework'])['requests_per_sec'].mean().unstack(fill_value=0)

        # Create heatmap
        sns.heatmap(pivot_data, annot=True, fmt='.0f', cmap='YlOrRd',
                   cbar_kws={'label': 'Requests per Second'})

        title = '🔥 Performance Heatmap: Requests per Second'
        if title_suffix:
            title = f'{title} ({title_suffix})'
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Framework', fontsize=12)
        plt.ylabel('Endpoint Type', fontsize=12)

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Performance heatmap saved: {save_path}")

    def create_category_comparison_chart(
        self,
        df: pd.DataFrame,
        category: str,
        save_path: str,
        worker_mode: str = None,
        workers: int = None,
    ):
        """Create performance comparison chart for a specific category"""
        # Filter data for the specific category
        category_df = df[df['benchmark_type'] == category].copy()

        worker_title_suffix = ""
        if worker_mode is not None and workers is not None:
            category_df = category_df[
                (category_df['worker_mode'] == worker_mode) &
                (category_df['workers'] == workers)
            ].copy()
            worker_title_suffix = f" ({self.worker_label(worker_mode, workers)})"

        if category_df.empty:
            print(f"⚠️  No data found for category: {category}")
            return

        plt.figure(figsize=(18, 12))

        # Create subplots for different metrics
        fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(24, 12))

        # 1. Requests per Second by Framework
        rps_data = category_df.groupby(['endpoint_name', 'framework'])['requests_per_sec'].mean().unstack(fill_value=0)
        rps_data.plot(kind='bar', ax=ax1, width=0.8)
        ax1.set_title(f'{category.title()} - Requests per Second{worker_title_suffix}', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Requests/sec')
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend(title='Framework')

        # Add value labels on bars
        for container in ax1.containers:
            ax1.bar_label(container, fmt='%.0f', rotation=90, fontsize=8)

        # 2. Average Latency by Framework
        latency_data = category_df.groupby(['endpoint_name', 'framework'])['avg_latency_ms'].mean().unstack(fill_value=0)
        latency_data.plot(kind='bar', ax=ax2, width=0.8)
        ax2.set_title(f'{category.title()} - Average Latency{worker_title_suffix}', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Latency (ms)')
        ax2.tick_params(axis='x', rotation=45)
        ax2.legend(title='Framework')

        # Add value labels on bars
        for container in ax2.containers:
            ax2.bar_label(container, fmt='%.1f', rotation=90, fontsize=8)

        # 3. Peak Memory by Framework
        memory_data = category_df.groupby(['endpoint_name', 'framework'])['peak_memory_mb'].mean().unstack(fill_value=0)
        memory_data.plot(kind='bar', ax=ax3, width=0.8)
        ax3.set_title(f'{category.title()} - Peak Memory{worker_title_suffix}', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Peak Memory (MB)')
        ax3.tick_params(axis='x', rotation=45)
        ax3.legend(title='Framework')

        for container in ax3.containers:
            ax3.bar_label(container, fmt='%.2f', rotation=90, fontsize=8)

        # 4. Framework Performance Summary (Average across all endpoints)
        framework_summary = category_df.groupby('framework').agg({
            'requests_per_sec': 'mean',
            'avg_latency_ms': 'mean',
            'peak_memory_mb': 'mean'
        }).round(2)

        frameworks = framework_summary.index
        rps_values = framework_summary['requests_per_sec']
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12'][:len(frameworks)]

        bars4 = ax4.bar(frameworks, rps_values, color=colors)
        ax4.set_title(f'{category.title()} - Framework Average RPS{worker_title_suffix}', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Average Requests/sec')
        ax4.tick_params(axis='x', rotation=45)

        # Add value labels
        for bar, value in zip(bars4, rps_values):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{value:.0f}', ha='center', va='bottom', fontweight='bold')

        # 5. Latency Comparison
        latency_values = framework_summary['avg_latency_ms']
        bars5 = ax5.bar(frameworks, latency_values, color=colors)
        ax5.set_title(f'{category.title()} - Framework Average Latency{worker_title_suffix}', fontsize=14, fontweight='bold')
        ax5.set_ylabel('Average Latency (ms)')
        ax5.tick_params(axis='x', rotation=45)

        # Add value labels
        for bar, value in zip(bars5, latency_values):
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{value:.1f}', ha='center', va='bottom', fontweight='bold')

        # 6. Memory Comparison
        memory_values = framework_summary['peak_memory_mb']
        bars6 = ax6.bar(frameworks, memory_values, color=colors)
        ax6.set_title(f'{category.title()} - Framework Average Peak Memory{worker_title_suffix}', fontsize=14, fontweight='bold')
        ax6.set_ylabel('Peak Memory (MB)')
        ax6.tick_params(axis='x', rotation=45)

        for bar, value in zip(bars6, memory_values):
            height = bar.get_height()
            ax6.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontweight='bold')

        plt.suptitle(f'🚀 {category.title()} Performance Analysis - Catzilla vs Competition{worker_title_suffix}',
                     fontsize=18, fontweight='bold', y=0.98)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Category '{category}' comparison chart saved: {save_path}")



    def generate_category_specific_visualizations(self, output_dir: str):
        """Generate visualizations for each category"""
        if not self.data:
            print("❌ No data loaded")
            return False

        print(f"📊 Processing {len(self.data)} benchmark results")
        df = self.prepare_dataframe()

        worker_signatures = self.get_worker_signatures(df)

        if len(worker_signatures) > 1:
            for worker_mode, workers in worker_signatures:
                worker_df = df[
                    (df['worker_mode'] == worker_mode) &
                    (df['workers'] == workers)
                ].copy()
                suffix = self.worker_file_suffix(worker_mode, workers)
                title_suffix = self.worker_label(worker_mode, workers)
                self.create_requests_per_second_chart(
                    worker_df,
                    os.path.join(output_dir, f'overall_{suffix}_requests_per_second.png'),
                    title_suffix,
                )
                self.create_latency_chart(
                    worker_df,
                    os.path.join(output_dir, f'overall_{suffix}_latency_comparison.png'),
                    title_suffix,
                )
                self.create_memory_chart(
                    worker_df,
                    os.path.join(output_dir, f'overall_{suffix}_memory_comparison.png'),
                    title_suffix,
                )
                self.create_overall_performance_chart(
                    worker_df,
                    os.path.join(output_dir, f'overall_{suffix}_performance_summary.png'),
                    title_suffix,
                )
                self.create_performance_matrix(
                    worker_df,
                    os.path.join(output_dir, f'overall_{suffix}_performance_heatmap.png'),
                    title_suffix,
                )
        else:
            self.create_requests_per_second_chart(df, os.path.join(output_dir, 'overall_requests_per_second.png'))
            self.create_latency_chart(df, os.path.join(output_dir, 'overall_latency_comparison.png'))
            self.create_memory_chart(df, os.path.join(output_dir, 'overall_memory_comparison.png'))
            self.create_overall_performance_chart(df, os.path.join(output_dir, 'overall_performance_summary.png'))
            self.create_performance_matrix(df, os.path.join(output_dir, 'overall_performance_heatmap.png'))

        # Generate category-specific visualizations
        print(f"\n🎯 Generating category-specific visualizations...")
        for category in sorted(self.categories):
            category_safe = category.replace(' ', '_').replace('-', '_')
            category_df = df[df['benchmark_type'] == category].copy()
            category_signatures = self.get_worker_signatures(category_df)
            if len(category_signatures) > 1:
                for worker_mode, workers in category_signatures:
                    worker_suffix = self.worker_file_suffix(worker_mode, workers)
                    category_file = os.path.join(output_dir, f'{category_safe}_{worker_suffix}_performance_analysis.png')
                    self.create_category_comparison_chart(df, category, category_file, worker_mode, workers)
            else:
                category_file = os.path.join(output_dir, f'{category_safe}_performance_analysis.png')
                self.create_category_comparison_chart(df, category, category_file)

        return True

    def generate_performance_report(self, df: pd.DataFrame, save_path: str):
        """Generate a comprehensive performance report"""
        # Calculate statistics
        framework_stats = df.groupby('framework').agg({
            'requests_per_sec': ['mean', 'max', 'min', 'std'],
            'avg_latency_ms': ['mean', 'max', 'min', 'std'],
            'peak_memory_mb': ['mean', 'max']
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
            report += f"- **Avg Peak Memory**: {stats[('peak_memory_mb', 'mean')]:.2f}MB\n"
            report += f"- **Max Peak Memory**: {stats[('peak_memory_mb', 'max')]:.2f}MB\n"
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
        """Generate all performance visualizations including category-specific ones"""
        if output_dir is None:
            output_dir = self.results_dir

        # Load data
        if not self.load_data():
            print("❌ Failed to load benchmark data")
            return False

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        try:
            # Generate enhanced category-specific visualizations
            success = self.generate_category_specific_visualizations(output_dir)

            if success:
                # Generate performance report
                report_path = os.path.join(output_dir, 'transparent_performance_report.md')
                self.generate_transparent_performance_report(report_path)

                print("\n" + "="*60)
                print("🎉 All visualizations generated successfully!")
                print(f"📁 Output directory: {output_dir}")
                print("📊 Generated files:")

                # List all generated files
                generated_files = []
                for file in os.listdir(output_dir):
                    if file.endswith('.png'):
                        generated_files.append(f"  - {file}")

                if generated_files:
                    print("\n".join(sorted(generated_files)))

                print(f"  - transparent_performance_report.md")
                print("="*60)
                return True
            else:
                print("❌ Failed to generate visualizations")
                return False

        except Exception as e:
            print(f"❌ Error generating visualizations: {e}")
            traceback.print_exc()
            return False

    def generate_transparent_performance_report(self, save_path: str):
        """Generate a comprehensive transparent performance report"""
        if not self.data:
            return

        df = self.prepare_dataframe()

        report = []
        report.append("# 🚀 Catzilla Framework - Transparent Performance Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("## 📋 Executive Summary")
        report.append("")
        report.append("This report provides a transparent, feature-by-feature comparison of Catzilla")
        report.append("against leading Python web frameworks (FastAPI, Flask, Django).")
        report.append("")

        # Overall statistics
        total_tests = len(df)
        frameworks = sorted(df['framework'].unique())
        categories = sorted(df['benchmark_type'].unique())
        worker_signatures = self.get_worker_signatures(df)

        report.append(f"- **Total Benchmarks**: {total_tests}")
        report.append(f"- **Frameworks Tested**: {', '.join(frameworks)}")
        report.append(f"- **Feature Categories**: {len(categories)}")
        report.append(f"- **Worker Configurations**: {', '.join(self.worker_label(mode, workers) for mode, workers in worker_signatures)}")
        report.append("")

        report.append("## 🏁 Benchmark Highlights")
        report.append("")
        report.append("Catzilla is built to be the **world's fastest Python web framework**.")
        report.append("In the benchmark suite in this repository, it leads FastAPI, Flask, and Django in both single-worker and 10-worker direct HTTP benchmarks.")
        report.append("")

        for worker_mode, workers in worker_signatures:
            worker_df = df[
                (df['worker_mode'] == worker_mode) &
                (df['workers'] == workers)
            ].copy()
            if worker_df.empty or 'catzilla' not in worker_df['framework'].values:
                continue

            suffix = self.worker_file_suffix(worker_mode, workers)
            label = self.worker_label(worker_mode, workers)
            catzilla_df = worker_df[worker_df['framework'] == 'catzilla']
            catzilla_avg_rps = catzilla_df['requests_per_sec'].mean()
            catzilla_avg_latency = catzilla_df['avg_latency_ms'].mean()
            catzilla_avg_memory = catzilla_df['peak_memory_mb'].mean()
            catzilla_best = catzilla_df.loc[catzilla_df['requests_per_sec'].idxmax()]

            other_frameworks = (
                worker_df[worker_df['framework'] != 'catzilla']
                .groupby('framework')['requests_per_sec']
                .mean()
                .sort_values(ascending=False)
            )

            report.append(f"### {label}")
            report.append("")
            report.append(f"- **Catzilla Avg RPS**: {catzilla_avg_rps:.0f}")
            report.append(f"- **Catzilla Best Endpoint**: {catzilla_best['endpoint_name']} ({catzilla_best['requests_per_sec']:.0f} RPS)")
            report.append(f"- **Catzilla Avg Latency**: {catzilla_avg_latency:.2f}ms")
            report.append(f"- **Catzilla Avg Peak Memory**: {catzilla_avg_memory:.2f}MB")
            if not other_frameworks.empty:
                best_other_framework = other_frameworks.index[0]
                best_other_rps = other_frameworks.iloc[0]
                lead_multiple = catzilla_avg_rps / best_other_rps if best_other_rps else 0
                report.append(f"- **Lead over {best_other_framework.title()}**: {lead_multiple:.1f}x average throughput")
            report.append("")
            report.append(f"![{label} performance summary](overall_{suffix}_performance_summary.png)")
            report.append("")
            report.append(f"![{label} memory comparison](overall_{suffix}_memory_comparison.png)")
            report.append("")

        # Category-by-category analysis
        report.append("## 🎯 Feature-by-Feature Analysis")
        report.append("")

        for category in sorted(categories):
            category_df = df[df['benchmark_type'] == category]
            if category_df.empty:
                continue

            report.append(f"### {category.replace('_', ' ').title()}")
            report.append("")

            # Framework performance summary for this category
            framework_stats = category_df.groupby('framework').agg({
                'requests_per_sec': ['mean', 'max'],
                'avg_latency_ms': ['mean', 'min'],
                'peak_memory_mb': ['mean', 'max']
            }).round(2)

            # Flatten column names
            framework_stats.columns = ['avg_rps', 'max_rps', 'avg_latency', 'min_latency', 'avg_peak_memory', 'max_peak_memory']

            report.append("| Framework | Avg RPS | Max RPS | Avg Latency (ms) | Min Latency (ms) | Avg Peak Memory (MB) | Max Peak Memory (MB) |")
            report.append("|-----------|---------|---------|------------------|------------------|----------------------|----------------------|")

            for framework in framework_stats.index:
                stats = framework_stats.loc[framework]
                report.append(f"| {framework.title()} | {stats['avg_rps']:.0f} | {stats['max_rps']:.0f} | {stats['avg_latency']:.2f} | {stats['min_latency']:.2f} | {stats['avg_peak_memory']:.2f} | {stats['max_peak_memory']:.2f} |")

            report.append("")

            # Catzilla advantage calculation
            if 'catzilla' in framework_stats.index:
                catzilla_rps = framework_stats.loc['catzilla', 'avg_rps']
                report.append("**Catzilla Performance Advantage:**")
                report.append("")

                for framework in framework_stats.index:
                    if framework != 'catzilla':
                        fw_rps = framework_stats.loc[framework, 'avg_rps']
                        if fw_rps > 0:
                            advantage = ((catzilla_rps - fw_rps) / fw_rps) * 100
                            if advantage > 0:
                                report.append(f"- **{advantage:.1f}% faster** than {framework.title()}")
                            else:
                                report.append(f"- **{abs(advantage):.1f}% slower** than {framework.title()}")
                        else:
                            report.append(f"- {framework.title()}: No data available")

                report.append("")

        # Top performers section
        report.append("## 🏆 Top Performers by Category")
        report.append("")

        for category in sorted(categories):
            category_df = df[df['benchmark_type'] == category]
            if category_df.empty:
                continue

            top_performer = category_df.loc[category_df['requests_per_sec'].idxmax()]
            report.append(f"- **{category.replace('_', ' ').title()}**: {top_performer['framework'].title()} ({top_performer['requests_per_sec']:.0f} RPS)")

        report.append("")
        report.append("## 📊 Visualization Files")
        report.append("")
        report.append("The following charts have been generated for detailed analysis:")
        report.append("")
        report.append("### Overall Performance")
        if len(worker_signatures) > 1:
            for worker_mode, workers in worker_signatures:
                worker_suffix = self.worker_file_suffix(worker_mode, workers)
                worker_label = self.worker_label(worker_mode, workers)
                report.append(f"- `overall_{worker_suffix}_requests_per_second.png` - Overall RPS comparison ({worker_label})")
                report.append(f"- `overall_{worker_suffix}_latency_comparison.png` - Overall latency comparison ({worker_label})")
                report.append(f"- `overall_{worker_suffix}_memory_comparison.png` - Overall peak memory comparison ({worker_label})")
                report.append(f"- `overall_{worker_suffix}_performance_summary.png` - Performance summary charts ({worker_label})")
                report.append(f"- `overall_{worker_suffix}_performance_heatmap.png` - Performance heatmap ({worker_label})")
        else:
            report.append("- `overall_requests_per_second.png` - Overall RPS comparison")
            report.append("- `overall_latency_comparison.png` - Overall latency comparison")
            report.append("- `overall_memory_comparison.png` - Overall peak memory comparison")
            report.append("- `overall_performance_summary.png` - Performance summary charts")
            report.append("- `overall_performance_heatmap.png` - Performance heatmap")
        report.append("")
        report.append("### Category-Specific Analysis")
        for category in sorted(categories):
            category_safe = category.replace(' ', '_').replace('-', '_')
            category_df = df[df['benchmark_type'] == category]
            category_signatures = self.get_worker_signatures(category_df)
            if len(category_signatures) > 1:
                for worker_mode, workers in category_signatures:
                    worker_suffix = self.worker_file_suffix(worker_mode, workers)
                    worker_label = self.worker_label(worker_mode, workers)
                    report.append(f"- `{category_safe}_{worker_suffix}_performance_analysis.png` - {category.replace('_', ' ').title()} detailed analysis ({worker_label})")
            else:
                report.append(f"- `{category_safe}_performance_analysis.png` - {category.replace('_', ' ').title()} detailed analysis")

        report.append("")
        report.append("---")
        report.append("*This report is automatically generated by the Catzilla Transparent Benchmarking System*")

        # Save report
        with open(save_path, 'w') as f:
            f.write('\n'.join(report))

        print(f"✅ Transparent performance report saved: {save_path}")


def main():
    """Main function to run the visualizer"""
    parser = argparse.ArgumentParser(description="Visualize Catzilla benchmark results")
    parser.add_argument("--results-dir", default="results",
                       help="Directory containing benchmark results (default: results)")
    parser.add_argument("--output-dir",
                       help="Output directory for visualizations (default: same as results-dir)")

    args = parser.parse_args()

    # Resolve paths - fix to look in benchmarks/results by default
    script_dir = os.path.dirname(os.path.abspath(__file__))
    benchmarks_dir = os.path.dirname(script_dir)  # Go up one level from tools/ to benchmarks/
    results_dir = os.path.join(benchmarks_dir, args.results_dir)
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
