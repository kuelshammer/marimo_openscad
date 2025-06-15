# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Marimo-OpenSCAD is an interactive 3D CAD modeling widget for Marimo notebooks that enables parametric 3D design with WebAssembly-powered browser-native rendering. It integrates SolidPython2 with OpenSCAD through a dual-renderer system (WASM + local fallback).

## Memories

- Beachte die Planungsdatei: `CSG_RENDERING_ROADMAP.md`

## ⚠️ **CRITICAL DEVELOPMENT WARNING**

### 🚨 **TEMPORARY MOCK IMPLEMENTATION IN PLACE**

**IMPORTANT**: The current codebase contains **extensive mocking** for CI/CD stability that **MUST be addressed**:

#### **Mock Locations:**
- `src/test/setup.js` - **Full browser API mocking** (WebAssembly, Canvas, Worker, etc.)
- `pytest.ini` - Updated with all marker definitions (fixed)
- Multiple test files using mocked WASM/browser functionality

#### **Development Priority:**
1. 🔥 **HIGH**: Implement real WASM renderer to replace mocks
2. 🚀 **MEDIUM**: Add Playwright E2E tests for real browser validation  
3. 🎯 **LOW**: Remove all temporary mocks after real implementation

#### **Before Production Deployment:**
- [ ] Remove all `global.*` assignments in `src/test/setup.js`
- [ ] Implement real WebAssembly integration
- [ ] Add real browser testing with Playwright
- [ ] Validate actual performance claims (190x)

## Development Commands

### Python Testing
```bash
# Install development dependencies
make install-dev

# Run all Python tests
make test-python

# 🔥 CRITICAL: Cache behavior tests (prevents LLM-identified regression)
make test-cache

# LLM regression tests (for cache fix validation)
make test-regression

# Integration tests
make test-integration

# Test coverage
make test-coverage

# Quick validation
make validate
```

### JavaScript Testing
```bash
# ⚠️ CURRENT: Uses extensive mocking (TEMPORARY)
npm test

# Run in watch mode  
npm run test:watch

# With coverage
npm run test:coverage

# WASM-specific tests (MOCKED)
npm run test:wasm

# CI-compatible test with JUnit XML (uses mocks)
npm run test:ci
```

### 🚨 **Mock Identification Commands**
```bash
# Find all mock implementations
grep -r "Mock" src/test/
grep -r "global\." src/test/setup.js

# Check for test mode indicators
grep -r "Running in test mode" src/

# Verify real vs mocked components
grep -r "WebAssembly" src/test/setup.js  # Should show mocked implementation
```

### Build Commands
```bash
# Build Python package
python -m build

# Build JavaScript widget
npm run build

# Build with WASM optimization
npm run build:wasm

# Production build
npm run build:production
```

### Linting and Formatting
```bash
# Python
make lint      # flake8, mypy
make format    # black, isort

# JavaScript
npm run lint   # eslint
npm run format # prettier
```

## Architecture

### Core Components

**Python Backend (src/marimo_openscad/)**:
- `viewer.py` - Main `openscad_viewer()` function and `OpenSCADViewer` class
- `openscad_wasm_renderer.py` - WASM-based renderer (190x faster than local)
- `openscad_renderer.py` - Local OpenSCAD CLI renderer (fallback)
- `renderer_config.py` - Renderer selection and configuration
- `solid_bridge.py` - SolidPython2 integration with intelligent caching
- `wasm/` - Bundled WASM modules (openscad.wasm, openscad.js, etc.)
- `js/` - JavaScript widget components

**JavaScript Frontend (src/js/)**:
- `widget.js` - Main anywidget implementation with Three.js rendering
- `openscad-wasm-renderer.js` - WebAssembly OpenSCAD execution
- `wasm-loader.js` - WASM module loading and caching
- `memory-manager.js` - Memory optimization and cleanup
- `worker-manager.js` - Web Worker coordination

### Hybrid Renderer System

The project uses intelligent renderer selection:
1. **Auto (default)**: Prefers WASM, falls back to local OpenSCAD
2. **WASM**: Browser-native rendering (190x faster, zero dependencies)
3. **Local**: ✅ **FUNCTIONAL** Traditional OpenSCAD CLI (auto-detected cross-platform)

### Data Flow

**WASM Pipeline (Default - Zero Dependencies)**:
```
SolidPython2 → SCAD Code → Browser WASM → STL → Three.js → WebGL
```

**Local Pipeline (Fallback - ✅ FUNCTIONAL)**:
```
SolidPython2 → SCAD Code → Local OpenSCAD CLI → STL → Three.js → WebGL
✅ Status: 912 bytes STL generation validated (15. Juni 2025)
✅ Auto-detection: Cross-platform standard installations working
```

**Package Structure**: WASM modules are bundled directly in the Python package at `marimo_openscad/wasm/`, eliminating the need for separate OpenSCAD installation in most cases.

## Critical Testing Requirements

### Cache Behavior Tests (CRITICAL)
- **Location**: `tests/test_cache_behavior.py`
- **Purpose**: Prevents regression of LLM-identified cache issue
- **Key scenarios**: `update_scad_code()` properly invalidates cache
- **Command**: `make test-cache`

### LLM Regression Tests
- **Location**: `tests/test_llm_identified_issues.py` 
- **Purpose**: Validates fixes for externally identified issues
- **Command**: `make test-regression`

### ⚠️ **WASM Testing Strategy (TEMPORARY MOCKS)**

**🚨 CRITICAL WARNING**: Current testing strategy relies on extensive mocking that **MUST be replaced**:

