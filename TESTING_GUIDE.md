# Testing Guide for Marimo-OpenSCAD Widget

## Overview

This document provides comprehensive information for writing tests for the JavaScript widget component of the Marimo-OpenSCAD project.

## Project Structure

```
marimo-openscad-clean/
├── src/
│   ├── js/
│   │   └── widget.js           # Main widget implementation
│   └── test/
│       ├── setup.js            # Test environment setup
│       └── widget.test.js      # Basic test examples
├── package.json                # Dependencies and test scripts
├── vitest.config.js           # Test framework configuration
└── public/index.html          # Development test page
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

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test -- --coverage
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

Aim for comprehensive coverage of:
- All public methods and functions
- Error handling paths
- Edge cases (empty data, malformed STL, etc.)
- Resource cleanup
- Event handling

## Performance Considerations

Test scenarios should include:
- Large STL files (1MB+)
- Rapid model updates
- Memory usage patterns
- Cleanup verification

## Additional Resources

- **Vitest Documentation**: https://vitest.dev/
- **Three.js Documentation**: https://threejs.org/docs/
- **anywidget Documentation**: https://anywidget.dev/
- **STL Format Specification**: Binary and ASCII format details