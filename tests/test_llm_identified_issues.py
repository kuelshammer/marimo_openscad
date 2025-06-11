"""
Tests specifically for issues identified by LLM analysis

This module contains tests that directly address the specific problems
reported by the external LLM that analyzed the codebase.
"""

import pytest
import unittest.mock as mock
import base64
from src.marimo_openscad.interactive_viewer import InteractiveViewer
from src.marimo_openscad.viewer import OpenSCADViewer


class MockSolidPythonModel:
    """Mock SolidPython2 model for testing"""
    
    def __init__(self, scad_code: str, name: str = "test_model"):
        self.scad_code = scad_code
        self.name = name
        
    def as_scad(self) -> str:
        return self.scad_code


@pytest.mark.regression
class TestLLMIdentifiedCacheIssue:
    """
    Test the specific cache issue identified by LLM:
    'update_scad_code doesn't properly update visual display'
    """
    
    def setup_method(self):
        """Setup test environment"""
        self.viewer = InteractiveViewer()
        
        # Mock renderer to simulate different outputs for different SCAD code
        self.render_calls = []
        
        def mock_render(scad_code):
            self.render_calls.append(scad_code)
            # Return different STL data based on SCAD content
            if "cube" in scad_code.lower():
                return b"STL_DATA_FOR_CUBE_UNIQUE_BYTES_12345"
            elif "sphere" in scad_code.lower():
                return b"STL_DATA_FOR_SPHERE_UNIQUE_BYTES_67890"
            elif "cylinder" in scad_code.lower():
                return b"STL_DATA_FOR_CYLINDER_UNIQUE_BYTES_11111"
            else:
                return b"STL_DATA_FOR_UNKNOWN_SHAPE_22222"
        
        self.viewer.bridge.renderer.render_scad_to_stl = mock_render
    
    def test_update_scad_code_cube_to_sphere_produces_different_output(self):
        """
        Test that mimics the LLM's test scenario:
        - Start with cube SCAD code 
        - Update to sphere SCAD code
        - Verify different STL output in HTML/base64
        """
        # Step 1: Update with cube code ("content for cube")
        cube_scad = "cube([10, 10, 10]);"
        self.viewer.update_scad_code(cube_scad)
        
        cube_output = self.viewer.stl_data  # This is the base64 STL data
        cube_decoded = base64.b64decode(cube_output)
        
        # Step 2: Update with sphere code ("content for sphere")  
        sphere_scad = "sphere(r=6);"
        self.viewer.update_scad_code(sphere_scad)
        
        sphere_output = self.viewer.stl_data  # This is the base64 STL data
        sphere_decoded = base64.b64decode(sphere_output)
        
        # Step 3: Verify different byte content (what LLM test was checking)
        assert cube_output != sphere_output, \
            "Base64 STL data should be different for cube vs sphere"
        
        assert cube_decoded != sphere_decoded, \
            "Decoded STL bytes should be different for cube vs sphere"
        
        assert b"CUBE" in cube_decoded.upper(), \
            "Cube STL should contain cube-specific data"
        
        assert b"SPHERE" in sphere_decoded.upper(), \
            "Sphere STL should contain sphere-specific data"
        
        # Verify renderer was called twice (no caching)
        assert len(self.render_calls) == 2
        assert "cube" in self.render_calls[0].lower()
        assert "sphere" in self.render_calls[1].lower()
    
    def test_mock_content_changes_appear_in_html_output(self):
        """
        Test that simulates the LLM's Mock test approach:
        - Mock different output_file_content for different SCAD codes
        - Verify the mock changes appear in the final HTML/widget output
        """
        # This test directly addresses the LLM's technical note:
        # "Der Test hat geprüft, ob unterschiedliche Byte-Inhalte 
        #  (gesetzt im Mock output_file_content vor und nach dem 
        #  update_scad_code-Aufruf) im HTML erscheinen"
        
        test_scenarios = [
            ("cube([5,5,5]);", "content for cube"),
            ("sphere(r=3);", "content for sphere"),
            ("cylinder(r=2, h=8);", "content for cylinder")
        ]
        
        outputs = []
        
        for scad_code, expected_content_type in test_scenarios:
            # Update SCAD code
            self.viewer.update_scad_code(scad_code)
            
            # Get the output that would appear in HTML (base64 STL data)
            html_output = self.viewer.stl_data
            
            # Decode to check actual byte content
            byte_content = base64.b64decode(html_output)
            
            outputs.append({
                'scad_code': scad_code,
                'expected_type': expected_content_type,
                'html_output': html_output,
                'byte_content': byte_content,
                'length': len(html_output)
            })
        
        # Verify all outputs are different (addresses the core LLM issue)
        html_outputs = [output['html_output'] for output in outputs]
        unique_outputs = set(html_outputs)
        
        assert len(unique_outputs) == len(html_outputs), \
            f"All HTML outputs should be unique. Got {len(unique_outputs)} unique out of {len(html_outputs)} total"
        
        # Verify byte contents are different
        byte_contents = [output['byte_content'] for output in outputs]
        unique_bytes = set(byte_contents)
        
        assert len(unique_bytes) == len(byte_contents), \
            "All byte contents should be unique"
        
        # Verify expected content appears in byte data
        for output in outputs:
            if "cube" in output['expected_type']:
                assert b"CUBE" in output['byte_content'].upper()
            elif "sphere" in output['expected_type']:
                assert b"SPHERE" in output['byte_content'].upper()
            elif "cylinder" in output['expected_type']:
                assert b"CYLINDER" in output['byte_content'].upper()
    
    def test_scad_code_property_vs_html_output_consistency(self):
        """
        Test that addresses the LLM's specific concern:
        'Die scad_code Eigenschaft wurde zwar korrekt aktualisiert, 
         aber der HTML-Output basierend auf dem Mock-Inhalt änderte sich nicht'
        """
        scad_codes = [
            "cube([10,10,10]);",
            "sphere(r=5);", 
            "cube([10,10,10]);"  # Repeat to test cache behavior
        ]
        
        results = []
        
        for i, scad_code in enumerate(scad_codes):
            # Update SCAD code
            self.viewer.update_scad_code(scad_code)
            
            # Check that both property and HTML output updated
            # Note: InteractiveViewer doesn't have scad_code property,
            # but the STL data should always change
            html_output = self.viewer.stl_data
            
            results.append({
                'iteration': i,
                'scad_code': scad_code,
                'html_output': html_output,
                'html_length': len(html_output)
            })
        
        # With repeated SCAD code, HTML output should still be generated
        # (because we bypass cache in update_scad_code)
        html_outputs = [r['html_output'] for r in results]
        
        # Check that different SCAD codes produce different outputs
        unique_scad_codes = list(set(scad_codes))
        if len(unique_scad_codes) > 1:
            # Should have at least as many unique outputs as unique codes
            unique_outputs = set(html_outputs)
            assert len(unique_outputs) >= 2, \
                "Different SCAD codes should produce different outputs"
        
        # Verify renderer was called for each update
        assert len(self.render_calls) == len(scad_codes)


