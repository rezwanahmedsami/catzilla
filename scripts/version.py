#!/usr/bin/env python3
"""
Catzilla Version Management

Single source of truth for version information across all files.
Usage:
    python scripts/version.py                 # Show current version
    python scripts/version.py 0.2.0          # Update to new version
    python scripts/version.py --check        # Verify version consistency
"""

import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

# 🎯 Single source of truth - change this to update version everywhere
VERSION = "0.1.0"

class VersionManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.version_files = {
            "pyproject.toml": self.update_pyproject_toml,
            "setup.py": self.update_setup_py,
            "python/catzilla/__init__.py": self.update_init_py,
            "CMakeLists.txt": self.update_cmake,
        }

    def get_current_versions(self) -> Dict[str, str]:
        """Get current version from each file"""
        versions = {}

        # pyproject.toml
        try:
            content = (self.root_dir / "pyproject.toml").read_text()
            match = re.search(r'version = "([^"]*)"', content)
            versions["pyproject.toml"] = match.group(1) if match else "NOT FOUND"
        except Exception as e:
            versions["pyproject.toml"] = f"ERROR: {e}"

        # setup.py
        try:
            content = (self.root_dir / "setup.py").read_text()
            match = re.search(r'version="([^"]*)"', content)
            versions["setup.py"] = match.group(1) if match else "NOT FOUND"
        except Exception as e:
            versions["setup.py"] = f"ERROR: {e}"

        # __init__.py
        try:
            content = (self.root_dir / "python/catzilla/__init__.py").read_text()
            match = re.search(r'__version__ = "([^"]*)"', content)
            versions["__init__.py"] = match.group(1) if match else "NOT FOUND"
        except Exception as e:
            versions["__init__.py"] = f"ERROR: {e}"

        # CMakeLists.txt
        try:
            content = (self.root_dir / "CMakeLists.txt").read_text()
            match = re.search(r'project\(catzilla VERSION ([0-9]+\.[0-9]+\.[0-9]+[^\s)]*)', content)
            versions["CMakeLists.txt"] = match.group(1) if match else "NOT FOUND"
        except Exception as e:
            versions["CMakeLists.txt"] = f"ERROR: {e}"

        return versions

    def check_version_consistency(self) -> Tuple[bool, List[str]]:
        """Check if all files have the same version"""
        versions = self.get_current_versions()
        issues = []

        # Filter out errors
        valid_versions = {k: v for k, v in versions.items() if not v.startswith("ERROR") and v != "NOT FOUND"}

        if not valid_versions:
            issues.append("❌ No valid versions found in any file!")
            return False, issues

        # Check consistency
        reference_version = list(valid_versions.values())[0]
        for file, version in valid_versions.items():
            if version != reference_version:
                issues.append(f"❌ {file}: {version} (expected {reference_version})")

        # Report errors
        for file, version in versions.items():
            if version.startswith("ERROR") or version == "NOT FOUND":
                issues.append(f"⚠️  {file}: {version}")

        return len(issues) == 0, issues

    def update_pyproject_toml(self, version: str):
        """Update version in pyproject.toml"""
        file_path = self.root_dir / "pyproject.toml"
        content = file_path.read_text()
        content = re.sub(r'version = "[^"]*"', f'version = "{version}"', content)
        file_path.write_text(content)
        print(f"✅ Updated pyproject.toml to {version}")

    def update_setup_py(self, version: str):
        """Update version in setup.py"""
        file_path = self.root_dir / "setup.py"
        content = file_path.read_text()
        content = re.sub(r'version="[^"]*"', f'version="{version}"', content)
        file_path.write_text(content)
        print(f"✅ Updated setup.py to {version}")

    def update_init_py(self, version: str):
        """Update version in __init__.py"""
        file_path = self.root_dir / "python/catzilla/__init__.py"
        content = file_path.read_text()
        content = re.sub(r'__version__ = "[^"]*"', f'__version__ = "{version}"', content)
        file_path.write_text(content)
        print(f"✅ Updated __init__.py to {version}")

    def update_cmake(self, version: str):
        """Update version in CMakeLists.txt"""
        file_path = self.root_dir / "CMakeLists.txt"
        content = file_path.read_text()
        content = re.sub(
            r'project\(catzilla VERSION [0-9]+\.[0-9]+\.[0-9]+[^\s)]*',
            f'project(catzilla VERSION {version}',
            content
        )
        file_path.write_text(content)
        print(f"✅ Updated CMakeLists.txt to {version}")

    def update_all_versions(self, new_version: str):
        """Update version in all files"""
        print(f"🔄 Updating Catzilla version to {new_version}")

        for file_name, update_func in self.version_files.items():
            try:
                update_func(new_version)
            except Exception as e:
                print(f"❌ Failed to update {file_name}: {e}")
                return False

        # Update this script's VERSION constant
        self.update_version_script(new_version)

        print(f"🎉 All files updated to version {new_version}")
        return True

    def update_version_script(self, new_version: str):
        """Update VERSION constant in this script"""
        script_path = Path(__file__)
        content = script_path.read_text()
        content = re.sub(r'VERSION = "[^"]*"', f'VERSION = "{new_version}"', content)
        script_path.write_text(content)
        print(f"✅ Updated version.py to {new_version}")

    def show_current_status(self):
        """Show current version status"""
        print("📋 Catzilla Version Status")
        print("=" * 50)

        versions = self.get_current_versions()
        for file, version in versions.items():
            status = "✅" if not version.startswith("ERROR") and version != "NOT FOUND" else "❌"
            print(f"{status} {file:<20} {version}")

        print()
        consistent, issues = self.check_version_consistency()
        if consistent:
            print("✅ All versions are consistent!")
        else:
            print("⚠️  Version inconsistencies found:")
            for issue in issues:
                print(f"   {issue}")

def main():
    parser = argparse.ArgumentParser(
        description="Catzilla Version Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/version.py                 # Show current status
  python scripts/version.py 0.2.0          # Update to version 0.2.0
  python scripts/version.py --check        # Check version consistency
  python scripts/version.py --current      # Show current version from script
        """
    )

    parser.add_argument("version", nargs="?", help="New version to set")
    parser.add_argument("--check", action="store_true", help="Check version consistency")
    parser.add_argument("--current", action="store_true", help="Show current version from script")

    args = parser.parse_args()

    vm = VersionManager()

    if args.current:
        print(f"Current version (from script): {VERSION}")
        return

    if args.check:
        vm.show_current_status()
        consistent, _ = vm.check_version_consistency()
        sys.exit(0 if consistent else 1)

    if args.version:
        # Validate version format
        if not re.match(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]*)?$', args.version):
            print(f"❌ Invalid version format: {args.version}")
            print("   Expected format: MAJOR.MINOR.PATCH (e.g., 0.2.0, 1.0.0-beta)")
            sys.exit(1)

        success = vm.update_all_versions(args.version)
        if success:
            print(f"\n📋 Next steps:")
            print(f"   git add .")
            print(f"   git commit -m 'Bump version to {args.version}'")
            print(f"   git tag v{args.version}")
            print(f"   git push origin v{args.version}")
        sys.exit(0 if success else 1)

    # Default: show status
    vm.show_current_status()

if __name__ == "__main__":
    main()
