"""
CI-Compatible Tests for Hybrid Renderer System

These tests are designed to work correctly in GitHub Actions CI environment
where environment variables are set via matrix configurations.
"""

import os
import pytest
from unittest.mock import patch


class TestCICompatibleRendererConfig:
    """Test renderer configuration in CI environment"""
    
    def test_renderer_config_respects_ci_environment(self):
        """Test that renderer configuration correctly reads CI environment"""
        from marimo_openscad.renderer_config import RendererConfig
        
        # Test that config respects current environment (set by CI matrix)
        config = RendererConfig()
        
        # These should match whatever the CI matrix set
        assert hasattr(config, 'default_renderer')
        assert hasattr(config, 'enable_wasm') 
        assert hasattr(config, 'force_local')
        assert hasattr(config, 'enable_local_fallback')
        
        # Verify configuration is consistent
        summary = config.get_summary()
        assert isinstance(summary, dict)
        assert 'default_renderer' in summary
        assert summary['default_renderer'] in ['local', 'wasm', 'auto']
    
    def test_ci_environment_variables_are_read(self):
        """Test that CI environment variables are properly loaded"""
        from marimo_openscad.renderer_config import RendererConfig
        
        config = RendererConfig()
        
        # Check if CI environment variables are being read
        ci_renderer = os.getenv('MARIMO_OPENSCAD_RENDERER')
        ci_enable_wasm = os.getenv('MARIMO_OPENSCAD_ENABLE_WASM')
        ci_force_local = os.getenv('MARIMO_OPENSCAD_FORCE_LOCAL')
        
        if ci_renderer:
            assert config.default_renderer.value == ci_renderer.lower()
        
        if ci_enable_wasm:
            expected_wasm = ci_enable_wasm.lower() in ('true', '1', 'yes', 'on')
            assert config.enable_wasm == expected_wasm
        
        if ci_force_local:
            expected_force = ci_force_local.lower() in ('true', '1', 'yes', 'on')
            assert config.force_local == expected_force
    
    def test_renderer_logic_with_current_config(self):
        """Test renderer selection logic with current CI configuration"""
        from marimo_openscad.renderer_config import RendererConfig
        
        config = RendererConfig()
        
        # Test that logic methods work regardless of current config
        wasm_result = config.should_use_wasm()
        fallback_result = config.should_fallback_to_local()
        preference = config.get_renderer_preference()
        
        # Results should be boolean/string as expected
        assert isinstance(wasm_result, bool)
        assert isinstance(fallback_result, bool)
        assert isinstance(preference, str)
        assert preference in ['local', 'wasm', 'auto']
        
        # Logic should be consistent
        if config.force_local:
            assert wasm_result is False
            assert preference == 'local'
        
        if not config.enable_wasm:
            assert wasm_result is False


class TestCICompatibleFeatureFlags:
    """Test feature flags in CI environment"""
    
    def test_feature_flag_functions_exist_and_work(self):
        """Test that all feature flag functions exist and are callable"""
        from marimo_openscad.renderer_config import (
            enable_wasm_only, enable_local_only, enable_auto_hybrid,
            set_renderer_preference, get_config
        )
        
        # Test that functions exist and are callable
        assert callable(enable_wasm_only)
        assert callable(enable_local_only)
        assert callable(enable_auto_hybrid)
        assert callable(set_renderer_preference)
        
        # Test that they can be called without errors
        config = get_config()
        original_renderer = config.default_renderer.value
        
        try:
            # These should not raise exceptions
            enable_auto_hybrid()
            enable_wasm_only()
            enable_local_only()
            
            # Test preference setting
            for renderer_type in ['auto', 'wasm', 'local']:
                set_renderer_preference(renderer_type)
                assert config.default_renderer.value == renderer_type
                
        finally:
            # Restore original state
            set_renderer_preference(original_renderer)
    
    def test_configuration_changes_persist(self):
        """Test that configuration changes work in CI environment"""
        from marimo_openscad.renderer_config import get_config, set_renderer_preference
        
        config = get_config()
        original_renderer = config.default_renderer.value
        
        try:
            # Test changing configuration
            test_types = ['auto', 'wasm', 'local']
            for renderer_type in test_types:
                set_renderer_preference(renderer_type)
                
                # Verify change took effect
                current_config = get_config()
                assert current_config.default_renderer.value == renderer_type
                
                # Verify summary reflects change
                summary = current_config.get_summary()
                assert summary['default_renderer'] == renderer_type
                
        finally:
            # Restore original state
            set_renderer_preference(original_renderer)


