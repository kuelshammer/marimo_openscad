"""
WASM Asset Server for anywidget

Provides HTTP serving capabilities for WASM files within the anywidget framework.
This module enables browsers to access the bundled OpenSCAD WASM files via HTTP.
"""

import os
import mimetypes
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
import base64
import urllib.parse

logger = logging.getLogger(__name__)


class WASMAssetServer:
    """
    Serves WASM assets through anywidget's HTTP serving capabilities.
    
    This class provides methods to serve WASM files via HTTP endpoints
    that can be accessed by browsers in the anywidget context.
    """
    
    def __init__(self):
        self.wasm_dir = self._get_wasm_directory()
        self.asset_registry = {}
        self._register_assets()
    
    def _get_wasm_directory(self) -> Path:
        """Get the directory containing WASM files"""
        return Path(__file__).parent / "wasm"
    
    def _register_assets(self):
        """Register all WASM assets for serving"""
        if not self.wasm_dir.exists():
            logger.warning(f"WASM directory not found: {self.wasm_dir}")
            return
        
        wasm_files = [
            "openscad.wasm",
            "openscad.js",
            "openscad.wasm.js", 
            "openscad.d.ts",
            "openscad.fonts.js",
            "openscad.fonts.d.ts",
            "openscad.mcad.js",
            "openscad.mcad.d.ts"
        ]
        
        for filename in wasm_files:
            file_path = self.wasm_dir / filename
            if file_path.exists():
                self.asset_registry[filename] = file_path
                logger.debug(f"Registered WASM asset: {filename}")
    
    def get_asset_data(self, filename: str) -> Optional[Tuple[bytes, str]]:
        """
        Get asset data and MIME type for a given filename
        
        Args:
            filename: Name of the WASM file to serve
            
        Returns:
            Tuple of (file_data, mime_type) or None if file not found
        """
        if filename not in self.asset_registry:
            logger.warning(f"WASM asset not found: {filename}")
            return None
        
        file_path = self.asset_registry[filename]
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Determine MIME type
            mime_type = self._get_mime_type(filename)
            
            logger.debug(f"Serving WASM asset: {filename} ({len(data)} bytes, {mime_type})")
            return data, mime_type
            
        except Exception as e:
            logger.error(f"Error reading WASM asset {filename}: {e}")
            return None
    
    def _get_mime_type(self, filename: str) -> str:
        """Get appropriate MIME type for WASM files"""
        if filename.endswith('.wasm'):
            return 'application/wasm'
        elif filename.endswith('.js'):
            return 'application/javascript'
        elif filename.endswith('.d.ts'):
            return 'application/typescript'
        else:
            return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    
    def get_asset_list(self) -> Dict[str, Dict[str, any]]:
        """Get list of available assets with metadata"""
        assets = {}
        
        for filename, file_path in self.asset_registry.items():
            try:
                stat = file_path.stat()
                assets[filename] = {
                    'size': stat.st_size,
                    'mime_type': self._get_mime_type(filename),
                    'path': str(file_path),
                    'available': True
                }
            except Exception as e:
                assets[filename] = {
                    'size': 0,
                    'mime_type': 'unknown',
                    'path': str(file_path),
                    'available': False,
                    'error': str(e)
                }
        
        return assets
    
    def create_data_url(self, filename: str) -> Optional[str]:
        """
        Create a data URL for a WASM asset (for small files only)
        
        Args:
            filename: Name of the WASM file
            
        Returns:
            Data URL string or None if file too large or not found
        """
        asset_data = self.get_asset_data(filename)
        if not asset_data:
            return None
        
        data, mime_type = asset_data
        
        # Only create data URLs for files smaller than 1MB
        if len(data) > 1024 * 1024:
            logger.warning(f"File {filename} too large for data URL ({len(data)} bytes)")
            return None
        
        # Encode as base64 data URL
        b64_data = base64.b64encode(data).decode('utf-8')
        return f"data:{mime_type};base64,{b64_data}"
    
    def get_asset_urls(self, base_url: str) -> Dict[str, str]:
        """
        Get URLs for all WASM assets using the provided base URL
        
        Args:
            base_url: Base URL for asset serving (e.g., from anywidget)
            
        Returns:
            Dictionary mapping filenames to URLs
        """
        urls = {}
        
        # Ensure base URL ends with /
        if not base_url.endswith('/'):
            base_url += '/'
        
        for filename in self.asset_registry:
            # URL-encode the filename for safety
            encoded_filename = urllib.parse.quote(filename)
            urls[filename] = base_url + encoded_filename
        
        return urls
    
    def validate_assets(self) -> Dict[str, bool]:
        """
        Validate that all required WASM assets are available
        
        Returns:
            Dictionary mapping filenames to availability status
        """
        required_files = ["openscad.wasm", "openscad.js"]
        optional_files = ["openscad.fonts.js", "openscad.mcad.js"]
        
        validation = {}
        
        for filename in required_files:
            validation[filename] = filename in self.asset_registry
            if not validation[filename]:
                logger.error(f"Required WASM asset missing: {filename}")
        
        for filename in optional_files:
            validation[filename] = filename in self.asset_registry
            if not validation[filename]:
                logger.warning(f"Optional WASM asset missing: {filename}")
        
        return validation


# Global instance for use across the package
wasm_asset_server = WASMAssetServer()


def get_wasm_asset_server() -> WASMAssetServer:
    """Get the global WASM asset server instance"""
    return wasm_asset_server


def serve_wasm_asset(filename: str) -> Optional[Tuple[bytes, str]]:
    """
    Convenience function to serve a WASM asset
    
    Args:
        filename: Name of the WASM file to serve
        
    Returns:
        Tuple of (file_data, mime_type) or None if file not found
    """
    return wasm_asset_server.get_asset_data(filename)