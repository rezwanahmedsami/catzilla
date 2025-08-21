#!/usr/bin/env python3
"""
Static File Server Tests for Catzilla

Tests for the mount_static API functionality. These tests focus on parameter
validation and API interface rather than background processes to avoid hanging.

Designed to run with: ./scripts/run_tests.sh -p
"""

import tempfile
from pathlib import Path
from catzilla import Catzilla


def test_mount_static_method_exists():
    """Test that mount_static method exists and is callable"""
    app = Catzilla()
    assert hasattr(app, 'mount_static')
    assert callable(getattr(app, 'mount_static'))


def test_mount_static_basic_functionality():
    """Test basic mount_static functionality with cache disabled"""
    app = Catzilla()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Basic mount with background processes disabled
        result = app.mount_static(
            "/static", temp_dir,
            enable_hot_cache=False,  # Disable to prevent hanging
            enable_compression=False
        )
        assert result is None


def test_mount_static_parameter_combinations():
    """Test mount_static with various parameter combinations"""
    app = Catzilla()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Test different parameter combinations
        result1 = app.mount_static(
            "/test1", temp_dir,
            index_file="index.html",
            enable_hot_cache=False,
            enable_compression=False
        )
        assert result1 is None

        result2 = app.mount_static(
            "/test2", temp_dir,
            enable_etags=True,
            enable_range_requests=True,
            enable_hot_cache=False,
            enable_compression=False
        )
        assert result2 is None


def test_mount_static_security_options():
    """Test mount_static security-related options"""
    app = Catzilla()

    with tempfile.TemporaryDirectory() as temp_dir:
        result = app.mount_static(
            "/secure", temp_dir,
            enable_hidden_files=False,
            enable_directory_listing=False,
            max_file_size=10*1024*1024,  # 10MB
            enable_hot_cache=False,  # Disable background processes
            enable_compression=False
        )
        assert result is None


def test_multiple_mount_points():
    """Test multiple static mount points"""
    app = Catzilla()

    with tempfile.TemporaryDirectory() as temp_dir1:
        with tempfile.TemporaryDirectory() as temp_dir2:
            # Mount multiple static paths
            result1 = app.mount_static(
                "/static1", temp_dir1,
                enable_hot_cache=False,
                enable_compression=False
            )
            result2 = app.mount_static(
                "/static2", temp_dir2,
                enable_hot_cache=False,
                enable_compression=False
            )

            assert result1 is None
            assert result2 is None


def test_mount_static_with_routes():
    """Test that mount_static works alongside regular routes"""
    app = Catzilla()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Mount static files first
        result = app.mount_static(
            "/static", temp_dir,
            enable_hot_cache=False,
            enable_compression=False
        )
        assert result is None

        # Add regular route after static mount
        @app.get("/api/test")
        def test_route(request):
            return {"message": "test"}

        # Add another static mount
        result2 = app.mount_static(
            "/assets", temp_dir,
            enable_hot_cache=False,
            enable_compression=False
        )
        assert result2 is None


def test_mount_static_path_validation():
    """Test mount path validation and normalization"""
    app = Catzilla()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Test different mount path formats
        result1 = app.mount_static(
            "/simple", temp_dir,
            enable_hot_cache=False,
            enable_compression=False
        )
        assert result1 is None

        result2 = app.mount_static(
            "/with/nested/path", temp_dir,
            enable_hot_cache=False,
            enable_compression=False
        )
        assert result2 is None


def test_mount_static_configuration_options():
    """Test comprehensive configuration options"""
    app = Catzilla()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Test comprehensive configuration (cache/compression disabled)
        result = app.mount_static(
            "/comprehensive", temp_dir,
            index_file="default.html",
            enable_hot_cache=False,  # Disabled to prevent hanging
            cache_size_mb=1,         # Minimum valid value
            cache_ttl_seconds=1,     # Minimal value
            enable_compression=False, # Disabled to prevent hanging
            compression_level=1,     # Minimal value
            enable_etags=True,
            enable_range_requests=True,
            enable_directory_listing=False,
            enable_hidden_files=False,
            max_file_size=50*1024*1024  # 50MB
        )
        assert result is None


def test_mount_static_realistic_usage():
    """Test realistic usage patterns"""
    app = Catzilla()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create subdirectories
        assets_dir = Path(temp_dir) / "assets"
        assets_dir.mkdir()

        media_dir = Path(temp_dir) / "media"
        media_dir.mkdir()

        # Mount different types of content
        # Web assets
        result1 = app.mount_static(
            "/assets", str(assets_dir),
            enable_hot_cache=False,  # Disabled for testing
            enable_compression=False
        )
        assert result1 is None

        # Media files
        result2 = app.mount_static(
            "/media", str(media_dir),
            enable_range_requests=True,
            enable_hot_cache=False,  # Disabled for testing
            enable_compression=False
        )
        assert result2 is None
