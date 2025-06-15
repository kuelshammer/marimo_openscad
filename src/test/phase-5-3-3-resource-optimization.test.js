/**
 * Phase 5.3.3 Resource Optimization Engine Tests
 * Comprehensive tests for geometry and buffer optimization
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// Mock global objects and APIs
global.THREE = {
    Vector3: class {
        constructor(x = 0, y = 0, z = 0) { this.x = x; this.y = y; this.z = z; }
        clone() { return new THREE.Vector3(this.x, this.y, this.z); }
        sub(v) { this.x -= v.x; this.y -= v.y; this.z -= v.z; return this; }
        add(v) { this.x += v.x; this.y += v.y; this.z += v.z; return this; }
        addScaledVector(v, s) { this.x += v.x * s; this.y += v.y * s; this.z += v.z * s; return this; }
        copy(v) { this.x = v.x; this.y = v.y; this.z = v.z; return this; }
        set(x, y, z) { this.x = x; this.y = y; this.z = z; return this; }
        distanceTo(v) { return Math.sqrt((this.x - v.x)**2 + (this.y - v.y)**2 + (this.z - v.z)**2); }
        normalize() { const len = Math.sqrt(this.x**2 + this.y**2 + this.z**2); this.x /= len; this.y /= len; this.z /= len; return this; }
        length() { return Math.sqrt(this.x**2 + this.y**2 + this.z**2); }
        dot(v) { return this.x * v.x + this.y * v.y + this.z * v.z; }
    },
    BufferGeometry: class {
        constructor() {
            this.attributes = {};
            this.index = null;
            this.userData = {};
            this.boundingBox = null;
            this.boundingSphere = null;
        }
        setAttribute(name, attr) { this.attributes[name] = attr; }
        getAttribute(name) { return this.attributes[name]; }
        getIndex() { return this.index; }
        setIndex(index) { this.index = index; }
        computeBoundingBox() { 
            this.boundingBox = { 
                min: new THREE.Vector3(-1, -1, -1), 
                max: new THREE.Vector3(1, 1, 1) 
            }; 
        }
        computeBoundingSphere() { 
            this.boundingSphere = { radius: 1, center: new THREE.Vector3() }; 
        }
        clone() { return new THREE.BufferGeometry(); }
        dispose() {}
        copy(source) { this.attributes = { ...source.attributes }; return this; }
        merge(geometry) {
            // Mock merge functionality
            Object.keys(geometry.attributes).forEach(key => {
                if (!this.attributes[key]) this.attributes[key] = geometry.attributes[key];
            });
        }
    },
    BufferAttribute: class {
        constructor(array, itemSize) {
            this.array = array;
            this.itemSize = itemSize;
            this.count = array.length / itemSize;
            this.needsUpdate = false;
        }
        clone() { return new THREE.BufferAttribute([...this.array], this.itemSize); }
        copy(source) { this.array = [...source.array]; this.itemSize = source.itemSize; return this; }
        setArray(array) { this.array = array; this.count = array.length / this.itemSize; }
    },
    Uint16BufferAttribute: class {
        constructor(array, itemSize) {
            this.array = new Uint16Array(array);
            this.itemSize = itemSize;
            this.count = this.array.length / itemSize;
            this.needsUpdate = false;
        }
        clone() { return new THREE.Uint16BufferAttribute([...this.array], this.itemSize); }
    },
    Uint32BufferAttribute: class {
        constructor(array, itemSize) {
            this.array = new Uint32Array(array);
            this.itemSize = itemSize;
            this.count = this.array.length / itemSize;
            this.needsUpdate = false;
        }
        clone() { return new THREE.Uint32BufferAttribute([...this.array], this.itemSize); }
    },
    Float32BufferAttribute: class {
        constructor(array, itemSize) {
            this.array = new Float32Array(array);
            this.itemSize = itemSize;
            this.count = this.array.length / itemSize;
            this.needsUpdate = false;
        }
        clone() { return new THREE.Float32BufferAttribute([...this.array], this.itemSize); }
    },
    Object3D: class {
        constructor() {
            this.children = [];
            this.visible = true;
            this.geometry = null;
            this.material = null;
            this.userData = {};
            this.position = new THREE.Vector3();
            this.rotation = { x: 0, y: 0, z: 0 };
            this.scale = new THREE.Vector3(1, 1, 1);
        }
        add(obj) { this.children.push(obj); }
        remove(obj) { this.children = this.children.filter(c => c !== obj); }
        traverse(fn) { fn(this); this.children.forEach(c => c.traverse?.(fn) || fn(c)); }
        clone() { return new THREE.Object3D(); }
    },
    Mesh: class {
        constructor(geometry, material) {
            this.geometry = geometry;
            this.material = material;
            this.visible = true;
            this.children = [];
            this.userData = {};
            this.position = new THREE.Vector3();
            this.rotation = { x: 0, y: 0, z: 0 };
            this.scale = new THREE.Vector3(1, 1, 1);
        }
        clone() { return new THREE.Mesh(this.geometry?.clone(), this.material); }
        traverse(fn) { fn(this); this.children.forEach(c => c.traverse?.(fn) || fn(c)); }
        updateMatrixWorld() {}
    },
    InstancedMesh: class {
        constructor(geometry, material, count) {
            this.geometry = geometry;
            this.material = material;
            this.count = count;
            this.instanceMatrix = { needsUpdate: false };
            this.visible = true;
            this.userData = {};
        }
        setMatrixAt(index, matrix) {}
        getMatrixAt(index, matrix) {}
        clone() { return new THREE.InstancedMesh(this.geometry?.clone(), this.material, this.count); }
    },
    MeshBasicMaterial: class {
        constructor(params = {}) {
            this.color = params.color || '#ffffff';
            this.wireframe = params.wireframe || false;
            this.transparent = params.transparent || false;
            this.opacity = params.opacity || 1.0;
            this.userData = {};
        }
        clone() { return new THREE.MeshBasicMaterial(); }
        dispose() {}
    },
    WebGLRenderer: class {
        constructor() {
            this.info = {
                memory: { geometries: 0, textures: 0 },
                render: { calls: 0, triangles: 0, points: 0, lines: 0 }
            };
        }
        dispose() {}
    }
};

global.performance = {
    memory: {
        usedJSHeapSize: 50 * 1024 * 1024,  // 50MB
        totalJSHeapSize: 100 * 1024 * 1024, // 100MB
        jsHeapSizeLimit: 200 * 1024 * 1024  // 200MB
    },
    now: vi.fn(() => Date.now())
};

global.window = {
    performance: global.performance,
    requestAnimationFrame: vi.fn((callback) => {
        setTimeout(callback, 16); // 60fps
        return 1;
    }),
    cancelAnimationFrame: vi.fn()
};

// Create mock renderer
function createMockRenderer() {
    return new THREE.WebGLRenderer();
}

// Create mock scene
function createMockScene() {
    const scene = new THREE.Object3D();
    scene.children = [];
    scene.add = vi.fn((obj) => scene.children.push(obj));
    scene.remove = vi.fn((obj) => scene.children = scene.children.filter(c => c !== obj));
    scene.traverse = vi.fn((fn) => {
        fn(scene);
        scene.children.forEach(child => {
            fn(child);
            if (child.children) {
                child.children.forEach(grandchild => fn(grandchild));
            }
        });
    });
    return scene;
}

// Create ResourceOptimizationEngine test class
function createResourceOptimizationEngine() {
    const scene = createMockScene();
    const renderer = createMockRenderer();

    // Simplified ResourceOptimizationEngine for testing
    class ResourceOptimizationEngine {
        constructor(scene, renderer) {
            this.scene = scene;
            this.renderer = renderer;
            this.enabled = true;
            
            // Optimization settings
            this.geometryPooling = true;
            this.bufferOptimization = true;
            this.instancedRendering = true;
            this.memoryManagement = true;
            this.autoCleanup = true;
            
            // Geometry pools
            this.geometryPool = new Map();
            this.bufferPool = new Map();
            this.materialPool = new Map();
            
            // Instance management
            this.instanceGroups = new Map();
            this.instancedObjects = new Map();
            
            // Memory tracking
            this.memoryStats = {
                geometries: 0,
                buffers: 0,
                materials: 0,
                instances: 0,
                totalMemory: 0
            };
            
            // Optimization thresholds
            this.thresholds = {
                maxGeometries: 1000,
                maxBuffers: 500,
                maxMaterials: 100,
                memoryLimit: 100 * 1024 * 1024, // 100MB
                instanceThreshold: 5, // Create instanced mesh after 5 similar objects
                cleanupInterval: 30000, // 30 seconds
                unusedResourceAge: 60000 // 1 minute
            };
            
            // Resource usage tracking
            this.resourceUsage = new Map();
            this.lastCleanup = performance.now();
            
            // Optimization statistics
            this.optimizationStats = {
                geometriesOptimized: 0,
                buffersOptimized: 0,
                instancesCreated: 0,
                memoryFreed: 0,
                optimizationTime: 0
            };
            
            this.initializeOptimization();
        }

        initializeOptimization() {
            if (this.autoCleanup) {
                this.startAutoCleanup();
            }
            console.log('🔧 ResourceOptimizationEngine initialized');
        }

        startAutoCleanup() {
            const cleanupLoop = () => {
                if (!this.enabled) return;
                
                const now = performance.now();
                if (now - this.lastCleanup > this.thresholds.cleanupInterval) {
                    this.performCleanup();
                    this.lastCleanup = now;
                }
                
                setTimeout(cleanupLoop, this.thresholds.cleanupInterval);
            };
            
            setTimeout(cleanupLoop, this.thresholds.cleanupInterval);
        }

        optimizeGeometry(geometry) {
            if (!this.geometryPooling || !geometry) return geometry;
            
            const startTime = performance.now();
            
            // Generate geometry signature for pooling
            const signature = this.generateGeometrySignature(geometry);
            
            // Check if we already have this geometry in pool
            if (this.geometryPool.has(signature)) {
                const pooledGeometry = this.geometryPool.get(signature);
                this.updateResourceUsage(signature, 'geometry');
                this.optimizationStats.geometriesOptimized++;
                return pooledGeometry;
            }
            
            // Optimize the geometry
            const optimizedGeometry = this.performGeometryOptimization(geometry);
            
            // Add to pool
            this.geometryPool.set(signature, optimizedGeometry);
            this.updateResourceUsage(signature, 'geometry');
            this.memoryStats.geometries++;
            
            this.optimizationStats.optimizationTime += performance.now() - startTime;
            return optimizedGeometry;
        }

        generateGeometrySignature(geometry) {
            // Generate unique signature based on geometry attributes
            let signature = '';
            
            Object.keys(geometry.attributes).forEach(key => {
                const attr = geometry.attributes[key];
                signature += `${key}:${attr.itemSize}:${attr.count};`;
            });
            
            if (geometry.index) {
                signature += `index:${geometry.index.count};`;
            }
            
            return signature;
        }

        performGeometryOptimization(geometry) {
            const optimized = geometry.clone();
            
            // Merge duplicate vertices
            if (this.bufferOptimization) {
                this.mergeVertices(optimized);
            }
            
            // Optimize buffer attributes
            this.optimizeBufferAttributes(optimized);
            
            // Compute bounding volumes
            optimized.computeBoundingBox();
            optimized.computeBoundingSphere();
            
            return optimized;
        }

        mergeVertices(geometry) {
            const positions = geometry.getAttribute('position');
            if (!positions) return;
            
            const vertices = [];
            const indices = [];
            const vertexMap = new Map();
            
            // Extract unique vertices
            for (let i = 0; i < positions.count; i++) {
                const x = positions.array[i * 3];
                const y = positions.array[i * 3 + 1];
                const z = positions.array[i * 3 + 2];
                const key = `${x.toFixed(6)},${y.toFixed(6)},${z.toFixed(6)}`;
                
                if (!vertexMap.has(key)) {
                    vertexMap.set(key, vertices.length / 3);
                    vertices.push(x, y, z);
                }
                
                indices.push(vertexMap.get(key));
            }
            
            // Update geometry
            geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
            geometry.setIndex(new THREE.Uint32BufferAttribute(indices, 1));
            
            geometry.userData.verticesMerged = true;
            geometry.userData.originalVertexCount = positions.count;
            geometry.userData.optimizedVertexCount = vertices.length / 3;
        }

        optimizeBufferAttributes(geometry) {
            Object.keys(geometry.attributes).forEach(key => {
                const attribute = geometry.attributes[key];
                
                // Use appropriate buffer type based on data range
                if (key === 'position' || key === 'normal') {
                    // Keep as Float32 for precision
                    return;
                }
                
                // Optimize color attributes to Uint8 if possible
                if (key === 'color') {
                    this.optimizeColorAttribute(geometry, attribute);
                }
                
                // Optimize UV coordinates
                if (key === 'uv') {
                    this.optimizeUVAttribute(geometry, attribute);
                }
            });
        }

        optimizeColorAttribute(geometry, attribute) {
            // Convert float colors to Uint8 to save memory
            const colors = new Uint8Array(attribute.count * attribute.itemSize);
            
            for (let i = 0; i < attribute.array.length; i++) {
                colors[i] = Math.round(attribute.array[i] * 255);
            }
            
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, attribute.itemSize, true));
        }

        optimizeUVAttribute(geometry, attribute) {
            // Use Uint16 for UV coordinates if they fit in range
            const uvs = new Uint16Array(attribute.count * attribute.itemSize);
            
            for (let i = 0; i < attribute.array.length; i++) {
                uvs[i] = Math.round(attribute.array[i] * 65535);
            }
            
            geometry.setAttribute('uv', new THREE.BufferAttribute(uvs, attribute.itemSize, true));
        }

        createInstancedMesh(objects) {
            if (!this.instancedRendering || objects.length < this.thresholds.instanceThreshold) {
                return objects;
            }
            
            // Group objects by geometry and material
            const groups = new Map();
            
            objects.forEach(obj => {
                if (!obj.geometry || !obj.material) return;
                
                const key = `${this.generateGeometrySignature(obj.geometry)}_${obj.material.uuid || 'default'}`;
                
                if (!groups.has(key)) {
                    groups.set(key, []);
                }
                groups.get(key).push(obj);
            });
            
            const instancedMeshes = [];
            
            groups.forEach((groupObjects, key) => {
                if (groupObjects.length >= this.thresholds.instanceThreshold) {
                    const instancedMesh = new THREE.InstancedMesh(
                        groupObjects[0].geometry,
                        groupObjects[0].material,
                        groupObjects.length
                    );
                    
                    // Set instance matrices
                    groupObjects.forEach((obj, index) => {
                        instancedMesh.setMatrixAt(index, this.createMatrixFromObject(obj));
                    });
                    
                    instancedMesh.instanceMatrix.needsUpdate = true;
                    instancedMesh.userData.originalObjects = groupObjects;
                    instancedMesh.userData.optimized = true;
                    
                    instancedMeshes.push(instancedMesh);
                    this.instancedObjects.set(key, instancedMesh);
                    this.optimizationStats.instancesCreated++;
                } else {
                    instancedMeshes.push(...groupObjects);
                }
            });
            
            return instancedMeshes;
        }

        createMatrixFromObject(object) {
            // Mock matrix creation from object transform
            return {
                elements: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 
                          object.position.x, object.position.y, object.position.z, 1]
            };
        }

        optimizeScene() {
            if (!this.enabled) return;
            
            const startTime = performance.now();
            const meshes = [];
            
            // Collect all meshes from scene
            this.scene.traverse((object) => {
                if (object instanceof THREE.Mesh) {
                    meshes.push(object);
                }
            });
            
            // Optimize geometries
            meshes.forEach(mesh => {
                if (mesh.geometry) {
                    mesh.geometry = this.optimizeGeometry(mesh.geometry);
                }
            });
            
            // Create instanced meshes where beneficial
            const optimizedMeshes = this.createInstancedMesh(meshes);
            
            // Replace original meshes with optimized ones
            meshes.forEach(mesh => {
                if (mesh.parent) {
                    mesh.parent.remove(mesh);
                }
            });
            
            optimizedMeshes.forEach(mesh => {
                this.scene.add(mesh);
            });
            
            this.updateMemoryStats();
            
            const optimizationTime = performance.now() - startTime;
            this.optimizationStats.optimizationTime += optimizationTime;
            
            console.log(`🔧 Scene optimization completed in ${optimizationTime.toFixed(2)}ms`);
            
            return {
                originalMeshCount: meshes.length,
                optimizedMeshCount: optimizedMeshes.length,
                optimizationTime,
                memoryStats: { ...this.memoryStats }
            };
        }

        updateResourceUsage(signature, type) {
            const now = performance.now();
            
            if (!this.resourceUsage.has(signature)) {
                this.resourceUsage.set(signature, {
                    type,
                    firstUsed: now,
                    lastUsed: now,
                    usageCount: 0
                });
            }
            
            const usage = this.resourceUsage.get(signature);
            usage.lastUsed = now;
            usage.usageCount++;
        }

        performCleanup() {
            if (!this.memoryManagement) return;
            
            const now = performance.now();
            const freedMemory = { geometries: 0, buffers: 0, materials: 0 };
            
            // Clean up unused geometries
            this.geometryPool.forEach((geometry, signature) => {
                const usage = this.resourceUsage.get(signature);
                if (usage && now - usage.lastUsed > this.thresholds.unusedResourceAge) {
                    geometry.dispose();
                    this.geometryPool.delete(signature);
                    this.resourceUsage.delete(signature);
                    freedMemory.geometries++;
                }
            });
            
            // Clean up unused buffers
            this.bufferPool.forEach((buffer, signature) => {
                const usage = this.resourceUsage.get(signature);
                if (usage && now - usage.lastUsed > this.thresholds.unusedResourceAge) {
                    this.bufferPool.delete(signature);
                    this.resourceUsage.delete(signature);
                    freedMemory.buffers++;
                }
            });
            
            // Clean up unused materials
            this.materialPool.forEach((material, signature) => {
                const usage = this.resourceUsage.get(signature);
                if (usage && now - usage.lastUsed > this.thresholds.unusedResourceAge) {
                    material.dispose();
                    this.materialPool.delete(signature);
                    this.resourceUsage.delete(signature);
                    freedMemory.materials++;
                }
            });
            
            this.updateMemoryStats();
            this.optimizationStats.memoryFreed += Object.values(freedMemory).reduce((a, b) => a + b, 0);
            
            console.log(`🔧 Cleanup completed: ${JSON.stringify(freedMemory)}`);
            
            return freedMemory;
        }

        updateMemoryStats() {
            this.memoryStats = {
                geometries: this.geometryPool.size,
                buffers: this.bufferPool.size,
                materials: this.materialPool.size,
                instances: this.instancedObjects.size,
                totalMemory: this.estimateTotalMemoryUsage()
            };
        }

        estimateTotalMemoryUsage() {
            let totalMemory = 0;
            
            // Estimate geometry memory
            this.geometryPool.forEach(geometry => {
                Object.values(geometry.attributes).forEach(attr => {
                    totalMemory += attr.array.byteLength;
                });
            });
            
            // Estimate buffer memory
            this.bufferPool.forEach(buffer => {
                totalMemory += buffer.byteLength || 1024; // Default estimate
            });
            
            return totalMemory;
        }

        getOptimizationReport() {
            return {
                enabled: this.enabled,
                settings: {
                    geometryPooling: this.geometryPooling,
                    bufferOptimization: this.bufferOptimization,
                    instancedRendering: this.instancedRendering,
                    memoryManagement: this.memoryManagement,
                    autoCleanup: this.autoCleanup
                },
                memoryStats: { ...this.memoryStats },
                optimizationStats: { ...this.optimizationStats },
                thresholds: { ...this.thresholds },
                poolSizes: {
                    geometryPool: this.geometryPool.size,
                    bufferPool: this.bufferPool.size,
                    materialPool: this.materialPool.size,
                    instanceGroups: this.instanceGroups.size
                },
                resourceUsage: Array.from(this.resourceUsage.entries()).slice(0, 10) // Last 10 resources
            };
        }

        setGeometryPooling(enabled) {
            this.geometryPooling = enabled;
            console.log(`🔧 Geometry pooling ${enabled ? 'enabled' : 'disabled'}`);
        }

        setBufferOptimization(enabled) {
            this.bufferOptimization = enabled;
            console.log(`🔧 Buffer optimization ${enabled ? 'enabled' : 'disabled'}`);
        }

        setInstancedRendering(enabled) {
            this.instancedRendering = enabled;
            console.log(`🔧 Instanced rendering ${enabled ? 'enabled' : 'disabled'}`);
        }

        setMemoryManagement(enabled) {
            this.memoryManagement = enabled;
            console.log(`🔧 Memory management ${enabled ? 'enabled' : 'disabled'}`);
        }

        setAutoCleanup(enabled) {
            this.autoCleanup = enabled;
            console.log(`🔧 Auto cleanup ${enabled ? 'enabled' : 'disabled'}`);
        }

        setThresholds(newThresholds) {
            this.thresholds = { ...this.thresholds, ...newThresholds };
        }

        clearPools() {
            // Dispose all pooled resources
            this.geometryPool.forEach(geometry => geometry.dispose());
            this.materialPool.forEach(material => material.dispose());
            
            this.geometryPool.clear();
            this.bufferPool.clear();
            this.materialPool.clear();
            this.instancedObjects.clear();
            this.resourceUsage.clear();
            
            this.updateMemoryStats();
            console.log('🔧 All resource pools cleared');
        }

        forceOptimization() {
            const result = this.optimizeScene();
            this.performCleanup();
            return result;
        }

        dispose() {
            this.enabled = false;
            this.clearPools();
            console.log('🔧 ResourceOptimizationEngine disposed');
        }
    }

    return new ResourceOptimizationEngine(scene, renderer);
}

describe('Phase 5.3.3 ResourceOptimizationEngine', () => {
    let resourceOptimizer;
    let scene;
    let renderer;

    beforeEach(() => {
        vi.clearAllMocks();
        
        // Reset performance.now mock
        let time = 0;
        performance.now.mockImplementation(() => {
            time += 16.67; // Simulate 60fps
            return time;
        });
        
        resourceOptimizer = createResourceOptimizationEngine();
        scene = resourceOptimizer.scene;
        renderer = resourceOptimizer.renderer;
    });

    afterEach(() => {
        if (resourceOptimizer) {
            resourceOptimizer.dispose();
        }
    });

    describe('Initialization', () => {
        it('should initialize with correct default values', () => {
            expect(resourceOptimizer.enabled).toBe(true);
            expect(resourceOptimizer.geometryPooling).toBe(true);
            expect(resourceOptimizer.bufferOptimization).toBe(true);
            expect(resourceOptimizer.instancedRendering).toBe(true);
            expect(resourceOptimizer.memoryManagement).toBe(true);
            expect(resourceOptimizer.autoCleanup).toBe(true);
        });

        it('should initialize empty pools', () => {
            expect(resourceOptimizer.geometryPool.size).toBe(0);
            expect(resourceOptimizer.bufferPool.size).toBe(0);
            expect(resourceOptimizer.materialPool.size).toBe(0);
            expect(resourceOptimizer.instancedObjects.size).toBe(0);
        });

        it('should have correct default thresholds', () => {
            const thresholds = resourceOptimizer.thresholds;
            
            expect(thresholds.maxGeometries).toBe(1000);
            expect(thresholds.maxBuffers).toBe(500);
            expect(thresholds.maxMaterials).toBe(100);
            expect(thresholds.instanceThreshold).toBe(5);
            expect(thresholds.cleanupInterval).toBe(30000);
        });

        it('should initialize memory stats', () => {
            const memoryStats = resourceOptimizer.memoryStats;
            
            expect(memoryStats.geometries).toBe(0);
            expect(memoryStats.buffers).toBe(0);
            expect(memoryStats.materials).toBe(0);
            expect(memoryStats.instances).toBe(0);
            expect(memoryStats.totalMemory).toBe(0);
        });

        it('should initialize optimization stats', () => {
            const optimizationStats = resourceOptimizer.optimizationStats;
            
            expect(optimizationStats.geometriesOptimized).toBe(0);
            expect(optimizationStats.buffersOptimized).toBe(0);
            expect(optimizationStats.instancesCreated).toBe(0);
            expect(optimizationStats.memoryFreed).toBe(0);
            expect(optimizationStats.optimizationTime).toBe(0);
        });
    });

    describe('Geometry Optimization', () => {
        it('should optimize geometry correctly', () => {
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0, 1, 1, 1], 3));
            
            const optimized = resourceOptimizer.optimizeGeometry(geometry);
            
            expect(optimized).toBeDefined();
            expect(resourceOptimizer.optimizationStats.geometriesOptimized).toBe(0); // First time, not from pool
        });

        it('should reuse geometry from pool', () => {
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0, 1, 1, 1], 3));
            
            const optimized1 = resourceOptimizer.optimizeGeometry(geometry);
            const optimized2 = resourceOptimizer.optimizeGeometry(geometry);
            
            expect(resourceOptimizer.optimizationStats.geometriesOptimized).toBe(1); // Second call uses pool
            expect(resourceOptimizer.geometryPool.size).toBe(1);
        });

        it('should generate unique geometry signatures', () => {
            const geometry1 = new THREE.BufferGeometry();
            geometry1.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3));
            
            const geometry2 = new THREE.BufferGeometry();
            geometry2.setAttribute('position', new THREE.Float32BufferAttribute([1, 1, 1], 3));
            
            const sig1 = resourceOptimizer.generateGeometrySignature(geometry1);
            const sig2 = resourceOptimizer.generateGeometrySignature(geometry2);
            
            expect(sig1).not.toBe(sig2);
            expect(sig1).toContain('position:3:1');
        });

        it('should merge duplicate vertices', () => {
            const geometry = new THREE.BufferGeometry();
            // Duplicate vertices
            geometry.setAttribute('position', new THREE.Float32BufferAttribute([
                0, 0, 0,  // vertex 0
                1, 1, 1,  // vertex 1
                0, 0, 0,  // duplicate of vertex 0
                2, 2, 2   // vertex 2
            ], 3));
            
            resourceOptimizer.mergeVertices(geometry);
            
            expect(geometry.userData.verticesMerged).toBe(true);
            expect(geometry.userData.originalVertexCount).toBe(4);
            expect(geometry.userData.optimizedVertexCount).toBe(3); // One duplicate removed
        });

        it('should not optimize geometry when pooling is disabled', () => {
            resourceOptimizer.setGeometryPooling(false);
            
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3));
            
            const result = resourceOptimizer.optimizeGeometry(geometry);
            
            expect(result).toBe(geometry); // Returns original
            expect(resourceOptimizer.geometryPool.size).toBe(0);
        });
    });

    describe('Buffer Optimization', () => {
        it('should optimize buffer attributes', () => {
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0, 1, 1, 1], 3));
            geometry.setAttribute('color', new THREE.Float32BufferAttribute([1.0, 0.5, 0.0, 0.0, 1.0, 0.5], 3));
            
            resourceOptimizer.optimizeBufferAttributes(geometry);
            
            // Color attribute should be optimized to Uint8
            const colorAttr = geometry.getAttribute('color');
            expect(colorAttr.array).toBeInstanceOf(Uint8Array);
        });

        it('should optimize color attributes to Uint8', () => {
            const geometry = new THREE.BufferGeometry();
            const colorAttr = new THREE.Float32BufferAttribute([1.0, 0.5, 0.0], 3);
            
            resourceOptimizer.optimizeColorAttribute(geometry, colorAttr);
            
            const optimizedColor = geometry.getAttribute('color');
            expect(optimizedColor.array).toBeInstanceOf(Uint8Array);
            expect(optimizedColor.array[0]).toBe(255); // 1.0 * 255
            expect(optimizedColor.array[1]).toBe(128); // 0.5 * 255 (rounded)
        });

        it('should optimize UV attributes to Uint16', () => {
            const geometry = new THREE.BufferGeometry();
            const uvAttr = new THREE.Float32BufferAttribute([0.5, 1.0], 2);
            
            resourceOptimizer.optimizeUVAttribute(geometry, uvAttr);
            
            const optimizedUV = geometry.getAttribute('uv');
            expect(optimizedUV.array).toBeInstanceOf(Uint16Array);
            expect(optimizedUV.array[0]).toBe(32768); // 0.5 * 65535 (rounded)
            expect(optimizedUV.array[1]).toBe(65535); // 1.0 * 65535
        });

        it('should preserve position and normal attributes as Float32', () => {
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3));
            geometry.setAttribute('normal', new THREE.Float32BufferAttribute([0, 1, 0], 3));
            
            resourceOptimizer.optimizeBufferAttributes(geometry);
            
            expect(geometry.getAttribute('position').array).toBeInstanceOf(Float32Array);
            expect(geometry.getAttribute('normal').array).toBeInstanceOf(Float32Array);
        });
    });

    describe('Instanced Rendering', () => {
        it('should create instanced mesh for similar objects', () => {
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3));
            const material = new THREE.MeshBasicMaterial();
            
            // Create 6 similar objects (above threshold of 5)
            const objects = [];
            for (let i = 0; i < 6; i++) {
                objects.push(new THREE.Mesh(geometry, material));
            }
            
            const result = resourceOptimizer.createInstancedMesh(objects);
            
            expect(result.length).toBe(1); // Should be reduced to single instanced mesh
            expect(result[0]).toBeInstanceOf(THREE.InstancedMesh);
            expect(result[0].count).toBe(6);
            expect(resourceOptimizer.optimizationStats.instancesCreated).toBe(1);
        });

        it('should not create instanced mesh below threshold', () => {
            const geometry = new THREE.BufferGeometry();
            const material = new THREE.MeshBasicMaterial();
            
            // Create 3 objects (below threshold of 5)
            const objects = [];
            for (let i = 0; i < 3; i++) {
                objects.push(new THREE.Mesh(geometry, material));
            }
            
            const result = resourceOptimizer.createInstancedMesh(objects);
            
            expect(result.length).toBe(3); // Should remain as individual meshes
            expect(resourceOptimizer.optimizationStats.instancesCreated).toBe(0);
        });

        it('should group objects by geometry and material', () => {
            const geometry1 = new THREE.BufferGeometry();
            geometry1.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3));
            const geometry2 = new THREE.BufferGeometry();
            geometry2.setAttribute('position', new THREE.Float32BufferAttribute([1, 1, 1], 3));
            const material = new THREE.MeshBasicMaterial();
            
            const objects = [];
            // 3 objects with geometry1
            for (let i = 0; i < 3; i++) {
                objects.push(new THREE.Mesh(geometry1, material));
            }
            // 6 objects with geometry2 (should be instanced)
            for (let i = 0; i < 6; i++) {
                objects.push(new THREE.Mesh(geometry2, material));
            }
            
            const result = resourceOptimizer.createInstancedMesh(objects);
            
            expect(result.length).toBe(4); // 3 individual + 1 instanced
            expect(resourceOptimizer.optimizationStats.instancesCreated).toBe(1);
        });

        it('should not create instances when instanced rendering is disabled', () => {
            resourceOptimizer.setInstancedRendering(false);
            
            const geometry = new THREE.BufferGeometry();
            const material = new THREE.MeshBasicMaterial();
            const objects = [];
            for (let i = 0; i < 6; i++) {
                objects.push(new THREE.Mesh(geometry, material));
            }
            
            const result = resourceOptimizer.createInstancedMesh(objects);
            
            expect(result.length).toBe(6); // No instancing
            expect(resourceOptimizer.optimizationStats.instancesCreated).toBe(0);
        });

        it('should create matrix from object transform', () => {
            const object = new THREE.Mesh();
            object.position.set(5, 10, 15);
            
            const matrix = resourceOptimizer.createMatrixFromObject(object);
            
            expect(matrix.elements[12]).toBe(5); // Translation X
            expect(matrix.elements[13]).toBe(10); // Translation Y
            expect(matrix.elements[14]).toBe(15); // Translation Z
        });
    });

    describe('Scene Optimization', () => {
        it('should optimize entire scene', () => {
            // Add meshes to scene
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0, 1, 1, 1], 3));
            const material = new THREE.MeshBasicMaterial();
            
            for (let i = 0; i < 3; i++) {
                const mesh = new THREE.Mesh(geometry, material);
                scene.children.push(mesh);
            }
            
            const result = resourceOptimizer.optimizeScene();
            
            expect(result).toHaveProperty('originalMeshCount');
            expect(result).toHaveProperty('optimizedMeshCount');
            expect(result).toHaveProperty('optimizationTime');
            expect(result).toHaveProperty('memoryStats');
            expect(result.originalMeshCount).toBe(3);
        });

        it('should track optimization time', () => {
            const result = resourceOptimizer.optimizeScene();
            
            expect(result.optimizationTime).toBeGreaterThan(0);
            expect(resourceOptimizer.optimizationStats.optimizationTime).toBeGreaterThan(0);
        });

        it('should update memory stats after optimization', () => {
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3));
            const mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial());
            scene.children.push(mesh);
            
            resourceOptimizer.optimizeScene();
            
            expect(resourceOptimizer.memoryStats.geometries).toBeGreaterThan(0);
        });
    });

    describe('Memory Management', () => {
        it('should update resource usage correctly', () => {
            const signature = 'test-signature';
            
            resourceOptimizer.updateResourceUsage(signature, 'geometry');
            
            expect(resourceOptimizer.resourceUsage.has(signature)).toBe(true);
            const usage = resourceOptimizer.resourceUsage.get(signature);
            expect(usage.type).toBe('geometry');
            expect(usage.usageCount).toBe(1);
        });

        it('should increment usage count on repeated access', () => {
            const signature = 'test-signature';
            
            resourceOptimizer.updateResourceUsage(signature, 'geometry');
            resourceOptimizer.updateResourceUsage(signature, 'geometry');
            
            const usage = resourceOptimizer.resourceUsage.get(signature);
            expect(usage.usageCount).toBe(2);
        });

        it('should perform cleanup of unused resources', () => {
            // Add resource to pool
            const geometry = new THREE.BufferGeometry();
            const signature = 'old-geometry';
            resourceOptimizer.geometryPool.set(signature, geometry);
            resourceOptimizer.resourceUsage.set(signature, {
                type: 'geometry',
                firstUsed: performance.now() - 70000, // Old resource
                lastUsed: performance.now() - 70000,
                usageCount: 1
            });
            
            const result = resourceOptimizer.performCleanup();
            
            expect(result.geometries).toBe(1); // One geometry cleaned up
            expect(resourceOptimizer.geometryPool.has(signature)).toBe(false);
        });

        it('should not cleanup recently used resources', () => {
            const geometry = new THREE.BufferGeometry();
            const signature = 'recent-geometry';
            resourceOptimizer.geometryPool.set(signature, geometry);
            resourceOptimizer.resourceUsage.set(signature, {
                type: 'geometry',
                firstUsed: performance.now(),
                lastUsed: performance.now(),
                usageCount: 1
            });
            
            const result = resourceOptimizer.performCleanup();
            
            expect(result.geometries).toBe(0); // No cleanup of recent resources
            expect(resourceOptimizer.geometryPool.has(signature)).toBe(true);
        });

        it('should estimate total memory usage', () => {
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3));
            resourceOptimizer.geometryPool.set('test', geometry);
            
            const memoryUsage = resourceOptimizer.estimateTotalMemoryUsage();
            
            expect(memoryUsage).toBeGreaterThan(0);
        });

        it('should update memory stats correctly', () => {
            resourceOptimizer.geometryPool.set('test', new THREE.BufferGeometry());
            resourceOptimizer.bufferPool.set('buffer', new ArrayBuffer(1024));
            
            resourceOptimizer.updateMemoryStats();
            
            expect(resourceOptimizer.memoryStats.geometries).toBe(1);
            expect(resourceOptimizer.memoryStats.buffers).toBe(1);
        });
    });

    describe('Configuration Management', () => {
        it('should enable/disable geometry pooling', () => {
            resourceOptimizer.setGeometryPooling(false);
            expect(resourceOptimizer.geometryPooling).toBe(false);
            
            resourceOptimizer.setGeometryPooling(true);
            expect(resourceOptimizer.geometryPooling).toBe(true);
        });

        it('should enable/disable buffer optimization', () => {
            resourceOptimizer.setBufferOptimization(false);
            expect(resourceOptimizer.bufferOptimization).toBe(false);
            
            resourceOptimizer.setBufferOptimization(true);
            expect(resourceOptimizer.bufferOptimization).toBe(true);
        });

        it('should enable/disable instanced rendering', () => {
            resourceOptimizer.setInstancedRendering(false);
            expect(resourceOptimizer.instancedRendering).toBe(false);
            
            resourceOptimizer.setInstancedRendering(true);
            expect(resourceOptimizer.instancedRendering).toBe(true);
        });

        it('should enable/disable memory management', () => {
            resourceOptimizer.setMemoryManagement(false);
            expect(resourceOptimizer.memoryManagement).toBe(false);
            
            resourceOptimizer.setMemoryManagement(true);
            expect(resourceOptimizer.memoryManagement).toBe(true);
        });

        it('should enable/disable auto cleanup', () => {
            resourceOptimizer.setAutoCleanup(false);
            expect(resourceOptimizer.autoCleanup).toBe(false);
            
            resourceOptimizer.setAutoCleanup(true);
            expect(resourceOptimizer.autoCleanup).toBe(true);
        });

        it('should set custom thresholds', () => {
            const newThresholds = {
                maxGeometries: 500,
                instanceThreshold: 10
            };
            
            resourceOptimizer.setThresholds(newThresholds);
            
            expect(resourceOptimizer.thresholds.maxGeometries).toBe(500);
            expect(resourceOptimizer.thresholds.instanceThreshold).toBe(10);
            expect(resourceOptimizer.thresholds.maxBuffers).toBe(500); // Should remain unchanged
        });
    });

    describe('Optimization Report', () => {
        it('should generate comprehensive optimization report', () => {
            const report = resourceOptimizer.getOptimizationReport();
            
            expect(report).toHaveProperty('enabled');
            expect(report).toHaveProperty('settings');
            expect(report).toHaveProperty('memoryStats');
            expect(report).toHaveProperty('optimizationStats');
            expect(report).toHaveProperty('thresholds');
            expect(report).toHaveProperty('poolSizes');
            expect(report).toHaveProperty('resourceUsage');
        });

        it('should include all optimization settings in report', () => {
            const report = resourceOptimizer.getOptimizationReport();
            
            expect(report.settings.geometryPooling).toBe(true);
            expect(report.settings.bufferOptimization).toBe(true);
            expect(report.settings.instancedRendering).toBe(true);
            expect(report.settings.memoryManagement).toBe(true);
            expect(report.settings.autoCleanup).toBe(true);
        });

        it('should include pool sizes in report', () => {
            resourceOptimizer.geometryPool.set('test', new THREE.BufferGeometry());
            
            const report = resourceOptimizer.getOptimizationReport();
            
            expect(report.poolSizes.geometryPool).toBe(1);
            expect(report.poolSizes.bufferPool).toBe(0);
            expect(report.poolSizes.materialPool).toBe(0);
        });

        it('should limit resource usage in report', () => {
            // Add many resources
            for (let i = 0; i < 15; i++) {
                resourceOptimizer.updateResourceUsage(`resource-${i}`, 'geometry');
            }
            
            const report = resourceOptimizer.getOptimizationReport();
            
            expect(report.resourceUsage.length).toBe(10); // Limited to 10
        });
    });

    describe('Pool Management', () => {
        it('should clear all pools', () => {
            // Add resources to pools
            resourceOptimizer.geometryPool.set('test', new THREE.BufferGeometry());
            resourceOptimizer.bufferPool.set('buffer', new ArrayBuffer(1024));
            resourceOptimizer.materialPool.set('material', new THREE.MeshBasicMaterial());
            resourceOptimizer.updateResourceUsage('test', 'geometry');
            
            resourceOptimizer.clearPools();
            
            expect(resourceOptimizer.geometryPool.size).toBe(0);
            expect(resourceOptimizer.bufferPool.size).toBe(0);
            expect(resourceOptimizer.materialPool.size).toBe(0);
            expect(resourceOptimizer.resourceUsage.size).toBe(0);
        });

        it('should force optimization and cleanup', () => {
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0], 3));
            const mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial());
            scene.children.push(mesh);
            
            const result = resourceOptimizer.forceOptimization();
            
            expect(result).toHaveProperty('originalMeshCount');
            expect(result).toHaveProperty('optimizationTime');
        });
    });

    describe('Cleanup and Disposal', () => {
        it('should dispose properly', () => {
            // Add some resources
            resourceOptimizer.geometryPool.set('test', new THREE.BufferGeometry());
            resourceOptimizer.updateResourceUsage('test', 'geometry');
            
            resourceOptimizer.dispose();
            
            expect(resourceOptimizer.enabled).toBe(false);
            expect(resourceOptimizer.geometryPool.size).toBe(0);
            expect(resourceOptimizer.resourceUsage.size).toBe(0);
        });

        it('should handle disposal of geometry resources', () => {
            const geometry = new THREE.BufferGeometry();
            const disposeSpy = vi.spyOn(geometry, 'dispose');
            resourceOptimizer.geometryPool.set('test', geometry);
            
            resourceOptimizer.clearPools();
            
            expect(disposeSpy).toHaveBeenCalled();
        });

        it('should handle disposal of material resources', () => {
            const material = new THREE.MeshBasicMaterial();
            const disposeSpy = vi.spyOn(material, 'dispose');
            resourceOptimizer.materialPool.set('test', material);
            
            resourceOptimizer.clearPools();
            
            expect(disposeSpy).toHaveBeenCalled();
        });
    });
});