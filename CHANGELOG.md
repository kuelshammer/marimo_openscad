# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2025-06-13

### Analysis & Planning
- **CRITICAL ANALYSIS**: Identified four architecture-breaking issues blocking production
- **SYSTEMATIC FIX PLAN**: 4-phase recovery strategy with 16 testable steps
- **Documentation Cleanup**: Removed 4 outdated MD files, consolidated architecture info

### Known Issues (Blocking Release)
- ❌ **Marimo Reactivity Conflicts** - Variable redefinition in notebook cells
- ❌ **anywidget Import Limitations** - Browser can't load local modules  
- ❌ **WASM Placeholder System** - Fake STL instead of real rendering
- ❌ **Test Coverage Gaps** - Mocks hide real integration failures

### Architecture Status
- ✅ **Phase 1 CSG Rendering** - Wireframe fallback completed (32/32 tests passing)
- ✅ **WASM-Safe Architecture** - anywidget-compatible design implemented
- ❌ **WASM Integration** - Blocked by critical import/placeholder issues
- 📋 **Fix Plan Ready** - Sequential dependency resolution approach prepared

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

### Known Limitations (v0.1.0)
- CSG operations show fallback cubes instead of real geometry
- WASM rendering advertised but not functional
- Test suite relies heavily on mocks

### Credits
- Inspired by [JupyterSCAD](https://github.com/jreiberkyle/jupyterscad) architecture
- Built on [SolidPython2](https://github.com/jeff-dh/SolidPython) for Python-CAD bridge
- Powered by [Three.js](https://threejs.org/) for WebGL rendering
- Integrated with [Marimo](https://github.com/marimo-team/marimo) reactive notebooks