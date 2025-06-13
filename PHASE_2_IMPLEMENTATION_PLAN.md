# 🔗 Phase 2 Implementation Plan: JavaScript Import Resolution

**Plan Date:** 13. Juni 2025  
**Based on:** Phase 1 E2E Test Results & Sequential Thinking Analysis  
**Duration:** 4-5 Tage  
**Status:** 🎯 READY FOR EXECUTION  
**Priority:** ⭐ CRITICAL (Blocker für WASM Integration)

## 🎯 **Strategic Objectives**

### **Primary Goal: Eliminate JavaScript Import Failures**
**Phase 1 Findings:** 
- ❌ `window.testBasicImport is not a function` - JavaScript modules nicht verfügbar
- ❌ Relative imports (`./openscad-direct-renderer.js`) fehlschlagen in anywidget
- ✅ Browser-Fähigkeiten bestätigt (WebAssembly, ES Modules, Fetch)
- ❌ WASM-Pfade nicht auflösbar (alle lokalen Pfade fehlgeschlagen)

**Success Criteria:**
- ✅ JavaScript-Module laden erfolgreich in Browser
- ✅ Import-Errors eliminiert  
- ✅ WASM-Loader von anywidget aus erreichbar
- ✅ Bereit für Phase 3 (WASM Integration)

---

## 📋 **Step 2.1: JavaScript Import Problem Analysis**
**Duration:** 0.5 Tage  
**Priority:** ⭐ CRITICAL

### **Root Cause Analysis basierend auf Phase 1**

#### **Erkannte Probleme:**

1. **Relative Import Failure**
   ```javascript
   // ❌ FAILS in anywidget context:
   import { OpenSCADDirectRenderer } from './openscad-direct-renderer.js';
   ```

2. **Module Resolution Context**
   ```
   Phase 1 Error: "window.testBasicImport is not a function"
   → JavaScript modules not loading in browser environment
   ```

3. **anywidget ESM Limitations**
   ```python
   # Current anywidget approach - problematic:
   class OpenSCADViewer(anywidget.AnyWidget):
       _esm = """
       // This context cannot resolve relative imports
       import widget from './widget.js';  // ❌ FAILS
       """
   ```

#### **Investigation Tasks**

**Task 2.1.1: Document Current Import Chain**
```bash
# Map out current import dependencies
src/js/widget.js
├── import './openscad-direct-renderer.js'
├── import './wasm-loader.js'  
├── import './memory-manager.js'
└── import * as THREE from 'three'
```

**Task 2.1.2: Analyze anywidget Module Context**
```python
# Test anywidget module resolution behavior
class TestWidget(anywidget.AnyWidget):
    _esm = """
    console.log('Module context:', import.meta);
    console.log('Base URL:', import.meta.url);
    """
```

**Acceptance Criteria:**
- ✅ Vollständige Import-Dependency-Map dokumentiert
- ✅ anywidget module resolution behavior verstanden
- ✅ Path resolution strategy identifiziert

---

## 📋 **Step 2.2: JavaScript Bundle Creation**
**Duration:** 1.5 Tage  
**Priority:** ⭐ CRITICAL

### **Solution Strategy: Single Bundled File**

**Problem:** anywidget kann nicht mit relativen imports umgehen  
**Solution:** Alle JavaScript-Module in eine einzige Datei bundeln

#### **Implementation Approach A: Webpack Bundle**

**Step 2.2.1: Webpack Configuration**
```javascript
// webpack.config.js - NEU
const path = require('path');

module.exports = {
  entry: './src/js/widget.js',
  output: {
    path: path.resolve(__dirname, 'src/marimo_openscad/static'),
    filename: 'widget-bundle.js',
    library: {
      type: 'module'
    }
  },
  experiments: {
    outputModule: true
  },
  resolve: {
    extensions: ['.js']
  },
  externals: {
    // three.js as external dependency
    'three': 'THREE'
  }
};
```

**Step 2.2.2: Build System Integration**
```bash
# Package.json scripts update
npm install --save-dev webpack webpack-cli
npm run build:bundle  # Creates widget-bundle.js
```

