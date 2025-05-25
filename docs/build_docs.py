#!/usr/bin/env python3
"""
Simple script to build and optionally serve Catzilla documentation.
"""

import subprocess
import sys
import os
from pathlib import Path

def build_docs():
    """Build the documentation using Sphinx."""
    print("Building Catzilla documentation...")

    docs_dir = Path(__file__).parent
    build_dir = docs_dir / "_build" / "html"
    logo_source = docs_dir.parent / "logo.png"
    logo_dest = docs_dir / "_static" / "logo.png"

    # Ensure we're in the docs directory
    os.chdir(docs_dir)

    # Copy logo if it exists and target is missing or older
    if logo_source.exists():
        if not logo_dest.exists() or logo_source.stat().st_mtime > logo_dest.stat().st_mtime:
            print("📸 Copying logo to _static directory...")
            import shutil
            shutil.copy2(logo_source, logo_dest)

    # Build the documentation
    result = subprocess.run([
        "sphinx-build", "-b", "html", ".", str(build_dir)
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Documentation built successfully!")
        print(f"📂 Output directory: {build_dir}")
        print(f"🌐 Open: file://{build_dir.absolute()}/index.html")
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
        print("❌ Documentation not built yet. Run with 'build' first.")
        return False

    print(f"📡 Serving documentation on http://localhost:{port}")
    print("Press Ctrl+C to stop the server.")

    os.chdir(build_dir)
    subprocess.run([sys.executable, "-m", "http.server", str(port)])
    return True

def clean_docs():
    """Clean the built documentation."""
    docs_dir = Path(__file__).parent
    build_dir = docs_dir / "_build"

    if build_dir.exists():
        print("🧹 Cleaning documentation build directory...")
        import shutil
        shutil.rmtree(build_dir)
        print("✅ Build directory cleaned.")
    else:
        print("ℹ️  Build directory doesn't exist, nothing to clean.")
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python build_docs.py [build|serve|build-serve|clean]")
        print("  build       - Build the documentation")
        print("  serve       - Serve the documentation (requires build first)")
        print("  build-serve - Build and then serve the documentation")
        print("  clean       - Clean the build directory")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "build":
        build_docs()
    elif command == "serve":
        serve_docs()
    elif command == "build-serve":
        if build_docs():
            serve_docs()
    elif command == "clean":
        clean_docs()
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
