"""
OpenSCAD CLI Renderer

Handles execution of OpenSCAD command-line interface to generate STL files
from SolidPython2 objects and OpenSCAD code.
"""

import subprocess
import tempfile
import os
import logging
from pathlib import Path
from typing import Union, Optional

# Configure logging
logger = logging.getLogger(__name__)

class OpenSCADError(Exception):
    """Custom exception for OpenSCAD-related errors"""
    pass

class OpenSCADRenderer:
    """
    Renderer for executing OpenSCAD and generating STL files
    
    Handles the conversion from OpenSCAD code to STL format using the
    OpenSCAD command-line interface.
    """
    
    def __init__(self, openscad_path: Optional[str] = None):
        """
        Initialize OpenSCAD renderer
        
        Args:
            openscad_path: Path to OpenSCAD executable. If None, searches common locations.
        """
        self.openscad_path = self._find_openscad(openscad_path)
        logger.info(f"Using OpenSCAD at: {self.openscad_path}")
        
        # Log OpenSCAD version
        try:
            version_result = subprocess.run(
                [self.openscad_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if version_result.returncode == 0:
                version = version_result.stdout.strip().split('\n')[0] if version_result.stdout else "Unknown"
            else:
                version = "Unknown"
            logger.info(f"OpenSCAD version: {version}")
        except Exception as e:
            logger.warning(f"Could not determine OpenSCAD version: {e}")
    
    def _find_openscad(self, openscad_path: Optional[str]) -> str:
        """Find OpenSCAD executable in common locations"""
        if openscad_path and os.path.exists(openscad_path):
            return openscad_path
        
        # Common OpenSCAD locations
        common_paths = [
            "./openscad",  # Local project directory
            "openscad",    # In PATH
            "/usr/bin/openscad",  # Linux
            "/usr/local/bin/openscad",  # macOS Homebrew
            "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD",  # macOS app
            "C:\\Program Files\\OpenSCAD\\openscad.exe",  # Windows
            "C:\\Program Files (x86)\\OpenSCAD\\openscad.exe"  # Windows 32-bit
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # Try which/where command
        try:
            result = subprocess.run(
                ["which", "openscad"] if os.name != 'nt' else ["where", "openscad"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except Exception:
            pass
        
        raise OpenSCADError(
            "OpenSCAD executable not found. Please install OpenSCAD or specify path."
        )
    
    def render_scad_to_stl(self, scad_code: str) -> bytes:
        """
        Render OpenSCAD code to STL format
        
        Args:
            scad_code: OpenSCAD code as string
            
        Returns:
            STL file contents as bytes
            
        Raises:
            OpenSCADError: If rendering fails
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as scad_file:
            scad_file.write(scad_code)
            scad_file_path = scad_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as stl_file:
            stl_file_path = stl_file.name
        
        try:
            # Execute OpenSCAD
            cmd = [
                self.openscad_path,
                "--export-format=binstl",
                "-o", stl_file_path,
                scad_file_path
            ]
            
            logger.info(f"Running OpenSCAD to generate STL: {' '.join(cmd)}")
            
            import time
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            end_time = time.time()
            
            if result.returncode != 0:
                error_msg = f"OpenSCAD failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f":\n{result.stderr}"
                raise OpenSCADError(error_msg)
            
            # Read generated STL file
            if not os.path.exists(stl_file_path):
                raise OpenSCADError("OpenSCAD did not generate STL file")
            
            with open(stl_file_path, 'rb') as f:
                stl_data = f.read()
            
            if len(stl_data) == 0:
                raise OpenSCADError("Generated STL file is empty")
            
            logger.info(f"OpenSCAD rendering completed in {end_time - start_time:.2f} seconds")
            
            return stl_data
            
        finally:
            # Clean up temporary files
            for temp_path in [scad_file_path, stl_file_path]:
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_path}: {e}")
    
    def render_solidpython_to_stl(self, model) -> bytes:
        """
        Render SolidPython2 model to STL format
        
        Args:
            model: SolidPython2 object with as_scad() method
            
        Returns:
            STL file contents as bytes
            
        Raises:
            OpenSCADError: If model is invalid or rendering fails
        """
        if not hasattr(model, 'as_scad'):
            raise OpenSCADError(
                "Model must be a SolidPython2 object with as_scad() method"
            )
        
        try:
            scad_code = model.as_scad()
        except Exception as e:
            raise OpenSCADError(f"Failed to generate OpenSCAD code: {e}")
        
        return self.render_scad_to_stl(scad_code)