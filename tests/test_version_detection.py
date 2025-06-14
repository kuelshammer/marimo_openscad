"""
Tests for OpenSCAD Version Detection System

Tests the version detection, parsing, and management capabilities
across different OpenSCAD installations and WASM modules.
"""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import json

from src.marimo_openscad.version_manager import (
    VersionInfo,
    OpenSCADVersionType,
    OpenSCADInstallation,
    LocalOpenSCADDetector,
    WASMVersionDetector,
    OpenSCADVersionManager,
    detect_openscad_version,
    is_openscad_available,
    get_openscad_capabilities
)


class TestVersionInfo:
    """Test VersionInfo data structure."""
    
    def test_version_info_creation(self):
        """Test creating VersionInfo instances."""
        # Basic version
        v1 = VersionInfo(2023, 6, 0)
        assert v1.major == 2023
        assert v1.minor == 6
        assert v1.patch == 0
        assert v1.build is None
        
        # Version with build
        v2 = VersionInfo(2023, 6, 23, "a1b2c3d")
        assert v2.build == "a1b2c3d"
        
    def test_version_info_string_representation(self):
        """Test string representation of versions."""
        v1 = VersionInfo(2021, 1, 0)
        assert str(v1) == "2021.01.00"
        
        v2 = VersionInfo(2023, 6, 23, "git-abc123")
        assert str(v2) == "2023.06.23.git-abc123"
        
    def test_version_info_comparison(self):
        """Test version comparison operations."""
        v1 = VersionInfo(2021, 1, 0)
        v2 = VersionInfo(2022, 3, 0)
        v3 = VersionInfo(2023, 6, 0)
        v4 = VersionInfo(2021, 1, 0)  # Same as v1
        
        # Equality
        assert v1 == v4
        assert v1 != v2
        
        # Ordering
        assert v1 < v2 < v3
        assert v3 > v2 > v1
        
        # Build info doesn't affect core comparison
        v5 = VersionInfo(2021, 1, 0, "build123")
        assert v1 == v5


