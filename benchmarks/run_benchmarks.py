#!/usr/bin/env python3
"""
Enhanced Benchmark Runner with Feature Support

This script provides a Python interface to the feature-based benchmark system,
maintaining compatibility with the old visualization and reporting system.
"""

import os
import sys
import json
import time
import subprocess
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add tools directory to path for imports
BENCHMARK_DIR = Path(__file__).parent
TOOLS_DIR = BENCHMARK_DIR / "tools"
RESULTS_DIR = BENCHMARK_DIR / "results"

sys.path.insert(0, str(TOOLS_DIR))

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_status(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def print_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def print_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

class FeatureBenchmarkRunner:
    """Enhanced benchmark runner with feature support"""

    def __init__(self):
        self.benchmark_dir = BENCHMARK_DIR
        self.results_dir = RESULTS_DIR
        self.servers_dir = BENCHMARK_DIR / "servers"
        self.tools_dir = TOOLS_DIR
        self.available_features = self._discover_features()

        # Ensure results directory exists
        self.results_dir.mkdir(exist_ok=True)

    def _discover_features(self) -> List[str]:
        """Discover available feature categories"""
        features = []
        if self.servers_dir.exists():
            for item in self.servers_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    features.append(item.name)
        return sorted(features)

    def run_feature_benchmark(self, feature: str, base_port: int = 8000) -> bool:
        """Run benchmark for a specific feature using the shell script"""
        print_status(f"Running benchmark for feature: {feature}")

        # Use the shell script runner
        script_path = self.benchmark_dir / "run_feature_benchmarks.sh"
        if not script_path.exists():
            print_error(f"Benchmark script not found: {script_path}")
            return False

        try:
            # Run the shell script with the specific feature
            cmd = [str(script_path), feature, str(base_port)]
            result = subprocess.run(
                cmd,
                cwd=str(self.benchmark_dir),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                print_success(f"Feature benchmark completed: {feature}")
                return True
            else:
                print_error(f"Feature benchmark failed: {feature}")
                print(f"Error output: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print_error(f"Feature benchmark timed out: {feature}")
            return False
        except Exception as e:
            print_error(f"Error running feature benchmark: {e}")
            return False

    def run_all_benchmarks(self, base_port: int = 8000) -> Dict[str, bool]:
        """Run benchmarks for all available features"""
        print_status("Running benchmarks for all available features")
        print(f"Available features: {', '.join(self.available_features)}")

        results = {}
        current_port = base_port

        for feature in self.available_features:
            print(f"\n{'='*60}")
            print_status(f"Starting benchmark for feature: {feature}")
            print(f"{'='*60}")

            success = self.run_feature_benchmark(feature, current_port)
            results[feature] = success

            if success:
                print_success(f"✅ {feature} benchmark completed")
            else:
                print_error(f"❌ {feature} benchmark failed")

            current_port += 100  # Space out ports for different features
            time.sleep(2)  # Brief pause between features

        return results

    def generate_report(self) -> bool:
        """Generate comprehensive report using existing tools"""
        print_status("Generating comprehensive benchmark report...")

        try:
            # Use the existing system_info.py if available
            system_info_script = self.tools_dir / "system_info.py"
            if system_info_script.exists():
                system_info_file = self.results_dir / "system_info.json"
                cmd = [sys.executable, str(system_info_script), "--output", str(system_info_file), "--format", "json"]
                subprocess.run(cmd, check=True)
                print_success("System information collected")

            # Generate summary report (compatible with old format)
            self._generate_summary_report()

            # Generate visualizations if available
            viz_script = self.tools_dir / "visualize_results.py"
            if viz_script.exists():
                print_status("Generating performance charts...")
                cmd = [sys.executable, str(viz_script), str(self.results_dir)]
                subprocess.run(cmd)
                print_success("Performance charts generated")

            return True

        except Exception as e:
            print_error(f"Error generating report: {e}")
            return False

    def _generate_summary_report(self):
        """Generate summary report compatible with old visualization system"""
        summary_file = self.results_dir / "benchmark_summary.json"

        # Collect all individual JSON results
        results = []
        for json_file in self.results_dir.glob("*.json"):
            if json_file.name not in ["benchmark_summary.json", "system_info.json"]:
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        results.append(data)
                except Exception as e:
                    print_warning(f"Failed to load {json_file}: {e}")

        # Create summary in old format for compatibility
        summary = {
            "benchmark_run": {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "total_tests": len(results),
                "features_tested": list(set(r.get("feature_category", "unknown") for r in results))
            },
            "system_info_file": "system_info.json",
            "results": results
        }

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print_success(f"Summary report generated: {summary_file}")

    def list_features(self):
        """List available feature categories"""
        print("Available feature categories:")
        for feature in self.available_features:
            feature_dir = self.servers_dir / feature
            endpoints_file = feature_dir / "endpoints.json"

            # Load feature description if available
            description = "No description available"
            if endpoints_file.exists():
                try:
                    with open(endpoints_file, 'r') as f:
                        config = json.load(f)
                        description = config.get("description", description)
                except:
                    pass

            # Count available servers
            server_count = len(list(feature_dir.glob("*.py")))

            print(f"  🎯 {feature:<25} - {description}")
            print(f"     {server_count} server implementations available")

    def check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        print_status("Checking dependencies...")

        # Check for wrk
        try:
            subprocess.run(["wrk", "--version"], capture_output=True, check=True)
            print_success("✅ wrk found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_error("❌ wrk not found. Install with: brew install wrk (macOS) or apt-get install wrk (Ubuntu)")
            return False

        # Check for Python
        if sys.version_info < (3, 7):
            print_error("❌ Python 3.7+ required")
            return False
        print_success("✅ Python version compatible")

        # Check for benchmark script
        script_path = self.benchmark_dir / "run_feature_benchmarks.sh"
        if not script_path.exists():
            print_error(f"❌ Benchmark script not found: {script_path}")
            return False
        print_success("✅ Benchmark script found")

        return True

def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Catzilla Feature-Based Benchmark Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_benchmarks.py --list                    # List available features
  python run_benchmarks.py --feature basic          # Run basic benchmarks
  python run_benchmarks.py --feature middleware     # Run middleware benchmarks
  python run_benchmarks.py --all                    # Run all benchmarks
  python run_benchmarks.py --all --port 9000        # Run all benchmarks starting from port 9000
  python run_benchmarks.py --check                  # Check dependencies
        """
    )

    parser.add_argument('--feature', '-f', help='Run benchmarks for specific feature category')
    parser.add_argument('--all', '-a', action='store_true', help='Run benchmarks for all features')
    parser.add_argument('--list', '-l', action='store_true', help='List available feature categories')
    parser.add_argument('--port', '-p', type=int, default=8000, help='Base port number (default: 8000)')
    parser.add_argument('--check', '-c', action='store_true', help='Check dependencies')
    parser.add_argument('--report-only', '-r', action='store_true', help='Generate report from existing results')

    args = parser.parse_args()

    runner = FeatureBenchmarkRunner()

    print(f"{Colors.BLUE}🚀 Catzilla Enhanced Feature-Based Benchmark Runner{Colors.NC}")
    print("=" * 60)

    if args.check:
        success = runner.check_dependencies()
        sys.exit(0 if success else 1)

    if args.list:
        runner.list_features()
        return

    if args.report_only:
        success = runner.generate_report()
        print_success("📊 Report generation completed") if success else print_error("❌ Report generation failed")
        return

    # Check dependencies before running benchmarks
    if not runner.check_dependencies():
        print_error("Dependency check failed. Please install missing dependencies.")
        sys.exit(1)

    if args.all:
        print_status("Running benchmarks for all available features...")
        results = runner.run_all_benchmarks(args.port)

        # Print summary
        print(f"\n{Colors.BLUE}📊 BENCHMARK SUMMARY{Colors.NC}")
        print("=" * 60)
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)

        for feature, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"  {feature:<25} - {status}")

        print(f"\nOverall: {success_count}/{total_count} features completed successfully")

        # Generate comprehensive report
        print("\n" + "=" * 60)
        success = runner.generate_report()

        if success and success_count == total_count:
            print_success("🎉 All benchmarks completed successfully!")
        else:
            print_warning("⚠️ Some benchmarks failed. Check the results above.")

    elif args.feature:
        if args.feature not in runner.available_features:
            print_error(f"Feature '{args.feature}' not found.")
            print("Available features:")
            for feature in runner.available_features:
                print(f"  - {feature}")
            sys.exit(1)

        success = runner.run_feature_benchmark(args.feature, args.port)

        if success:
            # Generate report for this feature
            runner.generate_report()
            print_success(f"✅ Feature benchmark completed: {args.feature}")
        else:
            print_error(f"❌ Feature benchmark failed: {args.feature}")
            sys.exit(1)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
