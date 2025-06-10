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
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
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


# Markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "cache: mark test as cache-related")
    config.addinivalue_line("markers", "regression: mark test as regression test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")