**Step 2.2.3: Bundle Output Structure**
```
src/marimo_openscad/static/
├── widget-bundle.js        # 🆕 All modules in one file
├── widget-bundle.min.js    # 🆕 Minified production version
├── widget-bundle.map       # 🆕 Source maps for debugging
└── wasm/                   # ✅ Existing WASM files
    ├── openscad.wasm
    └── openscad.js
```

#### **Implementation Approach B: Inline Module Concatenation**

**Alternative for simple approach:**
```python
# build_inline_bundle.py - NEU
def create_inline_bundle():
    """Concatenate all JavaScript modules into single string"""
    
    modules = [
        'src/js/memory-manager.js',
        'src/js/wasm-loader.js', 
        'src/js/openscad-direct-renderer.js',
        'src/js/widget.js'
    ]
    
    bundled_code = []
    for module in modules:
        with open(module, 'r') as f:
            # Remove import/export statements
            content = f.read()
            content = process_module_syntax(content)
            bundled_code.append(content)
    
    return '\n'.join(bundled_code)
```

**Acceptance Criteria:**
- ✅ Bundle build funktioniert ohne Errors
- ✅ Alle Module dependencies aufgelöst
- ✅ Output-Bundle syntactically valid
- ✅ Bundle size < 500KB (Performance-Constraint)

---

## 📋 **Step 2.3: anywidget Integration**
**Duration:** 1 Tag  
**Priority:** ⭐ CRITICAL

### **Bundle-Loading Strategy**

#### **Option A: Inline Bundle Integration**
```python
# viewer.py - Update OpenSCADViewer
class OpenSCADViewer(anywidget.AnyWidget):
    
    def _get_bundled_javascript(self):
        """Load bundled JavaScript from static files"""
        bundle_path = Path(__file__).parent / "static" / "widget-bundle.js"
        return bundle_path.read_text()
    
    @property
    def _esm(self):
        """Inline bundled JavaScript in anywidget"""
        return self._get_bundled_javascript()
```

#### **Option B: Dynamic Import Strategy**
```python
# Alternative: HTTP-served bundle
class OpenSCADViewer(anywidget.AnyWidget):
    _esm = """
    // Load bundle from static path
    const module = await import('/static/widget-bundle.js');
    export default module.default;
    """
```

#### **Option C: Template-Based Injection**
```python
# Template replacement approach
class OpenSCADViewer(anywidget.AnyWidget):
    _esm = """
    // Template: {BUNDLE_CONTENT} replaced at runtime
    {BUNDLE_CONTENT}
    
    // Module is now available
    export default createOpenSCADWidget;
    """
    
    def __init__(self, *args, **kwargs):
        # Replace template with actual bundle
        bundle = self._get_bundled_javascript()
        self._esm = self._esm.replace('{BUNDLE_CONTENT}', bundle)
        super().__init__(*args, **kwargs)
```

**Acceptance Criteria:**
- ✅ Bundle lädt erfolgreich in anywidget
- ✅ Keine import-related console errors
- ✅ JavaScript-Module-Functions verfügbar
- ✅ Phase 1 tests zeigen verfügbare functions

---

## 📋 **Step 2.4: WASM Path Resolution**
**Duration:** 1 Tag  
**Priority:** 🔴 HIGH

### **WASM Loading Strategy basierend auf Phase 1 Erkenntnissen**

**Phase 1 Finding:** Nur Data-URL funktionierte, alle File-Pfade fehlgeschlagen

#### **Dynamic WASM URL Generation**
```javascript
// In bundled JavaScript - WASMPathResolver
class WASMPathResolver {
    static detectEnvironment() {
        // Detect anywidget vs development context
        if (typeof window.anywidget !== 'undefined') {
            return 'anywidget';
        }
        if (window.location.protocol === 'file:') {
            return 'development';
        }
        return 'browser';
    }
    
    static getWASMBaseURL() {
        const env = this.detectEnvironment();
        
        switch(env) {
            case 'anywidget':
                return '/static/wasm/';  // Package static path
            case 'development': 
                return './wasm/';       // Relative to HTML
            default:
                return '/wasm/';        // Server root
        }
    }
    
    static async loadWASMModule(filename) {
        const baseURL = this.getWASMBaseURL();
        const wasmURL = `${baseURL}${filename}`;
        
        console.log(`🔍 Attempting WASM load: ${wasmURL}`);
        
        try {
            const response = await fetch(wasmURL);
            if (!response.ok) {
                throw new Error(`WASM fetch failed: ${response.status}`);
            }
            
            const wasmBytes = await response.arrayBuffer();
            console.log(`✅ WASM loaded: ${wasmBytes.byteLength} bytes`);
            
            return wasmBytes;
        } catch (error) {
            console.error(`❌ WASM load failed: ${error.message}`);
            throw error;
        }
    }
}
```

