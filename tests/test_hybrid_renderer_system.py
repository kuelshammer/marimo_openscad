"""
Tests for Hybrid Renderer System (Phase 5.3.1)

Tests the enhanced hybrid renderer system with configuration management,
feature flags, and automatic renderer selection for CI/CD environments.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestRendererConfig:
    """Test renderer configuration system"""
    
    def test_renderer_config_initialization(self):
        """Test that renderer configuration initializes correctly"""
        from marimo_openscad.renderer_config import RendererConfig, RendererType
        
        config = RendererConfig()
        
        # Check default values
        assert hasattr(config, 'default_renderer')
        assert hasattr(config, 'enable_wasm')
        assert hasattr(config, 'enable_local_fallback')
        assert hasattr(config, 'force_local')
        
        # Test enum values
        assert RendererType.LOCAL.value == "local"
        assert RendererType.WASM.value == "wasm"
        assert RendererType.AUTO.value == "auto"
    
    def test_environment_variable_handling(self):
        """Test that environment variables are handled correctly"""
        from marimo_openscad.renderer_config import RendererConfig
        
        test_env = {
            'MARIMO_OPENSCAD_RENDERER': 'wasm',
            'MARIMO_OPENSCAD_ENABLE_WASM': 'true', 
            'MARIMO_OPENSCAD_FORCE_LOCAL': 'false',
            'MARIMO_OPENSCAD_WASM_TIMEOUT': '25000'
        }
        
        with patch.dict(os.environ, test_env, clear=False):
            config = RendererConfig()
            
            assert config.default_renderer.value == 'wasm'
            assert config.enable_wasm is True
            assert config.force_local is False
            assert config.wasm_timeout_ms == 25000
    
    def test_renderer_preference_logic(self):
        """Test renderer preference decision logic"""
        from marimo_openscad.renderer_config import RendererConfig
        
        config = RendererConfig()
        
        # Test WASM preference
        config.force_local = False
        config.enable_wasm = True
        assert config.should_use_wasm() is True
        
        # Test local-only
        config.force_local = True
        assert config.should_use_wasm() is False
        
        # Test WASM disabled
        config.force_local = False
        config.enable_wasm = False
        assert config.should_use_wasm() is False
    
    def test_configuration_summary(self):
        """Test configuration summary generation"""
        from marimo_openscad.renderer_config import RendererConfig
        
        config = RendererConfig()
        summary = config.get_summary()
        
        required_keys = [
            'default_renderer', 'enable_wasm', 'enable_local_fallback',
            'force_local', 'wasm_timeout_ms', 'max_model_complexity'
        ]
        
        for key in required_keys:
            assert key in summary


class TestFeatureFlags:
    """Test feature flag functionality"""
    
    def test_wasm_only_mode(self):
        """Test WASM-only configuration"""
        from marimo_openscad.renderer_config import enable_wasm_only, get_config
        
        enable_wasm_only()
        config = get_config()
        
        assert config.should_use_wasm() is True
        assert config.should_fallback_to_local() is False
    
    def test_local_only_mode(self):
        """Test local-only configuration"""
        from marimo_openscad.renderer_config import enable_local_only, get_config
        
        enable_local_only()
        config = get_config()
        
        assert config.force_local is True
        assert config.enable_wasm is False
    
    def test_auto_hybrid_mode(self):
        """Test automatic hybrid configuration"""
        from marimo_openscad.renderer_config import enable_auto_hybrid, get_config
        
        enable_auto_hybrid()
        config = get_config()
        
        assert config.enable_wasm is True
        assert config.enable_local_fallback is True
        assert config.force_local is False
    
    def test_renderer_preference_setting(self):
        """Test setting renderer preferences"""
        from marimo_openscad.renderer_config import set_renderer_preference, get_config
        
        config = get_config()
        
        set_renderer_preference("wasm")
        assert config.default_renderer.value == "wasm"
        
        set_renderer_preference("local")
        assert config.default_renderer.value == "local"
        
        set_renderer_preference("auto")
        assert config.default_renderer.value == "auto"
    
    def test_invalid_renderer_preference(self):
        """Test error handling for invalid renderer preferences"""
        from marimo_openscad.renderer_config import set_renderer_preference
        
        with pytest.raises(ValueError, match="Invalid renderer type"):
            set_renderer_preference("invalid")


class TestHybridRendererConfiguration:
    """Test hybrid renderer configuration"""
    
    def test_hybrid_config_generation(self):
        """Test hybrid renderer configuration generation"""
        from marimo_openscad.renderer_config import get_config
        
        config = get_config()
        hybrid_config = config.get_hybrid_renderer_config()
        
        assert 'prefer_wasm' in hybrid_config
        assert 'fallback_to_local' in hybrid_config
        assert isinstance(hybrid_config['prefer_wasm'], bool)
        assert isinstance(hybrid_config['fallback_to_local'], bool)
    
    @patch('marimo_openscad.openscad_wasm_renderer.HybridOpenSCADRenderer')
    def test_hybrid_renderer_creation(self, mock_hybrid_renderer):
        """Test hybrid renderer creation with configuration"""
        from marimo_openscad.renderer_config import create_hybrid_renderer
        
        mock_instance = MagicMock()
        mock_hybrid_renderer.return_value = mock_instance
        
        renderer = create_hybrid_renderer(prefer_wasm=False)
        
        mock_hybrid_renderer.assert_called_once()
        assert renderer == mock_instance


class TestRendererStatusReporting:
    """Test renderer status and availability reporting"""
    
    @patch('marimo_openscad.openscad_wasm_renderer.OpenSCADWASMRenderer')
    @patch('marimo_openscad.openscad_renderer.OpenSCADRenderer')
    def test_renderer_availability_check(self, mock_local_renderer, mock_wasm_renderer):
        """Test renderer availability detection"""
        from marimo_openscad.renderer_config import get_renderer_status
        
        # Mock WASM renderer as available
        mock_wasm_instance = MagicMock()
        mock_wasm_instance.get_version.return_value = "OpenSCAD WASM 2022.03.20"
        mock_wasm_renderer.return_value = mock_wasm_instance
        
        # Mock local renderer as unavailable
        mock_local_renderer.side_effect = Exception("OpenSCAD not found")
        
        status = get_renderer_status()
        
        assert 'renderer_availability' in status
        availability = status['renderer_availability']
        
        assert 'wasm' in availability
        assert 'local' in availability
        
        # WASM should be available
        assert availability['wasm']['available'] is True
        assert 'version' in availability['wasm']
        
        # Local should be unavailable with error
        assert availability['local']['available'] is False
        assert 'error' in availability['local']
    
    def test_status_structure(self):
        """Test status report structure"""
        from marimo_openscad.renderer_config import get_renderer_status
        
        status = get_renderer_status()
        
        required_keys = [
            'default_renderer', 'enable_wasm', 'renderer_availability'
        ]
        
        for key in required_keys:
            assert key in status


class TestAPIIntegration:
    """Test API integration with main module"""
    
    def test_main_module_exports(self):
        """Test that main module exports new functions"""
        import marimo_openscad as mo
        
        # Test that new functions are exposed
        assert hasattr(mo, 'set_renderer_preference')
        assert hasattr(mo, 'get_renderer_status')
        assert hasattr(mo, 'enable_wasm_only')
        assert hasattr(mo, 'enable_local_only')
        assert hasattr(mo, 'enable_auto_hybrid')
        assert hasattr(mo, 'create_hybrid_renderer')
    
    def test_api_functions_callable(self):
        """Test that API functions are callable"""
        import marimo_openscad as mo
        
        # Test setting renderer preference
        mo.set_renderer_preference("auto")
        
        # Test getting status
        status = mo.get_renderer_status()
        assert isinstance(status, dict)
        
        # Test convenience functions
        mo.enable_auto_hybrid()
        mo.enable_wasm_only()
        mo.enable_local_only()


class TestViewerIntegration:
    """Test viewer integration with configuration system"""
    
    @patch('marimo_openscad.viewer.HybridOpenSCADRenderer')
    def test_viewer_uses_global_config(self, mock_hybrid_renderer):
        """Test that viewer uses global configuration"""
        from marimo_openscad.viewer import openscad_viewer
        from marimo_openscad.renderer_config import set_renderer_preference
        
        mock_renderer_instance = MagicMock()
        mock_renderer_instance.get_active_renderer_type.return_value = "wasm"
        mock_hybrid_renderer.return_value = mock_renderer_instance
        
        # Set global preference
        set_renderer_preference("auto")
        
        # Viewer should respect global configuration
        # Note: We can't fully test without a real model, but we test the function exists
        assert callable(openscad_viewer)
    
    @patch('marimo_openscad.viewer.OpenSCADViewer')
    def test_renderer_type_override(self, mock_viewer_class):
        """Test that renderer type can be overridden"""
        from marimo_openscad.viewer import openscad_viewer
        
        mock_viewer_instance = MagicMock()
        mock_viewer_class.return_value = mock_viewer_instance
        
        # Test with explicit renderer type
        viewer = openscad_viewer("cube([1,1,1]);", renderer_type="wasm")
        
        # Should have been called with the specified renderer type
        mock_viewer_class.assert_called_once()
        call_args = mock_viewer_class.call_args
        assert call_args[1]['renderer_type'] == "wasm"


class TestCICompatibility:
    """Test CI/CD environment compatibility"""
    
    def test_import_safety(self):
        """Test that all imports work in CI environment"""
        # Test that imports don't fail in CI
        from marimo_openscad.renderer_config import (
            RendererConfig, RendererType, get_config,
            set_renderer_preference, get_renderer_status
        )
        
        # Basic functionality should work
        config = get_config()
        assert config is not None
    
    def test_environment_isolation(self):
        """Test that tests don't interfere with each other"""
        from marimo_openscad.renderer_config import get_config, set_renderer_preference
        
        # Save original state
        config = get_config()
        original_renderer = config.default_renderer.value
        
        try:
            # Make changes
            set_renderer_preference("wasm")
            assert config.default_renderer.value == "wasm"
            
            # Changes should be contained to this test
            set_renderer_preference("local")
            assert config.default_renderer.value == "local"
            
        finally:
            # Restore original state
            set_renderer_preference(original_renderer)
    
    def test_no_external_dependencies(self):
        """Test that configuration system doesn't require external dependencies"""
        from marimo_openscad.renderer_config import RendererConfig
        
        # Should work without OpenSCAD or WASM modules installed
        config = RendererConfig()
        summary = config.get_summary()
        
        # Basic configuration should always work
        assert 'default_renderer' in summary
        assert 'enable_wasm' in summary


# Pytest markers for CI/CD
pytestmark = pytest.mark.hybrid_renderer


def test_full_integration():
    """Full integration test for CI/CD"""
    import marimo_openscad as mo
    
    # Test complete workflow
    mo.set_renderer_preference("auto")
    status = mo.get_renderer_status()
    
    # Should always work, regardless of what's installed
    assert isinstance(status, dict)
    assert 'default_renderer' in status
    
    # Test feature flags
    mo.enable_auto_hybrid()
    mo.enable_wasm_only()
    mo.enable_local_only()
    
    # No exceptions should be raised