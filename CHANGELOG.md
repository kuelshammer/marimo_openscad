# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-06-10

### Added
- Initial release of marimo-openscad
- JupyterSCAD-inspired architecture with Marimo integration
- Complete STL pipeline: SolidPython2 → OpenSCAD CLI → STL → Three.js
- Professional 3D rendering with Three.js and WebGL
- Reactive parameter updates through Marimo's DAG system
- Robust STL parser supporting binary and ASCII formats
- Cross-platform OpenSCAD integration (macOS, Linux, Windows)
- Examples: simple_demo.py and mechanical_parts.py

### Technical Features
- **STL Parser**: Based on Three.js STLLoader with enhancements
- **Rendering**: Anti-aliasing, shadows, OrbitControls navigation
- **Error Handling**: Graceful fallbacks and detailed error messages  
- **Performance**: Validated normals, TypedArrays, memory optimization
- **Compatibility**: Modern browsers with WebGL support

### Dependencies
- marimo >= 0.8.0
- solidpython2 >= 1.0.0
- anywidget >= 0.9.0
- traitlets >= 5.0.0
- OpenSCAD 2021.01+ (system dependency)

### Credits
- Inspired by [JupyterSCAD](https://github.com/jreiberkyle/jupyterscad) architecture
- Built on [SolidPython2](https://github.com/jeff-dh/SolidPython) for Python-CAD bridge
- Powered by [Three.js](https://threejs.org/) for WebGL rendering
- Integrated with [Marimo](https://github.com/marimo-team/marimo) reactive notebooks