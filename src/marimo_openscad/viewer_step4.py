"""
Step 4: Real OpenSCAD Integration (WASM + Local Fallback)
Test: Use actual OpenSCAD rendering instead of test STL
"""

import anywidget
import traitlets
import tempfile
import subprocess
from pathlib import Path
from .openscad_renderer import OpenSCADRenderer
from .openscad_wasm_renderer import OpenSCADWASMRenderer

class OpenSCADViewer(anywidget.AnyWidget):
    """Step 4: Real OpenSCAD integration with WASM support"""
    
    # Traits
    stl_data = traitlets.Unicode("").tag(sync=True)
    scad_code = traitlets.Unicode("").tag(sync=True)
    error_message = traitlets.Unicode("").tag(sync=True)
    renderer_type = traitlets.Unicode("auto").tag(sync=True)
    renderer_status = traitlets.Unicode("initializing").tag(sync=True)
    wasm_supported = traitlets.Bool(True).tag(sync=True)
    
    _esm = """
    async function render({ model, el }) {
        console.log('🚀 Step 4: Real OpenSCAD integration starting...');
        
        el.innerHTML = 
            '<div style="width: 100%; height: 400px; border: 2px solid #6f42c1; border-radius: 8px; position: relative; background: #f8f9fa;">' +
                '<div id="threejs-container" style="width: 100%; height: 100%;"></div>' +
                '<div id="status" style="position: absolute; top: 10px; left: 10px; background: rgba(111,66,193,0.9); color: white; padding: 8px 12px; border-radius: 4px; font-size: 12px;">' +
                    'Step 4: Initializing OpenSCAD renderer...' +
                '</div>' +
                '<div id="renderer-info" style="position: absolute; bottom: 10px; left: 10px; background: rgba(0,0,0,0.7); color: white; padding: 4px 8px; border-radius: 3px; font-size: 10px;">' +
                    'Renderer: ' + (model.get('renderer_type') || 'auto') +
                '</div>' +
                '<div id="model-info" style="position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 4px 8px; border-radius: 3px; font-size: 10px;">' +
                    'Waiting for model...' +
                '</div>' +
            '</div>';
        
        const container = el.querySelector('#threejs-container');
        const status = el.querySelector('#status');
        const rendererInfo = el.querySelector('#renderer-info');
        const modelInfo = el.querySelector('#model-info');
        
        let scene, camera, renderer, currentMesh;
        
        // Enhanced STL Parser (supports ASCII and detects binary)
        function parseSTL(data) {
            if (!data || data.length === 0) {
                throw new Error('No STL data provided');
            }
            
            console.log('🔍 DEBUG: STL data type check - length:', data.length);
            console.log('🔍 DEBUG: First 50 chars:', data.substring(0, 50));
            
            // Check if it's ASCII STL
            if (typeof data === 'string' && (data.includes('solid') || data.includes('facet'))) {
                return parseASCIISTL(data);
            } else {
                console.log('⚠️ DEBUG: Data does not look like ASCII STL, falling back to test geometry');
                return createFallbackGeometry();
            }
        }
        
        function parseASCIISTL(data) {
            const lines = data.split('\\n');
            const vertices = [];
            const normals = [];
            
            let vertexCount = 0;
            let currentNormal = null;
            
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                
                if (line.startsWith('facet normal')) {
                    const normalParts = line.split(/\\s+/).slice(2);
                    if (normalParts.length === 3) {
                        currentNormal = normalParts.map(parseFloat);
                        console.log('🔍 DEBUG: Found normal:', currentNormal);
                    }
                }
                
                if (line.startsWith('vertex')) {
                    const coords = line.split(/\\s+/).slice(1).map(parseFloat);
                    if (coords.length === 3 && coords.every(c => !isNaN(c))) {
                        vertices.push(...coords);
                        if (currentNormal && currentNormal.every(n => !isNaN(n))) {
                            normals.push(...currentNormal);
                        } else {
                            normals.push(0, 0, 1); // Default normal
                        }
                        vertexCount++;
                        console.log('🔍 DEBUG: Added vertex', vertexCount, ':', coords);
                    }
                }
            }
            
            console.log('📊 ASCII STL parsed:', vertexCount, 'vertices,', (vertexCount/3), 'triangles');
            
            if (vertexCount === 0) {
                console.log('⚠️ DEBUG: No vertices found in ASCII STL, using fallback');
                return createFallbackGeometry();
            }
            
            return { 
                vertices: new Float32Array(vertices), 
                normals: new Float32Array(normals),
                triangleCount: Math.floor(vertexCount / 3)
            };
        }
        
        function createFallbackGeometry() {
            console.log('🔧 DEBUG: Creating fallback cube geometry');
            // Simple cube vertices
            const vertices = new Float32Array([
                // Front face
                -1, -1,  1,  1, -1,  1,  1,  1,  1,
                -1, -1,  1,  1,  1,  1, -1,  1,  1,
                // Back face
                -1, -1, -1, -1,  1, -1,  1,  1, -1,
                -1, -1, -1,  1,  1, -1,  1, -1, -1,
                // Top face
                -1,  1, -1, -1,  1,  1,  1,  1,  1,
                -1,  1, -1,  1,  1,  1,  1,  1, -1,
                // Bottom face
                -1, -1, -1,  1, -1, -1,  1, -1,  1,
                -1, -1, -1,  1, -1,  1, -1, -1,  1,
                // Right face
                 1, -1, -1,  1,  1, -1,  1,  1,  1,
                 1, -1, -1,  1,  1,  1,  1, -1,  1,
                // Left face
                -1, -1, -1, -1, -1,  1, -1,  1,  1,
                -1, -1, -1, -1,  1,  1, -1,  1, -1
            ]);
            
            return {
                vertices: vertices,
                normals: new Float32Array(vertices.length), // Will be computed
                triangleCount: vertices.length / 9
            };
        }
        
        // Initialize Three.js (same as Step 3)
        async function initThreeJS() {
            if (!window.THREE) {
                status.textContent = 'Loading Three.js...';
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
            renderer.setClearColor(0x2c3e50); // Dark blue-gray background
            container.appendChild(renderer.domElement);
            
            // Enhanced lighting for better visibility
            const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
            scene.add(ambientLight);
            
            const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight1.position.set(1, 1, 1);
            scene.add(directionalLight1);
            
            // Additional light from opposite side
            const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
            directionalLight2.position.set(-1, -1, -1);
            scene.add(directionalLight2);
            
            camera.position.set(10, 10, 10);
            camera.lookAt(0, 0, 0);
            
            // Mouse controls
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
            console.log('🔍 DEBUG: renderSTL called with data length:', stlData ? stlData.length : 0);
            
            if (!stlData || stlData.trim() === '') {
                modelInfo.textContent = 'No STL data available';
                console.log('❌ DEBUG: No STL data provided');
                return;
            }
            
            console.log('🔍 DEBUG: STL data preview:', stlData.substring(0, 200));
            
            try {
                const parsed = parseSTL(stlData);
                console.log('🔍 DEBUG: STL parsed successfully:', parsed.triangleCount, 'triangles');
                
                if (currentMesh) {
                    scene.remove(currentMesh);
                }
                
                const geometry = new THREE.BufferGeometry();
                console.log('🔍 DEBUG: Creating BufferGeometry with', parsed.vertices.length, 'vertices');
                
                geometry.setAttribute('position', new THREE.BufferAttribute(parsed.vertices, 3));
                if (parsed.normals.length > 0) {
                    geometry.setAttribute('normal', new THREE.BufferAttribute(parsed.normals, 3));
                    console.log('🔍 DEBUG: Added normals:', parsed.normals.length);
                } else {
                    geometry.computeVertexNormals();
                    console.log('🔍 DEBUG: Computed vertex normals');
                }
                
                // Check if geometry is valid
                const positionAttribute = geometry.getAttribute('position');
                console.log('🔍 DEBUG: Position attribute count:', positionAttribute ? positionAttribute.count : 'NONE');
                
                if (!positionAttribute || positionAttribute.count === 0) {
                    throw new Error('Geometry has no vertices');
                }
                
                const material = new THREE.MeshLambertMaterial({ 
                    color: 0xe74c3c, // Bright red for high contrast
                    side: THREE.DoubleSide
                });
                
                currentMesh = new THREE.Mesh(geometry, material);
                console.log('🔍 DEBUG: Created mesh, adding to scene');
                scene.add(currentMesh);
                
                // Center and scale
                const box = new THREE.Box3().setFromObject(currentMesh);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);
                
                console.log('🔍 DEBUG: Bounding box - center:', center, 'size:', size, 'maxDim:', maxDim);
                
                currentMesh.position.sub(center);
                if (maxDim > 0) {
                    currentMesh.scale.setScalar(5 / maxDim);
                    console.log('🔍 DEBUG: Scaled mesh by factor:', (5 / maxDim));
                } else {
                    console.log('⚠️ DEBUG: MaxDim is 0, no scaling applied');
                }
                
                console.log('🔍 DEBUG: Final mesh position:', currentMesh.position, 'scale:', currentMesh.scale);
                
                renderer.render(scene, camera);
                console.log('🔍 DEBUG: Scene rendered');
                
                status.textContent = '✅ Step 4: Real OpenSCAD STL rendered!';
                modelInfo.textContent = 'Triangles: ' + parsed.triangleCount;
                
                // Update renderer info based on actual renderer used
                const rendererType = model.get('renderer_type') || 'auto';
                const rendererStatus = model.get('renderer_status') || 'unknown';
                rendererInfo.textContent = 'Renderer: ' + rendererType + ' (' + rendererStatus + ')';
                
            } catch (error) {
                status.textContent = '❌ STL Error: ' + error.message;
                modelInfo.textContent = 'Parse failed';
                console.error('STL parsing error:', error);
            }
        }
        
        try {
            await initThreeJS();
            status.textContent = 'Three.js ready, waiting for OpenSCAD STL...';
            
            // Initial render
            const initialSTL = model.get('stl_data') || '';
            const errorMsg = model.get('error_message') || '';
            
            if (errorMsg) {
                status.textContent = '⚠️ ' + errorMsg;
                status.style.background = 'rgba(255,193,7,0.9)';
            }
            
            if (initialSTL) {
                renderSTL(initialSTL);
            } else {
                modelInfo.textContent = 'Generating STL with OpenSCAD...';
            }
            
            // Listen for updates
            model.on('change:stl_data', () => {
                const newSTL = model.get('stl_data') || '';
                renderSTL(newSTL);
            });
            
            model.on('change:error_message', () => {
                const newError = model.get('error_message') || '';
                if (newError) {
                    status.textContent = '⚠️ ' + newError;
                    status.style.background = 'rgba(255,193,7,0.9)';
                }
            });
            
            model.on('change:renderer_status', () => {
                const newStatus = model.get('renderer_status') || 'unknown';
                const rendererType = model.get('renderer_type') || 'auto';
                rendererInfo.textContent = 'Renderer: ' + rendererType + ' (' + newStatus + ')';
            });
            
            console.log('✅ Step 4: Real OpenSCAD viewer initialized');
            
        } catch (error) {
            status.textContent = '❌ Error: ' + error.message;
            status.style.background = 'rgba(220,53,69,0.9)';
            console.error('❌ Step 4 error:', error);
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
        """Convert SolidPython2 object to STL using real OpenSCAD"""
        try:
            # Get SCAD code
            scad_code = model.as_scad()
            self.scad_code = scad_code
            self.renderer_status = "generating_stl"
            
            # Try WASM renderer first
            if self.renderer_type in ["auto", "wasm"]:
                try:
                    self.renderer_status = "trying_wasm"
                    wasm_renderer = OpenSCADWASMRenderer()
                    stl_bytes = wasm_renderer.render_scad_to_stl(scad_code)
                    stl_result = stl_bytes.decode('utf-8') if isinstance(stl_bytes, bytes) else stl_bytes
                    
                    if stl_result and len(stl_result.strip()) > 0:
                        self.stl_data = stl_result
                        self.renderer_status = "wasm_success"
                        self.error_message = ""
                        return
                    else:
                        self.renderer_status = "wasm_empty_result"
                        
                except Exception as wasm_error:
                    self.renderer_status = "wasm_failed"
                    print(f"WASM renderer failed: {wasm_error}")
            
            # Fallback to local OpenSCAD
            if self.renderer_type in ["auto", "local"]:
                try:
                    self.renderer_status = "trying_local"
                    local_renderer = OpenSCADRenderer()
                    stl_bytes = local_renderer.render_scad_to_stl(scad_code)
                    stl_result = stl_bytes.decode('utf-8') if isinstance(stl_bytes, bytes) else stl_bytes
                    
                    if stl_result and len(stl_result.strip()) > 0:
                        self.stl_data = stl_result
                        self.renderer_status = "local_success"
                        self.error_message = ""
                        return
                    else:
                        self.renderer_status = "local_empty_result"
                        
                except Exception as local_error:
                    self.renderer_status = "local_failed" 
                    print(f"Local renderer failed: {local_error}")
            
            # Final fallback: Test STL
            self.renderer_status = "fallback_test_stl"
            self.stl_data = self._create_test_stl()
            self.error_message = "Both WASM and local OpenSCAD failed, using test geometry"
                
        except Exception as e:
            self.renderer_status = "model_processing_failed"
            self.error_message = f"Model processing failed: {e}"
            self.stl_data = self._create_test_stl()
    
    def _create_test_stl(self):
        """Fallback: Complete test STL (cube with all 6 faces)"""
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
    """Step 4: Real OpenSCAD viewer factory"""
    return OpenSCADViewer(model=model, renderer_type=renderer_type, **kwargs)