#### **Fallback Strategy für WASM Loading**
```javascript
// Multi-path WASM loading with fallbacks
class WASMLoader {
    static async loadWithFallbacks(filename) {
        const paths = [
            `/static/wasm/${filename}`,           // Package static
            `./wasm/${filename}`,                 // Relative
            `../src/marimo_openscad/wasm/${filename}`, // Development
            `data:application/wasm;base64,...`    // Last resort: embedded
        ];
        
        for (const path of paths) {
            try {
                console.log(`🔍 Trying WASM path: ${path}`);
                const wasmBytes = await this.fetchWASM(path);
                console.log(`✅ WASM loaded from: ${path}`);
                return wasmBytes;
            } catch (error) {
                console.warn(`❌ WASM path failed: ${path} - ${error.message}`);
                continue;
            }
        }
        
        throw new Error('All WASM loading paths failed');
    }
}
```

**Acceptance Criteria:**
- ✅ WASM-URLs korrekt für anywidget-Kontext generiert
- ✅ WASM-Module laden erfolgreich im Browser
- ✅ Fallback-Chain funktioniert bei path failures
- ✅ Phase 1 WASM loading tests zeigen progress

---

## 📋 **Step 2.5: End-to-End Validation**
**Duration:** 1 Tag  
**Priority:** 🔴 HIGH

### **Validation gegen Phase 1 Test Suite**

#### **Test 2.5.1: JavaScript Import Validation**
```bash
# Run Phase 1 tests - should show improvement
uv run pytest tests/test_e2e_anywidget_real.py::TestRealAnyWidgetExecution::test_anywidget_import_failure_detection -v
```

**Expected Improvement:**
```
# Before Phase 2:
❌ window.testBasicImport is not a function

# After Phase 2:
✅ window.testBasicImport available
✅ JavaScript modules loaded successfully
```

#### **Test 2.5.2: WASM Loading Validation**
```bash
# Test WASM path resolution improvements
uv run pytest tests/test_e2e_wasm_failures.py::TestWASMLoadingFailures::test_wasm_file_accessibility -v
```

**Expected Improvement:**
```
# Before Phase 2:
❌ All paths failed except data URL

# After Phase 2:  
✅ At least one static path successful
✅ Fallback chain functional
```

#### **Test 2.5.3: Widget Creation Validation**
```bash
# Test widget creation with fixed imports
uv run pytest tests/test_e2e_anywidget_real.py::TestRealAnyWidgetExecution::test_widget_creation_failure_real -v
```

**Expected Improvement:**
```
# Before Phase 2:
❌ Widget creation failed (import failure)

# After Phase 2:
✅ Widget creation succeeds
✅ render function available
⚠️ STL data still placeholder (Phase 3 scope)
```

**Acceptance Criteria:**
- ✅ JavaScript import failures eliminated
- ✅ WASM loading path resolution improved
- ✅ Widget creation functional (even if STL placeholder)
- ✅ Foundation ready for Phase 3 (WASM Integration)

---

## 🔧 **Implementation Details**

### **Updated File Structure nach Phase 2**
```
src/marimo_openscad/
├── static/
│   ├── widget-bundle.js        # 🆕 Bundled JavaScript (all modules)
│   ├── widget-bundle.min.js    # 🆕 Production bundle
│   └── wasm/                   # ✅ Existing WASM files
│       ├── openscad.wasm
│       └── openscad.js
├── viewer.py                   # 🔄 Updated for bundle loading
└── js/                         # ✅ Source files (for development)
    ├── widget.js
    ├── openscad-direct-renderer.js
    └── wasm-loader.js
```

