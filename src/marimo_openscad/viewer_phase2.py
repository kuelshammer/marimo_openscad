"""
Phase 2 Viewer - JavaScript Bundle Integration

This version uses bundled JavaScript for anywidget compatibility,
eliminating the relative import problems identified in Phase 1.
"""

import anywidget
import traitlets
import tempfile
import subprocess
import base64
from pathlib import Path
import logging
from typing import Optional, Literal, Union
from .openscad_renderer import OpenSCADRenderer
from .openscad_wasm_renderer import OpenSCADWASMRenderer, HybridOpenSCADRenderer
from .renderer_config import get_config

logger = logging.getLogger(__name__)

class OpenSCADViewerPhase2(anywidget.AnyWidget):
    """
    Phase 2: Bundle-based 3D-Viewer für SolidPython2-Objekte
    
    Fixes JavaScript import problems through bundled modules.
    """
    
    # Viewer state traits
    stl_data = traitlets.Unicode("").tag(sync=True)
    scad_code = traitlets.Unicode("").tag(sync=True)
    error_message = traitlets.Unicode("").tag(sync=True)
    is_loading = traitlets.Bool(False).tag(sync=True)
    
    # Renderer configuration traits
    renderer_type = traitlets.Unicode("auto").tag(sync=True)
    renderer_status = traitlets.Unicode("initializing").tag(sync=True)
    wasm_supported = traitlets.Bool(True).tag(sync=True)
    wasm_enabled = traitlets.Bool(False).tag(sync=True)
    wasm_base_url = traitlets.Unicode("").tag(sync=True)
    
    def _get_bundled_javascript(self):
        """Load bundled JavaScript from static files"""
        bundle_path = Path(__file__).parent / "static" / "widget-bundle.js"
        if bundle_path.exists():
            logger.info(f"Loading ES bundle: {bundle_path}")
            return bundle_path.read_text()
        else:
            # Fallback to UMD bundle
            umd_path = Path(__file__).parent / "static" / "widget-bundle.umd.js"
            if umd_path.exists():
                logger.info(f"Loading UMD bundle: {umd_path}")
                bundle_content = umd_path.read_text()
                return f"""
                // Load UMD bundle and export for ES modules
                {bundle_content}
                // Export default for anywidget compatibility
                const widget = window.MarimoOpenSCADWidget?.default || window.MarimoOpenSCADWidget;
                export default widget;
                """
            else:
                raise FileNotFoundError("No JavaScript bundle found. Run 'npm run build' first.")
    
    @property 
    def _esm(self):
        """Dynamically load bundled JavaScript for anywidget"""
        try:
            bundle_code = self._get_bundled_javascript()
            return f"""
            // === PHASE 2: BUNDLED MARIMO-OPENSCAD WIDGET ===
            // All JavaScript modules bundled for anywidget compatibility
            
            {bundle_code}
            
            // === PHASE 2: ANYWIDGET RENDER FUNCTION ===
            async function render({{ model, el }}) {{
                console.log('🚀 Phase 2: Starting bundled marimo-openscad viewer...');
                console.log('📦 Bundle size: {len(bundle_code)} characters');
                
                // Phase 2 container with status
                el.innerHTML = `
                    <div style="width: 100%; height: 450px; border: 2px solid #4CAF50; position: relative; background: #f9f9f9;">
                        <div id="container" style="width: 100%; height: 100%;"></div>
                        <div style="position: absolute; top: 10px; left: 10px; background: rgba(76,175,80,0.9); color: white; padding: 8px 12px; border-radius: 4px; font-family: monospace; font-size: 12px;">
                            ✅ Phase 2: Bundle Loaded
                        </div>
                        <div style="position: absolute; bottom: 10px; left: 10px; background: rgba(0,0,0,0.7); color: white; padding: 4px 8px; border-radius: 3px; font-family: monospace; font-size: 10px;">
                            Bundle: ${{model.get('renderer_type') || 'auto'}} | Status: ${{model.get('renderer_status') || 'loading'}}
                        </div>
                        <div style="position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.9); padding: 8px; border-radius: 4px; font-size: 11px;">
                            🎯 Phase 2 Testing
                        </div>
                    </div>
                `;
                
                const container = el.querySelector('#container');
                
                // Test if bundled widget is available
                if (typeof window.MarimoOpenSCADWidget !== 'undefined') {{
                    console.log('✅ Bundle detected - MarimoOpenSCADWidget available');
                    console.log('🔍 Widget type:', typeof window.MarimoOpenSCADWidget);
                    console.log('🔍 Widget keys:', Object.keys(window.MarimoOpenSCADWidget || {{}}));
                    
                    // Try to use bundled renderer if available
                    const widget = window.MarimoOpenSCADWidget.default || window.MarimoOpenSCADWidget;
                    if (widget && typeof widget.render === 'function') {{
                        console.log('✅ Calling bundled render function');
                        try {{
                            return await widget.render({{ model, el: container }});
                        }} catch (error) {{
                            console.error('❌ Bundled render failed:', error);
                            container.innerHTML = `<div style="padding: 20px;">❌ Bundled render error: ${{error.message}}</div>`;
                        }}
                    }} else {{
                        console.warn('⚠️ Bundle loaded but no render function found');
                        container.innerHTML = '<div style="padding: 20px;">⚠️ Bundle missing render function</div>';
                    }}
                }} else {{
                    console.warn('⚠️ Bundle not detected in window scope');
                    
                    // Display STL data info for debugging
                    const stlData = model.get('stl_data') || 'None';
                    const stlPreview = stlData.substring(0, 100) + (stlData.length > 100 ? '...' : '');
                    
                    container.innerHTML = `
                        <div style="padding: 20px;">
                            <h3>🔧 Phase 2: Bundle Debug Info</h3>
                            <p><strong>Bundle Status:</strong> Not detected in window scope</p>
                            <p><strong>STL Data:</strong> ${{stlData.length}} characters</p>
                            <p><strong>Preview:</strong> <code>${{stlPreview}}</code></p>
                            <p><strong>Renderer:</strong> ${{model.get('renderer_type') || 'auto'}}</p>
                            
                            <div style="margin-top: 20px; padding: 10px; background: #fff3cd; border: 1px solid #ffeaa7;">
                                <strong>Expected Phase 2 Behavior:</strong>
                                <ul>
                                    <li>✅ Bundle loads without import errors</li>
                                    <li>⚠️ Widget functions may still be placeholders</li>
                                    <li>🎯 Ready for Phase 3 WASM integration</li>
                                </ul>
                            </div>
                        </div>
                    `;
                }}
                
                console.log('✅ Phase 2 render completed');
            }}
            
            export default {{ render }};
            """
        except Exception as e:
            logger.error(f"Failed to load bundled JavaScript: {e}")
            return self._get_fallback_esm()
    
    def _get_fallback_esm(self):
        """Fallback ESM when bundle is not available"""
        return """
        async function render({ model, el }) {
            console.log('❌ Phase 2: Bundle failed - using fallback');
            
            const stlData = model.get('stl_data') || 'None';
            const errorInfo = `Bundle loading failed. Please run: npm run build`;
            
            el.innerHTML = `
                <div style="padding: 20px; border: 2px solid #f44336; background: #ffebee;">
                    <h3>🚫 Phase 2: JavaScript Bundle Not Available</h3>
                    <p><strong>Error:</strong> ${errorInfo}</p>
                    <p><strong>STL Data:</strong> ${stlData.substring(0, 100)}${stlData.length > 100 ? '...' : ''}</p>
                    
                    <div style="margin-top: 20px; padding: 10px; background: #fff3cd; border: 1px solid #ffeaa7;">
                        <strong>To fix this:</strong>
                        <ol>
                            <li>Run <code>npm run build</code></li>
                            <li>Verify bundle exists in <code>src/marimo_openscad/static/</code></li>
                            <li>Restart Python kernel</li>
                        </ol>
                    </div>
                </div>
            `;
        }
        
        export default { render };
        """

    def __init__(self, solid_obj=None, renderer_type: Literal["auto", "wasm", "local"] = "auto", **kwargs):
        """Initialize Phase 2 viewer with bundle support"""
        super().__init__(**kwargs)
        
        self.renderer_type = renderer_type
        self.renderer_status = "initializing"
        
        if solid_obj is not None:
            self.update_model(solid_obj)
    
    def update_model(self, solid_obj):
        """Update the 3D model (Phase 2: uses existing renderers)"""
        try:
            self.is_loading = True
            self.error_message = ""
            self.renderer_status = "rendering"
            
            # Convert to SCAD code 
            if hasattr(solid_obj, 'scad_str'):
                scad_code = solid_obj.scad_str()
            elif hasattr(solid_obj, '_get_scad_str'):
                scad_code = solid_obj._get_scad_str()
            else:
                scad_code = str(solid_obj)
            
            self.scad_code = scad_code
            
            # Phase 2: Use existing renderer system
            config = get_config()
            if self.renderer_type == "auto":
                renderer = HybridOpenSCADRenderer(config)
            elif self.renderer_type == "wasm":
                renderer = OpenSCADWASMRenderer(config)
            else:
                renderer = OpenSCADRenderer(config)
            
            # Render STL
            stl_data = renderer.render_scad_to_stl(scad_code)
            
            if stl_data:
                self.stl_data = stl_data
                self.renderer_status = "ready"
                logger.info(f"Phase 2: STL generated, {len(stl_data)} characters")
            else:
                self.error_message = "No STL data generated"
                self.renderer_status = "error"
                
        except Exception as e:
            self.error_message = str(e)
            self.renderer_status = "error"
            logger.error(f"Phase 2 update_model failed: {e}")
        finally:
            self.is_loading = False

# Convenience function
def openscad_viewer_phase2(solid_obj, renderer_type: Literal["auto", "wasm", "local"] = "auto"):
    """Phase 2 viewer with bundled JavaScript"""
    return OpenSCADViewerPhase2(solid_obj, renderer_type=renderer_type)