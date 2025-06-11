"""
CI/CD Environment Compatibility Tests

Tests specifically designed for GitHub Actions CI environment
to ensure hybrid renderer system works correctly in automated environments.
"""

import os
import pytest
import sys
from unittest.mock import patch, MagicMock


class TestCIEnvironment:
    """Test CI/CD environment compatibility"""
    
    def test_github_actions_environment_detection(self):
        """Test that we correctly detect GitHub Actions environment"""
        # GitHub Actions sets GITHUB_ACTIONS=true
        github_actions = os.getenv('GITHUB_ACTIONS', 'false').lower() == 'true'
        
        if github_actions:
            # In GitHub Actions environment
            assert 'CI' in os.environ or 'GITHUB_ACTIONS' in os.environ
            print(f"✅ Running in GitHub Actions: {os.getenv('GITHUB_WORKFLOW', 'unknown')}")
        else:
            # Local environment
            print("✅ Running in local development environment")
    
    def test_environment_variable_isolation(self):
        """Test that environment variables don't interfere between tests"""
        from marimo_openscad.renderer_config import RendererConfig
        
        # Test with different environment configurations
        test_configs = [
            {'MARIMO_OPENSCAD_RENDERER': 'wasm'},
            {'MARIMO_OPENSCAD_RENDERER': 'local'},
            {'MARIMO_OPENSCAD_RENDERER': 'auto'},
        ]
        
        for test_env in test_configs:
            with patch.dict(os.environ, test_env, clear=False):
                config = RendererConfig()
                assert config.default_renderer.value == test_env['MARIMO_OPENSCAD_RENDERER']
    
    def test_no_external_dependencies_in_ci(self):
        """Test that core functionality works without external tools"""
        from marimo_openscad.renderer_config import RendererConfig, get_config
        from marimo_openscad import set_renderer_preference, get_renderer_status
        
        # Basic configuration should work without OpenSCAD or WASM
        config = RendererConfig()
        assert config.get_summary()
        
        # Global functions should work
        set_renderer_preference("auto")
        status = get_renderer_status()
        assert isinstance(status, dict)
        assert 'default_renderer' in status
    
    def test_import_safety_in_ci(self):
        """Test that all imports work in restricted CI environment"""
        try:
            # Core imports
            import marimo_openscad as mo
            from marimo_openscad.renderer_config import (
                RendererConfig, RendererType, get_config,
                set_renderer_preference, get_renderer_status,
                enable_wasm_only, enable_local_only, enable_auto_hybrid
            )
            from marimo_openscad.viewer import openscad_viewer, OpenSCADViewer
            from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer, HybridOpenSCADRenderer
            
            # All imports should succeed
            assert True
            
        except ImportError as e:
            pytest.fail(f"Import failed in CI environment: {e}")
    
    def test_ci_friendly_renderer_instantiation(self):
        """Test renderer instantiation without actual OpenSCAD/WASM"""
        from marimo_openscad.renderer_config import get_config, create_hybrid_renderer
        
        config = get_config()
        
        # Test that configuration works
        assert config.should_use_wasm() is not None
        assert config.should_fallback_to_local() is not None
        
        # Test renderer creation (may fail gracefully in CI)
        try:
            renderer = create_hybrid_renderer()
            # If it succeeds, that's great
            assert renderer is not None
        except Exception as e:
            # If it fails, that's expected in CI without OpenSCAD/WASM
            assert "OpenSCAD" in str(e) or "WASM" in str(e) or "not found" in str(e).lower()
    
    def test_mock_renderer_behavior_in_ci(self):
        """Test renderer behavior with mocked dependencies"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        
        # Test WASM renderer instantiation
        wasm_renderer = OpenSCADWASMRenderer()
        assert wasm_renderer.is_available is True
        assert wasm_renderer.get_version() == "OpenSCAD WASM 2022.03.20"
        
        # Test capabilities reporting
        capabilities = OpenSCADWASMRenderer.get_capabilities()
        assert capabilities['renderer_type'] == 'wasm'
        assert capabilities['requires_local_install'] is False
    
    @pytest.mark.skipif(
        sys.platform == "win32" and sys.version_info < (3, 9),
        reason="Windows Python 3.8 has compatibility issues"
    )
    def test_python_version_compatibility(self):
        """Test compatibility across Python versions"""
        from marimo_openscad.renderer_config import RendererConfig
        
        # Test that typing and enum work correctly
        config = RendererConfig()
        
        # Test enum values
        from marimo_openscad.renderer_config import RendererType
        assert RendererType.LOCAL.value == "local"
        assert RendererType.WASM.value == "wasm" 
        assert RendererType.AUTO.value == "auto"
        
        # Test typing annotations work
        renderer_type = config.get_renderer_preference()
        assert isinstance(renderer_type, str)
        assert renderer_type in ["local", "wasm", "auto"]
    
    def test_ci_memory_constraints(self):
        """Test that code works within CI memory constraints"""
        from marimo_openscad.renderer_config import get_config
        import gc
        
        # Test repeated configuration access doesn't leak memory
        configs = []
        for i in range(100):
            config = get_config()
            configs.append(config.get_summary())
        
        # Force garbage collection
        gc.collect()
        
        # Test should complete without memory issues
        assert len(configs) == 100
        assert all('default_renderer' in config for config in configs)
    
    def test_concurrent_configuration_access(self):
        """Test thread-safe configuration access"""
        from marimo_openscad.renderer_config import get_config, set_renderer_preference
        import threading
        import time
        
        results = []
        errors = []
        
        def test_config_access(thread_id):
            try:
                for i in range(10):
                    # Alternate between different configurations
                    renderer_type = ["auto", "wasm", "local"][i % 3]
                    set_renderer_preference(renderer_type)
                    
                    config = get_config()
                    summary = config.get_summary()
                    results.append((thread_id, summary['default_renderer']))
                    
                    time.sleep(0.001)  # Small delay to encourage race conditions
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Run multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=test_config_access, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Thread errors: {errors}"
        assert len(results) == 50  # 5 threads * 10 iterations
    
    def test_error_handling_robustness(self):
        """Test robust error handling in CI environment"""
        from marimo_openscad.renderer_config import set_renderer_preference
        
        # Test invalid renderer types are handled gracefully
        with pytest.raises(ValueError, match="Invalid renderer type"):
            set_renderer_preference("invalid_renderer")
        
        # Test that error doesn't break the configuration system
        from marimo_openscad.renderer_config import get_config
        config = get_config()
        assert config.get_summary()['default_renderer'] in ["local", "wasm", "auto"]


class TestCIPerformance:
    """Test performance characteristics in CI environment"""
    
    def test_configuration_loading_performance(self):
        """Test that configuration loading is fast enough for CI"""
        import time
        from marimo_openscad.renderer_config import RendererConfig
        
        start_time = time.time()
        for i in range(50):
            config = RendererConfig()
            summary = config.get_summary()
        end_time = time.time()
        
        elapsed = end_time - start_time
        # Should complete 50 configurations in under 1 second
        assert elapsed < 1.0, f"Configuration loading too slow: {elapsed:.3f}s"
    
    def test_api_response_time(self):
        """Test API response times are reasonable"""
        import time
        from marimo_openscad import get_renderer_status, set_renderer_preference
        
        start_time = time.time()
        for renderer_type in ["auto", "wasm", "local"] * 10:
            set_renderer_preference(renderer_type)
            status = get_renderer_status()
            assert isinstance(status, dict)
        end_time = time.time()
        
        elapsed = end_time - start_time
        # 30 API calls should complete in under 2 seconds
        assert elapsed < 2.0, f"API calls too slow: {elapsed:.3f}s"


@pytest.mark.ci_compatibility
class TestGitHubActionsSpecific:
    """Tests specific to GitHub Actions environment"""
    
    def test_github_actions_matrix_configurations(self):
        """Test that matrix configurations work correctly"""
        from marimo_openscad.renderer_config import RendererConfig
        
        # Test different matrix configurations that might be set via environment
        matrix_configs = [
            {"MARIMO_OPENSCAD_RENDERER": "wasm", "MARIMO_OPENSCAD_ENABLE_WASM": "true"},
            {"MARIMO_OPENSCAD_RENDERER": "local", "MARIMO_OPENSCAD_FORCE_LOCAL": "true"},
            {"MARIMO_OPENSCAD_RENDERER": "auto", "MARIMO_OPENSCAD_ENABLE_LOCAL_FALLBACK": "true"},
        ]
        
        for matrix_env in matrix_configs:
            with patch.dict(os.environ, matrix_env, clear=False):
                # Create fresh config instance to avoid global state interference
                config = RendererConfig()
                summary = config.get_summary()
                
                # Verify configuration matches matrix
                if matrix_env.get("MARIMO_OPENSCAD_RENDERER"):
                    assert summary["default_renderer"] == matrix_env["MARIMO_OPENSCAD_RENDERER"]
    
    def test_artifact_generation_compatibility(self):
        """Test that test artifacts can be generated in GitHub Actions"""
        import json
        from marimo_openscad.renderer_config import get_renderer_status
        
        # Test generating JSON artifacts (like test reports)
        status = get_renderer_status()
        
        # Should be serializable to JSON (for GitHub Actions artifacts)
        try:
            json_data = json.dumps(status, indent=2)
            assert len(json_data) > 0
            
            # Verify the JSON can be parsed back
            parsed_data = json.loads(json_data)
            assert isinstance(parsed_data, dict)
            assert 'default_renderer' in parsed_data
            assert 'renderer_availability' in parsed_data
            
            # Test that all values are JSON-serializable types
            def check_json_serializable(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        check_json_serializable(value, f"{path}.{key}" if path else key)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        check_json_serializable(item, f"{path}[{i}]")
                elif not isinstance(obj, (str, int, float, bool, type(None))):
                    raise TypeError(f"Non-JSON-serializable object at {path}: {type(obj)}")
            
            check_json_serializable(parsed_data)
            
        except (TypeError, ValueError) as e:
            pytest.fail(f"Status report not JSON serializable: {e}")
    
    def test_exit_code_handling(self):
        """Test proper exit codes for CI/CD"""
        # Import errors should not cause silent failures
        try:
            import marimo_openscad
            exit_code = 0
        except ImportError:
            exit_code = 1
        
        assert exit_code == 0, "Import should succeed in proper CI environment"


# Mark all tests in this module for CI compatibility
pytestmark = pytest.mark.ci_compatibility