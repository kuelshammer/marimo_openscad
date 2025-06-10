"""
SolidPython2 Bridge

Provides enhanced integration between SolidPython2 objects and OpenSCAD rendering
with automatic parameter extraction and model caching.
"""

import hashlib
import logging
from typing import Dict, Any, Optional

from .openscad_renderer import OpenSCADRenderer, OpenSCADError

# Configure logging
logger = logging.getLogger(__name__)

class SolidPythonError(Exception):
    """Custom exception for SolidPython2 errors"""
    pass

class SolidPythonBridge:
    """
    Enhanced bridge between SolidPython2 objects and OpenSCAD rendering
    
    Features:
    - Model caching based on content hash
    - Automatic parameter extraction
    - Intelligent re-rendering detection
    """
    
    def __init__(self, openscad_path: Optional[str] = None):
        """
        Initialize SolidPython2 bridge
        
        Args:
            openscad_path: Path to OpenSCAD executable (auto-detected if None)
        """
        self.renderer = OpenSCADRenderer(openscad_path=openscad_path)
        
        # Cache for model rendering results
        self.model_cache = {}
        
        logger.info("SolidPython bridge initialized")
    
    def render_to_stl(self, model, use_cache: bool = True) -> bytes:
        """
        Render a SolidPython2 model object to STL bytes with optional caching
        
        Args:
            model: SolidPython2 object with as_scad() method
            use_cache: Whether to use caching (default True)
            
        Returns:
            STL file contents as bytes
            
        Raises:
            SolidPythonError: If model is invalid or rendering fails
        """
        # Check if it's a valid SolidPython2 object
        if not hasattr(model, 'as_scad'):
            raise SolidPythonError(
                "Model must be a SolidPython2 object with as_scad() method"
            )
        
        try:
            # Generate SCAD code
            scad_code = model.as_scad()
            
            # Create comprehensive hash including model identity and SCAD code
            model_hash = self._hash_model(model, scad_code)
            
            # Check cache only if enabled
            if use_cache and model_hash in self.model_cache:
                logger.info(f"Using cached model for hash {model_hash[:8]}")
                return self.model_cache[model_hash]
            
            # Log for debugging cache misses
            if use_cache:
                logger.info(f"Cache miss for hash {model_hash[:8]}, rendering new STL")
            else:
                logger.info(f"Cache disabled, rendering new STL for hash {model_hash[:8]}")
            
            # Render to STL
            stl_data = self.renderer.render_scad_to_stl(scad_code)
            
            # Cache the result if enabled
            if use_cache:
                self.model_cache[model_hash] = stl_data
                logger.info(f"Cached model with hash {model_hash[:8]}")
            
            return stl_data
            
        except OpenSCADError:
            # Re-raise OpenSCAD errors as-is
            raise
        except Exception as e:
            raise SolidPythonError(f"Failed to render model: {e}")
    
    def save_model_to_stl(self, model, file_path: str) -> None:
        """
        Render a model and save it to an STL file
        
        Args:
            model: SolidPython2 object
            file_path: Path to save the STL file
            
        Raises:
            SolidPythonError: If rendering or saving fails
        """
        stl_data = self.render_to_stl(model)
        
        try:
            with open(file_path, 'wb') as f:
                f.write(stl_data)
            logger.info(f"Model saved to {file_path}")
        except Exception as e:
            raise SolidPythonError(f"Failed to save STL file: {e}")
    
    def _hash_scad_code(self, scad_code: str) -> str:
        """Generate a hash for OpenSCAD code for caching"""
        hasher = hashlib.md5()
        hasher.update(scad_code.encode('utf-8'))
        return hasher.hexdigest()
    
    def _hash_model(self, model, scad_code: str) -> str:
        """
        Generate a comprehensive hash for a model including object identity and SCAD code
        
        This ensures that different model instances with the same SCAD code
        get different cache entries if they represent different parameter states.
        """
        hasher = hashlib.md5()
        
        # Include SCAD code
        hasher.update(scad_code.encode('utf-8'))
        
        # Include model object identity to catch parameter changes
        # that don't change SCAD code structure
        hasher.update(str(id(model)).encode('utf-8'))
        
        # Try to include parameter values if accessible
        try:
            if hasattr(model, '__dict__'):
                # Sort dict items for consistent hashing
                model_state = str(sorted(model.__dict__.items()))
                hasher.update(model_state.encode('utf-8'))
        except Exception:
            # If we can't access model state, just use object id
            pass
            
        return hasher.hexdigest()
    
    def clear_cache(self) -> None:
        """Clear all cached models"""
        cache_size = len(self.model_cache)
        self.model_cache = {}
        logger.info(f"SolidPython bridge cache cleared ({cache_size} entries removed)")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state"""
        return {
            'cache_size': len(self.model_cache),
            'cache_keys': [key[:8] + '...' for key in self.model_cache.keys()]
        }