# Marimo-OpenSCAD Integration - Project Overview

## What This Project Does

This project enables **interactive 3D CAD modeling** directly in Marimo notebooks using SolidPython2 and OpenSCAD. Users can create parametric 3D models with **live sliders** that instantly update the 3D visualization in the browser.

## Key Features

✨ **Reactive 3D Modeling**: Change parameters with sliders and see the 3D model update instantly  
🖥️ **Browser-Based Rendering**: WebGL-powered 3D visualization with mouse controls  
📐 **OpenSCAD Integration**: Full SolidPython2 support with automatic OpenSCAD execution  
📁 **STL Export**: Generate files for 3D printing  
🔄 **Automatic Updates**: Marimo's reactive system ensures models stay synchronized  
🛡️ **Robust Fallbacks**: Progressive error handling for reliable operation  

## How It Works

1. **Define 3D models** using SolidPython2's intuitive Python syntax
2. **Create reactive parameters** with Marimo UI sliders and controls  
3. **Automatic 3D rendering** via OpenSCAD → STL → Three.js pipeline
4. **Interactive visualization** with mouse controls (rotate, zoom)
5. **Real-time updates** when parameters change

## Quick Example

```python
import marimo as mo
from solid2 import cube, cylinder
from marimo_openscad import InteractiveViewer

# Reactive parameter
height = mo.ui.slider(10, 100, value=50, label="Height")

# 3D model that updates automatically
model = cube([20, 20, height.value]) - cylinder(r=5, h=height.value+5, center=True)

# Interactive 3D viewer
viewer = InteractiveViewer()
viewer.update_model(model)
viewer
```

## Project Structure

```
marimo-openscad-clean/
├── README.md                          # Main project documentation
├── setup.py                           # Package installation script
├── pyproject.toml                     # Modern Python package configuration
├── LICENSE                            # MIT license
├── src/marimo_openscad/               # Core package source code
│   ├── __init__.py                    # Package exports
│   ├── openscad_renderer.py           # OpenSCAD CLI execution
│   ├── solid_bridge.py                # SolidPython2 integration with caching
│   └── interactive_viewer.py          # anywidget 3D viewer with Three.js
├── examples/                          # Example Marimo notebooks
│   ├── castle_demo.py                 # Interactive castle with 4 parameters
│   └── basic_shapes.py                # Simple shapes demonstration
└── docs/                              # Comprehensive documentation
    ├── installation.md                # Step-by-step installation guide
    ├── api.md                         # Complete API reference
    └── architecture.md                # Technical architecture overview
```

## Core Components

### 1. `OpenSCADRenderer`
- Executes OpenSCAD command-line interface
- Handles cross-platform OpenSCAD discovery
- Manages temporary files and error handling
- Converts SolidPython2 objects to STL binary data

### 2. `SolidPythonBridge`
- Integrates SolidPython2 with OpenSCAD execution
- Implements intelligent caching based on model content
- Provides high-level API for model rendering
- Handles error recovery and validation

### 3. `InteractiveViewer`
- anywidget-based 3D visualization component
- Three.js WebGL rendering with hardware acceleration
- Custom mouse controls (drag to rotate, wheel to zoom)
- Progressive fallback system (STL → Procedural → Test cube)
- Real-time synchronization with Marimo's reactive system

## Technical Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SolidPython2  │───▶│   OpenSCAD CLI  │───▶│   STL Binary    │
│     Objects     │    │   Execution     │    │      Data       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Marimo Reactive│◀───│   anywidget     │◀───│  Base64 Encode  │
│     Notebook    │    │   Integration   │    │   Transmission  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebGL Render  │◀───│   Three.js      │◀───│  JavaScript     │
│   with Controls │    │ BufferGeometry  │    │  STL Parser     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Installation Requirements

- **Python**: 3.8 or higher
- **Dependencies**: `marimo`, `solidpython2`, `anywidget` 
- **System**: OpenSCAD executable (auto-detected or manually specified)
- **Browser**: Modern browser with WebGL support

## Usage Workflow

1. **Install dependencies**: `pip install marimo solidpython2 anywidget`
2. **Install OpenSCAD**: Download from openscad.org or use package manager
3. **Run examples**: `marimo edit examples/castle_demo.py`
4. **Create your own**: Import `InteractiveViewer` and start modeling

## Advantages Over Traditional CAD Tools

🎛️ **Reactive Parameters**: Unlike traditional CAD, parameters update the model instantly  
📝 **Code-Based Modeling**: Version control, reproducibility, and programmatic generation  
🌐 **Web-Native**: Runs in browser, easy sharing and deployment  
📊 **Notebook Integration**: Combine CAD with data analysis and documentation  
🔄 **Marimo Benefits**: Deterministic execution, automatic dependency tracking  

## Performance Features

- **Model Caching**: Avoid re-rendering identical models
- **Triangle Limiting**: Automatic optimization for browser performance
- **Progressive Fallbacks**: Ensure something always renders
- **Lazy Loading**: Load Three.js only when needed

## Error Handling

The system implements a robust **3-layer fallback strategy**:

1. **Primary**: Parse and render actual STL data from OpenSCAD
2. **Secondary**: Show procedural geometry if STL parsing fails  
3. **Tertiary**: Display colored test cube if all else fails

This ensures users always see **something**, even when there are errors.

## Future Roadmap

🚀 **WebAssembly Integration**: Run OpenSCAD directly in browser for faster rendering  
📱 **Mobile Support**: Optimize for touch devices and smaller screens  
🎬 **Animation System**: Parameter sweeps and animated demonstrations  
🤝 **Collaboration**: Real-time sharing and editing capabilities  
📦 **PyPI Package**: Easy installation via `pip install marimo-openscad`  

## Development Philosophy

This project follows **modern Python packaging standards** and **clean architecture principles**:

- **Single Responsibility**: Each module has a clear, focused purpose
- **Dependency Injection**: Components can be configured and tested independently  
- **Error Handling**: Comprehensive exception handling with meaningful messages
- **Documentation**: Extensive docs with examples and troubleshooting
- **Type Safety**: Type hints throughout for better IDE support
- **Testing Ready**: Architecture designed for easy unit and integration testing

## Why This Matters

This project represents a **new paradigm** for CAD workflows:

- **Educational**: Perfect for teaching parametric design concepts
- **Rapid Prototyping**: Quick iteration on design ideas
- **Data-Driven Design**: Generate models from data and analysis
- **Open Source**: Built on open technologies, fully extensible
- **Web-First**: Native browser deployment, no complex software installation

The integration of **Marimo's reactive system** with **OpenSCAD's powerful modeling** creates a uniquely productive environment for 3D design and education.