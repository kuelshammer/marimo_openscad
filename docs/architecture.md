# Architecture Overview

## System Architecture

The Marimo-OpenSCAD integration implements a reactive 3D CAD pipeline that converts SolidPython2 objects into interactive WebGL visualizations.

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

## Core Components

### 1. SolidPython2 Interface

**Purpose**: Provides Pythonic API for 3D modeling
**Technology**: SolidPython2 library
**Responsibilities**:
- Define 3D geometry using Python syntax
- Generate OpenSCAD code via `as_scad()` method
- Support constructive solid geometry operations

**Example**:
```python
from solid2 import cube, cylinder
model = cube(20) - cylinder(r=5, h=25, center=True)
scad_code = model.as_scad()  # Generate OpenSCAD code
```

### 2. OpenSCAD Execution Engine

**Purpose**: Converts OpenSCAD code to STL mesh data
**Technology**: OpenSCAD command-line interface
**Responsibilities**:
- Execute OpenSCAD code in headless mode
- Generate binary STL files
- Handle OpenSCAD errors and timeouts

**Implementation**: `OpenSCADRenderer` class
- Manages temporary files for OpenSCAD execution
- Provides cross-platform OpenSCAD discovery
- Implements caching for performance

### 3. STL Processing Pipeline

**Purpose**: Convert STL binary data for web transmission
**Technology**: Python base64 encoding + JavaScript binary parsing
**Responsibilities**:
- Encode STL binary data as base64 for transmission
- Parse STL format in JavaScript
- Convert to Three.js BufferGeometry

**STL Format Structure**:
```
[80-byte header] [4-byte triangle count] [triangle data...]

Each triangle (50 bytes):
- 12 bytes: normal vector (3 × float32)
- 36 bytes: vertices (9 × float32)
- 2 bytes: attribute byte count
```

### 4. anywidget Integration

**Purpose**: Bridge between Python and JavaScript in Marimo
**Technology**: anywidget framework with ESM modules
**Responsibilities**:
- Synchronize Python data with JavaScript
- Handle bidirectional communication
- Manage widget lifecycle

**Trait System**:
```python
class InteractiveViewer(anywidget.AnyWidget):
    stl_data = traitlets.Unicode(default_value="").tag(sync=True)
    
    def update_model(self, model):
        stl_bytes = self.bridge.render_to_stl(model)
        self.stl_data = base64.b64encode(stl_bytes).decode('utf-8')
```

### 5. Three.js Rendering Engine

**Purpose**: Hardware-accelerated 3D rendering in browser
**Technology**: Three.js WebGL library
**Responsibilities**:
- Parse STL data into BufferGeometry
- Implement camera controls (orbit, zoom)
- Manage lighting and materials
- Handle progressive fallbacks

**Rendering Pipeline**:
```javascript
// 1. Parse STL binary data
const geometry = parseSTL(base64Data);

// 2. Create mesh with material
const material = new THREE.MeshPhongMaterial({color: 0x8B4513});
const mesh = new THREE.Mesh(geometry, material);

// 3. Setup scene and camera
scene.add(mesh);
camera.position.set(x, y, z);

// 4. Render loop
function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
```

### 6. Marimo Reactive System

**Purpose**: Automatic dependency tracking and updates
**Technology**: Marimo's static analysis and reactive execution
**Responsibilities**:
- Track dependencies between cells
- Trigger automatic updates when parameters change
- Maintain consistent notebook state

**Reactive Flow**:
```python
# Cell 1: Parameters
height = mo.ui.slider(10, 100, value=50)

# Cell 2: Model (depends on height)
model = cube([20, 20, height.value])

# Cell 3: Viewer (depends on model)
viewer.update_model(model)  # Automatically updates when height changes
```

## Data Flow

### 1. Parameter Update Flow

```
User moves slider → Marimo detects change → Model cell re-executes → 
Viewer cell re-executes → STL regenerated → JavaScript receives new data → 
3D view updates
```

### 2. STL Generation Flow

```
SolidPython2 object → .as_scad() → OpenSCAD code → 
OpenSCAD CLI execution → Binary STL file → 
Base64 encoding → anywidget trait update → 
JavaScript receives data
```

