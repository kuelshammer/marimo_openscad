"""
HTTP Server for WASM Assets

Provides a simple HTTP server to serve WASM files to browsers.
This server integrates with anywidget to provide web-accessible WASM assets.
"""

import asyncio
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote
from pathlib import Path
from typing import Optional, Dict, Any
import socket
import time

from .wasm_asset_server import get_wasm_asset_server

logger = logging.getLogger(__name__)


class WASMHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for serving WASM assets"""
    
    def __init__(self, *args, wasm_server=None, **kwargs):
        self.wasm_server = wasm_server or get_wasm_asset_server()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests for WASM files"""
        try:
            # Parse the URL
            parsed_url = urlparse(self.path)
            path = unquote(parsed_url.path)
            
            # Remove leading slash and extract filename
            if path.startswith('/'):
                path = path[1:]
            
            # Check if this is a WASM asset request
            if path.startswith('wasm/'):
                filename = path[5:]  # Remove 'wasm/' prefix
                self._serve_wasm_asset(filename)
            elif path in ['openscad.wasm', 'openscad.js', 'openscad.fonts.js', 'openscad.mcad.js']:
                # Direct asset requests
                self._serve_wasm_asset(path)
            else:
                self._send_not_found()
                
        except Exception as e:
            logger.error(f"Error handling request {self.path}: {e}")
            self._send_error(500, str(e))
    
    def _serve_wasm_asset(self, filename: str):
        """Serve a WASM asset file"""
        asset_data = self.wasm_server.get_asset_data(filename)
        
        if asset_data is None:
            self._send_not_found()
            return
        
        data, mime_type = asset_data
        
        # Send response
        self.send_response(200)
        self.send_header('Content-Type', mime_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'public, max-age=3600')  # Cache for 1 hour
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
        self.end_headers()
        
        self.wfile.write(data)
        
        logger.debug(f"Served WASM asset: {filename} ({len(data)} bytes)")
    
    def _send_not_found(self):
        """Send 404 Not Found response"""
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'WASM asset not found')
    
    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(f'Error: {message}'.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to use Python logging instead of stderr"""
        logger.debug(f"HTTP: {format % args}")


class WASMHTTPServer:
    """
    HTTP server for serving WASM assets
    
    This server runs in a separate thread and provides HTTP access to WASM files.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 0):
        """
        Initialize WASM HTTP server
        
        Args:
            host: Host to bind to (default: localhost)
            port: Port to bind to (0 for auto-select)
        """
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.running = False
        self.wasm_server = get_wasm_asset_server()
    
    def start(self) -> str:
        """
        Start the HTTP server
        
        Returns:
            Base URL for accessing WASM assets
        """
        if self.running:
            return self.get_base_url()
        
        try:
            # Create server with custom handler
            def handler_factory(*args, **kwargs):
                return WASMHTTPHandler(*args, wasm_server=self.wasm_server, **kwargs)
            
            self.server = HTTPServer((self.host, self.port), handler_factory)
            
            # Get the actual port if auto-selected
            if self.port == 0:
                self.port = self.server.server_port
            
            # Start server in background thread
            self.thread = threading.Thread(target=self._run_server, daemon=True)
            self.thread.start()
            
            self.running = True
            
            base_url = self.get_base_url()
            logger.info(f"WASM HTTP server started at {base_url}")
            
            return base_url
            
        except Exception as e:
            logger.error(f"Failed to start WASM HTTP server: {e}")
            raise
    
    def _run_server(self):
        """Run the HTTP server (called in background thread)"""
        try:
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"WASM HTTP server error: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        self.running = False
        logger.info("WASM HTTP server stopped")
    
    def get_base_url(self) -> str:
        """Get the base URL for accessing WASM assets"""
        if not self.running:
            raise RuntimeError("Server not running")
        
        return f"http://{self.host}:{self.port}"
    
    def get_wasm_url(self, filename: str) -> str:
        """
        Get the full URL for a specific WASM asset
        
        Args:
            filename: Name of the WASM file
            
        Returns:
            Full URL to the WASM asset
        """
        return f"{self.get_base_url()}/wasm/{filename}"
    
    def is_running(self) -> bool:
        """Check if the server is running"""
        return self.running
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status information"""
        return {
            'running': self.running,
            'host': self.host,
            'port': self.port,
            'base_url': self.get_base_url() if self.running else None,
            'assets': self.wasm_server.get_asset_list()
        }


# Global server instance
_global_server = None


def get_wasm_http_server() -> WASMHTTPServer:
    """Get or create the global WASM HTTP server"""
    global _global_server
    
    if _global_server is None:
        _global_server = WASMHTTPServer()
    
    return _global_server


def start_wasm_server(host: str = 'localhost', port: int = 0) -> str:
    """
    Start the global WASM HTTP server
    
    Args:
        host: Host to bind to
        port: Port to bind to (0 for auto-select)
        
    Returns:
        Base URL for accessing WASM assets
    """
    server = get_wasm_http_server()
    
    if not server.is_running():
        return server.start()
    else:
        return server.get_base_url()


def stop_wasm_server():
    """Stop the global WASM HTTP server"""
    global _global_server
    
    if _global_server:
        _global_server.stop()
        _global_server = None


def get_wasm_server_status() -> Dict[str, Any]:
    """Get status of the global WASM HTTP server"""
    global _global_server
    
    if _global_server:
        return _global_server.get_status()
    else:
        return {'running': False, 'server': None}