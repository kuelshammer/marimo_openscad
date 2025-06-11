"""
Tests for cache behavior and SCAD code update functionality with WASM support

These tests address the critical issue identified by LLM analysis where
update_scad_code changes don't trigger visual updates due to caching problems.
Includes WASM renderer support and fallback testing.
"""

import pytest
import unittest.mock as mock
import tempfile
import hashlib
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import with better error handling for CI
try:
    from marimo_openscad.solid_bridge import SolidPythonBridge, SolidPythonError
    from marimo_openscad.interactive_viewer import InteractiveViewer
    from marimo_openscad.viewer import OpenSCADViewer
except ImportError:
    # CI-friendly fallbacks
    SolidPythonBridge = None
    SolidPythonError = Exception
    InteractiveViewer = None
    OpenSCADViewer = None


class MockSolidPythonModel:
    """Mock SolidPython2 model for testing"""
    
    def __init__(self, scad_code: str, params: dict = None):
        self.scad_code = scad_code
        self.params = params or {}
        
    def as_scad(self) -> str:
        return self.scad_code


@pytest.mark.skipif(SolidPythonBridge is None, reason="Bridge classes not available in CI")
class TestSolidPythonBridge:
    """Test the caching behavior of SolidPythonBridge"""
    
    def setup_method(self):
        """Setup test environment"""
        self.bridge = SolidPythonBridge()
        # Mock the renderer to avoid needing actual OpenSCAD
        self.bridge.renderer = mock.MagicMock()
        self.bridge.renderer.render_scad_to_stl.return_value = b"mock_stl_data"
    
    def test_cache_basic_functionality(self):
        """Test that caching works for identical models"""
        model = MockSolidPythonModel("cube([10,10,10]);")
        
        # First render
        stl1 = self.bridge.render_to_stl(model)
        # Second render (should use cache)
        stl2 = self.bridge.render_to_stl(model)
        
        assert stl1 == stl2
        # Should only call renderer once due to caching
        assert self.bridge.renderer.render_scad_to_stl.call_count == 1
    
    def test_cache_invalidation_different_scad_code(self):
        """Test that different SCAD code invalidates cache"""
        model1 = MockSolidPythonModel("cube([10,10,10]);")
        model2 = MockSolidPythonModel("sphere(r=5);")
        
        # Configure mock to return different data for different inputs
        def mock_render(scad_code):
            if "cube" in scad_code:
                return b"cube_stl_data"
            elif "sphere" in scad_code:
                return b"sphere_stl_data"
            return b"default_stl_data"
        
        self.bridge.renderer.render_scad_to_stl.side_effect = mock_render
        
        stl1 = self.bridge.render_to_stl(model1)
        stl2 = self.bridge.render_to_stl(model2)
        
        assert stl1 != stl2
        assert stl1 == b"cube_stl_data"
        assert stl2 == b"sphere_stl_data"
        # Should call renderer twice for different models
        assert self.bridge.renderer.render_scad_to_stl.call_count == 2
    
    def test_cache_invalidation_different_parameters(self):
        """Test that different parameters invalidate cache even with same SCAD code"""
        # Same SCAD code but different parameter objects
        model1 = MockSolidPythonModel("cube([10,10,10]);", {"size": 10})
        model2 = MockSolidPythonModel("cube([10,10,10]);", {"size": 20})
        
        # Configure mock to return different data
        call_count = [0]
        def mock_render(scad_code):
            call_count[0] += 1
            return f"stl_data_{call_count[0]}".encode()
        
        self.bridge.renderer.render_scad_to_stl.side_effect = mock_render
        
        stl1 = self.bridge.render_to_stl(model1)
        stl2 = self.bridge.render_to_stl(model2)
        
        # Different parameters should result in different STL data
        assert stl1 != stl2
        assert self.bridge.renderer.render_scad_to_stl.call_count == 2
    
    def test_cache_bypass_functionality(self):
        """Test that cache can be bypassed when needed"""
        model = MockSolidPythonModel("cube([10,10,10]);")
        
        # Configure mock to return different data each time
        call_count = [0]
        def mock_render(scad_code):
            call_count[0] += 1
            return f"stl_data_{call_count[0]}".encode()
        
        self.bridge.renderer.render_scad_to_stl.side_effect = mock_render
        
        # First render with cache
        stl1 = self.bridge.render_to_stl(model, use_cache=True)
        # Second render with cache (should reuse)
        stl2 = self.bridge.render_to_stl(model, use_cache=True)
        # Third render without cache (should re-render)
        stl3 = self.bridge.render_to_stl(model, use_cache=False)
        
        assert stl1 == stl2  # Cache hit
        assert stl1 != stl3  # Cache bypass
        assert self.bridge.renderer.render_scad_to_stl.call_count == 2
    
    def test_cache_clearing(self):
        """Test that cache can be cleared manually"""
        model = MockSolidPythonModel("cube([10,10,10]);")
        
        # First render
        self.bridge.render_to_stl(model)
        assert len(self.bridge.model_cache) == 1
        
        # Clear cache
        self.bridge.clear_cache()
        assert len(self.bridge.model_cache) == 0
        
        # Render again (should not use cache)
        self.bridge.render_to_stl(model)
        assert self.bridge.renderer.render_scad_to_stl.call_count == 2
    
    def test_cache_info(self):
        """Test cache information retrieval"""
        model1 = MockSolidPythonModel("cube([10,10,10]);")
        model2 = MockSolidPythonModel("sphere(r=5);")
        
        # Initial state
        info = self.bridge.get_cache_info()
        assert info['cache_size'] == 0
        
        # Add models to cache
        self.bridge.render_to_stl(model1)
        self.bridge.render_to_stl(model2)
        
        info = self.bridge.get_cache_info()
        assert info['cache_size'] == 2
        assert len(info['cache_keys']) == 2


