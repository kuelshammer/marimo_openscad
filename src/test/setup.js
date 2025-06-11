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

console.log('✅ Test setup complete');