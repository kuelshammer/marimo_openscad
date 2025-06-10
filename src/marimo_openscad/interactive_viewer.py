"""
Interactive 3D Viewer

anywidget-based 3D viewer for OpenSCAD models with Three.js rendering,
mouse controls, and progressive fallback system.
"""

import base64
import logging
from typing import Optional

import anywidget
import traitlets

from .solid_bridge import SolidPythonBridge

# Configure logging
logger = logging.getLogger(__name__)

class InteractiveViewer(anywidget.AnyWidget):
    """
    Interactive 3D viewer for OpenSCAD models
    
    Features:
    - WebGL rendering with Three.js
    - Mouse controls (drag to rotate, wheel to zoom)
    - Progressive fallback system (STL → Procedural → Test cube)
    - Real-time parameter updates via traits
    """
    
    # JavaScript/CSS for the widget
    _esm = """
    function render({ model, el }) {
        el.innerHTML = '<div style="width:600px; height:400px; border:1px solid #333; background:#1a1a1a; color:white; display:flex; align-items:center; justify-content:center;">Loading 3D Viewer...</div>';
        
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
        
        script.onload = () => {
            setTimeout(() => {
                const scene = new THREE.Scene();
                const camera = new THREE.PerspectiveCamera(75, 600/400, 0.1, 1000);
                const renderer = new THREE.WebGLRenderer({ antialias: true });
                renderer.setSize(600, 400);
                renderer.setClearColor(0x1a1a1a);
                
                el.innerHTML = '';
                el.appendChild(renderer.domElement);
                
                // Mouse controls for camera
                let isDragging = false;
                let previousMousePosition = { x: 0, y: 0 };
                let cameraRotation = { x: 0.3, y: 0.5 };
                let cameraDistance = 500;
                
                renderer.domElement.addEventListener('mousedown', (e) => {
                    isDragging = true;
                    previousMousePosition = { x: e.clientX, y: e.clientY };
                });
                
                renderer.domElement.addEventListener('mousemove', (e) => {
                    if (isDragging) {
                        const deltaX = e.clientX - previousMousePosition.x;
                        const deltaY = e.clientY - previousMousePosition.y;
                        
                        cameraRotation.y += deltaX * 0.01;
                        cameraRotation.x += deltaY * 0.01;
                        
                        // Limit vertical rotation
                        cameraRotation.x = Math.max(-Math.PI/2, Math.min(Math.PI/2, cameraRotation.x));
                        
                        updateCameraPosition();
                        previousMousePosition = { x: e.clientX, y: e.clientY };
                    }
                });
                
                renderer.domElement.addEventListener('mouseup', () => {
                    isDragging = false;
                });
                
                renderer.domElement.addEventListener('wheel', (e) => {
                    e.preventDefault();
                    cameraDistance *= e.deltaY > 0 ? 1.1 : 0.9;
                    cameraDistance = Math.max(50, Math.min(2000, cameraDistance));
                    updateCameraPosition();
                });
                
                function updateCameraPosition() {
                    const x = cameraDistance * Math.cos(cameraRotation.x) * Math.cos(cameraRotation.y);
                    const y = cameraDistance * Math.cos(cameraRotation.x) * Math.sin(cameraRotation.y);
                    const z = cameraDistance * Math.sin(cameraRotation.x);
                    
                    camera.position.set(x, y, z);
                    camera.lookAt(0, 0, 0);
                }
                
                // Lighting setup
                scene.add(new THREE.AmbientLight(0x404040, 0.6));
                const light = new THREE.DirectionalLight(0xffffff, 0.8);
                light.position.set(10, 10, 5);
                scene.add(light);
                
                // Get STL data from model
                const stlData = model.get('stl_data');
                
                if (stlData && stlData.length > 100) {
                    try {
                        console.log('Parsing STL data...');
                        const geometry = parseSTL(stlData);
                        const material = new THREE.MeshPhongMaterial({color: 0x8B4513});
                        const mesh = new THREE.Mesh(geometry, material);
                        
                        // Center the model
                        geometry.computeBoundingBox();
                        const center = geometry.boundingBox.getCenter(new THREE.Vector3());
                        mesh.position.sub(center);
                        scene.add(mesh);
                        
                        // Set camera distance based on model size
                        const size = geometry.boundingBox.getSize(new THREE.Vector3());
                        const maxDim = Math.max(size.x, size.y, size.z);
                        cameraDistance = maxDim * 2;
                        updateCameraPosition();
                        
                        console.log('STL model loaded successfully');
                        
                    } catch (error) {
                        console.error('STL parsing failed:', error);
                        createFallbackCube();
                    }
                } else {
                    console.log('No STL data available, showing test cube');
                    createFallbackCube();
                }
                
                function createFallbackCube() {
                    // Show a colored test cube if STL fails
                    const geometry = new THREE.BoxGeometry(20, 20, 20);
                    const material = new THREE.MeshPhongMaterial({color: 0x00ff00});
                    const cube = new THREE.Mesh(geometry, material);
                    scene.add(cube);
                    cameraDistance = 100;
                    updateCameraPosition();
                }
                
                // Animation loop
                function animate() {
                    requestAnimationFrame(animate);
                    renderer.render(scene, camera);
                }
                animate();
                
                // Instructions overlay
                const instructions = document.createElement('div');
                instructions.innerHTML = 'Mouse: Drag to rotate • Wheel: Zoom';
                instructions.style.cssText = 'position:absolute; bottom:10px; left:10px; color:#ccc; font-size:12px; font-family:monospace; pointer-events:none;';
                el.style.position = 'relative';
                el.appendChild(instructions);
                
            }, 100);
        };
        
        script.onerror = () => {
            el.innerHTML = '<div style="color:red; padding:20px;">Failed to load Three.js library</div>';
        };
        
        document.head.appendChild(script);
        
        // STL parser function
        function parseSTL(base64Data) {
            console.log('Parsing STL, base64 length:', base64Data.length);
            
            // Decode base64 to binary
            const binaryString = atob(base64Data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            console.log('Binary data length:', bytes.length);
            
            // Read triangle count from STL header
            const triangleCount = new DataView(bytes.buffer, 80, 4).getUint32(0, true);
            console.log('Triangle count:', triangleCount);
            
            // Limit triangles for performance
            const maxTriangles = Math.min(triangleCount, 2000);
            
            const geometry = new THREE.BufferGeometry();
            const vertices = new Float32Array(maxTriangles * 9); // 3 vertices × 3 coordinates
            
            let offset = 84; // Skip 80-byte header + 4-byte triangle count
            
            for (let i = 0; i < maxTriangles; i++) {
                // Skip 12-byte normal vector
                offset += 12;
                
                // Read 3 vertices (9 floats total)
                for (let j = 0; j < 9; j++) {
                    const view = new DataView(bytes.buffer, offset + j * 4, 4);
                    vertices[i * 9 + j] = view.getFloat32(0, true);
                }
                
                offset += 36; // 9 floats × 4 bytes
                offset += 2;  // Skip 2-byte attribute count
            }
            
            geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
            geometry.computeVertexNormals();
            
            console.log('Geometry created with', vertices.length/3, 'vertices');
            return geometry;
        }
        
        // Update model when stl_data changes
        model.on('change:stl_data', () => {
            console.log('STL data updated, reloading...');
            render({ model, el });
        });
    }
    export default { render };
    """
    
    # Widget traits (synchronized with Python)
    stl_data = traitlets.Unicode(default_value="").tag(sync=True)
    
    def __init__(self, **kwargs):
        """Initialize the interactive viewer"""
        super().__init__(**kwargs)
        self.bridge = SolidPythonBridge()
        logger.info("Interactive viewer initialized")
    
    def force_update_model(self, model) -> None:
        """
        Force update the model, bypassing any caching
        
        Args:
            model: SolidPython2 object to render
        """
        self.update_model(model, force_render=True)
    
    def update_scad_code(self, scad_code: str) -> None:
        """
        Update the viewer with new SCAD code directly
        
        This method bypasses SolidPython2 and renders SCAD code directly,
        ensuring that code changes are immediately reflected in the viewer.
        
        Args:
            scad_code: Raw OpenSCAD code as string
        """
        try:
            # Store previous STL data for comparison
            previous_stl = self.stl_data
            
            # Render SCAD code directly to STL (no caching for code updates)
            stl_data = self.bridge.renderer.render_scad_to_stl(scad_code)
            
            # Convert to base64 for JavaScript transmission
            stl_base64 = base64.b64encode(stl_data).decode('utf-8')
            
            # Always update even if data appears same (code might have changed)
            self.stl_data = stl_base64
            
            logger.info(f"SCAD code updated: {len(stl_data)} bytes STL from {len(scad_code)} chars SCAD")
            logger.info(f"STL data changed: {stl_base64 != previous_stl}")
            
        except Exception as e:
            logger.error(f"SCAD code update failed: {e}")
            # Clear STL data to show error state
            self.stl_data = ""
    
    def clear_model_cache(self) -> None:
        """
        Clear the model rendering cache to ensure fresh renders
        """
        self.bridge.clear_cache()
        logger.info("Model cache cleared via interactive viewer")
    
    def update_model(self, model, force_render: bool = False) -> None:
        """
        Update the 3D model displayed in the viewer
        
        Args:
            model: SolidPython2 object to render
            force_render: Force re-rendering even if cached (default False)
        """
        try:
            # Store previous STL data for comparison
            previous_stl = self.stl_data
            
            # Render model to STL (optionally bypassing cache)
            stl_data = self.bridge.render_to_stl(model, use_cache=not force_render)
            
            # Convert to base64 for JavaScript transmission
            stl_base64 = base64.b64encode(stl_data).decode('utf-8')
            
            # Check if STL data actually changed
            if stl_base64 == previous_stl and not force_render:
                logger.info("Model unchanged, skipping update")
                return
            
            # Update widget trait (triggers JavaScript update)
            self.stl_data = stl_base64
            
            # Log cache info for debugging
            cache_info = self.bridge.get_cache_info()
            logger.info(f"Model updated: {len(stl_data)} bytes STL, {len(stl_base64)} chars base64")
            logger.info(f"Cache info: {cache_info['cache_size']} entries")
            
        except Exception as e:
            logger.error(f"Model update failed: {e}")
            # Clear STL data to show fallback cube
            self.stl_data = ""
    
    def save_stl(self, model, file_path: str) -> None:
        """
        Save the current model as an STL file
        
        Args:
            model: SolidPython2 object to save
            file_path: Path where to save the STL file
        """
        try:
            self.bridge.save_model_to_stl(model, file_path)
            logger.info(f"Model saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise