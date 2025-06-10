"""
JupyterSCAD-Style 3D Viewer für Marimo
Echte STL-Pipeline: SolidPython2 → OpenSCAD → STL → Three.js

Inspired by JupyterSCAD's architecture with modern anywidget integration.
"""

import anywidget
import traitlets
import tempfile
import subprocess
import base64
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class OpenSCADViewer(anywidget.AnyWidget):
    """
    3D-Viewer für SolidPython2-Objekte mit JupyterSCAD-kompatible Pipeline
    
    Pipeline: SolidPython2 → OpenSCAD CLI → STL → Three.js BufferGeometry
    """
    
    stl_data = traitlets.Unicode("").tag(sync=True)
    error_message = traitlets.Unicode("").tag(sync=True)
    is_loading = traitlets.Bool(False).tag(sync=True)
    
    _esm = """
    async function render({ model, el }) {
        // Container Setup
        el.innerHTML = `
            <div style="width: 100%; height: 450px; border: 1px solid #ddd; position: relative; background: #fafafa;">
                <div id="container" style="width: 100%; height: 100%;"></div>
                <div id="status" style="position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.8); color: white; padding: 8px 12px; border-radius: 4px; font-family: monospace; font-size: 12px;">
                    Initializing 3D viewer...
                </div>
                <div id="controls" style="position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.9); padding: 8px; border-radius: 4px; font-size: 11px;">
                    🖱️ Drag: Rotate | 🔍 Wheel: Zoom
                </div>
            </div>
        `;
        
        const container = el.querySelector('#container');
        const status = el.querySelector('#status');
        
        try {
            // Three.js laden (robuste Multi-CDN-Strategie)
            status.textContent = "Loading Three.js...";
            
            if (!window.THREE) {
                const threeSources = [
                    'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
                    'https://unpkg.com/three@0.128.0/build/three.min.js',
                    'https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js'
                ];
                
                let loaded = false;
                for (const src of threeSources) {
                    try {
                        const script = document.createElement('script');
                        script.src = src;
                        document.head.appendChild(script);
                        
                        await new Promise((resolve, reject) => {
                            script.onload = resolve;
                            script.onerror = reject;
                            setTimeout(reject, 8000);
                        });
                        
                        if (window.THREE) {
                            loaded = true;
                            console.log("✅ Three.js loaded from:", src);
                            break;
                        }
                    } catch (e) {
                        console.warn(`Three.js CDN ${src} failed:`, e);
                        continue;
                    }
                }
                
                if (!loaded) {
                    throw new Error("Could not load Three.js from any CDN");
                }
            }
            
            status.textContent = "Setting up 3D scene...";
            
            // Three.js Scene Setup
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf8f9fa);
            
            // Camera setup
            const rect = container.getBoundingClientRect();
            const camera = new THREE.PerspectiveCamera(45, rect.width / rect.height, 0.1, 1000);
            
            // Renderer - optimiert gegen Rendering-Artefakte
            const renderer = new THREE.WebGLRenderer({ 
                antialias: true,
                alpha: true,
                powerPreference: "high-performance",
                precision: "highp",
                stencil: false,
                depth: true
            });
            renderer.setSize(rect.width, rect.height);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            renderer.sortObjects = true;
            renderer.toneMapping = THREE.LinearToneMapping;
            container.appendChild(renderer.domElement);
            
            // Lighting Setup
            const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
            scene.add(ambientLight);
            
            const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.7);
            directionalLight1.position.set(10, 10, 5);
            directionalLight1.castShadow = true;
            scene.add(directionalLight1);
            
            const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
            directionalLight2.position.set(-5, -5, -5);
            scene.add(directionalLight2);
            
            // Grid Helper
            const gridHelper = new THREE.GridHelper(50, 50, 0x888888, 0xcccccc);
            gridHelper.position.y = -0.5;
            scene.add(gridHelper);
            
            // Mouse Controls
            let mouseDown = false;
            let mouseX = 0, mouseY = 0;
            let cameraDistance = 50;
            let cameraTheta = Math.PI / 4, cameraPhi = Math.PI / 4;
            
            function updateCameraPosition() {
                camera.position.x = cameraDistance * Math.sin(cameraPhi) * Math.cos(cameraTheta);
                camera.position.y = cameraDistance * Math.cos(cameraPhi);
                camera.position.z = cameraDistance * Math.sin(cameraPhi) * Math.sin(cameraTheta);
                camera.lookAt(0, 0, 0);
            }
            
            renderer.domElement.addEventListener('mousedown', (e) => {
                mouseDown = true;
                mouseX = e.clientX;
                mouseY = e.clientY;
            });
            
            renderer.domElement.addEventListener('mousemove', (e) => {
                if (!mouseDown) return;
                
                const deltaX = e.clientX - mouseX;
                const deltaY = e.clientY - mouseY;
                
                cameraTheta += deltaX * 0.01;
                cameraPhi = Math.max(0.1, Math.min(Math.PI - 0.1, cameraPhi + deltaY * 0.01));
                
                updateCameraPosition();
                
                mouseX = e.clientX;
                mouseY = e.clientY;
            });
            
            renderer.domElement.addEventListener('mouseup', () => {
                mouseDown = false;
            });
            
            renderer.domElement.addEventListener('wheel', (e) => {
                e.preventDefault();
                cameraDistance = Math.max(5, Math.min(200, cameraDistance + e.deltaY * 0.05));
                updateCameraPosition();
            });
            
            updateCameraPosition();
            
            let currentMesh = null;
            
            // STL Parser (nach Three.js STLLoader)
            class STLParser {
                static parseSTL(data) {
                    if (data instanceof ArrayBuffer) {
                        return this.parseBinary(data);
                    } else {
                        return this.parseASCII(data);
                    }
                }
                
                static parseBinary(data) {
                    const reader = new DataView(data);
                    const faces = reader.getUint32(80, true);
                    
                    console.log(`📦 Parsing binary STL: ${faces} faces`);
                    
                    const vertices = [];
                    const normals = [];
                    
                    for (let face = 0; face < faces; face++) {
                        const start = 84 + face * 50;
                        
                        // Normal vector
                        const normalX = reader.getFloat32(start, true);
                        const normalY = reader.getFloat32(start + 4, true);
                        const normalZ = reader.getFloat32(start + 8, true);
                        
                        // 3 vertices
                        for (let i = 0; i < 3; i++) {
                            const vertexstart = start + 12 + i * 12;
                            
                            vertices.push(
                                reader.getFloat32(vertexstart, true),
                                reader.getFloat32(vertexstart + 4, true),
                                reader.getFloat32(vertexstart + 8, true)
                            );
                            
                            normals.push(normalX, normalY, normalZ);
                        }
                    }
                    
                    return { vertices, normals };
                }
                
                static parseASCII(data) {
                    console.log("📄 Parsing ASCII STL");
                    
                    const vertices = [];
                    const normals = [];
                    const lines = data.split('\\n');
                    let currentNormal = [0, 0, 1];
                    let currentVertices = [];
                    
                    for (let line of lines) {
                        line = line.trim();
                        
                        if (line.startsWith('facet normal')) {
                            const parts = line.split(/\\s+/);
                            currentNormal = [
                                parseFloat(parts[2]) || 0,
                                parseFloat(parts[3]) || 0, 
                                parseFloat(parts[4]) || 0
                            ];
                            currentVertices = [];
                        }
                        else if (line.startsWith('vertex')) {
                            const parts = line.split(/\\s+/);
                            const vertex = [
                                parseFloat(parts[1]) || 0,
                                parseFloat(parts[2]) || 0,
                                parseFloat(parts[3]) || 0
                            ];
                            currentVertices.push(vertex);
                        }
                        else if (line.startsWith('endloop')) {
                            if (currentVertices.length === 3) {
                                for (let i = 0; i < 3; i++) {
                                    vertices.push(currentVertices[i][0], currentVertices[i][1], currentVertices[i][2]);
                                    normals.push(currentNormal[0], currentNormal[1], currentNormal[2]);
                                }
                            }
                        }
                    }
                    
                    console.log(`📄 ASCII STL parsed: ${vertices.length/3} vertices`);
                    return { vertices, normals };
                }
                
                static createBufferGeometry(parsed) {
                    const geometry = new THREE.BufferGeometry();
                    
                    geometry.setAttribute('position', 
                        new THREE.BufferAttribute(new Float32Array(parsed.vertices), 3));
                    
                    // Validierte Normalen
                    if (parsed.normals && parsed.normals.length === parsed.vertices.length) {
                        const validatedNormals = [];
                        for (let i = 0; i < parsed.normals.length; i += 3) {
                            let nx = parsed.normals[i] || 0;
                            let ny = parsed.normals[i + 1] || 0;
                            let nz = parsed.normals[i + 2] || 0;
                            
                            const length = Math.sqrt(nx*nx + ny*ny + nz*nz);
                            if (length > 0) {
                                nx /= length; ny /= length; nz /= length;
                            } else {
                                nx = 0; ny = 0; nz = 1;
                            }
                            
                            validatedNormals.push(nx, ny, nz);
                        }
                        
                        geometry.setAttribute('normal', 
                            new THREE.BufferAttribute(new Float32Array(validatedNormals), 3));
                    } else {
                        geometry.computeVertexNormals();
                    }
                    
                    geometry.computeBoundingBox();
                    geometry.computeBoundingSphere();
                    
                    return geometry;
                }
            }
            
            // STL-Daten verarbeiten
            function processSTLData(base64STL) {
                try {
                    status.textContent = "Processing STL data...";
                    
                    if (!base64STL || base64STL.length < 100) {
                        throw new Error("No valid STL data received");
                    }
                    
                    // Base64 → Binary
                    const binaryString = atob(base64STL);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    
                    // STL parsen
                    let parsed;
                    if (bytes.length >= 84) {
                        try {
                            parsed = STLParser.parseBinary(bytes.buffer);
                        } catch (e) {
                            const textDecoder = new TextDecoder('utf-8');
                            const asciiData = textDecoder.decode(bytes);
                            parsed = STLParser.parseASCII(asciiData);
                        }
                    } else {
                        const textDecoder = new TextDecoder('utf-8');
                        const asciiData = textDecoder.decode(bytes);
                        parsed = STLParser.parseASCII(asciiData);
                    }
                    
                    if (!parsed.vertices || parsed.vertices.length === 0) {
                        throw new Error("STL contains no valid geometry");
                    }
                    
                    const geometry = STLParser.createBufferGeometry(parsed);
                    
                    // Alte Mesh entfernen
                    if (currentMesh) {
                        scene.remove(currentMesh);
                        if (currentMesh.geometry) currentMesh.geometry.dispose();
                        if (currentMesh.material) currentMesh.material.dispose();
                    }
                    
                    // Material - optimiert gegen Artefakte
                    const material = new THREE.MeshLambertMaterial({ 
                        color: 0x3b82f6,
                        side: THREE.FrontSide,
                        wireframe: false,
                        flatShading: false
                    });
                    
                    currentMesh = new THREE.Mesh(geometry, material);
                    currentMesh.castShadow = true;
                    currentMesh.receiveShadow = true;
                    
                    // Auto-Center
                    const box = geometry.boundingBox;
                    const center = box.getCenter(new THREE.Vector3());
                    currentMesh.position.sub(center);
                    
                    scene.add(currentMesh);
                    
                    // Kamera optimal positionieren
                    const size = box.getSize(new THREE.Vector3());
                    const maxDim = Math.max(size.x, size.y, size.z);
                    cameraDistance = Math.max(maxDim * 2.5, 20);
                    updateCameraPosition();
                    
                    status.textContent = `✅ STL loaded: ${parsed.vertices.length/9} triangles`;
                    status.style.background = "rgba(34,197,94,0.9)";
                    
                } catch (error) {
                    console.error("STL Processing Error:", error);
                    status.textContent = `❌ STL Error: ${error.message}`;
                    status.style.background = "rgba(220,20,60,0.9)";
                    createFallbackGeometry();
                }
            }
            
            function createFallbackGeometry() {
                if (currentMesh) {
                    scene.remove(currentMesh);
                    if (currentMesh.geometry) currentMesh.geometry.dispose();
                    if (currentMesh.material) currentMesh.material.dispose();
                }
                
                const geometry = new THREE.BoxGeometry(10, 10, 10);
                const material = new THREE.MeshLambertMaterial({ color: 0xff6b6b });
                currentMesh = new THREE.Mesh(geometry, material);
                scene.add(currentMesh);
                
                status.textContent = "⚠️ Using fallback geometry";
                status.style.background = "rgba(255,193,7,0.9)";
            }
            
            // Model Update Handler
            function updateModel() {
                const stlData = model.get("stl_data") || "";
                const errorMsg = model.get("error_message") || "";
                const isLoading = model.get("is_loading");
                
                if (errorMsg) {
                    status.textContent = `❌ ${errorMsg}`;
                    status.style.background = "rgba(220,20,60,0.9)";
                    return;
                }
                
                if (isLoading) {
                    status.textContent = "🔄 Generating STL...";
                    status.style.background = "rgba(59,130,246,0.9)";
                    return;
                }
                
                if (stlData.trim()) {
                    processSTLData(stlData);
                } else {
                    status.textContent = "⏳ Waiting for STL data...";
                    status.style.background = "rgba(107,114,128,0.9)";
                }
            }
            
            // Event Listeners
            model.on("change:stl_data", updateModel);
            model.on("change:error_message", updateModel);
            model.on("change:is_loading", updateModel);
            
            // Animation Loop
            function animate() {
                requestAnimationFrame(animate);
                renderer.render(scene, camera);
            }
            
            // Window Resize
            function onWindowResize() {
                const rect = container.getBoundingClientRect();
                camera.aspect = rect.width / rect.height;
                camera.updateProjectionMatrix();
                renderer.setSize(rect.width, rect.height);
            }
            window.addEventListener('resize', onWindowResize);
            
            // Initialize
            status.textContent = "🚀 3D viewer ready";
            updateModel();
            animate();
            
        } catch (error) {
            console.error("Viewer initialization error:", error);
            status.textContent = `❌ Init Error: ${error.message}`;
            status.style.background = "rgba(220,20,60,0.9)";
        }
    }
    
    export default { render };
    """
    
    def __init__(self, model=None, **kwargs):
        super().__init__(**kwargs)
        if model is not None:
            self.update_model(model)
    
    def update_model(self, model, force_render: bool = False):
        """Update mit SolidPython2-Objekt - echte STL-Pipeline"""
        try:
            self.is_loading = True
            self.error_message = ""
            
            # Store previous STL for comparison
            previous_stl = self.stl_data
            
            # SolidPython2 → SCAD Code
            if hasattr(model, 'as_scad'):
                scad_code = model.as_scad()
            elif hasattr(model, '__scad__'):
                scad_code = model.__scad__()
            elif isinstance(model, str):
                scad_code = model
            else:
                raise ValueError("Model muss SolidPython2-Objekt mit .as_scad() Methode oder SCAD-String sein")
            
            # SCAD → STL (with optional cache bypass)
            stl_data = self._render_stl(scad_code, force_render)
            
            # STL → Base64 für Browser
            new_stl_base64 = base64.b64encode(stl_data).decode('utf-8')
            
            # Check if STL actually changed
            if new_stl_base64 == previous_stl and not force_render:
                logger.info("Model unchanged, skipping update")
                return
            
            self.stl_data = new_stl_base64
            
            logger.info(f"✅ STL rendered: {len(stl_data)} bytes")
            logger.info(f"STL data changed: {new_stl_base64 != previous_stl}")
            
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"❌ Model update error: {e}")
        finally:
            self.is_loading = False
    
    def update_scad_code(self, scad_code: str) -> None:
        """
        Update viewer with new SCAD code directly, bypassing caching
        
        Args:
            scad_code: Raw OpenSCAD code as string
        """
        try:
            self.is_loading = True
            self.error_message = ""
            
            # Store previous STL for comparison
            previous_stl = self.stl_data
            
            # SCAD → STL (no caching for direct code updates)
            stl_data = self._render_stl(scad_code, force_render=True)
            
            # STL → Base64 für Browser
            new_stl_base64 = base64.b64encode(stl_data).decode('utf-8')
            
            # Always update for code changes
            self.stl_data = new_stl_base64
            
            logger.info(f"✅ SCAD code updated: {len(stl_data)} bytes from {len(scad_code)} chars SCAD")
            logger.info(f"STL data changed: {new_stl_base64 != previous_stl}")
            
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"❌ SCAD code update error: {e}")
        finally:
            self.is_loading = False
    
    def _render_stl(self, scad_code, force_render: bool = False):
        """OpenSCAD Code zu STL mit optionalem Cache-Bypass"""
        # Log for debugging cache behavior
        if force_render:
            logger.info("Force rendering STL (cache bypassed)")
        else:
            logger.info("Normal STL rendering")
            
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            
            # SCAD-Datei schreiben
            scad_file = tmp_dir / "model.scad"
            scad_file.write_text(scad_code)
            
            # STL-Datei generieren  
            stl_file = tmp_dir / "model.stl"
            
            # OpenSCAD-Pfade
            openscad_paths = [
                "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD",  # macOS
                "openscad",  # System PATH
                "./openscad"  # Local
            ]
            
            success = False
            for openscad_path in openscad_paths:
                try:
                    cmd = [openscad_path, "-o", str(stl_file), str(scad_file)]
                    result = subprocess.run(
                        cmd, 
                        capture_output=True, 
                        text=True, 
                        timeout=60
                    )
                    
                    if result.returncode == 0 and stl_file.exists() and stl_file.stat().st_size > 0:
                        success = True
                        break
                        
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            if not success or not stl_file.exists():
                raise RuntimeError("OpenSCAD STL generation failed - check OpenSCAD installation")
            
            stl_content = stl_file.read_bytes()
            if len(stl_content) < 84:
                raise RuntimeError("Generated STL file is too small")
                
            return stl_content

def openscad_viewer(model):
    """
    Erstelle 3D-Viewer für SolidPython2-Objekte
    
    Args:
        model: SolidPython2-Objekt mit .as_scad() Methode
        
    Returns:
        OpenSCADViewer Widget für Marimo
        
    Example:
        from solid2 import cube, sphere
        model = cube([10, 10, 10]) + sphere(5).up(15)
        viewer = openscad_viewer(model)
    """
    return OpenSCADViewer(model=model)