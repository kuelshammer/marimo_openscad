"""
OpenSCAD WASM Renderer

Python interface for the OpenSCAD WebAssembly renderer.
Provides the same interface as the local OpenSCAD renderer but uses WASM.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from .openscad_renderer import OpenSCADRenderer, OpenSCADError
from .wasm_asset_server import get_wasm_asset_server

logger = logging.getLogger(__name__)


class OpenSCADWASMRenderer:
    """
    WebAssembly-based OpenSCAD renderer.
    
    This renderer uses OpenSCAD WASM module in the browser instead of
    requiring a local OpenSCAD installation.
    """
    
    def __init__(self, wasm_options: Optional[Dict[str, Any]] = None):
        """
        Initialize WASM renderer
        
        Args:
            wasm_options: Configuration options for WASM module
        """
        self.wasm_options = wasm_options or {}
        self.render_count = 0
        self.wasm_path = self._get_wasm_path()
        self.wasm_server = get_wasm_asset_server()
        self.is_available = self._check_wasm_availability()
        
        logger.info(f"OpenSCAD WASM Renderer initialized (available: {self.is_available})")
    
    def _get_wasm_path(self) -> Path:
        """Get path to bundled WASM files"""
        package_dir = Path(__file__).parent
        wasm_dir = package_dir / "wasm"
        return wasm_dir
    
    def _check_wasm_availability(self) -> bool:
        """Check if WASM files are available"""
        wasm_file = self.wasm_path / "openscad.wasm"
        js_file = self.wasm_path / "openscad.js"
        return wasm_file.exists() and js_file.exists()
    
    def render_scad_to_stl(self, scad_code: str) -> bytes:
        """
        Render OpenSCAD code to STL format using WASM
        
        Args:
            scad_code: OpenSCAD code as string
            
        Returns:
            STL binary data as bytes
            
        Raises:
            OpenSCADError: If rendering fails
            
        Note:
            The actual rendering happens in JavaScript/WASM.
            This method is called from the Python side but the heavy lifting
            is done by the anywidget frontend.
        """
        if not scad_code or not scad_code.strip():
            raise OpenSCADError("Empty SCAD code provided")
        
        logger.debug(f"WASM render request for {len(scad_code)} character SCAD code")
        
        # The actual WASM rendering will be handled by the JavaScript frontend
        # This method primarily validates input and tracks usage
        self.render_count += 1
        
        # In the WASM implementation, the rendering result will be passed back
        # via the anywidget communication channel
        # For now, we return a placeholder that indicates WASM rendering was requested
        return self._create_wasm_placeholder(scad_code)
    
    def _create_wasm_placeholder(self, scad_code: str) -> bytes:
        """
        Create a placeholder response for WASM rendering
        
        This is used to maintain API compatibility while the actual rendering
        happens asynchronously in the JavaScript frontend.
        """
        # Create a simple marker that indicates this is a WASM render request
        # The actual STL data will be provided by the JavaScript frontend
        placeholder = f"WASM_RENDER_REQUEST:{hash(scad_code)}".encode('utf-8')
        return placeholder
    
    def get_version(self) -> str:
        """Get OpenSCAD WASM version information"""
        return "OpenSCAD WASM 2022.03.20"
    
    def get_wasm_url_base(self, base_url: Optional[str] = None) -> str:
        """
        Get the URL base path for WASM assets
        
        This provides the web-accessible URL for WASM assets that can be
        used by the JavaScript frontend to load WASM modules.
        
        Args:
            base_url: Base URL for asset serving (provided by anywidget)
            
        Returns:
            Web-accessible URL base for WASM assets
        """
        if base_url:
            # Use provided base URL (from anywidget asset serving)
            return base_url.rstrip('/') + '/wasm/'
        else:
            # Default fallback - this should be set by the viewer
            logger.warning("No base URL provided for WASM assets, using fallback")
            return '/wasm/'
    
    def get_wasm_files(self, base_url: Optional[str] = None) -> Dict[str, str]:
        """
        Get URLs for all WASM-related files
        
        Args:
            base_url: Base URL for asset serving (provided by anywidget)
            
        Returns:
            Dictionary mapping filenames to web-accessible URLs
        """
        if base_url:
            # Use WASM asset server to get proper URLs
            return self.wasm_server.get_asset_urls(base_url.rstrip('/') + '/wasm/')
        else:
            # Fallback: return local file paths (for backward compatibility)
            files = {}
            wasm_files = [
                "openscad.wasm",
                "openscad.js", 
                "openscad.d.ts",
                "openscad.fonts.js",
                "openscad.mcad.js"
            ]
            
            for filename in wasm_files:
                file_path = self.wasm_path / filename
                if file_path.exists():
                    files[filename] = str(file_path)
            
            return files
    
    def get_wasm_asset_data(self, filename: str):
        """
        Get WASM asset data for serving
        
        Args:
            filename: Name of the WASM file to serve
            
        Returns:
            Tuple of (file_data, mime_type) or None if file not found
        """
        return self.wasm_server.get_asset_data(filename)
    
    def validate_wasm_assets(self) -> Dict[str, bool]:
        """
        Validate that WASM assets are available
        
        Returns:
            Dictionary mapping filenames to availability status
        """
        return self.wasm_server.validate_assets()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get renderer statistics"""
        return {
            'renderer_type': 'wasm',
            'render_count': self.render_count,
            'is_available': self.is_available,
            'wasm_path': str(self.wasm_path),
            'wasm_files': self.get_wasm_files(),
            'wasm_options': self.wasm_options,
            'capabilities': {
                'supports_manifold': True,
                'supports_fonts': True,
                'supports_mcad': True,
                'max_file_size': 50 * 1024 * 1024,  # 50MB
                'output_formats': ['binstl']
            }
        }
    
    @staticmethod
    def is_wasm_supported() -> bool:
        """
        Check if WASM is supported in the current environment
        
        Note: This check happens on the Python side but the actual
        WASM support detection occurs in the JavaScript frontend.
        """
        # On the Python side, we assume WASM support if we're in a web context
        # The actual check will be done in JavaScript
        return True
    
    @staticmethod
    def get_capabilities() -> Dict[str, Any]:
        """Get WASM renderer capabilities"""
        return {
            'renderer_type': 'wasm',
            'requires_local_install': False,
            'supports_browser': True,
            'supports_offline': True,  # After initial load
            'supports_web_workers': True,
            'max_complexity': 'high',
            'output_formats': ['binstl'],
            'supported_features': [
                'manifold_engine',
                'font_support',
                'mcad_library',
                'real_time_rendering'
            ]
        }