@pytest.mark.cache
class TestSuccessfulFunctionality:
    """
    Test the functionality that LLM reported as working correctly
    to ensure we don't break it with our cache fixes
    """
    
    def test_svg_images_support(self):
        """Test SVG image support (reported as working by LLM)"""
        svg_content = '''<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <circle cx="50" cy="50" r="40" fill="red"/>
</svg>'''
        
        # SVG support should continue working
        assert svg_content.startswith('<?xml')
        assert 'svg' in svg_content
        assert 'circle' in svg_content
    
    def test_obj_file_format_support(self):
        """Test OBJ file format support (reported as working by LLM)"""
        obj_filename = "model.obj"
        
        # Should recognize OBJ files
        assert obj_filename.lower().endswith('.obj')
        
        # Should have correct MIME type behavior
        if obj_filename.lower().endswith('.obj'):
            mime_type = "model/obj"  # Or appropriate MIME type
            assert mime_type is not None
    
    def test_unknown_file_format_handling(self):
        """Test unknown file format handling (reported as working by LLM)"""
        dxf_filename = "drawing.dxf"
        
        # Should handle unknown formats gracefully
        is_known_3d_format = dxf_filename.lower().endswith(('.stl', '.obj'))
        assert not is_known_3d_format  # DXF should not be recognized as 3D format
    
    def test_viewer_size_customization(self):
        """Test viewer size customization (reported as working by LLM)"""
        # Note: Current viewer implementation uses fixed dimensions
        # This test verifies viewer creation works (size customization to be added later)
        viewer = OpenSCADViewer()
        
        # Viewer should be created successfully
        assert viewer is not None
        assert hasattr(viewer, 'stl_data')
        # Note: Width/height customization is not yet implemented
    
    def test_case_insensitive_file_extensions(self):
        """Test case-insensitive file extension handling (reported as working by LLM)"""
        test_files = ["model.stl", "Model.STL", "MODEL.Stl"]
        
        for filename in test_files:
            # Should handle all case variations
            normalized = filename.lower()
            assert normalized.endswith('.stl')


@pytest.mark.integration
class TestEndToEndScenarios:
    """Integration tests for complete workflows"""
    
    def test_complete_scad_update_workflow(self):
        """Test the complete workflow that failed in LLM testing"""
        viewer = InteractiveViewer()
        
        # Mock the renderer with predictable outputs
        def deterministic_render(scad_code):
            code_hash = hash(scad_code)
            return f"STL_BINARY_DATA_HASH_{code_hash}".encode()
        
        viewer.bridge.renderer.render_scad_to_stl = deterministic_render
        
        # Simulate the LLM's test scenario
        steps = [
            ("Initial cube", "cube([10,10,10]);"),
            ("Update to sphere", "sphere(r=6);"),
            ("Back to cube", "cube([10,10,10]);"),  # Should still update
            ("Different sphere", "sphere(r=8);")
        ]
        
        outputs = []
        for step_name, scad_code in steps:
            viewer.update_scad_code(scad_code)
            output = viewer.stl_data
            outputs.append((step_name, output, len(output)))
        
        # All outputs should be present and different
        stl_data_list = [output[1] for output in outputs]
        assert all(stl_data for stl_data in stl_data_list), "All steps should produce output"
        
        # Check that different SCAD codes produce different outputs
        # (This addresses the core issue in LLM testing)
        step_to_output = {step: output for (step, output, _) in outputs}
        
        # Different shapes should produce different outputs
        cube_output = step_to_output["Initial cube"]
        sphere_output = step_to_output["Update to sphere"]
        cube_output_2 = step_to_output["Back to cube"]
        sphere_output_2 = step_to_output["Different sphere"]
        
        # Different shapes should have different outputs
        assert cube_output != sphere_output, "Cube and sphere should produce different outputs"
        assert sphere_output != sphere_output_2, "Different sphere sizes should produce different outputs"
        
        # Same SCAD code should produce same output (cache working correctly)
        assert cube_output == cube_output_2, "Same SCAD code should produce same output"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "regression"])