### **Build Process Integration**
```bash
# New development workflow:
npm run build:bundle           # Create production bundle
python -m pytest tests/test_e2e_*.py  # Validate improvements
uv run marimo edit examples/   # Test in real environment
```

### **Performance Considerations**
- **Bundle Size Target:** < 500KB (for fast loading)
- **Loading Time Target:** < 2s (anywidget initialization)
- **Memory Usage:** Monitor bundle memory footprint

---

## ✅ **Success Metrics & Validation Gates**

### **Gate 2.1: Import Resolution Success**
- ✅ Zero import-related console errors
- ✅ JavaScript functions available in browser
- ✅ Bundle loading < 2s
- ✅ Module dependencies resolved

### **Gate 2.2: WASM Path Resolution Success**  
- ✅ At least one WASM loading path functional
- ✅ Dynamic URL generation working
- ✅ Fallback chain tested and documented
- ✅ Compatible with anywidget static serving

### **Gate 2.3: anywidget Integration Success**
- ✅ Bundle integrates cleanly with anywidget
- ✅ No conflicts with anywidget internal systems
- ✅ Widget creation functional
- ✅ Ready for Phase 3 WASM integration

### **Final Phase 2 Validation:**
- ✅ Phase 1 import failure tests now passing
- ✅ WASM loading foundation established  
- ✅ JavaScript architecture anywidget-compatible
- ✅ Performance targets met

---

## 🚨 **Risk Mitigation & Contingency Plans**

### **High-Risk Areas**
1. **Bundle Size Explosion** - Multiple large dependencies
2. **anywidget Compatibility Issues** - Conflicting module systems  
3. **WASM Path Platform Differences** - Windows/Mac/Linux variations

### **Mitigation Strategies**

#### **Bundle Size Risk**
```bash
# Monitor and optimize bundle size
npm run analyze-bundle          # Analyze bundle composition
npm run build:optimize          # Tree-shaking and minification
```

#### **anywidget Compatibility Risk**
```python
# Feature detection and graceful fallback
class OpenSCADViewer(anywidget.AnyWidget):
    def __init__(self, *args, **kwargs):
        try:
            # Try bundled approach
            self._esm = self._get_bundled_javascript()
        except Exception:
            # Fallback to minimal approach
            self._esm = self._get_fallback_javascript()
```

#### **Cross-Platform Path Risk**
```javascript
// Normalized path handling
class PathNormalizer {
    static normalize(path) {
        return path.replace(/\\/g, '/');  // Normalize Windows paths
    }
}
```

### **Contingency Plans**
- **Bundle approach fails:** Fallback to inline concatenation
- **WASM paths fail:** Use embedded base64 data URLs
- **Performance targets missed:** Implement lazy loading

---

## 📅 **Implementation Timeline**

### **Day 1: Analysis & Setup**
- **Morning:** Step 2.1 - Import problem analysis
- **Afternoon:** Step 2.2.1 - Webpack setup & configuration

### **Day 2: Bundle Creation**
- **Morning:** Step 2.2.2-2.2.3 - Bundle creation & testing
- **Afternoon:** Step 2.3 - anywidget integration experiments

### **Day 3: Integration & WASM Paths**
- **Morning:** Step 2.3 - anywidget bundle integration  
- **Afternoon:** Step 2.4 - WASM path resolution

### **Day 4: Validation & Testing**
- **Morning:** Step 2.5 - End-to-end validation
- **Afternoon:** Performance testing & optimization

### **Day 5: Polish & Documentation**
- **Morning:** Bug fixes, edge cases
- **Afternoon:** Documentation, handoff to Phase 3

---

**Phase 2 Status:** 🎯 READY FOR EXECUTION  
**Next Action:** Begin Step 2.1 - JavaScript Import Problem Analysis  
**Expected Completion:** 18. Juni 2025  
**Success Indicator:** Phase 1 import tests transition from ❌ to ✅

**⚠️ Critical Success Factor:** Nach Phase 2 müssen JavaScript-Module in anywidget ladbar sein - das ist Grundvoraussetzung für Phase 3 WASM-Integration!