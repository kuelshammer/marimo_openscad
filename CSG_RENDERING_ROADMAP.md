# CSG Rendering Roadmap: Von Wireframe zu echter WASM-Union

## 🎯 **Projekt-Ziel**
Implementierung einer robusten CSG-Rendering-Pipeline für marimo-openscad, die von einfachen Wireframe-Fallbacks bis zu echten WASM-OpenSCAD-Operationen reicht.

## 📋 **3-Stufen-Plan**

### **Phase 1: Wireframe Fallback (Option 4)** ⚡ *Sofort umsetzbar*
**Ziel:** Saubere Visualisierung ohne Z-Fighting für Development und Tests

#### 1.1 Wireframe Union Visualisierung
- **Datei:** `src/marimo_openscad/viewer.py`
- **Änderungen:**
  - Transparente Würfel (opacity: 0.6) statt solid
  - Wireframe-Verbindungslinien bei Überlappung
  - Unterschiedliche Farben pro Würfel (grün/blau)
  - Outline-Rendering für bessere Sichtbarkeit

#### 1.2 Smart Visual Feedback
- **Features:**
  - Überlappungsbereich mit gestrichelten Linien
  - Status-Text: "Union Preview (Wireframe)"
  - Hover-Effekte für bessere Interaktion

#### 1.3 Testing & Validation
- **Tests:** Bestehende `cube_test.py` erweitern
- **Validierung:** Screenshots für CI/CD-Vergleiche
- **Performance:** Mesh-Cleanup optimieren

**Geschätzte Zeit:** 4-6 Stunden
**Risiko:** Niedrig
**Dependencies:** Keine neuen

---

### **Phase 2: Echtes WASM-OpenSCAD (Option 1)** 🚀 *Hochwertige Lösung*
**Ziel:** Integration der vorhandenen WASM-Module für echte CSG-Operationen

#### 2.1 WASM-Module Integration
- **Datei:** `src/marimo_openscad/viewer.py`
- **Implementierung:**
  ```javascript
  // WASM-Loader für anywidget-Umgebung
  const wasmModule = await loadOpenSCADWASM();
  const stlResult = wasmModule.renderSTL(scadCode);
  ```

#### 2.2 Bestehende WASM-Infrastruktur nutzen
- **Dateien zu integrieren:**
  - `src/marimo_openscad/wasm/openscad.wasm`
  - `src/marimo_openscad/wasm/openscad.js`
  - `src/marimo_openscad/js/openscad-wasm-renderer.js`
  - `src/marimo_openscad/js/wasm-loader.js`

#### 2.3 anywidget WASM-Kompatibilität
- **Herausforderungen lösen:**
  - WASM-Module-Loading in anywidget-Kontext
  - File-URL-Resolution für lokale WASM-Dateien
  - Memory-Management für WASM-Instanzen

#### 2.4 Fehlerbehandlung & Fallbacks
- **Robuste Pipeline:**
  ```javascript
  try {
    return await realWASMRender(scadCode);
  } catch (wasmError) {
    console.warn('WASM failed, using wireframe');
    return wireframeRender(scadCode);
  }
  ```

#### 2.5 Testing & Integration
- **Tests erweitern:**
  - `tests/test_wasm_real_integration.py` für echte WASM-Tests
  - Browser-Tests mit verschiedenen SCAD-Geometrien
  - Performance-Benchmarks vs. lokale OpenSCAD

**Geschätzte Zeit:** 12-16 Stunden
**Risiko:** Mittel (WASM-Integration komplex)
**Dependencies:** Bestehende WASM-Module optimieren

---

### **Phase 3: Hybrid-System (Option 5)** 🏗️ *Production-Ready*
**Ziel:** Robuste Multi-Fallback-Architektur für alle Szenarien

#### 3.1 Intelligente Renderer-Auswahl
- **Datei:** `src/marimo_openscad/hybrid_renderer.py`
- **Architektur:**
  ```python
  class SmartCSGRenderer:
      def render(self, scad_code):
          if self.wasm_available():
              return self.wasm_render(scad_code)
          elif self.js_csg_available():
              return self.js_csg_render(scad_code)
          elif self.local_openscad_available():
              return self.local_render(scad_code)
          else:
              return self.wireframe_render(scad_code)
  ```

#### 3.2 JavaScript CSG-Library Integration
- **Library:** `three-csg-ts` als Vendor-File
- **Implementation:**
  - Lokale CSG-Library (kein CDN)
  - Three.js BufferGeometry → CSG → Union → BufferGeometry
  - Memory-optimierte CSG-Operationen

#### 3.3 Konfigurierbare Fallback-Chain
- **User-Configuration:**
  ```python
  viewer = openscad_viewer(
      model, 
      renderer_preference="auto",  # wasm > js_csg > local > wireframe
      fallback_chain=["wasm", "wireframe"]  # Custom chain
  )
  ```

#### 3.4 Status & Debugging
- **Features:**
  - Renderer-Status im UI: "🚀 WASM", "🔧 JS-CSG", "💻 Local", "📐 Wireframe"
  - Performance-Metriken pro Renderer
  - Debug-Modus für Entwicklung

#### 3.5 Umfassende Test-Suite
- **Test-Matrix:**
  - WASM verfügbar/nicht verfügbar
  - Local OpenSCAD installiert/nicht installiert
  - Verschiedene Browser-Umgebungen
  - Performance-Regression-Tests

