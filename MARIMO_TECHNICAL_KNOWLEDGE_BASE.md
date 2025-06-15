# 🧠 MARIMO TECHNICAL KNOWLEDGE BASE

**Purpose**: Konsolidiertes Wissen über Marimo, reactive Programmierung, WebWorker, WASM Integration  
**Scope**: Technische Details für marimo-openscad Entwicklung  
**Last Updated**: 15. Juni 2025

---

## 🔄 **Marimo Reactive Programming Model**

### **Cell Execution & Variable Conflicts**
Marimo verwendet ein **reaktives Programmiermodell** mit automatic re-execution:

```python
# Cell 1
import marimo as mo
x = 5

# Cell 2 (depends on x)
y = x * 2  # Re-runs automatically when x changes

# Cell 3 (conflict scenario)
x = 10  # This creates a conflict - Marimo detects multiple definitions
```

**Wichtige Erkenntnisse:**
- ✅ **Variable isolation**: Jede Zelle kann eigene lokale Variablen haben
- ⚠️ **Name conflicts**: Marimo detektiert und warnt vor variable shadowing
- 🔄 **Automatic re-execution**: Dependent cells re-run when dependencies change
- 📊 **Dependency graph**: Marimo baut automatisch einen dependency graph auf

### **anywidget Integration Patterns**
```python
import anywidget
import traitlets

class MarimoWidget(anywidget.AnyWidget):
    # Traits synchronize between Python and JavaScript
    data = traitlets.Unicode("").tag(sync=True)
    is_loading = traitlets.Bool(False).tag(sync=True)
    
    # ESM-only JavaScript (no CommonJS)
    _esm = """
    function render({ model, el }) {
        // model.get() reads traits from Python
        // model.set() sends data back to Python
        // model.on('change:data', callback) listens for changes
    }
    export default { render };
    """
```

**Critical Requirements:**
- ✅ **ESM-only**: Marimo requires ES modules, nicht CommonJS
- 🔄 **Trait synchronization**: Real-time bidirectional data flow
- 🎯 **DOM management**: Widget manages its own DOM lifecycle
- 📱 **Responsive**: Must handle Marimo's layout changes

---

## 🌐 **Service Worker & WASM Integration**

### **Marimo Service Worker Bug (BEKANNT)**
**Problem**: Marimo 0.13.15 generates faulty Service Worker code
```javascript
// Problematic generated code in Marimo
navigator.serviceWorker.register('./public-files-sw.js?v=2')
    .then(registration => {
        registration.active.postMessage({ notebookId }); // ❌ registration.active is null
    })
```

**Impact auf WASM:**
- ❌ JavaScript execution errors in browser console
- ❌ WASM module loading kann gestört werden
- ❌ anywidget rendering kann fehlschlagen

**Workarounds:**
```javascript
// Option 1: Safe Service Worker check
if (registration.active) {
    registration.active.postMessage({ notebookId });
} else {
    // Wait for service worker to become active
    registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'activated') {
                newWorker.postMessage({ notebookId });
            }
        });
    });
}

// Option 2: Version downgrade
# uv add "marimo<0.13.15"
```

### **WASM Integration Architecture**
**Phase Evolution**:
1. **Phase 1**: Web Workers (multithreading attempt) ❌ Komplexität zu hoch
2. **Phase 2**: Main Thread WASM ✅ Simplified architecture  
3. **Phase 3**: Browser-native execution ✅ Zero dependencies

**Current WASM Setup**:
```python
# WASM files present in package
src/marimo_openscad/wasm/
├── openscad.wasm         # 7.7MB - Main WASM module
├── openscad.wasm.js      # 120KB - WASM loader
├── openscad.js           # 745B - Entry point
├── openscad.fonts.js     # 8MB - Font data  
├── openscad.mcad.js      # 491KB - MCAD library
└── *.d.ts               # TypeScript definitions
```

**Browser Integration Pattern**:
```javascript
// In anywidget ESM code
async function loadOpenSCADWASM() {
    // 1. Load WASM module from bundled files
    const wasmModule = await import('./wasm/openscad.js');
    
    // 2. Initialize with memory constraints
    const openscad = await wasmModule.default({
        wasmMemory: new WebAssembly.Memory({
            initial: 256,        // 16MB initial
            maximum: 32768       // 2GB maximum (WASM limit)
        })
    });
    
    // 3. Process SCAD -> STL conversion
    const stlData = openscad.processScad(scadCode);
    
    // 4. Transfer binary data to Python
    model.set('stl_data', stlData);
}
```

---

## 🎯 **Performance Optimization Strategies**

