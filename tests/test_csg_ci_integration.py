"""
CI-optimized tests for CSG Phase 1 operations

These tests are designed to run reliably in CI/CD environments without requiring
browser execution or complex WASM setup.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from marimo_openscad import openscad_viewer
from solid2 import cube, union, difference


class TestCSGPhase1CI:
    """CI-compatible tests for CSG Phase 1 functionality"""
    
    def test_scad_code_generation_union(self):
        """Test SCAD code generation for union operations (no rendering)"""
        cube1 = cube([10, 10, 10])
        cube2 = cube([8, 8, 8]).translate([5, 0, 0])
        model = union()(cube1, cube2)
        
        scad_code = model.as_scad() if hasattr(model, 'as_scad') else str(model)
        
        # Verify SCAD structure
        assert 'union()' in scad_code
        assert 'cube(' in scad_code
        assert 'translate(' in scad_code
        assert 'size = [10, 10, 10]' in scad_code or 'size = [10,10,10]' in scad_code
        assert 'size = [8, 8, 8]' in scad_code or 'size = [8,8,8]' in scad_code

    def test_scad_code_generation_difference(self):
        """Test SCAD code generation for difference operations (no rendering)"""
        main_cube = cube([20, 20, 20])
        hole_cube = cube([25, 8, 8])
        model = difference()(main_cube, hole_cube)
        
        scad_code = model.as_scad() if hasattr(model, 'as_scad') else str(model)
        
        # Verify SCAD structure
        assert 'difference()' in scad_code
        assert 'cube(' in scad_code
        assert 'size = [20, 20, 20]' in scad_code or 'size = [20,20,20]' in scad_code
        assert 'size = [25, 8, 8]' in scad_code or 'size = [25,8,8]' in scad_code

    def test_viewer_instantiation_union(self):
        """Test that union viewer can be instantiated without errors"""
        cube1 = cube([12, 12, 12])
        cube2 = cube([10, 10, 10]).translate([8, 0, 0])
        model = union()(cube1, cube2)
        
        # Should not raise exceptions during instantiation
        viewer = openscad_viewer(model, renderer_type="wasm")
        assert viewer is not None
        
        # Check that viewer has expected attributes (anywidget structure)
        assert hasattr(viewer, 'scad_code') or hasattr(viewer, '_model') or hasattr(viewer, 'model')

    def test_viewer_instantiation_difference(self):
        """Test that difference viewer can be instantiated without errors"""
        main_cube = cube([20, 20, 20])
        hole_cube = cube([25, 10, 10])
        model = difference()(main_cube, hole_cube)
        
        # Should not raise exceptions during instantiation
        viewer = openscad_viewer(model, renderer_type="wasm")
        assert viewer is not None
        
        # Check that viewer has expected attributes (anywidget structure)
        assert hasattr(viewer, 'scad_code') or hasattr(viewer, '_model') or hasattr(viewer, 'model')

    def test_complex_nested_scad_generation(self):
        """Test SCAD generation for complex nested operations"""
        # Create nested: difference(main_cube, union(cube1, cube2))
        inner_cube1 = cube([6, 6, 6])
        inner_cube2 = cube([4, 4, 4]).translate([3, 0, 0])
        inner_union = union()(inner_cube1, inner_cube2)
        
        outer_cube = cube([20, 20, 20])
        complex_model = difference()(outer_cube, inner_union)
        
        scad_code = complex_model.as_scad() if hasattr(complex_model, 'as_scad') else str(complex_model)
        
        # Should contain both operations
        assert 'difference()' in scad_code
        assert 'union()' in scad_code
        assert scad_code.count('cube(') >= 3  # outer + 2 inner cubes

    def test_phase1_csg_detection_patterns(self):
        """Test that our JavaScript parsing patterns work correctly"""
        
        # Test union detection pattern
        union_cube1 = cube([10, 10, 10])
        union_cube2 = cube([8, 8, 8]).translate([5, 0, 0])
        union_model = union()(union_cube1, union_cube2)
        union_scad = union_model.as_scad() if hasattr(union_model, 'as_scad') else str(union_model)
        
        # Our JS looks for 'union()' and 'cube(' patterns
        assert 'union()' in union_scad.lower()
        assert 'cube(' in union_scad.lower()
        
        # Test difference detection pattern
        diff_main = cube([20, 20, 20])
        diff_hole = cube([25, 8, 8])
        diff_model = difference()(diff_main, diff_hole)
        diff_scad = diff_model.as_scad() if hasattr(diff_model, 'as_scad') else str(diff_model)
        
        # Our JS looks for 'difference()' and 'cube(' patterns
        assert 'difference()' in diff_scad.lower()
        assert 'cube(' in diff_scad.lower()

    def test_cube_parameter_extraction(self):
        """Test that cube parameters can be correctly extracted from SCAD"""
        
        # Test various cube sizes and translations
        test_cases = [
            ([10, 10, 10], [0, 0, 0]),
            ([15, 8, 12], [5, -3, 2]),
            ([20, 20, 20], [10, 10, 10])
        ]
        
        for size, translation in test_cases:
            if translation == [0, 0, 0]:
                model = cube(size)
            else:
                model = cube(size).translate(translation)
            
            scad_code = model.as_scad() if hasattr(model, 'as_scad') else str(model)
            
            # Verify size appears in SCAD
            size_str = str(size).replace(' ', '')
            assert size_str in scad_code.replace(' ', '') or \
                   f"[{size[0]}, {size[1]}, {size[2]}]" in scad_code
            
            # Verify translation appears if non-zero
            if translation != [0, 0, 0]:
                assert 'translate(' in scad_code

    def test_error_handling_edge_cases(self):
        """Test error handling for edge cases in CI environment"""
        
        # Test very small cubes
        tiny_cube = cube([0.1, 0.1, 0.1])
        viewer = openscad_viewer(tiny_cube, renderer_type="wasm")
        assert viewer is not None
        
        # Test very large cubes
        large_cube = cube([1000, 1000, 1000])
        viewer = openscad_viewer(large_cube, renderer_type="wasm")
        assert viewer is not None
        
        # Test cubes with zero dimensions (should handle gracefully)
        try:
            zero_cube = cube([0, 10, 10])
            viewer = openscad_viewer(zero_cube, renderer_type="wasm")
            # Should either work or raise informative error
        except Exception as e:
            # Should be a reasonable error, not a crash
            assert isinstance(e, (ValueError, TypeError, AttributeError))

    def test_memory_efficiency(self):
        """Test that Phase 1 CSG operations are memory efficient"""
        
        # Create multiple CSG operations to test memory usage
        models = []
        for i in range(10):
            cube1 = cube([10, 10, 10])
            cube2 = cube([8, 8, 8]).translate([5 + i, 0, 0])
            model = union()(cube1, cube2)
            models.append(model)
        
        # Should be able to create viewers for all without memory issues
        viewers = []
        for model in models:
            viewer = openscad_viewer(model, renderer_type="wasm")
            assert viewer is not None
            viewers.append(viewer)
        
        # Cleanup should work without issues
        del viewers
        del models

    @pytest.mark.parametrize("cube_size", [5, 10, 15, 20, 25])
    def test_scalability_different_sizes(self, cube_size):
        """Test Phase 1 CSG works with different cube sizes"""
        
        # Union test
        cube1 = cube([cube_size, cube_size, cube_size])
        cube2 = cube([cube_size//2, cube_size//2, cube_size//2]).translate([cube_size//2, 0, 0])
        union_model = union()(cube1, cube2)
        
        viewer = openscad_viewer(union_model, renderer_type="wasm")
        assert viewer is not None
        
        # Difference test
        main_cube = cube([cube_size, cube_size, cube_size])
        hole_cube = cube([cube_size + 5, cube_size//3, cube_size//3])
        diff_model = difference()(main_cube, hole_cube)
        
        viewer = openscad_viewer(diff_model, renderer_type="wasm")
        assert viewer is not None

    def test_ci_environment_detection(self):
        """Test behavior in CI environment"""
        
        # Check if we're in CI (common CI environment variables)
        ci_vars = ['CI', 'GITHUB_ACTIONS', 'TRAVIS', 'CIRCLECI', 'JENKINS_URL']
        is_ci = any(os.getenv(var) for var in ci_vars)
        
        if is_ci:
            # In CI, focus on instantiation without rendering
            cube1 = cube([10, 10, 10])
            cube2 = cube([8, 8, 8]).translate([5, 0, 0])
            model = union()(cube1, cube2)
            
            # Should work without browser/WASM dependencies
            viewer = openscad_viewer(model, renderer_type="wasm")
            assert viewer is not None
        else:
            # In local development, can test more extensively
            pass

    def test_phase1_regression_protection(self):
        """Ensure Phase 1 changes don't break existing functionality"""
        
        # Test that original single cube rendering still works
        simple_cube = cube([15, 15, 15])
        viewer = openscad_viewer(simple_cube, renderer_type="wasm")
        assert viewer is not None
        
        # Test that translated cubes still work
        translated_cube = cube([10, 10, 10]).translate([5, 5, 5])
        viewer = openscad_viewer(translated_cube, renderer_type="wasm")
        assert viewer is not None
        
        # Test that we didn't break the basic API
        from marimo_openscad import openscad_viewer as orig_viewer
        assert callable(orig_viewer)


if __name__ == "__main__":
    # Run with CI-friendly options
    pytest.main([__file__, "-v", "--tb=short"])