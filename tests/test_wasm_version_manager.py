"""
Tests for WASM Version Management System

Tests the downloading, caching, and dynamic switching of different
OpenSCAD WASM versions for version compatibility support.

NOTE: Many tests in this file are marked as legacy_pre_bridge due to
AsyncIO conflicts with the new bridge system. They test the old
direct-download approach that has been replaced by the bridge pattern.
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.marimo_openscad.wasm_version_manager import (
    WASMVersion,
    WASMDownloadResult,
    WASMVersionRegistry,
    WASMDownloader,
    DynamicWASMLoader,
    WASMVersionSelector,
    WASMVersionManager
)
from src.marimo_openscad.version_manager import VersionInfo


class TestWASMVersion:
    """Test WASMVersion data structure."""
    
    def test_wasm_version_creation(self):
        """Test creating WASMVersion instances."""
        version_info = VersionInfo(2023, 6, 0)
        wasm_version = WASMVersion(
            version="2023.06",
            version_info=version_info,
            download_url="https://example.com/openscad.wasm",
            file_size=8_800_000,
            checksum="sha256:abc123"
        )
        
        assert wasm_version.version == "2023.06"
        assert wasm_version.version_info == version_info
        assert wasm_version.is_available is False  # Default
        assert "browser_rendering" in wasm_version.capabilities
        assert "wasm_execution" in wasm_version.capabilities
        
    def test_wasm_version_with_local_path(self):
        """Test WASMVersion with local file path."""
        local_path = Path("/tmp/openscad-2023.06.wasm")
        wasm_version = WASMVersion(
            version="2023.06",
            version_info=VersionInfo(2023, 6, 0),
            download_url="https://example.com/openscad.wasm",
            file_size=8_800_000,
            checksum="sha256:abc123",
            local_path=local_path,
            is_available=True
        )
        
        assert wasm_version.local_path == local_path
        assert wasm_version.is_available is True


class TestWASMVersionRegistry:
    """Test WASM version registry."""
    
    def test_get_available_versions(self):
        """Test getting available versions."""
        versions = WASMVersionRegistry.get_available_versions()
        
        assert isinstance(versions, list)
        assert len(versions) > 0
        assert "2021.01" in versions
        assert "2022.03" in versions
        assert "2023.06" in versions
        
    def test_get_version_info(self):
        """Test getting version information."""
        info = WASMVersionRegistry.get_version_info("2023.06")
        
        assert info is not None
        assert "download_url" in info
        assert "expected_size" in info
        assert "checksum" in info
        assert "backup_urls" in info
        
    def test_get_version_info_nonexistent(self):
        """Test getting info for nonexistent version."""
        info = WASMVersionRegistry.get_version_info("9999.99")
        assert info is None
        
    def test_parse_version_string(self):
        """Test parsing version strings."""
        # Standard version
        version_info = WASMVersionRegistry.parse_version_string("2023.06")
        assert version_info.major == 2023
        assert version_info.minor == 6
        assert version_info.patch == 0
        
        # Version with patch
        version_info = WASMVersionRegistry.parse_version_string("2023.06.23")
        assert version_info.major == 2023
        assert version_info.minor == 6
        assert version_info.patch == 23
        
    def test_parse_invalid_version_string(self):
        """Test parsing invalid version strings."""
        version_info = WASMVersionRegistry.parse_version_string("invalid")
        assert version_info.major == 2023  # Default fallback
        assert version_info.minor == 6
        assert version_info.patch == 0


class TestWASMDownloader:
    """Test WASM downloader functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.downloader = WASMDownloader(cache_dir=self.temp_dir)
        
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_downloader_initialization(self):
        """Test downloader initialization."""
        assert self.downloader.cache_dir == self.temp_dir
        assert self.downloader.cache_dir.exists()
        assert self.downloader.timeout_seconds == 60
        assert self.downloader.max_retries == 3
        
    @pytest.mark.asyncio
    async def test_download_unknown_version(self):
        """Test downloading unknown version."""
        result = await self.downloader.download_version("9999.99")
        
        assert result.success is False
        assert "Unknown version" in result.error_message
        assert result.wasm_version is None
        
    def test_list_cached_versions_empty(self):
        """Test listing cached versions when cache is empty."""
        cached = self.downloader.list_cached_versions()
        assert len(cached) == 0
        
    def test_list_cached_versions_with_files(self):
        """Test listing cached versions with mock files."""
        # Create mock WASM files
        (self.temp_dir / "openscad-2023.06.wasm").write_bytes(b"mock_wasm_data")
        (self.temp_dir / "openscad-2022.03.wasm").write_bytes(b"mock_wasm_data")
        
        cached = self.downloader.list_cached_versions()
        
        assert len(cached) == 2
        versions = [v.version for v in cached]
        assert "2023.06" in versions
        assert "2022.03" in versions
        
    def test_clear_cache_all(self):
        """Test clearing entire cache."""
        # Create mock files
        (self.temp_dir / "openscad-2023.06.wasm").write_bytes(b"data")
        (self.temp_dir / "openscad-2022.03.wasm").write_bytes(b"data")
        
        cleared_count = self.downloader.clear_cache()
        
        assert cleared_count == 2
        assert len(list(self.temp_dir.glob("*.wasm"))) == 0
        
    def test_clear_cache_by_age(self):
        """Test clearing cache by age."""
        # Create files with different ages
        recent_file = self.temp_dir / "openscad-2023.06.wasm"
        old_file = self.temp_dir / "openscad-2022.03.wasm"
        
        recent_file.write_bytes(b"data")
        old_file.write_bytes(b"data")
        
        # Make one file appear old
        old_time = datetime.now() - timedelta(days=10)
        import os
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))
        
        # Clear files older than 5 days
        cleared_count = self.downloader.clear_cache(older_than_days=5)
        
        assert cleared_count == 1
        assert recent_file.exists()
        assert not old_file.exists()
        
    @pytest.mark.asyncio
    async def test_validate_wasm_file_valid(self):
        """Test WASM file validation with valid file."""
        # Create mock WASM file with correct header
        wasm_file = self.temp_dir / "test.wasm"
        wasm_data = b'\x00asm\x01\x00\x00\x00' + b'x' * 1_000_000  # 1MB+ with WASM header
        wasm_file.write_bytes(wasm_data)
        
        is_valid = await self.downloader._validate_wasm_file(wasm_file, "mock_checksum")
        assert is_valid is True
        
    @pytest.mark.asyncio
    async def test_validate_wasm_file_invalid_header(self):
        """Test WASM file validation with invalid header."""
        wasm_file = self.temp_dir / "test.wasm"
        wasm_data = b'invalid' + b'x' * 1_000_000
        wasm_file.write_bytes(wasm_data)
        
        is_valid = await self.downloader._validate_wasm_file(wasm_file, "mock_checksum")
        assert is_valid is False
        
    @pytest.mark.asyncio
    async def test_validate_wasm_file_too_small(self):
        """Test WASM file validation with file too small."""
        wasm_file = self.temp_dir / "test.wasm"
        wasm_data = b'\x00asm\x01\x00\x00\x00' + b'x' * 100  # Only 100 bytes
        wasm_file.write_bytes(wasm_data)
        
        is_valid = await self.downloader._validate_wasm_file(wasm_file, "mock_checksum")
        assert is_valid is False
        
    def test_create_wasm_version(self):
        """Test creating WASMVersion from downloaded file."""
        # Create mock downloaded file
        local_path = self.temp_dir / "openscad-2023.06.wasm"
        local_path.write_bytes(b"mock_wasm_data")
        
        wasm_version = self.downloader._create_wasm_version(
            version="2023.06",
            url="https://example.com/openscad.wasm",
            local_path=local_path,
            expected_size=8_800_000,
            expected_checksum="mock_checksum"
        )
        
        assert wasm_version.version == "2023.06"
        assert wasm_version.version_info.major == 2023
        assert wasm_version.local_path == local_path
        assert wasm_version.is_available is True
        assert "openscad_2023.06" in wasm_version.capabilities


