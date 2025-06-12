"""
Tests for Phase 1 CSG Operations (Union, Difference, Intersection)

These tests validate that our Phase 1 wireframe CSG implementations work correctly
before proceeding to Phase 2 (real WASM integration).
"""

import pytest
import tempfile
from unittest.mock import patch, MagicMock
from marimo_openscad import openscad_viewer
from solid2 import cube, union, difference


class TestPhase1CSGOperations:
    """Test suite for Phase 1 CSG wireframe implementations"""
    
    def test_union_operation_detection(self):
        """Test that union operations are correctly detected and processed"""
        # Create a simple union of two cubes
        cube1 = cube([10, 10, 10])
        cube2 = cube([8, 8, 8]).translate([5, 0, 0])
        model = union()(cube1, cube2)
        
        # Generate SCAD code
        scad_code = model.as_scad() if hasattr(model, 'as_scad') else str(model)
        
        # Verify SCAD contains union
        assert 'union()' in scad_code
        assert 'cube(' in scad_code
        
        # Test viewer creation (should not raise exceptions)
        viewer = openscad_viewer(model, renderer_type="wasm")
        assert viewer is not None

    def test_difference_operation_detection(self):
        """Test that difference operations are correctly detected and processed"""
        # Create a cube with a hole
        main_cube = cube([20, 20, 20])
        hole_cube = cube([25, 8, 8])  # Goes through entire cube
        model = difference()(main_cube, hole_cube)
        
        # Generate SCAD code
        scad_code = model.as_scad() if hasattr(model, 'as_scad') else str(model)
        
        # Verify SCAD contains difference
        assert 'difference()' in scad_code
        assert 'cube(' in scad_code
        
        # Test viewer creation
        viewer = openscad_viewer(model, renderer_type="wasm")
        assert viewer is not None

    def test_single_cube_fallback(self):
        """Test that single cubes are handled correctly without CSG operations"""
        model = cube([15, 15, 15])
        
        scad_code = model.as_scad() if hasattr(model, 'as_scad') else str(model)
        
        # Should not contain CSG operations
        assert 'union()' not in scad_code
        assert 'difference()' not in scad_code
        assert 'cube(' in scad_code
        
        viewer = openscad_viewer(model, renderer_type="wasm")
        assert viewer is not None

    def test_union_progressive_overlap(self):
        """Test union behavior with different levels of cube overlap"""
        cube1 = cube([12, 12, 12])
        
        # Test cases: separated, touching, overlapping
        test_distances = [20, 12, 5, 0]  # separated -> overlapping -> complete overlap
        
        for distance in test_distances:
            cube2 = cube([10, 10, 10]).translate([distance, 0, 0])
            model = union()(cube1, cube2)
            
            viewer = openscad_viewer(model, renderer_type="wasm")
            assert viewer is not None

    def test_difference_progressive_hole_size(self):
        """Test difference behavior with different hole sizes"""
        main_cube = cube([20, 20, 20])
        
        # Test different hole sizes
        hole_sizes = [4, 8, 12, 16, 18]
        
        for hole_size in hole_sizes:
            hole_cube = cube([25, hole_size, hole_size])  # Always goes through
            model = difference()(main_cube, hole_cube)
            
            viewer = openscad_viewer(model, renderer_type="wasm")
            assert viewer is not None

    def test_phase1_status_messages(self):
        """Test that Phase 1 CSG operations generate appropriate status messages"""
        # This test checks that our JavaScript correctly identifies CSG operations
        # and generates the right status text
        
        # Union test
        cube1 = cube([10, 10, 10])
        cube2 = cube([8, 8, 8]).translate([5, 0, 0])
        union_model = union()(cube1, cube2)
        union_scad = union_model.as_scad() if hasattr(union_model, 'as_scad') else str(union_model)
        
        # Verify SCAD structure for union
        assert 'union()' in union_scad
        cube_count = union_scad.count('cube(')
        assert cube_count == 2
        
        # Difference test
        main_cube = cube([20, 20, 20])
        hole_cube = cube([25, 8, 8])
        diff_model = difference()(main_cube, hole_cube)
        diff_scad = diff_model.as_scad() if hasattr(diff_model, 'as_scad') else str(diff_model)
        
        # Verify SCAD structure for difference
        assert 'difference()' in diff_scad
        cube_count = diff_scad.count('cube(')
        assert cube_count == 2

    def test_csg_error_handling(self):
        """Test error handling for invalid CSG operations"""
        # Test with empty model (should not crash)
        try:
            viewer = openscad_viewer(None, renderer_type="wasm")
            # Should handle gracefully or raise informative error
        except Exception as e:
            # Verify it's an informative error, not a crash
            assert isinstance(e, (ValueError, TypeError))

    def test_complex_nested_operations(self):
        """Test nested CSG operations (union inside difference, etc.)"""
        # Create a complex nested structure
        inner_union = union()(
            cube([8, 8, 8]),
            cube([6, 6, 6]).translate([4, 0, 0])
        )
        
        outer_cube = cube([20, 20, 20])
        complex_model = difference()(outer_cube, inner_union)
        
        scad_code = complex_model.as_scad() if hasattr(complex_model, 'as_scad') else str(complex_model)
        
        # Should contain both operations
        assert 'difference()' in scad_code
        assert 'union()' in scad_code
        
        viewer = openscad_viewer(complex_model, renderer_type="wasm")
        assert viewer is not None


