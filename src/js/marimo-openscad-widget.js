/**
 * Marimo OpenSCAD Widget - anywidget Compatible
 * 
 * WASM-safe, Main-Thread optimized widget for marimo notebooks
 * Compatible with both local Marimo and Marimo WASM environments
 */

import * as THREE from 'three';
import { OpenSCADDirectRenderer, detectEnvironmentConstraints } from './openscad-direct-renderer.js';

/**
 * STL Parser - WASM-safe implementation
 */
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
        console.log('📄 Parsing ASCII STL');
        
        const vertices = [];
        const normals = [];
        
        const lines = data.split('\n');
        let currentNormal = null;
        
        for (const line of lines) {
            const parts = line.trim().split(/\s+/);
            
            if (parts[0] === 'facet' && parts[1] === 'normal') {
                currentNormal = [
                    parseFloat(parts[2]),
                    parseFloat(parts[3]),
                    parseFloat(parts[4])
                ];
            } else if (parts[0] === 'vertex') {
                vertices.push(
                    parseFloat(parts[1]),
                    parseFloat(parts[2]),
                    parseFloat(parts[3])
                );
                
                if (currentNormal) {
                    normals.push(...currentNormal);
                }
            }
        }
        
        return { vertices, normals };
    }
}

/**
 * WASM-safe 3D Scene Manager
 */
class MarimoSceneManager {
    constructor(container) {
        this.container = container;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.currentMesh = null;
        this.directRenderer = null;
        this.isWasmReady = false;
        this.lastScadCode = null;
        this.controls = {
            mouseDown: false,
            mouseX: 0,
            mouseY: 0,
            cameraDistance: 50,
            cameraTheta: Math.PI / 4,
            cameraPhi: Math.PI / 4
        };
        
        this.environmentInfo = detectEnvironmentConstraints();
        console.log('🌍 Environment constraints detected:', this.environmentInfo);
    }
    
    async init() {
        try {
            // Scene setup
            this.scene = new THREE.Scene();
            this.scene.background = new THREE.Color(0xf8f9fa);
            
            // Camera setup
            const rect = this.container.getBoundingClientRect();
            this.camera = new THREE.PerspectiveCamera(45, rect.width / rect.height, 0.1, 1000);
            
            // Renderer setup
            this.renderer = new THREE.WebGLRenderer({ 
                antialias: true,
                alpha: true,
                powerPreference: 'high-performance'
            });
            
            this.renderer.setSize(rect.width, rect.height);
            this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            this.container.appendChild(this.renderer.domElement);
            
            this.setupLighting();
            this.setupGrid();
            this.addTestCube();
            this.setupControls();
            this.updateCameraPosition();
            
            // Initialize WASM renderer
            await this.initializeWASMRenderer();
            
            this.startAnimationLoop();
            
            console.log('✅ Marimo Scene Manager initialized');
            
        } catch (error) {
            console.error('❌ Scene initialization failed:', error);
            throw error;
        }
    }
    
    async initializeWASMRenderer() {
        try {
            console.log('🚀 Initializing WASM renderer for Marimo...');
            
            this.directRenderer = new OpenSCADDirectRenderer({
                enableManifold: true,
                outputFormat: 'binstl',
                timeout: 30000
            });
            
            await this.directRenderer.initialize();
            this.isWasmReady = true;
            
            console.log('✅ WASM renderer ready for Marimo');
            
        } catch (error) {
            console.warn('⚠️ WASM renderer initialization failed, using STL-only mode:', error);
            this.isWasmReady = false;
        }
    }
    
    setupLighting() {
        const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.7);
        directionalLight.position.set(10, 10, 5);
        this.scene.add(directionalLight);
        
