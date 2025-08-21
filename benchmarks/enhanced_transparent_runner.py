#!/usr/bin/env python3
"""
Enhanced Transparent Benchmark Runner for Catzilla

This creates a transparent benchmarking system with proper append functionality
and category-based organization for fair feature-by-feature comparison.
"""

import os
import sys
import json
import time
import argparse
import subprocess
import threading
import queue
import signal
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import concurrent.futures

# Add shared modules to path
SCRIPT_DIR = Path(__file__).parent
SHARED_DIR = SCRIPT_DIR / "shared"
TOOLS_DIR = SCRIPT_DIR / "tools"
sys.path.insert(0, str(SHARED_DIR))
sys.path.insert(0, str(TOOLS_DIR))

# Import shared utilities
from benchmarks_config import (
    FRAMEWORKS, SERVER_CONFIGS, DEFAULT_TEST_PARAMS,
    get_framework_port, get_server_command
)

# Import system information collection
try:
    tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools')
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    from system_info import collect_system_info, format_system_info_markdown
    print("System info module loaded successfully")
except ImportError as e:
    print(f"Warning: system_info module not found ({e}). System information will not be included in reports.")
    def collect_system_info():
        return {"error": "system_info module not available"}
    def format_system_info_markdown(info):
        return "## System Information\n\nSystem information not available."


