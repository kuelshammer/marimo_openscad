"""
Real WASM Integration Tests - Testing with actual WASM files

These tests use the bundled WASM modules to test actual functionality
without excessive mocking where possible.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer, HybridOpenSCADRenderer


@pytest.mark.wasm
class TestRealWASMIntegration:
    """Test real WASM integration with bundled files"""
    
    def test_wasm_files_bundled(self):
        """Test that WASM files are properly bundled in package"""
        renderer = OpenSCADWASMRenderer()
        
        # Should find bundled WASM files
        assert renderer.is_available is True
        assert renderer.wasm_path.exists()
        
        # Check specific files exist
        wasm_files = renderer.get_wasm_files()
        assert "openscad.wasm" in wasm_files
        assert "openscad.js" in wasm_files
        
        # Verify files actually exist
        wasm_file = Path(wasm_files["openscad.wasm"])
        js_file = Path(wasm_files["openscad.js"])
        assert wasm_file.exists()
        assert js_file.exists()
        
        # Check file sizes (WASM should be substantial)
        assert wasm_file.stat().st_size > 1_000_000  # >1MB
        assert js_file.stat().st_size > 100  # Some JS content
    
    def test_wasm_url_generation(self):
        """Test WASM URL generation for JavaScript"""
        renderer = OpenSCADWASMRenderer()
        
        base_url = renderer.get_wasm_url_base()
        assert base_url
        assert "marimo_openscad/wasm" in base_url
        
        # Should be accessible path (convert URL to path if needed)
        if base_url.startswith('file://'):
            wasm_path = Path(base_url[7:])  # Remove 'file://' prefix
        else:
            wasm_path = Path(base_url)
        assert wasm_path.exists()
    
    def test_wasm_stats_real_data(self):
        """Test WASM stats with real bundled data"""
        renderer = OpenSCADWASMRenderer()
        stats = renderer.get_stats()
        
        assert stats['renderer_type'] == 'wasm'
        assert stats['is_available'] is True
        assert 'wasm_path' in stats
        assert 'wasm_files' in stats
        
        # Should have real file paths
        wasm_files = stats['wasm_files']
        assert len(wasm_files) >= 2  # At least .wasm and .js
        
        for filename, filepath in wasm_files.items():
            assert Path(filepath).exists()
    
    def test_wasm_capabilities_real(self):
        """Test WASM capabilities without mocking"""
        capabilities = OpenSCADWASMRenderer.get_capabilities()
        
        # Should be real capabilities, not mocked
        assert capabilities['renderer_type'] == 'wasm'
        assert capabilities['requires_local_install'] is False
        assert capabilities['supports_browser'] is True
        assert capabilities['supports_offline'] is True
        
        # Should support advanced features
        features = capabilities['supported_features']
        assert 'manifold_engine' in features
        assert 'font_support' in features
        assert 'mcad_library' in features


@pytest.mark.wasm  
class TestHybridRendererReal:
    """Test hybrid renderer with real WASM availability"""
    
    def test_hybrid_detects_real_wasm(self):
        """Test hybrid renderer detects real WASM availability"""
        # Test with real WASM detection (not mocked)
        renderer = HybridOpenSCADRenderer(prefer_wasm=True)
        
        # Should detect real WASM availability
        assert hasattr(renderer, 'wasm_renderer')
        if renderer.wasm_renderer:
            assert renderer.wasm_renderer.is_available
    
    def test_hybrid_wasm_initialization_real(self):
        """Test hybrid renderer initializes WASM with real files"""
        renderer = HybridOpenSCADRenderer(prefer_wasm=True)
        
        stats = renderer.get_stats()
        assert 'available_renderers' in stats
        
        # If WASM is available, should have WASM stats
        if 'wasm' in stats['available_renderers']:
            assert 'wasm_stats' in stats
            wasm_stats = stats['wasm_stats']
            assert wasm_stats['is_available'] is True
            assert 'wasm_files' in wasm_stats


@pytest.mark.wasm
@pytest.mark.integration
class TestWASMErrorHandling:
    """Test WASM error handling without excessive mocking"""
    
    def test_wasm_empty_scad_code(self):
        """Test WASM renderer handles empty SCAD code properly"""
        renderer = OpenSCADWASMRenderer()
        
        # Should handle empty code gracefully
        with pytest.raises(Exception) as exc_info:
            renderer.render_scad_to_stl("")
        
        # Should be a meaningful error, not a mock response
        assert "empty" in str(exc_info.value).lower()
    
    def test_wasm_invalid_scad_code(self):
        """Test WASM renderer handles invalid SCAD code"""
        renderer = OpenSCADWASMRenderer()
        
        # Test with clearly invalid SCAD
        invalid_scad = "this_is_not_valid_scad_syntax:::"
        
        # Should handle invalid code (may not fail until JavaScript execution)
        # But should at least validate input and track the call
        try:
            result = renderer.render_scad_to_stl(invalid_scad)
            # If it returns something, should be bytes
            assert isinstance(result, bytes)
        except Exception as e:
            # If it fails, should be a meaningful error
            assert "scad" in str(e).lower() or "invalid" in str(e).lower()


@pytest.mark.performance
@pytest.mark.wasm
class TestWASMPerformanceMetrics:
    """Test WASM performance tracking (without browser execution)"""
    
    def test_render_count_tracking(self):
        """Test WASM renderer tracks render count correctly"""
        renderer = OpenSCADWASMRenderer()
        
        initial_count = renderer.render_count
        assert initial_count == 0
        
        # Render a few models (note: actual WASM execution would happen in browser)
        test_codes = [
            "cube([1,1,1]);",
            "sphere(r=1);", 
            "cylinder(r=1, h=2);"
        ]
        
        for scad_code in test_codes:
            renderer.render_scad_to_stl(scad_code)
        
        # Should track all renders
        assert renderer.render_count == len(test_codes)
        
        # Stats should reflect count
        stats = renderer.get_stats()
        assert stats['render_count'] == len(test_codes)
    
    def test_wasm_memory_pressure_simulation(self):
        """Test WASM renderer handles multiple rapid requests"""
        renderer = OpenSCADWASMRenderer()
        
        # Simulate rapid requests (memory pressure test)
        large_scad = "cube([100,100,100]);" * 10  # Larger code
        
        for i in range(5):
            result = renderer.render_scad_to_stl(large_scad)
            assert isinstance(result, bytes)
            assert len(result) > 0
        
        # Should handle multiple rapid requests
        assert renderer.render_count == 5


@pytest.mark.wasm
class TestWASMFileIntegrity:
    """Test integrity of bundled WASM files"""
    
    def test_wasm_file_headers(self):
        """Test WASM files have correct headers"""
        renderer = OpenSCADWASMRenderer()
        wasm_files = renderer.get_wasm_files()
        
        if "openscad.wasm" in wasm_files:
            wasm_path = Path(wasm_files["openscad.wasm"])
            
            # Read first few bytes to check WASM magic number
            with open(wasm_path, 'rb') as f:
                header = f.read(4)
                # WASM magic number: 0x00 0x61 0x73 0x6d  
                assert header == b'\x00asm', f"Invalid WASM header: {header.hex()}"
    
    def test_js_file_syntax(self):
        """Test JavaScript files have valid syntax (basic check)"""
        renderer = OpenSCADWASMRenderer()
        wasm_files = renderer.get_wasm_files()
        
        js_files = [f for f in wasm_files.keys() if f.endswith('.js')]
        
        for js_file in js_files:
            js_path = Path(wasm_files[js_file])
            content = js_path.read_text()
            
            # Basic syntax checks
            assert len(content) > 0
            assert "function" in content or "=>" in content  # Some function definition
            # Should not have obvious syntax errors
            assert not content.count('{') < content.count('}')  # Balanced braces basic check


# Integration with existing tests
@pytest.mark.wasm
class TestWASMViewerIntegration:
    """Test WASM integration with main viewer (minimal mocking)"""
    
    @patch('marimo_openscad.viewer.anywidget.AnyWidget.__init__')
    def test_viewer_wasm_url_setup(self, mock_widget_init):
        """Test viewer sets up WASM URLs correctly"""
        mock_widget_init.return_value = None
        
        from marimo_openscad.viewer import OpenSCADViewer
        
        # Create viewer with WASM renderer
        viewer = OpenSCADViewer.__new__(OpenSCADViewer)  # Skip __init__
        viewer.renderer_type = "wasm"
        viewer.renderer_status = "initializing"
        viewer.enable_real_time_wasm = True
        viewer.wasm_base_url = ""
        viewer.wasm_enabled = False
        
        # Mock only the minimum needed
        mock_renderer = OpenSCADWASMRenderer()
        viewer.renderer = mock_renderer
        
        # Test _setup_wasm_urls method
        viewer._setup_wasm_urls()
        
        # Should set WASM URLs based on real renderer
        if mock_renderer.is_available:
            assert viewer.wasm_enabled is True
            assert viewer.wasm_base_url != ""
            assert "marimo_openscad/wasm" in viewer.wasm_base_url
        else:
            assert viewer.wasm_enabled is False