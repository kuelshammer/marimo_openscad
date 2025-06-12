"""
CI-Optimized WASM Tests

Tests designed specifically for CI/CD environments with proper fallbacks
and environment detection.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def is_ci_environment():
    """Check if running in CI environment"""
    return (
        os.environ.get('CI') == 'true' or 
        os.environ.get('GITHUB_ACTIONS') == 'true' or
        os.environ.get('CONTINUOUS_INTEGRATION') == 'true'
    )


@pytest.mark.wasm
@pytest.mark.ci_compatibility
class TestWASMCIOptimized:
    """CI-optimized WASM tests with proper environment detection"""
    
    def test_wasm_bundling_ci_compatible(self):
        """Test WASM file bundling in CI environment"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        
        renderer = OpenSCADWASMRenderer()
        
        # Should work in CI environment
        assert renderer.wasm_path.exists(), f"WASM path not found: {renderer.wasm_path}"
        
        # Check bundled files
        wasm_files = renderer.get_wasm_files()
        assert len(wasm_files) >= 2, f"Expected at least 2 WASM files, got {len(wasm_files)}"
        
        # Core files should exist
        assert "openscad.wasm" in wasm_files, "openscad.wasm not found in bundle"
        assert "openscad.js" in wasm_files, "openscad.js not found in bundle"
        
        # Files should be accessible
        for filename, filepath in wasm_files.items():
            file_path = Path(filepath)
            assert file_path.exists(), f"Bundled file not accessible: {filepath}"
            assert file_path.stat().st_size > 0, f"Bundled file is empty: {filepath}"
    
    def test_wasm_renderer_stats_ci(self):
        """Test WASM renderer stats in CI environment"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        
        renderer = OpenSCADWASMRenderer()
        stats = renderer.get_stats()
        
        # CI-compatible assertions
        assert stats['renderer_type'] == 'wasm'
        assert isinstance(stats['is_available'], bool)
        assert 'wasm_path' in stats
        assert 'wasm_files' in stats
        
        # In CI, WASM should be available due to bundling
        if is_ci_environment():
            assert stats['is_available'] is True, "WASM should be available in CI with bundled files"
            assert len(stats['wasm_files']) >= 2, "Should find bundled WASM files in CI"
    
    def test_wasm_file_integrity_ci(self):
        """Test WASM file integrity in CI"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        
        renderer = OpenSCADWASMRenderer()
        wasm_files = renderer.get_wasm_files()
        
        if "openscad.wasm" in wasm_files:
            wasm_path = Path(wasm_files["openscad.wasm"])
            
            # Check WASM magic number
            with open(wasm_path, 'rb') as f:
                header = f.read(4)
                assert header == b'\x00asm', f"Invalid WASM magic number: {header.hex()}"
            
            # Check reasonable file size (should be several MB)
            size = wasm_path.stat().st_size
            assert size > 1_000_000, f"WASM file too small: {size} bytes"
            assert size < 50_000_000, f"WASM file too large: {size} bytes"
    
    def test_wasm_capabilities_ci_safe(self):
        """Test WASM capabilities without browser dependencies"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        
        capabilities = OpenSCADWASMRenderer.get_capabilities()
        
        # Should work in any environment
        assert capabilities['renderer_type'] == 'wasm'
        assert capabilities['requires_local_install'] is False
        assert capabilities['supports_browser'] is True
        
        # Check feature flags
        features = capabilities.get('supported_features', [])
        expected_features = ['manifold_engine', 'font_support', 'mcad_library']
        
        for feature in expected_features:
            assert feature in features, f"Missing expected feature: {feature}"


@pytest.mark.wasm
@pytest.mark.ci_compatibility  
class TestHybridRendererCI:
    """Test hybrid renderer in CI environment"""
    
    def test_hybrid_renderer_ci_initialization(self):
        """Test hybrid renderer initializes properly in CI"""
        from marimo_openscad.openscad_wasm_renderer import HybridOpenSCADRenderer
        
        # Should work even if local OpenSCAD is not available in CI
        renderer = HybridOpenSCADRenderer(prefer_wasm=True, fallback_to_local=False)
        
        # Should have WASM renderer available due to bundling
        assert hasattr(renderer, 'wasm_renderer')
        if renderer.wasm_renderer:
            assert renderer.wasm_renderer.is_available
    
    def test_hybrid_renderer_stats_ci(self):
        """Test hybrid renderer stats in CI"""
        from marimo_openscad.openscad_wasm_renderer import HybridOpenSCADRenderer
        
        renderer = HybridOpenSCADRenderer(prefer_wasm=True)
        stats = renderer.get_stats()
        
        # CI-safe assertions
        assert 'active_renderer' in stats
        assert 'available_renderers' in stats
        
        # In CI with bundled WASM, should prefer WASM
        if is_ci_environment():
            assert 'wasm' in stats['available_renderers'], "WASM should be available in CI"


@pytest.mark.wasm
@pytest.mark.performance
@pytest.mark.ci_compatibility
class TestWASMPerformanceCI:
    """Test WASM performance tracking in CI"""
    
    def test_render_count_tracking_ci(self):
        """Test render count tracking works in CI"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        
        renderer = OpenSCADWASMRenderer()
        
        initial_count = renderer.render_count
        assert initial_count == 0
        
        # Simulate renders (actual WASM execution happens in browser)
        test_codes = ["cube([1,1,1]);", "sphere(r=1);"]
        
        for scad_code in test_codes:
            result = renderer.render_scad_to_stl(scad_code)
            assert isinstance(result, bytes)
        
        # Should track all renders
        assert renderer.render_count == len(test_codes)
    
    def test_wasm_error_handling_ci(self):
        """Test WASM error handling in CI environment"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer, OpenSCADError
        
        renderer = OpenSCADWASMRenderer()
        
        # Test empty code handling
        with pytest.raises(Exception):
            renderer.render_scad_to_stl("")
        
        # Test invalid code handling (should not crash)
        try:
            result = renderer.render_scad_to_stl("invalid_syntax:::")
            assert isinstance(result, bytes)  # Should return something
        except Exception as e:
            # If it raises an exception, should be meaningful
            assert "scad" in str(e).lower() or "invalid" in str(e).lower()


@pytest.mark.wasm
@pytest.mark.ci_compatibility
class TestWASMPackageIntegration:
    """Test WASM package integration for CI/CD deployment"""
    
    def test_package_structure_ci(self):
        """Test package structure is correct for deployment"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        
        renderer = OpenSCADWASMRenderer()
        
        # Package structure should be consistent
        expected_path_parts = ['marimo_openscad', 'wasm']
        actual_path = str(renderer.wasm_path)
        
        for part in expected_path_parts:
            assert part in actual_path, f"Expected path part '{part}' not found in {actual_path}"
    
    def test_import_compatibility_ci(self):
        """Test import compatibility for CI environments"""
        # Test that all expected modules can be imported
        imports_to_test = [
            "from marimo_openscad import openscad_viewer",
            "from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer",
            "from marimo_openscad.openscad_wasm_renderer import HybridOpenSCADRenderer",
        ]
        
        for import_statement in imports_to_test:
            try:
                exec(import_statement)
            except ImportError as e:
                pytest.fail(f"Import failed in CI: {import_statement} - {e}")
    
    def test_viewer_integration_ci_safe(self):
        """Test viewer integration without browser dependencies"""
        with patch('marimo_openscad.viewer.anywidget.AnyWidget.__init__'):
            from marimo_openscad.viewer import OpenSCADViewer
            from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
            
            # Create minimal viewer for CI testing
            viewer = OpenSCADViewer.__new__(OpenSCADViewer)
            viewer.renderer_type = "wasm"
            viewer.wasm_base_url = ""
            viewer.wasm_enabled = False
            
            # Should be able to create WASM renderer
            renderer = OpenSCADWASMRenderer()
            viewer.renderer = renderer
            
            # Test WASM URL setup
            viewer._setup_wasm_urls()
            
            if renderer.is_available:
                assert viewer.wasm_enabled is True
                assert viewer.wasm_base_url != ""


# Conditional test execution based on environment
if is_ci_environment():
    # Add CI-specific markers
    pytestmark = [pytest.mark.ci_compatibility, pytest.mark.wasm]
    
    def test_ci_environment_detected():
        """Confirm CI environment is properly detected"""
        assert is_ci_environment(), "CI environment not detected correctly"
        
        # Log CI environment info
        ci_vars = ['CI', 'GITHUB_ACTIONS', 'CONTINUOUS_INTEGRATION']
        detected_vars = [var for var in ci_vars if os.environ.get(var)]
        assert len(detected_vars) > 0, f"No CI environment variables detected: {ci_vars}"