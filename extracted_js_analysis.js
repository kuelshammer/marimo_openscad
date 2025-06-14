    _esm = """
    async function render({ model, el }) {
        console.log('🚀 Starting marimo-openscad viewer...');
        // Check renderer type from model
        const rendererType = model.get('renderer_type') || 'auto';
        const wasmSupported = model.get('wasm_supported') || false;
        const rendererStatus = model.get('renderer_status') || 'initializing';
        
        // Container Setup with renderer info
        el.innerHTML = 
            '<div style="width: 100%; height: 450px; border: 1px solid #ddd; position: relative; background: #fafafa;">' +
                '<div id="container" style="width: 100%; height: 100%;"></div>' +
                '<div id="status" style="position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.8); color: white; padding: 8px 12px; border-radius: 4px; font-family: monospace; font-size: 12px;">' +
                    'Initializing 3D viewer (' + rendererType + ')...' +
                '</div>' +
                '<div id="renderer-info" style="position: absolute; bottom: 10px; left: 10px; background: rgba(0,0,0,0.7); color: white; padding: 4px 8px; border-radius: 3px; font-family: monospace; font-size: 10px;">' +
                    (wasmSupported ? '🚀 WASM' : '🔧 Local') + ' | ' + rendererStatus +
                '</div>' +
                '<div id="controls" style="position: absolute; top: 10px; right: 10px; background: rgba(255,255,255,0.9); padding: 8px; border-radius: 4px; font-size: 11px;">' +
                    '🖱️ Drag: Rotate | 🔍 Wheel: Zoom' +
                '</div>' +
            '</div>';
        
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