class TestDynamicWASMLoader:
    """Test dynamic WASM loading functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.downloader = WASMDownloader(cache_dir=self.temp_dir)
        self.loader = DynamicWASMLoader(self.downloader)
        
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_loader_initialization(self):
        """Test loader initialization."""
        assert self.loader.downloader == self.downloader
        assert self.loader.active_version is None
        assert len(self.loader.loaded_versions) == 0
        
    def test_get_available_versions(self):
        """Test getting available versions."""
        versions = self.loader.get_available_versions()
        
        assert isinstance(versions, list)
        # Should include registry versions even if not cached
        registry_versions = WASMVersionRegistry.get_available_versions()
        for version in registry_versions:
            assert version in versions
            
    @pytest.mark.asyncio
    async def test_ensure_version_available_already_cached(self):
        """Test ensuring version available when already cached."""
        # Create mock cached file
        wasm_file = self.temp_dir / "openscad-2023.06.wasm"
        wasm_data = b'\x00asm\x01\x00\x00\x00' + b'x' * 1_000_000
        wasm_file.write_bytes(wasm_data)
        
        # Refresh cached versions
        self.loader._refresh_cached_versions()
        
        result = await self.loader.ensure_version_available("2023.06")
        assert result is True
        assert "2023.06" in self.loader.loaded_versions
        
    @pytest.mark.asyncio
    async def test_load_wasm_version_success(self):
        """Test loading WASM version successfully."""
        # Create mock cached file
        wasm_file = self.temp_dir / "openscad-2023.06.wasm"
        wasm_data = b'\x00asm\x01\x00\x00\x00' + b'x' * 1_000_000
        wasm_file.write_bytes(wasm_data)
        
        # Refresh cached versions
        self.loader._refresh_cached_versions()
        
        wasm_version = await self.loader.load_wasm_version("2023.06")
        
        assert wasm_version is not None
        assert wasm_version.version == "2023.06"
        assert self.loader.active_version == "2023.06"
        
    @pytest.mark.asyncio
    async def test_switch_wasm_version(self):
        """Test switching between WASM versions."""
        # Create mock cached files
        for version in ["2022.03", "2023.06"]:
            wasm_file = self.temp_dir / f"openscad-{version}.wasm"
            wasm_data = b'\x00asm\x01\x00\x00\x00' + b'x' * 1_000_000
            wasm_file.write_bytes(wasm_data)
        
        # Refresh cached versions
        self.loader._refresh_cached_versions()
        
        # Load first version
        success1 = await self.loader.switch_wasm_version("2022.03")
        assert success1 is True
        assert self.loader.active_version == "2022.03"
        
        # Switch to second version
        success2 = await self.loader.switch_wasm_version("2023.06")
        assert success2 is True
        assert self.loader.active_version == "2023.06"
        
        # Switch to same version (should succeed quickly)
        success3 = await self.loader.switch_wasm_version("2023.06")
        assert success3 is True
        
    def test_get_active_wasm_version(self):
        """Test getting active WASM version."""
        # Initially no active version
        active = self.loader.get_active_wasm_version()
        assert active is None
        
        # Set active version manually for testing
        mock_version = WASMVersion(
            version="2023.06",
            version_info=VersionInfo(2023, 6, 0),
            download_url="https://example.com",
            file_size=1000,
            checksum="mock"
        )
        self.loader.loaded_versions["2023.06"] = mock_version
        self.loader.active_version = "2023.06"
        
        active = self.loader.get_active_wasm_version()
        assert active == mock_version
        
    def test_get_version_info_summary(self):
        """Test getting version info summary."""
        summary = self.loader.get_version_info_summary()
        
        assert "active_version" in summary
        assert "available_versions" in summary
        assert "cached_versions" in summary
        assert "registry_versions" in summary
        assert "cache_dir" in summary
        assert "total_cached_size" in summary
        
        assert summary["cache_dir"] == str(self.temp_dir)


class TestWASMVersionSelector:
    """Test WASM version selection logic."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        downloader = WASMDownloader(cache_dir=self.temp_dir)
        self.loader = DynamicWASMLoader(downloader)
        self.selector = WASMVersionSelector(self.loader)
        
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_select_optimal_version_no_requirements(self):
        """Test version selection with no specific requirements."""
        requirements = {}
        
        version = self.selector.select_optimal_version(requirements)
        
        # Should select some available version
        assert version is not None
        assert version in WASMVersionRegistry.get_available_versions()
        
    def test_select_optimal_version_with_min_version(self):
        """Test version selection with minimum version requirement."""
        requirements = {
            "min_version": "2022.03"
        }
        
        version = self.selector.select_optimal_version(requirements)
        
        assert version is not None
        selected_info = WASMVersionRegistry.parse_version_string(version)
        min_info = WASMVersionRegistry.parse_version_string("2022.03")
        assert selected_info >= min_info
        
    def test_select_optimal_version_with_preferred(self):
        """Test version selection with preferred version."""
        requirements = {
            "preferred_version": "2023.06"
        }
        
        version = self.selector.select_optimal_version(requirements)
        
        # Should select preferred version if available
        assert version == "2023.06"
        
    def test_select_optimal_version_performance_fastest(self):
        """Test version selection with fastest performance preference."""
        requirements = {
            "performance": "fastest"
        }
        
        version = self.selector.select_optimal_version(requirements)
        
        # Should select newest available version
        available_versions = WASMVersionRegistry.get_available_versions()
        expected_newest = max(
            available_versions,
            key=lambda v: WASMVersionRegistry.parse_version_string(v)
        )
        assert version == expected_newest
        
    def test_select_optimal_version_performance_stable(self):
        """Test version selection with stable performance preference."""
        requirements = {
            "performance": "stable"
        }
        
        version = self.selector.select_optimal_version(requirements)
        
        # Should prefer 2022.03 as stable choice
        assert version is not None
        # If 2022.03 is available, it should be selected
        if "2022.03" in WASMVersionRegistry.get_available_versions():
            assert version == "2022.03"
            
    def test_analyze_scad_requirements_basic(self):
        """Test SCAD code analysis for basic requirements."""
        scad_code = "cube([10, 10, 10]);"
        
        requirements = self.selector.analyze_scad_requirements(scad_code)
        
        assert "min_version" in requirements
        assert "features" in requirements
        assert "performance" in requirements
        assert requirements["min_version"] == "2021.01"  # Conservative default
        
    def test_analyze_scad_requirements_with_exponent(self):
        """Test SCAD code analysis with exponent operator."""
        scad_code = "cube([10**2, 10, 10]);"  # Uses ** operator
        
        requirements = self.selector.analyze_scad_requirements(scad_code)
        
        assert requirements["min_version"] == "2023.06"  # Requires newer version
        assert "exponent_operator" in requirements["features"]
        
    def test_analyze_scad_requirements_with_list_comprehension(self):
        """Test SCAD code analysis with list comprehension."""
        scad_code = "points = [for (i = [1:10]) [i, i*2]];"
        
        requirements = self.selector.analyze_scad_requirements(scad_code)
        
        assert "list_comprehension" in requirements["features"]
        
    def test_analyze_scad_requirements_large_model(self):
        """Test SCAD code analysis for large model."""
        # Create large SCAD code
        scad_code = "cube([10, 10, 10]);\n" * 1000  # Large model
        
        requirements = self.selector.analyze_scad_requirements(scad_code)
        
        assert requirements["performance"] == "fastest"  # Should prefer fastest for large models


