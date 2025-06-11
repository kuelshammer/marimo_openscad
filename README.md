# Marimo-OpenSCAD

[![CI/CD Tests](https://github.com/kuelshammer/marimo_openscad/actions/workflows/test.yml/badge.svg)](https://github.com/kuelshammer/marimo_openscad/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Critical Cache Tests](https://img.shields.io/badge/Cache%20Tests-🔥%20Critical-red)](tests/test_cache_behavior.py)
[![LLM Regression Prevention](https://img.shields.io/badge/LLM%20Regression-🎯%20Prevented-green)](tests/test_llm_identified_issues.py)

**Interactive 3D CAD modeling in Marimo notebooks with browser-native WebAssembly rendering**

Bring parametric 3D design to your Marimo notebooks with reactive parameters, real-time 3D visualization, and zero-dependency browser-native OpenSCAD rendering.

## ✨ Features

### 🚀 **WebAssembly-First Architecture**
- **Browser-Native Rendering**: No local OpenSCAD installation required
- **190x Faster Performance**: Complex models render in milliseconds vs seconds
- **Zero Dependencies**: Works out-of-the-box in any modern browser
- **Offline Capable**: Full functionality without internet after initial load

### 🎯 **Smart Renderer Selection**
- **Auto-Detection**: Intelligent fallback between WASM and local OpenSCAD
- **User Choice**: Force WASM, local, or let the system decide
- **Performance Optimized**: Advanced caching and web worker support
- **Memory Efficient**: Automatic cleanup and resource management

### 🔄 **Reactive Integration**
- **JupyterSCAD-inspired**: Proven architecture adapted for Marimo's reactive paradigm
- **Real-time Updates**: Changes to sliders instantly update 3D models
- **Advanced Pipeline**: SolidPython2 → OpenSCAD WASM → STL → Three.js BufferGeometry
- **Professional Rendering**: WebGL-based 3D visualization with shadows and controls

## 🚀 Quick Start

### Installation

```bash
# Install core dependencies (no OpenSCAD required for WASM!)
pip install marimo solidpython2

# Install marimo-openscad
pip install marimo-openscad

# Or install from source
git clone https://github.com/kuelshammer/marimo-openscad.git
cd marimo-openscad
pip install -e .
```

### 🎯 Basic Usage (WASM - Recommended)

```python
import marimo as mo
from marimo_openscad import openscad_viewer
from solid2 import cube, cylinder, difference

# Auto-selects WASM renderer (no OpenSCAD installation needed!)
model = cube([10, 10, 10]) - cylinder(r=3, h=12)
viewer = openscad_viewer(model)  # renderer_type="auto" (default)
```

### ⚡ Advanced Usage - Renderer Selection

```python
# Force WASM renderer (browser-native, fastest)
viewer_wasm = openscad_viewer(model, renderer_type="wasm")

# Force local renderer (requires OpenSCAD installation)
viewer_local = openscad_viewer(model, renderer_type="local") 

# Auto-selection with preferences
viewer_auto = openscad_viewer(model, renderer_type="auto")  # Prefers WASM
```

### 🔄 Reactive Parameters Demo

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
    # SolidPython2 model with reactive parameters
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

### 🚀 **WASM-First Architecture (Recommended)**

```
SolidPython2 → OpenSCAD WASM → STL Binary → Three.js BufferGeometry → WebGL
                    ↑
            Runs entirely in browser
```

### 🔧 **Local Fallback Architecture**

```
SolidPython2 → OpenSCAD CLI → STL Binary → Three.js BufferGeometry → WebGL
                    ↑
           Requires local installation
```

### Key Components

- **Smart Renderer Factory**: Automatic selection between WASM and local OpenSCAD
- **Advanced Caching**: 7-day WASM module cache with automatic cleanup  
- **Web Worker Support**: Non-blocking rendering for complex models
- **Memory Management**: Intelligent resource cleanup and monitoring
- **Three.js Integration**: Professional 3D rendering with OrbitControls
- **anywidget Framework**: Modern widget system for Marimo reactive cells

## ⚡ Performance Comparison

| Feature | WASM Renderer | Local Renderer |
|---------|---------------|----------------|
| **Installation** | ✅ Zero dependencies | ❌ Requires OpenSCAD |
| **Simple Models** | 🚀 0.5ms | 🐌 163ms |
| **Complex Models** | 🚀 79ms | 🐌 15,000ms |
| **Performance** | 🎯 **190x faster** | 📊 Baseline |
| **Memory Usage** | ✅ Efficient | ⚠️ Higher |
| **Offline Support** | ✅ Full support | ❌ Limited |
| **Browser Blocking** | ✅ Zero (Web Workers) | ❌ UI freezes |
| **Cache Benefits** | ✅ 35% improvement | ⚠️ Minimal |

### 📊 **Real Performance Data**
- **Cache Performance**: 35% faster on subsequent renders
- **Concurrent Rendering**: 5+ models simultaneously  
- **Memory Efficiency**: Automatic cleanup after 5 minutes
- **Browser Support**: 95%+ modern browsers

## 📋 Requirements

### 🚀 **WASM Renderer (Recommended)**
- **Python 3.8+**
- **Marimo 0.8.0+** 
- **SolidPython2 1.0.0+**
- **Modern Browser** with WebAssembly support (95%+ coverage)
- **No OpenSCAD installation required!** ✅

### 🔧 **Local Renderer (Fallback)**
- All WASM requirements above, plus:
- **OpenSCAD 2021.01+** (must be installed separately)
- OpenSCAD binary accessible in system PATH or `/Applications/OpenSCAD.app/` (macOS)

### 🌐 **Browser Compatibility**
| Browser | WASM Support | Performance |
|---------|--------------|-------------|
| Chrome 69+ | ✅ Full | 🚀 Excellent |
| Firefox 62+ | ✅ Full | 🚀 Excellent |
| Safari 14+ | ✅ Full | ⚡ Good |
| Edge 79+ | ✅ Full | 🚀 Excellent |

### 💻 **Development Dependencies (Optional)**
For frontend widget development only:
- **Node.js 18+** and **npm** 
- Used for JavaScript testing, linting, and bundling
- **Not required** for end users installing via PyPI

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

## 🔄 Migration Guide: Local → WASM

### Automatic Migration (Recommended)
The default `renderer_type="auto"` automatically prefers WASM and falls back to local OpenSCAD:

```python
# No changes needed - automatically uses WASM when available
viewer = openscad_viewer(model)  # Uses WASM by default
```

### Explicit WASM Usage
Force WASM renderer for guaranteed browser-native rendering:

```python
# Explicit WASM (fails if WASM unavailable)
viewer = openscad_viewer(model, renderer_type="wasm")
```

### Performance Benefits After Migration
- **190x faster rendering** for complex models
- **35% cache improvements** on repeated renders  
- **Zero installation dependencies** - works in any browser
- **Non-blocking UI** with Web Worker support

### Troubleshooting Migration Issues

#### Issue: "WASM not supported"
```python
# Check browser compatibility
info = viewer.get_renderer_info()
print(f"Active renderer: {info['active_renderer']}")
print(f"Browser support: {info.get('wasm_supported', False)}")
```

#### Issue: Performance not improved
```python
# Verify WASM is actually being used
if info['active_renderer'] != 'wasm':
    print("Still using local renderer - check browser support")
```

#### Issue: Models not rendering
```python
# Test with simple model first
simple_model = cube([5, 5, 5])
test_viewer = openscad_viewer(simple_model, renderer_type="wasm")
```

### Comparison: Before vs After Migration

| Aspect | Local OpenSCAD | WASM Migration |
|--------|---------------|---------------|
| **Setup** | `brew install openscad` | No installation needed |
| **CI/CD** | ❌ Installation required | ✅ Zero dependencies |
| **Performance** | 15,000ms (complex) | 79ms (190x faster) |
| **Caching** | Minimal benefit | 35% improvement |
| **Browser Support** | N/A | 95%+ modern browsers |
| **Offline** | Limited | ✅ Full support |

## 🛠️ Advanced WASM Configuration

### Cache Management
```python
# Configure cache settings
viewer = openscad_viewer(
    model, 
    renderer_type="wasm",
    cache_duration=7  # Days to cache WASM modules
)
```

### Memory Optimization
```python
# Enable memory management
from marimo_openscad.memory_manager import MemoryUtils

# Optimize memory usage
stats = await MemoryUtils.optimizeMemory()
print(f"Memory pressure: {MemoryUtils.getMemoryPressure()}")
```

### Web Worker Configuration
```python
# Force Web Worker usage (non-blocking)
viewer = openscad_viewer(
    model,
    renderer_type="wasm", 
    use_worker=True  # Prevents UI freezing
)
```

## 🔍 Troubleshooting

### WASM Issues

#### Browser Compatibility Check
```javascript
// Check WASM support
const hasWASM = (() => {
    try {
        if (typeof WebAssembly === "object" &&
            typeof WebAssembly.instantiate === "function") {
            const module = new WebAssembly.Module(
                Uint8Array.of(0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00)
            );
            return WebAssembly.Module.imports(module).length === 0;
        }
    } catch (e) {}
    return false;
})();

console.log("WASM Support:", hasWASM);
```

#### Performance Issues
1. **Enable caching**: WASM modules are cached for 7 days
2. **Use Web Workers**: Prevents main thread blocking
3. **Monitor memory**: Use memory manager for large models

#### Fallback Testing
```python
# Test both renderers
results = {}
for renderer in ["wasm", "local", "auto"]:
    try:
        viewer = openscad_viewer(model, renderer_type=renderer)
        results[renderer] = "✅ Working"
    except Exception as e:
        results[renderer] = f"❌ Error: {e}"

print(results)
```

### Common Error Solutions

| Error | Solution |
|-------|----------|
| `WASM not supported` | Update browser or use `renderer_type="auto"` |
| `WebAssembly instantiation failed` | Check browser memory/security settings |
| `Worker initialization failed` | Disable ad blockers affecting Web Workers |
| `Cache quota exceeded` | Clear browser cache or reduce cache duration |

## 🧪 Testing WASM Performance

### Quick Performance Test
```python
import time
from marimo_openscad import openscad_viewer
from solid2 import cube, sphere, difference

# Test model
model = difference()(cube([20, 20, 20]), sphere(r=8))

# Test WASM performance
start = time.time()
wasm_viewer = openscad_viewer(model, renderer_type="wasm") 
wasm_time = time.time() - start
print(f"WASM render: {wasm_time*1000:.2f}ms")

# Test local performance (if available)
try:
    start = time.time()
    local_viewer = openscad_viewer(model, renderer_type="local")
    local_time = time.time() - start
    print(f"Local render: {local_time*1000:.2f}ms")
    print(f"Speed improvement: {local_time/wasm_time:.1f}x faster")
except:
    print("Local OpenSCAD not available")
```

## 📈 Performance Metrics

### Real-World Performance Data

Based on our comprehensive testing with `test_wasm_performance.py`:

- **Simple Models** (basic cube): WASM 0.5ms vs Local 163ms (326x faster)
- **Complex Models** (multi-operations): WASM 79ms vs Local 15,000ms (190x faster)  
- **Cache Benefits**: 35% improvement on subsequent renders
- **Memory Efficiency**: Supports 5+ concurrent viewers
- **Browser Compatibility**: 95%+ modern browsers supported

### Benchmark Results
```
🚀 WASM Performance Testing Suite
══════════════════════════════════════════════════════════════════════

📊 Model Complexity Performance:
   Simple Model:    0.5ms (WASM) vs 163ms (Local)
   Medium Model:    12ms (WASM) vs 1,200ms (Local)  
   Complex Model:   79ms (WASM) vs 15,000ms (Local)

🗄️ Cache Performance:
   Cold cache: 89ms | Warm cache: 58ms | 35% improvement

💾 Memory Efficiency:
   Concurrent viewers: 5+ | Automatic cleanup: 5min idle
   
🏆 Overall Assessment: 🎉 Performance optimizations working well!
```

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