#!/usr/bin/env python3
"""
Catzilla Quick Release Manager

A professional-grade helper script for creating quick releases when version is already prepared.
This is designed for rapid hotfixes and tags when you've already done version management.

For comprehensive releases with testing and version updates, use: ./scripts/bump_version.sh

Usage:
    python scripts/release.py v1.2.3           # Quick stable release
    python scripts/release.py v1.2.3-hotfix    # Quick pre-release
    python scripts/release.py v1.2.3 --dry-run # Preview changes
"""

import re
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Tuple


def run_command(cmd: str, capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd, shell=True, capture_output=capture_output, text=True
    )
    return result.returncode, result.stdout, result.stderr


def get_base_version(version: str) -> str:
    """Extract base semantic version without pre-release identifiers."""
    # Remove 'v' prefix if present
    clean_version = version.lstrip('v')
    # Extract just MAJOR.MINOR.PATCH
    match = re.match(r'(\d+\.\d+\.\d+)', clean_version)
    return match.group(1) if match else clean_version


def validate_version(version: str) -> Tuple[bool, str, bool]:
    """
    Validate version format and determine if it's stable or pre-release.

    Returns:
        (is_valid, clean_version, is_stable)
    """
    # Remove 'v' prefix if present
    clean_version = version.lstrip('v')

    # Semantic version pattern
    stable_pattern = r'^(\d+)\.(\d+)\.(\d+)$'
    prerelease_pattern = r'^(\d+)\.(\d+)\.(\d+)-(.+)$'

    if re.match(stable_pattern, clean_version):
        return True, clean_version, True
    elif re.match(prerelease_pattern, clean_version):
        return True, clean_version, False
    else:
        return False, clean_version, False


def check_git_status():
    """Check if git working directory is clean."""
    exit_code, stdout, stderr = run_command("git status --porcelain")
    if exit_code != 0:
        print(f"❌ Error checking git status: {stderr}")
        return False

    if stdout.strip():
        print("⚠️ Warning: You have uncommitted changes:")
        print(stdout)
        response = input("Continue anyway? (y/N): ")
        return response.lower() == 'y'

    return True


def get_current_version():
    """Get current version from pyproject.toml."""
    try:
        with open("pyproject.toml", "r") as f:
            content = f.read()
            match = re.search(r'version = "([^"]+)"', content)
            if match:
                return match.group(1)
    except FileNotFoundError:
        pass
    return None


def check_existing_tag(tag_name: str) -> bool:
    """Check if tag already exists."""
    exit_code, stdout, stderr = run_command(f"git tag -l {tag_name}")
    return bool(stdout.strip())


def update_version_if_needed(clean_version: str, force_update: bool = False) -> bool:
    """Update version in pyproject.toml if needed."""
    # Extract base version for project files (no pre-release identifiers)
    base_version = get_base_version(clean_version)
    current_version = get_current_version()

    if current_version == base_version and not force_update:
        print(f"✅ Version already matches: {base_version}")
        return True

    if current_version and current_version != base_version:
        print(f"⚠️ Version mismatch detected:")
        print(f"   File version: {current_version}")
        print(f"   Target base version: {base_version}")

        if clean_version != base_version:
            print(f"   📋 Note: Git tag will use full version: {clean_version}")

        if not force_update:
            response = input("Update pyproject.toml to match base version? (y/N): ")
            if response.lower() != 'y':
                print("❌ Version mismatch not resolved")
                return False

    # Update pyproject.toml with base version only
    try:
        with open("pyproject.toml", "r") as f:
            content = f.read()

        content = re.sub(
            r'version = "[^"]+"',
            f'version = "{base_version}"',
            content
        )

        with open("pyproject.toml", "w") as f:
            f.write(content)

        print(f"✅ Updated version in pyproject.toml to {base_version}")
        if clean_version != base_version:
            print(f"   📋 Note: Git tag will use full version: {clean_version}")
        return True
    except Exception as e:
        print(f"❌ Error updating pyproject.toml: {e}")
        return False


def check_version_script_exists() -> bool:
    """Check if the comprehensive version script exists."""
    version_script = Path("scripts/version.py")
    bump_script = Path("scripts/bump_version.sh")

    if version_script.exists() or bump_script.exists():
        return True
    return False


def check_for_recent_bump_version_usage():
    """Check if bump_version.sh was recently used to avoid conflicts."""
    try:
        # Check recent commits for bump_version.sh patterns
        exit_code, stdout, _ = run_command("git log --oneline -5")
        if exit_code == 0:
            recent_commits = stdout.lower()
            if "bump version" in recent_commits or "🔖" in recent_commits:
                print("⚠️ Warning: Recent commits suggest bump_version.sh was used")
                print("   This might indicate version files are already updated")
                print("   Consider using --update-version flag or check version consistency")
                return True
    except Exception:
        pass
    return False


def validate_environment():
    """Validate the environment before creating release."""
    issues = []

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        issues.append("pyproject.toml not found - run from project root")

    # Check if git is available
    exit_code, _, _ = run_command("git --version")
    if exit_code != 0:
        issues.append("git command not available")

    # Check if we're in a git repository
    exit_code, _, _ = run_command("git rev-parse --git-dir")
    if exit_code != 0:
        issues.append("not in a git repository")

    return issues


