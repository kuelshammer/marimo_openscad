"""
JupyterSCAD-Style 3D Viewer für Marimo
Echte STL-Pipeline: SolidPython2 → OpenSCAD → STL → Three.js

Supports both local OpenSCAD and WebAssembly rendering.
Inspired by JupyterSCAD's architecture with modern anywidget integration.
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

class OpenSCADViewer(anywidget.AnyWidget):
    """
    3D-Viewer für SolidPython2-Objekte mit WASM/Local OpenSCAD support
    
    Pipeline Options:
    - Local: SolidPython2 → OpenSCAD CLI → STL → Three.js BufferGeometry  
    - WASM:  SolidPython2 → OpenSCAD WASM → STL → Three.js BufferGeometry
    - Auto:  Hybrid renderer with intelligent fallback
    """
    
    # Viewer state traits
    stl_data = traitlets.Unicode("").tag(sync=True)
    scad_code = traitlets.Unicode("").tag(sync=True)  # Raw SCAD code for WASM rendering
    error_message = traitlets.Unicode("").tag(sync=True)
    is_loading = traitlets.Bool(False).tag(sync=True)
    
    # Renderer configuration traits
    renderer_type = traitlets.Unicode("auto").tag(sync=True)  # "local", "wasm", "auto"
    renderer_status = traitlets.Unicode("initializing").tag(sync=True)  # "ready", "error", "loading"
    wasm_supported = traitlets.Bool(True).tag(sync=True)  # Whether WASM is supported
    wasm_enabled = traitlets.Bool(False).tag(sync=True)  # Whether WASM is actively enabled
    
    _esm = """
    async function render({ model, el }) {
        // Check renderer type from model
        const rendererType = model.get('renderer_type') || 'auto';
        const wasmSupported = model.get('wasm_supported') || false;
        const rendererStatus = model.get('renderer_status') || 'initializing';
        
        // Container Setup with renderer info
        el.innerHTML = `
            <div style="width: 100%; height: 450px; border: 1px solid #ddd; position: relative; background: #fafafa;">
                <div id="container" style="width: 100%; height: 100%;"></div>
                <div id="status" style="position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.8); color: white; padding: 8px 12px; border-radius: 4px; font-family: monospace; font-size: 12px;">
                    Initializing 3D viewer (${rendererType})...
                </div>
                <div id="renderer-info" style="position: absolute; bottom: 10px; left: 10px; background: rgba(0,0,0,0.7); color: white; padding: 4px 8px; border-radius: 3px; font-family: monospace; font-size: 10px;">
                    ${wasmSupported ? '🚀 WASM' : '🔧 Local'} | ${rendererStatus}
                </div>
                <div id="controls" style="position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.9); padding: 8px; border-radius: 4px; font-size: 11px;">
                    🖱️ Drag: Rotate | 🔍 Wheel: Zoom
                </div>
            </div>
        `;
        
        const container = el.querySelector('#container');
        const status = el.querySelector('#status');
        const rendererInfo = el.querySelector('#renderer-info');
        
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
            
            // WASM Renderer Integration
            let wasmRenderer = null;
            
            async function initializeWASMRenderer() {
                if (wasmSupported && rendererType !== 'local') {
                    try {
                        status.textContent = "🚀 Initializing WASM renderer...";
                        
                        // Try to load WASM renderer from our modules
                        const wasmModule = await import('/wasm/openscad.js').catch(() => null);
                        if (wasmModule) {
                            wasmRenderer = wasmModule.default || wasmModule;
                            status.textContent = "✅ WASM renderer ready";
                            rendererInfo.textContent = "🚀 WASM | ready";
                            return true;
                        }
                    } catch (error) {
                        console.warn('WASM renderer initialization failed:', error);
                        status.textContent = "⚠️ WASM unavailable, using fallback";
                        rendererInfo.textContent = "🔧 Local | fallback";
                    }
                }
                return false;
            }
            
            // Enhanced Model Update Handler with WASM support
            async function updateModel() {
                const stlData = model.get("stl_data") || "";
                const errorMsg = model.get("error_message") || "";
                const isLoading = model.get("is_loading");
                const currentRendererType = model.get("renderer_type") || 'auto';
                const currentRendererStatus = model.get("renderer_status") || 'initializing';
                
                // Update renderer info display
                rendererInfo.textContent = `${wasmSupported ? '🚀 WASM' : '🔧 Local'} | ${currentRendererStatus}`;
                
                if (errorMsg) {
                    status.textContent = `❌ ${errorMsg}`;
                    status.style.background = "rgba(220,20,60,0.9)";
                    return;
                }
                
                if (isLoading) {
                    status.textContent = `🔄 Generating STL (${currentRendererType})...`;
                    status.style.background = "rgba(59,130,246,0.9)";
                    return;
                }
                
                if (stlData.trim()) {
                    // Check if this is a WASM render request placeholder
                    if (stlData.includes('WASM_RENDER_REQUEST') && wasmRenderer) {
                        await handleWASMRenderRequest(stlData);
                    } else {
                        processSTLData(stlData);
                    }
                } else {
                    status.textContent = "⏳ Waiting for STL data...";
                    status.style.background = "rgba(107,114,128,0.9)";
                }
            }
            
            // Handle WASM render requests
            async function handleWASMRenderRequest(placeholder) {
                try {
                    status.textContent = "🚀 Rendering with WASM...";
                    status.style.background = "rgba(59,130,246,0.9)";
                    
                    // Extract SCAD code from placeholder or get it from model
                    // For now, we'll need to trigger this from Python side
                    // The actual WASM rendering logic will be implemented here
                    
                    console.log('WASM render request received:', placeholder);
                    
                    // Placeholder for actual WASM rendering
                    // This will be implemented when we integrate the WASM renderer
                    setTimeout(() => {
                        status.textContent = "🚀 WASM rendering (simulated)";
                        status.style.background = "rgba(34,197,94,0.9)";
                    }, 1000);
                    
                } catch (error) {
                    console.error('WASM rendering failed:', error);
                    status.textContent = `❌ WASM error: ${error.message}`;
                    status.style.background = "rgba(220,20,60,0.9)";
                }
            }
            
            // Event Listeners
            model.on("change:stl_data", updateModel);
            model.on("change:error_message", updateModel);
            model.on("change:is_loading", updateModel);
            model.on("change:renderer_type", updateModel);
            model.on("change:renderer_status", updateModel);
            model.on("change:wasm_supported", updateModel);
            
            // Initialize WASM renderer if needed
            if (wasmSupported && rendererType !== 'local') {
                initializeWASMRenderer();
            }
            
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
    
    def __init__(self, 
                 model=None, 
                 renderer_type: Literal["local", "wasm", "auto"] = "auto",
                 openscad_path: Optional[str] = None,
                 wasm_options: Optional[dict] = None,
                 enable_real_time_wasm: bool = True,
                 **kwargs):
        """
        Initialize OpenSCAD Viewer with renderer selection
        
        Args:
            model: SolidPython2 model or SCAD code string
            renderer_type: "local", "wasm", or "auto" (default: "auto")
            openscad_path: Path to local OpenSCAD executable (for local/auto)
            wasm_options: Options for WASM renderer initialization
            enable_real_time_wasm: Whether to enable real-time WASM rendering (default: True)
            **kwargs: Additional anywidget arguments
        """
        # Set renderer type before calling super().__init__
        self.renderer_type = renderer_type
        self.renderer_status = "initializing"
        self.enable_real_time_wasm = enable_real_time_wasm
        
        super().__init__(**kwargs)
        
        # Initialize renderer based on type
        self.renderer = self._create_renderer(renderer_type, openscad_path, wasm_options)
        
        if model is not None:
            self.update_model(model)
    
    def _create_renderer(self, renderer_type: str, openscad_path: Optional[str], wasm_options: Optional[dict]):
        """
        Create appropriate renderer based on type
        """
        try:
            if renderer_type == "wasm":
                logger.info("Initializing WASM renderer")
                renderer = OpenSCADWASMRenderer(wasm_options or {})
                self.renderer_status = "ready"
                self.wasm_supported = True
                return renderer
            
            elif renderer_type == "local":
                logger.info("Initializing local renderer")
                renderer = OpenSCADRenderer(openscad_path)
                self.renderer_status = "ready"
                return renderer
            
            elif renderer_type == "auto":
                logger.info("Initializing hybrid renderer with configuration")
                config = get_config()
                hybrid_config = config.get_hybrid_renderer_config()
                
                # Override with any provided path
                if openscad_path:
                    hybrid_config['openscad_path'] = openscad_path
                
                renderer = HybridOpenSCADRenderer(**hybrid_config)
                self.renderer_status = "ready"
                
                # Check if WASM is actually being used
                active_type = renderer.get_active_renderer_type()
                self.wasm_supported = (active_type == "wasm")
                
                logger.info(f"Hybrid renderer initialized: active={active_type}, config={config.get_summary()}")
                return renderer
            
            else:
                raise ValueError(f"Unknown renderer_type: {renderer_type}")
                
        except Exception as e:
            logger.error(f"Failed to initialize renderer: {e}")
            self.renderer_status = "error"
            self.error_message = f"Renderer initialization failed: {e}"
            
            # Fallback to local renderer as last resort
            try:
                logger.warning("Falling back to local renderer")
                return OpenSCADRenderer(openscad_path)
            except Exception as fallback_error:
                logger.error(f"Fallback renderer also failed: {fallback_error}")
                raise RuntimeError(f"All renderers failed. Primary: {e}, Fallback: {fallback_error}")
    
    def update_model(self, model, force_render: bool = False):
        """Update with SolidPython2 object - enhanced STL/WASM pipeline"""
        try:
            self.is_loading = True
            self.error_message = ""
            
            # Store previous data for comparison
            previous_stl = self.stl_data
            previous_scad = self.scad_code
            
            # SolidPython2 → SCAD Code
            if hasattr(model, 'as_scad'):
                scad_code = model.as_scad()
            elif hasattr(model, '__scad__'):
                scad_code = model.__scad__()
            elif isinstance(model, str):
                scad_code = model
            else:
                raise ValueError("Model muss SolidPython2-Objekt mit .as_scad() Methode oder SCAD-String sein")
            
            # For WASM-enabled viewers, send SCAD code directly to frontend
            if self.wasm_enabled and self.enable_real_time_wasm:
                # Check if SCAD code actually changed
                if scad_code == previous_scad and not force_render:
                    logger.info("SCAD code unchanged, skipping WASM update")
                    return
                
                self.scad_code = scad_code
                logger.info(f"✅ SCAD code sent to WASM renderer: {len(scad_code)} chars")
                logger.info(f"SCAD code changed: {scad_code != previous_scad}")
                
                # Clear STL data to prioritize WASM rendering
                if self.stl_data:
                    self.stl_data = ""
                
                return
            
            # Fallback: SCAD → STL (traditional pipeline)
            stl_data = self._render_stl(scad_code, force_render)
            
            # STL → Base64 for browser
            new_stl_base64 = base64.b64encode(stl_data).decode('utf-8')
            
            # Check if STL actually changed
            if new_stl_base64 == previous_stl and not force_render:
                logger.info("STL unchanged, skipping update")
                return
            
            self.stl_data = new_stl_base64
            
            # Clear SCAD code when using STL mode
            if self.scad_code:
                self.scad_code = ""
            
            logger.info(f"✅ STL rendered: {len(stl_data)} bytes")
            logger.info(f"STL data changed: {new_stl_base64 != previous_stl}")
            
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"❌ Model update error: {e}")
        finally:
            self.is_loading = False
    
    def update_scad_code(self, scad_code: str, use_wasm: bool = None) -> None:
        """
        Update viewer with new SCAD code directly
        
        Args:
            scad_code: Raw OpenSCAD code as string
            use_wasm: Whether to use WASM rendering (None = auto-detect)
        """
        try:
            self.is_loading = True
            self.error_message = ""
            
            # Auto-detect WASM usage if not specified
            if use_wasm is None:
                use_wasm = self.wasm_enabled and self.enable_real_time_wasm
            
            if use_wasm:
                # For WASM: send SCAD code directly to frontend
                previous_scad = self.scad_code
                self.scad_code = scad_code
                
                # Clear STL data to prioritize WASM rendering
                if self.stl_data:
                    self.stl_data = ""
                
                logger.info(f"✅ SCAD code sent to WASM: {len(scad_code)} chars")
                logger.info(f"SCAD code changed: {scad_code != previous_scad}")
            else:
                # For local: render to STL
                previous_stl = self.stl_data
                
                # SCAD → STL (no caching for direct code updates)
                stl_data = self._render_stl(scad_code, force_render=True)
                
                # STL → Base64 for browser
                new_stl_base64 = base64.b64encode(stl_data).decode('utf-8')
                self.stl_data = new_stl_base64
                
                # Clear SCAD code when using STL mode
                if self.scad_code:
                    self.scad_code = ""
                
                logger.info(f"✅ SCAD code rendered to STL: {len(stl_data)} bytes from {len(scad_code)} chars")
                logger.info(f"STL data changed: {new_stl_base64 != previous_stl}")
            
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"❌ SCAD code update error: {e}")
        finally:
            self.is_loading = False
    
    def _render_stl(self, scad_code, force_render: bool = False):
        """
        Render OpenSCAD code to STL using configured renderer
        
        Args:
            scad_code: OpenSCAD code string
            force_render: Whether to bypass caching (for WASM always bypassed)
            
        Returns:
            bytes: STL binary data
        """
        # Log for debugging cache behavior
        if force_render:
            logger.info("Force rendering STL (cache bypassed)")
        else:
            logger.info("Normal STL rendering")
        
        try:
            # Use the configured renderer
            stl_data = self.renderer.render_scad_to_stl(scad_code)
            
            # For WASM renderer, we need to handle placeholder responses
            if isinstance(self.renderer, OpenSCADWASMRenderer):
                # WASM rendering happens asynchronously in JavaScript
                # The Python side gets a placeholder for API compatibility
                if isinstance(stl_data, bytes) and b"WASM_RENDER_REQUEST" in stl_data:
                    logger.info("WASM render request initiated")
                    # Return placeholder for now - actual rendering happens in frontend
                    return stl_data
            
            # Validate STL data
            if not stl_data or len(stl_data) == 0:
                raise RuntimeError("Renderer produced empty STL data")
            
            logger.info(f"✅ STL rendered successfully: {len(stl_data)} bytes")
            return stl_data
            
        except Exception as e:
            logger.error(f"❌ STL rendering failed: {e}")
            self.error_message = f"Rendering error: {e}"
            raise
    
    def get_renderer_info(self) -> dict:
        """Get information about the current renderer"""
        return {
            'type': self.renderer_type,
            'status': self.renderer_status,
            'wasm_supported': self.wasm_supported,
            'wasm_enabled': self.wasm_enabled,
            'real_time_wasm': self.enable_real_time_wasm,
            'active_renderer': getattr(self.renderer, 'get_active_renderer_type', lambda: self.renderer_type)(),
            'stats': getattr(self.renderer, 'get_stats', lambda: {})(),
            'current_mode': 'wasm' if (self.scad_code and self.wasm_enabled) else 'stl'
        }

def openscad_viewer(model, renderer_type: Optional[Literal["local", "wasm", "auto"]] = None, **kwargs):
    """
    Erstelle 3D-Viewer für SolidPython2-Objekte mit WASM/Local OpenSCAD support
    
    Args:
        model: SolidPython2-Objekt mit .as_scad() Methode
        renderer_type: "local", "wasm", or "auto" (default: from config)
        **kwargs: Additional arguments passed to OpenSCADViewer
        
    Returns:
        OpenSCADViewer Widget für Marimo
        
    Example:
        import marimo_openscad as mo
        from solid2 import cube, sphere
        
        # Use global configuration preference
        model = cube([10, 10, 10]) + sphere(5).up(15)
        viewer = mo.openscad_viewer(model)
        
        # Override configuration for this viewer
        viewer_wasm = mo.openscad_viewer(model, renderer_type="wasm")
        
        # Configure globally
        mo.set_renderer_preference("wasm")
        viewer_global = mo.openscad_viewer(model)  # Will use WASM
    """
    # Use global config if not specified
    if renderer_type is None:
        config = get_config()
        renderer_type = config.get_renderer_preference()
    
    return OpenSCADViewer(model=model, renderer_type=renderer_type, **kwargs)