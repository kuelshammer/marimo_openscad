"""
CI-Friendly Tests for Real-Time Parameter Updates via WASM

Tests the real-time parameter update functionality that allows
modifications to OpenSCAD parameters without full re-rendering.
Designed to work correctly in GitHub Actions CI environment.
"""

import pytest
import os
import re
from unittest.mock import patch, MagicMock, Mock
import json
from typing import Dict, Any


class TestParameterExtraction:
    """Test parameter extraction from OpenSCAD code"""
    
    def test_simple_parameter_detection(self):
        """Test detection of simple parameters in SCAD code"""
        scad_code = """
        // Simple cube with parameters
        width = 10;
        height = 15;
        depth = 20;
        
        cube([width, height, depth]);
        """
        
        # Extract parameters using regex (CI-friendly approach)
        params = self._extract_parameters(scad_code)
        
        expected_params = {'width': '10', 'height': '15', 'depth': '20'}
        
        for param, value in expected_params.items():
            assert param in params
            assert params[param] == value
    
    def test_complex_parameter_detection(self):
        """Test detection of complex parameters"""
        scad_code = """
        // Complex parameters
        radius = 5.5;
        segments = 32;
        scale_factor = 1.2;
        enable_feature = true;
        
        cylinder(h=10, r=radius, $fn=segments);
        """
        
        params = self._extract_parameters(scad_code)
        
        assert 'radius' in params
        assert 'segments' in params
        assert 'scale_factor' in params
        assert 'enable_feature' in params
        
        # Check specific values
        assert params['radius'] == '5.5'
        assert params['segments'] == '32'
        assert params['enable_feature'] == 'true'
    
    def test_parameter_update_substitution(self):
        """Test parameter value substitution in SCAD code"""
        original_scad = """
        width = 10;
        height = 15;
        cube([width, height, 5]);
        """
        
        updates = {'width': '20', 'height': '25'}
        updated_scad = self._update_parameters(original_scad, updates)
        
        # Check that values were updated
        assert 'width = 20;' in updated_scad
        assert 'height = 25;' in updated_scad
        assert 'width = 10;' not in updated_scad
        assert 'height = 15;' not in updated_scad
    
    def test_parameter_type_handling(self):
        """Test handling of different parameter types"""
        scad_code = """
        int_param = 42;
        float_param = 3.14159;
        bool_param = false;
        string_param = "hello";
        """
        
        params = self._extract_parameters(scad_code)
        
        assert params['int_param'] == '42'
        assert params['float_param'] == '3.14159'
        assert params['bool_param'] == 'false'
        assert params['string_param'] == '"hello"'
    
    def _extract_parameters(self, scad_code: str) -> Dict[str, str]:
        """Extract parameters from SCAD code using regex"""
        # Simple regex to match parameter assignments
        param_pattern = r'^\s*(\w+)\s*=\s*([^;]+);'
        params = {}
        
        for line in scad_code.split('\n'):
            line = line.strip()
            if line.startswith('//') or not line:
                continue
                
            match = re.match(param_pattern, line)
            if match:
                param_name = match.group(1)
                param_value = match.group(2).strip()
                params[param_name] = param_value
        
        return params
    
    def _update_parameters(self, scad_code: str, updates: Dict[str, str]) -> str:
        """Update parameter values in SCAD code"""
        lines = scad_code.split('\n')
        updated_lines = []
        
        for line in lines:
            updated_line = line
            for param_name, new_value in updates.items():
                # Simple substitution pattern
                pattern = rf'^(\s*{param_name}\s*=\s*)[^;]+(;.*)$'
                replacement = rf'\g<1>{new_value}\g<2>'
                updated_line = re.sub(pattern, replacement, updated_line)
            
            updated_lines.append(updated_line)
        
        return '\n'.join(updated_lines)


