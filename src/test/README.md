# Test Directory

This directory contains test files for the JavaScript widget component.

## Files

- **`setup.js`** - Test environment setup with Three.js mocks and browser API polyfills
- **`widget.test.js`** - Basic test examples (needs expansion)

## Running Tests

```bash
# Install dependencies first
npm install

# Run tests
npm run test

# Run in watch mode for development
npm run test:watch

# Run with coverage report
npm run test -- --coverage

# Run with UI (browser-based test runner)
npm run test:ui
```

## Current Test Coverage

The existing tests provide basic examples for:
- Widget initialization
- Model trait handling
- Cleanup function verification

## Areas Needing Test Coverage

1. **STL Parser**
   - Binary STL parsing with various face counts
   - ASCII STL parsing with different formats
   - Error handling for malformed STL data
   - Edge cases (empty files, large files)

2. **Scene Manager**
   - Three.js scene initialization
   - Camera controls (mouse interactions)
   - Mesh loading and disposal
   - Lighting setup
   - Resize handling

3. **Widget Integration**
   - Full widget lifecycle
   - Model synchronization
   - Error state handling
   - Resource cleanup

4. **Performance Tests**
   - Large STL file handling
   - Memory leak detection
   - Rapid model updates

## Test Data

Sample STL files and test data generators should be added for comprehensive testing.

## Mocking Strategy

The test environment uses comprehensive mocks for:
- Three.js classes and constants
- DOM APIs (atob, btoa, performance)
- Browser APIs (requestAnimationFrame)

This allows tests to run in Node.js environment without requiring actual WebGL support.