#!/usr/bin/env python3
"""
Catzilla Version Management

Single source of truth for version information across all files.
Professional version handling with CMake compatibility.

Usage:
    python scripts/version.py                 # Show current version
    python scripts/version.py 0.2.0          # Update to new version
    python scripts/version.py 0.2.1b1        # Update to beta version
    python scripts/version.py --check        # Verify version consistency
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from packaging.version import InvalidVersion, Version

VERSION = "0.2.2"


class VersionManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.version_files = {
            "pyproject.toml": self.update_pyproject_toml,
            "setup.py": self.update_setup_py,
            "python/catzilla/__init__.py": self.update_init_py,
            "CMakeLists.txt": self.update_cmake,
        }

    def normalize_version(self, version_string: str) -> str:
        """Normalize a version string using Python packaging rules."""
        return str(Version(version_string))

    def get_cmake_version(self, version_string: str) -> str:
        """Extract CMake-compatible version (MAJOR.MINOR.PATCH only)."""
        parsed_version = Version(version_string)
        return ".".join(str(part) for part in parsed_version.release[:3])

    def get_base_version(self, version_string: str) -> str:
        """Extract MAJOR.MINOR.PATCH from a package version."""
        parsed_version = Version(version_string)
        return ".".join(str(part) for part in parsed_version.release[:3])

    def get_current_versions(self) -> Dict[str, str]:
        """Get current version from each file."""
        versions: Dict[str, str] = {}

        try:
            content = (self.root_dir / "pyproject.toml").read_text()
            match = re.search(r'version = "([^"]*)"', content)
            versions["pyproject.toml"] = match.group(1) if match else "NOT FOUND"
        except Exception as exc:
            versions["pyproject.toml"] = f"ERROR: {exc}"

        try:
            content = (self.root_dir / "setup.py").read_text()
            match = re.search(r'version="([^"]*)"', content)
            versions["setup.py"] = match.group(1) if match else "NOT FOUND"
        except Exception as exc:
            versions["setup.py"] = f"ERROR: {exc}"

        try:
            content = (self.root_dir / "python/catzilla/__init__.py").read_text()
            match = re.search(r'__version__ = "([^"]*)"', content)
            versions["__init__.py"] = match.group(1) if match else "NOT FOUND"
        except Exception as exc:
            versions["__init__.py"] = f"ERROR: {exc}"

        try:
            content = (self.root_dir / "CMakeLists.txt").read_text()
            match = re.search(r'project\(catzilla VERSION ([0-9]+\.[0-9]+\.[0-9]+)', content)
            if match:
                cmake_version = match.group(1)
                expected_cmake = self.get_cmake_version(VERSION)
                if cmake_version == expected_cmake:
                    versions["CMakeLists.txt"] = f"{cmake_version} (CMake format)"
                else:
                    versions["CMakeLists.txt"] = f"{cmake_version} (expected {expected_cmake})"
            else:
                versions["CMakeLists.txt"] = "NOT FOUND"
        except Exception as exc:
            versions["CMakeLists.txt"] = f"ERROR: {exc}"

        return versions

    def check_version_consistency(self) -> Tuple[bool, List[str]]:
        """Check if all tracked files have consistent versions."""
        versions = self.get_current_versions()
        issues: List[str] = []
        expected_cmake_version = self.get_cmake_version(VERSION)

        for file_name, version in versions.items():
            if version.startswith("ERROR") or version == "NOT FOUND":
                issues.append(f"⚠️  {file_name}: {version}")
                continue

            if file_name == "CMakeLists.txt":
                cmake_match = re.match(r'([0-9]+\.[0-9]+\.[0-9]+)', version)
                if not cmake_match:
                    issues.append(f"❌ {file_name}: Invalid format - {version}")
                elif cmake_match.group(1) != expected_cmake_version:
                    issues.append(
                        f"❌ {file_name}: {cmake_match.group(1)} (expected {expected_cmake_version})"
                    )
                continue

            if version != VERSION:
                issues.append(f"❌ {file_name}: {version} (expected {VERSION})")

        return len(issues) == 0, issues

    def update_pyproject_toml(self, version: str):
        file_path = self.root_dir / "pyproject.toml"
        content = file_path.read_text()
        content = re.sub(r'version = "[^"]*"', f'version = "{version}"', content)
        file_path.write_text(content)
        print(f"✅ Updated pyproject.toml to {version}")

    def update_setup_py(self, version: str):
        file_path = self.root_dir / "setup.py"
        content = file_path.read_text()
        content = re.sub(r'version="[^"]*"', f'version="{version}"', content)
        file_path.write_text(content)
        print(f"✅ Updated setup.py to {version}")

    def update_init_py(self, version: str):
        file_path = self.root_dir / "python/catzilla/__init__.py"
        content = file_path.read_text()
        content = re.sub(r'__version__ = "[^"]*"', f'__version__ = "{version}"', content)
        file_path.write_text(content)
        print(f"✅ Updated __init__.py to {version}")

    def update_cmake(self, version: str):
        file_path = self.root_dir / "CMakeLists.txt"
        content = file_path.read_text()
        cmake_version = self.get_cmake_version(version)
        content = re.sub(
            r'project\(catzilla VERSION [0-9]+\.[0-9]+\.[0-9]+',
            f'project(catzilla VERSION {cmake_version}',
            content,
        )
        file_path.write_text(content)
        print(f"✅ Updated CMakeLists.txt to {cmake_version} (CMake format)")
        if version != cmake_version:
            print(f"   📐 Note: CMake uses {cmake_version}, other files use {version}")

    def update_version_script(self, new_version: str):
        script_path = Path(__file__)
        content = script_path.read_text()
        content = re.sub(r'VERSION = "[^"]*"', f'VERSION = "{new_version}"', content, count=1)
        script_path.write_text(content)
        print(f"✅ Updated version.py to {new_version}")

    def update_all_versions(self, new_version: str):
        normalized_version = self.normalize_version(new_version)
        base_version = self.get_base_version(normalized_version)
        cmake_version = self.get_cmake_version(normalized_version)

        print(f"🔄 Updating Catzilla version to {normalized_version}")
        print(f"📦 Project files will use: {normalized_version} (package version)")
        print(f"📐 CMake will use: {cmake_version} (CMake format)")
        print(f"🏷️  Git tag will use: {normalized_version} (full version)")
        print()

        for file_name, update_func in self.version_files.items():
            try:
                if file_name == "CMakeLists.txt":
                    update_func(base_version)
                else:
                    update_func(normalized_version)
            except Exception as exc:
                print(f"❌ Failed to update {file_name}: {exc}")
                return False

        self.update_version_script(normalized_version)

        print("\n🎉 All files updated!")
        print("💡 Professional version handling:")
        print(f"   • Project files: {normalized_version} (package version)")
        print(f"   • CMake: {cmake_version} (numeric only)")
        print(f"   • Git tag: v{normalized_version} (full version)")
        if normalized_version != base_version:
            print(
                f"   📋 Note: Pre-release identifier '{normalized_version[len(base_version):]}' is omitted only for CMake"
            )
        return True

    def show_current_status(self):
        print("📋 Catzilla Version Status")
        print("=" * 50)

        versions = self.get_current_versions()
        for file_name, version in versions.items():
            if file_name == "CMakeLists.txt":
                status = "✅" if "CMake format" in version or not version.startswith("ERROR") else "❌"
            else:
                status = "✅" if not version.startswith("ERROR") and version != "NOT FOUND" else "❌"
            print(f"{status} {file_name:<20} {version}")

        print()
        print(f"🎯 Target version: {VERSION}")
        print(f"📐 CMake version: {self.get_cmake_version(VERSION)} (CMake format)")
        print()

        consistent, issues = self.check_version_consistency()
        if consistent:
            print("✅ All versions are consistent!")
            print("💡 Professional version strategy:")
            print("   • Python files use full package versions")
            print("   • CMake uses base version (tool limitation)")
            print("   • This follows Python packaging and CMake constraints")
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
  python scripts/version.py 0.2.1b1        # Update to beta version
  python scripts/version.py --check        # Check version consistency
  python scripts/version.py --current      # Show current version from script

Professional Notes:
  • CMake versions are automatically converted to MAJOR.MINOR.PATCH format
  • Python/PyPI supports PEP 440 prereleases like a1, b1, and rc1
  • This keeps package metadata correct while preserving CMake compatibility
        """,
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
        if not re.match(r'^\d+\.\d+\.\d+((a|b|rc)\d+)?$', args.version):
            print(f"❌ Invalid version format: {args.version}")
            print("   Expected format: MAJOR.MINOR.PATCH or PEP 440 pre-release (e.g., 0.2.0, 0.2.1b1, 1.0.0rc1)")
            sys.exit(1)

        try:
            normalized_version = vm.normalize_version(args.version)
        except InvalidVersion as exc:
            print(f"❌ Invalid version: {args.version}")
            print(f"   {exc}")
            sys.exit(1)

        success = vm.update_all_versions(normalized_version)
        if success:
            print("\n📋 Next steps:")
            print("   git add pyproject.toml setup.py python/catzilla/__init__.py CMakeLists.txt scripts/version.py")
            print(f"   git commit -m 'Bump version to {normalized_version}'")
            print(f"   git tag v{normalized_version}")
            print(f"   git push origin v{normalized_version}")
        sys.exit(0 if success else 1)

    vm.show_current_status()


if __name__ == "__main__":
    main()