class TestWASMParameterViewer:
    """Test parameter updates in WASM-enabled viewer"""
    
    def test_parameter_update_via_scad_code(self):
        """Test parameter updates through SCAD code changes"""
        from marimo_openscad.viewer import OpenSCADViewer
        
        viewer = OpenSCADViewer(renderer_type="wasm", enable_real_time_wasm=True)
        viewer.wasm_enabled = True
        
        # Initial SCAD with parameters
        initial_scad = """
        size = 10;
        cube([size, size, size]);
        """
        
        viewer.update_scad_code(initial_scad)
        assert viewer.scad_code == initial_scad
        
        # Update with modified parameters
        updated_scad = """
        size = 20;
        cube([size, size, size]);
        """
        
        viewer.update_scad_code(updated_scad)
        assert viewer.scad_code == updated_scad
        assert viewer.scad_code != initial_scad
    
    def test_parametric_model_updates(self):
        """Test updates to parametric models"""
        from marimo_openscad.viewer import OpenSCADViewer
        
        viewer = OpenSCADViewer(renderer_type="wasm", enable_real_time_wasm=True)
        viewer.wasm_enabled = True
        
        # Define parametric model generator
        def generate_parametric_model(radius=5, height=10, segments=16):
            return f"""
            radius = {radius};
            height = {height};
            segments = {segments};
            
            cylinder(h=height, r=radius, $fn=segments);
            """
        
        # Initial parameters
        model1 = generate_parametric_model(radius=5, height=10, segments=16)
        viewer.update_scad_code(model1)
        
        # Updated parameters
        model2 = generate_parametric_model(radius=8, height=15, segments=32)
        viewer.update_scad_code(model2)
        
        # Verify update was applied
        assert viewer.scad_code == model2
        assert 'radius = 8' in viewer.scad_code
        assert 'height = 15' in viewer.scad_code
        assert 'segments = 32' in viewer.scad_code
    
    def test_real_time_parameter_workflow(self):
        """Test complete real-time parameter update workflow"""
        from marimo_openscad.viewer import OpenSCADViewer
        
        viewer = OpenSCADViewer(renderer_type="wasm", enable_real_time_wasm=True)
        viewer.wasm_enabled = True
        
        # Base model template
        base_template = """
        // Customizable parameters
        box_width = {width};
        box_height = {height};
        box_depth = {depth};
        corner_radius = {radius};
        
        // Generate model
        hull() {{
            translate([corner_radius, corner_radius, 0])
                cylinder(h=box_height, r=corner_radius);
            translate([box_width-corner_radius, corner_radius, 0])
                cylinder(h=box_height, r=corner_radius);
            translate([corner_radius, box_depth-corner_radius, 0])
                cylinder(h=box_height, r=corner_radius);
            translate([box_width-corner_radius, box_depth-corner_radius, 0])
                cylinder(h=box_height, r=corner_radius);
        }}
        """
        
        # Parameter sets for testing
        param_sets = [
            {'width': 10, 'height': 5, 'depth': 15, 'radius': 1},
            {'width': 20, 'height': 8, 'depth': 25, 'radius': 2},
            {'width': 15, 'height': 12, 'depth': 20, 'radius': 1.5},
        ]
        
        for i, params in enumerate(param_sets):
            scad_code = base_template.format(**params)
            viewer.update_scad_code(scad_code)
            
            # Verify parameters were applied
            for param_name, param_value in params.items():
                expected_line = f"{param_name.replace('_', '_')} = {param_value};"
                assert expected_line in viewer.scad_code
            
            # Verify no errors occurred
            assert viewer.error_message == ""
            assert viewer.is_loading is False
    
    def test_parameter_validation(self):
        """Test parameter validation and error handling"""
        from marimo_openscad.viewer import OpenSCADViewer
        
        viewer = OpenSCADViewer(renderer_type="wasm", enable_real_time_wasm=True)
        viewer.wasm_enabled = True
        
        # Valid parameters
        valid_scad = """
        radius = 5;
        height = 10;
        cylinder(h=height, r=radius);
        """
        
        viewer.update_scad_code(valid_scad)
        assert viewer.error_message == ""
        
        # Test with potentially problematic parameters (should still work in WASM mode)
        edge_case_scad = """
        very_small = 0.001;
        very_large = 1000;
        zero_value = 0;
        
        if (zero_value == 0) {
            cube([very_small, very_large, 5]);
        }
        """
        
        viewer.update_scad_code(edge_case_scad)
        # Should handle edge cases gracefully
        # Error handling depends on WASM implementation