class TransparentBenchmarkRunner:
    """Enhanced transparent benchmark runner with append functionality"""

    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.servers = {}
        self.results = {}
        self.test_categories = [
            "basic",
            "middleware",
            "dependency_injection",
            "async_operations",
            "validation",
            "file_operations",
            "background_tasks",
            "real_world_scenarios"
        ]
        self.summary_file = self.output_dir / "benchmark_summary.json"

    def load_existing_summary(self) -> Dict[str, Any]:
        """Load existing benchmark summary or create new structure"""
        if self.summary_file.exists():
            try:
                with open(self.summary_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                print("⚠️  Existing summary file corrupted, creating new one")

        # Create new structure
        return {
            "metadata": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "2.0",
                "description": "Transparent Feature-by-Feature Framework Comparison"
            },
            "categories": {}
        }

    def append_category_results(self, category: str, category_results: Dict[str, Any]):
        """Append results for a specific category without affecting others"""
        print(f"📝 Appending {category} results to summary...")

        # Load existing summary
        summary = self.load_existing_summary()

        # Update metadata
        summary["metadata"]["last_updated"] = datetime.now().isoformat()

        # Normalize category results to our standard format
        normalized_results = []

        # Handle different input formats
        if "frameworks" in category_results:
            # New nested format
            for framework, fw_data in category_results["frameworks"].items():
                if "endpoints" in fw_data:
                    for endpoint, endpoint_data in fw_data["endpoints"].items():
                        if isinstance(endpoint_data, dict) and "requests_per_sec" in endpoint_data:
                            normalized_results.append({
                                "framework": framework,
                                "category": category,
                                "endpoint": endpoint,
                                "endpoint_name": f"{category}_{endpoint.strip('/').replace('/', '_')}",
                                "benchmark_type": category,
                                "method": endpoint_data.get("method", "GET"),
                                "requests_per_sec": str(endpoint_data.get("requests_per_sec", "0")),
                                "avg_latency": endpoint_data.get("avg_latency", "0ms"),
                                "p99_latency": endpoint_data.get("p99_latency", "0ms"),
                                "transfer_per_sec": endpoint_data.get("transfer_per_sec", "0KB"),
                                "timestamp": datetime.now().isoformat(),
                                "test_params": category_results.get("test_params", {}),
                                "system_info": category_results.get("system_info", {})
                            })
        elif "results" in category_results:
            # Handle results array format
            for result in category_results["results"]:
                if isinstance(result, dict) and "framework" in result:
                    result["category"] = category
                    result["benchmark_type"] = category
                    normalized_results.append(result)

        # Store category results with metadata
        summary["categories"][category] = {
            "last_run": datetime.now().isoformat(),
            "test_params": category_results.get("test_params", {}),
            "system_info": category_results.get("system_info", {}),
            "results": normalized_results,
            "summary_stats": self._calculate_category_stats(normalized_results)
        }

        # Save updated summary
        with open(self.summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"✅ {category} results appended successfully!")
        print(f"📊 Added {len(normalized_results)} benchmark results")
        return summary

    def _calculate_category_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics for a category"""
        if not results:
            return {}

        stats = {}
        frameworks = set()

        for result in results:
            framework = result.get("framework", "unknown")
            frameworks.add(framework)

            if framework not in stats:
                stats[framework] = {
                    "avg_rps": 0,
                    "avg_latency": 0,
                    "endpoint_count": 0,
                    "total_rps": 0
                }

            # Parse RPS
            rps_str = result.get("requests_per_sec", "0")
            try:
                if 'k' in str(rps_str).lower():
                    rps = float(str(rps_str).lower().replace('k', '')) * 1000
                else:
                    rps = float(str(rps_str).replace(',', ''))
            except:
                rps = 0

            # Parse latency
            latency_str = result.get("avg_latency", "0ms")
            try:
                latency = float(str(latency_str).replace('ms', '').replace('us', ''))
                if 'us' in str(latency_str):
                    latency = latency / 1000
            except:
                latency = 0

            stats[framework]["total_rps"] += rps
            stats[framework]["endpoint_count"] += 1

        # Calculate averages
        for framework in stats:
            if stats[framework]["endpoint_count"] > 0:
                stats[framework]["avg_rps"] = stats[framework]["total_rps"] / stats[framework]["endpoint_count"]

        return stats

    def run_single_category_benchmark(self, category: str, frameworks: List[str] = None,
                                    test_params: Dict = None) -> Dict[str, Any]:
        """Run benchmark for a single category and append to summary"""
        if frameworks is None:
            frameworks = FRAMEWORKS

        if test_params is None:
            test_params = DEFAULT_TEST_PARAMS.copy()

        print(f"🚀 Running {category} benchmarks...")
        print(f"📋 Frameworks: {', '.join(frameworks)}")
        print(f"⚙️  Test params: {test_params}")

        # Run the category benchmark (using existing logic)
        category_results = self._run_category_benchmark_internal(category, frameworks, test_params)

        # Append to summary
        self.append_category_results(category, category_results)

        return category_results

    def _run_category_benchmark_internal(self, category: str, frameworks: List[str],
                                       test_params: Dict) -> Dict[str, Any]:
        """Internal method to run actual benchmark (placeholder for now)"""
        # This would contain the actual benchmark running logic
        # For now, return a sample structure
        return {
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "test_params": test_params,
            "system_info": collect_system_info(),
            "frameworks": {
                fw: {
                    "framework": fw,
                    "category": category,
                    "endpoints": {}
                } for fw in frameworks
            }
        }

    def get_category_summary(self, category: str) -> Dict[str, Any]:
        """Get summary for a specific category"""
        summary = self.load_existing_summary()
        return summary.get("categories", {}).get(category, {})

    def get_all_categories_summary(self) -> Dict[str, Any]:
        """Get summary for all categories"""
        return self.load_existing_summary()

    def generate_transparent_report(self) -> str:
        """Generate a transparent comparison report"""
        summary = self.load_existing_summary()

        report = []
        report.append("# 🎯 Transparent Framework Comparison Report")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("This report provides transparent, feature-by-feature performance comparison")
        report.append("between Catzilla and other Python web frameworks.")
        report.append("")

        # Categories overview
        report.append("## 📊 Categories Benchmarked")
        report.append("")

        categories = summary.get("categories", {})
        if not categories:
            report.append("No benchmark data available. Run benchmarks first.")
            return "\n".join(report)

        for category, data in categories.items():
            last_run = data.get("last_run", "Unknown")
            result_count = len(data.get("results", []))
            report.append(f"- **{category.title()}**: {result_count} results (Last run: {last_run})")

        report.append("")

        # Performance comparison for each category
        for category, data in categories.items():
            report.append(f"## 🚀 {category.title()} Performance")
            report.append("")

            stats = data.get("summary_stats", {})
            if stats:
                report.append("| Framework | Avg RPS | Endpoints |")
                report.append("|-----------|---------|-----------|")

                # Sort by average RPS (descending)
                sorted_frameworks = sorted(stats.items(),
                                         key=lambda x: x[1].get("avg_rps", 0),
                                         reverse=True)

                for framework, fw_stats in sorted_frameworks:
                    avg_rps = fw_stats.get("avg_rps", 0)
                    endpoint_count = fw_stats.get("endpoint_count", 0)
                    report.append(f"| {framework.title()} | {avg_rps:,.0f} | {endpoint_count} |")

                report.append("")

                # Calculate Catzilla advantage
                if "catzilla" in stats and len(stats) > 1:
                    catzilla_rps = stats["catzilla"].get("avg_rps", 0)
                    competitors = {k: v for k, v in stats.items() if k != "catzilla"}

                    if competitors and catzilla_rps > 0:
                        report.append("### 🎯 Catzilla Advantage")
                        for competitor, comp_stats in competitors.items():
                            comp_rps = comp_stats.get("avg_rps", 0)
                            if comp_rps > 0:
                                advantage = ((catzilla_rps - comp_rps) / comp_rps) * 100
                                report.append(f"- **vs {competitor.title()}**: {advantage:+.1f}% ({catzilla_rps:,.0f} vs {comp_rps:,.0f} RPS)")
                        report.append("")

        return "\n".join(report)


def main():
    """Main function for transparent benchmark runner"""
    parser = argparse.ArgumentParser(description="Transparent Feature-by-Feature Benchmark Runner")
    parser.add_argument("--category", help="Specific category to benchmark")
    parser.add_argument("--frameworks", nargs="+", default=FRAMEWORKS,
                       help="Frameworks to benchmark")
    parser.add_argument("--output-dir", default="results",
                       help="Output directory for results")
    parser.add_argument("--report", action="store_true",
                       help="Generate transparency report only")

    args = parser.parse_args()

    runner = TransparentBenchmarkRunner(args.output_dir)

    if args.report:
        # Generate report only
        report = runner.generate_transparent_report()
        report_file = runner.output_dir / "transparency_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"📊 Transparency report generated: {report_file}")
        print("\n" + report)
        return

    if args.category:
        # Run single category
        runner.run_single_category_benchmark(args.category, args.frameworks)
        print(f"\n✅ {args.category} benchmark completed!")
        print("📊 Run with --report to see comparison results")
    else:
        print("Please specify --category or use --report to see existing results")
        print("Available categories:", ", ".join(runner.test_categories))


if __name__ == "__main__":
    main()
