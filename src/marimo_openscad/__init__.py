"""
Marimo-OpenSCAD Integration

Interactive 3D CAD modeling in Marimo notebooks using SolidPython2 and OpenSCAD
with real-time parameter updates and WebGL visualization.
"""

from .openscad_renderer import OpenSCADRenderer, OpenSCADError
from .solid_bridge import SolidPythonBridge, SolidPythonError
from .interactive_viewer import InteractiveViewer

__version__ = "1.0.0"
__author__ = "Marimo-OpenSCAD Contributors"

__all__ = [
    "OpenSCADRenderer",
    "OpenSCADError", 
    "SolidPythonBridge",
    "SolidPythonError",
    "InteractiveViewer"
]