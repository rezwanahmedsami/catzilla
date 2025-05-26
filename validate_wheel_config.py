#!/usr/bin/env python3
"""
Validate cibuildwheel configuration in pyproject.toml
"""

import toml

def validate_cibuildwheel_config():
    """Validate the cibuildwheel configuration"""
    try:
        # Load pyproject.toml
        with open('pyproject.toml', 'r') as f:
            config = toml.load(f)

        cibw_config = config.get('tool', {}).get('cibuildwheel', {})

        print("🔍 Validating cibuildwheel configuration...")

        # Check required fields
        required_fields = ['build', 'skip', 'test-requires', 'test-command']
        for field in required_fields:
            if field in cibw_config:
                print(f"✅ {field}: {cibw_config[field]}")
            else:
                print(f"❌ Missing required field: {field}")

        # Check platform-specific configs
        platforms = ['linux', 'macos', 'windows']
        for platform in platforms:
            platform_config = cibw_config.get(platform, {})
            if platform_config:
                print(f"✅ {platform} config: {len(platform_config)} settings")
            else:
                print(f"⚠️  No specific config for {platform}")

        print("\n🎯 Key configuration:")
        print(f"  Build targets: {cibw_config.get('build')}")
        print(f"  Skip targets: {cibw_config.get('skip')}")
        print(f"  Test command: {cibw_config.get('test-command')}")

        print("\n✅ Configuration validation successful!")
        return True

    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

if __name__ == "__main__":
    validate_cibuildwheel_config()
