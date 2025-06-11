# OpenSCAD WASM Migration Plan

## Overview
This document outlines the comprehensive plan to migrate from local OpenSCAD executable dependency to a WebAssembly (WASM) based solution. This migration will enable browser-native 3D modeling without requiring local OpenSCAD installation.

## Current Architecture vs Target Architecture

### Current (Local OpenSCAD)
```
SolidPython2 → OpenSCAD CLI → STL Binary → Base64 → Three.js → WebGL
                    ↑
            Requires local installation
```

### Target (WASM OpenSCAD)
```
SolidPython2 → OpenSCAD WASM → STL Binary → Base64 → Three.js → WebGL
                    ↑
            Runs entirely in browser
```

## Research Findings

### OpenSCAD WASM Availability
- **Official Project**: `openscad/openscad-wasm` on GitHub
- **Status**: Active development with recent releases
- **API**: ES6 module with Emscripten filesystem
- **Features**: Full OpenSCAD functionality in browser
- **Performance**: Functional but noted as slower than native

### Integration Compatibility
- **Marimo**: Native WASM notebook support
- **Anywidget**: Compatible with WASM applications
- **Three.js**: Already used for 3D rendering
- **Workflow**: SolidPython2 → WASM fits existing pipeline

## Migration Phases

### Phase 1: WASM Integration Foundation (Week 1-2)
**Objective**: Establish WASM OpenSCAD loading and basic functionality

#### 1.1 WASM Module Integration
- [ ] Add OpenSCAD WASM as npm dependency or CDN resource
- [ ] Create WASM loader utility in JavaScript
- [ ] Implement WASM instance management
- [ ] Add error handling for WASM initialization

#### 1.2 Basic WASM Renderer
- [ ] Create `OpenSCADWASMRenderer` class
- [ ] Implement file system operations (writeFile/readFile)
- [ ] Add SCAD code execution via `callMain()`
- [ ] Implement STL output retrieval

#### 1.3 Testing Infrastructure
- [ ] Add WASM-specific test fixtures
- [ ] Mock WASM module for CI/CD
- [ ] Create integration tests for WASM renderer
- [ ] Performance benchmarking setup

### Phase 2: Widget Integration (Week 3-4)
**Objective**: Integrate WASM renderer with existing anywidget infrastructure

#### 2.1 Widget Architecture Update
- [ ] Extend `OpenSCADViewer` for WASM support
- [ ] Add `renderer_type` parameter (`"local"` | `"wasm"`)
- [ ] Implement renderer factory pattern
- [ ] Maintain backward compatibility

#### 2.2 JavaScript Widget Enhancement
- [ ] Add WASM loading logic to `widget.js`
- [ ] Implement loading states and progress indicators
- [ ] Add WASM initialization error handling
- [ ] Optimize for web worker usage

#### 2.3 Marimo Integration
- [ ] Test WASM renderer in marimo notebooks
- [ ] Optimize for marimo's reactive execution
- [ ] Add marimo-specific configuration options
- [ ] Ensure compatibility with marimo WASM notebooks

### Phase 3: Performance & User Experience (Week 5-6)
**Objective**: Optimize performance and enhance user experience

#### 3.1 Performance Optimization
- [ ] Implement WASM module caching
- [ ] Add web worker support for non-blocking rendering
- [ ] Optimize memory management
- [ ] Implement progressive rendering for complex models

#### 3.2 Enhanced Features
- [ ] Add OpenSCAD library support (MCAD, fonts)
- [ ] Implement real-time parameter updates
- [ ] Add WASM-specific configuration options
- [ ] Enhanced error reporting and debugging

#### 3.3 Fallback Strategy
- [ ] Implement automatic fallback to local OpenSCAD
- [ ] Add user preference for renderer selection
- [ ] Smart detection of WASM support
- [ ] Graceful degradation for unsupported browsers

### Phase 4: Production Ready (Week 7-8)
**Objective**: Prepare for production deployment

#### 4.1 Documentation & Examples
- [ ] Update README with WASM instructions
- [ ] Create WASM-specific examples
- [ ] Add migration guide from local to WASM
- [ ] Performance comparison documentation

#### 4.2 CI/CD & Distribution
- [ ] Add WASM tests to CI pipeline
- [ ] Update build process for WASM assets
- [ ] Configure CDN distribution for WASM files
- [ ] Add browser compatibility testing

