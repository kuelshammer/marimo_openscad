"""
Minimal OpenSCAD Viewer for Testing
"""

import anywidget
import traitlets

class MinimalOpenSCADViewer(anywidget.AnyWidget):
    """Minimal 3D viewer for debugging JavaScript issues"""
    
    stl_data = traitlets.Unicode("").tag(sync=True)
    error_message = traitlets.Unicode("").tag(sync=True)
    
    _esm = """
    async function render({ model, el }) {
        console.log('🚀 Minimal viewer starting...');
        
        el.innerHTML = `
            <div style="width: 100%; height: 300px; border: 1px solid #ddd; display: flex; align-items: center; justify-content: center; background: #f5f5f5;">
                <div style="text-align: center;">
                    <h3>🎯 Minimal OpenSCAD Viewer</h3>
                    <p>Testing JavaScript execution...</p>
                    <div id="status">Initializing...</div>
                </div>
            </div>
        `;
        
        const status = el.querySelector('#status');
        
        try {
            status.textContent = "✅ JavaScript execution successful!";
            console.log('✅ Minimal viewer rendered successfully');
        } catch (error) {
            status.textContent = "❌ Error: " + error.message;
            console.error('❌ Minimal viewer error:', error);
        }
    }
    
    export default { render };
    """
    
    def __init__(self):
        super().__init__()

def minimal_viewer():
    """Create a minimal viewer for testing"""
    return MinimalOpenSCADViewer()