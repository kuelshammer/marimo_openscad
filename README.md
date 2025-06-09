# Marimo-OpenSCAD Integration

Interactive 3D CAD modeling in Marimo notebooks using SolidPython2 and OpenSCAD with real-time parameter updates and WebGL visualization.

## Features

- 🎛️ **Reactive Parameters**: Live sliders that instantly update 3D models
- 🖥️ **Browser 3D Rendering**: WebGL-powered visualization with mouse controls
- 📐 **OpenSCAD Integration**: Full SolidPython2 support with automatic OpenSCAD execution
- 📁 **Export Functionality**: Generate STL files for 3D printing
- 🔄 **Automatic Updates**: Marimo's reactive system ensures consistent state
- 🛡️ **Robust Fallbacks**: Progressive error handling for reliable operation

## Quick Start

1. **Install dependencies:**
```bash
pip install marimo solidpython2 anywidget
```

2. **Install OpenSCAD:**
   - Download from [openscad.org](https://openscad.org)
   - Place `openscad` executable in project root or ensure it's in PATH

3. **Run the example:**
```bash
marimo edit examples/castle_demo.py
```

## Architecture

```
SolidPython2 Objects → OpenSCAD CLI → STL Generation → 
Base64 Encoding → JavaScript STL Parser → Three.js BufferGeometry → 
WebGL Rendering → anywidget → Marimo Reactive Cell
```

## Core Components

- **`OpenSCADRenderer`**: Handles OpenSCAD CLI execution and STL generation
- **`SolidPythonBridge`**: Integrates SolidPython2 objects with OpenSCAD
- **`InteractiveCastleViewer`**: anywidget for 3D visualization with Three.js
- **Reactive Notebooks**: Marimo notebooks with live parameter controls

## Usage Example

```python
import marimo as mo
from solid2 import cube, cylinder
from marimo_openscad import OpenSCADRenderer, InteractiveViewer

# Reactive parameters
height = mo.ui.slider(10, 100, value=50, label="Height")
radius = mo.ui.slider(5, 25, value=15, label="Radius")

# Create 3D model
model = cube([30, 30, height.value]) + cylinder(r=radius.value, h=height.value).translate([15, 15, height.value])

# 3D visualization with interactive controls
viewer = InteractiveViewer()
viewer.update_model(model)
viewer
```

## Documentation

- [Installation Guide](docs/installation.md)
- [API Reference](docs/api.md)
- [Architecture Overview](docs/architecture.md)
- [Examples](examples/)

## Requirements

- Python 3.8+
- Marimo >= 0.13.0
- SolidPython2 >= 1.0.0
- anywidget >= 0.9.0
- OpenSCAD (system dependency)
- Modern browser with WebGL support

## License

MIT License - see LICENSE file for details.