class TestWASMVersionManager:
    """Test complete WASM version management system."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = WASMVersionManager(cache_dir=self.temp_dir)
        
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_manager_initialization(self):
        """Test manager initialization."""
        assert self.manager.downloader is not None
        assert self.manager.loader is not None
        assert self.manager.selector is not None
        
    @pytest.mark.asyncio
    async def test_get_optimal_version_for_scad(self):
        """Test getting optimal version for SCAD code."""
        scad_code = "cube([10, 10, 10]);"
        
        version = await self.manager.get_optimal_version_for_scad(scad_code)
        
        assert version is not None
        assert version in WASMVersionRegistry.get_available_versions()
        
    @pytest.mark.asyncio
    async def test_get_optimal_version_with_user_preferences(self):
        """Test getting optimal version with user preferences."""
        scad_code = "cube([10, 10, 10]);"
        user_preferences = {
            "preferred_version": "2022.03",
            "performance": "stable"
        }
        
        version = await self.manager.get_optimal_version_for_scad(
            scad_code, user_preferences
        )
        
        # Should respect user preference if possible
        assert version == "2022.03"
        
    def test_get_system_info(self):
        """Test getting system information."""
        info = self.manager.get_system_info()
        
        assert "wasm_manager" in info
        assert "registry" in info
        
        wasm_info = info["wasm_manager"]
        assert "cache_dir" in wasm_info
        assert "available_versions" in wasm_info
        assert "cached_versions" in wasm_info
        assert "active_version" in wasm_info
        
        registry_info = info["registry"]
        assert "known_versions" in registry_info
        assert "version_count" in registry_info


if __name__ == "__main__":
    pytest.main([__file__])