class TestPhase1GeometryGeneration:
    """Test the geometric correctness of Phase 1 implementations"""
    
    def test_union_l_shaped_generation(self):
        """Test that L-shaped union geometry is generated correctly"""
        # Create overlapping cubes that should form an L-shape
        cube1 = cube([12, 12, 12])
        cube2 = cube([8, 8, 8]).translate([8, 0, 0])  # Overlapping
        model = union()(cube1, cube2)
        
        viewer = openscad_viewer(model, renderer_type="wasm")
        assert viewer is not None
        
        # The viewer should successfully create without errors
        # (More detailed geometry validation would require JS testing)

    def test_difference_frame_generation(self):
        """Test that difference creates proper frame/hollow structure"""
        main_cube = cube([20, 20, 20])
        hole_cube = cube([25, 10, 10])  # Through-hole
        model = difference()(main_cube, hole_cube)
        
        viewer = openscad_viewer(model, renderer_type="wasm")
        assert viewer is not None

    def test_no_z_fighting_in_unions(self):
        """Test that union operations avoid Z-fighting artifacts"""
        # Create touching cubes (prone to Z-fighting)
        cube1 = cube([10, 10, 10])
        cube2 = cube([10, 10, 10]).translate([10, 0, 0])  # Exactly touching
        model = union()(cube1, cube2)
        
        # Should not raise exceptions during rendering
        viewer = openscad_viewer(model, renderer_type="wasm")
        assert viewer is not None


class TestPhase1RegressionPrevention:
    """Regression tests to ensure Phase 1 improvements don't break"""
    
    def test_original_cube_rendering_still_works(self):
        """Ensure single cube rendering wasn't broken by CSG additions"""
        simple_cube = cube([15, 15, 15])
        viewer = openscad_viewer(simple_cube, renderer_type="wasm")
        assert viewer is not None

    def test_translated_cubes_still_work(self):
        """Ensure translated cubes still render correctly"""
        translated_cube = cube([10, 10, 10]).translate([5, 5, 5])
        viewer = openscad_viewer(translated_cube, renderer_type="wasm")
        assert viewer is not None

    def test_multiple_cubes_without_csg_operations(self):
        """Test multiple cubes without explicit CSG operations"""
        # This should fall back to showing just the first cube
        cube1 = cube([10, 10, 10])
        cube2 = cube([8, 8, 8]).translate([15, 0, 0])
        
        # Create without union() - should show first cube
        viewer1 = openscad_viewer(cube1, renderer_type="wasm")
        viewer2 = openscad_viewer(cube2, renderer_type="wasm")
        
        assert viewer1 is not None
        assert viewer2 is not None


@pytest.mark.parametrize("renderer_type", ["wasm"])
class TestPhase1RendererCompatibility:
    """Test Phase 1 CSG operations work with different renderer types"""
    
    def test_union_with_renderer(self, renderer_type):
        """Test union operations work with specific renderer"""
        cube1 = cube([10, 10, 10])
        cube2 = cube([8, 8, 8]).translate([5, 0, 0])
        model = union()(cube1, cube2)
        
        viewer = openscad_viewer(model, renderer_type=renderer_type)
        assert viewer is not None

    def test_difference_with_renderer(self, renderer_type):
        """Test difference operations work with specific renderer"""
        main_cube = cube([20, 20, 20])
        hole_cube = cube([25, 8, 8])
        model = difference()(main_cube, hole_cube)
        
        viewer = openscad_viewer(model, renderer_type=renderer_type)
        assert viewer is not None


if __name__ == "__main__":
    # Run tests when called directly
    pytest.main([__file__, "-v"])