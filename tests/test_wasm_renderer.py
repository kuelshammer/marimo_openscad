"""
Tests for OpenSCAD WASM Renderer

Tests the WebAssembly-based OpenSCAD renderer functionality.
"""

import pytest
from unittest.mock import Mock, patch
from marimo_openscad.openscad_wasm_renderer import (
    OpenSCADWASMRenderer, 
    HybridOpenSCADRenderer
)


@pytest.mark.wasm
class TestOpenSCADWASMRenderer:
    """Test WASM renderer functionality"""
    
    def test_wasm_renderer_initialization(self, mock_wasm_renderer):
        """Test WASM renderer can be initialized"""
        renderer = mock_wasm_renderer
        
        assert renderer.is_available is True
        assert renderer.render_count == 0
        assert renderer.get_version() == "OpenSCAD WASM 2022.03.20"
    
    def test_wasm_renderer_capabilities(self):
        """Test WASM renderer capabilities"""
        capabilities = OpenSCADWASMRenderer.get_capabilities()
        
        assert capabilities['renderer_type'] == 'wasm'
        assert capabilities['requires_local_install'] is False
        assert capabilities['supports_browser'] is True
        assert 'manifold_engine' in capabilities['supported_features']
    
    def test_wasm_supported_check(self):
        """Test WASM support detection"""
        assert OpenSCADWASMRenderer.is_wasm_supported() is True
    
    def test_wasm_render_different_shapes(self, mock_wasm_renderer, wasm_test_codes):
        """Test WASM renderer produces different outputs for different shapes"""
        renderer = mock_wasm_renderer
        
        # Render different shapes
        cube_result = renderer.render_scad_to_stl(wasm_test_codes['simple_cube'])
        sphere_result = renderer.render_scad_to_stl(wasm_test_codes['parametric_sphere'])
        
        # Should produce different outputs
        assert cube_result != sphere_result
        assert b"cube" in cube_result
        assert b"sphere" in sphere_result
        
        # Should track render count
        assert renderer.render_count == 2
    
    def test_wasm_renderer_stats(self, mock_wasm_renderer):
        """Test WASM renderer statistics"""
        renderer = mock_wasm_renderer
        
        # Initial stats
        stats = renderer.get_stats()
        assert stats['renderer_type'] == 'wasm'
        assert stats['render_count'] == 0
        
        # After rendering
        renderer.render_scad_to_stl('cube([1,1,1]);')
        stats = renderer.get_stats()
        assert stats['render_count'] == 1


@pytest.mark.wasm
class TestHybridRenderer:
    """Test hybrid renderer functionality"""
    
    def test_hybrid_renderer_wasm_preference(self, mock_hybrid_renderer):
        """Test hybrid renderer prefers WASM when available"""
        renderer = mock_hybrid_renderer
        
        assert renderer.get_active_renderer_type() == "wasm"
        assert renderer.prefer_wasm is True
    
    def test_hybrid_renderer_fallback(self, mock_hybrid_renderer):
        """Test hybrid renderer can fallback to local"""
        # Use the fixture and modify it for local preference
        renderer = mock_hybrid_renderer
        renderer.prefer_wasm = False
        renderer.active_renderer = "local"
        
        assert renderer.get_active_renderer_type() == "local"
        assert renderer.prefer_wasm is False
    
    def test_hybrid_renderer_switching(self, mock_hybrid_renderer):
        """Test hybrid renderer can switch between renderers"""
        renderer = mock_hybrid_renderer
        
        # Test WASM rendering
        wasm_result = renderer.render_scad_to_stl('cube([1,1,1]);')
        assert b"wasm" in wasm_result
        
        # Switch to local
        renderer.active_renderer = "local"
        local_result = renderer.render_scad_to_stl('cube([1,1,1]);')
        assert b"local" in local_result
        
        # Results should be different
        assert wasm_result != local_result


@pytest.mark.wasm
@pytest.mark.integration
class TestWASMIntegration:
    """Integration tests for WASM renderer"""
    
    def test_wasm_placeholder_generation(self):
        """Test WASM placeholder generation for API compatibility"""
        renderer = OpenSCADWASMRenderer()
        
        # Test placeholder generation
        scad_code = 'cube([10, 10, 10]);'
        placeholder = renderer._create_wasm_placeholder(scad_code)
        
        assert isinstance(placeholder, bytes)
        assert b"WASM_RENDER_REQUEST" in placeholder
        
        # Different code should produce different placeholders
        different_code = 'sphere(r=5);'
        different_placeholder = renderer._create_wasm_placeholder(different_code)
        assert placeholder != different_placeholder
    
    def test_wasm_renderer_error_handling(self):
        """Test WASM renderer error handling"""
        renderer = OpenSCADWASMRenderer()
        
        # Test empty code handling
        with pytest.raises(Exception) as exc_info:
            renderer.render_scad_to_stl("")
        assert "Empty SCAD code" in str(exc_info.value)
        
        # Test None code handling
        with pytest.raises(Exception):
            renderer.render_scad_to_stl(None)
    
    def test_wasm_renderer_stats_accumulation(self):
        """Test WASM renderer statistics accumulation"""
        renderer = OpenSCADWASMRenderer()
        
        initial_stats = renderer.get_stats()
        assert initial_stats['render_count'] == 0
        
        # Simulate multiple renders
        for i in range(3):
            renderer.render_scad_to_stl(f'cube([{i+1}, {i+1}, {i+1}]);')
        
        final_stats = renderer.get_stats()
        assert final_stats['render_count'] == 3


@pytest.mark.wasm
@pytest.mark.performance
class TestWASMPerformance:
    """Performance tests for WASM renderer"""
    
    def test_wasm_renderer_capability_limits(self):
        """Test WASM renderer capability limits"""
        capabilities = OpenSCADWASMRenderer.get_capabilities()
        
        # Check reasonable limits
        assert 'max_complexity' in capabilities
        assert 'output_formats' in capabilities
        assert 'binstl' in capabilities['output_formats']
    
    def test_wasm_complex_model_handling(self, mock_wasm_renderer, wasm_test_codes):
        """Test WASM renderer with complex models"""
        renderer = mock_wasm_renderer
        
        # Test complex model
        result = renderer.render_scad_to_stl(wasm_test_codes['complex_model'])
        assert len(result) > 0
        
        # Test stress test model
        stress_result = renderer.render_scad_to_stl(wasm_test_codes['wasm_stress_test'])
        assert len(stress_result) > 0
        
        # Should have different outputs
        assert result != stress_result


# Utility tests
@pytest.mark.wasm
class TestWASMUtilities:
    """Test WASM utility functions"""
    
    def test_wasm_renderer_initialization_options(self):
        """Test WASM renderer initialization with options"""
        options = {
            'enableManifold': True,
            'outputFormat': 'binstl',
            'timeout': 60000
        }
        
        renderer = OpenSCADWASMRenderer(options)
        assert renderer.wasm_options == options
    
    def test_hybrid_renderer_initialization_variants(self):
        """Test hybrid renderer with different initialization options"""
        
        # Test WASM-preferred hybrid
        hybrid_wasm = HybridOpenSCADRenderer(prefer_wasm=True, fallback_to_local=True)
        assert hybrid_wasm.prefer_wasm is True
        assert hybrid_wasm.fallback_to_local is True
        
        # Test local-preferred hybrid
        hybrid_local = HybridOpenSCADRenderer(prefer_wasm=False, fallback_to_local=False)
        assert hybrid_local.prefer_wasm is False
        assert hybrid_local.fallback_to_local is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])