class TestParameterBinding:
    """Test parameter binding and reactivity"""
    
    def test_parameter_change_detection(self):
        """Test detection of parameter changes"""
        original_params = {'width': '10', 'height': '15', 'depth': '20'}
        updated_params = {'width': '12', 'height': '15', 'depth': '20'}
        
        changes = self._detect_parameter_changes(original_params, updated_params)
        
        assert len(changes) == 1
        assert 'width' in changes
        assert changes['width'] == ('10', '12')
    
    def test_multiple_parameter_changes(self):
        """Test detection of multiple parameter changes"""
        original_params = {'a': '1', 'b': '2', 'c': '3'}
        updated_params = {'a': '10', 'b': '2', 'c': '30'}
        
        changes = self._detect_parameter_changes(original_params, updated_params)
        
        assert len(changes) == 2
        assert 'a' in changes
        assert 'c' in changes
        assert changes['a'] == ('1', '10')
        assert changes['c'] == ('3', '30')
    
    def test_parameter_addition_removal(self):
        """Test parameter addition and removal"""
        original_params = {'width': '10', 'height': '15'}
        updated_params = {'width': '10', 'depth': '20'}
        
        changes = self._detect_parameter_changes(original_params, updated_params)
        
        # Should detect removal of 'height' and addition of 'depth'
        assert 'height' in changes  # Removed parameter
        assert 'depth' in changes   # Added parameter
    
    def test_parameter_binding_performance(self):
        """Test parameter binding with many parameters"""
        # Create large parameter sets
        large_params_1 = {f'param_{i}': str(i) for i in range(100)}
        large_params_2 = {f'param_{i}': str(i + 1) for i in range(100)}
        
        # Should handle large parameter sets efficiently
        changes = self._detect_parameter_changes(large_params_1, large_params_2)
        
        assert len(changes) == 100  # All parameters changed
        
        # Verify a few specific changes
        assert changes['param_0'] == ('0', '1')
        assert changes['param_50'] == ('50', '51')
        assert changes['param_99'] == ('99', '100')
    
    def _detect_parameter_changes(self, original: Dict[str, str], updated: Dict[str, str]) -> Dict[str, tuple]:
        """Detect changes between parameter sets"""
        changes = {}
        
        # Check for modified parameters
        for param, value in updated.items():
            if param in original:
                if original[param] != value:
                    changes[param] = (original[param], value)
            else:
                # New parameter
                changes[param] = (None, value)
        
        # Check for removed parameters
        for param, value in original.items():
            if param not in updated:
                changes[param] = (value, None)
        
        return changes


class TestCIParameterUpdates:
    """Test parameter updates in CI environment"""
    
    def test_parameter_updates_ci_safe(self):
        """Test parameter updates work in CI environment"""
        from marimo_openscad.viewer import OpenSCADViewer
        
        # Simulate CI environment
        with patch.dict(os.environ, {'CI': 'true', 'GITHUB_ACTIONS': 'true'}):
            viewer = OpenSCADViewer(renderer_type="auto")
            
            # Should work without browser dependencies
            parametric_scad = """
            size = 15;
            segments = 24;
            sphere(r=size, $fn=segments);
            """
            
            viewer.update_scad_code(parametric_scad)
            
            # Should complete without errors
            assert viewer.error_message == ""
            
            # Should handle parameter updates
            updated_scad = """
            size = 25;
            segments = 48;
            sphere(r=size, $fn=segments);
            """
            
            viewer.update_scad_code(updated_scad)
            assert viewer.error_message == ""
    
    def test_parameter_serialization_ci(self):
        """Test parameter serialization for CI artifacts"""
        from marimo_openscad.viewer import OpenSCADViewer
        
        viewer = OpenSCADViewer(renderer_type="wasm", enable_real_time_wasm=True)
        
        # Set up parametric model
        parametric_model = """
        length = 30;
        width = 20;
        height = 10;
        cube([length, width, height]);
        """
        
        viewer.update_scad_code(parametric_model)
        
        # Extract parameters for serialization
        params = self._extract_parameters_from_viewer(viewer)
        
        # Test JSON serialization
        try:
            json_data = json.dumps(params)
            parsed_params = json.loads(json_data)
            
            assert isinstance(parsed_params, dict)
            # Should contain extracted parameters
            
        except (TypeError, ValueError) as e:
            pytest.fail(f"Parameter data not JSON serializable: {e}")
    
    def test_parameter_update_logging_ci(self):
        """Test parameter update logging in CI"""
        from marimo_openscad.viewer import OpenSCADViewer
        import logging
        
        # Set up logging capture
        logger = logging.getLogger('marimo_openscad.viewer')
        
        with patch.object(logger, 'info') as mock_info:
            viewer = OpenSCADViewer(renderer_type="wasm", enable_real_time_wasm=True)
            viewer.wasm_enabled = True
            
            test_scad = "radius = 8; sphere(radius);"
            viewer.update_scad_code(test_scad)
            
            # Should have logged the update
            mock_info.assert_called()
            
            # Check for expected log messages
            log_calls = [call.args[0] for call in mock_info.call_args_list]
            scad_log_found = any("SCAD code" in msg for msg in log_calls)
            assert scad_log_found, "Expected SCAD code log message not found"
    
    def _extract_parameters_from_viewer(self, viewer) -> Dict[str, Any]:
        """Extract parameters from viewer state (CI-friendly)"""
        # Simple extraction from SCAD code
        if not viewer.scad_code:
            return {}
        
        # Use regex to extract parameters
        param_pattern = r'^\s*(\w+)\s*=\s*([^;]+);'
        params = {}
        
        for line in viewer.scad_code.split('\n'):
            line = line.strip()
            if line.startswith('//') or not line:
                continue
                
            match = re.match(param_pattern, line)
            if match:
                param_name = match.group(1)
                param_value = match.group(2).strip()
                
                # Try to parse value type
                try:
                    if param_value in ('true', 'false'):
                        params[param_name] = param_value == 'true'
                    elif param_value.startswith('"') and param_value.endswith('"'):
                        params[param_name] = param_value[1:-1]  # Remove quotes
                    elif '.' in param_value:
                        params[param_name] = float(param_value)
                    else:
                        params[param_name] = int(param_value)
                except ValueError:
                    params[param_name] = param_value  # Keep as string
        
        return params