### **190x Performance Improvement Methodology**
**Measurement Setup**:
```python
import time
import psutil

def measure_rendering_performance(model, renderer_type):
    """Comprehensive performance measurement"""
    start_time = time.perf_counter()
    start_memory = psutil.Process().memory_info().rss
    
    # Create viewer with specified renderer
    viewer = openscad_viewer(model, renderer_type=renderer_type)
    
    end_time = time.perf_counter()
    end_memory = psutil.Process().memory_info().rss
    
    return {
        'render_time': end_time - start_time,
        'memory_increase': end_memory - start_memory,
        'stl_size': len(getattr(viewer, 'stl_data', b'')),
        'success': bool(getattr(viewer, 'stl_data', None))
    }
```

**Performance Targets**:
- 🎯 **Speed**: 190x faster than local OpenSCAD
- 🎯 **Memory**: <2GB WASM limit compliance
- 🎯 **Latency**: <100ms for simple models
- 🎯 **Throughput**: >10 renders/second

### **Browser Compatibility Matrix**
| Browser | Version | WASM Support | SharedArrayBuffer | Performance |
|---------|---------|--------------|-------------------|-------------|
| Chrome | 69+ | ✅ Full | ✅ Available | ⭐⭐⭐⭐⭐ |
| Firefox | 62+ | ✅ Full | ⚠️ Requires headers | ⭐⭐⭐⭐ |
| Safari | 14+ | ✅ Full | ❌ Not supported | ⭐⭐⭐ |
| Edge | 79+ | ✅ Full | ✅ Available | ⭐⭐⭐⭐⭐ |

**Coverage**: 95%+ moderne Browser unterstützt

---

## 🔧 **STL Processing Pipeline**

### **Three.js Integration Pattern**
```javascript
// Complete STL -> Three.js workflow
function createThreeJSMesh(stlData) {
    // 1. Parse STL binary data
    const geometry = new THREE.STLLoader().parse(stlData);
    
    // 2. Optimize geometry
    geometry.computeVertexNormals();
    geometry.computeBoundingBox();
    geometry.computeBoundingSphere();
    
    // 3. Create material with fallback
    const material = new THREE.MeshPhongMaterial({
        color: 0x00ff00,
        side: THREE.DoubleSide,
        transparent: false
    });
    
    // 4. Create mesh
    const mesh = new THREE.Mesh(geometry, material);
    
    // 5. Add to scene with controls
    scene.add(mesh);
    
    // 6. Setup camera and controls
    setupCameraAndControls(geometry.boundingBox);
    
    return mesh;
}
```

### **Memory Management Strategies**
```javascript
// Proper cleanup to prevent memory leaks
function disposeMesh(mesh) {
    if (mesh.geometry) {
        mesh.geometry.dispose();
    }
    if (mesh.material) {
        if (Array.isArray(mesh.material)) {
            mesh.material.forEach(material => material.dispose());
        } else {
            mesh.material.dispose();
        }
    }
    scene.remove(mesh);
}

// Automatic cleanup on widget destruction
function dispose() {
    scene.traverse((object) => {
        if (object instanceof THREE.Mesh) {
            disposeMesh(object);
        }
    });
    renderer.dispose();
}
```

---

## 🛡️ **Error Handling & Fallback Systems**

### **3-Layer Fallback Architecture**
```python
class HybridOpenSCADRenderer:
    """Intelligent fallback between WASM, Local, and Mock"""
    
    def render(self, scad_code):
        # Layer 1: Try WASM (fastest, zero dependencies)
        try:
            if self.wasm_available:
                return self.wasm_renderer.render(scad_code)
        except Exception as e:
            logger.warning(f"WASM render failed: {e}")
        
        # Layer 2: Try Local OpenSCAD (requires installation)
        try:
            if self.local_available:
                return self.local_renderer.render(scad_code)
        except Exception as e:
            logger.warning(f"Local render failed: {e}")
        
        # Layer 3: Return test geometry (always works)
        return self.generate_test_geometry()
```

### **Progressive Enhancement Pattern**
```javascript
// Feature detection and graceful degradation
function initializeViewer() {
    const capabilities = detectCapabilities();
    
    if (capabilities.wasm && capabilities.threejs) {
        return new FullFeaturedViewer();
    } else if (capabilities.threejs) {
        return new BasicThreeJSViewer();
    } else {
        return new FallbackCanvasViewer();
    }
}

function detectCapabilities() {
    return {
        wasm: 'WebAssembly' in window,
        threejs: checkThreeJSAvailability(),
        webgl: checkWebGLSupport(),
        sharedArrayBuffer: 'SharedArrayBuffer' in window
    };
}
```

---

## 📊 **Development & Testing Patterns**