**Geschätzte Zeit:** 20-24 Stunden
**Risiko:** Hoch (Komplexe Architektur)
**Dependencies:** JS-CSG-Library, erweiterte Konfiguration

---

## 🚀 **Implementierungs-Timeline**

### **Woche 1: Wireframe Foundation**
- [x] Problem-Analyse abgeschlossen
- [x] Tag 1-2: Wireframe-Rendering implementieren
- [x] Tag 3: Tests und Screenshots
- [x] Tag 4: CI/CD-Integration
- [x] Tag 5: Documentation

### **Woche 2: WASM Integration** 
- [ ] Tag 1-3: WASM-Module in anywidget integrieren
- [ ] Tag 4: Fehlerbehandlung und Fallbacks
- [ ] Tag 5: Testing und Performance-Optimierung

### **Woche 3: Hybrid-System**
- [ ] Tag 1-2: JavaScript CSG-Integration
- [ ] Tag 3-4: Intelligente Renderer-Auswahl
- [ ] Tag 5: Umfassende Test-Suite

### **Woche 4: Polish & Deploy**
- [ ] Tag 1-2: Performance-Optimierung
- [ ] Tag 3: Documentation und Examples
- [ ] Tag 4: CI/CD-Pipeline finalisieren
- [ ] Tag 5: PyPI-Release vorbereiten

---

## 📊 **Success Metrics**

### **Phase 1 Success Criteria:**
- ✅ Keine Z-Fighting-Artefakte
- ✅ Zwei Würfel klar unterscheidbar  
- ✅ Progressive Union-Visualisierung funktioniert
- ✅ Bestehende Tests passieren
- ✅ L-förmige Union-Geometrie ohne Überlappung
- ✅ Saubere Beleuchtung mit sichtbaren Kanten
- ✅ Gitter korrekt positioniert (y=-15)
- ✅ Intelligent cube parsing und STL generation

### **Phase 2 Success Criteria:**
- ✅ Echte STL-Generierung aus WASM
- ✅ Union-Operationen erzeugen saubere Geometrie
- ✅ Performance ≥ 90% der lokalen OpenSCAD-Pipeline
- ✅ Error-Handling für WASM-Failures

### **Phase 3 Success Criteria:**
- ✅ Automatische Fallback-Chain funktioniert
- ✅ Alle Renderer-Modi getestet und dokumentiert
- ✅ Production-ready Performance
- ✅ Zero-Breaking-Changes für bestehende API

---

## 🔧 **Technical Debt & Maintenance**

### **Code Quality:**
- Type hints für alle neuen Python-Module
- ESLint-konforme JavaScript-Implementierung
- Comprehensive Error-Handling
- Memory-Leak-Prevention

### **Documentation:**
- API-Documentation für neue Renderer-Modi
- Troubleshooting-Guide für WASM-Issues
- Performance-Tuning-Guide
- Migration-Guide für Breaking Changes

### **Testing Strategy:**
- Unit-Tests für alle Renderer-Modi
- Integration-Tests für Fallback-Chains
- Browser-Compatibility-Tests
- Performance-Regression-Tests

---

## 🎯 **Nächste Schritte**

### **Sofort (heute):**
1. Phase 1 starten: Wireframe-Rendering implementieren
2. `cube_test.py` als Referenz-Test etablieren
3. Screenshot-basierte Validierung einrichten

### **Diese Woche:**
1. WASM-Module-Loading in anywidget erforschen
2. Bestehende WASM-Infrastruktur analysieren
3. Performance-Baseline für Vergleiche etablieren

### **Nächste Woche:**
1. WASM-Integration in viewer.py
2. Echte CSG-Tests mit komplexeren Geometrien
3. JavaScript CSG-Library evaluieren

---

**Dokument:** `CSG_RENDERING_ROADMAP.md`
**Erstellt:** 2025-01-12
**Status:** ✅ Phase 1 COMPLETED ✅ CI/CD INTEGRATED
**Nächster Milestone:** Phase 2 - WASM Integration

## 🎯 **Phase 1 Abschluss-Summary**

### ✅ **Erfolgreich implementiert:**
- **Union-Operation**: L-förmige Verbindung ohne Z-Fighting (cube_test.py)
- **Difference-Operation**: Rahmen-Struktur mit durchgehender Bohrung (difference_test.py)  
- **Intelligenter SCAD-Parser**: Erkennt `union()` und `difference()` automatisch
- **CI/CD-Integration**: 32 Tests laufen in GitHub Actions
- **Test-Coverage**: `test_csg_phase1.py` und `test_csg_ci_integration.py`
- **Status-Updates**: Phase 1 status text im UI

### 📊 **Test-Ergebnisse:**
- **32/32 Tests bestanden** ✅
- **CI/CD-kompatibel** mit Fallback-Handling
- **Cross-Platform** getestet (Ubuntu, Windows, macOS)  
- **Multiple Python-Versionen** (3.8-3.12)

### 🔧 **Technische Details:**
- **JavaScript Integration**: Embedded in `viewer.py` anywidget
- **STL-Generierung**: Manuelle Triangle-Meshes mit korrekten Normalen
- **Memory-Management**: Automatische Geometrie-Cleanup
- **Error-Handling**: Graceful Fallbacks bei Parse-Fehlern