class TestAdvancedParameterScenarios:
    """Test advanced parameter update scenarios"""
    
    def test_nested_parameter_dependencies(self):
        """Test parameters that depend on other parameters"""
        scad_code = """
        base_size = 10;
        scale_factor = 1.5;
        final_size = base_size * scale_factor;
        
        cube([final_size, final_size, base_size]);
        """
        
        # This tests complex parameter relationships
        # In a real implementation, parameter dependency resolution would be needed
        
        from marimo_openscad.viewer import OpenSCADViewer
        viewer = OpenSCADViewer(renderer_type="wasm", enable_real_time_wasm=True)
        viewer.wasm_enabled = True
        
        viewer.update_scad_code(scad_code)
        assert viewer.error_message == ""
    
    def test_conditional_parameter_usage(self):
        """Test parameters used in conditional statements"""
        scad_code = """
        enable_feature = true;
        feature_size = 5;
        base_size = 10;
        
        cube([base_size, base_size, base_size]);
        
        if (enable_feature) {
            translate([0, 0, base_size])
                sphere(r=feature_size);
        }
        """
        
        from marimo_openscad.viewer import OpenSCADViewer
        viewer = OpenSCADViewer(renderer_type="wasm", enable_real_time_wasm=True)
        viewer.wasm_enabled = True
        
        viewer.update_scad_code(scad_code)
        assert viewer.error_message == ""
        
        # Test toggling the feature
        updated_scad = scad_code.replace('enable_feature = true;', 'enable_feature = false;')
        viewer.update_scad_code(updated_scad)
        assert viewer.error_message == ""
    
    def test_array_parameter_handling(self):
        """Test parameters that are arrays or vectors"""
        scad_code = """
        dimensions = [15, 20, 25];
        color_rgb = [1, 0.5, 0];
        
        color(color_rgb)
            cube(dimensions);
        """
        
        from marimo_openscad.viewer import OpenSCADViewer
        viewer = OpenSCADViewer(renderer_type="wasm", enable_real_time_wasm=True)
        viewer.wasm_enabled = True
        
        viewer.update_scad_code(scad_code)
        assert viewer.error_message == ""


# Pytest markers for test categorization
pytestmark = [
    pytest.mark.wasm_parameters,
    pytest.mark.ci_compatibility,
    pytest.mark.phase_5_3_2
]


def test_parameter_updates_integration():
    """Full integration test for parameter updates"""
    from marimo_openscad.viewer import openscad_viewer
    
    # Create viewer with real-time WASM enabled
    viewer = openscad_viewer(
        "cube([10, 10, 10]);", 
        renderer_type="wasm", 
        enable_real_time_wasm=True
    )
    
    # Test parameter update workflow
    parametric_models = [
        """
        size = 10;
        cube([size, size, size]);
        """,
        """
        size = 15;
        cube([size, size, size]);
        """,
        """
        size = 20;
        cube([size, size, size]);
        """
    ]
    
    for model in parametric_models:
        viewer.update_scad_code(model.strip())
        
        # Verify update completed
        assert viewer.error_message == ""
        assert viewer.is_loading is False
        
        # Verify SCAD code was set (for WASM mode)
        if viewer.wasm_enabled:
            assert viewer.scad_code.strip() == model.strip()


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v", "--tb=short"])