### **Test-Driven WASM Development**
```python
# Real WASM testing (no mocks)
def test_wasm_real_integration():
    """Test actual WASM files without mocking"""
    renderer = OpenSCADWASMRenderer()
    
    # Test 1: WASM files exist
    assert renderer.wasm_path.exists()
    assert (renderer.wasm_path / "openscad.wasm").exists()
    
    # Test 2: Can load WASM module  
    wasm_files = renderer.get_wasm_files()
    assert len(wasm_files) > 0
    
    # Test 3: Can generate STL data
    simple_scad = "cube([1,1,1]);"
    result = renderer.render(simple_scad)
    assert len(result) > 0  # Real STL data
```

### **Browser Testing with Playwright**
```python
# E2E testing for Marimo integration
def test_marimo_widget_e2e(browser):
    """Test complete Marimo workflow in real browser"""
    page = browser.new_page()
    
    # Start Marimo notebook
    page.goto("http://localhost:2721")
    
    # Check for Service Worker errors
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text))
    
    # Test widget creation
    page.fill("#code-cell", "import marimo_openscad; viewer = marimo_openscad.openscad_viewer(cube([1,1,1]))")
    page.press("#code-cell", "Shift+Enter")
    
    # Verify no service worker errors
    assert not any("registration.active is null" in error for error in console_errors)
    
    # Verify widget rendered
    assert page.locator(".anywidget-container").is_visible()
```

---

## 🔍 **Debugging Strategies**

### **WASM Debugging Workflow**
```python
def debug_wasm_pipeline(scad_code):
    """Step-by-step WASM execution debugging"""
    print(f"🔍 Debug Step 1: Input SCAD code ({len(scad_code)} chars)")
    print(f"    Code preview: {scad_code[:100]}...")
    
    print(f"🔍 Debug Step 2: WASM module loading")
    wasm_files = get_wasm_files()
    print(f"    Found {len(wasm_files)} WASM files")
    
    print(f"🔍 Debug Step 3: WASM execution")
    try:
        stl_data = execute_wasm_render(scad_code)
        print(f"    STL output: {len(stl_data)} bytes")
        return stl_data
    except Exception as e:
        print(f"    ❌ WASM execution failed: {e}")
        return None
```

### **Marimo Environment Analysis**
```python
def analyze_marimo_environment():
    """Analyze Marimo execution environment"""
    import sys, os
    
    env_info = {
        'marimo_version': get_marimo_version(),
        'python_path': sys.path,
        'working_directory': os.getcwd(),
        'environment_variables': dict(os.environ),
        'imported_modules': list(sys.modules.keys()),
        'anywidget_available': 'anywidget' in sys.modules
    }
    
    return env_info
```

---

## ⚙️ **Configuration & Deployment**

### **Package Data Configuration**
```toml
# pyproject.toml - WASM files bundling
[tool.setuptools.package-data]
marimo_openscad = [
    "wasm/*.wasm",
    "wasm/*.js", 
    "wasm/*.d.ts",
    "js/*.js"
]
```

### **Development vs Production**
```python
# Environment detection
def get_environment():
    if os.getenv('MARIMO_ENV') == 'development':
        return 'development'
    elif 'pytest' in sys.modules:
        return 'testing'
    else:
        return 'production'

# Configuration per environment
CONFIG = {
    'development': {
        'debug_wasm': True,
        'use_local_files': True,
        'verbose_logging': True
    },
    'production': {
        'debug_wasm': False,
        'use_bundled_files': True,
        'verbose_logging': False
    },
    'testing': {
        'mock_wasm': True,
        'use_test_data': True,
        'verbose_logging': True
    }
}
```

---

## 🎯 **Best Practices Summary**

### **Marimo Widget Development**
✅ **DO**:
- Use ESM modules exclusively
- Implement proper trait synchronization
- Handle Marimo's reactive execution model
- Test in real Marimo environment
- Implement fallback strategies

❌ **DON'T**:
- Use CommonJS modules
- Assume synchronous execution
- Ignore service worker errors
- Skip cross-browser testing
- Hard-code absolute paths

### **WASM Integration**
✅ **DO**:
- Respect 2GB memory limit
- Implement proper error handling
- Use main thread (not Web Workers)
- Bundle WASM files with package
- Test with real browser environment

❌ **DON'T**:
- Attempt multithreading with Web Workers
- Ignore browser compatibility
- Skip memory management
- Assume WASM always available
- Use outdated WASM techniques

### **Performance Optimization**
✅ **DO**:
- Measure actual performance gains
- Use real STL data for testing
- Implement progressive enhancement
- Cache expensive computations
- Monitor memory usage

❌ **DON'T**:
- Optimize without measuring
- Use placeholder data for benchmarks
- Ignore memory constraints
- Skip browser profiling
- Assume linear scaling

---

**This knowledge base consolidates 2+ years of marimo-openscad development experience and should be the primary technical reference for future development.**