        const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
        fillLight.position.set(-5, -5, -5);
        this.scene.add(fillLight);
    }
    
    setupGrid() {
        const gridHelper = new THREE.GridHelper(50, 50, 0x888888, 0xcccccc);
        gridHelper.position.y = -0.5;
        this.scene.add(gridHelper);
    }
    
    addTestCube() {
        const testGeometry = new THREE.BoxGeometry(1, 1, 1);
        const testMaterial = new THREE.MeshPhongMaterial({ 
            color: 0xff6b6b, 
            transparent: true, 
            opacity: 0.7 
        });
        const testCube = new THREE.Mesh(testGeometry, testMaterial);
        testCube.position.set(0, 1, 0);
        testCube.name = 'testCube';
        this.scene.add(testCube);
    }
    
    setupControls() {
        const canvas = this.renderer.domElement;
        
        canvas.addEventListener('mousedown', (e) => {
            this.controls.mouseDown = true;
            this.controls.mouseX = e.clientX;
            this.controls.mouseY = e.clientY;
        });
        
        canvas.addEventListener('mousemove', (e) => {
            if (!this.controls.mouseDown) return;
            
            const deltaX = e.clientX - this.controls.mouseX;
            const deltaY = e.clientY - this.controls.mouseY;
            
            this.controls.cameraTheta += deltaX * 0.01;
            this.controls.cameraPhi = Math.max(0.1, 
                Math.min(Math.PI - 0.1, this.controls.cameraPhi + deltaY * 0.01));
            
            this.updateCameraPosition();
            
            this.controls.mouseX = e.clientX;
            this.controls.mouseY = e.clientY;
        });
        
        canvas.addEventListener('mouseup', () => {
            this.controls.mouseDown = false;
        });
        
        canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            this.controls.cameraDistance = Math.max(5, 
                Math.min(200, this.controls.cameraDistance + e.deltaY * 0.05));
            this.updateCameraPosition();
        });
    }
    
    updateCameraPosition() {
        const { cameraDistance, cameraTheta, cameraPhi } = this.controls;
        
        this.camera.position.x = cameraDistance * Math.sin(cameraPhi) * Math.cos(cameraTheta);
        this.camera.position.y = cameraDistance * Math.cos(cameraPhi);
        this.camera.position.z = cameraDistance * Math.sin(cameraPhi) * Math.sin(cameraTheta);
        this.camera.lookAt(0, 0, 0);
    }
    
    startAnimationLoop() {
        const animate = () => {
            requestAnimationFrame(animate);
            this.renderer.render(this.scene, this.camera);
        };
        animate();
    }
    
    /**
     * Render SCAD code using direct WASM renderer
     */
    async renderScadCode(scadCode) {
        if (!scadCode || typeof scadCode !== 'string') {
            console.warn('⚠️ No SCAD code provided');
            return { success: false, message: 'No SCAD code provided' };
        }
        
        if (!this.isWasmReady || !this.directRenderer) {
            console.warn('⚠️ WASM renderer not ready');
            return { success: false, message: 'WASM renderer not ready' };
        }
        
        try {
            console.log('🚀 Rendering SCAD code with direct WASM...');
            
            const result = await this.directRenderer.renderToSTL(scadCode);
            
            if (result.success) {
                const success = this.loadSTLData(result.stlData);
                
                if (success) {
                    console.log(`✅ SCAD render completed: ${result.size} bytes`);
                    return {
                        success: true,
                        renderer: 'direct-wasm',
                        size: result.size,
                        renderTime: result.renderTime
                    };
                }
            }
            
            return { success: false, message: 'STL loading failed' };
            
        } catch (error) {
            console.error('❌ SCAD rendering failed:', error);
            return { success: false, message: error.message };
        }
    }
    
    /**
     * Load STL data into the scene
     */
    loadSTLData(stlData) {
        try {
            const { vertices, normals } = STLParser.parseSTL(stlData);
            
            this.clearMesh();
            
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
            geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
            
            const material = new THREE.MeshPhongMaterial({
                color: 0x3498db,
                shininess: 100,
                side: THREE.DoubleSide
            });
            
            this.currentMesh = new THREE.Mesh(geometry, material);
            this.scene.add(this.currentMesh);
            
            // Center and fit the model
            geometry.computeBoundingBox();
            const center = geometry.boundingBox.getCenter(new THREE.Vector3());
            this.currentMesh.position.copy(center.negate());
            
            const size = geometry.boundingBox.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);
            this.controls.cameraDistance = maxDim * 2;
            this.updateCameraPosition();
            
            console.log(`✅ STL loaded: ${vertices.length / 3} vertices`);
            return true;
            
        } catch (error) {
            console.error('Error loading STL:', error);
            return false;
        }
    }
    
    clearMesh() {
        if (this.currentMesh) {
            this.scene.remove(this.currentMesh);
            this.currentMesh.geometry.dispose();
            this.currentMesh.material.dispose();
            this.currentMesh = null;
        }
    }
    
    resize() {
        const rect = this.container.getBoundingClientRect();
        this.camera.aspect = rect.width / rect.height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(rect.width, rect.height);
    }
    
    getStatus() {
        return {
            isWasmReady: this.isWasmReady,
            hasRenderer: this.directRenderer !== null,
            hasMesh: this.currentMesh !== null,
            sceneChildren: this.scene ? this.scene.children.length : 0,
            environmentInfo: this.environmentInfo,
            rendererStatus: this.directRenderer ? this.directRenderer.getStatus() : null
        };
    }
    
    dispose() {
        this.clearMesh();
        
        if (this.renderer) {
            this.renderer.dispose();
            this.renderer = null;
        }
        
        if (this.scene) {
            this.scene.clear();
            this.scene = null;
        }
        
        this.camera = null;
        this.directRenderer = null;
    }
}

/**
 * Main anywidget render function - WASM-safe
 */