class TestCICompatibleAPIIntegration:
    """Test API integration in CI environment"""
    
    def test_main_module_api_works_in_ci(self):
        """Test that main module API works in CI environment"""
        import marimo_openscad as mo
        
        # Test that all expected functions are available
        api_functions = [
            'set_renderer_preference', 'get_renderer_status',
            'enable_wasm_only', 'enable_local_only', 'enable_auto_hybrid',
            'create_hybrid_renderer', 'openscad_viewer'
        ]
        
        for func_name in api_functions:
            assert hasattr(mo, func_name), f"Missing API function: {func_name}"
            assert callable(getattr(mo, func_name)), f"API function not callable: {func_name}"
    
    def test_renderer_status_in_ci(self):
        """Test renderer status reporting in CI environment"""
        import marimo_openscad as mo
        
        # Test getting status
        status = mo.get_renderer_status()
        
        # Verify status structure
        assert isinstance(status, dict)
        assert 'default_renderer' in status
        assert 'enable_wasm' in status
        assert 'renderer_availability' in status
        
        # Verify availability structure
        availability = status['renderer_availability']
        assert 'wasm' in availability
        assert 'local' in availability
        
        # Each renderer should have availability info
        for renderer_type in ['wasm', 'local']:
            renderer_info = availability[renderer_type]
            assert 'available' in renderer_info
            assert isinstance(renderer_info['available'], bool)
    
    def test_viewer_creation_in_ci(self):
        """Test viewer creation in CI environment"""
        import marimo_openscad as mo
        
        # Test that viewer function exists and can be called
        assert callable(mo.openscad_viewer)
        
        # Test with simple model (without actual rendering in CI)
        try:
            # This should not raise import errors
            viewer = mo.openscad_viewer("cube([1,1,1]);")
            assert viewer is not None
            
            # Test that viewer has expected attributes
            assert hasattr(viewer, 'renderer_type')
            assert hasattr(viewer, 'get_renderer_info')
            
        except Exception as e:
            # In CI, actual rendering might fail, but basic instantiation should work
            error_msg = str(e).lower()
            # Only allow specific CI-related errors
            allowed_errors = ['openscad', 'not found', 'unavailable', 'installation']
            assert any(allowed in error_msg for allowed in allowed_errors), f"Unexpected error: {e}"


class TestCICompatibleErrorHandling:
    """Test error handling in CI environment"""
    
    def test_invalid_renderer_preference_handling(self):
        """Test that invalid renderer preferences are handled correctly"""
        from marimo_openscad.renderer_config import set_renderer_preference
        
        # Test that invalid renderer types raise appropriate errors
        with pytest.raises(ValueError, match="Invalid renderer type"):
            set_renderer_preference("invalid_renderer")
        
        # Test other invalid values
        invalid_types = ["", "none", "unknown", "test"]
        for invalid_type in invalid_types:
            with pytest.raises(ValueError):
                set_renderer_preference(invalid_type)
    
    def test_configuration_robustness(self):
        """Test that configuration system is robust in CI"""
        from marimo_openscad.renderer_config import RendererConfig, get_config
        
        # Test repeated configuration access
        configs = []
        for i in range(10):
            config = get_config()
            configs.append(config.get_summary())
        
        # All configs should be consistent
        first_config = configs[0]
        for config in configs[1:]:
            assert config['default_renderer'] == first_config['default_renderer']
            assert config['enable_wasm'] == first_config['enable_wasm']
            assert config['force_local'] == first_config['force_local']
    
    def test_environment_variable_edge_cases(self):
        """Test edge cases in environment variable handling"""
        from marimo_openscad.renderer_config import RendererConfig
        
        # Test with various boolean value formats
        boolean_tests = [
            ('true', True), ('false', False), ('1', True), ('0', False),
            ('yes', True), ('no', False), ('on', True), ('off', False),
            ('TRUE', True), ('FALSE', False)
        ]
        
        for str_val, expected_bool in boolean_tests:
            test_env = {'MARIMO_OPENSCAD_ENABLE_WASM': str_val}
            with patch.dict(os.environ, test_env, clear=False):
                config = RendererConfig()
                assert config.enable_wasm == expected_bool, f"Failed for {str_val} -> {expected_bool}"


# Mark all tests as CI compatible
pytestmark = pytest.mark.ci_compatibility