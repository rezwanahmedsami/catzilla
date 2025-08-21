#!/usr/bin/env python3
"""
Catzilla Version Management

Single source of truth for version information across all files.
Professional version handling with CMake compatibility.

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
VERSION = "0.2.0"

class VersionManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.version_files = {
            "pyproject.toml": self.update_pyproject_toml,
            "setup.py": self.update_setup_py,
            "python/catzilla/__init__.py": self.update_init_py,
            "CMakeLists.txt": self.update_cmake,
        }

    def get_cmake_version(self, version_string: str) -> str:
        """Extract CMake-compatible version (MAJOR.MINOR.PATCH only)"""
        # CMake only accepts numeric MAJOR.MINOR.PATCH format
        match = re.match(r'(\d+\.\d+\.\d+)', version_string)
        return match.group(1) if match else "0.1.0"

    def get_base_version(self, version_string: str) -> str:
        """Extract base semantic version without pre-release identifiers (MAJOR.MINOR.PATCH only)"""
        # Extract just the base version for project files
        match = re.match(r'(\d+\.\d+\.\d+)', version_string)
        return match.group(1) if match else "0.1.0"

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

        # CMakeLists.txt (special handling for CMake format)
        try:
            content = (self.root_dir / "CMakeLists.txt").read_text()
            match = re.search(r'project\(catzilla VERSION ([0-9]+\.[0-9]+\.[0-9]+)', content)
            if match:
                cmake_version = match.group(1)
                # Show both CMake version and expected full version for comparison
                expected_cmake = self.get_cmake_version(VERSION)
                if cmake_version == expected_cmake:
                    versions["CMakeLists.txt"] = f"{cmake_version} (CMake format)"
                else:
                    versions["CMakeLists.txt"] = f"{cmake_version} (expected {expected_cmake})"
            else:
                versions["CMakeLists.txt"] = "NOT FOUND"
        except Exception as e:
            versions["CMakeLists.txt"] = f"ERROR: {e}"

        return versions

    def check_version_consistency(self) -> Tuple[bool, List[str]]:
        """Check if all files have the same version (with CMake format consideration)"""
        versions = self.get_current_versions()
        issues = []

        # Filter out errors and extract core versions for comparison
        valid_versions = {}
        expected_cmake_version = self.get_cmake_version(VERSION)

        for file, version in versions.items():
            if version.startswith("ERROR") or version == "NOT FOUND":
                issues.append(f"⚠️  {file}: {version}")
            elif file == "CMakeLists.txt":
                # Special handling for CMake - extract just the version number
                cmake_match = re.match(r'([0-9]+\.[0-9]+\.[0-9]+)', version)
                if cmake_match:
                    cmake_version = cmake_match.group(1)
                    if cmake_version == expected_cmake_version:
                        valid_versions[file] = "CMAKE_OK"
                    else:
                        issues.append(f"❌ {file}: {cmake_version} (expected {expected_cmake_version})")
                else:
                    issues.append(f"❌ {file}: Invalid format - {version}")
            else:
                # Python files should have full version
                if version == VERSION:
                    valid_versions[file] = version
                else:
                    issues.append(f"❌ {file}: {version} (expected {VERSION})")

        # If no issues, all versions are consistent
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
        """Update version in CMakeLists.txt (CMake format only)"""
        file_path = self.root_dir / "CMakeLists.txt"
        content = file_path.read_text()

        # Use CMake-compatible version (remove pre-release identifiers)
        cmake_version = self.get_cmake_version(version)

        content = re.sub(
            r'project\(catzilla VERSION [0-9]+\.[0-9]+\.[0-9]+',
            f'project(catzilla VERSION {cmake_version}',
            content
        )
        file_path.write_text(content)
        print(f"✅ Updated CMakeLists.txt to {cmake_version} (CMake format)")
        if version != cmake_version:
            print(f"   📐 Note: CMake uses {cmake_version}, other files use {version}")

    def update_all_versions(self, new_version: str):
        """Update version in all files"""
        print(f"🔄 Updating Catzilla version to {new_version}")

        # Extract base version for project files (removes pre-release identifiers)
        base_version = self.get_base_version(new_version)
        cmake_version = self.get_cmake_version(new_version)

        print(f"📦 Project files will use: {base_version} (base semantic version)")
        print(f"📐 CMake will use: {cmake_version} (CMake format)")
        print(f"🏷️  Git tag will use: {new_version} (full version)")
        print()

        for file_name, update_func in self.version_files.items():
            try:
                if file_name == "CMakeLists.txt":
                    # CMake uses base version (already handled by get_cmake_version)
                    update_func(base_version)
                else:
                    # All other files use base version (no pre-release identifiers)
                    update_func(base_version)
            except Exception as e:
                print(f"❌ Failed to update {file_name}: {e}")
                return False

        # Update this script's VERSION constant to the base version
        self.update_version_script(base_version)

        print(f"\n🎉 All files updated!")
        print(f"💡 Professional version handling:")
        print(f"   • Project files: {base_version} (base semantic version)")
        print(f"   • CMake: {cmake_version} (numeric only)")
        print(f"   • Git tag: v{new_version} (full version with pre-release)")
        if new_version != base_version:
            print(f"   📋 Note: Pre-release identifier '{new_version[len(base_version):]}' is only used for git tag")
        return True

    def update_version_script(self, new_version: str):
        """Update VERSION constant in this script"""
        script_path = Path(__file__)
        content = script_path.read_text()
        content = re.sub(r'VERSION = "0.2.0"]*"', f'VERSION = "0.2.0"', content)
        script_path.write_text(content)
        print(f"✅ Updated version.py to {new_version}")

    def show_current_status(self):
        """Show current version status"""
        print("📋 Catzilla Version Status")
        print("=" * 50)

        versions = self.get_current_versions()
        for file, version in versions.items():
            if file == "CMakeLists.txt":
                status = "✅" if "CMake format" in version or not version.startswith("ERROR") else "❌"
            else:
                status = "✅" if not version.startswith("ERROR") and version != "NOT FOUND" else "❌"
            print(f"{status} {file:<20} {version}")

        print()
        print(f"🎯 Target version: {VERSION}")
        print(f"📐 CMake version: {self.get_cmake_version(VERSION)} (CMake format)")
        print()

        consistent, issues = self.check_version_consistency()
        if consistent:
            print("✅ All versions are consistent!")
            print("💡 Professional version strategy:")
            print("   • Python files use full semver with pre-release")
            print("   • CMake uses base version (tool limitation)")
            print("   • This follows industry best practices")
        else:
            print("⚠️  Version inconsistencies found:")
            for issue in issues:
                print(f"   {issue}")

def main():
    parser = argparse.ArgumentParser(
        description="Catzilla Professional Version Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/version.py                 # Show current status
  python scripts/version.py 0.2.0          # Update to version 0.2.0
  python scripts/version.py 0.2.0-beta     # Update to beta version
  python scripts/version.py --check        # Check version consistency
  python scripts/version.py --current      # Show current version from script

Professional Notes:
  • CMake versions are automatically converted to MAJOR.MINOR.PATCH format
  • Python/PyPI supports full semantic versioning including pre-release
  • This follows industry standards used by LLVM, OpenCV, Boost, etc.
        """
    )

    parser.add_argument("version", nargs="?", help="New version to set")
    parser.add_argument("--check", action="store_true", help="Check version consistency")
    parser.add_argument("--current", action="store_true", help="Show current version from script")

    args = parser.parse_args()

    vm = VersionManager()

    if args.current:
        print(f"Current version (from script): {VERSION}")
        print(f"CMake format: {vm.get_cmake_version(VERSION)}")
        return

    if args.check:
        vm.show_current_status()
        consistent, _ = vm.check_version_consistency()
        sys.exit(0 if consistent else 1)

    if args.version:
        # Validate version format
        if not re.match(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]*)?$', args.version):
            print(f"❌ Invalid version format: {args.version}")
            print("   Expected format: MAJOR.MINOR.PATCH[-PRERELEASE] (e.g., 0.2.0, 1.0.0-beta)")
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
