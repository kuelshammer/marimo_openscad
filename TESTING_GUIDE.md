# Testing Guide for Marimo-OpenSCAD Widget

## Overview

This document provides comprehensive information for testing both the JavaScript widget component and Python backend of the Marimo-OpenSCAD project.

**⚠️ CRITICAL:** This project includes specific tests for cache behavior issues identified by external LLM analysis. These tests are essential for preventing regression of the `update_scad_code` functionality.

## Project Structure

```
marimo-openscad-clean/
├── src/
│   ├── js/
│   │   └── widget.js           # Main widget implementation
│   ├── marimo_openscad/        # Python backend
│   │   ├── viewer.py           # Main viewer classes
│   │   ├── solid_bridge.py     # SolidPython2 integration
│   │   └── interactive_viewer.py # Interactive widget
│   └── test/
│       ├── setup.js            # JS test environment setup
│       └── widget.test.js      # Basic JS test examples
├── tests/                      # Python tests
│   ├── test_cache_behavior.py  # 🔥 CRITICAL: Cache fix tests
│   ├── test_llm_identified_issues.py # LLM-specific regression tests
│   ├── test_viewer_integration.py # Integration tests
│   └── conftest.py             # Pytest configuration
├── .github/workflows/test.yml  # CI/CD pipeline
├── Makefile                    # Development commands
├── package.json                # JS dependencies
├── pytest.ini                 # Python test config
└── pyproject.toml             # Python package config
```

## Widget Architecture

### Main Components

The widget consists of several key classes and functions:

#### 1. `STLParser` class
- **Purpose**: Parses both binary and ASCII STL file formats
- **Methods**:
  - `parseSTL(data)` - Auto-detects format and delegates to appropriate parser
  - `parseBinary(data)` - Handles binary STL format (DataView based)
  - `parseASCII(data)` - Handles ASCII STL format (text parsing)
- **Returns**: `{ vertices: Float32Array, normals: Float32Array }`

#### 2. `SceneManager` class
- **Purpose**: Manages Three.js scene, camera, renderer, and user interactions
- **Key Methods**:
  - `init()` - Sets up Three.js scene with lighting, camera, renderer
  - `setupLighting()` - Configures ambient and directional lights
  - `setupGrid()` - Adds grid helper to scene
  - `setupControls()` - Mouse/wheel event handlers for camera control
  - `loadSTLData(stlData)` - Creates mesh from STL data and adds to scene
  - `clearMesh()` - Removes current mesh and cleans up resources
  - `resize()` - Handles window/container resize events
  - `dispose()` - Cleanup method for proper resource disposal

#### 3. `render({ model, el })` function
- **Purpose**: Main anywidget entry point
- **Parameters**:
  - `model` - anywidget model with traits (stl_data, error_message, is_loading)
  - `el` - DOM element to render widget into
- **Returns**: Cleanup function for widget disposal

### Widget State Management

The widget synchronizes with Python backend through these traits:
- `stl_data` (string) - Base64 encoded STL file data
- `error_message` (string) - Error messages from backend
- `is_loading` (boolean) - Loading state indicator

### Event Handling

The widget responds to:
- Model trait changes (stl_data, error_message, is_loading)
- Mouse interactions (drag to rotate, wheel to zoom)
- Window resize events

## Test Environment Setup

### Dependencies