class TestLocalOpenSCADDetector:
    """Test local OpenSCAD detection."""
    
    def setup_method(self):
        """Setup test environment."""
        self.detector = LocalOpenSCADDetector()
        
    def test_parse_version_standard_release(self):
        """Test parsing standard release version strings."""
        version_strings = [
            "OpenSCAD version 2021.01",
            "OpenSCAD version 2022.03",
            "OpenSCAD version 2023.06"
        ]
        
        expected_versions = [
            VersionInfo(2021, 1, 0),
            VersionInfo(2022, 3, 0),
            VersionInfo(2023, 6, 0)
        ]
        
        for version_string, expected in zip(version_strings, expected_versions):
            result = self.detector.parse_version_info(version_string)
            assert result == expected
            
    def test_parse_version_development_build(self):
        """Test parsing development build version strings."""
        version_string = "OpenSCAD version 2023.06.23 (git a1b2c3d)"
        expected = VersionInfo(2023, 6, 23, "a1b2c3d")
        
        result = self.detector.parse_version_info(version_string)
        assert result == expected
        
    def test_parse_version_alternative_format(self):
        """Test parsing alternative version formats."""
        version_string = "OpenSCAD 2021.01.03"
        expected = VersionInfo(2021, 1, 3)
        
        result = self.detector.parse_version_info(version_string)
        assert result == expected
        
    def test_parse_version_invalid_string(self):
        """Test handling invalid version strings."""
        invalid_strings = [
            "Some other program version 1.0",
            "OpenSCAD",
            "version 2021.01",
            "invalid format"
        ]
        
        for invalid_string in invalid_strings:
            result = self.detector.parse_version_info(invalid_string)
            assert result is None
            
    @patch('shutil.which')
    def test_find_openscad_in_path(self, mock_which):
        """Test finding OpenSCAD in system PATH."""
        mock_which.return_value = "/usr/bin/openscad"
        
        result = self.detector.find_openscad_executable()
        assert result == Path("/usr/bin/openscad")
        
        # Verify it tried the right executables
        mock_which.assert_called()
        
    @patch('shutil.which')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    @patch.object(LocalOpenSCADDetector, '_is_executable')
    def test_find_openscad_in_search_paths(self, mock_is_executable, mock_is_file, mock_exists, mock_which):
        """Test finding OpenSCAD in platform-specific paths."""
        # Not in PATH
        mock_which.return_value = None
        
        # Mock file system
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_is_executable.return_value = True
        
        result = self.detector.find_openscad_executable()
        
        # Should find something in search paths
        assert result is not None
        assert isinstance(result, Path)
        
    @patch('subprocess.run')
    def test_is_executable_valid(self, mock_run):
        """Test validating executable with --version check."""
        # Mock successful version check
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "OpenSCAD version 2023.06"
        mock_run.return_value = mock_result
        
        path = Path("/usr/bin/openscad")
        result = self.detector._is_executable(path)
        
        assert result is True
        mock_run.assert_called_once_with(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
    @patch('subprocess.run')
    def test_is_executable_invalid(self, mock_run):
        """Test handling invalid executable."""
        # Mock failed version check
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "command not found"
        mock_run.return_value = mock_result
        
        path = Path("/usr/bin/not-openscad")
        result = self.detector._is_executable(path)
        
        assert result is False
        
    @patch('subprocess.run')
    def test_get_version_string_success(self, mock_run):
        """Test getting version string from executable."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "OpenSCAD version 2023.06\n"
        mock_run.return_value = mock_result
        
        path = Path("/usr/bin/openscad")
        result = self.detector.get_version_string(path)
        
        assert result == "OpenSCAD version 2023.06"
        
    @patch('subprocess.run')
    def test_get_version_string_failure(self, mock_run):
        """Test handling version string retrieval failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: command failed"
        mock_run.return_value = mock_result
        
        path = Path("/usr/bin/openscad")
        result = self.detector.get_version_string(path)
        
        assert result is None


class TestWASMVersionDetector:
    """Test WASM version detection."""
    
    def setup_method(self):
        """Setup test environment."""
        # Use a mock package root
        self.package_root = Path("/mock/package")
        self.detector = WASMVersionDetector(self.package_root)
        
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_find_bundled_wasm_files(self, mock_glob, mock_exists):
        """Test finding bundled WASM files."""
        # Mock file system structure
        mock_exists.return_value = True
        
        wasm_files = [
            Path("/mock/package/wasm/openscad.wasm"),
            Path("/mock/package/wasm/openscad.fonts.wasm")
        ]
        mock_glob.return_value = wasm_files
        
        result = self.detector.find_bundled_wasm_files()
        
        # Should find files from both potential WASM directories
        assert len(result) >= 2  # May find duplicates if both dirs exist
        assert all(isinstance(f, Path) for f in result)
        # Check that our expected files are in the results
        assert any(str(f).endswith("openscad.wasm") for f in result)
        assert any(str(f).endswith("openscad.fonts.wasm") for f in result)
        
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_read_version_from_json_manifest(self, mock_read_text, mock_exists):
        """Test reading version from JSON manifest."""
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps({
            "openscad_version": "2023.06",
            "build_date": "2023-06-15"
        })
        
        version_file = Path("/mock/package/wasm/manifest.json")
        result = self.detector._read_version_from_file(version_file)
        
        assert result == "2023.06"
        
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_read_version_from_text_file(self, mock_read_text, mock_exists):
        """Test reading version from plain text file."""
        mock_exists.return_value = True
        mock_read_text.return_value = "2023.06.23\n"
        
        version_file = Path("/mock/package/wasm/version.txt")
        result = self.detector._read_version_from_file(version_file)
        
        assert result == "2023.06.23"
        
    def test_validate_wasm_integrity_valid(self):
        """Test WASM integrity validation with valid file."""
        # Create temporary WASM file with correct header
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as tmp:
            # Write WASM magic number and version
            tmp.write(b'\x00asm\x01\x00\x00\x00')
            tmp.write(b'\x00' * 100)  # Some dummy content
            tmp_path = Path(tmp.name)
        
        try:
            result = self.detector.validate_wasm_integrity(tmp_path)
            assert result is True
        finally:
            tmp_path.unlink()
            
    def test_validate_wasm_integrity_invalid(self):
        """Test WASM integrity validation with invalid file."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as tmp:
            # Write invalid header
            tmp.write(b'invalid\x00\x00')
            tmp_path = Path(tmp.name)
        
        try:
            result = self.detector.validate_wasm_integrity(tmp_path)
            assert result is False
        finally:
            tmp_path.unlink()
            
    def test_validate_wasm_integrity_nonexistent(self):
        """Test WASM integrity validation with nonexistent file."""
        nonexistent_path = Path("/nonexistent/file.wasm")
        result = self.detector.validate_wasm_integrity(nonexistent_path)
        assert result is False
        
    @patch.object(WASMVersionDetector, 'find_bundled_wasm_files')
    def test_infer_version_from_metadata(self, mock_find_files):
        """Test version inference from file metadata."""
        # Mock WASM file with known size
        mock_file = Mock(spec=Path)
        mock_file.stat.return_value.st_size = 7_700_000  # ~7.7MB
        mock_find_files.return_value = [mock_file]
        
        result = self.detector._infer_version_from_metadata()
        
        # Should infer version based on file size
        assert result in ["2021.01", "2022.03", "2023.06", "unknown"]


class TestOpenSCADVersionManager:
    """Test comprehensive version management."""
    
    def setup_method(self):
        """Setup test environment."""
        self.manager = OpenSCADVersionManager()
        
    @patch.object(OpenSCADVersionManager, '_detect_local_installation')
    @patch.object(OpenSCADVersionManager, '_detect_bundled_wasm')
    def test_detect_all_installations(self, mock_wasm, mock_local):
        """Test detecting all installations."""
        # Mock installations
        local_install = OpenSCADInstallation(
            version_info=VersionInfo(2023, 6, 0),
            installation_type=OpenSCADVersionType.LOCAL,
            executable_path=Path("/usr/bin/openscad")
        )
        
        wasm_install = OpenSCADInstallation(
            version_info=VersionInfo(2023, 6, 0, "bundled"),
            installation_type=OpenSCADVersionType.WASM_BUNDLED,
            wasm_path=Path("/package/wasm/openscad.wasm")
        )
        
        mock_local.return_value = local_install
        mock_wasm.return_value = wasm_install
        
        result = self.manager.detect_all_installations()
        
        assert len(result) == 2
        assert local_install in result
        assert wasm_install in result
        
    @patch.object(OpenSCADVersionManager, 'detect_all_installations')
    def test_get_preferred_installation_local_preferred(self, mock_detect):
        """Test preferred installation selection - local preferred."""
        installations = [
            OpenSCADInstallation(
                version_info=VersionInfo(2023, 6, 0),
                installation_type=OpenSCADVersionType.LOCAL
            ),
            OpenSCADInstallation(
                version_info=VersionInfo(2022, 3, 0, "bundled"),
                installation_type=OpenSCADVersionType.WASM_BUNDLED
            )
        ]
        mock_detect.return_value = installations
        
        result = self.manager.get_preferred_installation()
        
        # Should prefer newer local installation
        assert result.installation_type == OpenSCADVersionType.LOCAL
        assert result.version_info.major == 2023
        
    @patch.object(OpenSCADVersionManager, 'detect_all_installations')
    def test_get_preferred_installation_wasm_fallback(self, mock_detect):
        """Test preferred installation selection - WASM fallback."""
        installations = [
            OpenSCADInstallation(
                version_info=VersionInfo(2023, 6, 0, "bundled"),
                installation_type=OpenSCADVersionType.WASM_BUNDLED
            )
        ]
        mock_detect.return_value = installations
        
        result = self.manager.get_preferred_installation()
        
        # Should fall back to WASM
        assert result.installation_type == OpenSCADVersionType.WASM_BUNDLED
        
    @patch.object(OpenSCADVersionManager, 'detect_all_installations')
    def test_get_installation_by_version_exact_match(self, mock_detect):
        """Test finding installation by exact version match."""
        installations = [
            OpenSCADInstallation(
                version_info=VersionInfo(2021, 1, 0),
                installation_type=OpenSCADVersionType.LOCAL
            ),
            OpenSCADInstallation(
                version_info=VersionInfo(2023, 6, 0),
                installation_type=OpenSCADVersionType.WASM_BUNDLED
            )
        ]
        mock_detect.return_value = installations
        
        # Test string version
        result = self.manager.get_installation_by_version("2023.06")
        assert result.version_info == VersionInfo(2023, 6, 0)
        
        # Test VersionInfo
        target = VersionInfo(2021, 1, 0)
        result = self.manager.get_installation_by_version(target)
        assert result.version_info == target
        
    @patch.object(OpenSCADVersionManager, 'detect_all_installations')
    def test_get_version_summary(self, mock_detect):
        """Test version summary generation."""
        installations = [
            OpenSCADInstallation(
                version_info=VersionInfo(2023, 6, 0),
                installation_type=OpenSCADVersionType.LOCAL,
                executable_path=Path("/usr/bin/openscad"),
                capabilities=["full_openscad"]
            ),
            OpenSCADInstallation(
                version_info=VersionInfo(2023, 6, 0, "bundled"),
                installation_type=OpenSCADVersionType.WASM_BUNDLED,
                wasm_path=Path("/package/wasm/openscad.wasm"),
                capabilities=["browser_rendering"]
            )
        ]
        mock_detect.return_value = installations
        
        summary = self.manager.get_version_summary()
        
        assert summary["total_installations"] == 2
        assert len(summary["local_installations"]) == 1
        assert len(summary["wasm_installations"]) == 1
        assert summary["preferred_version"] == "2023.06.00"


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @patch('src.marimo_openscad.version_manager.OpenSCADVersionManager')
    def test_detect_openscad_version(self, mock_manager_class):
        """Test quick version detection function."""
        mock_manager = Mock()
        mock_installation = Mock()
        mock_installation.version_info = VersionInfo(2023, 6, 0)
        mock_manager.get_preferred_installation.return_value = mock_installation
        mock_manager_class.return_value = mock_manager
        
        result = detect_openscad_version()
        assert result == "2023.06.00"
        
    @patch('src.marimo_openscad.version_manager.OpenSCADVersionManager')
    def test_is_openscad_available(self, mock_manager_class):
        """Test availability check function."""
        mock_manager = Mock()
        mock_manager.detect_all_installations.return_value = [Mock()]
        mock_manager_class.return_value = mock_manager
        
        result = is_openscad_available()
        assert result is True
        
        # Test no installations
        mock_manager.detect_all_installations.return_value = []
        result = is_openscad_available()
        assert result is False
        
    @patch('src.marimo_openscad.version_manager.OpenSCADVersionManager')
    def test_get_openscad_capabilities(self, mock_manager_class):
        """Test capabilities retrieval function."""
        mock_manager = Mock()
        mock_installation = Mock()
        mock_installation.capabilities = ["full_openscad", "file_operations"]
        mock_manager.get_preferred_installation.return_value = mock_installation
        mock_manager_class.return_value = mock_manager
        
        result = get_openscad_capabilities()
        assert result == ["full_openscad", "file_operations"]


if __name__ == "__main__":
    pytest.main([__file__])