async function render({ model, el }) {
    console.log('🎯 Initializing Marimo OpenSCAD Widget (WASM-safe)');
    
    // Create UI container
    el.innerHTML = `
        <div style="width: 100%; height: 450px; border: 1px solid #ddd; position: relative; background: #fafafa;">
            <div id="container" style="width: 100%; height: 100%;"></div>
            <div id="status" style="position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.8); color: white; padding: 8px 12px; border-radius: 4px; font-family: monospace; font-size: 12px;">
                Initializing WASM-safe viewer...
            </div>
            <div id="controls" style="position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.9); padding: 8px; border-radius: 4px; font-size: 11px;">
                🖱️ Drag: Rotate | 🔍 Wheel: Zoom<br>
                <div style="margin-top: 4px; font-size: 10px; color: #666;">Mode: Direct WASM</div>
            </div>
        </div>
    `;
    
    const container = el.querySelector('#container');
    const statusElement = el.querySelector('#status');
    
    let sceneManager = null;
    
    try {
        // Check for test environment
        const isTestEnvironment = typeof process !== 'undefined' && process.env?.NODE_ENV === 'test' ||
                                  typeof window !== 'undefined' && window.happyDOM ||
                                  typeof global !== 'undefined' && global.happyDOM;
        
        if (isTestEnvironment) {
            statusElement.textContent = 'Test mode - 3D rendering disabled';
            console.log('🧪 Running in test mode, skipping 3D initialization');
        } else {
            statusElement.textContent = 'Setting up WASM-safe 3D scene...';
            
            sceneManager = new MarimoSceneManager(container);
            await sceneManager.init();
            
            statusElement.textContent = 'Ready - WASM renderer initialized';
            console.log('✅ Marimo OpenSCAD Widget ready');
        }
        
        // Handle model data changes
        function handleModelDataChange() {
            const stlData = model.get('stl_data');
            const scadCode = model.get('scad_code');
            
            if (!stlData && !scadCode) {
                if (sceneManager) {
                    sceneManager.clearMesh();
                }
                statusElement.textContent = 'No model data';
                return;
            }
            
            // Handle SCAD code rendering (priority)
            if (scadCode && sceneManager && sceneManager.isWasmReady) {
                console.log('🚀 Processing SCAD code with direct WASM...');
                statusElement.textContent = 'Rendering SCAD code...';
                
                sceneManager.renderScadCode(scadCode)
                    .then(result => {
                        if (result.success) {
                            statusElement.textContent = `WASM render completed (${result.size} bytes, ${result.renderTime.toFixed(0)}ms)`;
                            statusElement.style.backgroundColor = 'rgba(76, 175, 80, 0.8)';
                        } else {
                            statusElement.textContent = `WASM render failed: ${result.message}`;
                            statusElement.style.backgroundColor = 'rgba(244, 67, 54, 0.8)';
                        }
                    })
                    .catch(error => {
                        console.error('SCAD rendering error:', error);
                        statusElement.textContent = `Render error: ${error.message}`;
                        statusElement.style.backgroundColor = 'rgba(244, 67, 54, 0.8)';
                    });
                return;
            }
            
            // Handle STL data fallback
            if (stlData && sceneManager) {
                statusElement.textContent = 'Loading STL model...';
                
                try {
                    const binaryString = atob(stlData);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    
                    const success = sceneManager.loadSTLData(bytes.buffer);
                    if (success) {
                        statusElement.textContent = 'STL model loaded';
                        statusElement.style.backgroundColor = 'rgba(76, 175, 80, 0.8)';
                    } else {
                        statusElement.textContent = 'Error loading STL model';
                        statusElement.style.backgroundColor = 'rgba(244, 67, 54, 0.8)';
                    }
                } catch (error) {
                    console.error('STL loading error:', error);
                    statusElement.textContent = 'STL loading error';
                    statusElement.style.backgroundColor = 'rgba(244, 67, 54, 0.8)';
                }
            }
        }
        
        // Watch for model changes
        model.on('change:stl_data', handleModelDataChange);
        model.on('change:scad_code', handleModelDataChange);
        
        // Handle error messages
        model.on('change:error_message', () => {
            const error = model.get('error_message');
            if (error) {
                statusElement.textContent = `Error: ${error}`;
                statusElement.style.backgroundColor = 'rgba(244, 67, 54, 0.8)';
            }
        });
        
        // Handle loading state
        model.on('change:is_loading', () => {
            const isLoading = model.get('is_loading');
            if (isLoading) {
                statusElement.textContent = 'Loading...';
                statusElement.style.backgroundColor = 'rgba(255, 193, 7, 0.8)';
            }
        });
        
        // Initial load
        handleModelDataChange();
        
        // Handle resize
        window.addEventListener('resize', () => {
            if (sceneManager) {
                sceneManager.resize();
            }
        });
        
    } catch (error) {
        console.error('Widget initialization error:', error);
        statusElement.textContent = `Initialization error: ${error.message}`;
        statusElement.style.backgroundColor = 'rgba(244, 67, 54, 0.8)';
    }
    
    // Cleanup function
    return () => {
        if (sceneManager) {
            sceneManager.dispose();
        }
    };
}

// Export anywidget compatible object
export default { render };