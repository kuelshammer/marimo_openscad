"""
Step 1: Minimal OpenSCAD Viewer - Only HTML Container
Test: Basic HTML rendering without any JavaScript complexity
"""

import anywidget
import traitlets

class OpenSCADViewer(anywidget.AnyWidget):
    """Step 1: Basic HTML container only"""
    
    # Basic traits
    stl_data = traitlets.Unicode("").tag(sync=True)
    error_message = traitlets.Unicode("").tag(sync=True)
    renderer_type = traitlets.Unicode("auto").tag(sync=True)
    
    _esm = """
    async function render({ model, el }) {
        console.log('🚀 Step 1: Basic container rendering...');
        
        el.innerHTML = 
            '<div style="width: 100%; height: 400px; border: 2px solid #007acc; border-radius: 8px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); display: flex; align-items: center; justify-content: center; font-family: system-ui;">' +
                '<div style="text-align: center; padding: 20px;">' +
                    '<h2 style="color: #007acc; margin: 0 0 10px 0;">🎯 Step 1: Container Test</h2>' +
                    '<p style="color: #666; margin: 0;">Basic HTML rendering successful!</p>' +
                    '<div style="margin-top: 15px; padding: 10px; background: rgba(0,122,204,0.1); border-radius: 4px;">' +
                        '<code>Renderer: ' + (model.get('renderer_type') || 'auto') + '</code>' +
                    '</div>' +
                '</div>' +
            '</div>';
        
        console.log('✅ Step 1: Container rendered successfully');
    }
    
    export default { render };
    """
    
    def __init__(self, model=None, renderer_type="auto", **kwargs):
        super().__init__()
        self.renderer_type = renderer_type

def openscad_viewer(model, renderer_type="auto", **kwargs):
    """Step 1: Basic viewer factory"""
    return OpenSCADViewer(model=model, renderer_type=renderer_type, **kwargs)