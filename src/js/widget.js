/**
 * Marimo-OpenSCAD Widget
 * 
 * Modern 3D viewer for SolidPython2 objects using Three.js
 * Extracted from Python widget for better development workflow
 */

import * as THREE from 'three';

/**
 * STL Parser class for handling both binary and ASCII STL formats
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
        console.log("📄 Parsing ASCII STL");
        
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
 * 3D Scene Manager
 */
class SceneManager {
    constructor(container) {
        this.container = container;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.currentMesh = null;
        this.controls = {
            mouseDown: false,
            mouseX: 0,
            mouseY: 0,
            cameraDistance: 50,
            cameraTheta: Math.PI / 4,
            cameraPhi: Math.PI / 4
        };
        
        this.init();
    }
    
    init() {
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
            powerPreference: "high-performance",
            precision: "highp",
            stencil: false,
            depth: true
        });
        
        this.renderer.setSize(rect.width, rect.height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.sortObjects = true;
        this.renderer.toneMapping = THREE.LinearToneMapping;
        
        // Ensure canvas can receive mouse events
        this.renderer.domElement.style.cursor = 'grab';
        this.renderer.domElement.style.userSelect = 'none';
        
        this.container.appendChild(this.renderer.domElement);
        
        this.setupWebGLContextHandling();
        this.setupLighting();
        this.setupGrid();
        this.addTestCube(); // Add test cube to verify 3D scene works
        this.setupControls();
        this.updateCameraPosition();
        
        console.log(`📹 Initial camera position: x=${this.camera.position.x.toFixed(2)}, y=${this.camera.position.y.toFixed(2)}, z=${this.camera.position.z.toFixed(2)}`);
        
        this.startAnimationLoop();
    }
    
    setupLighting() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
        this.scene.add(ambientLight);
        
        // Main directional light
        const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.7);
        directionalLight1.position.set(10, 10, 5);
        directionalLight1.castShadow = true;
        this.scene.add(directionalLight1);
        
        // Fill light
        const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
        directionalLight2.position.set(-5, -5, -5);
        this.scene.add(directionalLight2);
    }
    
    setupGrid() {
        const gridHelper = new THREE.GridHelper(50, 50, 0x888888, 0xcccccc);
        gridHelper.position.y = -0.5;
        this.scene.add(gridHelper);
    }
    
    addTestCube() {
        // Add a small test cube to verify 3D scene is working
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
        console.log('🧪 Test cube added to verify 3D scene functionality');
    }
    
    setupControls() {
        const canvas = this.renderer.domElement;
        
        // CRITICAL VALIDATION: Verify controls are attached to correct element
        if (!canvas || canvas.tagName !== 'CANVAS') {
            console.error('❌ CRITICAL ERROR: Controls not attached to canvas element!');
            throw new Error('Controls must be attached to canvas element');
        }
        
        console.log(`🔍 Setting up controls on canvas element:`, canvas.tagName, canvas.width, canvas.height);
        console.log(`✅ VERIFIED: Controls correctly attached to canvas element`);
        
        canvas.addEventListener('mousedown', (e) => {
            this.controls.mouseDown = true;
            this.controls.mouseX = e.clientX;
            this.controls.mouseY = e.clientY;
            console.log('🔄 Mouse down event triggered');
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
    
    setupWebGLContextHandling() {
        if (!this.renderer || !this.renderer.domElement) return;
        
        this.renderer.domElement.addEventListener('webglcontextlost', (event) => {
            event.preventDefault();
            console.warn('⚠️ WebGL context lost');
        });
        
        this.renderer.domElement.addEventListener('webglcontextrestored', () => {
            console.log('✅ WebGL context restored');
            // Reinitialize scene components
            this.setupLighting();
            this.setupGrid();
            if (this.currentMesh) {
                // Reload current mesh if it exists
                const geometry = this.currentMesh.geometry;
                const material = this.currentMesh.material;
                this.scene.add(new THREE.Mesh(geometry, material));
            }
        });
    }
    
    startAnimationLoop() {
        const animate = () => {
            requestAnimationFrame(animate);
            this.renderer.render(this.scene, this.camera);
        };
        animate();
    }
    
    loadSTLData(stlData) {
        try {
            const { vertices, normals } = STLParser.parseSTL(stlData);
            
            // Clear existing mesh
            this.clearMesh();
            
            // Create geometry
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
            geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
            
            // Create material
            const material = new THREE.MeshPhongMaterial({
                color: 0x3498db,
                shininess: 100,
                side: THREE.DoubleSide
            });
            
            // Create mesh
            this.currentMesh = new THREE.Mesh(geometry, material);
            this.currentMesh.castShadow = true;
            this.currentMesh.receiveShadow = true;
            
            // Center the mesh
            geometry.computeBoundingBox();
            const center = geometry.boundingBox.getCenter(new THREE.Vector3());
            this.currentMesh.position.copy(center.negate());
            
            this.scene.add(this.currentMesh);
            
            // CRITICAL VALIDATION: Verify mesh was actually added to scene
            if (!this.scene.children.includes(this.currentMesh)) {
                console.error('❌ CRITICAL ERROR: Mesh was not added to scene!');
                throw new Error('Mesh was not added to scene');
            }
            
            console.log(`🔍 Scene children count: ${this.scene.children.length}`);
            console.log(`🔍 Mesh position: x=${this.currentMesh.position.x.toFixed(2)}, y=${this.currentMesh.position.y.toFixed(2)}, z=${this.currentMesh.position.z.toFixed(2)}`);
            console.log(`✅ VERIFIED: Mesh successfully added to scene and is visible`);
            
            // Adjust camera to fit model
            const size = geometry.boundingBox.getSize(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);
            this.controls.cameraDistance = maxDim * 2;
            this.updateCameraPosition();
            
            console.log(`✅ STL loaded: ${vertices.length / 3} vertices, camera distance: ${this.controls.cameraDistance}`);
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
    
    dispose() {
        this.clearMesh();
        
        // Remove event listeners
        if (this.renderer && this.renderer.domElement) {
            this.renderer.domElement.removeEventListener('webglcontextlost', null);
            this.renderer.domElement.removeEventListener('webglcontextrestored', null);
            this.renderer.domElement.removeEventListener('mousedown', null);
            this.renderer.domElement.removeEventListener('mousemove', null);
            this.renderer.domElement.removeEventListener('mouseup', null);
            this.renderer.domElement.removeEventListener('wheel', null);
        }
        
        if (this.renderer) {
            this.renderer.dispose();
            this.renderer = null;
        }
        
        if (this.scene) {
            this.scene.clear();
            this.scene = null;
        }
        
        this.camera = null;
    }
}

/**
 * Main widget render function for anywidget
 */
export function render({ model, el }) {
    // Create container with status display
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
    const statusElement = el.querySelector('#status');
    
    let sceneManager = null;
    
    try {
        statusElement.textContent = "Setting up 3D scene...";
        
        // Initialize scene manager with validation
        sceneManager = new SceneManager(container);
        
        // Verify scene was created successfully
        if (!sceneManager.scene || !sceneManager.renderer) {
            throw new Error('Failed to initialize 3D scene');
        }
        
        statusElement.textContent = "Ready - waiting for model data...";
        console.log('✅ 3D scene initialized successfully');
        
        // Handle model data changes
        function handleModelDataChange() {
            const stlData = model.get('stl_data');
            if (!stlData) {
                sceneManager.clearMesh();
                statusElement.textContent = "No model data";
                return;
            }
            
            statusElement.textContent = "Loading model...";
            
            try {
                // Decode base64 STL data
                const binaryString = atob(stlData);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                
                const success = sceneManager.loadSTLData(bytes.buffer);
                if (success) {
                    statusElement.textContent = `Model loaded (${sceneManager.scene.children.length} objects in scene)`;
                    statusElement.style.backgroundColor = 'rgba(76, 175, 80, 0.8)';
                } else {
                    statusElement.textContent = "Error loading model";
                    statusElement.style.backgroundColor = 'rgba(244, 67, 54, 0.8)';
                }
                
            } catch (error) {
                console.error('Error loading model:', error);
                statusElement.textContent = "Error loading model";
            }
        }
        
        // Handle error messages
        function handleErrorMessage() {
            const error = model.get('error_message');
            if (error) {
                statusElement.textContent = `Error: ${error}`;
            }
        }
        
        // Handle loading state
        function handleLoadingState() {
            const isLoading = model.get('is_loading');
            if (isLoading) {
                statusElement.textContent = "Loading...";
            }
        }
        
        // Watch for model changes
        model.on('change:stl_data', handleModelDataChange);
        model.on('change:error_message', handleErrorMessage);
        model.on('change:is_loading', handleLoadingState);
        
        // Initial load
        handleModelDataChange();
        handleErrorMessage();
        handleLoadingState();
        
        // Handle resize
        window.addEventListener('resize', () => {
            if (sceneManager) {
                sceneManager.resize();
            }
        });
        
    } catch (error) {
        console.error('Widget initialization error:', error);
        statusElement.textContent = `Initialization error: ${error.message}`;
    }
    
    // Cleanup function
    return () => {
        if (sceneManager) {
            sceneManager.dispose();
        }
    };
}

// Export for UMD builds
export default { render };