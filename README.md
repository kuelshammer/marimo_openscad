# Marimo-OpenSCAD

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**Interactive 3D CAD modeling in Marimo notebooks using SolidPython2 and OpenSCAD**

Bring parametric 3D design to your Marimo notebooks with reactive parameters, real-time 3D visualization, and seamless integration with the SolidPython2 ecosystem.

## ✨ Features

- 🎯 **JupyterSCAD-inspired**: Proven architecture adapted for Marimo's reactive paradigm
- 🔄 **Reactive Parameters**: Changes to sliders instantly update 3D models
- 🚀 **Real STL Pipeline**: SolidPython2 → OpenSCAD CLI → STL → Three.js BufferGeometry
- 🎨 **Professional Rendering**: WebGL-based 3D visualization with shadows and controls
- 📦 **Zero Server Dependencies**: Works with static HTML export
- 🔧 **Production Ready**: Generate models for 3D printing and CNC machining

## 🚀 Quick Start

### Installation

```bash
pip install marimo solidpython2
# Ensure OpenSCAD is installed and accessible in PATH
```

### Basic Usage

```python
import marimo as mo
from marimo_openscad import openscad_viewer
from solid2 import cube, cylinder, difference

app = mo.App()

@app.cell
def __():
    # Reactive parameters
    size = mo.ui.slider(5, 30, value=15, label="Size")
    hole_radius = mo.ui.slider(1, 10, value=4, label="Hole Radius")
    return size, hole_radius

@app.cell  
def __(size, hole_radius):
    # Normal SolidPython2 syntax
    base = cube([size.value, size.value, 10])
    hole = cylinder(r=hole_radius.value, h=12).up(-1)
    model = difference()(base, hole)
    return model,

@app.cell
def __(model):
    # 3D visualization
    viewer = openscad_viewer(model)
    return viewer,
```

## 🏗️ Architecture

Our implementation follows the proven **JupyterSCAD architecture** with modern enhancements:

```
SolidPython2 Objects → OpenSCAD CLI → STL Generation → 
Three.js BufferGeometry → WebGL Rendering → anywidget → Marimo Reactive Cell
```

### Key Components

- **STL Pipeline**: Real OpenSCAD execution for accurate geometry
- **Three.js Integration**: Professional 3D rendering with OrbitControls
- **anywidget Framework**: Modern widget system for Marimo
- **Reactive Updates**: Automatic model regeneration on parameter changes

## 📋 Requirements

### Software Dependencies
- **Python 3.8+**
- **Marimo 0.8.0+**
- **SolidPython2 1.0.0+**
- **OpenSCAD 2021.01+** (must be installed separately)

### System Requirements
- Modern browser with WebGL support
- OpenSCAD binary accessible in system PATH or `/Applications/OpenSCAD.app/` (macOS)

## 🎨 Examples

### Mechanical Bracket
```python
from solid2 import cube, cylinder, union, difference

def create_bracket(width=40, height=25, thickness=5, hole_diameter=6):
    # L-shaped bracket
    horizontal = cube([width, thickness, height])
    vertical = cube([thickness, width, height])
    bracket = union()(horizontal, vertical)
    
    # Mounting holes
    hole1 = cylinder(d=hole_diameter, h=height+2).translate([width/2, thickness/2, -1])
    hole2 = cylinder(d=hole_diameter, h=height+2).translate([thickness/2, width/2, -1])
    
    return difference()(bracket, hole1, hole2)
```

### Parametric Gear
```python
from solid2 import cylinder, union
import math

def create_gear(teeth=16, module=2, thickness=6):
    pitch_radius = (teeth * module) / 2
    base = cylinder(r=pitch_radius, h=thickness)
    
    # Simplified teeth
    tooth_geometries = []
    for i in range(teeth):
        angle = (360 / teeth) * i
        # ... tooth geometry creation
    
    return union()(base, *tooth_geometries)
```

More examples in the [`examples/`](./examples/) directory.

## 🙏 Credits and Inspiration

This project builds upon the excellent work of several open-source projects:

### Core Inspiration
- **[JupyterSCAD](https://github.com/jreiberkyle/jupyterscad)** by jreiberkyle
  - *Architecture inspiration*: Proven SolidPython2 → STL → Three.js pipeline
  - *Implementation reference*: STL parsing and BufferGeometry creation
  - *Design patterns*: Widget integration and 3D visualization approaches

### Foundational Technologies
- **[SolidPython2](https://github.com/jeff-dh/SolidPython)** by jeff-dh
  - *Core modeling*: Python-to-OpenSCAD code generation
  - *Syntax design*: Modern method chaining and operator overloading
  - *API patterns*: `.as_scad()` method and object model

- **[Marimo](https://github.com/marimo-team/marimo)** 
  - *Reactive framework*: Deterministic notebook execution
  - *Widget system*: Modern anywidget integration
  - *Architecture*: Dependency graph and reactive updates

- **[Three.js](https://threejs.org/)**
  - *3D rendering*: WebGL-based geometry rendering
  - *STL loader*: Binary and ASCII STL parsing algorithms
  - *Controls*: OrbitControls for 3D navigation

### Technical References
- **[Three.js STLLoader](https://github.com/mrdoob/three.js/blob/dev/examples/jsm/loaders/STLLoader.js)**
  - *STL parsing algorithms*: Binary and ASCII format support
  - *BufferGeometry creation*: Efficient vertex and normal handling
  - *Error handling patterns*: Robust parsing with fallbacks

- **[OpenSCAD](https://openscad.org/)**
  - *CAD engine*: Constructive solid geometry processing
  - *STL export*: High-quality mesh generation
  - *CLI interface*: Automated batch processing

## 🔧 Technical Details

### STL Processing Pipeline

Our STL parser is based on the Three.js STLLoader with enhancements:

```javascript
// Binary STL parsing (based on Three.js implementation)
static parseBinary(data) {
    const reader = new DataView(data);
    const faces = reader.getUint32(80, true);
    // ... triangle extraction with validated normals
}

// ASCII STL parsing with line-by-line processing
static parseASCII(data) {
    const lines = data.split('\\n');
    // ... vertex and normal extraction
}
```

### Performance Optimizations

- **Validated Normals**: Automatic normal vector validation and correction
- **Memory Efficiency**: TypedArrays for vertex data
- **Rendering Quality**: Anti-aliasing and optimized material settings
- **Fallback Systems**: Graceful degradation with test geometries

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### Development Setup
```bash
git clone https://github.com/yourusername/marimo-openscad.git
cd marimo-openscad
pip install -e .
```

## 📄 License

MIT License - see [LICENSE](./LICENSE) file for details.

## 🌟 Acknowledgments

Special thanks to:
- The JupyterSCAD team for pioneering Jupyter-OpenSCAD integration
- The Marimo team for creating an excellent reactive notebook platform  
- The SolidPython2 maintainers for the powerful Python-CAD bridge
- The Three.js community for world-class 3D web technologies
- The OpenSCAD project for the robust CAD kernel

---

*Built with ❤️ for the open-source CAD community*