Tests use Vitest with the following setup:
- **Test Framework**: Vitest (Jest-compatible API)
- **DOM Environment**: happy-dom (lightweight DOM implementation)
- **Mocking**: vi (Vitest's mocking utilities)
- **Three.js Mocking**: Custom mocks in `setup.js`

### Available Mocks

The test environment provides mocks for:
- **Three.js classes**: Scene, Camera, Renderer, Geometry, Material, Mesh, etc.
- **DOM APIs**: atob/btoa for base64, performance, requestAnimationFrame
- **Browser APIs**: Basic implementations for testing

## Testing Scenarios to Cover

### 1. Widget Initialization
- Container HTML creation
- SceneManager initialization
- Event listener registration
- Initial state handling

### 2. STL Parser Testing
- Binary STL parsing (different face counts, edge cases)
- ASCII STL parsing (various formats, malformed data)
- Error handling for corrupted files
- Performance with large STL files

### 3. SceneManager Functionality
- Three.js scene setup (camera, lights, renderer)
- Mouse control interactions
- STL data loading and mesh creation
- Resource cleanup and disposal
- Resize handling

### 4. Model Synchronization
- Trait change handling (stl_data updates)
- Error state management
- Loading state indicators
- Event listener cleanup

### 5. Integration Testing
- Full widget lifecycle (init → load data → cleanup)
- Multiple STL data updates
- Error recovery scenarios
- Memory leak prevention

## Sample Test Data

### Binary STL Format
```javascript
// Minimal valid binary STL (84 bytes)
const createTestSTL = (faceCount = 0) => {
    const header = new ArrayBuffer(80);  // 80-byte header
    const faceData = new ArrayBuffer(4); // 4-byte face count
    const faceCountView = new DataView(faceData);
    faceCountView.setUint32(0, faceCount, true);
    
    const combined = new ArrayBuffer(84);
    const view = new Uint8Array(combined);
    view.set(new Uint8Array(header), 0);
    view.set(new Uint8Array(faceData), 80);
    
    return combined;
};
```

### ASCII STL Format
```javascript
const asciiSTL = `solid test
facet normal 0 0 1
  outer loop
    vertex 0 0 0
    vertex 1 0 0
    vertex 0 1 0
  endloop
endfacet
endsolid test`;
```

## Test Commands

### Python Tests (Backend)

```bash
# Run all Python tests
make test

# 🔥 CRITICAL: Run cache behavior tests (prevents LLM-identified regression)
make test-cache-behavior

# Run regression tests for LLM-identified issues
make test-regression

# Run integration tests
make test-integration

# Run LLM-specific issue tests
make test-llm-issues

# Run with coverage
make test-coverage

# Quick validation (fast subset)
make validate
```

### JavaScript Tests (Frontend)

```bash
# Run all JS tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test -- --coverage
```

### Combined Tests

```bash
# Run both Python and JavaScript tests
make test-all

# Full CI-like test suite
make test-ci
```

## Example Test Structure

```javascript
describe('Widget Component', () => {
    let mockModel, mockEl;
    
    beforeEach(() => {
        // Setup mocks
    });
    
    it('should initialize properly', () => {
        // Test initialization
    });
    
    it('should handle STL data changes', () => {
        // Test model synchronization
    });
    
    it('should cleanup resources', () => {
        // Test proper disposal
    });
});
```

## Coverage Goals

### Python Backend Coverage
Aim for comprehensive coverage of:
- **Cache behavior** (CRITICAL - prevents regression)
- `update_scad_code()` functionality
- `update_model()` with different parameters
- Cache invalidation scenarios
- Force rendering options
- Error handling paths
- STL generation pipeline

### JavaScript Frontend Coverage
Aim for comprehensive coverage of:
- All public methods and functions
- STL parsing (binary/ASCII)
- Three.js scene management
- Error handling paths
- Edge cases (empty data, malformed STL, etc.)
- Resource cleanup
- Event handling

## Performance Considerations

### Python Backend Performance
- Cache hit/miss ratios
- STL generation time
- Memory usage with large models
- Cache memory consumption

### JavaScript Frontend Performance  
- Large STL files (1MB+)
- Rapid model updates
- Three.js scene complexity
- Memory usage patterns
- Cleanup verification

### Cache Performance (Critical)
- Ensure cache fixes don't cause performance regression
- Monitor cache memory usage
- Test cache effectiveness with various model types
- Validate force-render performance impact

## Critical Test Categories

### 🔥 Cache Behavior Tests (`test_cache_behavior.py`)
**Purpose**: Prevent regression of the LLM-identified cache issue where `update_scad_code` doesn't update visual display.

**Key Test Cases**:
- Cache invalidation with different SCAD code
- Cache invalidation with different parameters  
- Cache bypass functionality
- Force rendering options
- Cache clearing effectiveness

### 🎯 LLM Regression Tests (`test_llm_identified_issues.py`)
**Purpose**: Directly test the specific scenarios that failed in external LLM analysis.

**Key Test Cases**:
- Cube-to-sphere SCAD code updates produce different output
- Mock content changes appear in HTML output
- SCAD code property vs HTML output consistency
- End-to-end update workflows

### 🔗 Integration Tests (`test_viewer_integration.py`)
**Purpose**: Test complete workflows and ensure all reported-working functionality continues to work.

**Key Test Cases**:
- Viewer size customization
- Error message handling
- File format support (STL, OBJ, SVG, DXF)
- Case-insensitive file extensions
- Performance and memory usage

## CI/CD Integration

The GitHub Actions workflow (`.github/workflows/test.yml`) automatically runs:
1. **Cache behavior tests** (critical for preventing regression)
2. **LLM regression tests** (ensures identified issues stay fixed)
3. **Integration tests** (ensures overall functionality)
4. **Coverage reporting** (maintains code quality)

## Additional Resources

- **Vitest Documentation**: https://vitest.dev/
- **Three.js Documentation**: https://threejs.org/docs/
- **anywidget Documentation**: https://anywidget.dev/
- **pytest Documentation**: https://docs.pytest.org/
- **STL Format Specification**: Binary and ASCII format details
- **SolidPython2**: https://github.com/jeff-dh/SolidPython2