class HybridOpenSCADRenderer:
    """
    Hybrid renderer that can use either local OpenSCAD or WASM
    based on availability and user preference.
    """
    
    def __init__(self, 
                 prefer_wasm: bool = True,
                 fallback_to_local: bool = True,
                 openscad_path: Optional[str] = None):
        """
        Initialize hybrid renderer
        
        Args:
            prefer_wasm: Whether to prefer WASM over local OpenSCAD
            fallback_to_local: Whether to fallback to local if WASM fails
            openscad_path: Path to local OpenSCAD (for fallback)
        """
        self.prefer_wasm = prefer_wasm
        self.fallback_to_local = fallback_to_local
        self.wasm_renderer = None
        self.local_renderer = None
        self.active_renderer = None
        
        # Initialize renderers based on preferences
        self._initialize_renderers(openscad_path)
    
    def _initialize_renderers(self, openscad_path: Optional[str]):
        """Initialize available renderers"""
        
        # Always try to initialize WASM renderer
        try:
            self.wasm_renderer = OpenSCADWASMRenderer()
            logger.info("WASM renderer initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize WASM renderer: {e}")
        
        # Initialize local renderer if fallback is enabled
        if self.fallback_to_local:
            try:
                self.local_renderer = OpenSCADRenderer(openscad_path)
                logger.info("Local renderer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize local renderer: {e}")
        
        # Select active renderer
        self._select_active_renderer()
    
    def _select_active_renderer(self):
        """Select the active renderer based on preferences and availability"""
        
        if self.prefer_wasm and self.wasm_renderer:
            self.active_renderer = self.wasm_renderer
            logger.info("Using WASM renderer")
        elif self.local_renderer:
            self.active_renderer = self.local_renderer
            logger.info("Using local renderer")
        elif self.wasm_renderer:
            self.active_renderer = self.wasm_renderer
            logger.info("Using WASM renderer (local not available)")
        else:
            raise OpenSCADError("No OpenSCAD renderer available")
    
    def render_scad_to_stl(self, scad_code: str) -> bytes:
        """
        Render using the active renderer with fallback support
        """
        if not self.active_renderer:
            raise OpenSCADError("No renderer available")
        
        primary_renderer = self.active_renderer
        
        try:
            return primary_renderer.render_scad_to_stl(scad_code)
        except Exception as e:
            logger.warning(f"Primary renderer failed: {e}")
            
            # Try fallback if available and different from primary
            if (self.fallback_to_local and 
                self.local_renderer and 
                primary_renderer != self.local_renderer):
                
                logger.info("Attempting fallback to local renderer")
                try:
                    return self.local_renderer.render_scad_to_stl(scad_code)
                except Exception as fallback_error:
                    logger.error(f"Fallback renderer also failed: {fallback_error}")
                    raise OpenSCADError(f"Both renderers failed. Primary: {e}, Fallback: {fallback_error}")
            
            # Re-raise original error if no fallback
            raise
    
    def get_active_renderer_type(self) -> str:
        """Get the type of the currently active renderer"""
        if self.active_renderer == self.wasm_renderer:
            return "wasm"
        elif self.active_renderer == self.local_renderer:
            return "local"
        else:
            return "none"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive renderer statistics"""
        stats = {
            'active_renderer': self.get_active_renderer_type(),
            'prefer_wasm': self.prefer_wasm,
            'fallback_to_local': self.fallback_to_local,
            'available_renderers': []
        }
        
        if self.wasm_renderer:
            stats['available_renderers'].append('wasm')
            stats['wasm_stats'] = self.wasm_renderer.get_stats()
        
        if self.local_renderer:
            stats['available_renderers'].append('local')
            # Local renderer stats would be added here if available
        
        return stats