**Current Approach (TEMPORARY)**:
- **Location**: `src/test/setup.js` - **Full browser API mocking**
- **Coverage**: WebAssembly, Canvas, Worker, fetch - **ALL MOCKED**
- **Benefits**: CI/CD stable, cross-platform compatible
- **Limitations**: **DOES NOT validate real functionality**

**Real WASM Tests (Preferred - FUTURE)**:
- **Target**: `tests/test_wasm_real_integration.py`
- **Strategy**: Uses actual bundled WASM files in real browsers
- **Status**: ❌ **Currently uses mocks, needs real implementation**

**Legacy Mock Tests (CURRENT)**:
- **Location**: `tests/test_wasm_renderer.py`, `tests/test_wasm_integration.py`
- **Strategy**: Heavy mocking for browser execution simulation
- **Status**: ✅ **Working but not validating real functionality**

**CI-Optimized Tests (CURRENT)**:
- **Location**: `tests/test_wasm_ci_optimized.py`
- **Strategy**: Environment detection with mock fallbacks
- **Status**: ✅ **Working for CI but needs real browser validation**

**REQUIRED MIGRATION PLAN**:
1. ❌ **Remove all browser API mocks from setup.js**
2. ❌ **Implement real WASM renderer integration**
3. ❌ **Add Playwright/Selenium E2E tests**
4. ❌ **Validate actual 190x performance claims**

### Performance Tests
- **WASM performance**: `test_wasm_performance.py`, `test_wasm_real_integration.py`
- **Cache effectiveness**: Cache hit/miss ratios
- **Memory usage**: Memory manager functionality
- **File integrity**: WASM file headers, JS syntax validation

## WASM Integration

### Key Features
- **Zero Dependencies**: No OpenSCAD installation required
- **Performance**: 190x faster than local rendering
- **Caching**: 7-day module cache with 35% improvement
- **Offline**: Full functionality after initial load

### WASM-Specific Files
- `public/wasm/openscad.wasm` - Main OpenSCAD WASM module
- `public/wasm/openscad.js` - WASM loader and bindings
- `scripts/download-wasm-modules.js` - WASM module fetching
- `scripts/optimize-wasm-assets.js` - Asset optimization

## Code Conventions

### Python
- **Formatting**: Black (line length 88)
- **Imports**: isort with black profile
- **Type hints**: Required for all public APIs
- **Testing**: pytest with comprehensive markers

### JavaScript
- **ES Modules**: All JS uses ESM syntax
- **Testing**: Vitest with happy-dom environment
- **Three.js**: Use typed arrays for performance
- **Error handling**: Progressive fallback system

## File Structure Patterns

```
src/marimo_openscad/        # Python package
├── __init__.py             # Main API exports
├── viewer.py               # Primary viewer implementation
├── *_renderer.py           # Renderer implementations
└── renderer_config.py      # Configuration management

src/js/                     # JavaScript widget code
├── widget.js               # Main anywidget entry point
├── *-manager.js            # Specialized managers
└── openscad-*.js           # OpenSCAD integration

tests/                      # Python tests
├── test_cache_behavior.py  # 🔥 Critical cache tests
├── test_*_renderer*.py     # Renderer tests
└── conftest.py             # pytest configuration

src/test/                   # JavaScript tests
├── setup.js                # Test environment setup
└── *.test.js               # Test files
```

## Performance Considerations

### Memory Management
- WASM modules cached for 7 days
- Automatic cleanup after 5 minutes idle
- Memory pressure monitoring
- Resource disposal on widget cleanup

### Rendering Optimization
- Triangle count limiting (browser performance)
- Progressive fallback system
- Hardware-accelerated WebGL rendering
- Web Worker support for non-blocking execution

## Error Handling Strategies

### 3-Layer Fallback System
1. **Primary**: Render actual STL from WASM/local OpenSCAD
2. **Secondary**: Procedural geometry if STL parsing fails
3. **Tertiary**: Test cube if all else fails

### Common Error Patterns
- **WASM not supported**: Auto-fallback to local renderer
- **OpenSCAD not found**: Clear installation instructions
- **Cache corruption**: Automatic cache clearing and retry
- **Memory pressure**: Garbage collection and resource cleanup

## Browser Compatibility

### WASM Support
- Chrome 69+, Firefox 62+, Safari 14+, Edge 79+
- 95%+ modern browser coverage
- Automatic feature detection and fallback

### WebGL Requirements
- Hardware acceleration preferred
- Software fallback available
- Progressive enhancement approach

## Development Workflow

1. **Setup**: `make install-dev` (installs Python and Node.js deps)
2. **Test**: `make validate` (quick validation suite)
3. **Develop**: Use watch modes for rapid iteration
4. **Pre-commit**: Run `make test-ci` (full CI-like suite)
5. **Performance**: Monitor WASM cache effectiveness

## Deployment Considerations

### PyPI Package
- Built via `uv build` or `python -m build`
- **WASM assets bundled**: `marimo_openscad/wasm/*.wasm`, `*.js` included
- **JavaScript components**: `marimo_openscad/js/*.js` included
- **Zero dependencies**: Users don't need OpenSCAD installation when using WASM
- Version managed by setuptools_scm

### WASM Integration
- WASM modules automatically discovered via `OpenSCADWASMRenderer.get_wasm_files()`
- JavaScript frontend loads WASM from package location
- Offline-capable after initial module download
- 7-day browser cache for performance

### Package Data Configuration
```toml
[tool.setuptools.package-data]
marimo_openscad = [
    "wasm/*.wasm",
    "wasm/*.js", 
    "wasm/*.d.ts",
    "js/*.js"
]
```