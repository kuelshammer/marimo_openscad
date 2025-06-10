"""
Tests for cache behavior and SCAD code update functionality

These tests address the critical issue identified by LLM analysis where
update_scad_code changes don't trigger visual updates due to caching problems.
"""

import pytest
import unittest.mock as mock
import tempfile
import hashlib
from pathlib import Path

from src.marimo_openscad.solid_bridge import SolidPythonBridge, SolidPythonError
from src.marimo_openscad.interactive_viewer import InteractiveViewer
from src.marimo_openscad.viewer import OpenSCADViewer


class MockSolidPythonModel:
    """Mock SolidPython2 model for testing"""
    
    def __init__(self, scad_code: str, params: dict = None):
        self.scad_code = scad_code
        self.params = params or {}
        
    def as_scad(self) -> str:
        return self.scad_code


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


class TestOpenSCADViewer:
    """Test the OpenSCADViewer class cache behavior"""
    
    def setup_method(self):
        """Setup test environment"""
        self.viewer = OpenSCADViewer()
        
        # Mock subprocess to avoid needing actual OpenSCAD
        self.subprocess_patcher = mock.patch('src.marimo_openscad.viewer.subprocess.run')
        self.mock_subprocess = self.subprocess_patcher.start()
        
        # Configure subprocess mock
        self.mock_subprocess.return_value.returncode = 0
        self.mock_subprocess.return_value.stderr = ""
        
        # Mock file operations
        self.temp_file_patcher = mock.patch('tempfile.TemporaryDirectory')
        self.mock_temp_dir = self.temp_file_patcher.start()
        
        # Create a mock temporary directory
        mock_dir = mock.MagicMock()
        mock_dir.__enter__.return_value = mock_dir
        mock_dir.__exit__.return_value = None
        self.mock_temp_dir.return_value = mock_dir
        
        # Mock Path operations
        self.path_patcher = mock.patch('src.marimo_openscad.viewer.Path')
        self.mock_path = self.path_patcher.start()
        
        def create_mock_file(path_str):
            mock_file = mock.MagicMock()
            mock_file.__truediv__ = lambda self, other: create_mock_file(f"{path_str}/{other}")
            mock_file.__str__ = lambda: path_str
            if path_str.endswith('.stl'):
                # Return different STL data based on SCAD content
                if hasattr(create_mock_file, '_scad_content'):
                    content = create_mock_file._scad_content
                    if "cube" in content:
                        mock_file.read_bytes.return_value = b"cube_stl_data"
                    elif "sphere" in content:
                        mock_file.read_bytes.return_value = b"sphere_stl_data"
                    else:
                        mock_file.read_bytes.return_value = b"default_stl_data"
                else:
                    mock_file.read_bytes.return_value = b"default_stl_data"
            else:
                # For SCAD files, capture the content
                def write_text(content):
                    create_mock_file._scad_content = content
                mock_file.write_text = write_text
            return mock_file
        
        self.mock_path.side_effect = create_mock_file
        mock_dir.__truediv__ = lambda self, other: create_mock_file(str(other))
    
    def teardown_method(self):
        """Clean up mocks"""
        self.subprocess_patcher.stop()
        self.temp_file_patcher.stop() 
        self.path_patcher.stop()
    
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
        assert cube_output != sphere_output
        assert len(cube_output) > 0
        assert len(sphere_output) > 0
        
        # Should have called subprocess twice
        assert self.mock_subprocess.call_count == 2


# Pytest fixtures and configuration
@pytest.fixture
def mock_openscad_environment():
    """Fixture to mock OpenSCAD environment for testing"""
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        yield mock_run


# Integration test
def test_end_to_end_scad_update_behavior(mock_openscad_environment):
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
    
    # All outputs should be different (even the repeated cube)
    assert len(set(outputs)) == len(outputs), "All SCAD updates should produce unique outputs"
    
    # Each output should be non-empty
    for output in outputs:
        assert len(output) > 0, "Each SCAD update should produce non-empty output"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])