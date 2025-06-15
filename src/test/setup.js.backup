/**
 * Test setup for Vitest
 * Configures testing environment for widget testing
 */

// Mock Three.js for testing
global.THREE = {
    Scene: class MockScene {
        constructor() {
            this.children = [];
            this.background = null;
        }
        add(object) {
            this.children.push(object);
        }
        remove(object) {
            const index = this.children.indexOf(object);
            if (index > -1) {
                this.children.splice(index, 1);
            }
        }
    },
    
    PerspectiveCamera: class MockCamera {
        constructor(fov, aspect, near, far) {
            this.fov = fov;
            this.aspect = aspect;
            this.near = near;
            this.far = far;
            this.position = { x: 0, y: 0, z: 0, set: () => {} };
        }
        lookAt() {}
        updateProjectionMatrix() {}
    },
    
    WebGLRenderer: class MockRenderer {
        constructor(options) {
            this.domElement = document.createElement('canvas');
        }
        setSize() {}
        setPixelRatio() {}
        render() {}
        dispose() {}
    },
    
    Color: class MockColor {
        constructor(color) {
            this.color = color;
        }
    },
    
    AmbientLight: class MockLight {
        constructor(color, intensity) {
            this.color = color;
            this.intensity = intensity;
        }
    },
    
    DirectionalLight: class MockLight {
        constructor(color, intensity) {
            this.color = color;
            this.intensity = intensity;
            this.position = { set: () => {} };
            this.castShadow = false;
        }
    },
    
    GridHelper: class MockGridHelper {
        constructor(size, divisions, color1, color2) {
            this.position = { y: 0 };
        }
    },
    
    BufferGeometry: class MockGeometry {
        constructor() {
            this.attributes = {};
            this.boundingBox = null;
        }
        setAttribute(name, attribute) {
            this.attributes[name] = attribute;
        }
        computeBoundingBox() {
            this.boundingBox = {
                getCenter: () => ({ x: 0, y: 0, z: 0, negate: () => ({ x: 0, y: 0, z: 0 }) }),
                getSize: () => ({ x: 10, y: 10, z: 10 })
            };
        }
        dispose() {}
    },
    
    Float32BufferAttribute: class MockAttribute {
        constructor(array, itemSize) {
            this.array = array;
            this.itemSize = itemSize;
        }
    },
    
    MeshPhongMaterial: class MockMaterial {
        constructor(options) {
            Object.assign(this, options);
        }
        dispose() {}
    },
    
    Mesh: class MockMesh {
        constructor(geometry, material) {
            this.geometry = geometry;
            this.material = material;
            this.position = { copy: () => {} };
            this.castShadow = false;
            this.receiveShadow = false;
        }
    },
    
    Vector3: class MockVector3 {
        constructor(x = 0, y = 0, z = 0) {
            this.x = x;
            this.y = y;
            this.z = z;
        }
        negate() {
            return new global.THREE.Vector3(-this.x, -this.y, -this.z);
        }
        copy(v) {
            this.x = v.x;
            this.y = v.y;
            this.z = v.z;
            return this;
        }
    },
    
    // Constants
    DoubleSide: 2,
    PCFSoftShadowMap: 1,
    LinearToneMapping: 0
};

// Mock DOM APIs
global.atob = (str) => {
    return Buffer.from(str, 'base64').toString('binary');
};

global.btoa = (str) => {
    return Buffer.from(str, 'binary').toString('base64');
};

// Mock missing DOM methods
global.document = global.document || {};
global.document.createElementNS = global.document.createElementNS || function(namespace, tagName) {
    return global.document.createElement(tagName);
};

global.document.createElement = global.document.createElement || function(tagName) {
    return {
        style: {},
        classList: {
            add: () => {},
            remove: () => {},
            contains: () => false
        },
        addEventListener: () => {},
        removeEventListener: () => {},
        appendChild: () => {},
        removeChild: () => {},
        getAttribute: () => null,
        setAttribute: () => {},
        getBoundingClientRect: () => ({ width: 600, height: 400, top: 0, left: 0 })
    };
};

// Mock performance API
global.performance = {
    now: () => Date.now()
};

// Mock requestAnimationFrame
global.requestAnimationFrame = (callback) => {
    return setTimeout(callback, 16);
};

global.cancelAnimationFrame = (id) => {
    clearTimeout(id);
};

