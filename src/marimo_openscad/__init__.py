"""
Marimo-OpenSCAD Integration
3D CAD visualization for SolidPython2 objects in Marimo notebooks

Inspired by JupyterSCAD and built with modern web technologies.
"""

from .viewer import openscad_viewer, OpenSCADViewer

__version__ = "0.1.0"
__author__ = "Claude Code Assistant"
__description__ = "3D CAD visualization for SolidPython2 objects in Marimo notebooks"

# Expose main API
__all__ = ["openscad_viewer", "OpenSCADViewer"]