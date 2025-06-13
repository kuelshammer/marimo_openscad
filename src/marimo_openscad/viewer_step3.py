"""
Step 3: STL Parsing + SolidPython2 Integration
Test: Parse STL data and render real geometry from SolidPython2 objects
"""

import anywidget
import traitlets
import tempfile
import subprocess
from pathlib import Path

class OpenSCADViewer(anywidget.AnyWidget):
    """Step 3: STL parsing with SolidPython2 integration"""
    
    # Traits
    stl_data = traitlets.Unicode("").tag(sync=True)
    scad_code = traitlets.Unicode("").tag(sync=True)
    error_message = traitlets.Unicode("").tag(sync=True)
    renderer_type = traitlets.Unicode("auto").tag(sync=True)
    
    _esm = """
    async function render({ model, el }) {
        console.log('🚀 Step 3: STL parsing + SolidPython2 integration...');
        
        el.innerHTML = 
            '<div style="width: 100%; height: 400px; border: 2px solid #dc3545; border-radius: 8px; position: relative; background: #f8f9fa;">' +
                '<div id="threejs-container" style="width: 100%; height: 100%;"></div>' +
                '<div id="status" style="position: absolute; top: 10px; left: 10px; background: rgba(220,53,69,0.9); color: white; padding: 8px 12px; border-radius: 4px; font-size: 12px;">' +
                    'Step 3: Processing SolidPython2 model...' +
                '</div>' +
                '<div id="model-info" style="position: absolute; bottom: 10px; left: 10px; background: rgba(0,0,0,0.7); color: white; padding: 4px 8px; border-radius: 3px; font-size: 10px;">' +
                    'Waiting for STL data...' +
                '</div>' +
            '</div>';
        
        const container = el.querySelector('#threejs-container');
        const status = el.querySelector('#status');
        const modelInfo = el.querySelector('#model-info');
        
        let scene, camera, renderer, currentMesh;
        
        // STL Parser (simplified)
        function parseSTL(data) {
            if (!data || data.length === 0) {
                throw new Error('No STL data provided');
            }
            
            // Simple ASCII STL parser for testing
            const lines = data.split('\\n');
            const vertices = [];
            const normals = [];
            
            let vertexCount = 0;
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                if (line.startsWith('vertex')) {
                    const coords = line.split(/\\s+/).slice(1).map(parseFloat);
                    if (coords.length === 3) {
                        vertices.push(...coords);
                        vertexCount++;
                    }
                }
                if (line.startsWith('facet normal')) {
                    const normal = line.split(/\\s+/).slice(2).map(parseFloat);
                    if (normal.length === 3) {
                        // Add same normal for 3 vertices of the triangle
                        normals.push(...normal, ...normal, ...normal);
                    }
                }
            }
            
            console.log('📊 STL parsed:', vertexCount, 'vertices');
            return { vertices: new Float32Array(vertices), normals: new Float32Array(normals) };
        }
        
        // Initialize Three.js
        async function initThreeJS() {
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
            
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(75, container.offsetWidth / container.offsetHeight, 0.1, 1000);
            renderer = new THREE.WebGLRenderer({ antialias: true });
            
            renderer.setSize(container.offsetWidth, container.offsetHeight);
            renderer.setClearColor(0xf5f5f5);
            container.appendChild(renderer.domElement);
            
            // Add lights
            const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(1, 1, 1);
            scene.add(directionalLight);
            
            camera.position.set(10, 10, 10);
            camera.lookAt(0, 0, 0);
            
            // Add simple mouse controls for rotation
            let isMouseDown = false;
            let mouseX = 0, mouseY = 0;
            
            container.addEventListener('mousedown', (e) => {
                isMouseDown = true;
                mouseX = e.clientX;
                mouseY = e.clientY;
            });
            
            container.addEventListener('mouseup', () => {
                isMouseDown = false;
            });
            
            container.addEventListener('mousemove', (e) => {
                if (!isMouseDown || !currentMesh) return;
                
                const deltaX = e.clientX - mouseX;
                const deltaY = e.clientY - mouseY;
                
                currentMesh.rotation.y += deltaX * 0.01;
                currentMesh.rotation.x += deltaY * 0.01;
                
                mouseX = e.clientX;
                mouseY = e.clientY;
                
                renderer.render(scene, camera);
            });
        }
        
        // Render STL data
        function renderSTL(stlData) {
            if (!stlData || stlData.trim() === '') {
                modelInfo.textContent = 'No STL data available';
                return;
            }
            
            try {
                const parsed = parseSTL(stlData);
                
                if (currentMesh) {
                    scene.remove(currentMesh);
                }
                
                const geometry = new THREE.BufferGeometry();
                geometry.setAttribute('position', new THREE.BufferAttribute(parsed.vertices, 3));
                if (parsed.normals.length > 0) {
                    geometry.setAttribute('normal', new THREE.BufferAttribute(parsed.normals, 3));
                } else {
                    geometry.computeVertexNormals();
                }
                
                const material = new THREE.MeshLambertMaterial({ 
                    color: 0x007acc,
                    side: THREE.DoubleSide
                });
                
                currentMesh = new THREE.Mesh(geometry, material);
                scene.add(currentMesh);
                
                // Center and scale the model
                const box = new THREE.Box3().setFromObject(currentMesh);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);
                
                currentMesh.position.sub(center);
                if (maxDim > 0) {
                    currentMesh.scale.setScalar(5 / maxDim);
                }
                
                renderer.render(scene, camera);
                
                status.textContent = '✅ Step 3: STL rendered successfully!';
                modelInfo.textContent = 'Triangles: ' + (parsed.vertices.length / 9).toFixed(0);
                
            } catch (error) {
                status.textContent = '❌ STL Error: ' + error.message;
                modelInfo.textContent = 'Parse failed';
                console.error('STL parsing error:', error);
            }
        }
        
        try {
            await initThreeJS();
            status.textContent = 'Three.js ready, waiting for STL...';
            
            // Initial render
            const initialSTL = model.get('stl_data') || '';
            if (initialSTL) {
                renderSTL(initialSTL);
            }
            
            // Listen for STL updates
            model.on('change:stl_data', () => {
                const newSTL = model.get('stl_data') || '';
                renderSTL(newSTL);
            });
            
            console.log('✅ Step 3: STL viewer initialized');
            
        } catch (error) {
            status.textContent = '❌ Error: ' + error.message;
            status.style.background = 'rgba(220,53,69,0.9)';
            console.error('❌ Step 3 error:', error);
        }
    }
    
    export default { render };
    """
    
    def __init__(self, model=None, renderer_type="auto", **kwargs):
        super().__init__()
        self.renderer_type = renderer_type
        if model is not None:
            self.update_model(model)
    
    def update_model(self, model):
        """Convert SolidPython2 object to STL"""
        try:
            # Get SCAD code from model
            scad_code = model.as_scad()
            self.scad_code = scad_code
            
            # Try to generate STL using OpenSCAD (if available)
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as scad_file:
                    scad_file.write(scad_code)
                    scad_path = scad_file.name
                
                stl_path = scad_path.replace('.scad', '.stl')
                
                # Try OpenSCAD command
                result = subprocess.run([
                    'openscad', '-o', stl_path, scad_path
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and Path(stl_path).exists():
                    with open(stl_path, 'r') as f:
                        self.stl_data = f.read()
                    self.error_message = ""
                else:
                    # Fallback: Create simple STL for testing
                    self.stl_data = self._create_test_stl()
                    self.error_message = "OpenSCAD not available, using test geometry"
                
                # Cleanup
                Path(scad_path).unlink(missing_ok=True)
                Path(stl_path).unlink(missing_ok=True)
                
            except Exception as e:
                # Fallback: Create simple test STL
                self.stl_data = self._create_test_stl()
                self.error_message = f"STL generation failed: {e}"
                
        except Exception as e:
            self.error_message = f"Model processing failed: {e}"
    
    def _create_test_stl(self):
        """Create a complete test STL (cube with all 6 faces)"""
        return """solid cube
facet normal 0 0 1
  outer loop
    vertex 0 0 1
    vertex 1 0 1
    vertex 1 1 1
  endloop
endfacet
facet normal 0 0 1
  outer loop
    vertex 0 0 1
    vertex 1 1 1
    vertex 0 1 1
  endloop
endfacet
facet normal 0 0 -1
  outer loop
    vertex 0 0 0
    vertex 1 1 0
    vertex 1 0 0
  endloop
endfacet
facet normal 0 0 -1
  outer loop
    vertex 0 0 0
    vertex 0 1 0
    vertex 1 1 0
  endloop
endfacet
facet normal 1 0 0
  outer loop
    vertex 1 0 0
    vertex 1 1 0
    vertex 1 1 1
  endloop
endfacet
facet normal 1 0 0
  outer loop
    vertex 1 0 0
    vertex 1 1 1
    vertex 1 0 1
  endloop
endfacet
facet normal -1 0 0
  outer loop
    vertex 0 0 0
    vertex 0 1 1
    vertex 0 1 0
  endloop
endfacet
facet normal -1 0 0
  outer loop
    vertex 0 0 0
    vertex 0 0 1
    vertex 0 1 1
  endloop
endfacet
facet normal 0 1 0
  outer loop
    vertex 0 1 0
    vertex 0 1 1
    vertex 1 1 1
  endloop
endfacet
facet normal 0 1 0
  outer loop
    vertex 0 1 0
    vertex 1 1 1
    vertex 1 1 0
  endloop
endfacet
facet normal 0 -1 0
  outer loop
    vertex 0 0 0
    vertex 1 0 1
    vertex 0 0 1
  endloop
endfacet
facet normal 0 -1 0
  outer loop
    vertex 0 0 0
    vertex 1 0 0
    vertex 1 0 1
  endloop
endfacet
endsolid cube"""

def openscad_viewer(model, renderer_type="auto", **kwargs):
    """Step 3: STL parsing viewer factory"""
    return OpenSCADViewer(model=model, renderer_type=renderer_type, **kwargs)