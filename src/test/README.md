# JavaScript Test Directory

## ⚠️ **CRITICAL WARNING: EXTENSIVE MOCKING**

**🚨 IMPORTANT**: This directory contains tests that use **comprehensive mocking** of browser APIs. These tests provide CI/CD stability but **DO NOT validate real browser functionality**.

### **Current Mock Implementation Status:**
- ✅ **CI/CD Stable**: All tests pass in Node.js environment
- ❌ **Real Validation**: Browser APIs are completely mocked
- 🎯 **Target**: Replace with real browser testing (Playwright/Selenium)

This directory contains test files for the JavaScript widget component.

## Files

- **`setup.js`** - ⚠️ **TEMPORARY MOCK IMPLEMENTATION** - Comprehensive browser API mocking
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

## ⚠️ **TEMPORARY MOCKING STRATEGY**

**CRITICAL WARNING**: The test environment uses **extensive mocking** that **MUST be removed** before production:

### **Current Mocks (setup.js):**
```javascript
// ⚠️ TEMPORARY - REMOVE AFTER REAL IMPLEMENTATION
global.THREE = { /* Complete Three.js mock */ };
global.WebAssembly = { /* Full WASM API simulation */ };
global.HTMLCanvasElement = { /* Canvas/WebGL mock */ };
global.Worker = { /* Web Worker simulation */ };
global.fetch = { /* Module loading mock */ };
global.ResizeObserver = { /* Responsive behavior mock */ };
// + atob, btoa, performance, requestAnimationFrame...
```

### **What These Mocks Provide:**
- ✅ **CI/CD Stability**: Tests pass in Node.js without browser
- ✅ **Development Velocity**: Fast test execution
- ✅ **Cross-Platform**: Works on all CI environments

### **What These Mocks Hide:**
- ❌ **Real WASM loading failures**
- ❌ **Canvas rendering issues**
- ❌ **WebGL compatibility problems**
- ❌ **Memory management failures**
- ❌ **Browser-specific bugs**
- ❌ **Performance bottlenecks**

### **MOCK REMOVAL REQUIREMENTS:**
1. **Replace with Playwright E2E tests**
2. **Test in real browser environments**
3. **Validate actual WASM performance**
4. **Cross-browser compatibility testing**
5. **Remove all global.* assignments**

This **temporary approach** allows tests to run in Node.js environment without requiring actual WebGL support, but **does not validate real functionality**.