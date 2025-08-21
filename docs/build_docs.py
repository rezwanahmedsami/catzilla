#!/usr/bin/env python3
"""
Build script for Catzilla v0.2.0 documentation.
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def build_docs():
    """Build the documentation using Sphinx."""
    print("🚀 Building Catzilla v0.2.0 Documentation...")

    docs_dir = Path(__file__).parent
    build_dir = docs_dir / "_build" / "html"
    logo_source = docs_dir.parent / "logo.png"
    logo_dest = docs_dir / "_static" / "logo.png"

    # Ensure we're in the docs directory
    os.chdir(docs_dir)

    # Copy logo if it exists
    if logo_source.exists():
        if not logo_dest.exists() or logo_source.stat().st_mtime > logo_dest.stat().st_mtime:
            print("📸 Copying logo to _static directory...")
            shutil.copy2(logo_source, logo_dest)

    # Clean previous build
    if build_dir.exists():
        print("🧹 Cleaning previous build...")
        shutil.rmtree(build_dir)

    # Build the documentation
    print("📚 Building documentation with Sphinx...")
    result = subprocess.run([
        "sphinx-build", "-b", "html", ".", str(build_dir)
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Documentation built successfully!")
        print(f"📂 Output directory: {build_dir}")
        print(f"🌐 Open: file://{build_dir.absolute()}/index.html")

        # Show some stats
        html_files = list(build_dir.rglob("*.html"))
        print(f"📄 Generated {len(html_files)} HTML pages")

        return True
    else:
        print("❌ Documentation build failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False

def serve_docs(port=8080):
    """Serve the documentation using Python's built-in HTTP server."""
    docs_dir = Path(__file__).parent
    build_dir = docs_dir / "_build" / "html"

    if not build_dir.exists():
        print("❌ Documentation not built yet. Run build first.")
        return False

    print(f"🌐 Serving documentation on http://localhost:{port}")
    print("📖 Press Ctrl+C to stop the server")

    os.chdir(build_dir)

    try:
        subprocess.run([
            sys.executable, "-m", "http.server", str(port)
        ])
    except KeyboardInterrupt:
        print("\\n📖 Documentation server stopped")
        return True

def clean_build():
    """Clean the build directory."""
    docs_dir = Path(__file__).parent
    build_dir = docs_dir / "_build"

    if build_dir.exists():
        print("🧹 Cleaning build directory...")
        shutil.rmtree(build_dir)
        print("✅ Build directory cleaned")
    else:
        print("ℹ️  Build directory doesn't exist")

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking documentation dependencies...")

    required_packages = [
        "sphinx",
        "sphinx_rtd_theme",
        "myst_parser",
        "sphinx_sitemap",
        "sphinx_copybutton"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)

    if missing_packages:
        print(f"\\n📦 Install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    print("✅ All dependencies are installed")
    return True

def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Catzilla v0.2.0 Documentation Builder"
    )

    parser.add_argument(
        "command",
        choices=["build", "serve", "clean", "check"],
        help="Command to run"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for serve command (default: 8080)"
    )

    args = parser.parse_args()

    print("📚 Catzilla v0.2.0 Documentation Builder")
    print("=" * 50)

    if args.command == "check":
        success = check_dependencies()
        sys.exit(0 if success else 1)

    elif args.command == "clean":
        clean_build()

    elif args.command == "build":
        if not check_dependencies():
            sys.exit(1)
        success = build_docs()
        sys.exit(0 if success else 1)

    elif args.command == "serve":
        if not check_dependencies():
            sys.exit(1)
        success = serve_docs(args.port)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
