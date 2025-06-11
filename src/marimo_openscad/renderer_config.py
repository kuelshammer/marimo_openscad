"""
🎛️ Renderer Configuration and Feature Flags

Centralized configuration system for OpenSCAD renderer selection.
Allows users to control renderer behavior through environment variables and runtime settings.
"""

import os
import logging
from typing import Literal, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)

class RendererType(Enum):
    """Available renderer types"""
    LOCAL = "local"
    WASM = "wasm"
    AUTO = "auto"

class RendererConfig:
    """
    Centralized renderer configuration with feature flags
    """
    
    def __init__(self):
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables and defaults"""
        
        # Primary renderer preference
        self.default_renderer = self._get_env_renderer(
            "MARIMO_OPENSCAD_RENDERER", 
            RendererType.AUTO
        )
        
        # Feature flags
        self.enable_wasm = self._get_env_bool("MARIMO_OPENSCAD_ENABLE_WASM", True)
        self.enable_local_fallback = self._get_env_bool("MARIMO_OPENSCAD_ENABLE_LOCAL_FALLBACK", True)
        self.force_local = self._get_env_bool("MARIMO_OPENSCAD_FORCE_LOCAL", False)
        
        # Performance settings
        self.wasm_timeout_ms = self._get_env_int("MARIMO_OPENSCAD_WASM_TIMEOUT", 30000)
        self.max_model_complexity = self._get_env_int("MARIMO_OPENSCAD_MAX_COMPLEXITY", 10000)
        
        # Development flags
        self.debug_renderer = self._get_env_bool("MARIMO_OPENSCAD_DEBUG_RENDERER", False)
        self.log_performance = self._get_env_bool("MARIMO_OPENSCAD_LOG_PERFORMANCE", False)
        
        logger.info(f"Renderer config loaded: {self.get_summary()}")
    
    def _get_env_renderer(self, key: str, default: RendererType) -> RendererType:
        """Get renderer type from environment variable"""
        value = os.getenv(key, default.value).lower()
        try:
            return RendererType(value)
        except ValueError:
            logger.warning(f"Invalid renderer type '{value}' for {key}, using {default.value}")
            return default
    
    def _get_env_bool(self, key: str, default: bool) -> bool:
        """Get boolean from environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _get_env_int(self, key: str, default: int) -> int:
        """Get integer from environment variable"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid integer for {key}, using default {default}")
            return default
    
    def should_use_wasm(self) -> bool:
        """Determine if WASM renderer should be used"""
        if self.force_local:
            return False
        if not self.enable_wasm:
            return False
        return self.default_renderer in (RendererType.WASM, RendererType.AUTO)
    
    def should_fallback_to_local(self) -> bool:
        """Determine if local fallback should be enabled"""
        if self.force_local:
            return True
        return self.enable_local_fallback
    
    def get_renderer_preference(self) -> str:
        """Get string representation of renderer preference"""
        if self.force_local:
            return "local"
        return self.default_renderer.value
    
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            'default_renderer': self.default_renderer.value,
            'enable_wasm': self.enable_wasm,
            'enable_local_fallback': self.enable_local_fallback,
            'force_local': self.force_local,
            'wasm_timeout_ms': self.wasm_timeout_ms,
            'max_model_complexity': self.max_model_complexity,
            'debug_renderer': self.debug_renderer,
            'log_performance': self.log_performance
        }
    
    def set_renderer_type(self, renderer_type: Literal["local", "wasm", "auto"]):
        """Programmatically set renderer type"""
        try:
            self.default_renderer = RendererType(renderer_type)
            logger.info(f"Renderer type set to: {renderer_type}")
        except ValueError:
            raise ValueError(f"Invalid renderer type: {renderer_type}")
    
    def enable_debug_mode(self):
        """Enable debug mode with detailed logging"""
        self.debug_renderer = True
        self.log_performance = True
        logging.getLogger('marimo_openscad').setLevel(logging.DEBUG)
        logger.info("Debug mode enabled")
    
    def get_hybrid_renderer_config(self) -> Dict[str, Any]:
        """Get configuration for HybridOpenSCADRenderer"""
        return {
            'prefer_wasm': self.should_use_wasm(),
            'fallback_to_local': self.should_fallback_to_local()
            # Note: wasm_options are handled during WASM renderer initialization
        }

# Global configuration instance
config = RendererConfig()

def get_config() -> RendererConfig:
    """Get the global renderer configuration"""
    return config

def create_hybrid_renderer(**kwargs):
    """
    Create a hybrid renderer with current configuration
    
    Example:
        # Use environment variables
        renderer = create_hybrid_renderer()
        
        # Override specific settings  
        renderer = create_hybrid_renderer(prefer_wasm=False)
    """
    from .openscad_wasm_renderer import HybridOpenSCADRenderer
    
    hybrid_config = config.get_hybrid_renderer_config()
    hybrid_config.update(kwargs)  # Allow overrides
    
    return HybridOpenSCADRenderer(**hybrid_config)

def set_renderer_preference(renderer_type: Literal["local", "wasm", "auto"]):
    """
    Set global renderer preference
    
    Args:
        renderer_type: "local", "wasm", or "auto"
    
    Example:
        import marimo_openscad as mo
        
        # Force WASM rendering
        mo.set_renderer_preference("wasm")
        
        # Force local rendering (requires OpenSCAD installation)
        mo.set_renderer_preference("local")
        
        # Automatic selection (default)
        mo.set_renderer_preference("auto")
    """
    config.set_renderer_type(renderer_type)

def get_renderer_status() -> Dict[str, Any]:
    """
    Get current renderer status and configuration
    
    Returns:
        Dict with current configuration and available renderers
    """
    from .openscad_wasm_renderer import OpenSCADWASMRenderer
    from .openscad_renderer import OpenSCADRenderer
    
    status = config.get_summary()
    
    # Check renderer availability
    status['renderer_availability'] = {}
    
    try:
        wasm_renderer = OpenSCADWASMRenderer()
        status['renderer_availability']['wasm'] = {
            'available': True,
            'version': wasm_renderer.get_version()
        }
    except Exception as e:
        status['renderer_availability']['wasm'] = {
            'available': False,
            'error': str(e)
        }
    
    try:
        local_renderer = OpenSCADRenderer()
        status['renderer_availability']['local'] = {
            'available': True,
            'version': local_renderer.get_version()
        }
    except Exception as e:
        status['renderer_availability']['local'] = {
            'available': False,
            'error': str(e)
        }
    
    return status

# Convenience functions for common configurations
def enable_wasm_only():
    """Enable WASM-only rendering (no local fallback)"""
    config.default_renderer = RendererType.WASM
    config.enable_local_fallback = False
    config.force_local = False
    logger.info("WASM-only rendering enabled")

def enable_local_only():
    """Enable local-only rendering (no WASM)"""
    config.force_local = True
    config.enable_wasm = False
    logger.info("Local-only rendering enabled")

def enable_auto_hybrid():
    """Enable automatic hybrid rendering (default)"""
    config.default_renderer = RendererType.AUTO
    config.enable_wasm = True
    config.enable_local_fallback = True
    config.force_local = False
    logger.info("Automatic hybrid rendering enabled")