#### 4.3 Migration Strategy
- [ ] Feature flag for WASM renderer
- [ ] User migration path documentation
- [ ] Deprecation timeline for local dependency
- [ ] Community feedback integration

## Technical Implementation Details

### WASM Module Loading
```javascript
import OpenSCAD from "./openscad.js";
import { addFonts } from "./openscad.fonts.js";
import { addMCAD } from "./openscad.mcad.js";

class OpenSCADWASMRenderer {
    async initialize() {
        this.instance = await OpenSCAD({noInitialRun: true});
        await addFonts(this.instance);
        await addMCAD(this.instance);
    }

    async render(scadCode) {
        const filename = `output_${Date.now()}.stl`;
        this.instance.FS.writeFile("/input.scad", scadCode);
        this.instance.callMain([
            "/input.scad",
            "--enable=manifold",
            "-o",
            `/${filename}`
        ]);
        return this.instance.FS.readFile(`/${filename}`);
    }
}
```

### Widget Integration Pattern
```python
class OpenSCADViewer(anywidget.AnyWidget):
    def __init__(self, renderer_type="auto", **kwargs):
        self.renderer_type = renderer_type
        self.renderer = self._create_renderer()
        super().__init__(**kwargs)
    
    def _create_renderer(self):
        if self.renderer_type == "wasm":
            return OpenSCADWASMRenderer()
        elif self.renderer_type == "local":
            return OpenSCADRenderer()
        else:  # auto
            return self._detect_best_renderer()
```

### Web Worker Integration
```javascript
// openscad-worker.js
importScripts('./openscad.js');

self.onmessage = async function(e) {
    const { scadCode, options } = e.data;
    try {
        const instance = await OpenSCAD({noInitialRun: true});
        // ... rendering logic
        self.postMessage({ success: true, data: stlData });
    } catch (error) {
        self.postMessage({ success: false, error: error.message });
    }
};
```

## Benefits of WASM Migration

### For Users
- **No Installation Required**: Works in any modern browser
- **Faster Setup**: Immediate availability without dependencies  
- **Cross-Platform**: Consistent behavior across all platforms
- **Offline Capable**: Can work without internet after initial load
- **Shareable**: Models can be shared as web links

### For Developers
- **Simplified Distribution**: No OpenSCAD installation instructions
- **Better CI/CD**: No dependency management in build systems
- **Enhanced Integration**: Native web technology stack
- **Future-Proof**: Aligns with web-first development trends

### For the Project
- **Lower Barrier to Entry**: Easier user onboarding
- **Broader Compatibility**: Works in more environments
- **Modern Architecture**: Web-native approach
- **Community Growth**: Easier contribution and adoption

## Risks and Mitigation

### Performance Concerns
- **Risk**: WASM may be slower than native OpenSCAD
- **Mitigation**: Implement web workers, caching, and progressive rendering

### Browser Compatibility
- **Risk**: WASM not supported in older browsers
- **Mitigation**: Maintain fallback to local renderer

### File Size
- **Risk**: WASM module may be large
- **Mitigation**: Lazy loading, CDN distribution, compression

### Debugging Complexity
- **Risk**: WASM debugging more complex than local execution
- **Mitigation**: Enhanced error reporting, debugging tools

## Success Metrics

- [ ] WASM renderer passes all existing tests
- [ ] Performance within 2x of local renderer
- [ ] Compatible with 95%+ of target browsers
- [ ] User onboarding time reduced by 50%
- [ ] Zero local dependency installation required
- [ ] Maintains feature parity with local renderer

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 2 weeks | WASM integration foundation |
| Phase 2 | 2 weeks | Widget integration complete |
| Phase 3 | 2 weeks | Performance optimized |
| Phase 4 | 2 weeks | Production ready |
| **Total** | **8 weeks** | **Full WASM migration** |

## Next Steps

1. **Immediate (Next 1-2 days)**:
   - Research OpenSCAD WASM API in detail
   - Set up development environment with WASM module
   - Create proof-of-concept WASM renderer

2. **Short Term (Next week)**:
   - Begin Phase 1 implementation
   - Update project roadmap with WASM timeline
   - Communicate migration plan to stakeholders

3. **Medium Term (Next month)**:
   - Complete Phases 1-2
   - Begin user testing with WASM renderer
   - Gather performance metrics and feedback

This migration represents a significant architectural improvement that will modernize the project and dramatically improve user experience by eliminating local dependencies while maintaining full OpenSCAD functionality.