@pytest.mark.skipif(InteractiveViewer is None, reason="Viewer classes not available in CI")
class TestUpdateScadCode:
    """Test the critical update_scad_code functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.viewer = InteractiveViewer()
        # Mock the bridge renderer
        self.viewer.bridge.renderer = mock.MagicMock()
        
        # Configure mock to return different STL data for different SCAD code
        def mock_render(scad_code):
            if "cube" in scad_code:
                return b"cube_stl_binary_data"
            elif "sphere" in scad_code:
                return b"sphere_stl_binary_data"
            elif "cylinder" in scad_code:
                return b"cylinder_stl_binary_data"
            return b"default_stl_binary_data"
        
        self.viewer.bridge.renderer.render_scad_to_stl.side_effect = mock_render
    
    def test_update_scad_code_changes_output(self):
        """Test that update_scad_code produces different output for different code"""
        # Update with cube code
        cube_scad = "cube([10, 10, 10]);"
        self.viewer.update_scad_code(cube_scad)
        cube_stl_data = self.viewer.stl_data
        
        # Update with sphere code
        sphere_scad = "sphere(r=6);"
        self.viewer.update_scad_code(sphere_scad)
        sphere_stl_data = self.viewer.stl_data
        
        # STL data should be different
        assert cube_stl_data != sphere_stl_data
        assert len(cube_stl_data) > 0
        assert len(sphere_stl_data) > 0
        
        # Should have called renderer twice
        assert self.viewer.bridge.renderer.render_scad_to_stl.call_count == 2
    
    def test_update_scad_code_bypasses_cache(self):
        """Test that update_scad_code always bypasses cache"""
        # Same SCAD code, but should render twice
        scad_code = "cube([10, 10, 10]);"
        
        self.viewer.update_scad_code(scad_code)
        first_call_count = self.viewer.bridge.renderer.render_scad_to_stl.call_count
        
        self.viewer.update_scad_code(scad_code)
        second_call_count = self.viewer.bridge.renderer.render_scad_to_stl.call_count
        
        # Should have called renderer both times (no caching)
        assert second_call_count == first_call_count + 1
    
    def test_force_update_model(self):
        """Test that force_update_model bypasses cache"""
        model = MockSolidPythonModel("cube([10,10,10]);")
        
        # Normal update (uses cache)
        self.viewer.update_model(model)
        first_call_count = self.viewer.bridge.renderer.render_scad_to_stl.call_count
        
        # Force update (bypasses cache)
        self.viewer.force_update_model(model)
        second_call_count = self.viewer.bridge.renderer.render_scad_to_stl.call_count
        
        # Should have called renderer again
        assert second_call_count > first_call_count
    
    def test_clear_model_cache(self):
        """Test that clear_model_cache works correctly"""
        model = MockSolidPythonModel("cube([10,10,10]);")
        
        # Add to cache
        self.viewer.update_model(model)
        cache_size_before = len(self.viewer.bridge.model_cache)
        
        # Clear cache
        self.viewer.clear_model_cache()
        cache_size_after = len(self.viewer.bridge.model_cache)
        
        assert cache_size_before > 0
        assert cache_size_after == 0


@pytest.mark.skipif(OpenSCADViewer is None, reason="Viewer classes not available in CI")
class TestOpenSCADViewer:
    """Test the OpenSCADViewer class cache behavior"""
    
    def setup_method(self):
        """Setup test environment"""
        self.viewer = OpenSCADViewer()
        
        # Replace the _render_stl method with a simple mock
        def mock_render_stl(scad_code, force_render=False):
            if "cube" in scad_code.lower():
                return b"cube_stl_binary_data"
            elif "sphere" in scad_code.lower():
                return b"sphere_stl_binary_data"
            elif "cylinder" in scad_code.lower():
                return b"cylinder_stl_binary_data"
            return b"default_stl_binary_data"
        
        self.viewer._render_stl = mock_render_stl
    
    def test_update_scad_code_produces_different_output(self):
        """Test that update_scad_code produces different outputs for different SCAD code"""
        # Test cube
        cube_scad = "cube([10, 10, 10]);"
        self.viewer.update_scad_code(cube_scad)
        cube_output = self.viewer.stl_data
        
        # Test sphere  
        sphere_scad = "sphere(r=6);"
        self.viewer.update_scad_code(sphere_scad)
        sphere_output = self.viewer.stl_data
        
        # Outputs should be different
        assert cube_output != sphere_output, f"Cube output: {cube_output}, Sphere output: {sphere_output}"
        assert len(cube_output) > 0, "Cube output should not be empty"
        assert len(sphere_output) > 0, "Sphere output should not be empty"


# Pytest fixtures and configuration
@pytest.fixture
def mock_openscad_environment():
    """Fixture to mock OpenSCAD environment for testing"""
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        yield mock_run


# Integration test
def test_end_to_end_scad_update_behavior():
    """Integration test for the complete SCAD update workflow"""
    viewer = InteractiveViewer()
    
    # Mock the renderer to return predictable data
    def mock_render(scad_code):
        return f"STL_DATA_FOR_{hash(scad_code)}".encode()
    
    viewer.bridge.renderer.render_scad_to_stl = mock_render
    
    # Test sequence of updates
    codes = [
        "cube([10, 10, 10]);",
        "sphere(r=5);", 
        "cylinder(r=3, h=8);",
        "cube([10, 10, 10]);"  # Same as first, but should still update
    ]
    
    outputs = []
    for code in codes:
        viewer.update_scad_code(code)
        outputs.append(viewer.stl_data)
    
    # Each output should be non-empty
    for i, output in enumerate(outputs):
        assert len(output) > 0, f"Output {i} should be non-empty: {codes[i]}"
    
    # Different SCAD codes should produce different outputs
    # Note: Repeated cube might produce same result, which is actually correct behavior
    unique_codes = list(set(codes))
    if len(unique_codes) > 1:
        # Get outputs for different unique codes
        code_to_output = {}
        for i, code in enumerate(codes):
            if code not in code_to_output:
                code_to_output[code] = outputs[i]
        
        # Different codes should produce different outputs
        unique_outputs = list(code_to_output.values())
        assert len(set(unique_outputs)) == len(unique_outputs), \
            f"Different SCAD codes should produce different outputs. Codes: {list(code_to_output.keys())}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])