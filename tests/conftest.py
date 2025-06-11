"""
Pytest configuration and shared fixtures for marimo-openscad tests
"""

import pytest
import unittest.mock as mock
import tempfile
import sys
from pathlib import Path

# Add src to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_openscad_executable():
    """Mock OpenSCAD executable to avoid requiring actual installation"""
    with mock.patch('subprocess.run') as mock_run, \
         mock.patch('os.path.exists') as mock_exists, \
         mock.patch('marimo_openscad.openscad_renderer.subprocess.run') as mock_renderer_run:
        
        # Mock subprocess.run for OpenSCAD calls
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        mock_run.return_value.stdout = "OpenSCAD version 2021.01"
        
        # Mock the renderer's subprocess calls too
        mock_renderer_run.return_value.returncode = 0
        mock_renderer_run.return_value.stderr = ""
        mock_renderer_run.return_value.stdout = "OpenSCAD version 2021.01"
        
        # Mock path existence checks - make openscad appear available
        def mock_path_exists(path):
            if 'openscad' in path.lower():
                return True
            return False
        mock_exists.side_effect = mock_path_exists
        
        yield mock_run


@pytest.fixture
def mock_file_system():
    """Mock file system operations for testing"""
    with mock.patch('tempfile.TemporaryDirectory') as mock_temp_dir, \
         mock.patch('pathlib.Path') as mock_path:
        
        # Setup temporary directory mock
        mock_dir = mock.MagicMock()
        mock_dir.__enter__.return_value = mock_dir
        mock_dir.__exit__.return_value = None
        mock_temp_dir.return_value = mock_dir
        
        # Setup Path mock
        def create_mock_path(path_str):
            mock_file = mock.MagicMock()
            mock_file.__truediv__ = lambda self, other: create_mock_path(f"{path_str}/{other}")
            mock_file.__str__ = lambda: path_str
            
            if path_str.endswith('.stl'):
                mock_file.read_bytes.return_value = b"mock_stl_data"
            else:
                mock_file.write_text = mock.MagicMock()
            
            return mock_file
        
        mock_path.side_effect = create_mock_path
        mock_dir.__truediv__ = lambda self, other: create_mock_path(str(other))
        
        yield mock_temp_dir, mock_path


@pytest.fixture
def sample_scad_codes():
    """Provide sample SCAD codes for testing"""
    return {
        'cube': 'cube([10, 10, 10]);',
        'sphere': 'sphere(r=5);',
        'cylinder': 'cylinder(r=3, h=8);',
        'complex': '''
            difference() {
                cube([20, 20, 20]);
                sphere(r=8);
            }
        ''',
        'invalid': 'invalid_scad_syntax_here:::'
    }


@pytest.fixture
def mock_solid_python_model():
    """Factory for creating mock SolidPython2 models"""
    def _create_model(scad_code, params=None):
        class MockModel:
            def __init__(self, scad_code, params=None):
                self.scad_code = scad_code
                self.params = params or {}
            
            def as_scad(self):
                return self.scad_code
        
        return MockModel(scad_code, params)
    
    return _create_model


@pytest.fixture
def capture_render_calls():
    """Fixture to capture and track render calls for testing"""
    calls = []
    
    def mock_render(scad_code):
        calls.append({
            'scad_code': scad_code,
            'call_number': len(calls) + 1,
            'hash': hash(scad_code)
        })
        return f"stl_data_call_{len(calls)}_{hash(scad_code)}".encode()
    
    return calls, mock_render


# Auto-use fixtures for all tests
@pytest.fixture(autouse=True)
def auto_mock_openscad(mock_openscad_executable):
    """Automatically mock OpenSCAD for all tests"""
    pass


@pytest.fixture
def mock_wasm_renderer():
    """Mock WASM renderer for testing"""
    from unittest.mock import MagicMock
    
    class MockWASMRenderer:
        def __init__(self):
            self.render_count = 0
            self.is_available = True
            
        def render_scad_to_stl(self, scad_code):
            self.render_count += 1
            # Return different data for different SCAD codes based on priority matching
            code_lower = scad_code.lower()
            
            # Priority-based matching (most specific first)
            if "for(" in code_lower and "translate" in code_lower:
                return b"wasm_stress_test_stl_data"
            elif "difference" in code_lower and "union" in code_lower:
                return b"wasm_complex_stl_data"
            elif "sphere" in code_lower:
                return b"wasm_sphere_stl_data"
            elif "cylinder" in code_lower:
                return b"wasm_cylinder_stl_data"
            elif "cube" in code_lower:
                return b"wasm_cube_stl_data"
            
            return b"wasm_generic_stl_data"
            
        def get_stats(self):
            return {
                'renderer_type': 'wasm',
                'render_count': self.render_count,
                'is_available': self.is_available
            }
            
        def get_version(self):
            return "OpenSCAD WASM 2022.03.20"
            
        @staticmethod
        def is_wasm_supported():
            return True
            
        @staticmethod
        def get_capabilities():
            return {
                'renderer_type': 'wasm',
                'requires_local_install': False,
                'supports_browser': True
            }
    
    return MockWASMRenderer()


@pytest.fixture
def mock_hybrid_renderer():
    """Mock hybrid renderer for testing both WASM and local"""
    from unittest.mock import MagicMock
    
    class MockHybridRenderer:
        def __init__(self, prefer_wasm=True):
            self.prefer_wasm = prefer_wasm
            self.active_renderer = "wasm" if prefer_wasm else "local"
            self.render_count = 0
            
        def render_scad_to_stl(self, scad_code):
            self.render_count += 1
            prefix = "wasm" if self.active_renderer == "wasm" else "local"
            
            if "cube" in scad_code.lower():
                return f"{prefix}_cube_stl_data".encode()
            elif "sphere" in scad_code.lower():
                return f"{prefix}_sphere_stl_data".encode()
            return f"{prefix}_generic_stl_data".encode()
            
        def get_active_renderer_type(self):
            return self.active_renderer
            
        def get_stats(self):
            return {
                'active_renderer': self.active_renderer,
                'prefer_wasm': self.prefer_wasm,
                'render_count': self.render_count
            }
    
    return MockHybridRenderer()


@pytest.fixture
def wasm_test_codes():
    """Provide WASM-specific test codes"""
    return {
        'simple_cube': 'cube([5, 5, 5]);',
        'parametric_sphere': 'sphere(r=radius);',
        'complex_model': '''
            difference() {
                union() {
                    cube([20, 20, 20]);
                    translate([0, 0, 20]) sphere(r=10);
                }
                cylinder(r=5, h=40, center=true);
            }
        ''',
        'wasm_stress_test': '''
            for(i = [0:10]) {
                translate([i*2, 0, 0]) 
                cube([1, 1, 1]);
            }
        '''
    }


# Markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "cache: mark test as cache-related")
    config.addinivalue_line("markers", "regression: mark test as regression test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "wasm: mark test as WASM-related")
    config.addinivalue_line("markers", "performance: mark test as performance-related")