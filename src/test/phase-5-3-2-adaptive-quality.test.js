/**
 * Phase 5.3.2 Adaptive Quality Manager Tests
 * Comprehensive tests for LOD optimization and adaptive quality management
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// Mock global objects and APIs
global.THREE = {
    Spherical: class {
        constructor() { this.theta = 0; this.phi = Math.PI / 2; }
        setFromVector3(vec) { return this; }
    },
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
    },
    Object3D: class {
        constructor() {
            this.children = [];
            this.visible = true;
            this.geometry = null;
            this.material = null;
            this.userData = {};
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
        }
        clone() { return new THREE.Mesh(this.geometry, this.material); }
        traverse(fn) { fn(this); this.children.forEach(c => c.traverse?.(fn) || fn(c)); }
    },
    BufferGeometry: class {
        constructor() {
            this.attributes = {};
            this.index = null;
            this.userData = {};
        }
        setAttribute(name, attr) { this.attributes[name] = attr; }
        getAttribute(name) { return this.attributes[name]; }
        getIndex() { return this.index; }
        setIndex(index) { this.index = index; }
        computeBoundingSphere() { this.boundingSphere = { radius: 1, center: new THREE.Vector3() }; }
        clone() { return new THREE.BufferGeometry(); }
        dispose() {}
    },
    LOD: class {
        constructor() {
            this.levels = [];
            this.children = [];
            this.visible = true;
        }
        addLevel(mesh, distance) { 
            this.levels.push({ object: mesh, distance });
            this.children.push(mesh);
        }
        getObjectForDistance(distance) {
            return this.levels.find(l => distance >= l.distance)?.object || null;
        }
        update(camera) {
            const distance = camera.position.distanceTo(new THREE.Vector3());
            this.children.forEach(child => child.visible = false);
            const activeLevel = this.getObjectForDistance(distance);
            if (activeLevel) activeLevel.visible = true;
        }
        clone() { return new THREE.LOD(); }
    },
    MeshBasicMaterial: class {
        constructor(params = {}) {
            this.color = params.color || '#ffffff';
            this.wireframe = params.wireframe || false;
            this.transparent = params.transparent || false;
            this.opacity = params.opacity || 1.0;
        }
        clone() { return new THREE.MeshBasicMaterial(); }
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

// Create mock camera
function createMockCamera() {
    return {
        position: new THREE.Vector3(10, 10, 10),
        updateMatrixWorld: vi.fn(),
        getWorldDirection: vi.fn(() => new THREE.Vector3(0, 0, -1))
    };
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

// Create AdaptiveQualityManager test class
function createAdaptiveQualityManager() {
    const scene = createMockScene();
    const camera = createMockCamera();
    
    // Mock performance monitor
    const performanceMonitor = {
        fps: 60,
        performanceLevel: 'good',
        memoryUsage: { used: 50, total: 100, limit: 200 },
        onPerformanceChange: null,
        onMemoryPressure: null
    };

    // Simplified AdaptiveQualityManager for testing
    class AdaptiveQualityManager {
        constructor(scene, camera, performanceMonitor) {
            this.scene = scene;
            this.camera = camera;
            this.performanceMonitor = performanceMonitor;
            this.enabled = true;
            
            // Quality levels and thresholds
            this.qualityLevel = 'high';
            this.qualityLevels = ['low', 'medium', 'high', 'ultra'];
            this.qualityThresholds = {
                excellent: 'ultra',
                good: 'high', 
                poor: 'medium',
                critical: 'low'
            };
            
            // LOD (Level of Detail) settings
            this.lodEnabled = true;
            this.lodDistances = {
                high: [0, 20, 50, 100],    // Show full detail up to 20 units
                medium: [0, 15, 35, 70],   // Reduce detail sooner
                low: [0, 10, 25, 50]       // Aggressive detail reduction
            };
            
            // Geometry simplification settings
            this.simplificationEnabled = true;
            this.targetTriangleCounts = {
                ultra: 100000,
                high: 50000,
                medium: 25000,
                low: 10000
            };
            
            // Material quality settings
            this.materialQuality = 'high';
            this.materialSettings = {
                ultra: { textureSize: 2048, shadows: true, reflections: true },
                high: { textureSize: 1024, shadows: true, reflections: false },
                medium: { textureSize: 512, shadows: false, reflections: false },
                low: { textureSize: 256, shadows: false, reflections: false }
            };
            
            // Adaptive settings
            this.adaptiveEnabled = true;
            this.fpsTarget = 60;
            this.fpsThresholds = {
                increase: 55,  // Increase quality if FPS > 55
                decrease: 25   // Decrease quality if FPS < 25
            };
            
            // Quality tracking
            this.qualityHistory = [];
            this.qualityHistoryLimit = 60; // Track last 60 adjustments
            this.lastQualityChange = 0;
            this.qualityChangeCooldown = 2000; // 2 seconds between changes
            
            // Scene analysis cache
            this.sceneAnalysis = {
                triangleCount: 0,
                objectCount: 0,
                textureMemory: 0,
                lastUpdate: 0
            };
            this.analysisInterval = 1000; // Update analysis every second
            
            // LOD objects cache
            this.lodObjects = new Map();
            this.originalObjects = new Map();
            
            this.initializeAdaptiveQuality();
        }

        initializeAdaptiveQuality() {
            // Connect to performance monitor events
            if (this.performanceMonitor) {
                this.performanceMonitor.onPerformanceChange = (level, metrics) => {
                    this.onPerformanceChange(level, metrics);
                };
                
                this.performanceMonitor.onMemoryPressure = (memoryUsage) => {
                    this.onMemoryPressure(memoryUsage);
                };
            }
            
            // Start adaptive quality monitoring
            this.startAdaptiveMonitoring();
            console.log('📊 AdaptiveQualityManager initialized');
        }

        startAdaptiveMonitoring() {
            if (!this.adaptiveEnabled) return;
            
            const monitorLoop = () => {
                if (!this.enabled) return;
                
                this.updateSceneAnalysis();
                this.adaptQuality();
                this.updateLOD();
                
                requestAnimationFrame(monitorLoop);
            };
            
            requestAnimationFrame(monitorLoop);
        }

        updateSceneAnalysis() {
            const now = performance.now();
            if (now - this.sceneAnalysis.lastUpdate < this.analysisInterval) return;
            
            let triangleCount = 0;
            let objectCount = 0;
            let textureMemory = 0;
            
            this.scene.traverse((object) => {
                objectCount++;
                
                if (object.geometry) {
                    const positions = object.geometry.getAttribute('position');
                    if (positions) {
                        triangleCount += positions.count / 3;
                    }
                }
                
                if (object.material) {
                    // Estimate texture memory usage
                    const settings = this.materialSettings[this.materialQuality];
                    textureMemory += (settings.textureSize * settings.textureSize * 4) / (1024 * 1024); // MB
                }
            });
            
            this.sceneAnalysis = {
                triangleCount,
                objectCount,
                textureMemory,
                lastUpdate: now
            };
        }

        adaptQuality() {
            if (!this.adaptiveEnabled || !this.performanceMonitor) return;
            
            const now = performance.now();
            if (now - this.lastQualityChange < this.qualityChangeCooldown) return;
            
            const currentFPS = this.performanceMonitor.fps;
            let targetQuality = this.qualityLevel;
            
            // Determine if quality should change based on FPS
            if (currentFPS < this.fpsThresholds.decrease) {
                targetQuality = this.decreaseQuality(this.qualityLevel);
            } else if (currentFPS > this.fpsThresholds.increase) {
                targetQuality = this.increaseQuality(this.qualityLevel);
            }
            
            // Apply memory pressure considerations
            const memoryUsage = this.performanceMonitor.memoryUsage;
            if (memoryUsage.used / memoryUsage.limit > 0.8) {
                targetQuality = this.decreaseQuality(targetQuality);
            }
            
            if (targetQuality !== this.qualityLevel) {
                this.setQualityLevel(targetQuality);
                this.lastQualityChange = now;
            }
        }

        setQualityLevel(newLevel) {
            if (!this.qualityLevels.includes(newLevel)) return;
            
            const oldLevel = this.qualityLevel;
            this.qualityLevel = newLevel;
            
            // Update material quality
            this.materialQuality = newLevel;
            
            // Update LOD distances
            this.updateLODSettings();
            
            // Apply simplification if needed
            if (this.simplificationEnabled) {
                this.applyGeometrySimplification();
            }
            
            // Update materials
            this.updateMaterialQuality();
            
            // Track quality change
            this.qualityHistory.push({
                timestamp: performance.now(),
                oldLevel,
                newLevel,
                reason: this.getQualityChangeReason()
            });
            
            if (this.qualityHistory.length > this.qualityHistoryLimit) {
                this.qualityHistory.shift();
            }
            
            console.log(`📊 Quality level changed: ${oldLevel} → ${newLevel}`);
            
            // Trigger callback if available
            if (this.onQualityChange) {
                this.onQualityChange(newLevel, oldLevel, this.sceneAnalysis);
            }
        }

        increaseQuality(currentLevel) {
            const currentIndex = this.qualityLevels.indexOf(currentLevel);
            return currentIndex < this.qualityLevels.length - 1 
                ? this.qualityLevels[currentIndex + 1] 
                : currentLevel;
        }

        decreaseQuality(currentLevel) {
            const currentIndex = this.qualityLevels.indexOf(currentLevel);
            return currentIndex > 0 
                ? this.qualityLevels[currentIndex - 1] 
                : currentLevel;
        }

        updateLODSettings() {
            if (!this.lodEnabled) return;
            
            const distances = this.lodDistances[this.qualityLevel] || this.lodDistances.medium;
            
            // Update existing LOD objects
            this.lodObjects.forEach((lodObject, originalObject) => {
                lodObject.levels.forEach((level, index) => {
                    level.distance = distances[index] || distances[distances.length - 1];
                });
            });
        }

        createLODObject(originalObject) {
            if (!this.lodEnabled || this.lodObjects.has(originalObject)) {
                return originalObject;
            }
            
            const lod = new THREE.LOD();
            const distances = this.lodDistances[this.qualityLevel] || this.lodDistances.medium;
            
            // Create multiple detail levels
            distances.forEach((distance, index) => {
                const detailLevel = this.createDetailLevel(originalObject, index);
                lod.addLevel(detailLevel, distance);
            });
            
            this.lodObjects.set(originalObject, lod);
            this.originalObjects.set(lod, originalObject);
            
            return lod;
        }

        createDetailLevel(originalObject, levelIndex) {
            const detailMesh = originalObject.clone();
            
            // Apply geometry simplification based on level
            if (detailMesh.geometry && levelIndex > 0) {
                const simplificationFactor = Math.pow(0.5, levelIndex);
                this.simplifyGeometry(detailMesh.geometry, simplificationFactor);
            }
            
            // Apply material quality based on level
            if (detailMesh.material) {
                this.simplifyMaterial(detailMesh.material, levelIndex);
            }
            
            return detailMesh;
        }

        simplifyGeometry(geometry, factor) {
            // Mock geometry simplification
            if (geometry.attributes.position) {
                const positions = geometry.attributes.position;
                const simplifiedCount = Math.floor(positions.count * factor);
                
                // Update geometry metadata for tracking
                geometry.userData.originalCount = positions.count;
                geometry.userData.simplifiedCount = simplifiedCount;
                geometry.userData.simplificationFactor = factor;
            }
        }

        simplifyMaterial(material, levelIndex) {
            // Mock material simplification
            if (levelIndex === 0) return; // Full quality
            
            if (levelIndex === 1) {
                material.wireframe = false;
            } else if (levelIndex === 2) {
                material.wireframe = true;
                material.transparent = true;
                material.opacity = 0.8;
            } else {
                material.wireframe = true;
                material.transparent = true;
                material.opacity = 0.5;
            }
        }

        applyGeometrySimplification() {
            const targetTriangleCount = this.targetTriangleCounts[this.qualityLevel];
            if (!targetTriangleCount) return;
            
            let currentTriangleCount = this.sceneAnalysis.triangleCount;
            if (currentTriangleCount <= targetTriangleCount) return;
            
            const simplificationFactor = targetTriangleCount / currentTriangleCount;
            
            this.scene.traverse((object) => {
                if (object.geometry && !object.userData.simplified) {
                    this.simplifyGeometry(object.geometry, simplificationFactor);
                    object.userData.simplified = true;
                    object.userData.originalQuality = this.qualityLevel;
                }
            });
        }

        updateMaterialQuality() {
            const settings = this.materialSettings[this.materialQuality];
            if (!settings) return;
            
            this.scene.traverse((object) => {
                if (object.material) {
                    // Apply material quality settings
                    object.material.userData.qualityLevel = this.materialQuality;
                    object.material.userData.textureSize = settings.textureSize;
                    object.material.userData.shadows = settings.shadows;
                    object.material.userData.reflections = settings.reflections;
                }
            });
        }

        updateLOD() {
            if (!this.lodEnabled) return;
            
            this.lodObjects.forEach((lodObject) => {
                lodObject.update(this.camera);
            });
        }

        onPerformanceChange(level, metrics) {
            const targetQuality = this.qualityThresholds[level];
            if (targetQuality && targetQuality !== this.qualityLevel) {
                this.setQualityLevel(targetQuality);
            }
        }

        onMemoryPressure(memoryUsage) {
            const usageRatio = memoryUsage.used / memoryUsage.limit;
            
            if (usageRatio > 0.9) {
                // Critical memory pressure - force lowest quality
                this.setQualityLevel('low');
            } else if (usageRatio > 0.7) {
                // High memory pressure - decrease quality
                const newQuality = this.decreaseQuality(this.qualityLevel);
                if (newQuality !== this.qualityLevel) {
                    this.setQualityLevel(newQuality);
                }
            }
        }

        getQualityChangeReason() {
            const fps = this.performanceMonitor?.fps || 60;
            const memoryUsage = this.performanceMonitor?.memoryUsage;
            const memoryRatio = memoryUsage ? memoryUsage.used / memoryUsage.limit : 0;
            
            if (memoryRatio > 0.9) return 'critical_memory_pressure';
            if (memoryRatio > 0.7) return 'high_memory_usage';
            if (fps < this.fpsThresholds.decrease) return 'low_fps';
            if (fps > this.fpsThresholds.increase) return 'high_fps';
            return 'performance_optimization';
        }

        getQualityReport() {
            return {
                currentLevel: this.qualityLevel,
                materialQuality: this.materialQuality,
                lodEnabled: this.lodEnabled,
                simplificationEnabled: this.simplificationEnabled,
                sceneAnalysis: { ...this.sceneAnalysis },
                qualityHistory: this.qualityHistory.slice(-10),
                thresholds: { ...this.fpsThresholds },
                targetTriangleCount: this.targetTriangleCounts[this.qualityLevel],
                lodObjectCount: this.lodObjects.size,
                materialSettings: this.materialSettings[this.materialQuality]
            };
        }

        setQualityThresholds(newThresholds) {
            this.fpsThresholds = { ...this.fpsThresholds, ...newThresholds };
        }

        setLODEnabled(enabled) {
            this.lodEnabled = enabled;
            console.log(`📊 LOD system ${enabled ? 'enabled' : 'disabled'}`);
        }

        setSimplificationEnabled(enabled) {
            this.simplificationEnabled = enabled;
            console.log(`📊 Geometry simplification ${enabled ? 'enabled' : 'disabled'}`);
        }

        setAdaptiveEnabled(enabled) {
            this.adaptiveEnabled = enabled;
            console.log(`📊 Adaptive quality ${enabled ? 'enabled' : 'disabled'}`);
        }

        resetQuality() {
            this.qualityLevel = 'high';
            this.materialQuality = 'high';
            this.qualityHistory = [];
            
            // Reset all simplified objects
            this.scene.traverse((object) => {
                if (object.userData.simplified) {
                    delete object.userData.simplified;
                    delete object.userData.originalQuality;
                }
            });
            
            console.log('📊 Quality settings reset to defaults');
        }

        dispose() {
            this.enabled = false;
            this.adaptiveEnabled = false;
            
            // Clean up LOD objects
            this.lodObjects.clear();
            this.originalObjects.clear();
            
            // Disconnect performance monitor
            if (this.performanceMonitor) {
                this.performanceMonitor.onPerformanceChange = null;
                this.performanceMonitor.onMemoryPressure = null;
            }
            
            console.log('📊 AdaptiveQualityManager disposed');
        }
    }

    return new AdaptiveQualityManager(scene, camera, performanceMonitor);
}

describe('Phase 5.3.2 AdaptiveQualityManager', () => {
    let adaptiveQualityManager;
    let scene;
    let camera;
    let performanceMonitor;

    beforeEach(() => {
        vi.clearAllMocks();
        
        // Reset performance.now mock
        let time = 0;
        performance.now.mockImplementation(() => {
            time += 16.67; // Simulate 60fps
            return time;
        });
        
        adaptiveQualityManager = createAdaptiveQualityManager();
        scene = adaptiveQualityManager.scene;
        camera = adaptiveQualityManager.camera;
        performanceMonitor = adaptiveQualityManager.performanceMonitor;
    });

    afterEach(() => {
        if (adaptiveQualityManager) {
            adaptiveQualityManager.dispose();
        }
    });

    describe('Initialization', () => {
        it('should initialize with correct default values', () => {
            expect(adaptiveQualityManager.enabled).toBe(true);
            expect(adaptiveQualityManager.qualityLevel).toBe('high');
            expect(adaptiveQualityManager.materialQuality).toBe('high');
            expect(adaptiveQualityManager.lodEnabled).toBe(true);
            expect(adaptiveQualityManager.simplificationEnabled).toBe(true);
            expect(adaptiveQualityManager.adaptiveEnabled).toBe(true);
        });

        it('should have correct quality levels', () => {
            expect(adaptiveQualityManager.qualityLevels).toEqual(['low', 'medium', 'high', 'ultra']);
        });

        it('should have correct quality thresholds', () => {
            const thresholds = adaptiveQualityManager.qualityThresholds;
            
            expect(thresholds.excellent).toBe('ultra');
            expect(thresholds.good).toBe('high');
            expect(thresholds.poor).toBe('medium');
            expect(thresholds.critical).toBe('low');
        });

        it('should have LOD distance settings', () => {
            const lodDistances = adaptiveQualityManager.lodDistances;
            
            expect(lodDistances).toHaveProperty('high');
            expect(lodDistances).toHaveProperty('medium');
            expect(lodDistances).toHaveProperty('low');
            expect(Array.isArray(lodDistances.high)).toBe(true);
        });

        it('should have target triangle counts for each quality level', () => {
            const triangleCounts = adaptiveQualityManager.targetTriangleCounts;
            
            expect(triangleCounts.ultra).toBe(100000);
            expect(triangleCounts.high).toBe(50000);
            expect(triangleCounts.medium).toBe(25000);
            expect(triangleCounts.low).toBe(10000);
        });
    });

    describe('Quality Level Management', () => {
        it('should set quality level correctly', () => {
            adaptiveQualityManager.setQualityLevel('medium');
            
            expect(adaptiveQualityManager.qualityLevel).toBe('medium');
            expect(adaptiveQualityManager.materialQuality).toBe('medium');
        });

        it('should track quality changes in history', () => {
            adaptiveQualityManager.setQualityLevel('low');
            
            expect(adaptiveQualityManager.qualityHistory.length).toBe(1);
            expect(adaptiveQualityManager.qualityHistory[0].oldLevel).toBe('high');
            expect(adaptiveQualityManager.qualityHistory[0].newLevel).toBe('low');
        });

        it('should increase quality level correctly', () => {
            const newLevel = adaptiveQualityManager.increaseQuality('medium');
            expect(newLevel).toBe('high');
            
            const maxLevel = adaptiveQualityManager.increaseQuality('ultra');
            expect(maxLevel).toBe('ultra'); // Should not exceed max
        });

        it('should decrease quality level correctly', () => {
            const newLevel = adaptiveQualityManager.decreaseQuality('medium');
            expect(newLevel).toBe('low');
            
            const minLevel = adaptiveQualityManager.decreaseQuality('low');
            expect(minLevel).toBe('low'); // Should not go below min
        });

        it('should ignore invalid quality levels', () => {
            const originalLevel = adaptiveQualityManager.qualityLevel;
            adaptiveQualityManager.setQualityLevel('invalid');
            
            expect(adaptiveQualityManager.qualityLevel).toBe(originalLevel);
        });

        it('should trigger quality change callback', () => {
            const qualityChangeCallback = vi.fn();
            adaptiveQualityManager.onQualityChange = qualityChangeCallback;
            
            adaptiveQualityManager.setQualityLevel('low');
            
            expect(qualityChangeCallback).toHaveBeenCalledWith(
                'low',
                'high',
                expect.any(Object)
            );
        });

        it('should limit quality history size', () => {
            // Add more changes than the limit
            for (let i = 0; i < 65; i++) {
                adaptiveQualityManager.setQualityLevel(i % 2 === 0 ? 'low' : 'high');
            }
            
            expect(adaptiveQualityManager.qualityHistory.length).toBe(60); // qualityHistoryLimit
        });
    });

    describe('Scene Analysis', () => {
        it('should analyze scene correctly', () => {
            // Add mock objects to scene
            const mockObject = new THREE.Mesh(
                new THREE.BufferGeometry(),
                new THREE.MeshBasicMaterial()
            );
            mockObject.geometry.setAttribute('position', { count: 300 }); // 100 triangles
            scene.children.push(mockObject);
            
            // Force analysis update by setting lastUpdate to 0
            adaptiveQualityManager.sceneAnalysis.lastUpdate = 0;
            adaptiveQualityManager.updateSceneAnalysis();
            
            expect(adaptiveQualityManager.sceneAnalysis.objectCount).toBeGreaterThan(0);
            expect(adaptiveQualityManager.sceneAnalysis.triangleCount).toBeGreaterThan(0);
        });

        it('should respect analysis interval', () => {
            const initialUpdateTime = adaptiveQualityManager.sceneAnalysis.lastUpdate;
            
            // Call update immediately - should be skipped due to interval
            adaptiveQualityManager.updateSceneAnalysis();
            
            expect(adaptiveQualityManager.sceneAnalysis.lastUpdate).toBe(initialUpdateTime);
        });

        it('should calculate texture memory usage', () => {
            const mockObject = new THREE.Mesh(
                new THREE.BufferGeometry(),
                new THREE.MeshBasicMaterial()
            );
            scene.children.push(mockObject);
            
            adaptiveQualityManager.updateSceneAnalysis();
            
            expect(adaptiveQualityManager.sceneAnalysis.textureMemory).toBeGreaterThan(0);
        });
    });

    describe('Adaptive Quality System', () => {
        it('should adapt quality based on FPS', () => {
            // Simulate low FPS
            performanceMonitor.fps = 20;
            
            adaptiveQualityManager.adaptQuality();
            
            expect(adaptiveQualityManager.qualityLevel).toBe('medium'); // Decreased from high
        });

        it('should increase quality when FPS is high', () => {
            // Start with low quality
            adaptiveQualityManager.setQualityLevel('low');
            adaptiveQualityManager.lastQualityChange = 0; // Reset cooldown
            
            // Simulate high FPS
            performanceMonitor.fps = 60;
            
            adaptiveQualityManager.adaptQuality();
            
            expect(adaptiveQualityManager.qualityLevel).toBe('medium'); // Increased from low
        });

        it('should respect quality change cooldown', () => {
            const originalLevel = adaptiveQualityManager.qualityLevel;
            adaptiveQualityManager.lastQualityChange = performance.now();
            
            // Simulate low FPS - should be ignored due to cooldown
            performanceMonitor.fps = 10;
            
            adaptiveQualityManager.adaptQuality();
            
            expect(adaptiveQualityManager.qualityLevel).toBe(originalLevel);
        });

        it('should adapt quality based on memory pressure', () => {
            adaptiveQualityManager.lastQualityChange = 0; // Reset cooldown
            
            // Simulate high memory usage
            performanceMonitor.memoryUsage = {
                used: 170,
                total: 190,
                limit: 200
            };
            
            adaptiveQualityManager.adaptQuality();
            
            expect(adaptiveQualityManager.qualityLevel).toBe('medium'); // Decreased due to memory pressure
        });

        it('should not adapt when adaptive mode is disabled', () => {
            adaptiveQualityManager.setAdaptiveEnabled(false);
            const originalLevel = adaptiveQualityManager.qualityLevel;
            
            performanceMonitor.fps = 10; // Very low FPS
            
            adaptiveQualityManager.adaptQuality();
            
            expect(adaptiveQualityManager.qualityLevel).toBe(originalLevel);
        });
    });

    describe('LOD (Level of Detail) System', () => {
        it('should create LOD object correctly', () => {
            const originalMesh = new THREE.Mesh(
                new THREE.BufferGeometry(),
                new THREE.MeshBasicMaterial()
            );
            
            const lodObject = adaptiveQualityManager.createLODObject(originalMesh);
            
            expect(lodObject).toBeInstanceOf(THREE.LOD);
            expect(adaptiveQualityManager.lodObjects.has(originalMesh)).toBe(true);
            expect(adaptiveQualityManager.originalObjects.has(lodObject)).toBe(true);
        });

        it('should not create duplicate LOD objects', () => {
            const originalMesh = new THREE.Mesh(
                new THREE.BufferGeometry(),
                new THREE.MeshBasicMaterial()
            );
            
            const lodObject1 = adaptiveQualityManager.createLODObject(originalMesh);
            const lodObject2 = adaptiveQualityManager.createLODObject(originalMesh);
            
            expect(lodObject1).toBe(originalMesh); // Returns original on second call
            expect(lodObject2).toBe(originalMesh);
        });

        it('should update LOD settings when quality changes', () => {
            const originalMesh = new THREE.Mesh(
                new THREE.BufferGeometry(),
                new THREE.MeshBasicMaterial()
            );
            const lodObject = adaptiveQualityManager.createLODObject(originalMesh);
            
            adaptiveQualityManager.setQualityLevel('low');
            
            // LOD distances should be updated
            const lowDistances = adaptiveQualityManager.lodDistances.low;
            expect(lodObject.levels[0].distance).toBe(lowDistances[0]);
        });

        it('should update LOD objects during rendering', () => {
            const originalMesh = new THREE.Mesh(
                new THREE.BufferGeometry(),
                new THREE.MeshBasicMaterial()
            );
            const lodObject = adaptiveQualityManager.createLODObject(originalMesh);
            const updateSpy = vi.spyOn(lodObject, 'update');
            
            adaptiveQualityManager.updateLOD();
            
            expect(updateSpy).toHaveBeenCalledWith(camera);
        });

        it('should enable/disable LOD system', () => {
            adaptiveQualityManager.setLODEnabled(false);
            expect(adaptiveQualityManager.lodEnabled).toBe(false);
            
            adaptiveQualityManager.setLODEnabled(true);
            expect(adaptiveQualityManager.lodEnabled).toBe(true);
        });

        it('should return original object when LOD is disabled', () => {
            adaptiveQualityManager.setLODEnabled(false);
            
            const originalMesh = new THREE.Mesh(
                new THREE.BufferGeometry(),
                new THREE.MeshBasicMaterial()
            );
            
            const result = adaptiveQualityManager.createLODObject(originalMesh);
            
            expect(result).toBe(originalMesh);
        });
    });

    describe('Geometry Simplification', () => {
        it('should simplify geometry with correct factor', () => {
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', { count: 300 });
            
            adaptiveQualityManager.simplifyGeometry(geometry, 0.5);
            
            expect(geometry.userData.originalCount).toBe(300);
            expect(geometry.userData.simplifiedCount).toBe(150);
            expect(geometry.userData.simplificationFactor).toBe(0.5);
        });

        it('should apply geometry simplification to scene', () => {
            const mockObject = new THREE.Mesh(
                new THREE.BufferGeometry(),
                new THREE.MeshBasicMaterial()
            );
            mockObject.geometry.setAttribute('position', { count: 300 });
            scene.children.push(mockObject);
            
            adaptiveQualityManager.sceneAnalysis.triangleCount = 200000; // High triangle count
            adaptiveQualityManager.applyGeometrySimplification();
            
            expect(mockObject.userData.simplified).toBe(true);
            expect(mockObject.userData.originalQuality).toBe('high');
        });

        it('should skip simplification when triangle count is below target', () => {
            const mockObject = new THREE.Mesh(
                new THREE.BufferGeometry(),
                new THREE.MeshBasicMaterial()
            );
            scene.children.push(mockObject);
            
            adaptiveQualityManager.sceneAnalysis.triangleCount = 1000; // Low triangle count
            adaptiveQualityManager.applyGeometrySimplification();
            
            expect(mockObject.userData.simplified).toBeUndefined();
        });

        it('should enable/disable simplification system', () => {
            adaptiveQualityManager.setSimplificationEnabled(false);
            expect(adaptiveQualityManager.simplificationEnabled).toBe(false);
            
            adaptiveQualityManager.setSimplificationEnabled(true);
            expect(adaptiveQualityManager.simplificationEnabled).toBe(true);
        });
    });

    describe('Material Quality Management', () => {
        it('should update material quality correctly', () => {
            const mockObject = new THREE.Mesh(
                new THREE.BufferGeometry(),
                new THREE.MeshBasicMaterial()
            );
            scene.children.push(mockObject);
            
            adaptiveQualityManager.setQualityLevel('low');
            
            const material = mockObject.material;
            expect(material.userData.qualityLevel).toBe('low');
            expect(material.userData.textureSize).toBe(256);
            expect(material.userData.shadows).toBe(false);
        });

        it('should simplify material for different detail levels', () => {
            const material = new THREE.MeshBasicMaterial();
            
            adaptiveQualityManager.simplifyMaterial(material, 2);
            
            expect(material.wireframe).toBe(true);
            expect(material.transparent).toBe(true);
            expect(material.opacity).toBe(0.8);
        });

        it('should not simplify material for level 0', () => {
            const material = new THREE.MeshBasicMaterial();
            const originalWireframe = material.wireframe;
            
            adaptiveQualityManager.simplifyMaterial(material, 0);
            
            expect(material.wireframe).toBe(originalWireframe);
        });
    });

    describe('Performance Integration', () => {
        it('should respond to performance change events', () => {
            adaptiveQualityManager.onPerformanceChange('critical', {
                fps: 15,
                frameTime: 67,
                memory: { used: 80, total: 100, limit: 200 }
            });
            
            expect(adaptiveQualityManager.qualityLevel).toBe('low');
        });

        it('should respond to memory pressure events', () => {
            adaptiveQualityManager.onMemoryPressure({
                used: 190,
                total: 195,
                limit: 200
            });
            
            expect(adaptiveQualityManager.qualityLevel).toBe('low');
        });

        it('should handle high memory pressure', () => {
            adaptiveQualityManager.setQualityLevel('ultra');
            
            adaptiveQualityManager.onMemoryPressure({
                used: 150,
                total: 180,
                limit: 200 // 75% usage
            });
            
            expect(adaptiveQualityManager.qualityLevel).toBe('high'); // Decreased from ultra
        });
    });

    describe('Quality Change Reasons', () => {
        it('should identify critical memory pressure reason', () => {
            performanceMonitor.memoryUsage = {
                used: 190,
                total: 195,
                limit: 200
            };
            
            const reason = adaptiveQualityManager.getQualityChangeReason();
            expect(reason).toBe('critical_memory_pressure');
        });

        it('should identify high memory usage reason', () => {
            performanceMonitor.memoryUsage = {
                used: 150,
                total: 180,
                limit: 200
            };
            
            const reason = adaptiveQualityManager.getQualityChangeReason();
            expect(reason).toBe('high_memory_usage');
        });

        it('should identify low FPS reason', () => {
            performanceMonitor.fps = 20;
            performanceMonitor.memoryUsage = {
                used: 50,
                total: 100,
                limit: 200
            };
            
            const reason = adaptiveQualityManager.getQualityChangeReason();
            expect(reason).toBe('low_fps');
        });

        it('should identify high FPS reason', () => {
            performanceMonitor.fps = 65;
            performanceMonitor.memoryUsage = {
                used: 50,
                total: 100,
                limit: 200
            };
            
            const reason = adaptiveQualityManager.getQualityChangeReason();
            expect(reason).toBe('high_fps');
        });
    });

    describe('Quality Report', () => {
        it('should generate comprehensive quality report', () => {
            const report = adaptiveQualityManager.getQualityReport();
            
            expect(report).toHaveProperty('currentLevel');
            expect(report).toHaveProperty('materialQuality');
            expect(report).toHaveProperty('lodEnabled');
            expect(report).toHaveProperty('simplificationEnabled');
            expect(report).toHaveProperty('sceneAnalysis');
            expect(report).toHaveProperty('qualityHistory');
            expect(report).toHaveProperty('thresholds');
            expect(report).toHaveProperty('targetTriangleCount');
            expect(report).toHaveProperty('lodObjectCount');
            expect(report).toHaveProperty('materialSettings');
        });

        it('should include recent quality history in report', () => {
            // Add some quality changes
            adaptiveQualityManager.setQualityLevel('low');
            adaptiveQualityManager.setQualityLevel('medium');
            
            const report = adaptiveQualityManager.getQualityReport();
            
            expect(report.qualityHistory.length).toBe(2);
            expect(report.qualityHistory[0].newLevel).toBe('low');
            expect(report.qualityHistory[1].newLevel).toBe('medium');
        });

        it('should limit quality history in report to last 10 entries', () => {
            // Add many quality changes
            for (let i = 0; i < 15; i++) {
                adaptiveQualityManager.setQualityLevel(i % 2 === 0 ? 'low' : 'high');
            }
            
            const report = adaptiveQualityManager.getQualityReport();
            
            expect(report.qualityHistory.length).toBe(10);
        });
    });

    describe('Configuration Management', () => {
        it('should set quality thresholds correctly', () => {
            const newThresholds = {
                increase: 50,
                decrease: 20
            };
            
            adaptiveQualityManager.setQualityThresholds(newThresholds);
            
            expect(adaptiveQualityManager.fpsThresholds.increase).toBe(50);
            expect(adaptiveQualityManager.fpsThresholds.decrease).toBe(20);
        });

        it('should preserve existing thresholds when setting partial updates', () => {
            const originalThresholds = { ...adaptiveQualityManager.fpsThresholds };
            
            adaptiveQualityManager.setQualityThresholds({
                increase: 50
            });
            
            expect(adaptiveQualityManager.fpsThresholds.increase).toBe(50);
            expect(adaptiveQualityManager.fpsThresholds.decrease).toBe(originalThresholds.decrease);
        });

        it('should enable/disable adaptive quality system', () => {
            adaptiveQualityManager.setAdaptiveEnabled(false);
            expect(adaptiveQualityManager.adaptiveEnabled).toBe(false);
            
            adaptiveQualityManager.setAdaptiveEnabled(true);
            expect(adaptiveQualityManager.adaptiveEnabled).toBe(true);
        });
    });

    describe('Reset and Cleanup', () => {
        it('should reset quality to defaults', () => {
            // Change quality and add history
            adaptiveQualityManager.setQualityLevel('low');
            
            adaptiveQualityManager.resetQuality();
            
            expect(adaptiveQualityManager.qualityLevel).toBe('high');
            expect(adaptiveQualityManager.materialQuality).toBe('high');
            expect(adaptiveQualityManager.qualityHistory).toEqual([]);
        });

        it('should clean up simplified objects on reset', () => {
            const mockObject = new THREE.Mesh(
                new THREE.BufferGeometry(),
                new THREE.MeshBasicMaterial()
            );
            mockObject.userData.simplified = true;
            scene.children.push(mockObject);
            
            adaptiveQualityManager.resetQuality();
            
            expect(mockObject.userData.simplified).toBeUndefined();
        });

        it('should dispose properly', () => {
            const originalMesh = new THREE.Mesh(
                new THREE.BufferGeometry(),
                new THREE.MeshBasicMaterial()
            );
            adaptiveQualityManager.createLODObject(originalMesh);
            
            adaptiveQualityManager.dispose();
            
            expect(adaptiveQualityManager.enabled).toBe(false);
            expect(adaptiveQualityManager.adaptiveEnabled).toBe(false);
            expect(adaptiveQualityManager.lodObjects.size).toBe(0);
            expect(adaptiveQualityManager.originalObjects.size).toBe(0);
        });

        it('should disconnect performance monitor on disposal', () => {
            adaptiveQualityManager.dispose();
            
            expect(performanceMonitor.onPerformanceChange).toBe(null);
            expect(performanceMonitor.onMemoryPressure).toBe(null);
        });
    });
});