### 3. 3D Rendering Flow

```
Base64 STL data → atob() decode → Uint8Array → 
DataView parsing → Float32Array vertices → 
Three.js BufferGeometry → WebGL rendering
```

## Error Handling Strategy

### Progressive Fallback System

1. **Primary**: Parse and render actual STL data
2. **Secondary**: Show procedural geometry if STL parsing fails
3. **Tertiary**: Display colored test cube if all else fails

```javascript
if (stlData && stlData.length > 100) {
    try {
        const geometry = parseSTL(stlData);
        renderSTLMesh(geometry);
    } catch (error) {
        createProceduralFallback();
    }
} else {
    createTestCube();
}
```

### Error Types and Handling

| Error Type | Component | Recovery Strategy |
|------------|-----------|-------------------|
| OpenSCAD not found | OpenSCADRenderer | Provide installation instructions |
| Invalid SolidPython2 object | SolidPythonBridge | Show error message, keep previous model |
| STL parsing failure | JavaScript | Fall back to procedural geometry |
| Three.js load failure | anywidget | Show error message with troubleshooting |
| WebGL not supported | Browser | Graceful degradation message |

## Performance Optimizations

### 1. Model Caching

**Implementation**: Hash-based caching in `SolidPythonBridge`
```python
def _hash_scad_code(self, scad_code: str) -> str:
    hasher = hashlib.md5()
    hasher.update(scad_code.encode('utf-8'))
    return hasher.hexdigest()
```

**Benefits**:
- Avoid re-rendering identical models
- Faster parameter updates
- Reduced OpenSCAD execution time

### 2. Triangle Limiting

**Implementation**: Limit STL models to 2000 triangles
```javascript
const maxTriangles = Math.min(triangleCount, 2000);
```

**Benefits**:
- Consistent browser performance
- Prevent memory exhaustion
- Smooth interaction on low-end devices

### 3. Lazy Loading

**Implementation**: Load Three.js only when needed
```javascript
const script = document.createElement('script');
script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
script.onload = () => initViewer();
```

**Benefits**:
- Faster initial page load
- Reduced bandwidth usage
- Better user experience

## Browser Compatibility

### Requirements

- **WebGL**: Hardware-accelerated 3D rendering
- **ES6 Modules**: Modern JavaScript features
- **WebAssembly**: Future expansion capability
- **Typed Arrays**: Efficient binary data handling

### Supported Browsers

| Browser | Minimum Version | Notes |
|---------|----------------|-------|
| Chrome | 57+ | Full support, best performance |
| Firefox | 52+ | Full support |
| Safari | 11+ | Full support |
| Edge | 79+ | Full support (Chromium-based) |

### Feature Detection

```javascript
// Check WebGL support
const canvas = document.createElement('canvas');
const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
if (!gl) {
    showWebGLUnsupportedMessage();
}
```

## Security Considerations

### 1. OpenSCAD Execution

- OpenSCAD runs as subprocess with timeout
- Temporary files are cleaned up automatically
- No user input is directly passed to shell

### 2. JavaScript Execution

- Three.js loaded from trusted CDN
- No eval() or dynamic code execution
- STL parsing uses typed arrays for safety

### 3. Data Transmission

- Base64 encoding prevents binary data issues
- No sensitive data transmitted to browser
- All processing happens locally

## Future Architecture Considerations

### WebAssembly Integration

**Goal**: Run OpenSCAD directly in browser
**Benefits**:
- Eliminate server dependency
- Faster rendering with Manifold engine
- Better offline capabilities

**Implementation Plan**:
```javascript
// Future WebAssembly integration
const wasmModule = await OpenSCAD.initialize();
const stlBuffer = wasmModule.render(scadCode, parameters);
const geometry = parseSTLBuffer(stlBuffer);
```

### Progressive Web App

**Goal**: Standalone web application
**Benefits**:
- Offline functionality
- Native app-like experience
- Push notifications for render completion

### Advanced 3D Features

**Planned Enhancements**:
- Multi-material support
- Animation system
- Section views and measurements
- Real-time collaboration