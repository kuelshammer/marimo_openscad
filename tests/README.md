# Test Suite for Marimo-OpenSCAD

## ⚠️ **CRITICAL WARNING: TEMPORARY MOCK IMPLEMENTATION**

**🚨 IMPORTANT**: This test suite currently uses **extensive mocking** to achieve CI/CD stability. The mocks **DO NOT validate real functionality** and **MUST be removed** before production deployment.

### **Current Mock Status:**
- ✅ **CI/CD Stable**: All tests pass in GitHub Actions
- ❌ **Real Implementation**: Browser/WASM APIs are mocked
- 🎯 **Target**: Remove mocks after real WASM implementation

## 🚨 CRITICAL: Cache Behavior Tests

This test suite includes **CRITICAL** tests that prevent regression of the cache issue identified by external LLM analysis where `update_scad_code` changes don't trigger visual updates.

## Test Organization

### 🐍 Python Backend Tests

#### 🔥 `test_cache_behavior.py` - CRITICAL CACHE TESTS
**Purpose**: Prevent regression of the LLM-identified cache issue

**Key Test Cases**:
- ✅ Cache invalidation with different SCAD code
- ✅ Cache invalidation with different parameters  
- ✅ Cache bypass functionality (`use_cache=False`)
- ✅ Force rendering options
- ✅ Cache clearing effectiveness

**Why Critical**: These tests ensure that the core issue reported by the LLM - "update_scad_code doesn't properly update visual display" - never happens again.

#### 🎯 `test_llm_identified_issues.py` - LLM REGRESSION TESTS
**Purpose**: Directly test the specific scenarios that failed in external LLM analysis

**Key Test Cases**:
- ✅ Cube-to-sphere SCAD code updates produce different output
- ✅ Mock content changes appear in HTML output  
- ✅ SCAD code property vs HTML output consistency
- ✅ End-to-end update workflows

**Why Important**: These tests replicate the exact test scenarios the LLM used and ensure they now pass.

#### 🔗 `test_viewer_integration.py` - INTEGRATION TESTS
**Purpose**: Test complete workflows and ensure reported-working functionality continues to work

**Key Test Cases**:
- ✅ Viewer size customization
- ✅ Error message handling (long messages)
- ✅ File format support (STL, OBJ, SVG, DXF)
- ✅ Case-insensitive file extensions
- ✅ Performance and memory usage

### 🟨 JavaScript Frontend Tests

Located in `src/test/`:
- `widget.test.js` - JavaScript widget component tests
- `setup.js` - Test environment configuration

## Running Tests

### Quick Commands

```bash
# Show all available test commands
make help

# 🔥 CRITICAL: Run cache behavior tests
make test-cache

# 🎯 Run LLM regression tests  
make test-regression

# 🚨 Run specific LLM-identified issue tests
make test-llm-issues

# 🔄 Run all tests (Python + JavaScript)
make test-all

# ⚡ Quick validation
make validate
```

### Detailed Commands

```bash
# Python backend tests
make test-python              # All Python tests
make test-integration         # Integration tests only
make test-coverage           # With coverage reporting

# JavaScript frontend tests
make test-js                 # JavaScript widget tests
make build-js               # Build JavaScript

# CI/CD commands
make test-ci                # Full CI-like test suite
```

### Direct pytest Commands

```bash
# Run tests by marker
pytest tests/ -v -m "cache"        # Cache-related tests
pytest tests/ -v -m "regression"   # Regression prevention tests
pytest tests/ -v -m "integration"  # Integration tests

# Run specific test files
pytest tests/test_cache_behavior.py -v --tb=long
pytest tests/test_llm_identified_issues.py -v --tb=long
pytest tests/test_viewer_integration.py -v --tb=short

# Run with coverage
pytest tests/ --cov=marimo_openscad --cov-report=html
```

## Test Failure Notifications

### 🚨 Where You'll See Test Failures

#### 1. **GitHub Actions CI/CD**
- **Location**: Repository → Actions tab
- **Notifications**: 
  - GitHub will send email notifications on failure
  - PR checks will show red ❌ status
  - Commit status badges will show failure