// Mock Canvas and WebGL for WASM tests
global.HTMLCanvasElement = class MockCanvas {
    constructor() {
        this.width = 300;
        this.height = 150;
        this.style = {};
    }
    
    getContext(contextType) {
        if (contextType === 'webgl' || contextType === 'experimental-webgl') {
            return {
                // WebGL context mock
                getShaderPrecisionFormat: () => ({ precision: 23 }),
                getExtension: () => null,
                getParameter: (param) => {
                    // Mock common WebGL parameters
                    if (param === 0x1F00) return 'Mock WebGL Vendor'; // GL_VENDOR
                    if (param === 0x1F01) return 'Mock WebGL Renderer'; // GL_RENDERER
                    if (param === 0x1F02) return 'WebGL 1.0'; // GL_VERSION
                    return null;
                },
                createShader: () => ({}),
                createProgram: () => ({}),
                deleteShader: () => {},
                deleteProgram: () => {},
                useProgram: () => {},
                createBuffer: () => ({}),
                bindBuffer: () => {},
                bufferData: () => {},
                createTexture: () => ({}),
                bindTexture: () => {},
                texImage2D: () => {},
                viewport: () => {},
                clear: () => {},
                drawArrays: () => {},
                drawElements: () => {},
                enable: () => {},
                disable: () => {},
                clearColor: () => {},
                clearDepth: () => {}
            };
        } else if (contextType === '2d') {
            return {
                // 2D context mock
                fillRect: () => {},
                clearRect: () => {},
                strokeRect: () => {},
                beginPath: () => {},
                moveTo: () => {},
                lineTo: () => {},
                stroke: () => {},
                fill: () => {},
                arc: () => {},
                fillText: () => {},
                measureText: () => ({ width: 100 })
            };
        }
        return null;
    }
    
    toDataURL() {
        return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
    }
};

// Mock WebAssembly for WASM tests
global.WebAssembly = {
    Module: class MockWASMModule {
        constructor(bytes) {
            this.bytes = bytes;
        }
        
        static imports() {
            return [];
        }
    },
    
    Memory: class MockWASMMemory {
        constructor(descriptor) {
            this.buffer = new ArrayBuffer(descriptor.initial * 65536); // 64KB pages
        }
    },
    
    Instance: class MockWASMInstance {
        constructor(module, imports = {}) {
            this.exports = {
                // Mock OpenSCAD WASM exports
                render: () => new Uint8Array(100), // Mock STL data
                memory: new ArrayBuffer(1024 * 1024), // 1MB mock memory
                _initialize: () => {},
                _free: () => {},
                _malloc: () => 0
            };
        }
    },
    
    instantiate: async function(bytes, imports = {}) {
        const module = new this.Module(bytes);
        const instance = new this.Instance(module, imports);
        return { module, instance };
    },
    
    compile: async function(bytes) {
        return new this.Module(bytes);
    },
    
    validate: function(bytes) {
        return bytes instanceof ArrayBuffer || bytes instanceof Uint8Array;
    }
};

// Mock Worker for WASM worker tests
global.Worker = class MockWorker {
    constructor(scriptURL) {
        this.scriptURL = scriptURL;
        this.onmessage = null;
        this.onerror = null;
        
        // Simulate async worker initialization
        setTimeout(() => {
            if (this.onmessage) {
                this.onmessage({
                    data: { type: 'ready', status: 'initialized' }
                });
            }
        }, 10);
    }
    
    postMessage(data) {
        // Mock worker response
        setTimeout(() => {
            if (this.onmessage) {
                if (data.type === 'render') {
                    // Mock STL rendering response
                    this.onmessage({
                        data: {
                            type: 'render_complete',
                            stl_data: new Uint8Array(100), // Mock STL
                            success: true
                        }
                    });
                } else {
                    this.onmessage({
                        data: { type: 'response', payload: 'mock_response' }
                    });
                }
            }
        }, 50); // Simulate processing time
    }
    
    terminate() {
        // Mock worker termination
    }
};

// Mock URL and Blob for worker creation
global.URL = global.URL || {
    createObjectURL: (blob) => 'blob:mock-url-' + Math.random(),
    revokeObjectURL: (url) => {}
};

global.Blob = global.Blob || class MockBlob {
    constructor(parts, options = {}) {
        this.parts = parts;
        this.type = options.type || '';
        this.size = parts.reduce((size, part) => size + (part.length || 0), 0);
    }
};

// Mock fetch for WASM module loading
global.fetch = global.fetch || async function(url) {
    return {
        ok: true,
        status: 200,
        arrayBuffer: async () => new ArrayBuffer(1024), // Mock WASM bytes
        text: async () => '// Mock JavaScript module',
        json: async () => ({ version: '1.0.0', mock: true })
    };
};

// Mock ResizeObserver for responsive components
global.ResizeObserver = class MockResizeObserver {
    constructor(callback) {
        this.callback = callback;
    }
    
    observe() {
        // Mock resize event
        setTimeout(() => {
            this.callback([{
                target: { clientWidth: 600, clientHeight: 400 },
                contentRect: { width: 600, height: 400 }
            }]);
        }, 10);
    }
    
    unobserve() {}
    disconnect() {}
};

// Mock IntersectionObserver for performance optimization
global.IntersectionObserver = class MockIntersectionObserver {
    constructor(callback) {
        this.callback = callback;
    }
    
    observe() {
        // Mock intersection event
        setTimeout(() => {
            this.callback([{
                target: {},
                isIntersecting: true,
                intersectionRatio: 1.0
            }]);
        }, 10);
    }
    
    unobserve() {}
    disconnect() {}
};

console.log('✅ Test setup complete with enhanced WASM and browser mocking');