def create_quick_release(version: str, dry_run: bool = False, update_version: bool = False):
    """Create a quick release (tag + push only, minimal validation)."""
    print(f"⚡ Quick Release Manager for version {version}")

    # Show tool guidance
    if check_version_script_exists():
        print("💡 For comprehensive releases with tests, use: ./scripts/bump_version.sh")
        print("💡 This tool is for quick releases when version is already prepared")
        print()

    # Validate version
    is_valid, clean_version, is_stable = validate_version(version)
    if not is_valid:
        print(f"❌ Invalid version format: {version}")
        print("   Expected: v1.2.3 (stable) or v1.2.3-alpha1 (pre-release)")
        return False

    # Determine release type
    release_type = "stable" if is_stable else "pre-release"
    pypi_action = "will be published to PyPI" if is_stable else "will NOT be published to PyPI"

    print(f"📊 Release type: {release_type}")
    print(f"📦 PyPI status: {pypi_action}")

    # Check if tag already exists
    tag_name = f"v{clean_version}"
    if check_existing_tag(tag_name):
        print(f"❌ Tag {tag_name} already exists!")
        print("   Use a different version or delete the existing tag:")
        print(f"   git tag -d {tag_name}")
        print(f"   git push origin :refs/tags/{tag_name}")
        return False

    # Check git status
    if not check_git_status():
        print("❌ Please resolve git status issues first")
        return False

    # Handle version consistency
    if not dry_run:
        if not update_version_if_needed(clean_version, update_version):
            return False

        # Commit version update if changes were made
        exit_code, stdout, _ = run_command("git status --porcelain")
        if exit_code == 0 and stdout.strip():
            run_command("git add pyproject.toml")
            base_version = get_base_version(clean_version)
            exit_code, _, stderr = run_command(f'git commit -m "Update version to {base_version} for quick release {clean_version}"')
            if exit_code == 0:
                print("✅ Committed version update")
            else:
                print(f"⚠️ Could not commit version update: {stderr}")

    if dry_run:
        print(f"🔍 DRY RUN: Would create tag {tag_name}")
        print(f"🔍 DRY RUN: Would push tag and trigger release workflow")
        return True

    # Create tag
    exit_code, _, stderr = run_command(f'git tag -a {tag_name} -m "Quick release {tag_name}"')
    if exit_code != 0:
        print(f"❌ Error creating tag: {stderr}")
        return False

    print(f"✅ Created tag {tag_name}")

    # Push any changes first
    exit_code, stdout, _ = run_command("git status --porcelain")
    if exit_code == 0 and not stdout.strip():
        # No uncommitted changes, safe to push
        pass
    else:
        # Push any committed changes
        exit_code, _, stderr = run_command("git push")
        if exit_code != 0:
            print(f"❌ Error pushing changes: {stderr}")
            return False
        print("✅ Pushed version update")

    # Push tag
    exit_code, _, stderr = run_command(f"git push origin {tag_name}")
    if exit_code != 0:
        print(f"❌ Error pushing tag: {stderr}")
        # Try to clean up the local tag
        run_command(f"git tag -d {tag_name}")
        return False

    print(f"✅ Pushed tag {tag_name}")
    print(f"🚀 Release workflow should now be running!")
    print(f"🔗 Check: https://github.com/rezwanahmedsami/catzilla/actions")

    return True



def main():
    parser = argparse.ArgumentParser(
        description="Catzilla Quick Release Manager",
        epilog="""
Examples:
  python scripts/release.py v1.2.3           # Quick stable release (publishes to PyPI)
  python scripts/release.py v1.2.3-hotfix    # Quick pre-release (GitHub only)
  python scripts/release.py v1.2.3 --dry-run # Preview changes

Usage Patterns:
  - For comprehensive releases: Use ./scripts/bump_version.sh
  - For quick releases/hotfixes: Use this script
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("version", help="Version to release (e.g., v1.2.3 or v1.2.3-alpha1)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without actually doing it")
    parser.add_argument("--update-version", action="store_true", help="Force update pyproject.toml version to match tag")

    args = parser.parse_args()

    print("⚡ Catzilla Quick Release Manager")
    print("=" * 40)
    print("💡 Use ./scripts/bump_version.sh for comprehensive releases with tests")
    print("💡 Use this script for quick releases when version is already prepared")
    print()

    # Validate environment
    env_issues = validate_environment()
    if env_issues:
        print("❌ Environment validation failed:")
        for issue in env_issues:
            print(f"  - {issue}")
        sys.exit(1)

    # Check for recent bump_version.sh usage
    check_for_recent_bump_version_usage()

    success = create_quick_release(args.version, args.dry_run, args.update_version)

    if success:
        print("\n🎉 Quick release process completed successfully!")
        if not args.dry_run:
            is_valid, clean_version, is_stable = validate_version(args.version)
            base_version = get_base_version(clean_version)
            if is_stable:
                print(f"📦 Once published, users can install with: pip install catzilla=={base_version}")
            else:
                print(f"📦 Pre-release created - users can install from GitHub releases")
                print(f"   📋 Project files use base version: {base_version}")
                print(f"   🏷️  Git tag uses full version: {clean_version}")
    else:
        print("\n❌ Quick release process failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
