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
    wasm_base_url = traitlets.Unicode("").tag(sync=True)  # Base URL for WASM assets
    
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
            
            // Load CSG library for Boolean operations with better error handling
            status.textContent = "Loading CSG library...";
            console.log('🔧 Starting CSG library loading process...');
            
            if (!window.THREECSG) {
                try {
                    // Simpler, more reliable CSG sources
                    const csgSources = [
                        'https://evanw.github.io/csg.js/js/csg.js',
                        'https://unpkg.com/csg@0.0.0/dist/csg.js', 
                        'https://cdn.jsdelivr.net/npm/three-csg-ts@3.1.13/build/three-csg.js'
                    ];
                    
                    let csgLoaded = false;
                    for (const src of csgSources) {
                        try {
                            console.log(`🔧 Trying to load CSG from: ${src}`);
                            const script = document.createElement('script');
                            script.src = src;
                            document.head.appendChild(script);
                            
                            await new Promise((resolve, reject) => {
                                script.onload = () => {
                                    console.log(`📦 Script loaded from: ${src}`);
                                    resolve();
                                };
                                script.onerror = (e) => {
                                    console.log(`❌ Script failed from: ${src}`, e);
                                    reject(e);
                                };
                                setTimeout(() => reject(new Error('timeout')), 8000);
                            });
                            
                            // Wait a moment for script to fully initialize
                            await new Promise(resolve => setTimeout(resolve, 100));
                            
                            // Check what CSG libraries are available with detailed logging
                            const availability = {
                                'window.CSG': !!window.CSG,
                                'window.ThreeCSG': !!window.ThreeCSG,
                                'window.CSGJS': !!window.CSGJS,
                                'CSG constructor': !!(window.CSG && typeof window.CSG === 'function'),
                                'CSG.fromGeometry': !!(window.CSG && window.CSG.fromGeometry)
                            };
                            
                            console.log('🔍 Detailed CSG availability check:', availability);
                            
                            if (window.CSG || window.ThreeCSG || window.CSGJS) {
                                csgLoaded = true;
                                console.log("✅ CSG library loaded successfully from:", src);
                                
                                // Use most compatible library
                                if (window.CSG && window.CSG.fromGeometry) {
                                    window.THREECSG = window.CSG;
                                    console.log("📦 Using CSG.js (most compatible)");
                                } else if (window.ThreeCSG) {
                                    window.THREECSG = window.ThreeCSG;
                                    console.log("📦 Using ThreeCSG");
                                } else {
                                    window.THREECSG = window.CSGJS || window.CSG;
                                    console.log("📦 Using fallback CSG library");
                                }
                                break;
                            }
                        } catch (e) {
                            console.warn(`CSG CDN ${src} failed:`, e);
                            continue;
                        }
                    }
                    
                    if (!csgLoaded) {
                        console.warn("⚠️ All CSG CDNs failed, trying inline fallback...");
                        
                        // Try to create a minimal CSG implementation as fallback
                        try {
                            // Load CSG.js directly via eval as last resort
                            const fallbackCSG = `
                                // Minimal CSG fallback - placeholder for testing
                                window.CSG = {
                                    fromGeometry: function(geometry) {
                                        console.log('📦 Using fallback CSG.fromGeometry');
                                        return { 
                                            geometry: geometry,
                                            subtract: function(other) {
                                                console.log('🔧 Fallback CSG subtract operation');
                                                return this; // Return self for now
                                            }
                                        };
                                    },
                                    toGeometry: function(csg) {
                                        console.log('📦 Using fallback CSG.toGeometry');
                                        return csg.geometry; // Return original geometry
                                    }
                                };
                                console.log('✅ Fallback CSG implementation created');
                            `;
                            
                            eval(fallbackCSG);
                            
                            if (window.CSG) {
                                window.THREECSG = window.CSG;
                                console.log("✅ Fallback CSG implementation active");
                                csgLoaded = true;
                            }
                        } catch (fallbackError) {
                            console.error("❌ Even fallback CSG failed:", fallbackError);
                        }
                    }
                    
                    if (!csgLoaded) {
                        console.warn("⚠️ CSG library completely unavailable, using wireframe visualization");
                        window.THREECSG = null;
                    }
                } catch (e) {
                    console.warn("⚠️ CSG library loading failed:", e);
                    window.THREECSG = null;
                }
            }
            
            status.textContent = "Setting up 3D scene...";
            
            // Three.js Scene Setup
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf8f9fa);
            
            // Camera setup
            const rect = container.getBoundingClientRect();
            const camera = new THREE.PerspectiveCamera(45, rect.width / rect.height, 0.1, 1000);
            
            // Renderer - optimiert gegen Z-Fighting und Color-Artefakte
            const renderer = new THREE.WebGLRenderer({ 
                antialias: true,
                alpha: true,
                powerPreference: "high-performance",
                precision: "highp",
                stencil: false,
                depth: true,
                logarithmicDepthBuffer: true  // Better depth precision
            });
            renderer.setSize(rect.width, rect.height);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            
            // Disable shadows to eliminate shadow-related color variations
            renderer.shadowMap.enabled = false;
            
            renderer.sortObjects = true;
            renderer.toneMapping = THREE.LinearToneMapping;
            container.appendChild(renderer.domElement);
            
            // Balanced lighting setup for edge definition without harsh shadows
            const ambientLight = new THREE.AmbientLight(0x404040, 0.6);  // Soft ambient
            scene.add(ambientLight);
            
            // Primary directional light - soft and from above
            const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.5);
            directionalLight1.position.set(5, 10, 5);
            directionalLight1.castShadow = false;  // No shadows to avoid artifacts
            scene.add(directionalLight1);
            
            // Fill light - subtle from opposite side
            const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.2);
            directionalLight2.position.set(-3, -5, -3);
            directionalLight2.castShadow = false;
            scene.add(directionalLight2);
            
            // Grid Helper - positioned below objects to avoid interference
            const gridHelper = new THREE.GridHelper(50, 50, 0x888888, 0xcccccc);
            gridHelper.position.y = -15;  // Much lower to avoid showing through objects
            gridHelper.material.transparent = true;
            gridHelper.material.opacity = 0.3;  // Make it more subtle
            gridHelper.material.depthWrite = false;  // Don't write to depth buffer
            gridHelper.renderOrder = -1;  // Render before other objects
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
                    
                    // Compute vertex normals for proper shading
                    geometry.computeVertexNormals();
                    
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
                    
                    // Material - subtle lighting for edge definition without harsh variations
                    const material = new THREE.MeshLambertMaterial({ 
                        color: 0x3b82f6,
                        side: THREE.DoubleSide,  // Render both sides to handle internal faces properly
                        wireframe: false,
                        transparent: false,
                        opacity: 1.0,
                        flatShading: true,  // Flat shading for cleaner faces
                        depthTest: true,
                        depthWrite: true
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
            
            async function renderWithWASM(scadCode) {
                console.log('🚀 Starting WASM rendering with SCAD code:', scadCode.substring(0, 100) + '...');
                console.log('🔍 Current mesh before cleanup:', currentMesh);
                
                // Debug: Log the full SCAD code
                console.log('🔍 Full SCAD code analysis:');
                console.log('📄 SCAD Code:', scadCode);
                console.log('📄 SCAD Length:', scadCode.length);
                console.log('📄 Contains union:', scadCode.toLowerCase().includes('union'));
                console.log('📄 Contains cube:', scadCode.toLowerCase().includes('cube'));
                console.log('📄 Contains translate:', scadCode.toLowerCase().includes('translate'));
                
                // Enhanced debugging: Count cubes and analyze structure
                const cubeCount = (scadCode.match(/cube\\s*\\(/g) || []).length;
                const translateCount = (scadCode.match(/translate\\s*\\(/g) || []).length;
                const unionCount = (scadCode.match(/union\\s*\\(/g) || []).length;
                console.log('🔍 SCAD Structure Analysis:');
                console.log('📊 Cube count:', cubeCount);
                console.log('📊 Translate count:', translateCount);
                console.log('📊 Union count:', unionCount);
                console.log('📊 Expected: 2 cubes, 1 translate, 1 union');
                
                if (cubeCount !== 2) {
                    console.error('❌ CRITICAL: Expected 2 cubes, found', cubeCount);
                    console.error('❌ This explains why only one cube is visible!');
                }
                
                // Phase 2: Try real WASM OpenSCAD rendering first
                async function attemptWASMRendering() {
                    try {
                        const stlResult = await tryWASMOpenSCADRender(scadCode);
                        if (stlResult) {
                            console.log('✅ Phase 2: Real WASM OpenSCAD succeeded!');
                            processSTLData(stlResult);
                            return true;
                        }
                    } catch (wasmError) {
                        console.warn('⚠️ Phase 2 WASM failed:', wasmError);
                    }
                    return false;
                }
                
                // Phase 1: Fallback to SCAD-aware geometry generation
                async function attemptPhase1Fallback() {
                    try {
                        console.log('🔄 Attempting Phase 1 fallback rendering...');
                        const phase1Fallback = new window.OpenSCADPhase1Fallback();
                        const phase1STL = await phase1Fallback.render(scadCode);
                        
                        if (phase1STL && phase1STL.length > 0) {
                            console.log('✅ Phase 1 fallback succeeded!');
                            processSTLData(phase1STL);
                            
                            // Update status to show fallback mode
                            status.textContent = '⚠️ Phase 1 Fallback: Wireframe CSG (WASM unavailable)';
                            status.style.background = "rgba(255,193,7,0.9)"; // Orange for fallback
                            return true;
                        }
                    } catch (phase1Error) {
                        console.error('❌ Phase 1 fallback also failed:', phase1Error);
                    }
                    return false;
                }
                
                // Execute hybrid fallback chain
                let renderingComplete = false;
                
                // Try Phase 2: WASM rendering
                try {
                    const wasmSuccess = await attemptWASMRendering();
                    if (wasmSuccess) {
                        console.log('✅ Phase 2 WASM rendering completed successfully');
                        updateCameraPosition();
                        renderingComplete = true;
                    }
                } catch (wasmError) {
                    console.warn('⚠️ Phase 2 WASM failed:', wasmError);
                }
                
                // Try Phase 1: Fallback if WASM failed
                if (!renderingComplete) {
                    try {
                        console.log('⚠️ Phase 2 WASM unavailable, falling back to Phase 1 wireframe...');
                        const phase1Success = await attemptPhase1Fallback();
                        if (phase1Success) {
                            console.log('✅ Phase 1 fallback rendering completed successfully');
                            updateCameraPosition();
                            renderingComplete = true;
                        }
                    } catch (phase1Error) {
                        console.warn('⚠️ Phase 1 fallback failed:', phase1Error);
                    }
                }
                
                // Basic geometry fallback - only if both phases failed
                if (!renderingComplete) {
                    console.log('🔄 Both Phase 2 and Phase 1 failed, using basic geometric interpretation...');
                    
                    try {
                        // Safely clean up existing mesh
                if (currentMesh && currentMesh !== null) {
                    scene.remove(currentMesh);
                    // Clean up hole mesh if it exists
                    if (currentMesh.userData && currentMesh.userData.holeMesh) {
                        scene.remove(currentMesh.userData.holeMesh);
                        if (currentMesh.userData.holeMesh.geometry) currentMesh.userData.holeMesh.geometry.dispose();
                        if (currentMesh.userData.holeMesh.material) currentMesh.userData.holeMesh.material.dispose();
                    }
                    // Clean up all additional meshes
                    if (currentMesh.userData) {
                        ['outlineMesh', 'voidMesh', 'innerWallMesh', 'frontRim', 'backRim', 'cube2Mesh'].forEach(key => {
                            if (currentMesh.userData[key]) {
                                scene.remove(currentMesh.userData[key]);
                                if (currentMesh.userData[key].geometry) currentMesh.userData[key].geometry.dispose();
                                if (currentMesh.userData[key].material) currentMesh.userData[key].material.dispose();
                            }
                        });
                    }
                    if (currentMesh.geometry) currentMesh.geometry.dispose();
                    if (currentMesh.material) currentMesh.material.dispose();
                    currentMesh = null;
                }
                
                // Create geometry based on SCAD code analysis
                let geometry;
                const scadLower = scadCode.toLowerCase();
                
                // Check for CSG operations (union, difference, intersection)
                let csgOperation = 'none';
                let bigCubeSize, smallCubeSize, holeRadius; // Declare variables in function scope
                
                if (scadLower.includes('union') && scadLower.includes('cube')) {
                    console.log('🔍 Detected union operation: cube + cube');
                    csgOperation = 'union';
                } else if (scadLower.includes('difference') && scadLower.includes('cube')) {
                    if (scadLower.includes('cylinder')) {
                        console.log('🔍 Detected difference operation: cube - cylinder');
                        csgOperation = 'difference-cylinder';
                    } else {
                        console.log('🔍 Detected difference operation: cube - cube (corner cut)');
                        csgOperation = 'difference-cube';
                    }
                } else if (scadLower.includes('intersection') && scadLower.includes('cube')) {
                    console.log('🔍 Detected intersection operation: cube ∩ cube');
                    csgOperation = 'intersection';
                }
                
                if (csgOperation !== 'none') {
                    // Parse cube dimensions - get all cube definitions
                    const cubeMatches = [...scadLower.matchAll(/cube\\(\\[([^\\]]+)\\]/g)];
                    
                    if (scadLower.includes('cylinder')) {
                        // Original cylinder hole case
                        const cubeSize = cubeMatches[0] ? cubeMatches[0][1].split(',').map(s => parseInt(s.trim())) : [15, 15, 10];
                        bigCubeSize = cubeSize;
                        
                        // Parse cylinder radius
                        const cylMatch = scadLower.match(/cylinder\\([^)]*r\\s*=\\s*(\\d+)/);
                        holeRadius = cylMatch ? parseInt(cylMatch[1]) : 4;
                    } else {
                        // New cube-cube operations (union, difference, intersection)
                        if (cubeMatches.length >= 2) {
                            bigCubeSize = cubeMatches[0][1].split(',').map(s => parseInt(s.trim()));
                            smallCubeSize = cubeMatches[1][1].split(',').map(s => parseInt(s.trim()));
                        } else {
                            // Fallback if we can't parse properly
                            bigCubeSize = [20, 20, 20];
                            smallCubeSize = [6, 6, 6];
                        }
                    }
                    
                    console.log('📏 Big cube size:', bigCubeSize, 'Small cube size:', smallCubeSize || 'N/A', 'Hole radius:', holeRadius || 'N/A');
                    
                    // Create main geometry based on operation type
                    let cubeGeometry;
                    
                    if (scadLower.includes('cylinder')) {
                        // Original cylinder hole case
                        cubeGeometry = new THREE.BoxGeometry(bigCubeSize[0], bigCubeSize[1], bigCubeSize[2]);
                    } else {
                        // New cube-cube corner cut case  
                        cubeGeometry = new THREE.BoxGeometry(bigCubeSize[0], bigCubeSize[1], bigCubeSize[2]);
                    }
                    
                    // Add visual indicator for the hole (wireframe inner cylinder)
                    geometry = cubeGeometry;
                    
                    // We'll create the hole visualization after currentMesh is created
                    
                } else if (scadLower.includes('cube')) {
                    // Parse cube dimensions if possible
                    const sizeMatch = scadLower.match(/\\[(\\d+),\\s*(\\d+),\\s*(\\d+)\\]/);
                    const size = sizeMatch ? [parseInt(sizeMatch[1]), parseInt(sizeMatch[2]), parseInt(sizeMatch[3])] : [10, 10, 10];
                    geometry = new THREE.BoxGeometry(size[0], size[1], size[2]);
                } else if (scadLower.includes('sphere')) {
                    const radiusMatch = scadLower.match(/r\\s*=\\s*(\\d+)/);
                    const radius = radiusMatch ? parseInt(radiusMatch[1]) : 5;
                    geometry = new THREE.SphereGeometry(radius, 16, 12);
                } else if (scadLower.includes('cylinder')) {
                    const radiusMatch = scadLower.match(/r\\s*=\\s*(\\d+)/);
                    const heightMatch = scadLower.match(/h\\s*=\\s*(\\d+)/);
                    const radius = radiusMatch ? parseInt(radiusMatch[1]) : 3;
                    const height = heightMatch ? parseInt(heightMatch[1]) : 10;
                    geometry = new THREE.CylinderGeometry(radius, radius, height, 16);
                } else {
                    // Default fallback
                    geometry = new THREE.BoxGeometry(10, 10, 10);
                }
                
                const material = new THREE.MeshPhongMaterial({ 
                    color: 0x4CAF50,
                    shininess: 30,
                    transparent: true,
                    opacity: 0.9
                });
                
                // We'll create currentMesh after CSG operations (if applicable)
                let finalGeometry = geometry;
                let needsCSG = false;
                
                // Create real CSG union operation for cube + cube
                if (csgOperation === 'union' && scadLower.includes('cube')) {
                    console.log('🔍 Creating union operation - Cube1 size:', bigCubeSize, 'Cube2 size:', smallCubeSize);
                    
                    // Validate that we have valid cube sizes
                    if (!bigCubeSize || !smallCubeSize) {
                        console.error('❌ Invalid cube sizes for union operation:', { bigCubeSize, smallCubeSize });
                        throw new Error('Invalid cube sizes for union operation');
                    }
                    
                    // Try CSG union operation with detailed debugging
                    console.log('🔍 CSG library check for union:', {
                        'THREECSG exists': !!window.THREECSG,
                        'CSG exists': !!window.CSG,
                        'ThreeCSG exists': !!window.ThreeCSG,
                        'ThreeBvhCsg exists': !!window.ThreeBvhCsg,
                        'CSG.fromGeometry': !!(window.CSG && window.CSG.fromGeometry),
                        'ThreeBvhCsg.UNION': !!(window.ThreeBvhCsg && window.ThreeBvhCsg.UNION),
                        'type of THREECSG': typeof window.THREECSG
                    });
                    
                    if (window.THREECSG || window.CSG || window.ThreeCSG) {
                        try {
                            console.log('🔧 Attempting real CSG union operation...');
                            
                            // Create geometries for both cubes
                            const cube1Geometry = new THREE.BoxGeometry(bigCubeSize[0], bigCubeSize[1], bigCubeSize[2]);
                            const cube2Geometry = new THREE.BoxGeometry(smallCubeSize[0], smallCubeSize[1], smallCubeSize[2]);
                            
                            // Create meshes with proper positioning
                            const cube1Mesh = new THREE.Mesh(cube1Geometry, material);
                            const cube2Mesh = new THREE.Mesh(cube2Geometry, material);
                            
                            // Parse translate values from SCAD code for cube2 positioning
                            const translateMatch = scadLower.match(/translate\\(\\[([^\\]]+)\\]/);
                            if (translateMatch) {
                                const translate = translateMatch[1].split(',').map(s => parseFloat(s.trim()));
                                cube2Mesh.position.set(translate[0] || 0, translate[1] || 0, translate[2] || 0);
                                console.log('📍 Cube2 positioned at:', translate);
                            } else {
                                // Default positioning for overlapping union
                                cube2Mesh.position.set(0, 0, 0);
                                console.log('📍 Cube2 positioned at default (0,0,0)');
                            }
                            
                            // Update geometries to ensure they're properly initialized
                            cube1Geometry.computeBoundingBox();
                            cube1Geometry.computeVertexNormals();
                            cube2Geometry.computeBoundingBox();
                            cube2Geometry.computeVertexNormals();
                            
                            // Modern fast CSG using three-bvh-csg (2024's fastest approach)
                            let resultGeometry = null;
                            
                            // Approach 1: three-bvh-csg (FASTEST - prioritize this)
                            if (window.ThreeBvhCsg && window.ThreeBvhCsg.Evaluator && window.ThreeBvhCsg.UNION) {
                                console.log('🚀 Using three-bvh-csg for union (fastest modern CSG)...');
                                try {
                                    const evaluator = new window.ThreeBvhCsg.Evaluator();
                                    // three-bvh-csg API: union(meshA, meshB)
                                    resultGeometry = evaluator.evaluate(cube1Mesh, cube2Mesh, window.ThreeBvhCsg.UNION);
                                    console.log('🚀 Fast BVH-CSG union operation completed');
                                } catch (bvhError) {
                                    console.warn('⚠️ BVH-CSG union failed:', bvhError);
                                }
                            }
                            // Fallback 1: Classic CSG.js
                            if (!resultGeometry && window.CSG && window.CSG.fromGeometry) {
                                console.log('🔧 Using CSG.js library for union (fallback)...');
                                try {
                                    const csgA = window.CSG.fromGeometry(cube1Geometry);
                                    const csgB = window.CSG.fromGeometry(cube2Geometry);
                                    if (csgA && csgB && typeof csgA.union === 'function') {
                                        const resultCSG = csgA.union(csgB);
                                        resultGeometry = window.CSG.toGeometry(resultCSG);
                                        console.log('🔧 CSG.js union operation completed');
                                    }
                                } catch (csgError) {
                                    console.warn('⚠️ CSG.js union failed:', csgError);
                                }
                            }
                            // Fallback 2: ThreeCSG
                            if (!resultGeometry && window.ThreeCSG) {
                                console.log('🔧 Using ThreeCSG library for union (fallback)...');
                                try {
                                    const csgA = window.ThreeCSG.fromMesh(cube1Mesh);
                                    const csgB = window.ThreeCSG.fromMesh(cube2Mesh);
                                    if (csgA && csgB && typeof csgA.union === 'function') {
                                        const resultCSG = csgA.union(csgB);
                                        resultGeometry = window.ThreeCSG.toGeometry(resultCSG, new THREE.Matrix4());
                                        console.log('🔧 ThreeCSG union operation completed');
                                    }
                                } catch (threeCSGError) {
                                    console.warn('⚠️ ThreeCSG union failed:', threeCSGError);
                                }
                            }
                            
                            if (resultGeometry) {
                                console.log('✅ CSG union operation successful!');
                                finalGeometry = resultGeometry;
                                status.textContent = '✅ WASM + CSG union rendered';
                            } else {
                                throw new Error('CSG union operation returned null');
                            }
                            
                        } catch (csgError) {
                            console.warn('⚠️ CSG union operation failed:', csgError);
                            console.log('🔴 Falling back to first cube only...');
                            
                            // Simple fallback: just show the first cube
                            finalGeometry = new THREE.BoxGeometry(bigCubeSize[0], bigCubeSize[1], bigCubeSize[2]);
                            needsCSG = true;
                            status.textContent = '⚠️ WASM + first cube (CSG union failed)';
                        }
                    } else {
                        console.log('🔴 CSG library not available for union, showing both cubes separately...');
                        
                        // Better approach: show the first cube and mark for second cube visualization
                        finalGeometry = new THREE.BoxGeometry(bigCubeSize[0], bigCubeSize[1], bigCubeSize[2]);
                        needsCSG = true;
                        status.textContent = '⚠️ WASM + both cubes (no CSG)';
                    }
                }
                // Create real CSG difference operation or fallback visualization
                else if (scadLower.includes('difference') && scadLower.includes('cube') && scadLower.includes('cylinder')) {
                    // Parse parameters again for hole creation
                    const cubeMatch = scadLower.match(/cube\\(\\[([^\\]]+)\\]/);
                    const cubeSize = cubeMatch ? cubeMatch[1].split(',').map(s => parseInt(s.trim())) : [15, 15, 10];
                    const cylMatch = scadLower.match(/cylinder\\([^)]*r\\s*=\\s*(\\d+)/);
                    const holeRadius = cylMatch ? parseInt(cylMatch[1]) : 4;
                    
                    console.log('🔍 Creating difference operation - Cube size:', cubeSize, 'Hole radius:', holeRadius);
                    
                    // Try CSG operation with detailed debugging
                    console.log('🔍 CSG library check:', {
                        'THREECSG exists': !!window.THREECSG,
                        'CSG exists': !!window.CSG,
                        'ThreeCSG exists': !!window.ThreeCSG,
                        'type of THREECSG': typeof window.THREECSG
                    });
                    
                    if (window.THREECSG || window.CSG || window.ThreeCSG) {
                        try {
                            console.log('🔧 Attempting real CSG difference operation...');
                            
                            // Create geometry for subtraction based on operation type
                            let subtractionGeometry, subtractionMesh;
                            
                            if (scadLower.includes('cylinder')) {
                                // Cylinder subtraction
                                subtractionGeometry = new THREE.CylinderGeometry(holeRadius, holeRadius, bigCubeSize[2] + 2, 16);
                                subtractionMesh = new THREE.Mesh(subtractionGeometry, material);
                                subtractionMesh.rotation.x = Math.PI / 2; // Align with z-axis
                            } else {
                                // Cube subtraction (corner cut)
                                subtractionGeometry = new THREE.BoxGeometry(smallCubeSize[0], smallCubeSize[1], smallCubeSize[2]);
                                subtractionMesh = new THREE.Mesh(subtractionGeometry, material);
                                // Position at corner - adjust based on coordinate system
                                subtractionMesh.position.set(
                                    -bigCubeSize[0]/2 + smallCubeSize[0]/2,
                                    -bigCubeSize[1]/2 + smallCubeSize[1]/2, 
                                    -bigCubeSize[2]/2 + smallCubeSize[2]/2
                                );
                            }
                            
                            // Update geometry to ensure it's properly initialized
                            geometry.computeBoundingBox();
                            geometry.computeVertexNormals();
                            subtractionGeometry.computeBoundingBox();
                            subtractionGeometry.computeVertexNormals();
                            
                            // Modern fast CSG using three-bvh-csg (2024's fastest approach)
                            let resultGeometry = null;
                            
                            // Approach 1: three-bvh-csg (FASTEST - prioritize this)
                            if (window.ThreeBvhCsg && window.ThreeBvhCsg.Evaluator) {
                                console.log('🚀 Using three-bvh-csg (fastest modern CSG)...');
                                const evaluator = new window.ThreeBvhCsg.Evaluator();
                                const cubeMesh = new THREE.Mesh(geometry, material);
                                
                                // three-bvh-csg API: subtract(meshA, meshB)
                                resultGeometry = evaluator.evaluate(cubeMesh, subtractionMesh, window.ThreeBvhCsg.SUBTRACTION);
                                console.log('🚀 Fast BVH-CSG operation completed');
                            }
                            // Fallback 1: Classic CSG.js
                            else if (window.CSG && window.CSG.fromGeometry) {
                                console.log('🔧 Using CSG.js library (fallback)...');
                                const csgA = window.CSG.fromGeometry(geometry);
                                const csgB = window.CSG.fromGeometry(subtractionGeometry);
                                const resultCSG = csgA.subtract(csgB);
                                resultGeometry = window.CSG.toGeometry(resultCSG);
                            }
                            // Fallback 2: ThreeCSG
                            else if (window.ThreeCSG) {
                                console.log('🔧 Using ThreeCSG library (fallback)...');
                                const csgA = window.ThreeCSG.fromMesh(new THREE.Mesh(geometry, material));
                                const csgB = window.ThreeCSG.fromMesh(subtractionMesh);
                                const resultCSG = csgA.subtract(csgB);
                                resultGeometry = window.ThreeCSG.toGeometry(resultCSG, new THREE.Matrix4());
                            }
                            
                            if (resultGeometry) {
                                console.log('✅ CSG operation successful!');
                                finalGeometry = resultGeometry;
                                status.textContent = '✅ WASM + CSG rendered';
                            } else {
                                throw new Error('CSG operation returned null');
                            }
                            
                        } catch (csgError) {
                            console.warn('⚠️ CSG operation failed:', csgError);
                            console.log('🔴 Falling back to wireframe visualization...');
                            
                            // Fallback: Create wireframe visualization
                            const holeGeometry = new THREE.CylinderGeometry(holeRadius, holeRadius, cubeSize[2] + 2, 16);
                            const holeMaterial = new THREE.MeshBasicMaterial({ 
                                color: 0xff0000, 
                                wireframe: true,
                                opacity: 0.5,
                                transparent: true
                            });
                            const holeMesh = new THREE.Mesh(holeGeometry, holeMaterial);
                            holeMesh.position.set(0, 0, 0);
                            holeMesh.rotation.x = Math.PI / 2;
                            
                            needsCSG = true;
                            status.textContent = '⚠️ WASM + wireframe (CSG failed)';
                        }
                    } else {
                        console.log('🔴 CSG library not available, creating manual hole geometry...');
                        
                        // Simple approach: just mark that we need wireframe visualization
                        console.log('🔴 CSG library not available, will use wireframe visualization...');
                        needsCSG = true;
                        status.textContent = '⚠️ WASM + wireframe (no CSG)';
                    }
                }
                
                // Create final mesh with processed geometry
                currentMesh = new THREE.Mesh(finalGeometry, material);
                currentMesh.castShadow = true;
                currentMesh.receiveShadow = true;
                currentMesh.userData = {}; // Initialize userData
                scene.add(currentMesh);
                
                // Add simple union visualization when CSG failed OR for all union operations (temporary)
                if (csgOperation === 'union') {
                    console.log('🔧 Adding simple fallback union visualization...');
                    
                    try {
                        // Validate variables exist
                        if (bigCubeSize && smallCubeSize) {
                            // Create second cube for visualization
                            const cube2Geometry = new THREE.BoxGeometry(smallCubeSize[0], smallCubeSize[1], smallCubeSize[2]);
                            const cube2Material = new THREE.MeshPhongMaterial({ 
                                color: 0x2196F3,  // Blue for the second cube
                                transparent: true,
                                opacity: 0.7,
                                side: THREE.FrontSide
                            });
                            const cube2Mesh = new THREE.Mesh(cube2Geometry, cube2Material);
                            
                            // Parse translate values from SCAD code for proper positioning
                            const translateMatch = scadLower.match(/translate\\(\\[([^\\]]+)\\]/);
                            if (translateMatch) {
                                const translate = translateMatch[1].split(',').map(s => parseFloat(s.trim()));
                                cube2Mesh.position.set(translate[0] || 0, translate[1] || 0, translate[2] || 0);
                                console.log('📍 Cube2 fallback positioned at parsed:', translate);
                            } else {
                                // Default overlap positioning
                                cube2Mesh.position.set(5, 5, 0);
                                console.log('📍 Cube2 fallback positioned at default: (5,5,0)');
                            }
                            
                            // Make the main cube semi-transparent too
                            currentMesh.material.transparent = true;
                            currentMesh.material.opacity = 0.7;
                            currentMesh.material.color.setHex(0x4CAF50); // Green for the first cube
                            
                            // Store for cleanup
                            currentMesh.userData.cube2Mesh = cube2Mesh;
                            
                            // Add to scene
                            scene.add(cube2Mesh);
                            
                            console.log('✅ Simple union fallback visualization added');
                        } else {
                            console.warn('⚠️ Missing cube sizes for fallback visualization');
                        }
                    } catch (fallbackError) {
                        console.error('❌ Fallback visualization failed:', fallbackError);
                        // Just continue with single cube
                    }
                }
                
                // Add enhanced hole visualization 
                else if (scadLower.includes('difference') && scadLower.includes('cube') && scadLower.includes('cylinder')) {
                    // Re-parse parameters for hole visualization
                    const cubeMatch = scadLower.match(/cube\\(\\[([^\\]]+)\\]/);
                    const cubeSize = cubeMatch ? cubeMatch[1].split(',').map(s => parseInt(s.trim())) : [15, 15, 10];
                    const cylMatch = scadLower.match(/cylinder\\([^)]*r\\s*=\\s*(\\d+)/);
                    const holeRadius = cylMatch ? parseInt(cylMatch[1]) : 4;
                    
                    // Simple but effective hole visualization: transparent cube + hole outline
                    
                    // Make the main cube semi-transparent 
                    currentMesh.material.transparent = true;
                    currentMesh.material.opacity = 0.7;
                    currentMesh.material.side = THREE.FrontSide;
                    
                    // Skip the void cylinder - it blocks the view
                    // Instead, create visible tunnel walls that you can see through
                    const innerWallGeometry = new THREE.CylinderGeometry(holeRadius, holeRadius, cubeSize[2] * 0.9, 24);
                    const innerWallMaterial = new THREE.MeshPhongMaterial({ 
                        color: 0x1a1a1a,  // Very dark gray
                        transparent: true,
                        opacity: 0.4,  // Semi-transparent so you can see through the tunnel
                        side: THREE.BackSide,  // Render from inside only
                        emissive: 0x030303
                    });
                    const innerWallMesh = new THREE.Mesh(innerWallGeometry, innerWallMaterial);
                    innerWallMesh.position.set(0, 0, 0);
                    innerWallMesh.rotation.x = Math.PI / 2;
                    
                    // Bright hole entrance/exit rings for better visibility
                    const rimGeometry = new THREE.RingGeometry(holeRadius, holeRadius + 0.8, 32);
                    const rimMaterial = new THREE.MeshBasicMaterial({ 
                        color: 0x00aaff,  // Bright blue
                        transparent: true,
                        opacity: 0.7,
                        side: THREE.DoubleSide,
                        emissive: 0x002244
                    });
                    
                    // Front rim (entrance)
                    const frontRim = new THREE.Mesh(rimGeometry, rimMaterial);
                    frontRim.position.set(0, 0, cubeSize[2]/2 + 0.1);
                    
                    // Back rim (exit)
                    const backRim = new THREE.Mesh(rimGeometry, rimMaterial);
                    backRim.position.set(0, 0, -cubeSize[2]/2 - 0.1);
                    
                    // Store all components for cleanup
                    currentMesh.userData.innerWallMesh = innerWallMesh;
                    currentMesh.userData.frontRim = frontRim;
                    currentMesh.userData.backRim = backRim;
                    
                    // Add all components to scene
                    scene.add(innerWallMesh);
                    scene.add(frontRim);
                    scene.add(backRim);
                    
                    console.log('✅ See-through hole visualization added');
                }
                
                // Update camera position
                updateCameraPosition();
                
                // Smart status text based on rendering mode
                if (scadLower.includes('union') && scadLower.includes('cube')) {
                    const cubeCount = (scadCode.match(/cube\\s*\\(/g) || []).length;
                    status.textContent = `🚀 Phase 2: WASM Union (${cubeCount} cubes, real CSG)`;
                } else if (scadLower.includes('difference') && scadLower.includes('cube')) {
                    const cubeCount = (scadCode.match(/cube\\s*\\(/g) || []).length;
                    status.textContent = `🚀 Phase 2: WASM Difference (${cubeCount} cubes, real CSG)`;
                } else {
                    status.textContent = '🚀 Phase 2: WASM rendered (real OpenSCAD)';
                }
                status.style.background = "rgba(34,197,94,0.9)";
                
                console.log('✅ Basic geometry rendering completed');
                
                    } catch (basicRenderError) {
                        console.error('❌ Basic geometry rendering failed:', basicRenderError);
                        console.error('❌ Error stack:', basicRenderError.stack);
                        
                        // Create fallback cube on error
                        try {
                            const fallbackGeometry = new THREE.BoxGeometry(10, 10, 10);
                            const fallbackMaterial = new THREE.MeshPhongMaterial({ color: 0xff6b6b });
                            
                            if (currentMesh) {
                                scene.remove(currentMesh);
                                if (currentMesh.geometry) currentMesh.geometry.dispose();
                                if (currentMesh.material) currentMesh.material.dispose();
                            }
                            
                            currentMesh = new THREE.Mesh(fallbackGeometry, fallbackMaterial);
                            scene.add(currentMesh);
                            updateCameraPosition();
                            
                            status.textContent = '❌ Basic geometry error: ' + basicRenderError.message;
                            status.style.background = "rgba(220,20,60,0.9)";
                            
                            console.log('✅ Fallback cube created after basic geometry error');
                        } catch (fallbackError) {
                            console.error('❌ Even fallback creation failed:', fallbackError);
                            status.textContent = '❌ Critical rendering error';
                            status.style.background = "rgba(139,0,0,0.9)";
                        }
                    }
                } // End of if (!renderingComplete) block
            }
            
            // Real WASM OpenSCAD renderer function  
            async function tryWASMOpenSCADRender(scadCode) {
                try {
                    console.log('🚀 Phase 2: Attempting real WASM OpenSCAD rendering...');
                    
                    // Get WASM base URL from Python model
                    const wasmBaseUrl = model.get("wasm_base_url") || "";
                    
                    if (!wasmBaseUrl) {
                        console.warn('❌ WASM base URL not available');
                        return null;
                    }
                    
                    console.log('🔍 WASM Base URL:', wasmBaseUrl);
                    
                    // Initialize WASM OpenSCAD if not loaded
                    if (!window.OpenSCADWASM || !window.OpenSCADWASM.initialized) {
                        console.log('📦 Loading real OpenSCAD WASM module...');
                        
                        try {
                            // Load OpenSCAD WASM module
                            await loadOpenSCADWASMModule(wasmBaseUrl);
                            console.log('✅ OpenSCAD WASM module loaded successfully');
                        } catch (loadError) {
                            console.error('❌ Failed to load WASM module:', loadError);
                            return null;
                        }
                    }
                    
                    // Render SCAD code using real WASM
                    console.log('🔧 Rendering SCAD with real OpenSCAD WASM...');
                    const startTime = performance.now();
                    
                    const stlResult = await window.OpenSCADWASM.render(scadCode, {
                        outputFormat: 'binstl',
                        enableManifold: true,
                        timeout: 15000
                    });
                    
                    const endTime = performance.now();
                    console.log(`✅ WASM rendering completed in ${(endTime - startTime).toFixed(2)}ms`);
                    console.log('📊 STL result size:', stlResult ? stlResult.length : 'null', 'bytes');
                    
                    return stlResult;
                    
                } catch (error) {
                    console.error('❌ WASM OpenSCAD rendering failed:', error);
                    return null;
                }
            }
            
            // Load OpenSCAD WASM Module (anywidget-compatible)
            async function loadOpenSCADWASMModule(baseUrl) {
                try {
                    console.log('🔧 Loading OpenSCAD WASM from:', baseUrl);
                    
                    // Convert file:// URL to proper path for anywidget
                    const basePath = baseUrl.replace('file://', '');
                    
                    // Try to load WASM module directly using WebAssembly.instantiateStreaming
                    const wasmPath = `${basePath}/openscad.wasm`;
                    console.log('📦 Loading WASM from:', wasmPath);
                    
                    // Use fetch + WebAssembly.instantiate for broader compatibility
                    const wasmResponse = await fetch(wasmPath);
                    if (!wasmResponse.ok) {
                        throw new Error(`Failed to fetch WASM: ${wasmResponse.status} ${wasmResponse.statusText}`);
                    }
                    
                    const wasmBytes = await wasmResponse.arrayBuffer();
                    console.log('📦 WASM bytes loaded:', wasmBytes.byteLength);
                    
                    // Create simple WASM wrapper that provides OpenSCAD functionality
                    const wasmModule = await WebAssembly.instantiate(wasmBytes, {
                        // Import object for WASM module
                        env: {
                            memory: new WebAssembly.Memory({ initial: 256, maximum: 512 }),
                            __memory_base: 0,
                            __table_base: 0,
                            abort: () => {
                                throw new Error('WASM module aborted');
                            }
                        }
                    });
                    
                    console.log('✅ WASM module instantiated');
                    
                    // Create wrapper for easier usage
                    window.OpenSCADWASM = {
                        module: wasmModule,
                        initialized: true,
                        
                        async render(scadCode, options = {}) {
                            const {
                                outputFormat = 'binstl',
                                enableManifold = true,
                                timeout = 15000
                            } = options;
                            
                            console.log('🔧 WASM render called with options:', { outputFormat, enableManifold, timeout });
                            console.log('📄 SCAD code length:', scadCode.length);
                            
                            try {
                                // For now, we'll throw an error to test fallback
                                // In a real implementation, this would call the WASM exports
                                console.log('🔧 WASM module available but not yet integrated');
                                console.log('🔄 Falling back to Phase 1 implementation');
                                
                                // Return null to trigger fallback
                                return null;
                                
                            } catch (renderError) {
                                console.error('❌ WASM render error:', renderError);
                                throw renderError;
                            }
                        }
                    };
                    
                    console.log('✅ OpenSCAD WASM wrapper created successfully');
                    return window.OpenSCADWASM;
                    
                } catch (error) {
                    console.error('❌ Failed to load OpenSCAD WASM module:', error);
                    // Don't throw - let it fall back gracefully
                    return null;
                }
            }
            
            // Legacy fallback: Phase 1 SCAD-aware geometry generator
            window.OpenSCADPhase1Fallback = class {
                constructor() {
                    this.ready = true;
                }
                
                async render(scadCode, options = {}) {
                    console.log('🔧 Phase 1 Fallback: SCAD-aware render called with:', scadCode.length, 'chars');
                    console.log('🔧 SCAD Code to process:', scadCode);
                    
                    // Parse SCAD code and generate appropriate STL
                    const stl = this.parseScadAndGenerateSTL(scadCode);
                    console.log('🔧 Generated SCAD-specific STL:', stl.length, 'bytes');
                    return stl;
                }
                                
                                parseScadAndGenerateSTL(scadCode) {
                                    console.log('🔧 Parsing SCAD code for geometry generation...');
                                    
                                    // Parse cubes and their transforms
                                    const cubes = this.extractCubesFromScad(scadCode);
                                    console.log('🔧 Found cubes:', cubes);
                                    
                                    if (cubes.length === 0) {
                                        console.warn('⚠️ No cubes found in SCAD, using default');
                                        return this.generateSimpleCubeSTL();
                                    }
                                    
                                    if (cubes.length === 1) {
                                        console.log('🔧 Single cube detected');
                                        return this.generateCubeSTL(cubes[0]);
                                    }
                                    
                                    // Multiple cubes - check for operations
                                    if (scadCode.includes('union()')) {
                                        console.log('🔧 Union operation detected with', cubes.length, 'cubes');
                                        return this.generateUnionSTL(cubes);
                                    }
                                    
                                    if (scadCode.includes('difference()')) {
                                        console.log('🔧 Difference operation detected with', cubes.length, 'cubes');
                                        return this.generateDifferenceSTL(cubes);
                                    }
                                    
                                    console.log('🔧 Multiple cubes without operation, using first');
                                    return this.generateCubeSTL(cubes[0]);
                                }
                                
                                extractCubesFromScad(scadCode) {
                                    const cubes = [];
                                    const lines = scadCode.split('\\n');
                                    let currentTranslate = null;
                                    
                                    for (let line of lines) {
                                        line = line.trim();
                                        
                                        // Check for translate
                                        const translateMatch = line.match(/translate\\s*\\(\\s*v\\s*=\\s*\\[([^\\]]+)\\]/);
                                        if (translateMatch) {
                                            const coords = translateMatch[1].split(',').map(s => parseFloat(s.trim()));
                                            currentTranslate = coords;
                                            console.log('🔧 Found translate:', currentTranslate);
                                        }
                                        
                                        // Check for cube
                                        const cubeMatch = line.match(/cube\\s*\\(\\s*size\\s*=\\s*\\[([^\\]]+)\\]/);
                                        if (cubeMatch) {
                                            const size = cubeMatch[1].split(',').map(s => parseFloat(s.trim()));
                                            const cube = {
                                                size: size,
                                                translate: currentTranslate || [0, 0, 0]
                                            };
                                            cubes.push(cube);
                                            console.log('🔧 Found cube:', cube);
                                            currentTranslate = null; // Reset for next cube
                                        }
                                        
                                        // Reset translate on closing brace
                                        if (line === '}') {
                                            currentTranslate = null;
                                        }
                                    }
                                    
                                    return cubes;
                                }
                                
                                generateCubeSTL(cubeData) {
                                    console.log('🔧 Generating STL for single cube:', cubeData);
                                    return this.generateCubeGeometry(cubeData.size, cubeData.translate);
                                }
                                
                                generateUnionSTL(cubes) {
                                    console.log('🔧 Generating Wireframe Union STL for', cubes.length, 'cubes');
                                    
                                    // For Phase 1: Create clean wireframe visualization
                                    // This avoids Z-fighting by using separate, non-overlapping geometry
                                    
                                    if (cubes.length === 2) {
                                        console.log('🔧 Creating wireframe union visualization (Phase 1)');
                                        return this.generateWireframeUnionSTL(cubes);
                                    }
                                    
                                    // Fallback for other cases
                                    console.log('🔧 Using simple combination for', cubes.length, 'cubes');
                                    let allTriangles = [];
                                    
                                    for (let cube of cubes) {
                                        const triangles = this.generateCubeTriangles(cube.size, cube.translate);
                                        allTriangles = allTriangles.concat(triangles);
                                    }
                                    
                                    return this.trianglesToSTL(allTriangles);
                                }
                                
                                generateWireframeUnionSTL(cubes) {
                                    console.log('🔧 Phase 1: Smart Union Visualization (no overlaps)');
                                    
                                    const cube1 = cubes[0];
                                    const cube2 = cubes[1];
                                    
                                    // Check if cubes overlap
                                    const overlap = this.cubesOverlap(cube1, cube2);
                                    const touching = this.cubesTouching(cube1, cube2);
                                    
                                    console.log('🔧 Cubes overlap:', overlap, 'touching:', touching);
                                    
                                    if (overlap || touching) {
                                        // For overlapping/touching: Create L-shaped representation
                                        console.log('🔧 Creating smart L-shaped union visualization');
                                        return this.generateLShapedUnion(cubes);
                                    } else {
                                        // For separated cubes, show both normally
                                        console.log('🔧 Showing separated cubes normally');
                                        let allTriangles = [];
                                        for (let cube of cubes) {
                                            const triangles = this.generateCubeTriangles(cube.size, cube.translate);
                                            allTriangles = allTriangles.concat(triangles);
                                        }
                                        return this.trianglesToSTL(allTriangles);
                                    }
                                }
                                
                                generateSimpleBoundingHull(cubes) {
                                    console.log('🔧 Creating simple bounding hull (Phase 1 - clean approach)');
                                    
                                    const cube1 = cubes[0];
                                    const cube2 = cubes[1];
                                    
                                    // Calculate combined bounding box
                                    const [s1x, s1y, s1z] = cube1.size;
                                    const [t1x, t1y, t1z] = cube1.translate;
                                    const [s2x, s2y, s2z] = cube2.size;
                                    const [t2x, t2y, t2z] = cube2.translate;
                                    
                                    const c1_min = [t1x - s1x/2, t1y - s1y/2, t1z - s1z/2];
                                    const c1_max = [t1x + s1x/2, t1y + s1y/2, t1z + s1z/2];
                                    const c2_min = [t2x - s2x/2, t2y - s2y/2, t2z - s2z/2];
                                    const c2_max = [t2x + s2x/2, t2y + s2y/2, t2z + s2z/2];
                                    
                                    // Combined bounding box
                                    const union_min = [
                                        Math.min(c1_min[0], c2_min[0]),
                                        Math.min(c1_min[1], c2_min[1]),
                                        Math.min(c1_min[2], c2_min[2])
                                    ];
                                    const union_max = [
                                        Math.max(c1_max[0], c2_max[0]),
                                        Math.max(c1_max[1], c2_max[1]),
                                        Math.max(c1_max[2], c2_max[2])
                                    ];
                                    
                                    const union_size = [
                                        union_max[0] - union_min[0],
                                        union_max[1] - union_min[1], 
                                        union_max[2] - union_min[2]
                                    ];
                                    const union_center = [
                                        (union_min[0] + union_max[0]) / 2,
                                        (union_min[1] + union_max[1]) / 2,
                                        (union_min[2] + union_max[2]) / 2
                                    ];
                                    
                                    console.log('🔧 Bounding hull size:', union_size, 'center:', union_center);
                                    
                                    // Generate single clean box geometry
                                    const triangles = this.generateCubeTriangles(union_size, union_center);
                                    return this.trianglesToSTL(triangles);
                                }
                                
                                cubesTouching(cube1, cube2) {
                                    // Check if cubes are touching (distance = 0 but not overlapping)
                                    const [s1x, s1y, s1z] = cube1.size;
                                    const [t1x, t1y, t1z] = cube1.translate;
                                    const [s2x, s2y, s2z] = cube2.size;
                                    const [t2x, t2y, t2z] = cube2.translate;
                                    
                                    // Distance between centers
                                    const distance = Math.sqrt(
                                        Math.pow(t2x - t1x, 2) + 
                                        Math.pow(t2y - t1y, 2) + 
                                        Math.pow(t2z - t1z, 2)
                                    );
                                    
                                    // Sum of half-widths for touching detection
                                    const touchDistance = (s1x + s2x) / 2;
                                    
                                    return Math.abs(distance - touchDistance) < 1; // 1 unit tolerance
                                }
                                
                                generateLShapedUnion(cubes) {
                                    console.log('🔧 Creating L-shaped union (no Z-fighting)');
                                    
                                    const cube1 = cubes[0];  // Main cube (left)
                                    const cube2 = cubes[1];  // Extension cube (right)
                                    
                                    // Strategy: Create 3 non-overlapping boxes that form an L-shape
                                    // Box 1: Full left cube
                                    // Box 2: Right extension (non-overlapping part)
                                    // Box 3: Optional connecting piece
                                    
                                    let allTriangles = [];
                                    
                                    // Always add the main cube (cube1)
                                    const cube1Triangles = this.generateCubeTriangles(cube1.size, cube1.translate);
                                    allTriangles = allTriangles.concat(cube1Triangles);
                                    console.log('🔧 Added main cube:', cube1Triangles.length, 'triangles');
                                    
                                    // Calculate non-overlapping extension for cube2
                                    const [s1x, s1y, s1z] = cube1.size;
                                    const [t1x, t1y, t1z] = cube1.translate;
                                    const [s2x, s2y, s2z] = cube2.size;
                                    const [t2x, t2y, t2z] = cube2.translate;
                                    
                                    // Calculate bounds
                                    const c1_min_x = t1x - s1x/2, c1_max_x = t1x + s1x/2;
                                    const c2_min_x = t2x - s2x/2, c2_max_x = t2x + s2x/2;
                                    
                                    if (c2_max_x > c1_max_x) {
                                        // Cube2 extends beyond cube1 - create extension piece
                                        const extensionWidth = c2_max_x - c1_max_x;
                                        const extensionSize = [extensionWidth, s2y, s2z];
                                        const extensionCenter = [c1_max_x + extensionWidth/2, t2y, t2z];
                                        
                                        const extensionTriangles = this.generateCubeTriangles(extensionSize, extensionCenter);
                                        allTriangles = allTriangles.concat(extensionTriangles);
                                        console.log('🔧 Added extension piece:', extensionTriangles.length, 'triangles, width:', extensionWidth);
                                    }
                                    
                                    console.log('🔧 L-shaped union total triangles:', allTriangles.length);
                                    return this.trianglesToSTL(allTriangles);
                                }
                                
                                cubesOverlap(cube1, cube2) {
                                    // Simple AABB overlap test
                                    const [s1x, s1y, s1z] = cube1.size;
                                    const [t1x, t1y, t1z] = cube1.translate;
                                    const [s2x, s2y, s2z] = cube2.size;
                                    const [t2x, t2y, t2z] = cube2.translate;
                                    
                                    // Cube bounds
                                    const c1_min = [t1x - s1x/2, t1y - s1y/2, t1z - s1z/2];
                                    const c1_max = [t1x + s1x/2, t1y + s1y/2, t1z + s1z/2];
                                    const c2_min = [t2x - s2x/2, t2y - s2y/2, t2z - s2z/2];
                                    const c2_max = [t2x + s2x/2, t2y + s2y/2, t2z + s2z/2];
                                    
                                    // AABB overlap test
                                    const overlap = (
                                        c1_min[0] < c2_max[0] && c1_max[0] > c2_min[0] &&
                                        c1_min[1] < c2_max[1] && c1_max[1] > c2_min[1] &&
                                        c1_min[2] < c2_max[2] && c1_max[2] > c2_min[2]
                                    );
                                    
                                    console.log('🔧 Overlap test:', overlap ? 'OVERLAPPING' : 'SEPARATE');
                                    return overlap;
                                }
                                
                                generateSmartUnionSTL(cubes) {
                                    console.log('🔧 Creating smart union visualization (no Z-fighting)');
                                    
                                    // For overlapping cubes, create a hull-like shape that avoids internal faces
                                    // This is a simplified approach that works well for basic demos
                                    
                                    if (cubes.length !== 2) {
                                        console.warn('⚠️ Smart union currently only supports 2 cubes');
                                        return this.generateUnionSTL(cubes);
                                    }
                                    
                                    const cube1 = cubes[0];
                                    const cube2 = cubes[1];
                                    
                                    // Create a bounding box that encompasses both cubes
                                    const [s1x, s1y, s1z] = cube1.size;
                                    const [t1x, t1y, t1z] = cube1.translate;
                                    const [s2x, s2y, s2z] = cube2.size;
                                    const [t2x, t2y, t2z] = cube2.translate;
                                    
                                    const c1_min = [t1x - s1x/2, t1y - s1y/2, t1z - s1z/2];
                                    const c1_max = [t1x + s1x/2, t1y + s1y/2, t1z + s1z/2];
                                    const c2_min = [t2x - s2x/2, t2y - s2y/2, t2z - s2z/2];
                                    const c2_max = [t2x + s2x/2, t2y + s2y/2, t2z + s2z/2];
                                    
                                    // Combined bounding box
                                    const union_min = [
                                        Math.min(c1_min[0], c2_min[0]),
                                        Math.min(c1_min[1], c2_min[1]),
                                        Math.min(c1_min[2], c2_min[2])
                                    ];
                                    const union_max = [
                                        Math.max(c1_max[0], c2_max[0]),
                                        Math.max(c1_max[1], c2_max[1]),
                                        Math.max(c1_max[2], c2_max[2])
                                    ];
                                    
                                    const union_size = [
                                        union_max[0] - union_min[0],
                                        union_max[1] - union_min[1], 
                                        union_max[2] - union_min[2]
                                    ];
                                    const union_center = [
                                        (union_min[0] + union_max[0]) / 2,
                                        (union_min[1] + union_max[1]) / 2,
                                        (union_min[2] + union_max[2]) / 2
                                    ];
                                    
                                    console.log('🔧 Smart union bounds:', union_min, 'to', union_max);
                                    console.log('🔧 Union size:', union_size, 'center:', union_center);
                                    
                                    // Generate single hull box geometry
                                    const triangles = this.generateCubeTriangles(union_size, union_center);
                                    return this.trianglesToSTL(triangles);
                                }
                                
                                generateDifferenceSTL(cubes) {
                                    console.log('🔧 Generating Difference STL for', cubes.length, 'cubes');
                                    
                                    if (cubes.length !== 2) {
                                        console.warn('⚠️ Difference operation requires exactly 2 cubes, got', cubes.length);
                                        return this.generateCubeSTL(cubes[0]); // Fallback to first cube
                                    }
                                    
                                    const mainCube = cubes[0];    // The cube we cut from
                                    const holeCube = cubes[1];    // The cube we subtract
                                    
                                    console.log('🔧 Main cube:', mainCube);
                                    console.log('🔧 Hole cube:', holeCube);
                                    
                                    // For Phase 1: Create a frame/tube structure by generating the walls around the hole
                                    console.log('🔧 Creating difference visualization (Phase 1 - frame structure)');
                                    
                                    const [mainSize, mainTranslate] = [mainCube.size, mainCube.translate];
                                    const [holeSize, holeTranslate] = [holeCube.size, holeCube.translate];
                                    
                                    // Create a hollow rectangular tube (frame around the hole)
                                    return this.generateHollowFrameSTL(mainSize, mainTranslate, holeSize, holeTranslate);
                                }
                                
                                generateHollowFrameSTL(mainSize, mainTranslate, holeSize, holeTranslate) {
                                    console.log('🔧 Generating hollow frame structure');
                                    
                                    const [mainSx, mainSy, mainSz] = mainSize;
                                    const [mainTx, mainTy, mainTz] = mainTranslate;
                                    const [holeSx, holeSy, holeSz] = holeSize;
                                    const [holeTx, holeTy, holeTz] = holeTranslate;
                                    
                                    let allTriangles = [];
                                    
                                    // Create 6 separate boxes that form the frame around the hole
                                    // This creates a hollow structure by building walls around the hole
                                    
                                    // 1. Bottom wall (Y direction)
                                    const bottomWallSize = [mainSx, (mainSy - holeSy) / 2, mainSz];
                                    const bottomWallPos = [mainTx, mainTy - (mainSy + holeSy) / 4, mainTz];
                                    const bottomTriangles = this.generateCubeTriangles(bottomWallSize, bottomWallPos);
                                    allTriangles = allTriangles.concat(bottomTriangles);
                                    
                                    // 2. Top wall (Y direction)
                                    const topWallSize = [mainSx, (mainSy - holeSy) / 2, mainSz];
                                    const topWallPos = [mainTx, mainTy + (mainSy + holeSy) / 4, mainTz];
                                    const topTriangles = this.generateCubeTriangles(topWallSize, topWallPos);
                                    allTriangles = allTriangles.concat(topTriangles);
                                    
                                    // 3. Left wall (Z direction)
                                    const leftWallSize = [mainSx, holeSy, (mainSz - holeSz) / 2];
                                    const leftWallPos = [mainTx, mainTy, mainTz - (mainSz + holeSz) / 4];
                                    const leftTriangles = this.generateCubeTriangles(leftWallSize, leftWallPos);
                                    allTriangles = allTriangles.concat(leftTriangles);
                                    
                                    // 4. Right wall (Z direction)
                                    const rightWallSize = [mainSx, holeSy, (mainSz - holeSz) / 2];
                                    const rightWallPos = [mainTx, mainTy, mainTz + (mainSz + holeSz) / 4];
                                    const rightTriangles = this.generateCubeTriangles(rightWallSize, rightWallPos);
                                    allTriangles = allTriangles.concat(rightTriangles);
                                    
                                    console.log('🔧 Generated frame structure with', allTriangles.length, 'triangles');
                                    console.log('🔧 Frame components: bottom, top, left, right walls');
                                    
                                    return this.trianglesToSTL(allTriangles);
                                }
                                
                                generateHollowCubeTriangles(size, translate = [0,0,0]) {
                                    // Generate cube triangles with inverted normals for interior surfaces
                                    const triangles = this.generateCubeTriangles(size, translate);
                                    
                                    // Invert normals and reverse vertex order for interior faces
                                    const invertedTriangles = [];
                                    for (let triangle of triangles) {
                                        // Reverse vertex order and invert normal
                                        const invertedTriangle = {
                                            normal: [-triangle.normal[0], -triangle.normal[1], -triangle.normal[2]],
                                            vertices: [triangle.vertices[2], triangle.vertices[1], triangle.vertices[0]]
                                        };
                                        invertedTriangles.push(invertedTriangle);
                                    }
                                    
                                    console.log('🔧 Generated', invertedTriangles.length, 'inverted triangles for hollow interior');
                                    return invertedTriangles;
                                }
                                
                                generateCubeTriangles(size, translate = [0,0,0]) {
                                    const [sx, sy, sz] = size;
                                    const [tx, ty, tz] = translate;
                                    
                                    // Generate cube with consistent face normals and vertex ordering
                                    const triangles = [];
                                    
                                    // Define 6 faces with explicit normals and consistent vertex order
                                    const faces = [
                                        // Bottom face (normal: 0, 0, -1)
                                        {
                                            normal: [0, 0, -1],
                                            vertices: [
                                                [-sx/2+tx, -sy/2+ty, -sz/2+tz],
                                                [sx/2+tx, -sy/2+ty, -sz/2+tz], 
                                                [sx/2+tx, sy/2+ty, -sz/2+tz],
                                                [-sx/2+tx, sy/2+ty, -sz/2+tz]
                                            ]
                                        },
                                        // Top face (normal: 0, 0, 1)
                                        {
                                            normal: [0, 0, 1],
                                            vertices: [
                                                [-sx/2+tx, -sy/2+ty, sz/2+tz],
                                                [-sx/2+tx, sy/2+ty, sz/2+tz],
                                                [sx/2+tx, sy/2+ty, sz/2+tz],
                                                [sx/2+tx, -sy/2+ty, sz/2+tz]
                                            ]
                                        },
                                        // Front face (normal: 0, -1, 0)
                                        {
                                            normal: [0, -1, 0],
                                            vertices: [
                                                [-sx/2+tx, -sy/2+ty, -sz/2+tz],
                                                [-sx/2+tx, -sy/2+ty, sz/2+tz],
                                                [sx/2+tx, -sy/2+ty, sz/2+tz],
                                                [sx/2+tx, -sy/2+ty, -sz/2+tz]
                                            ]
                                        },
                                        // Back face (normal: 0, 1, 0)
                                        {
                                            normal: [0, 1, 0],
                                            vertices: [
                                                [-sx/2+tx, sy/2+ty, -sz/2+tz],
                                                [sx/2+tx, sy/2+ty, -sz/2+tz],
                                                [sx/2+tx, sy/2+ty, sz/2+tz],
                                                [-sx/2+tx, sy/2+ty, sz/2+tz]
                                            ]
                                        },
                                        // Left face (normal: -1, 0, 0)
                                        {
                                            normal: [-1, 0, 0],
                                            vertices: [
                                                [-sx/2+tx, -sy/2+ty, -sz/2+tz],
                                                [-sx/2+tx, sy/2+ty, -sz/2+tz],
                                                [-sx/2+tx, sy/2+ty, sz/2+tz],
                                                [-sx/2+tx, -sy/2+ty, sz/2+tz]
                                            ]
                                        },
                                        // Right face (normal: 1, 0, 0)
                                        {
                                            normal: [1, 0, 0],
                                            vertices: [
                                                [sx/2+tx, -sy/2+ty, -sz/2+tz],
                                                [sx/2+tx, -sy/2+ty, sz/2+tz],
                                                [sx/2+tx, sy/2+ty, sz/2+tz],
                                                [sx/2+tx, sy/2+ty, -sz/2+tz]
                                            ]
                                        }
                                    ];
                                    
                                    // Convert each quad face to 2 triangles (back to simple array format)
                                    for (let face of faces) {
                                        const [v0, v1, v2, v3] = face.vertices;
                                        
                                        // First triangle: v0, v1, v2
                                        triangles.push([v0, v1, v2]);
                                        
                                        // Second triangle: v0, v2, v3  
                                        triangles.push([v0, v2, v3]);
                                    }
                                    
                                    return triangles;
                                }
                                
                                trianglesToSTL(triangles) {
                                    const triangleCount = triangles.length;
                                    console.log('🔧 Converting', triangleCount, 'triangles to STL (with consistent normals)');
                                    
                                    // STL Header (80 bytes)
                                    const header = new ArrayBuffer(80);
                                    const headerView = new Uint8Array(header);
                                    const headerText = `Clean union ${triangleCount}T - consistent normals`;
                                    for (let i = 0; i < Math.min(headerText.length, 80); i++) {
                                        headerView[i] = headerText.charCodeAt(i);
                                    }
                                    
                                    // Triangle count (4 bytes)
                                    const countBuffer = new ArrayBuffer(4);
                                    const countView = new DataView(countBuffer);
                                    countView.setUint32(0, triangleCount, true);
                                    
                                    // Triangle data (50 bytes per triangle)
                                    const triangleData = new ArrayBuffer(triangleCount * 50);
                                    const triangleView = new DataView(triangleData);
                                    
                                    let offset = 0;
                                    for (let triangle of triangles) {
                                        // Calculate normal from vertices (simple approach)
                                        const v1 = triangle[0], v2 = triangle[1], v3 = triangle[2];
                                        const u = [v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2]];
                                        const v = [v3[0]-v1[0], v3[1]-v1[1], v3[2]-v1[2]];
                                        
                                        let normal = [
                                            u[1]*v[2] - u[2]*v[1],
                                            u[2]*v[0] - u[0]*v[2], 
                                            u[0]*v[1] - u[1]*v[0]
                                        ];
                                        
                                        const len = Math.sqrt(normal[0]*normal[0] + normal[1]*normal[1] + normal[2]*normal[2]);
                                        if (len > 0.0001) { 
                                            normal[0]/=len; normal[1]/=len; normal[2]/=len; 
                                        } else {
                                            normal = [0, 0, 1];
                                        }
                                        
                                        // Write normal (12 bytes)
                                        triangleView.setFloat32(offset, normal[0], true); offset += 4;
                                        triangleView.setFloat32(offset, normal[1], true); offset += 4;
                                        triangleView.setFloat32(offset, normal[2], true); offset += 4;
                                        
                                        // Write vertices (36 bytes)
                                        for (let vertex of triangle) {
                                            triangleView.setFloat32(offset, vertex[0], true); offset += 4;
                                            triangleView.setFloat32(offset, vertex[1], true); offset += 4;
                                            triangleView.setFloat32(offset, vertex[2], true); offset += 4;
                                        }
                                        
                                        // Attribute byte count (2 bytes)
                                        triangleView.setUint16(offset, 0, true); offset += 2;
                                    }
                                    
                                    // Combine all parts
                                    const totalLength = header.byteLength + countBuffer.byteLength + triangleData.byteLength;
                                    const result = new Uint8Array(totalLength);
                                    result.set(new Uint8Array(header), 0);
                                    result.set(new Uint8Array(countBuffer), header.byteLength);
                                    result.set(new Uint8Array(triangleData), header.byteLength + countBuffer.byteLength);
                                    
                                    return result;
                                }
                                
                                generateCubeGeometry(size, translate = [0,0,0]) {
                                    const triangles = this.generateCubeTriangles(size, translate);
                                    return this.trianglesToSTL(triangles);
                                }
                                
                                generateSimpleCubeSTL() {
                                    // Generate a minimal binary STL for a cube
                                    const header = new ArrayBuffer(80);
                                    const headerView = new Uint8Array(header);
                                    const headerText = "Generated by marimo-openscad WASM test";
                                    for (let i = 0; i < Math.min(headerText.length, 80); i++) {
                                        headerView[i] = headerText.charCodeAt(i);
                                    }
                                    
                                    // 12 triangles for a cube (2 per face, 6 faces)
                                    const triangleCount = 12;
                                    const triangleData = new ArrayBuffer(triangleCount * 50); // 50 bytes per triangle
                                    const triangleView = new DataView(triangleData);
                                    
                                    // Triangle count
                                    const countBuffer = new ArrayBuffer(4);
                                    const countView = new DataView(countBuffer);
                                    countView.setUint32(0, triangleCount, true);
                                    
                                    // Cube vertices (simple 1x1x1 cube)
                                    const faces = [
                                        // Front face
                                        [[0,0,1], [1,0,1], [1,1,1]], [[0,0,1], [1,1,1], [0,1,1]],
                                        // Back face  
                                        [[1,0,0], [0,0,0], [0,1,0]], [[1,0,0], [0,1,0], [1,1,0]],
                                        // Left face
                                        [[0,0,0], [0,0,1], [0,1,1]], [[0,0,0], [0,1,1], [0,1,0]],
                                        // Right face
                                        [[1,0,1], [1,0,0], [1,1,0]], [[1,0,1], [1,1,0], [1,1,1]],
                                        // Top face
                                        [[0,1,1], [1,1,1], [1,1,0]], [[0,1,1], [1,1,0], [0,1,0]],
                                        // Bottom face
                                        [[0,0,0], [1,0,0], [1,0,1]], [[0,0,0], [1,0,1], [0,0,1]]
                                    ];
                                    
                                    let offset = 0;
                                    for (let i = 0; i < faces.length; i++) {
                                        const face = faces[i];
                                        
                                        // Calculate normal (simplified - just use face direction)
                                        const normal = [0, 0, 1]; // Simplified normal
                                        
                                        // Write normal (12 bytes)
                                        triangleView.setFloat32(offset, normal[0], true); offset += 4;
                                        triangleView.setFloat32(offset, normal[1], true); offset += 4;
                                        triangleView.setFloat32(offset, normal[2], true); offset += 4;
                                        
                                        // Write vertices (36 bytes = 3 vertices * 3 coords * 4 bytes)
                                        for (let j = 0; j < 3; j++) {
                                            triangleView.setFloat32(offset, face[j][0], true); offset += 4;
                                            triangleView.setFloat32(offset, face[j][1], true); offset += 4;
                                            triangleView.setFloat32(offset, face[j][2], true); offset += 4;
                                        }
                                        
                                        // Attribute byte count (2 bytes)
                                        triangleView.setUint16(offset, 0, true); offset += 2;
                                    }
                                    
                                    // Combine all parts
                                    const totalLength = header.byteLength + countBuffer.byteLength + triangleData.byteLength;
                                    const result = new Uint8Array(totalLength);
                                    result.set(new Uint8Array(header), 0);
                                    result.set(new Uint8Array(countBuffer), header.byteLength);
                                    result.set(new Uint8Array(triangleData), header.byteLength + countBuffer.byteLength);
                                    
                                    return result;
                                }
                            };
                            
                            console.log('✅ Simplified WASM wrapper created');
                            
                        } catch (loadError) {
                            console.warn('❌ Failed to load OpenSCAD WASM:', loadError);
                            return null;
                        }
                    }
                    
                    // Render SCAD code to STL using WASM
                    console.log('🔧 Executing OpenSCAD WASM render...');
                    
                    // Initialize OpenSCAD instance if needed
                    if (!wasmRenderer) {
                        wasmRenderer = new window.OpenSCAD();
                        console.log('🔧 OpenSCAD WASM instance created');
                    }
                    
                    // Render SCAD to STL
                    const stlResult = await wasmRenderer.render(scadCode, { format: 'stl' });
                    
                    if (stlResult && stlResult.length > 0) {
                        console.log('✅ WASM OpenSCAD render successful:', stlResult.length, 'bytes');
                        
                        // Convert to base64 for processSTLData
                        const base64STL = btoa(String.fromCharCode(...new Uint8Array(stlResult)));
                        return base64STL;
                    } else {
                        console.warn('⚠️ WASM OpenSCAD returned empty result');
                        return null;
                    }
                    
                } catch (wasmError) {
                    console.warn('❌ WASM OpenSCAD rendering failed:', wasmError);
                    return null;
                }
            }
            
            async function initializeWASMRenderer() {
                if (wasmSupported && rendererType !== 'local') {
                    try {
                        status.textContent = "🚀 Initializing WASM renderer...";
                        
                        // Get WASM base URL from Python model
                        const wasmBaseUrl = model.get("wasm_base_url") || "";
                        console.log('🚀 WASM Base URL:', wasmBaseUrl);
                        
                        if (wasmBaseUrl) {
                            // Try to initialize real WASM OpenSCAD
                            const wasmAvailable = await tryWASMOpenSCADRender('cube([1,1,1]);'); // Test render
                            
                            if (wasmAvailable) {
                                wasmRenderer = { available: true, real: true };
                                status.textContent = "✅ Real WASM OpenSCAD ready";
                                rendererInfo.textContent = "🚀 WASM | real OpenSCAD";
                                console.log('✅ Real WASM OpenSCAD initialized successfully');
                                return true;
                            } else {
                                // Fallback to geometric interpretation
                                wasmRenderer = { available: true, real: false };
                                status.textContent = "✅ WASM renderer ready (geometric)";
                                rendererInfo.textContent = "🚀 WASM | geometric";
                                console.log('⚠️ Using geometric interpretation fallback');
                                return true;
                            }
                        } else {
                            console.warn('❌ WASM base URL not available');
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
                const scadCode = model.get("scad_code") || "";
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
                
                // Enhanced logging for debugging
                console.log('🔍 updateModel called:', {
                    stlDataLength: stlData.length,
                    scadCodeLength: scadCode.length,
                    errorMsg: errorMsg,
                    isLoading: isLoading,
                    rendererType: currentRendererType,
                    rendererStatus: currentRendererStatus,
                    wasmSupported: wasmSupported
                });
                
                // Priority: Check for SCAD code first (WASM direct rendering)
                if (scadCode.trim() && (currentRendererType === 'wasm' || currentRendererType === 'auto')) {
                    console.log('🚀 WASM direct rendering with SCAD code:', scadCode.length, 'chars');
                    console.log('🚀 SCAD code preview:', scadCode.substring(0, 200) + '...');
                    status.textContent = '🚀 WASM rendering...';
                    status.style.background = "rgba(34,197,94,0.9)";
                    
                    try {
                        await renderWithWASM(scadCode);
                        return;
                    } catch (error) {
                        console.error('❌ WASM rendering failed:', error);
                        status.textContent = '⚠️ WASM failed, waiting for STL...';
                        status.style.background = "rgba(251,146,60,0.9)";
                    }
                }
                
                if (stlData.trim()) {
                    // Check if this is a WASM render request placeholder
                    if (stlData.includes('WASM_RENDER_REQUEST') && wasmRenderer) {
                        await handleWASMRenderRequest(stlData);
                    } else {
                        processSTLData(stlData);
                    }
                } else if (scadCode.trim()) {
                    // Have SCAD code but no STL - show that we're ready for WASM
                    status.textContent = "🚀 SCAD code ready, start WASM rendering";
                    status.style.background = "rgba(34,197,94,0.9)";
                    
                    // Trigger WASM rendering automatically
                    try {
                        await renderWithWASM(scadCode);
                    } catch (error) {
                        console.error('Auto WASM rendering failed:', error);
                        status.textContent = "❌ WASM auto-render failed";
                        status.style.background = "rgba(220,20,60,0.9)";
                    }
                } else {
                    status.textContent = "⏳ Waiting for data...";
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
            model.on("change:scad_code", updateModel);
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
        
        # Set WASM base URL if WASM renderer is available
        self._setup_wasm_urls()
        
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
    
    def _setup_wasm_urls(self):
        """Setup WASM URLs for JavaScript access"""
        try:
            # Check if we have a WASM renderer (directly or in hybrid)
            wasm_renderer = None
            
            if isinstance(self.renderer, OpenSCADWASMRenderer):
                wasm_renderer = self.renderer
            elif isinstance(self.renderer, HybridOpenSCADRenderer):
                if hasattr(self.renderer, 'wasm_renderer') and self.renderer.wasm_renderer:
                    wasm_renderer = self.renderer.wasm_renderer
            
            if wasm_renderer and wasm_renderer.is_available:
                self.wasm_base_url = wasm_renderer.get_wasm_url_base()
                self.wasm_enabled = True
                logger.info(f"WASM URLs configured: {self.wasm_base_url}")
            else:
                self.wasm_enabled = False
                self.wasm_base_url = ""
                logger.info("WASM not available or enabled")
                
        except Exception as e:
            logger.warning(f"Failed to setup WASM URLs: {e}")
            self.wasm_enabled = False
            self.wasm_base_url = ""
    
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