#### 2. **Pull Request Checks**
- **Location**: PR page → Checks section
- **Details**: Each test job shows individual results:
  - 🔥 Critical Cache Behavior Tests
  - 🎯 LLM Regression Tests  
  - 🔗 Integration Tests
  - 🟨 JavaScript Tests

#### 3. **Local Development**
```bash
# Run tests locally to catch issues before pushing
make test-cache        # Critical cache tests
make test-regression   # LLM regression tests
make validate         # Quick validation
```

#### 4. **Test Result Artifacts**
- **Location**: GitHub Actions → Run → Artifacts
- **Contents**: JUnit XML test results for detailed analysis

### 🚨 Critical Failure Alerts

If **cache behavior tests** fail, the CI will:
- ❌ Fail the entire build
- 🚨 Show "CRITICAL FAILURE" error in GitHub Actions
- 📧 Send notification emails
- 🛑 Block PR merging (if branch protection enabled)

## Test Markers

Use pytest markers to run specific test categories:

```python
@pytest.mark.cache          # Cache-related tests
@pytest.mark.regression     # Regression prevention
@pytest.mark.integration    # Integration tests  
@pytest.mark.slow          # Slow-running tests
```

## Debugging Failed Tests

### 1. **Check Test Output**
```bash
# Run with verbose output and full traceback
pytest tests/test_cache_behavior.py -v --tb=long

# Run specific failing test
pytest tests/test_llm_identified_issues.py::TestLLMIdentifiedCacheIssue::test_update_scad_code_cube_to_sphere_produces_different_output -v
```

### 2. **Check Coverage Reports**
```bash
# Generate HTML coverage report
make test-coverage
# Open htmlcov/index.html in browser
```

### 3. **Run Standalone Cache Test**
```bash
# Run the standalone cache validation script
python test_cache_fix.py
```

## Adding New Tests

### For Cache-Related Functionality
Add tests to `test_cache_behavior.py` with `@pytest.mark.cache`

### For New Features
Add tests to `test_viewer_integration.py` with appropriate markers

### For Regression Prevention
Add tests to `test_llm_identified_issues.py` with `@pytest.mark.regression`

## Test Environment

### ⚠️ **EXTENSIVE MOCKING (TEMPORARY)**

**CRITICAL**: Current test environment uses comprehensive mocking for CI/CD stability:

#### **Python Mocks:**
- OpenSCAD executable is mocked (no real OpenSCAD needed)
- File system operations are mocked
- WASM renderer execution is mocked

#### **JavaScript Mocks (src/test/setup.js):**
```javascript
// TEMPORARY MOCKS - MUST BE REMOVED
global.WebAssembly = { /* Full WASM API mock */ };
global.HTMLCanvasElement = { /* Canvas/WebGL mock */ };
global.Worker = { /* Web Worker mock */ };
global.fetch = { /* Module loading mock */ };
// + ResizeObserver, IntersectionObserver, URL, Blob...
```

#### **What These Mocks Hide:**
- ❌ **Real WASM module loading failures**
- ❌ **Browser compatibility issues**
- ❌ **Canvas/WebGL integration problems**
- ❌ **Actual performance characteristics**
- ❌ **Memory management behavior**
- ❌ **Cross-browser differences**

#### **Mock Removal Plan:**
1. **Phase 1**: Implement real WASM renderer
2. **Phase 2**: Add Playwright E2E tests with real browsers
3. **Phase 3**: Remove all temporary mocks
4. **Phase 4**: Validate with real browser testing

### Dependencies
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `unittest.mock` - Python mocking
- `vitest` - JavaScript testing

## Continuous Integration

The GitHub Actions workflow runs:
1. **Python tests** across multiple OS and Python versions
2. **Critical regression tests** on every commit  
3. **JavaScript tests** with Node.js
4. **Coverage reporting** to Codecov
5. **Test result publishing** to PR comments

**The test suite is designed to catch the LLM-identified cache regression issue immediately and prevent it from ever happening again.**