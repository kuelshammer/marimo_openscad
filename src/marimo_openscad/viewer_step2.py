"""
Step 2: Three.js Integration + Simple Cube
Test: Load Three.js and render a basic cube geometry
"""

import anywidget
import traitlets

class OpenSCADViewer(anywidget.AnyWidget):
    """Step 2: Three.js integration with simple geometry"""
    
    # Basic traits
    stl_data = traitlets.Unicode("").tag(sync=True)
    error_message = traitlets.Unicode("").tag(sync=True)
    renderer_type = traitlets.Unicode("auto").tag(sync=True)
    
    _esm = """
    async function render({ model, el }) {
        console.log('🚀 Step 2: Three.js integration starting...');
        
        // Simple container
        el.innerHTML = 
            '<div style="width: 100%; height: 400px; border: 2px solid #28a745; border-radius: 8px; position: relative; background: #f8f9fa;">' +
                '<div id="threejs-container" style="width: 100%; height: 100%;"></div>' +
                '<div id="status" style="position: absolute; top: 10px; left: 10px; background: rgba(40,167,69,0.9); color: white; padding: 8px 12px; border-radius: 4px; font-size: 12px;">' +
                    'Step 2: Loading Three.js...' +
                '</div>' +
            '</div>';
        
        const container = el.querySelector('#threejs-container');
        const status = el.querySelector('#status');
        
        try {
            // Load Three.js from CDN
            status.textContent = 'Loading Three.js from CDN...';
            
            if (!window.THREE) {
                const script = document.createElement('script');
                script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
                document.head.appendChild(script);
                
                await new Promise((resolve, reject) => {
                    script.onload = resolve;
                    script.onerror = reject;
                    setTimeout(reject, 10000);
                });
            }
            
            if (!window.THREE) {
                throw new Error('Three.js failed to load');
            }
            
            status.textContent = 'Creating 3D scene...';
            
            // Basic Three.js setup
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, container.offsetWidth / container.offsetHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            
            renderer.setSize(container.offsetWidth, container.offsetHeight);
            renderer.setClearColor(0xf0f0f0);
            container.appendChild(renderer.domElement);
            
            // Simple test cube
            const geometry = new THREE.BoxGeometry(2, 2, 2);
            const material = new THREE.MeshBasicMaterial({ color: 0x007acc, wireframe: true });
            const cube = new THREE.Mesh(geometry, material);
            scene.add(cube);
            
            // Position camera
            camera.position.z = 5;
            
            // Simple rotation animation
            function animate() {
                requestAnimationFrame(animate);
                cube.rotation.x += 0.01;
                cube.rotation.y += 0.01;
                renderer.render(scene, camera);
            }
            
            animate();
            status.textContent = '✅ Step 2: Three.js cube rendering!';
            
            console.log('✅ Step 2: Three.js integration successful');
            
        } catch (error) {
            status.textContent = '❌ Error: ' + error.message;
            status.style.background = 'rgba(220,53,69,0.9)';
            console.error('❌ Step 2 error:', error);
        }
    }
    
    export default { render };
    """
    
    def __init__(self, model=None, renderer_type="auto", **kwargs):
        super().__init__()
        self.renderer_type = renderer_type

def openscad_viewer(model, renderer_type="auto", **kwargs):
    """Step 2: Three.js viewer factory"""
    return OpenSCADViewer(model=model, renderer_type=renderer_type, **kwargs)