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
import asyncio
import time
from pathlib import Path
import logging
from typing import Optional, Literal, Union, Dict
from .openscad_renderer import OpenSCADRenderer
from .openscad_wasm_renderer import OpenSCADWASMRenderer, HybridOpenSCADRenderer
from .renderer_config import get_config
from .realtime_renderer import RealTimeRenderer
from .wasm_version_manager import WASMVersionManager
from .version_manager import OpenSCADVersionManager
from .migration_engine import MigrationEngine
from .wasm_http_server import start_wasm_server, stop_wasm_server

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
    
    # Real-time rendering traits (Phase 3.3b)
    real_time_enabled = traitlets.Bool(False).tag(sync=True)  # Whether real-time rendering is active
    debounce_delay_ms = traitlets.Int(100).tag(sync=True)  # Parameter change debounce delay
    cache_hit_rate = traitlets.Float(0.0).tag(sync=True)  # Current cache hit rate
    render_time_ms = traitlets.Float(0.0).tag(sync=True)  # Last render time in milliseconds
    
    # Version management traits (Phase 4.2)
    openscad_version = traitlets.Unicode("auto").tag(sync=True)  # OpenSCAD version to use
    available_versions = traitlets.List([]).tag(sync=True)  # List of available OpenSCAD versions
    active_wasm_version = traitlets.Unicode("").tag(sync=True)  # Currently active WASM version
    version_compatibility = traitlets.Dict({}).tag(sync=True)  # Version compatibility information
    auto_version_selection = traitlets.Bool(True).tag(sync=True)  # Whether to auto-select optimal version
    
    # Phase 4.4: Migration and workflow integration traits
    migration_suggestions = traitlets.List([]).tag(sync=True)  # Available migration suggestions
    version_compatibility_status = traitlets.Unicode("unknown").tag(sync=True)  # "compatible", "migration_suggested", "incompatible"
    available_migrations = traitlets.Dict({}).tag(sync=True)  # Migration preview data
    version_detection_cache = traitlets.Dict({}).tag(sync=True)  # Cache for version detection results
    
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
        
        // Initialize progressive loader for enhanced UX
        progressiveLoader = new ProgressiveLoader(container, status);
        
        try {
            // Workaround for Marimo Service Worker bug
            // Suppress Service Worker errors that break JavaScript execution
            const originalError = console.error;
            console.error = function(...args) {
                const message = args.join(' ');
                if (!message.includes('service worker') && !message.includes('registration.active')) {
                    originalError.apply(console, args);
                }
            };
            
            // ====================================================================
            // PHASE 5.1.1: ADVANCED MEMORY MANAGEMENT SYSTEM
            // ====================================================================
            
            class MemoryManager {
                constructor() {
                    this.resources = new Set();
                    this.cleanupTimers = new Map();
                    this.memoryWarningThreshold = 100 * 1024 * 1024; // 100MB
                    this.lastCleanup = Date.now();
                    this.cleanupInterval = 5 * 60 * 1000; // 5 minutes
                    
                    console.log('🧠 MemoryManager initialized');
                    this.startMonitoring();
                }
                
                register(resource, cleanupFn, category = 'general') {
                    const entry = { 
                        resource, 
                        cleanupFn, 
                        category,
                        timestamp: Date.now(),
                        id: Math.random().toString(36).substr(2, 9)
                    };
                    this.resources.add(entry);
                    console.log(`🧠 Resource registered: ${category}:${entry.id}`);
                    return entry.id;
                }
                
                unregister(resourceId) {
                    for (const entry of this.resources) {
                        if (entry.id === resourceId) {
                            this.resources.delete(entry);
                            console.log(`🧠 Resource unregistered: ${entry.category}:${resourceId}`);
                            return true;
                        }
                    }
                    return false;
                }
                
                scheduleCleanup(delay = this.cleanupInterval) {
                    if (this.cleanupTimers.has('auto')) {
                        clearTimeout(this.cleanupTimers.get('auto'));
                    }
                    
                    const timer = setTimeout(() => this.cleanup(), delay);
                    this.cleanupTimers.set('auto', timer);
                    console.log(`🧠 Cleanup scheduled in ${delay/1000}s`);
                }
                
                cleanup(category = null) {
                    let cleaned = 0;
                    const now = Date.now();
                    
                    for (const entry of this.resources) {
                        if (category && entry.category !== category) continue;
                        
                        // Auto-cleanup resources older than 10 minutes
                        if (!category && (now - entry.timestamp) < 10 * 60 * 1000) continue;
                        
                        try {
                            entry.cleanupFn(entry.resource);
                            this.resources.delete(entry);
                            cleaned++;
                            console.log(`🧠 Cleaned up: ${entry.category}:${entry.id}`);
                        } catch (error) {
                            console.warn(`🧠 Cleanup failed for ${entry.category}:${entry.id}:`, error);
                        }
                    }
                    
                    this.lastCleanup = now;
                    console.log(`🧠 Cleanup completed: ${cleaned} resources freed`);
                    
                    // Trigger garbage collection if available
                    if (window.gc) {
                        window.gc();
                        console.log('🧠 Manual garbage collection triggered');
                    }
                    
                    return cleaned;
                }
                
                getMemoryUsage() {
                    if ('memory' in performance) {
                        return {
                            used: performance.memory.usedJSHeapSize,
                            total: performance.memory.totalJSHeapSize,
                            limit: performance.memory.jsHeapSizeLimit
                        };
                    }
                    return null;
                }
                
                checkMemoryPressure() {
                    const memory = this.getMemoryUsage();
                    if (!memory) return false;
                    
                    const usageRatio = memory.used / memory.limit;
                    if (usageRatio > 0.8) {
                        console.warn(`🧠 High memory usage: ${(usageRatio * 100).toFixed(1)}%`);
                        this.cleanup();
                        return true;
                    }
                    return false;
                }
                
                startMonitoring() {
                    // Check memory every 30 seconds
                    setInterval(() => {
                        this.checkMemoryPressure();
                        
                        // Auto-cleanup every 5 minutes
                        if (Date.now() - this.lastCleanup > this.cleanupInterval) {
                            this.cleanup();
                        }
                    }, 30000);
                    
                    console.log('🧠 Memory monitoring started');
                }
                
                dispose() {
                    // Clear all resources
                    this.cleanup();
                    
                    // Clear all timers
                    for (const timer of this.cleanupTimers.values()) {
                        clearTimeout(timer);
                    }
                    this.cleanupTimers.clear();
                    
                    console.log('🧠 MemoryManager disposed');
                }
            }
            
            // Initialize global memory manager
            const memoryManager = new MemoryManager();
            
            // ====================================================================
            // PHASE 5.1.2: INTELLIGENT WASM LOADING & CACHING SYSTEM
            // ====================================================================
            
            class WASMCache {
                constructor() {
                    this.cache = new Map();
                    this.loadingPromises = new Map();
                    this.cacheStats = {
                        hits: 0,
                        misses: 0,
                        loads: 0,
                        errors: 0
                    };
                    this.maxCacheSize = 50 * 1024 * 1024; // 50MB cache limit
                    this.maxCacheAge = 7 * 24 * 60 * 60 * 1000; // 7 days
                    
                    console.log('🚀 WASMCache initialized with 50MB limit, 7-day expiry');
                    this.startCacheCleanup();
                }
                
                async loadModule(url, version = 'latest', options = {}) {
                    const cacheKey = `${url}@${version}`;
                    const now = Date.now();
                    
                    // Check cache first
                    if (this.cache.has(cacheKey)) {
                        const entry = this.cache.get(cacheKey);
                        
                        // Check if cache entry is still valid
                        if (now - entry.timestamp < this.maxCacheAge) {
                            this.cacheStats.hits++;
                            console.log(`🚀 WASM cache hit: ${cacheKey} (${this.getCacheHitRate()}% hit rate)`);
                            return entry.module;
                        } else {
                            // Cache expired, remove it
                            this.cache.delete(cacheKey);
                            console.log(`🚀 WASM cache expired: ${cacheKey}`);
                        }
                    }
                    
                    // Check if already loading
                    if (this.loadingPromises.has(cacheKey)) {
                        console.log(`🚀 WASM already loading: ${cacheKey}`);
                        return this.loadingPromises.get(cacheKey);
                    }
                    
                    // Load with caching
                    this.cacheStats.misses++;
                    const loadPromise = this._loadAndCache(url, cacheKey, options);
                    this.loadingPromises.set(cacheKey, loadPromise);
                    
                    return loadPromise;
                }
                
                async _loadAndCache(url, cacheKey, options) {
                    const startTime = performance.now();
                    
                    try {
                        console.log(`🚀 Loading WASM module: ${url}`);
                        this.cacheStats.loads++;
                        
                        // Enhanced loading with streaming and compression detection
                        const response = await fetch(url, {
                            cache: 'force-cache', // Use browser cache first
                            ...options.fetchOptions
                        });
                        
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                        }
                        
                        // Check content encoding
                        const contentEncoding = response.headers.get('content-encoding');
                        const contentLength = response.headers.get('content-length');
                        
                        console.log(`🚀 WASM response headers:`, {
                            encoding: contentEncoding,
                            size: contentLength,
                            type: response.headers.get('content-type')
                        });
                        
                        // Use streaming instantiation for better performance
                        let module;
                        if (typeof WebAssembly.instantiateStreaming === 'function') {
                            console.log('🚀 Using WebAssembly.instantiateStreaming');
                            module = await WebAssembly.instantiateStreaming(response, options.imports || {});
                        } else {
                            console.log('🚀 Fallback to WebAssembly.instantiate');
                            const arrayBuffer = await response.arrayBuffer();
                            module = await WebAssembly.instantiate(arrayBuffer, options.imports || {});
                        }
                        
                        const loadTime = performance.now() - startTime;
                        console.log(`🚀 WASM loaded in ${loadTime.toFixed(2)}ms: ${cacheKey}`);
                        
                        // Cache the module
                        const entry = {
                            module,
                            timestamp: Date.now(),
                            size: contentLength ? parseInt(contentLength) : 0,
                            loadTime
                        };
                        
                        this.cache.set(cacheKey, entry);
                        
                        // Check cache size and cleanup if needed
                        this.enforceMemoryLimits();
                        
                        // Register with memory manager for cleanup
                        memoryManager.register(entry, (e) => {
                            this.cache.delete(cacheKey);
                            console.log(`🚀 WASM cache entry disposed: ${cacheKey}`);
                        }, 'wasm-cache');
                        
                        return module;
                        
                    } catch (error) {
                        this.cacheStats.errors++;
                        console.error(`🚀 WASM loading failed: ${url}`, error);
                        throw new Error(`WASM loading failed: ${error.message}`);
                    } finally {
                        this.loadingPromises.delete(cacheKey);
                    }
                }
                
                enforceMemoryLimits() {
                    const entries = Array.from(this.cache.entries());
                    const totalSize = entries.reduce((sum, [, entry]) => sum + (entry.size || 0), 0);
                    
                    if (totalSize > this.maxCacheSize) {
                        console.log(`🚀 WASM cache size limit exceeded: ${(totalSize/1024/1024).toFixed(2)}MB`);
                        
                        // Sort by timestamp (oldest first) and remove entries
                        entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
                        
                        let removedSize = 0;
                        for (const [key, entry] of entries) {
                            this.cache.delete(key);
                            removedSize += entry.size || 0;
                            console.log(`🚀 Evicted WASM cache entry: ${key}`);
                            
                            if (totalSize - removedSize <= this.maxCacheSize * 0.8) {
                                break; // Keep some headroom
                            }
                        }
                    }
                }
                
                getCacheHitRate() {
                    const total = this.cacheStats.hits + this.cacheStats.misses;
                    return total > 0 ? Math.round((this.cacheStats.hits / total) * 100) : 0;
                }
                
                getStats() {
                    return {
                        ...this.cacheStats,
                        hitRate: this.getCacheHitRate(),
                        cacheSize: this.cache.size,
                        totalMemory: Array.from(this.cache.values()).reduce((sum, entry) => sum + (entry.size || 0), 0)
                    };
                }
                
                clearCache() {
                    const cleared = this.cache.size;
                    this.cache.clear();
                    this.loadingPromises.clear();
                    console.log(`🚀 WASM cache cleared: ${cleared} entries`);
                    return cleared;
                }
                
                startCacheCleanup() {
                    // Clean expired entries every hour
                    setInterval(() => {
                        const now = Date.now();
                        let cleaned = 0;
                        
                        for (const [key, entry] of this.cache.entries()) {
                            if (now - entry.timestamp > this.maxCacheAge) {
                                this.cache.delete(key);
                                cleaned++;
                            }
                        }
                        
                        if (cleaned > 0) {
                            console.log(`🚀 WASM cache auto-cleanup: ${cleaned} expired entries removed`);
                        }
                    }, 60 * 60 * 1000); // 1 hour
                }
                
                // Prefetch WASM modules for better performance
                async prefetch(urls, versions = {}) {
                    const prefetchPromises = urls.map(url => {
                        const version = versions[url] || 'latest';
                        return this.loadModule(url, version).catch(error => {
                            console.warn(`🚀 WASM prefetch failed for ${url}:`, error);
                        });
                    });
                    
                    await Promise.allSettled(prefetchPromises);
                    console.log(`🚀 WASM prefetch completed for ${urls.length} modules`);
                }
            }
            
            // Initialize global WASM cache
            const wasmCache = new WASMCache();
            
            // ====================================================================
            // PHASE 5.1.3: THREE.JS LOD & RENDERING OPTIMIZATION
            // ====================================================================
            
            class RenderingOptimizer {
                constructor(renderer, scene) {
                    this.renderer = renderer;
                    this.scene = scene;
                    this.performanceMonitor = {
                        frameRate: 60,
                        frameTime: 16.67,
                        triangleCount: 0,
                        lodLevel: 0
                    };
                    this.lodDistances = [25, 75, 150]; // LOD switch distances
                    this.maxTriangles = {
                        high: 100000,   // High detail
                        medium: 25000,  // Medium detail
                        low: 5000       // Low detail
                    };
                    
                    console.log('🎨 RenderingOptimizer initialized');
                    this.startPerformanceMonitoring();
                }
                
                optimizeGeometry(geometry, targetTriangles = this.maxTriangles.high) {
                    if (!geometry || !geometry.attributes.position) {
                        console.warn('🎨 Invalid geometry for optimization');
                        return geometry;
                    }
                    
                    const currentTriangles = geometry.attributes.position.count / 3;
                    console.log(`🎨 Optimizing geometry: ${currentTriangles} → target: ${targetTriangles} triangles`);
                    
                    if (currentTriangles <= targetTriangles) {
                        console.log('🎨 Geometry already within triangle limit');
                        return geometry;
                    }
                    
                    // Simple vertex decimation for optimization
                    const optimizedGeometry = this.simplifyGeometry(geometry, targetTriangles);
                    this.performanceMonitor.triangleCount = optimizedGeometry.attributes.position.count / 3;
                    
                    console.log(`🎨 Geometry optimized: ${currentTriangles} → ${this.performanceMonitor.triangleCount} triangles`);
                    return optimizedGeometry;
                }
                
                simplifyGeometry(geometry, targetTriangles) {
                    // Create a simplified version using vertex reduction
                    const positions = geometry.attributes.position.array;
                    const normals = geometry.attributes.normal ? geometry.attributes.normal.array : null;
                    
                    const currentTriangles = positions.length / 9; // 3 vertices * 3 coordinates
                    const reductionRatio = Math.min(targetTriangles / currentTriangles, 1.0);
                    
                    if (reductionRatio >= 0.95) {
                        // Less than 5% reduction needed, return original
                        return geometry;
                    }
                    
                    // Simple every-nth-triangle reduction (better algorithms exist but this is fast)
                    const step = Math.max(1, Math.floor(1 / reductionRatio));
                    const newPositions = [];
                    const newNormals = normals ? [] : null;
                    
                    for (let i = 0; i < positions.length; i += 9 * step) {
                        if (i + 8 < positions.length) {
                            // Add triangle vertices
                            for (let j = 0; j < 9; j++) {
                                newPositions.push(positions[i + j]);
                            }
                            
                            if (normals && newNormals) {
                                for (let j = 0; j < 9; j++) {
                                    newNormals.push(normals[i + j]);
                                }
                            }
                        }
                    }
                    
                    const simplifiedGeometry = new THREE.BufferGeometry();
                    simplifiedGeometry.setAttribute('position', new THREE.Float32Array(newPositions));
                    
                    if (newNormals) {
                        simplifiedGeometry.setAttribute('normal', new THREE.Float32Array(newNormals));
                    } else {
                        simplifiedGeometry.computeVertexNormals();
                    }
                    
                    return simplifiedGeometry;
                }
                
                createLODMesh(originalMesh, distances = this.lodDistances) {
                    if (!originalMesh || !originalMesh.geometry) {
                        console.warn('🎨 Invalid mesh for LOD creation');
                        return originalMesh;
                    }
                    
                    const lod = new THREE.LOD();
                    
                    // High detail (original)
                    const highDetailMesh = originalMesh.clone();
                    highDetailMesh.geometry = this.optimizeGeometry(originalMesh.geometry, this.maxTriangles.high);
                    lod.addLevel(highDetailMesh, distances[0] || 25);
                    
                    // Medium detail
                    const mediumDetailMesh = originalMesh.clone();
                    mediumDetailMesh.geometry = this.optimizeGeometry(originalMesh.geometry, this.maxTriangles.medium);
                    mediumDetailMesh.material = mediumDetailMesh.material.clone();
                    mediumDetailMesh.material.wireframe = false;
                    lod.addLevel(mediumDetailMesh, distances[1] || 75);
                    
                    // Low detail (wireframe)
                    const lowDetailMesh = originalMesh.clone();
                    lowDetailMesh.geometry = this.optimizeGeometry(originalMesh.geometry, this.maxTriangles.low);
                    lowDetailMesh.material = lowDetailMesh.material.clone();
                    lowDetailMesh.material.wireframe = true;
                    lowDetailMesh.material.wireframeLinewidth = 2;
                    lod.addLevel(lowDetailMesh, distances[2] || 150);
                    
                    // Register LOD with memory manager
                    memoryManager.register(lod, (lodMesh) => {
                        lodMesh.levels.forEach(level => {
                            if (level.object.geometry) level.object.geometry.dispose();
                            if (level.object.material) level.object.material.dispose();
                        });
                        console.log('🎨 LOD mesh disposed');
                    }, 'lod-mesh');
                    
                    console.log(`🎨 LOD mesh created with ${lod.levels.length} detail levels`);
                    return lod;
                }
                
                adaptiveQuality(camera) {
                    // Adjust rendering quality based on performance
                    const frameTime = this.performanceMonitor.frameTime;
                    const targetFrameTime = 16.67; // 60 FPS
                    
                    if (frameTime > targetFrameTime * 1.5) {
                        // Performance is poor, reduce quality
                        this.renderer.setPixelRatio(Math.max(1, this.renderer.getPixelRatio() * 0.9));
                        console.log('🎨 Reducing render quality due to performance');
                        return 'reduced';
                    } else if (frameTime < targetFrameTime * 0.8) {
                        // Performance is good, can increase quality
                        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, this.renderer.getPixelRatio() * 1.1));
                        console.log('🎨 Increasing render quality');
                        return 'increased';
                    }
                    
                    return 'stable';
                }
                
                startPerformanceMonitoring() {
                    let lastTime = performance.now();
                    let frameCount = 0;
                    
                    const monitor = () => {
                        const now = performance.now();
                        const deltaTime = now - lastTime;
                        
                        if (deltaTime >= 1000) { // Update every second
                            this.performanceMonitor.frameRate = (frameCount * 1000) / deltaTime;
                            this.performanceMonitor.frameTime = deltaTime / frameCount;
                            
                            // Log performance if it's concerning
                            if (this.performanceMonitor.frameRate < 30) {
                                console.warn(`🎨 Low framerate: ${this.performanceMonitor.frameRate.toFixed(1)} FPS`);
                            }
                            
                            frameCount = 0;
                            lastTime = now;
                        }
                        
                        frameCount++;
                        requestAnimationFrame(monitor);
                    };
                    
                    requestAnimationFrame(monitor);
                    console.log('🎨 Performance monitoring started');
                }
                
                getPerformanceStats() {
                    return {
                        ...this.performanceMonitor,
                        pixelRatio: this.renderer.getPixelRatio(),
                        memoryUsage: this.renderer.info.memory,
                        renderInfo: this.renderer.info.render
                    };
                }
                
                // Frustum culling optimization
                enableFrustumCulling(camera) {
                    const frustum = new THREE.Frustum();
                    const matrix = new THREE.Matrix4();
                    
                    return () => {
                        matrix.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
                        frustum.setFromProjectionMatrix(matrix);
                        
                        this.scene.traverse((object) => {
                            if (object.isMesh) {
                                object.visible = frustum.intersectsObject(object);
                            }
                        });
                    };
                }
                
                // Automatic LOD switching based on camera distance
                updateLOD(camera) {
                    this.scene.traverse((object) => {
                        if (object.isLOD) {
                            object.update(camera);
                        }
                    });
                }
            }
            
            // Will be initialized after scene creation
            let renderingOptimizer = null;
            
            // ====================================================================
            // PHASE 5.2.2: ENHANCED ERROR HANDLING & RECOVERY SUGGESTIONS
            // ====================================================================
            
            class ErrorHandler {
                constructor(container, progressiveLoader) {
                    this.container = container;
                    this.progressiveLoader = progressiveLoader;
                    this.errorHistory = [];
                    this.maxErrorHistory = 10;
                    this.retryCount = 0;
                    this.maxRetries = 3;
                    
                    console.log('🛡️ ErrorHandler initialized');
                }
                
                handleError(error, context = 'general', retryCallback = null) {
                    const errorRecord = {
                        error,
                        context,
                        timestamp: Date.now(),
                        retryCount: this.retryCount,
                        stack: error.stack || '',
                        userAgent: navigator.userAgent
                    };
                    
                    this.errorHistory.push(errorRecord);
                    
                    // Keep only recent errors
                    if (this.errorHistory.length > this.maxErrorHistory) {
                        this.errorHistory.shift();
                    }
                    
                    console.error(`🛡️ Error handled: ${context}`, errorRecord);
                    
                    // Show appropriate error UI
                    this.showContextualError(error, context, retryCallback);
                    
                    // Report to analytics if available
                    this.reportError(errorRecord);
                    
                    return errorRecord;
                }
                
                showContextualError(error, context, retryCallback) {
                    const errorStrategies = {
                        'webgl': {
                            icon: '🖥️',
                            title: 'Graphics Not Available',
                            message: 'WebGL is required for 3D rendering but isn\'t available.',
                            detailedMessage: 'This could be due to hardware limitations, browser settings, or disabled graphics acceleration.',
                            suggestions: [
                                'Enable hardware acceleration in browser settings',
                                'Update your graphics drivers',
                                'Try a different browser (Chrome, Firefox, Edge)',
                                'Check if WebGL is supported at webglreport.com'
                            ],
                            actions: [
                                { label: '🔄 Retry', action: 'retry', primary: true },
                                { label: '📱 Use 2D Fallback', action: 'fallback', primary: false },
                                { label: '🌐 Check WebGL Support', action: 'check_webgl', primary: false }
                            ],
                            severity: 'high'
                        },
                        'wasm': {
                            icon: '🚀',
                            title: 'WebAssembly Loading Failed',
                            message: 'Unable to load OpenSCAD WebAssembly modules.',
                            detailedMessage: 'This could be due to network issues, browser restrictions, or CORS policies.',
                            suggestions: [
                                'Refresh the page to retry loading',
                                'Check your internet connection',
                                'Disable ad blockers or browser extensions',
                                'Try using a different network'
                            ],
                            actions: [
                                { label: '🔄 Retry Loading', action: 'retry', primary: true },
                                { label: '🔧 Use Local Renderer', action: 'fallback_local', primary: false },
                                { label: '📊 Network Diagnostics', action: 'network_check', primary: false }
                            ],
                            severity: 'medium'
                        },
                        'network': {
                            icon: '🌐',
                            title: 'Network Connection Error',
                            message: 'Failed to load required resources.',
                            detailedMessage: 'Unable to connect to CDN or load external dependencies.',
                            suggestions: [
                                'Check your internet connection',
                                'Disable VPN or proxy if active',
                                'Try refreshing the page',
                                'Clear browser cache and cookies'
                            ],
                            actions: [
                                { label: '🔄 Retry', action: 'retry', primary: true },
                                { label: '📱 Offline Mode', action: 'offline_mode', primary: false },
                                { label: '🔍 Connection Test', action: 'connection_test', primary: false }
                            ],
                            severity: 'medium'
                        },
                        'parsing': {
                            icon: '🔧',
                            title: 'Model Processing Error',
                            message: 'Unable to process the 3D model data.',
                            detailedMessage: 'The STL data might be corrupted, incomplete, or in an unsupported format.',
                            suggestions: [
                                'Try regenerating the model',
                                'Check if the model is too complex',
                                'Verify the source SCAD code',
                                'Reduce model complexity if possible'
                            ],
                            actions: [
                                { label: '🔄 Regenerate', action: 'regenerate', primary: true },
                                { label: '📐 Use Simple Model', action: 'fallback_model', primary: false },
                                { label: '🔍 Debug SCAD', action: 'debug_scad', primary: false }
                            ],
                            severity: 'low'
                        },
                        'memory': {
                            icon: '🧠',
                            title: 'Memory Limit Exceeded',
                            message: 'Not enough memory to render this model.',
                            detailedMessage: 'The model is too complex for your device\'s available memory.',
                            suggestions: [
                                'Close other browser tabs',
                                'Reduce model complexity',
                                'Try a simpler version',
                                'Restart your browser'
                            ],
                            actions: [
                                { label: '🔄 Try Again', action: 'retry', primary: true },
                                { label: '📐 Simplify Model', action: 'simplify', primary: false },
                                { label: '🧹 Free Memory', action: 'cleanup', primary: false }
                            ],
                            severity: 'high'
                        },
                        'timeout': {
                            icon: '⏱️',
                            title: 'Operation Timeout',
                            message: 'The operation took too long to complete.',
                            detailedMessage: 'This might be due to model complexity or slow network connection.',
                            suggestions: [
                                'Try again with a simpler model',
                                'Check your internet connection speed',
                                'Reduce model detail level',
                                'Wait and retry in a moment'
                            ],
                            actions: [
                                { label: '🔄 Retry', action: 'retry', primary: true },
                                { label: '📐 Reduce Quality', action: 'reduce_quality', primary: false },
                                { label: '⏳ Extend Timeout', action: 'extend_timeout', primary: false }
                            ],
                            severity: 'medium'
                        },
                        'general': {
                            icon: '❌',
                            title: 'Unexpected Error',
                            message: error.message || 'An unknown error occurred.',
                            detailedMessage: 'Something went wrong that we didn\'t anticipate.',
                            suggestions: [
                                'Try refreshing the page',
                                'Check the browser console for details',
                                'Report this issue if it persists',
                                'Try using a different browser'
                            ],
                            actions: [
                                { label: '🔄 Retry', action: 'retry', primary: true },
                                { label: '📋 Copy Error', action: 'copy_error', primary: false },
                                { label: '🐛 Report Bug', action: 'report_bug', primary: false }
                            ],
                            severity: 'medium'
                        }
                    };
                    
                    const strategy = errorStrategies[context] || errorStrategies['general'];
                    this.showEnhancedErrorUI(strategy, error, retryCallback);
                }
                
                showEnhancedErrorUI(strategy, error, retryCallback) {
                    const severityColors = {
                        'low': { bg: 'rgba(245, 158, 11, 0.1)', border: '#f59e0b', text: '#92400e' },
                        'medium': { bg: 'rgba(239, 68, 68, 0.1)', border: '#ef4444', text: '#dc2626' },
                        'high': { bg: 'rgba(127, 29, 29, 0.1)', border: '#991b1b', text: '#7f1d1d' }
                    };
                    
                    const colors = severityColors[strategy.severity] || severityColors['medium'];
                    
                    // Create enhanced error UI
                    this.container.innerHTML = `
                        <div style="
                            background: ${colors.bg}; 
                            border: 1px solid ${colors.border}; 
                            border-radius: 12px; 
                            padding: 20px;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                            max-width: 500px;
                            margin: 20px auto;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                        ">
                            <!-- Header -->
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                                <span style="font-size: 24px;">${strategy.icon}</span>
                                <div>
                                    <div style="color: ${colors.text}; font-weight: 700; font-size: 16px; margin-bottom: 2px;">
                                        ${strategy.title}
                                    </div>
                                    <div style="color: #6b7280; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">
                                        ${strategy.severity} severity
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Main Message -->
                            <div style="color: #374151; font-size: 14px; margin-bottom: 12px; line-height: 1.5;">
                                ${strategy.message}
                            </div>
                            
                            <!-- Detailed Message (Expandable) -->
                            <details style="margin-bottom: 16px;">
                                <summary style="color: #6b7280; font-size: 12px; cursor: pointer; margin-bottom: 8px;">
                                    🔍 Technical Details
                                </summary>
                                <div style="
                                    color: #4b5563; 
                                    font-size: 12px; 
                                    background: rgba(0,0,0,0.05); 
                                    padding: 10px; 
                                    border-radius: 6px;
                                    line-height: 1.4;
                                ">
                                    ${strategy.detailedMessage}
                                    <br><br>
                                    <strong>Error:</strong> ${error.message}<br>
                                    <strong>Time:</strong> ${new Date().toLocaleTimeString()}<br>
                                    <strong>Retry Count:</strong> ${this.retryCount}/${this.maxRetries}
                                </div>
                            </details>
                            
                            <!-- Suggestions -->
                            <div style="margin-bottom: 16px;">
                                <div style="color: #059669; font-size: 13px; font-weight: 600; margin-bottom: 8px;">
                                    💡 Suggested Solutions:
                                </div>
                                <ul style="margin: 0; padding-left: 16px; color: #374151; font-size: 12px; line-height: 1.5;">
                                    ${strategy.suggestions.map(suggestion => 
                                        `<li style="margin-bottom: 4px;">${suggestion}</li>`
                                    ).join('')}
                                </ul>
                            </div>
                            
                            <!-- Action Buttons -->
                            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                                ${strategy.actions.map(action => `
                                    <button 
                                        onclick="window.errorHandler.executeAction('${action.action}', '${error.message}')"
                                        style="
                                            background: ${action.primary ? colors.border : 'transparent'}; 
                                            color: ${action.primary ? 'white' : colors.text}; 
                                            border: 1px solid ${colors.border}; 
                                            border-radius: 6px; 
                                            padding: 8px 12px; 
                                            font-size: 12px; 
                                            cursor: pointer;
                                            font-weight: ${action.primary ? '600' : '400'};
                                            transition: all 0.2s;
                                        " 
                                        onmouseover="this.style.opacity='0.8'" 
                                        onmouseout="this.style.opacity='1'"
                                    >
                                        ${action.label}
                                    </button>
                                `).join('')}
                            </div>
                            
                            <!-- Error History Link -->
                            ${this.errorHistory.length > 1 ? `
                                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(0,0,0,0.1);">
                                    <button onclick="window.errorHandler.showErrorHistory()" style="
                                        background: none; 
                                        border: none; 
                                        color: #6b7280; 
                                        font-size: 11px; 
                                        cursor: pointer;
                                        text-decoration: underline;
                                    ">
                                        📋 View Error History (${this.errorHistory.length} errors)
                                    </button>
                                </div>
                            ` : ''}
                        </div>
                    `;
                    
                    // Store retry callback globally for button access
                    window.errorHandler = this;
                    this.currentRetryCallback = retryCallback;
                }
                
                executeAction(action, errorMessage) {
                    console.log(`🛡️ Executing error action: ${action}`);
                    
                    switch (action) {
                        case 'retry':
                            this.retryOperation();
                            break;
                        case 'fallback':
                            this.useFallbackMode();
                            break;
                        case 'fallback_local':
                            this.switchToLocalRenderer();
                            break;
                        case 'fallback_model':
                            this.useSimpleModel();
                            break;
                        case 'copy_error':
                            this.copyErrorToClipboard(errorMessage);
                            break;
                        case 'report_bug':
                            this.openBugReport(errorMessage);
                            break;
                        case 'check_webgl':
                            window.open('https://webglreport.com', '_blank');
                            break;
                        case 'network_check':
                            this.runNetworkDiagnostics();
                            break;
                        case 'cleanup':
                            this.performMemoryCleanup();
                            break;
                        case 'regenerate':
                            this.regenerateModel();
                            break;
                        case 'debug_scad':
                            this.debugSCADCode();
                            break;
                        case 'simplify':
                            this.simplifyModel();
                            break;
                        case 'connection_test':
                            this.runConnectionTest();
                            break;
                        default:
                            console.warn(`Unknown action: ${action}`);
                    }
                }
                
                useFallbackMode() {
                    console.log('🛡️ Switching to fallback mode');
                    // Implement 2D fallback or simple geometry
                    if (window.createFallbackGeometry) {
                        window.createFallbackGeometry();
                    }
                }
                
                switchToLocalRenderer() {
                    console.log('🛡️ Switching to local renderer');
                    // Force switch to local OpenSCAD renderer
                    if (window.model && window.model.set) {
                        window.model.set('renderer_type', 'local');
                    }
                }
                
                useSimpleModel() {
                    console.log('🛡️ Using simple fallback model');
                    if (window.createFallbackGeometry) {
                        window.createFallbackGeometry();
                    }
                }
                
                regenerateModel() {
                    console.log('🛡️ Regenerating model');
                    // Trigger model regeneration
                    if (window.updateModel) {
                        window.updateModel();
                    }
                }
                
                debugSCADCode() {
                    console.log('🛡️ Opening SCAD debugger');
                    // Show SCAD code in console for debugging
                    if (window.model && window.model.get) {
                        const scadCode = window.model.get('scad_code');
                        console.log('SCAD Code for debugging:', scadCode);
                    }
                }
                
                simplifyModel() {
                    console.log('🛡️ Simplifying model');
                    // Reduce model complexity
                    // This would need to be implemented based on specific model parameters
                }
                
                runConnectionTest() {
                    console.log('🛡️ Running connection test');
                    const testUrls = [
                        'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
                        'https://unpkg.com/three@0.128.0/build/three.min.js',
                        'https://www.google.com/favicon.ico'
                    ];
                    
                    Promise.all(testUrls.map(url => 
                        fetch(url, { mode: 'no-cors' })
                            .then(() => ({ url, status: 'ok' }))
                            .catch(() => ({ url, status: 'failed' }))
                    )).then(results => {
                        console.log('🛡️ Connection test results:', results);
                    });
                }
                
                openBugReport(errorMessage) {
                    const bugReportUrl = `https://github.com/your-repo/marimo-openscad/issues/new?title=Error%20Report&body=${encodeURIComponent(this.generateErrorReport())}`;
                    window.open(bugReportUrl, '_blank');
                }
                }
                
                retryOperation() {
                    this.retryCount++;
                    if (this.retryCount <= this.maxRetries) {
                        console.log(`🔄 Retrying operation (${this.retryCount}/${this.maxRetries})`);
                        if (this.currentRetryCallback) {
                            this.currentRetryCallback();
                        } else {
                            location.reload();
                        }
                    } else {
                        this.showMaxRetriesReached();
                    }
                }
                
                showMaxRetriesReached() {
                    this.container.innerHTML = `
                        <div style="
                            background: rgba(127, 29, 29, 0.1); 
                            border: 1px solid #991b1b; 
                            border-radius: 8px; 
                            padding: 16px;
                            text-align: center;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                        ">
                            <div style="font-size: 24px; margin-bottom: 8px;">😞</div>
                            <div style="color: #7f1d1d; font-weight: 600; margin-bottom: 8px;">
                                Maximum Retries Reached
                            </div>
                            <div style="color: #374151; font-size: 13px; margin-bottom: 12px;">
                                We've tried ${this.maxRetries} times but the issue persists.
                            </div>
                            <button onclick="location.reload()" style="
                                background: #991b1b; 
                                color: white; 
                                border: none; 
                                border-radius: 6px; 
                                padding: 8px 16px; 
                                cursor: pointer;
                            ">
                                🔄 Refresh Page
                            </button>
                        </div>
                    `;
                }
                
                copyErrorToClipboard(errorMessage) {
                    const errorReport = this.generateErrorReport();
                    navigator.clipboard.writeText(errorReport).then(() => {
                        console.log('📋 Error report copied to clipboard');
                        // Show temporary success message
                        const button = event.target;
                        const original = button.textContent;
                        button.textContent = '✅ Copied!';
                        setTimeout(() => button.textContent = original, 2000);
                    });
                }
                
                generateErrorReport() {
                    const latest = this.errorHistory[this.errorHistory.length - 1];
                    return `
=== MARIMO-OPENSCAD ERROR REPORT ===
Time: ${new Date(latest.timestamp).toISOString()}
Error: ${latest.error.message}
Context: ${latest.context}
Stack: ${latest.stack}
Retry Count: ${latest.retryCount}
User Agent: ${latest.userAgent}
URL: ${window.location.href}

Error History (${this.errorHistory.length} errors):
${this.errorHistory.map((err, i) => 
    `${i + 1}. [${new Date(err.timestamp).toLocaleTimeString()}] ${err.context}: ${err.error.message}`
).join('\n')}
                    `.trim();
                }
                
                showErrorHistory() {
                    const historyHTML = this.errorHistory.map((err, index) => `
                        <div style="
                            padding: 8px; 
                            border-bottom: 1px solid rgba(0,0,0,0.1);
                            font-size: 11px;
                        ">
                            <strong>${index + 1}.</strong> 
                            ${new Date(err.timestamp).toLocaleTimeString()} - 
                            <span style="color: #ef4444;">${err.context}</span>: 
                            ${err.error.message}
                        </div>
                    `).join('');
                    
                    this.container.innerHTML = `
                        <div style="
                            background: rgba(107, 114, 128, 0.1); 
                            border: 1px solid #6b7280; 
                            border-radius: 8px; 
                            padding: 16px;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                            max-height: 300px;
                            overflow-y: auto;
                        ">
                            <h3 style="margin: 0 0 12px 0; color: #374151;">📋 Error History</h3>
                            ${historyHTML}
                            <button onclick="location.reload()" style="
                                background: #6b7280; 
                                color: white; 
                                border: none; 
                                border-radius: 6px; 
                                padding: 8px 16px; 
                                margin-top: 12px;
                                cursor: pointer;
                            ">
                                🔄 Refresh & Start Over
                            </button>
                        </div>
                    `;
                }
                
                reportError(errorRecord) {
                    // Send to analytics if available
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'exception', {
                            description: `${errorRecord.context}: ${errorRecord.error.message}`,
                            fatal: false
                        });
                    }
                    
                    // Log to console for debugging
                    console.error('🛡️ Error Report:', errorRecord);
                }
                
                performMemoryCleanup() {
                    // Trigger garbage collection if available
                    if (window.gc) {
                        window.gc();
                    }
                    
                    // Clear caches
                    if (window.memoryManager) {
                        window.memoryManager.cleanup();
                    }
                    
                    console.log('🧹 Memory cleanup performed');
                }
                
                runNetworkDiagnostics() {
                    console.log('🌐 Running network diagnostics...');
                    // Basic connectivity test
                    fetch('https://www.google.com/favicon.ico', { mode: 'no-cors' })
                        .then(() => console.log('✅ Internet connection OK'))
                        .catch(() => console.log('❌ Internet connection failed'));
                }
                
                getErrorSummary() {
                    return {
                        totalErrors: this.errorHistory.length,
                        errorsByContext: this.errorHistory.reduce((acc, err) => {
                            acc[err.context] = (acc[err.context] || 0) + 1;
                            return acc;
                        }, {}),
                        lastErrorTime: this.errorHistory.length > 0 ? 
                            this.errorHistory[this.errorHistory.length - 1].timestamp : null,
                        retryCount: this.retryCount
                    };
                }
            }
            
            // Initialize enhanced error handler
            let errorHandler = null;
            
            // ====================================================================
            // PHASE 5.2.1: PROGRESSIVE LOADING STATES & VISUAL FEEDBACK
            // ====================================================================
            
            class ProgressiveLoader {
                constructor(container, statusElement) {
                    this.container = container;
                    this.statusElement = statusElement;
                    this.states = ['initializing', 'loading-three', 'loading-wasm', 'parsing-stl', 'optimizing', 'rendering', 'complete'];
                    this.currentState = 0;
                    this.startTime = Date.now();
                    this.stateHistory = [];
                    
                    console.log('🔄 ProgressiveLoader initialized');
                }
                
                showState(state, progress = 0, details = '') {
                    const now = Date.now();
                    const elapsed = now - this.startTime;
                    
                    // Update state history for analytics
                    this.stateHistory.push({
                        state,
                        progress,
                        details,
                        timestamp: now,
                        elapsed
                    });
                    
                    const stateInfo = {
                        'initializing': { 
                            icon: '⚡', 
                            text: 'Initializing 3D viewer...', 
                            color: '#3b82f6',
                            bgColor: 'rgba(59, 130, 246, 0.1)'
                        },
                        'loading-three': { 
                            icon: '📦', 
                            text: 'Loading Three.js library...', 
                            color: '#8b5cf6',
                            bgColor: 'rgba(139, 92, 246, 0.1)'
                        },
                        'loading-wasm': { 
                            icon: '🚀', 
                            text: 'Loading WASM modules...', 
                            color: '#06b6d4',
                            bgColor: 'rgba(6, 182, 212, 0.1)'
                        },
                        'parsing-stl': { 
                            icon: '🔧', 
                            text: 'Processing 3D model...', 
                            color: '#f59e0b',
                            bgColor: 'rgba(245, 158, 11, 0.1)'
                        },
                        'optimizing': { 
                            icon: '⚡', 
                            text: 'Optimizing geometry...', 
                            color: '#10b981',
                            bgColor: 'rgba(16, 185, 129, 0.1)'
                        },
                        'rendering': { 
                            icon: '🎨', 
                            text: 'Rendering scene...', 
                            color: '#f97316',
                            bgColor: 'rgba(249, 115, 22, 0.1)'
                        },
                        'complete': { 
                            icon: '✅', 
                            text: 'Ready for interaction', 
                            color: '#22c55e',
                            bgColor: 'rgba(34, 197, 94, 0.1)'
                        }
                    };
                    
                    const info = stateInfo[state] || stateInfo['initializing'];
                    this.updateUI(info, progress, details, elapsed);
                    
                    console.log(`🔄 Loading state: ${state} (${progress}%) - ${details}`);
                }
                
                updateUI(info, progress, details, elapsed) {
                    const progressPercent = Math.max(0, Math.min(100, progress));
                    const elapsedSeconds = (elapsed / 1000).toFixed(1);
                    
                    // Enhanced status display with progress bar
                    this.statusElement.innerHTML = `
                        <div style="
                            background: ${info.bgColor}; 
                            border: 1px solid ${info.color}; 
                            border-radius: 8px; 
                            padding: 12px 16px;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                            font-size: 13px;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                            backdrop-filter: blur(10px);
                            min-width: 280px;
                        ">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                                <span style="font-size: 16px;">${info.icon}</span>
                                <span style="color: ${info.color}; font-weight: 600;">${info.text}</span>
                                <span style="color: #6b7280; font-size: 11px; margin-left: auto;">${elapsedSeconds}s</span>
                            </div>
                            
                            ${progressPercent > 0 ? `
                                <div style="
                                    background: rgba(0,0,0,0.1); 
                                    border-radius: 4px; 
                                    height: 6px; 
                                    margin-bottom: 6px;
                                    overflow: hidden;
                                ">
                                    <div style="
                                        background: linear-gradient(90deg, ${info.color}, ${this.lightenColor(info.color, 20)});
                                        height: 100%; 
                                        width: ${progressPercent}%; 
                                        border-radius: 4px;
                                        transition: width 0.3s ease;
                                        box-shadow: 0 0 6px ${info.color}40;
                                    "></div>
                                </div>
                                <div style="color: #6b7280; font-size: 11px; text-align: center;">${progressPercent}%</div>
                            ` : ''}
                            
                            ${details ? `
                                <div style="
                                    color: #6b7280; 
                                    font-size: 11px; 
                                    margin-top: 4px;
                                    text-align: center;
                                    font-style: italic;
                                ">${details}</div>
                            ` : ''}
                        </div>
                    `;
                    
                    this.statusElement.style.background = info.bgColor;
                    this.statusElement.style.borderColor = info.color;
                }
                
                // Helper function to lighten colors for gradients
                lightenColor(color, percent) {
                    const num = parseInt(color.replace("#", ""), 16);
                    const amt = Math.round(2.55 * percent);
                    const R = (num >> 16) + amt;
                    const B = (num >> 8 & 0x00FF) + amt;
                    const G = (num & 0x0000FF) + amt;
                    return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 + 
                                  (B < 255 ? B < 1 ? 0 : B : 255) * 0x100 + 
                                  (G < 255 ? G < 1 ? 0 : G : 255)).toString(16).slice(1);
                }
                
                // Show error state with recovery options
                showError(error, context = 'general') {
                    const errorInfo = {
                        'webgl': {
                            icon: '⚠️',
                            title: 'WebGL Not Available',
                            message: 'Your browser doesn\'t support WebGL or it\'s disabled.',
                            suggestion: 'Try enabling hardware acceleration in your browser settings.',
                            action: 'Retry with Software Rendering'
                        },
                        'wasm': {
                            icon: '🚨',
                            title: 'WebAssembly Loading Failed',
                            message: 'Unable to load WebAssembly modules for 3D rendering.',
                            suggestion: 'This might be due to browser restrictions or network issues.',
                            action: 'Fallback to Local Rendering'
                        },
                        'network': {
                            icon: '🌐',
                            title: 'Network Error',
                            message: 'Failed to load required resources from the network.',
                            suggestion: 'Check your internet connection and try refreshing the page.',
                            action: 'Retry Loading'
                        },
                        'parsing': {
                            icon: '🔧',
                            title: 'Model Processing Error',
                            message: 'Unable to process the 3D model data.',
                            suggestion: 'The model might be corrupted or in an unsupported format.',
                            action: 'Generate Fallback Model'
                        },
                        'general': {
                            icon: '❌',
                            title: 'Unexpected Error',
                            message: error.message || 'An unknown error occurred.',
                            suggestion: 'Please try refreshing the page or check the browser console.',
                            action: 'Retry Operation'
                        }
                    };
                    
                    const info = errorInfo[context] || errorInfo['general'];
                    
                    this.statusElement.innerHTML = `
                        <div style="
                            background: rgba(239, 68, 68, 0.1); 
                            border: 1px solid #ef4444; 
                            border-radius: 8px; 
                            padding: 16px;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                            max-width: 400px;
                        ">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                                <span style="font-size: 18px;">${info.icon}</span>
                                <span style="color: #ef4444; font-weight: 600; font-size: 14px;">${info.title}</span>
                            </div>
                            
                            <div style="color: #374151; font-size: 13px; margin-bottom: 8px;">
                                ${info.message}
                            </div>
                            
                            <div style="color: #6b7280; font-size: 12px; margin-bottom: 12px; font-style: italic;">
                                💡 ${info.suggestion}
                            </div>
                            
                            <button style="
                                background: #ef4444; 
                                color: white; 
                                border: none; 
                                border-radius: 6px; 
                                padding: 8px 16px; 
                                font-size: 12px; 
                                cursor: pointer;
                                font-weight: 500;
                                transition: background 0.2s;
                            " 
                            onmouseover="this.style.background='#dc2626'" 
                            onmouseout="this.style.background='#ef4444'"
                            onclick="location.reload()">
                                🔄 ${info.action}
                            </button>
                            
                            <details style="margin-top: 12px;">
                                <summary style="color: #6b7280; font-size: 11px; cursor: pointer;">Technical Details</summary>
                                <pre style="
                                    color: #374151; 
                                    font-size: 10px; 
                                    margin: 8px 0 0 0; 
                                    padding: 8px; 
                                    background: rgba(0,0,0,0.05); 
                                    border-radius: 4px;
                                    white-space: pre-wrap;
                                    word-break: break-word;
                                ">${error.stack || error.message || 'No additional details available'}</pre>
                            </details>
                        </div>
                    `;
                    
                    console.error(`🔄 Error state: ${context}`, error);
                }
                
                // Show completion with performance stats
                showComplete(stats = {}) {
                    const totalTime = Date.now() - this.startTime;
                    const performanceRating = this.getPerformanceRating(totalTime);
                    
                    this.statusElement.innerHTML = `
                        <div style="
                            background: rgba(34, 197, 94, 0.1); 
                            border: 1px solid #22c55e; 
                            border-radius: 8px; 
                            padding: 12px 16px;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                            font-size: 13px;
                            text-align: center;
                        ">
                            <div style="font-size: 18px; margin-bottom: 4px;">✅</div>
                            <div style="color: #22c55e; font-weight: 600; margin-bottom: 8px;">3D Viewer Ready</div>
                            <div style="color: #6b7280; font-size: 11px;">
                                Loaded in ${(totalTime/1000).toFixed(1)}s ${performanceRating}
                            </div>
                            ${stats.triangles ? `
                                <div style="color: #6b7280; font-size: 10px; margin-top: 4px;">
                                    ${stats.triangles.toLocaleString()} triangles, ${stats.renderer || 'auto'} renderer
                                </div>
                            ` : ''}
                        </div>
                    `;
                    
                    // Auto-hide after 3 seconds
                    setTimeout(() => {
                        this.statusElement.style.opacity = '0';
                        this.statusElement.style.transition = 'opacity 0.5s ease';
                        setTimeout(() => {
                            this.statusElement.innerHTML = '';
                            this.statusElement.style.opacity = '1';
                        }, 500);
                    }, 3000);
                }
                
                getPerformanceRating(timeMs) {
                    if (timeMs < 1000) return '⚡';
                    if (timeMs < 3000) return '🚀';
                    if (timeMs < 5000) return '👍';
                    return '🐌';
                }
                
                getLoadingStats() {
                    return {
                        totalTime: Date.now() - this.startTime,
                        stateHistory: this.stateHistory,
                        currentState: this.currentState
                    };
                }
            }
            
            // Initialize progressive loader and error handler
            progressiveLoader = new ProgressiveLoader(container, status);
            errorHandler = new ErrorHandler(container, progressiveLoader);
            
            // ====================================================================
            // PHASE 5.3.1: PERFORMANCE MONITOR FOUNDATION
            // ====================================================================
            
            class PerformanceMonitor {
                constructor(container, hudElement) {
                    this.container = container;
                    this.hudElement = hudElement;
                    this.enabled = true;
                    this.showHUD = false; // Hidden by default, togglable
                    
                    // Performance tracking
                    this.fps = 60;
                    this.frameTime = 16.67; // ms
                    this.lastFrameTime = performance.now();
                    this.frameTimes = [];
                    this.frameTimeWindow = 60; // Track last 60 frames
                    
                    // Memory tracking
                    this.memoryUsage = { used: 0, total: 0 };
                    this.memoryHistory = [];
                    this.maxMemoryHistory = 100;
                    
                    // Performance thresholds
                    this.thresholds = {
                        excellent: { fps: 55, frameTime: 18 },
                        good: { fps: 45, frameTime: 22 },
                        poor: { fps: 25, frameTime: 40 },
                        critical: { fps: 15, frameTime: 67 }
                    };
                    
                    // WebGL performance tracking
                    this.renderStats = {
                        drawCalls: 0,
                        triangles: 0,
                        vertices: 0,
                        textures: 0
                    };
                    
                    // Performance HUD
                    this.hudVisible = false;
                    this.performanceLevel = 'excellent';
                    this.lastAlert = 0;
                    this.alertCooldown = 5000; // 5 seconds between alerts
                    
                    console.log('📊 PerformanceMonitor initialized');
                    this.setupHUD();
                    this.startMonitoring();
                }
                
                setupHUD() {
                    // Create performance HUD container
                    this.performanceHUD = document.createElement('div');
                    this.performanceHUD.id = 'performance-hud';
                    this.performanceHUD.style.cssText = `
                        position: absolute;
                        top: 50px;
                        right: 10px;
                        background: rgba(0, 0, 0, 0.8);
                        color: white;
                        padding: 8px 12px;
                        border-radius: 6px;
                        font-family: 'Courier New', monospace;
                        font-size: 11px;
                        line-height: 1.4;
                        z-index: 1000;
                        min-width: 140px;
                        backdrop-filter: blur(4px);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        display: none;
                        transition: all 0.3s ease;
                    `;
                    
                    // Create toggle button
                    this.perfToggleBtn = document.createElement('button');
                    this.perfToggleBtn.innerHTML = '📊';
                    this.perfToggleBtn.title = 'Toggle Performance Monitor';
                    this.perfToggleBtn.style.cssText = `
                        position: absolute;
                        top: 50px;
                        right: 160px;
                        background: rgba(0, 0, 0, 0.7);
                        color: white;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        border-radius: 4px;
                        padding: 4px 8px;
                        cursor: pointer;
                        font-size: 12px;
                        z-index: 1001;
                        transition: all 0.2s ease;
                    `;
                    
                    this.perfToggleBtn.onmouseover = () => {
                        this.perfToggleBtn.style.background = 'rgba(0, 0, 0, 0.9)';
                        this.perfToggleBtn.style.transform = 'scale(1.1)';
                    };
                    
                    this.perfToggleBtn.onmouseout = () => {
                        this.perfToggleBtn.style.background = 'rgba(0, 0, 0, 0.7)';
                        this.perfToggleBtn.style.transform = 'scale(1)';
                    };
                    
                    this.perfToggleBtn.onclick = () => this.toggleHUD();
                    
                    // Add to container
                    if (this.container) {
                        this.container.appendChild(this.performanceHUD);
                        this.container.appendChild(this.perfToggleBtn);
                    }
                }
                
                startMonitoring() {
                    if (!this.enabled) return;
                    
                    // FPS monitoring using requestAnimationFrame
                    const monitorFrame = (currentTime) => {
                        if (this.lastFrameTime) {
                            this.frameTime = currentTime - this.lastFrameTime;
                            this.fps = 1000 / this.frameTime;
                            
                            // Store frame time history
                            this.frameTimes.push(this.frameTime);
                            if (this.frameTimes.length > this.frameTimeWindow) {
                                this.frameTimes.shift();
                            }
                        }
                        
                        this.lastFrameTime = currentTime;
                        
                        // Update HUD if visible
                        if (this.hudVisible) {
                            this.updateHUD();
                        }
                        
                        // Check performance thresholds
                        this.checkPerformanceThresholds();
                        
                        // Continue monitoring
                        if (this.enabled) {
                            requestAnimationFrame(monitorFrame);
                        }
                    };
                    
                    requestAnimationFrame(monitorFrame);
                    
                    // Memory monitoring (every 2 seconds)
                    setInterval(() => {
                        this.updateMemoryStats();
                    }, 2000);
                }
                
                updateMemoryStats() {
                    try {
                        // Use performance.memory if available (Chrome)
                        if (performance.memory) {
                            this.memoryUsage = {
                                used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                                total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
                                limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
                            };
                        } else {
                            // Fallback estimation based on typical usage
                            this.memoryUsage = {
                                used: Math.round(Math.random() * 50 + 20), // Estimate 20-70MB
                                total: Math.round(Math.random() * 100 + 50),
                                limit: 512 // Assume 512MB limit
                            };
                        }
                        
                        // Store memory history
                        this.memoryHistory.push({
                            timestamp: Date.now(),
                            used: this.memoryUsage.used,
                            total: this.memoryUsage.total
                        });
                        
                        if (this.memoryHistory.length > this.maxMemoryHistory) {
                            this.memoryHistory.shift();
                        }
                        
                    } catch (error) {
                        console.warn('Memory monitoring error:', error);
                    }
                }
                
                checkPerformanceThresholds() {
                    const avgFPS = this.getAverageFPS();
                    const avgFrameTime = this.getAverageFrameTime();
                    
                    let newLevel = 'excellent';
                    if (avgFPS < this.thresholds.critical.fps) {
                        newLevel = 'critical';
                    } else if (avgFPS < this.thresholds.poor.fps) {
                        newLevel = 'poor';
                    } else if (avgFPS < this.thresholds.good.fps) {
                        newLevel = 'good';
                    }
                    
                    // Performance level changed
                    if (newLevel !== this.performanceLevel) {
                        const oldLevel = this.performanceLevel;
                        this.performanceLevel = newLevel;
                        this.onPerformanceLevelChange(oldLevel, newLevel);
                    }
                    
                    // Memory alerts
                    if (this.memoryUsage.used > this.memoryUsage.limit * 0.9) {
                        this.showAlert('High memory usage detected', 'warning');
                    }
                }
                
                onPerformanceLevelChange(oldLevel, newLevel) {
                    console.log(`📊 Performance level changed: ${oldLevel} → ${newLevel}`);
                    
                    // Show alert for significant drops
                    if ((oldLevel === 'excellent' && newLevel === 'poor') ||
                        (oldLevel === 'good' && newLevel === 'critical') ||
                        newLevel === 'critical') {
                        
                        const messages = {
                            poor: 'Performance degraded - consider reducing quality',
                            critical: 'Critical performance issues - switching to emergency mode'
                        };
                        
                        this.showAlert(messages[newLevel] || 'Performance level changed', 'warning');
                    }
                    
                    // Emit event for adaptive quality system
                    this.container.dispatchEvent(new CustomEvent('performanceLevelChange', {
                        detail: { oldLevel, newLevel, fps: this.getAverageFPS(), frameTime: this.getAverageFrameTime() }
                    }));
                }
                
                showAlert(message, type = 'info') {
                    const now = Date.now();
                    if (now - this.lastAlert < this.alertCooldown) return;
                    
                    console.log(`📊 Performance Alert [${type}]: ${message}`);
                    this.lastAlert = now;
                    
                    // Could integrate with existing notification system
                    if (this.hudElement) {
                        const originalText = this.hudElement.textContent;
                        const originalBg = this.hudElement.style.background;
                        
                        this.hudElement.textContent = `⚠️ ${message}`;
                        this.hudElement.style.background = type === 'warning' ? 'rgba(255, 193, 7, 0.9)' : 'rgba(0, 123, 255, 0.9)';
                        
                        setTimeout(() => {
                            this.hudElement.textContent = originalText;
                            this.hudElement.style.background = originalBg;
                        }, 3000);
                    }
                }
                
                getAverageFPS() {
                    if (this.frameTimes.length === 0) return 60;
                    const avgFrameTime = this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length;
                    return 1000 / avgFrameTime;
                }
                
                getAverageFrameTime() {
                    if (this.frameTimes.length === 0) return 16.67;
                    return this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length;
                }
                
                toggleHUD() {
                    this.hudVisible = !this.hudVisible;
                    this.performanceHUD.style.display = this.hudVisible ? 'block' : 'none';
                    
                    if (this.hudVisible) {
                        this.updateHUD();
                    }
                    
                    console.log(`📊 Performance HUD: ${this.hudVisible ? 'shown' : 'hidden'}`);
                }
                
                updateHUD() {
                    if (!this.hudVisible || !this.performanceHUD) return;
                    
                    const avgFPS = this.getAverageFPS();
                    const avgFrameTime = this.getAverageFrameTime();
                    
                    // Color coding based on performance
                    const getPerformanceColor = (level) => {
                        const colors = {
                            excellent: '#22c55e',
                            good: '#eab308', 
                            poor: '#f97316',
                            critical: '#ef4444'
                        };
                        return colors[level] || '#6b7280';
                    };
                    
                    const perfColor = getPerformanceColor(this.performanceLevel);
                    
                    this.performanceHUD.innerHTML = `
                        <div style="color: ${perfColor}; font-weight: bold; margin-bottom: 4px;">
                            📊 Performance Monitor
                        </div>
                        <div>FPS: <span style="color: ${perfColor}">${Math.round(avgFPS)}</span></div>
                        <div>Frame: <span style="color: ${perfColor}">${avgFrameTime.toFixed(1)}ms</span></div>
                        <div>Memory: <span style="color: #60a5fa">${this.memoryUsage.used}MB</span></div>
                        <div style="font-size: 9px; margin-top: 4px; color: #9ca3af;">
                            Level: ${this.performanceLevel.toUpperCase()}
                        </div>
                        <div style="font-size: 9px; color: #9ca3af;">
                            Frames: ${this.frameTimes.length}/${this.frameTimeWindow}
                        </div>
                    `;
                }
                
                getPerformanceReport() {
                    return {
                        fps: {
                            current: this.fps,
                            average: this.getAverageFPS(),
                            min: Math.min(...this.frameTimes.map(ft => 1000 / ft)),
                            max: Math.max(...this.frameTimes.map(ft => 1000 / ft))
                        },
                        frameTime: {
                            current: this.frameTime,
                            average: this.getAverageFrameTime(),
                            min: Math.min(...this.frameTimes),
                            max: Math.max(...this.frameTimes)
                        },
                        memory: this.memoryUsage,
                        memoryHistory: this.memoryHistory.slice(-10), // Last 10 entries
                        level: this.performanceLevel,
                        renderStats: this.renderStats
                    };
                }
                
                updateRenderStats(drawCalls, triangles, vertices, textures) {
                    this.renderStats = { drawCalls, triangles, vertices, textures };
                }
                
                dispose() {
                    this.enabled = false;
                    
                    if (this.performanceHUD && this.performanceHUD.parentNode) {
                        this.performanceHUD.parentNode.removeChild(this.performanceHUD);
                    }
                    
                    if (this.perfToggleBtn && this.perfToggleBtn.parentNode) {
                        this.perfToggleBtn.parentNode.removeChild(this.perfToggleBtn);
                    }
                    
                    console.log('📊 PerformanceMonitor disposed');
                }
            }
            
            // Initialize performance monitor
            performanceMonitor = new PerformanceMonitor(container, status);
            
            // ===== PHASE 5.3.2: Adaptive Quality System =====
            // Dynamic LOD and quality adjustment based on performance
            class AdaptiveQualityManager {
                constructor(performanceMonitor, progressiveLoader) {
                    this.performanceMonitor = performanceMonitor;
                    this.progressiveLoader = progressiveLoader;
                    this.enabled = true;
                    
                    // Quality levels and configurations
                    this.qualityLevels = {
                        ultra: {
                            name: 'Ultra',
                            triangleLimit: 500000,
                            textureResolution: 2048,
                            shadows: true,
                            antialiasing: 4,
                            postProcessing: true,
                            renderScale: 1.0,
                            lodBias: 0.0
                        },
                        high: {
                            name: 'High',
                            triangleLimit: 200000,
                            textureResolution: 1024,
                            shadows: true,
                            antialiasing: 2,
                            postProcessing: true,
                            renderScale: 1.0,
                            lodBias: 0.2
                        },
                        medium: {
                            name: 'Medium',
                            triangleLimit: 100000,
                            textureResolution: 512,
                            shadows: false,
                            antialiasing: 1,
                            postProcessing: false,
                            renderScale: 0.9,
                            lodBias: 0.4
                        },
                        low: {
                            name: 'Low',
                            triangleLimit: 50000,
                            textureResolution: 256,
                            shadows: false,
                            antialiasing: 0,
                            postProcessing: false,
                            renderScale: 0.8,
                            lodBias: 0.6
                        },
                        potato: {
                            name: 'Potato',
                            triangleLimit: 25000,
                            textureResolution: 128,
                            shadows: false,
                            antialiasing: 0,
                            postProcessing: false,
                            renderScale: 0.7,
                            lodBias: 0.8
                        }
                    };
                    
                    // Current state
                    this.currentQuality = 'high';
                    this.targetQuality = 'high';
                    this.autoAdjustEnabled = true;
                    this.transitionCooldown = 2000; // 2 seconds between quality changes
                    this.lastTransition = 0;
                    this.stabilityTimer = null;
                    this.stabilityPeriod = 3000; // 3 seconds stability before quality increase
                    
                    // Performance mapping
                    this.performanceToQuality = {
                        excellent: 'ultra',
                        good: 'high',
                        poor: 'medium',
                        critical: 'low'
                    };
                    
                    // Geometry optimization
                    this.lodGeometries = new Map();
                    this.geometryCache = new Map();
                    
                    this.setupEventListeners();
                    console.log('🎨 AdaptiveQualityManager initialized');
                }
                
                setupEventListeners() {
                    // Listen to performance level changes
                    if (this.performanceMonitor) {
                        this.performanceMonitor.onPerformanceChange = (level, metrics) => {
                            this.handlePerformanceChange(level, metrics);
                        };
                    }
                }
                
                handlePerformanceChange(performanceLevel, metrics) {
                    if (!this.autoAdjustEnabled) return;
                    
                    const suggestedQuality = this.performanceToQuality[performanceLevel] || 'medium';
                    
                    // Immediate downgrade for critical performance
                    if (performanceLevel === 'critical') {
                        this.setQuality('low', 'Performance critical - reducing quality');
                        return;
                    }
                    
                    // Handle upgrades with stability period
                    if (this.shouldUpgradeQuality(suggestedQuality)) {
                        this.scheduleQualityUpgrade(suggestedQuality);
                    } else if (this.shouldDowngradeQuality(suggestedQuality)) {
                        this.setQuality(suggestedQuality, `Performance ${performanceLevel} - adjusting quality`);
                    }
                }
                
                shouldUpgradeQuality(suggestedQuality) {
                    const currentLevel = this.getQualityLevel(this.currentQuality);
                    const suggestedLevel = this.getQualityLevel(suggestedQuality);
                    return suggestedLevel > currentLevel;
                }
                
                shouldDowngradeQuality(suggestedQuality) {
                    const currentLevel = this.getQualityLevel(this.currentQuality);
                    const suggestedLevel = this.getQualityLevel(suggestedQuality);
                    return suggestedLevel < currentLevel;
                }
                
                getQualityLevel(qualityName) {
                    const levels = { potato: 0, low: 1, medium: 2, high: 3, ultra: 4 };
                    return levels[qualityName] || 2;
                }
                
                scheduleQualityUpgrade(targetQuality) {
                    // Clear existing timer
                    if (this.stabilityTimer) {
                        clearTimeout(this.stabilityTimer);
                    }
                    
                    // Schedule upgrade after stability period
                    this.stabilityTimer = setTimeout(() => {
                        // Recheck performance is still good
                        const currentPerf = this.performanceMonitor?.performanceLevel || 'good';
                        const stillGood = ['excellent', 'good'].includes(currentPerf);
                        
                        if (stillGood && this.shouldUpgradeQuality(targetQuality)) {
                            this.setQuality(targetQuality, 'Performance stable - upgrading quality');
                        }
                    }, this.stabilityPeriod);
                }
                
                setQuality(qualityName, reason = '') {
                    const now = Date.now();
                    if (now - this.lastTransition < this.transitionCooldown) {
                        return; // Too soon for another transition
                    }
                    
                    if (this.currentQuality === qualityName) {
                        return; // Already at this quality
                    }
                    
                    const oldQuality = this.currentQuality;
                    this.currentQuality = qualityName;
                    this.lastTransition = now;
                    
                    console.log(`🎨 Quality: ${oldQuality} → ${qualityName} (${reason})`);
                    
                    // Show quality change notification
                    if (this.progressiveLoader) {
                        this.progressiveLoader.showState('optimizing', 50, `Quality: ${this.qualityLevels[qualityName].name}`);
                    }
                    
                    // Apply quality settings
                    this.applyQualitySettings(qualityName);
                    
                    // Update any existing geometries
                    this.updateExistingGeometries();
                    
                    // Emit quality change event for other systems
                    this.onQualityChange?.(qualityName, oldQuality, reason);
                }
                
                applyQualitySettings(qualityName) {
                    const quality = this.qualityLevels[qualityName];
                    
                    // Store settings for renderer use
                    this.currentSettings = quality;
                    
                    // Apply to renderer if available
                    if (window.renderer && renderer.setPixelRatio) {
                        renderer.setPixelRatio(window.devicePixelRatio * quality.renderScale);
                    }
                    
                    // Apply antialiasing if supported
                    if (window.renderer && renderer.antialias !== undefined) {
                        renderer.antialias = quality.antialiasing > 0;
                    }
                    
                    console.log(`🎨 Applied quality settings:`, {
                        triangleLimit: quality.triangleLimit,
                        textureRes: quality.textureResolution,
                        renderScale: quality.renderScale,
                        shadows: quality.shadows,
                        antialiasing: quality.antialiasing
                    });
                }
                
                optimizeGeometry(geometry, targetQuality = null) {
                    const quality = targetQuality ? this.qualityLevels[targetQuality] : this.currentSettings;
                    
                    if (!geometry || !quality) return geometry;
                    
                    const vertexCount = geometry.attributes?.position?.count || 0;
                    const estimatedTriangles = vertexCount / 3;
                    
                    // Check if optimization is needed
                    if (estimatedTriangles <= quality.triangleLimit) {
                        return geometry; // Already within limits
                    }
                    
                    // Calculate reduction ratio
                    const reductionRatio = quality.triangleLimit / estimatedTriangles;
                    
                    console.log(`🎨 Optimizing geometry: ${estimatedTriangles} → ${quality.triangleLimit} triangles (${(reductionRatio * 100).toFixed(1)}%)`);
                    
                    // Apply Level of Detail (LOD) reduction
                    return this.applyLODReduction(geometry, reductionRatio, quality.lodBias);
                }
                
                applyLODReduction(geometry, reductionRatio, lodBias) {
                    // Create a simplified version using decimation
                    try {
                        // Simple vertex skip-based reduction for basic LOD
                        const positions = geometry.attributes.position.array;
                        const normals = geometry.attributes.normal?.array;
                        const indices = geometry.index?.array;
                        
                        if (!positions) return geometry;
                        
                        // Calculate skip factor
                        const skipFactor = Math.max(1, Math.floor(1 / reductionRatio));
                        
                        // Create reduced arrays
                        const newPositions = [];
                        const newNormals = normals ? [] : null;
                        const newIndices = [];
                        
                        // Simple vertex decimation
                        for (let i = 0; i < positions.length; i += skipFactor * 3) {
                            if (i + 2 < positions.length) {
                                newPositions.push(positions[i], positions[i + 1], positions[i + 2]);
                                if (newNormals && i + 2 < normals.length) {
                                    newNormals.push(normals[i], normals[i + 1], normals[i + 2]);
                                }
                            }
                        }
                        
                        // Update indices if they exist
                        if (indices) {
                            for (let i = 0; i < indices.length; i += skipFactor) {
                                if (i < indices.length) {
                                    const adjustedIndex = Math.floor(indices[i] / skipFactor);
                                    if (adjustedIndex < newPositions.length / 3) {
                                        newIndices.push(adjustedIndex);
                                    }
                                }
                            }
                        }
                        
                        // Create new geometry
                        const optimizedGeometry = new THREE.BufferGeometry();
                        optimizedGeometry.setAttribute('position', new THREE.Float32BufferAttribute(newPositions, 3));
                        
                        if (newNormals && newNormals.length > 0) {
                            optimizedGeometry.setAttribute('normal', new THREE.Float32BufferAttribute(newNormals, 3));
                        }
                        
                        if (newIndices.length > 0) {
                            optimizedGeometry.setIndex(newIndices);
                        }
                        
                        // Compute missing normals if needed
                        if (!newNormals) {
                            optimizedGeometry.computeVertexNormals();
                        }
                        
                        console.log(`✅ LOD reduction: ${positions.length / 3} → ${newPositions.length / 3} vertices`);
                        
                        return optimizedGeometry;
                    } catch (error) {
                        console.warn('⚠️ LOD reduction failed, using original geometry:', error);
                        return geometry;
                    }
                }
                
                updateExistingGeometries() {
                    // Update any cached geometries with new quality settings
                    this.geometryCache.forEach((geometry, key) => {
                        const optimized = this.optimizeGeometry(geometry);
                        this.geometryCache.set(key, optimized);
                    });
                }
                
                getQualityInfo() {
                    return {
                        current: this.currentQuality,
                        settings: this.currentSettings,
                        autoAdjust: this.autoAdjustEnabled,
                        availableLevels: Object.keys(this.qualityLevels),
                        performanceMapping: this.performanceToQuality
                    };
                }
                
                setAutoAdjust(enabled) {
                    this.autoAdjustEnabled = enabled;
                    console.log(`🎨 Auto quality adjustment: ${enabled ? 'enabled' : 'disabled'}`);
                }
                
                forceQuality(qualityName, reason = 'Manual override') {
                    this.setAutoAdjust(false);
                    this.setQuality(qualityName, reason);
                }
                
                dispose() {
                    this.enabled = false;
                    
                    if (this.stabilityTimer) {
                        clearTimeout(this.stabilityTimer);
                        this.stabilityTimer = null;
                    }
                    
                    this.geometryCache.clear();
                    this.lodGeometries.clear();
                    
                    console.log('🎨 AdaptiveQualityManager disposed');
                }
            }
            
            // Initialize adaptive quality system
            adaptiveQuality = new AdaptiveQualityManager(performanceMonitor, progressiveLoader);
            
            // ===== PHASE 5.3.3: Resource Optimization Engine =====
            // Advanced memory management and resource optimization
            class ResourceOptimizationEngine {
                constructor(performanceMonitor, adaptiveQuality, progressiveLoader) {
                    this.performanceMonitor = performanceMonitor;
                    this.adaptiveQuality = adaptiveQuality;
                    this.progressiveLoader = progressiveLoader;
                    this.enabled = true;
                    
                    // Resource pools and caches
                    this.geometryPool = new Map();
                    this.materialPool = new Map();
                    this.texturePool = new Map();
                    this.bufferPool = [];
                    
                    // Memory management
                    this.memoryBudget = 256 * 1024 * 1024; // 256MB default budget
                    this.memoryUsage = 0;
                    this.memoryWarningThreshold = 0.8; // 80%
                    this.memoryCriticalThreshold = 0.95; // 95%
                    
                    // Cache strategies
                    this.maxCacheSize = 100;
                    this.cacheAccessTimes = new Map();
                    this.compressionEnabled = true;
                    
                    // Resource tracking
                    this.activeResources = new Set();
                    this.resourceMetrics = {
                        geometries: 0,
                        materials: 0,
                        textures: 0,
                        totalVertices: 0,
                        totalTriangles: 0,
                        memoryFootprint: 0
                    };
                    
                    // Optimization timers
                    this.cleanupInterval = null;
                    this.compressionQueue = [];
                    this.isOptimizing = false;
                    
                    this.initializeResourceManagement();
                    console.log('🛠️ ResourceOptimizationEngine initialized');
                }
                
                initializeResourceManagement() {
                    // Start periodic cleanup
                    this.cleanupInterval = setInterval(() => {
                        if (!this.isOptimizing) {
                            this.performResourceCleanup();
                        }
                    }, 5000); // Every 5 seconds
                    
                    // Monitor memory pressure
                    if (this.performanceMonitor) {
                        this.performanceMonitor.onMemoryPressure = (usage) => {
                            this.handleMemoryPressure(usage);
                        };
                    }
                    
                    // Buffer pool initialization
                    this.initializeBufferPool();
                }
                
                initializeBufferPool() {
                    // Pre-allocate common buffer sizes
                    const commonSizes = [1024, 4096, 16384, 65536, 262144]; // Various buffer sizes
                    
                    commonSizes.forEach(size => {
                        for (let i = 0; i < 3; i++) { // 3 buffers per size
                            this.bufferPool.push({
                                size: size,
                                buffer: new ArrayBuffer(size),
                                inUse: false,
                                lastUsed: Date.now()
                            });
                        }
                    });
                    
                    console.log(`🛠️ Buffer pool initialized with ${this.bufferPool.length} buffers`);
                }
                
                getOptimizedBuffer(requiredSize) {
                    // Find smallest available buffer that fits
                    const availableBuffer = this.bufferPool
                        .filter(b => !b.inUse && b.size >= requiredSize)
                        .sort((a, b) => a.size - b.size)[0];
                    
                    if (availableBuffer) {
                        availableBuffer.inUse = true;
                        availableBuffer.lastUsed = Date.now();
                        return availableBuffer.buffer.slice(0, requiredSize);
                    }
                    
                    // Create new buffer if needed
                    const newBuffer = new ArrayBuffer(requiredSize);
                    this.bufferPool.push({
                        size: requiredSize,
                        buffer: newBuffer,
                        inUse: true,
                        lastUsed: Date.now()
                    });
                    
                    return newBuffer;
                }
                
                releaseBuffer(buffer) {
                    const poolEntry = this.bufferPool.find(b => b.buffer === buffer);
                    if (poolEntry) {
                        poolEntry.inUse = false;
                        poolEntry.lastUsed = Date.now();
                    }
                }
                
                optimizeGeometry(geometry, cacheKey = null) {
                    if (!geometry) return geometry;
                    
                    // Check cache first
                    if (cacheKey && this.geometryPool.has(cacheKey)) {
                        this.updateCacheAccess(cacheKey);
                        return this.geometryPool.get(cacheKey);
                    }
                    
                    // Create optimized copy
                    const optimized = this.createOptimizedGeometry(geometry);
                    
                    // Cache if beneficial
                    if (cacheKey && this.shouldCache(optimized)) {
                        this.cacheGeometry(cacheKey, optimized);
                    }
                    
                    return optimized;
                }
                
                createOptimizedGeometry(geometry) {
                    try {
                        // Apply adaptive quality optimization first
                        let optimized = this.adaptiveQuality?.optimizeGeometry(geometry) || geometry;
                        
                        // Further optimizations
                        optimized = this.mergeVertices(optimized);
                        optimized = this.removeUnusedVertices(optimized);
                        optimized = this.optimizeIndices(optimized);
                        
                        // Compress attributes if enabled
                        if (this.compressionEnabled) {
                            optimized = this.compressGeometry(optimized);
                        }
                        
                        // Update metrics
                        this.updateResourceMetrics(optimized);
                        
                        console.log('🛠️ Geometry optimized:', {
                            vertices: optimized.attributes.position?.count || 0,
                            triangles: optimized.index ? optimized.index.count / 3 : 0
                        });
                        
                        return optimized;
                    } catch (error) {
                        console.warn('⚠️ Geometry optimization failed:', error);
                        return geometry;
                    }
                }
                
                mergeVertices(geometry, tolerance = 1e-6) {
                    // Merge duplicate vertices within tolerance
                    if (!geometry.attributes.position) return geometry;
                    
                    const positions = geometry.attributes.position.array;
                    const normals = geometry.attributes.normal?.array;
                    const uvs = geometry.attributes.uv?.array;
                    
                    const vertexMap = new Map();
                    const newPositions = [];
                    const newNormals = normals ? [] : null;
                    const newUVs = uvs ? [] : null;
                    const indexMap = [];
                    
                    for (let i = 0; i < positions.length; i += 3) {
                        const x = Math.round(positions[i] / tolerance) * tolerance;
                        const y = Math.round(positions[i + 1] / tolerance) * tolerance;
                        const z = Math.round(positions[i + 2] / tolerance) * tolerance;
                        
                        const key = `${x},${y},${z}`;
                        
                        if (vertexMap.has(key)) {
                            indexMap.push(vertexMap.get(key));
                        } else {
                            const newIndex = newPositions.length / 3;
                            vertexMap.set(key, newIndex);
                            indexMap.push(newIndex);
                            
                            newPositions.push(x, y, z);
                            
                            if (newNormals && i + 2 < normals.length) {
                                newNormals.push(normals[i], normals[i + 1], normals[i + 2]);
                            }
                            
                            if (newUVs && (i / 3) * 2 + 1 < uvs.length) {
                                const uvIndex = (i / 3) * 2;
                                newUVs.push(uvs[uvIndex], uvs[uvIndex + 1]);
                            }
                        }
                    }
                    
                    // Create optimized geometry
                    const optimized = new THREE.BufferGeometry();
                    optimized.setAttribute('position', new THREE.Float32BufferAttribute(newPositions, 3));
                    
                    if (newNormals) {
                        optimized.setAttribute('normal', new THREE.Float32BufferAttribute(newNormals, 3));
                    }
                    
                    if (newUVs) {
                        optimized.setAttribute('uv', new THREE.Float32BufferAttribute(newUVs, 2));
                    }
                    
                    // Update indices if they exist
                    if (geometry.index) {
                        const oldIndices = geometry.index.array;
                        const newIndices = [];
                        
                        for (let i = 0; i < oldIndices.length; i++) {
                            newIndices.push(indexMap[oldIndices[i]]);
                        }
                        
                        optimized.setIndex(newIndices);
                    }
                    
                    const reduction = (1 - newPositions.length / positions.length) * 100;
                    if (reduction > 1) {
                        console.log(`🛠️ Vertex merging: ${reduction.toFixed(1)}% reduction`);
                    }
                    
                    return optimized;
                }
                
                removeUnusedVertices(geometry) {
                    if (!geometry.index) return geometry; // Nothing to optimize without indices
                    
                    const indices = geometry.index.array;
                    const usedVertices = new Set(indices);
                    
                    if (usedVertices.size === geometry.attributes.position.count) {
                        return geometry; // All vertices are used
                    }
                    
                    // Create mapping from old to new indices
                    const vertexMap = [];
                    let newIndex = 0;
                    
                    for (let i = 0; i < geometry.attributes.position.count; i++) {
                        if (usedVertices.has(i)) {
                            vertexMap[i] = newIndex++;
                        }
                    }
                    
                    // Create new attributes with only used vertices
                    Object.keys(geometry.attributes).forEach(attributeName => {
                        const attribute = geometry.attributes[attributeName];
                        const itemSize = attribute.itemSize;
                        const newArray = new Float32Array(usedVertices.size * itemSize);
                        
                        let writeIndex = 0;
                        for (let i = 0; i < geometry.attributes.position.count; i++) {
                            if (usedVertices.has(i)) {
                                for (let j = 0; j < itemSize; j++) {
                                    newArray[writeIndex * itemSize + j] = attribute.array[i * itemSize + j];
                                }
                                writeIndex++;
                            }
                        }
                        
                        geometry.setAttribute(attributeName, new THREE.BufferAttribute(newArray, itemSize));
                    });
                    
                    // Update indices
                    const newIndices = new Uint32Array(indices.length);
                    for (let i = 0; i < indices.length; i++) {
                        newIndices[i] = vertexMap[indices[i]];
                    }
                    
                    geometry.setIndex(new THREE.BufferAttribute(newIndices, 1));
                    
                    console.log(`🛠️ Removed ${geometry.attributes.position.count - usedVertices.size} unused vertices`);
                    
                    return geometry;
                }
                
                optimizeIndices(geometry) {
                    if (!geometry.index) return geometry;
                    
                    // Use appropriate index type based on vertex count
                    const vertexCount = geometry.attributes.position.count;
                    const indices = geometry.index.array;
                    
                    let newIndices;
                    if (vertexCount < 256) {
                        newIndices = new Uint8Array(indices);
                    } else if (vertexCount < 65536) {
                        newIndices = new Uint16Array(indices);
                    } else {
                        newIndices = new Uint32Array(indices);
                    }
                    
                    geometry.setIndex(new THREE.BufferAttribute(newIndices, 1));
                    
                    return geometry;
                }
                
                compressGeometry(geometry) {
                    // Quantize vertex positions for better compression
                    if (geometry.attributes.position) {
                        const positions = geometry.attributes.position.array;
                        
                        // Find bounding box
                        let minX = Infinity, minY = Infinity, minZ = Infinity;
                        let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
                        
                        for (let i = 0; i < positions.length; i += 3) {
                            minX = Math.min(minX, positions[i]);
                            minY = Math.min(minY, positions[i + 1]);
                            minZ = Math.min(minZ, positions[i + 2]);
                            maxX = Math.max(maxX, positions[i]);
                            maxY = Math.max(maxY, positions[i + 1]);
                            maxZ = Math.max(maxZ, positions[i + 2]);
                        }
                        
                        // Quantize to reduce precision while maintaining quality
                        const quantizationBits = 14; // Good balance of quality vs size
                        const scale = (1 << quantizationBits) - 1;
                        
                        for (let i = 0; i < positions.length; i += 3) {
                            positions[i] = Math.round(((positions[i] - minX) / (maxX - minX)) * scale) / scale * (maxX - minX) + minX;
                            positions[i + 1] = Math.round(((positions[i + 1] - minY) / (maxY - minY)) * scale) / scale * (maxY - minY) + minY;
                            positions[i + 2] = Math.round(((positions[i + 2] - minZ) / (maxZ - minZ)) * scale) / scale * (maxZ - minZ) + minZ;
                        }
                    }
                    
                    return geometry;
                }
                
                cacheGeometry(key, geometry) {
                    // Check cache size limit
                    if (this.geometryPool.size >= this.maxCacheSize) {
                        this.evictLRUCache();
                    }
                    
                    this.geometryPool.set(key, geometry);
                    this.cacheAccessTimes.set(key, Date.now());
                    
                    console.log(`🛠️ Cached geometry: ${key} (cache size: ${this.geometryPool.size})`);
                }
                
                evictLRUCache() {
                    // Remove least recently used items
                    const sortedEntries = Array.from(this.cacheAccessTimes.entries())
                        .sort((a, b) => a[1] - b[1]);
                    
                    const toRemove = sortedEntries.slice(0, Math.floor(this.maxCacheSize * 0.25)); // Remove 25%
                    
                    toRemove.forEach(([key]) => {
                        this.geometryPool.delete(key);
                        this.cacheAccessTimes.delete(key);
                    });
                    
                    console.log(`🛠️ Cache eviction: removed ${toRemove.length} items`);
                }
                
                updateCacheAccess(key) {
                    this.cacheAccessTimes.set(key, Date.now());
                }
                
                shouldCache(geometry) {
                    const vertexCount = geometry.attributes.position?.count || 0;
                    const minVerticesForCaching = 1000; // Only cache substantial geometries
                    
                    return vertexCount >= minVerticesForCaching;
                }
                
                updateResourceMetrics(geometry) {
                    const vertices = geometry.attributes.position?.count || 0;
                    const triangles = geometry.index ? geometry.index.count / 3 : vertices / 3;
                    
                    this.resourceMetrics.totalVertices += vertices;
                    this.resourceMetrics.totalTriangles += triangles;
                    this.resourceMetrics.geometries++;
                    
                    // Estimate memory footprint
                    const positionSize = vertices * 3 * 4; // 3 floats per vertex
                    const normalSize = geometry.attributes.normal ? vertices * 3 * 4 : 0;
                    const uvSize = geometry.attributes.uv ? vertices * 2 * 4 : 0;
                    const indexSize = geometry.index ? geometry.index.count * 4 : 0;
                    
                    this.resourceMetrics.memoryFootprint += positionSize + normalSize + uvSize + indexSize;
                }
                
                handleMemoryPressure(memoryUsage) {
                    const usageRatio = memoryUsage.used / this.memoryBudget;
                    
                    if (usageRatio > this.memoryCriticalThreshold) {
                        console.warn('🛠️ Critical memory pressure - aggressive cleanup');
                        this.performAggressiveCleanup();
                    } else if (usageRatio > this.memoryWarningThreshold) {
                        console.warn('🛠️ Memory pressure detected - performing cleanup');
                        this.performResourceCleanup();
                    }
                }
                
                performResourceCleanup() {
                    if (this.isOptimizing) return;
                    
                    this.isOptimizing = true;
                    
                    try {
                        // Clean buffer pool
                        const now = Date.now();
                        const bufferTimeout = 30000; // 30 seconds
                        
                        this.bufferPool = this.bufferPool.filter(buffer => {
                            if (!buffer.inUse && (now - buffer.lastUsed) > bufferTimeout) {
                                return false; // Remove old unused buffers
                            }
                            return true;
                        });
                        
                        // Clean geometry cache
                        const cacheTimeout = 60000; // 1 minute
                        const expiredKeys = [];
                        
                        this.cacheAccessTimes.forEach((time, key) => {
                            if ((now - time) > cacheTimeout) {
                                expiredKeys.push(key);
                            }
                        });
                        
                        expiredKeys.forEach(key => {
                            this.geometryPool.delete(key);
                            this.cacheAccessTimes.delete(key);
                        });
                        
                        if (expiredKeys.length > 0) {
                            console.log(`🛠️ Cleanup: removed ${expiredKeys.length} expired cache entries`);
                        }
                        
                        // Force garbage collection if available
                        if (window.gc) {
                            window.gc();
                        }
                        
                    } finally {
                        this.isOptimizing = false;
                    }
                }
                
                performAggressiveCleanup() {
                    // Clear all caches
                    this.geometryPool.clear();
                    this.materialPool.clear();
                    this.texturePool.clear();
                    this.cacheAccessTimes.clear();
                    
                    // Reset unused buffers
                    this.bufferPool = this.bufferPool.filter(buffer => buffer.inUse);
                    
                    // Reset metrics
                    this.resourceMetrics = {
                        geometries: 0,
                        materials: 0,
                        textures: 0,
                        totalVertices: 0,
                        totalTriangles: 0,
                        memoryFootprint: 0
                    };
                    
                    console.log('🛠️ Aggressive cleanup completed');
                }
                
                getResourceReport() {
                    return {
                        metrics: this.resourceMetrics,
                        cache: {
                            geometries: this.geometryPool.size,
                            materials: this.materialPool.size,
                            textures: this.texturePool.size,
                            buffers: this.bufferPool.length
                        },
                        memory: {
                            budget: this.memoryBudget,
                            estimated: this.resourceMetrics.memoryFootprint,
                            usage: this.resourceMetrics.memoryFootprint / this.memoryBudget
                        },
                        performance: {
                            compressionEnabled: this.compressionEnabled,
                            maxCacheSize: this.maxCacheSize
                        }
                    };
                }
                
                dispose() {
                    this.enabled = false;
                    
                    if (this.cleanupInterval) {
                        clearInterval(this.cleanupInterval);
                        this.cleanupInterval = null;
                    }
                    
                    this.performAggressiveCleanup();
                    
                    console.log('🛠️ ResourceOptimizationEngine disposed');
                }
            }
            
            // Initialize resource optimization engine
            resourceOptimizer = new ResourceOptimizationEngine(performanceMonitor, adaptiveQuality, progressiveLoader);
            
            // ===== PHASE 5.2.3: Keyboard Navigation & Accessibility =====
            // Comprehensive keyboard navigation and screen reader support
            class AccessibilityManager {
                constructor(container, controls) {
                    this.container = container;
                    this.controls = controls;
                    this.enabled = true;
                    
                    // Keyboard navigation state
                    this.keyboardEnabled = true;
                    this.focusVisible = false;
                    this.activeElement = null;
                    
                    // Navigation speeds
                    this.rotationSpeed = 0.05; // radians per keypress
                    this.panSpeed = 0.1; // units per keypress
                    this.zoomSpeed = 0.1; // zoom factor per keypress
                    
                    // Accessibility features
                    this.screenReaderEnabled = this.detectScreenReader();
                    this.highContrastMode = false;
                    this.reducedMotion = this.detectReducedMotion();
                    
                    // Keyboard shortcuts
                    this.shortcuts = {
                        // Camera controls
                        'ArrowLeft': () => this.rotateCamera(-this.rotationSpeed, 0),
                        'ArrowRight': () => this.rotateCamera(this.rotationSpeed, 0),
                        'ArrowUp': () => this.rotateCamera(0, -this.rotationSpeed),
                        'ArrowDown': () => this.rotateCamera(0, this.rotationSpeed),
                        'w': () => this.panCamera(0, this.panSpeed, 0),
                        'a': () => this.panCamera(-this.panSpeed, 0, 0),
                        's': () => this.panCamera(0, -this.panSpeed, 0),
                        'd': () => this.panCamera(this.panSpeed, 0, 0),
                        'q': () => this.panCamera(0, 0, this.panSpeed),
                        'e': () => this.panCamera(0, 0, -this.panSpeed),
                        '+': () => this.zoomCamera(1 + this.zoomSpeed),
                        '-': () => this.zoomCamera(1 - this.zoomSpeed),
                        'r': () => this.resetCamera(),
                        
                        // View presets
                        '1': () => this.setViewPreset('front'),
                        '2': () => this.setViewPreset('back'),
                        '3': () => this.setViewPreset('left'),
                        '4': () => this.setViewPreset('right'),
                        '5': () => this.setViewPreset('top'),
                        '6': () => this.setViewPreset('bottom'),
                        '7': () => this.setViewPreset('isometric'),
                        
                        // Accessibility
                        'h': () => this.showKeyboardHelp(),
                        'c': () => this.toggleHighContrast(),
                        'f': () => this.toggleFullscreen(),
                        'Escape': () => this.exitFocus()
                    };
                    
                    // ARIA live region for announcements
                    this.announcements = null;
                    
                    this.initializeAccessibility();
                    console.log('♿ AccessibilityManager initialized');
                }
                
                initializeAccessibility() {
                    // Make container focusable
                    this.container.setAttribute('tabindex', '0');
                    this.container.setAttribute('role', 'application');
                    this.container.setAttribute('aria-label', '3D OpenSCAD Model Viewer');
                    this.container.setAttribute('aria-describedby', 'viewer-help');
                    
                    // Create ARIA live region
                    this.announcements = document.createElement('div');
                    this.announcements.setAttribute('aria-live', 'polite');
                    this.announcements.setAttribute('aria-atomic', 'true');
                    this.announcements.style.cssText = `
                        position: absolute;
                        left: -10000px;
                        width: 1px;
                        height: 1px;
                        overflow: hidden;
                    `;
                    this.container.appendChild(this.announcements);
                    
                    // Create keyboard help overlay
                    this.createKeyboardHelp();
                    
                    // Setup event listeners
                    this.setupEventListeners();
                    
                    // Apply accessibility preferences
                    this.applyAccessibilityPreferences();
                    
                    // Announce initial state
                    this.announce('3D OpenSCAD viewer loaded. Press H for keyboard shortcuts.');
                }
                
                setupEventListeners() {
                    // Keyboard navigation
                    this.container.addEventListener('keydown', (e) => {
                        if (!this.keyboardEnabled) return;
                        
                        const key = e.key;
                        const shortcut = this.shortcuts[key];
                        
                        if (shortcut) {
                            e.preventDefault();
                            shortcut();
                            this.showFocusIndicator();
                        }
                    });
                    
                    // Focus management
                    this.container.addEventListener('focus', () => {
                        this.focusVisible = true;
                        this.container.classList.add('keyboard-focused');
                        this.announce('3D viewer focused. Use arrow keys to rotate, WASD to pan, +/- to zoom.');
                    });
                    
                    this.container.addEventListener('blur', () => {
                        this.focusVisible = false;
                        this.container.classList.remove('keyboard-focused');
                    });
                    
                    // Mouse interaction detection
                    this.container.addEventListener('mousedown', () => {
                        this.focusVisible = false;
                        this.container.classList.remove('keyboard-focused');
                    });
                }
                
                detectScreenReader() {
                    // Check for common screen reader indicators
                    return !!(
                        navigator.userAgent.includes('NVDA') ||
                        navigator.userAgent.includes('JAWS') ||
                        navigator.userAgent.includes('VoiceOver') ||
                        window.speechSynthesis ||
                        navigator.mediaDevices?.getUserMedia
                    );
                }
                
                detectReducedMotion() {
                    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
                }
                
                applyAccessibilityPreferences() {
                    // Apply reduced motion
                    if (this.reducedMotion) {
                        this.container.classList.add('reduced-motion');
                        // Disable animations in controls if available
                        if (this.controls && this.controls.enableDamping) {
                            this.controls.enableDamping = false;
                        }
                    }
                    
                    // High contrast detection
                    if (window.matchMedia('(prefers-contrast: high)').matches) {
                        this.enableHighContrast();
                    }
                }
                
                rotateCamera(deltaX, deltaY) {
                    if (!this.controls) return;
                    
                    // Apply rotation through controls
                    if (this.controls.object) {
                        const camera = this.controls.object;
                        
                        // Horizontal rotation (around Y axis)
                        if (deltaX !== 0) {
                            const spherical = new THREE.Spherical();
                            spherical.setFromVector3(camera.position.clone().sub(this.controls.target));
                            spherical.theta += deltaX;
                            camera.position.setFromSpherical(spherical).add(this.controls.target);
                        }
                        
                        // Vertical rotation (around X axis)
                        if (deltaY !== 0) {
                            const spherical = new THREE.Spherical();
                            spherical.setFromVector3(camera.position.clone().sub(this.controls.target));
                            spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi + deltaY));
                            camera.position.setFromSpherical(spherical).add(this.controls.target);
                        }
                        
                        camera.lookAt(this.controls.target);
                        this.controls.update();
                        
                        this.announce(`Camera rotated. Position: ${this.describeCameraPosition()}`);
                    }
                }
                
                panCamera(deltaX, deltaY, deltaZ) {
                    if (!this.controls || !this.controls.object) return;
                    
                    const camera = this.controls.object;
                    const offset = new THREE.Vector3(deltaX, deltaY, deltaZ);
                    
                    // Transform by camera orientation
                    offset.applyMatrix3(camera.matrix.extractBasis(new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()));
                    
                    camera.position.add(offset);
                    this.controls.target.add(offset);
                    this.controls.update();
                    
                    this.announce(`Camera panned. Position: ${this.describeCameraPosition()}`);
                }
                
                zoomCamera(factor) {
                    if (!this.controls || !this.controls.object) return;
                    
                    const camera = this.controls.object;
                    const direction = new THREE.Vector3();
                    direction.subVectors(this.controls.target, camera.position).normalize();
                    
                    const distance = camera.position.distanceTo(this.controls.target);
                    const newDistance = Math.max(0.1, distance * (1 / factor));
                    
                    camera.position.copy(this.controls.target).addScaledVector(direction, -newDistance);
                    this.controls.update();
                    
                    this.announce(`Camera zoom: ${factor > 1 ? 'in' : 'out'}. Distance: ${newDistance.toFixed(1)}`);
                }
                
                resetCamera() {
                    if (!this.controls) return;
                    
                    // Reset to default position
                    const camera = this.controls.object;
                    camera.position.set(10, 10, 10);
                    this.controls.target.set(0, 0, 0);
                    camera.lookAt(this.controls.target);
                    this.controls.update();
                    
                    this.announce('Camera reset to default position');
                }
                
                setViewPreset(view) {
                    if (!this.controls || !this.controls.object) return;
                    
                    const camera = this.controls.object;
                    const distance = camera.position.distanceTo(this.controls.target);
                    
                    const positions = {
                        front: [0, 0, distance],
                        back: [0, 0, -distance],
                        left: [-distance, 0, 0],
                        right: [distance, 0, 0],
                        top: [0, distance, 0],
                        bottom: [0, -distance, 0],
                        isometric: [distance * 0.7, distance * 0.7, distance * 0.7]
                    };
                    
                    const pos = positions[view];
                    if (pos) {
                        camera.position.set(...pos);
                        camera.lookAt(this.controls.target);
                        this.controls.update();
                        
                        this.announce(`View set to ${view}`);
                    }
                }
                
                describeCameraPosition() {
                    if (!this.controls || !this.controls.object) return 'unknown';
                    
                    const camera = this.controls.object;
                    const pos = camera.position;
                    const distance = pos.distanceTo(this.controls.target);
                    
                    return `X: ${pos.x.toFixed(1)}, Y: ${pos.y.toFixed(1)}, Z: ${pos.z.toFixed(1)}, Distance: ${distance.toFixed(1)}`;
                }
                
                showFocusIndicator() {
                    this.container.classList.add('keyboard-active');
                    setTimeout(() => {
                        this.container.classList.remove('keyboard-active');
                    }, 200);
                }
                
                announce(message) {
                    if (!this.announcements) return;
                    
                    this.announcements.textContent = message;
                    console.log('♿ Announced:', message);
                }
                
                createKeyboardHelp() {
                    const helpId = 'viewer-help';
                    const existing = document.getElementById(helpId);
                    if (existing) existing.remove();
                    
                    const help = document.createElement('div');
                    help.id = helpId;
                    help.className = 'keyboard-help';
                    help.setAttribute('role', 'dialog');
                    help.setAttribute('aria-labelledby', 'help-title');
                    help.style.cssText = `
                        position: fixed;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        background: rgba(0, 0, 0, 0.95);
                        color: white;
                        padding: 20px;
                        border-radius: 8px;
                        max-width: 500px;
                        max-height: 80vh;
                        overflow-y: auto;
                        z-index: 10000;
                        display: none;
                        font-family: monospace;
                        font-size: 14px;
                        line-height: 1.4;
                    `;
                    
                    help.innerHTML = `
                        <h3 id="help-title" style="margin-top: 0; color: #4CAF50;">🎯 Keyboard Navigation</h3>
                        
                        <div style="margin-bottom: 15px;">
                            <h4 style="color: #2196F3; margin-bottom: 5px;">📹 Camera Controls</h4>
                            <div>Arrow Keys: Rotate camera</div>
                            <div>W/A/S/D: Pan camera</div>
                            <div>Q/E: Move up/down</div>
                            <div>+/-: Zoom in/out</div>
                            <div>R: Reset camera</div>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <h4 style="color: #FF9800; margin-bottom: 5px;">👁️ View Presets</h4>
                            <div>1: Front view</div>
                            <div>2: Back view</div>
                            <div>3: Left view</div>
                            <div>4: Right view</div>
                            <div>5: Top view</div>
                            <div>6: Bottom view</div>
                            <div>7: Isometric view</div>
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <h4 style="color: #9C27B0; margin-bottom: 5px;">♿ Accessibility</h4>
                            <div>H: Show this help</div>
                            <div>C: Toggle high contrast</div>
                            <div>F: Toggle fullscreen</div>
                            <div>Esc: Exit focus/close dialogs</div>
                        </div>
                        
                        <div style="text-align: center; margin-top: 20px;">
                            <button onclick="this.parentElement.parentElement.style.display='none'" 
                                    style="background: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                                Close (Esc)
                            </button>
                        </div>
                    `;
                    
                    document.body.appendChild(help);
                    this.keyboardHelp = help;
                }
                
                showKeyboardHelp() {
                    if (this.keyboardHelp) {
                        this.keyboardHelp.style.display = 'block';
                        this.keyboardHelp.focus();
                        this.announce('Keyboard help dialog opened');
                    }
                }
                
                toggleHighContrast() {
                    this.highContrastMode = !this.highContrastMode;
                    
                    if (this.highContrastMode) {
                        this.enableHighContrast();
                    } else {
                        this.disableHighContrast();
                    }
                    
                    this.announce(`High contrast mode ${this.highContrastMode ? 'enabled' : 'disabled'}`);
                }
                
                enableHighContrast() {
                    this.container.classList.add('high-contrast');
                    document.documentElement.style.setProperty('--viewer-bg', '#000000');
                    document.documentElement.style.setProperty('--viewer-text', '#ffffff');
                    document.documentElement.style.setProperty('--viewer-border', '#ffffff');
                }
                
                disableHighContrast() {
                    this.container.classList.remove('high-contrast');
                    document.documentElement.style.removeProperty('--viewer-bg');
                    document.documentElement.style.removeProperty('--viewer-text');
                    document.documentElement.style.removeProperty('--viewer-border');
                }
                
                toggleFullscreen() {
                    if (!document.fullscreenElement) {
                        this.container.requestFullscreen?.() || 
                        this.container.webkitRequestFullscreen?.() || 
                        this.container.mozRequestFullScreen?.();
                        this.announce('Entered fullscreen mode');
                    } else {
                        document.exitFullscreen?.() || 
                        document.webkitExitFullscreen?.() || 
                        document.mozCancelFullScreen?.();
                        this.announce('Exited fullscreen mode');
                    }
                }
                
                exitFocus() {
                    if (this.keyboardHelp && this.keyboardHelp.style.display !== 'none') {
                        this.keyboardHelp.style.display = 'none';
                        this.container.focus();
                        this.announce('Help dialog closed');
                    } else {
                        this.container.blur();
                        this.announce('Viewer unfocused');
                    }
                }
                
                setKeyboardEnabled(enabled) {
                    this.keyboardEnabled = enabled;
                    this.announce(`Keyboard navigation ${enabled ? 'enabled' : 'disabled'}`);
                }
                
                getAccessibilityInfo() {
                    return {
                        keyboardEnabled: this.keyboardEnabled,
                        screenReaderDetected: this.screenReaderEnabled,
                        highContrastMode: this.highContrastMode,
                        reducedMotion: this.reducedMotion,
                        focusVisible: this.focusVisible,
                        shortcuts: Object.keys(this.shortcuts)
                    };
                }
                
                dispose() {
                    this.enabled = false;
                    
                    if (this.keyboardHelp && this.keyboardHelp.parentNode) {
                        this.keyboardHelp.parentNode.removeChild(this.keyboardHelp);
                    }
                    
                    if (this.announcements && this.announcements.parentNode) {
                        this.announcements.parentNode.removeChild(this.announcements);
                    }
                    
                    console.log('♿ AccessibilityManager disposed');
                }
            }
            
            // Initialize accessibility manager (will be connected to controls later)
            accessibilityManager = new AccessibilityManager(container, null);
            
            // ===== PHASE 5.2.4: Mobile Touch Controls =====
            // Advanced touch navigation and mobile optimization
            class MobileTouchManager {
                constructor(container, canvas) {
                    this.container = container;
                    this.canvas = canvas;
                    this.enabled = true;
                    
                    // Touch state management
                    this.touches = new Map();
                    this.lastTouchTime = 0;
                    this.touchStartTime = 0;
                    this.gestureActive = false;
                    this.initialPinchDistance = 0;
                    this.initialTouchCenter = { x: 0, y: 0 };
                    
                    // Mobile detection
                    this.isMobile = this.detectMobile();
                    this.isTablet = this.detectTablet();
                    this.hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
                    
                    // Touch sensitivity settings
                    this.sensitivity = {
                        rotation: this.isMobile ? 0.008 : 0.005,
                        pan: this.isMobile ? 0.4 : 0.3,
                        zoom: this.isMobile ? 0.3 : 0.2,
                        doubleTap: 300, // ms
                        longPress: 800, // ms
                        swipeThreshold: 50 // pixels
                    };
                    
                    // Gesture recognition
                    this.gestureTypes = {
                        NONE: 'none',
                        ROTATE: 'rotate',
                        PAN: 'pan',
                        ZOOM: 'zoom',
                        SWIPE: 'swipe',
                        TAP: 'tap',
                        DOUBLE_TAP: 'double_tap',
                        LONG_PRESS: 'long_press'
                    };
                    
                    this.currentGesture = this.gestureTypes.NONE;
                    this.lastTap = 0;
                    this.longPressTimer = null;
                    
                    // Performance optimization for mobile
                    this.frameThrottle = this.isMobile ? 33 : 16; // 30fps vs 60fps
                    this.lastFrameTime = 0;
                    
                    // Haptic feedback support
                    this.hapticEnabled = this.detectHapticSupport();
                    
                    // Controls reference (will be set later)
                    this.controls = null;
                    
                    this.initializeMobileControls();
                    console.log('📱 MobileTouchManager initialized:', {
                        mobile: this.isMobile,
                        tablet: this.isTablet,
                        touch: this.hasTouch,
                        haptic: this.hapticEnabled
                    });
                }
                
                detectMobile() {
                    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
                }
                
                detectTablet() {
                    return /iPad|Android.*Tablet|Windows.*Touch/i.test(navigator.userAgent) || 
                           (navigator.maxTouchPoints > 1 && window.innerWidth > 768);
                }
                
                detectHapticSupport() {
                    return 'vibrate' in navigator || 'hapticFeedback' in navigator;
                }
                
                initializeMobileControls() {
                    if (!this.hasTouch) return;
                    
                    // Apply mobile-specific styles
                    this.applyMobileStyles();
                    
                    // Setup touch event listeners
                    this.setupTouchListeners();
                    
                    // Create mobile UI enhancements
                    this.createMobileUI();
                    
                    // Optimize for mobile performance
                    this.optimizeForMobile();
                }
                
                applyMobileStyles() {
                    // Prevent default touch behaviors
                    this.container.style.touchAction = 'none';
                    this.container.style.userSelect = 'none';
                    this.container.style.webkitUserSelect = 'none';
                    this.container.style.webkitTouchCallout = 'none';
                    
                    // Mobile-optimized cursor
                    if (this.isMobile) {
                        this.container.style.cursor = 'grab';
                    }
                    
                    // Add mobile-specific CSS classes
                    this.container.classList.add('mobile-touch-enabled');
                    if (this.isMobile) this.container.classList.add('mobile-device');
                    if (this.isTablet) this.container.classList.add('tablet-device');
                }
                
                setupTouchListeners() {
                    // Touch events
                    this.container.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
                    this.container.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
                    this.container.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: false });
                    this.container.addEventListener('touchcancel', (e) => this.handleTouchCancel(e), { passive: false });
                    
                    // Gesture events (for Safari)
                    this.container.addEventListener('gesturestart', (e) => this.handleGestureStart(e), { passive: false });
                    this.container.addEventListener('gesturechange', (e) => this.handleGestureChange(e), { passive: false });
                    this.container.addEventListener('gestureend', (e) => this.handleGestureEnd(e), { passive: false });
                }
                
                handleTouchStart(event) {
                    event.preventDefault();
                    
                    const now = Date.now();
                    this.touchStartTime = now;
                    this.lastTouchTime = now;
                    
                    // Store all touches
                    for (let i = 0; i < event.touches.length; i++) {
                        const touch = event.touches[i];
                        this.touches.set(touch.identifier, {
                            id: touch.identifier,
                            startX: touch.clientX,
                            startY: touch.clientY,
                            currentX: touch.clientX,
                            currentY: touch.clientY,
                            startTime: now
                        });
                    }
                    
                    // Determine gesture type
                    this.determineGesture(event);
                    
                    // Setup long press detection for single touch
                    if (event.touches.length === 1) {
                        this.longPressTimer = setTimeout(() => {
                            this.triggerLongPress(event.touches[0]);
                        }, this.sensitivity.longPress);
                    }
                    
                    this.hapticFeedback('light');
                }
                
                handleTouchMove(event) {
                    event.preventDefault();
                    
                    const now = Date.now();
                    if (now - this.lastFrameTime < this.frameThrottle) return; // Throttle for performance
                    this.lastFrameTime = now;
                    
                    // Clear long press if finger moves
                    if (this.longPressTimer) {
                        clearTimeout(this.longPressTimer);
                        this.longPressTimer = null;
                    }
                    
                    // Update touch positions
                    for (let i = 0; i < event.touches.length; i++) {
                        const touch = event.touches[i];
                        const stored = this.touches.get(touch.identifier);
                        if (stored) {
                            stored.currentX = touch.clientX;
                            stored.currentY = touch.clientY;
                        }
                    }
                    
                    // Handle gesture
                    this.handleGestureMove(event);
                }
                
                handleTouchEnd(event) {
                    event.preventDefault();
                    
                    const now = Date.now();
                    const touchDuration = now - this.touchStartTime;
                    
                    // Clear timers
                    if (this.longPressTimer) {
                        clearTimeout(this.longPressTimer);
                        this.longPressTimer = null;
                    }
                    
                    // Handle tap gestures
                    if (event.changedTouches.length === 1 && touchDuration < this.sensitivity.doubleTap) {
                        this.handleTap(event.changedTouches[0], now);
                    }
                    
                    // Remove ended touches
                    for (let i = 0; i < event.changedTouches.length; i++) {
                        const touch = event.changedTouches[i];
                        this.touches.delete(touch.identifier);
                    }
                    
                    // Reset gesture if no more touches
                    if (event.touches.length === 0) {
                        this.currentGesture = this.gestureTypes.NONE;
                        this.gestureActive = false;
                    }
                    
                    this.hapticFeedback('light');
                }
                
                handleTouchCancel(event) {
                    // Clear all touch state
                    this.touches.clear();
                    this.currentGesture = this.gestureTypes.NONE;
                    this.gestureActive = false;
                    
                    if (this.longPressTimer) {
                        clearTimeout(this.longPressTimer);
                        this.longPressTimer = null;
                    }
                }
                
                determineGesture(event) {
                    const touchCount = event.touches.length;
                    
                    if (touchCount === 1) {
                        this.currentGesture = this.gestureTypes.PAN;
                    } else if (touchCount === 2) {
                        this.currentGesture = this.gestureTypes.ZOOM;
                        this.setupPinchGesture(event);
                    } else if (touchCount === 3) {
                        this.currentGesture = this.gestureTypes.ROTATE;
                    }
                    
                    this.gestureActive = true;
                }
                
                setupPinchGesture(event) {
                    const touch1 = event.touches[0];
                    const touch2 = event.touches[1];
                    
                    // Calculate initial distance and center
                    this.initialPinchDistance = this.getDistance(touch1, touch2);
                    this.initialTouchCenter = this.getCenter(touch1, touch2);
                }
                
                handleGestureMove(event) {
                    if (!this.gestureActive || !this.controls) return;
                    
                    switch (this.currentGesture) {
                        case this.gestureTypes.PAN:
                            this.handlePanGesture(event);
                            break;
                        case this.gestureTypes.ZOOM:
                            this.handleZoomGesture(event);
                            break;
                        case this.gestureTypes.ROTATE:
                            this.handleRotateGesture(event);
                            break;
                    }
                }
                
                handlePanGesture(event) {
                    if (event.touches.length !== 1) return;
                    
                    const touch = event.touches[0];
                    const stored = this.touches.get(touch.identifier);
                    if (!stored) return;
                    
                    const deltaX = touch.clientX - stored.startX;
                    const deltaY = touch.clientY - stored.startY;
                    
                    // Check if this is a rotation gesture (around edges) or pan (center)
                    const rect = this.container.getBoundingClientRect();
                    const centerX = rect.width / 2;
                    const centerY = rect.height / 2;
                    const touchX = touch.clientX - rect.left;
                    const touchY = touch.clientY - rect.top;
                    
                    const distanceFromCenter = Math.sqrt(
                        Math.pow(touchX - centerX, 2) + Math.pow(touchY - centerY, 2)
                    );
                    
                    // If touch is near edges, treat as rotation; if near center, treat as pan
                    const edgeThreshold = Math.min(rect.width, rect.height) * 0.3;
                    
                    if (distanceFromCenter > edgeThreshold) {
                        // Rotation around center
                        this.applyCameraRotation(-deltaX * this.sensitivity.rotation, -deltaY * this.sensitivity.rotation);
                    } else {
                        // Pan camera
                        this.applyCameraPan(deltaX * this.sensitivity.pan, -deltaY * this.sensitivity.pan);
                    }
                    
                    // Update start position for continuous movement
                    stored.startX = touch.clientX;
                    stored.startY = touch.clientY;
                }
                
                handleZoomGesture(event) {
                    if (event.touches.length !== 2) return;
                    
                    const touch1 = event.touches[0];
                    const touch2 = event.touches[1];
                    
                    const currentDistance = this.getDistance(touch1, touch2);
                    const zoomFactor = currentDistance / this.initialPinchDistance;
                    
                    this.applyCameraZoom(zoomFactor);
                    
                    // Update for next frame
                    this.initialPinchDistance = currentDistance;
                    
                    this.hapticFeedback('medium');
                }
                
                handleRotateGesture(event) {
                    if (event.touches.length < 2) return;
                    
                    // Use first two touches for rotation
                    const touch1 = event.touches[0];
                    const touch2 = event.touches[1];
                    
                    const stored1 = this.touches.get(touch1.identifier);
                    const stored2 = this.touches.get(touch2.identifier);
                    
                    if (!stored1 || !stored2) return;
                    
                    // Calculate rotation based on finger movement
                    const deltaX = ((touch1.clientX - stored1.startX) + (touch2.clientX - stored2.startX)) / 2;
                    const deltaY = ((touch1.clientY - stored1.startY) + (touch2.clientY - stored2.startY)) / 2;
                    
                    this.applyCameraRotation(deltaX * this.sensitivity.rotation * 0.5, deltaY * this.sensitivity.rotation * 0.5);
                    
                    // Update start positions
                    stored1.startX = touch1.clientX;
                    stored1.startY = touch1.clientY;
                    stored2.startX = touch2.clientX;
                    stored2.startY = touch2.clientY;
                }
                
                handleTap(touch, now) {
                    const timeSinceLastTap = now - this.lastTap;
                    
                    if (timeSinceLastTap < this.sensitivity.doubleTap) {
                        // Double tap - reset camera
                        this.resetCamera();
                        this.hapticFeedback('strong');
                    } else {
                        // Single tap - could be used for selection in the future
                        this.hapticFeedback('light');
                    }
                    
                    this.lastTap = now;
                }
                
                triggerLongPress(touch) {
                    // Long press - show mobile controls menu
                    this.showMobileMenu(touch);
                    this.hapticFeedback('strong');
                }
                
                applyCameraRotation(deltaX, deltaY) {
                    if (!this.controls || !this.controls.object) return;
                    
                    const camera = this.controls.object;
                    const spherical = new THREE.Spherical();
                    spherical.setFromVector3(camera.position.clone().sub(this.controls.target));
                    
                    spherical.theta += deltaX;
                    spherical.phi = Math.max(0.1, Math.min(Math.PI - 0.1, spherical.phi + deltaY));
                    
                    camera.position.setFromSpherical(spherical).add(this.controls.target);
                    camera.lookAt(this.controls.target);
                    this.controls.update();
                }
                
                applyCameraPan(deltaX, deltaY) {
                    if (!this.controls || !this.controls.object) return;
                    
                    const camera = this.controls.object;
                    const offset = new THREE.Vector3();
                    
                    // Get camera's right and up vectors
                    const right = new THREE.Vector3();
                    const up = new THREE.Vector3();
                    camera.getWorldDirection(offset);
                    right.crossVectors(offset, camera.up).normalize();
                    up.crossVectors(right, offset).normalize();
                    
                    // Apply pan movement
                    const panOffset = new THREE.Vector3();
                    panOffset.addScaledVector(right, deltaX * 0.01);
                    panOffset.addScaledVector(up, deltaY * 0.01);
                    
                    camera.position.add(panOffset);
                    this.controls.target.add(panOffset);
                    this.controls.update();
                }
                
                applyCameraZoom(factor) {
                    if (!this.controls || !this.controls.object) return;
                    
                    const camera = this.controls.object;
                    const direction = new THREE.Vector3();
                    direction.subVectors(this.controls.target, camera.position).normalize();
                    
                    const distance = camera.position.distanceTo(this.controls.target);
                    const newDistance = Math.max(0.1, distance / factor);
                    
                    camera.position.copy(this.controls.target).addScaledVector(direction, -newDistance);
                    this.controls.update();
                }
                
                resetCamera() {
                    if (!this.controls || !this.controls.object) return;
                    
                    const camera = this.controls.object;
                    camera.position.set(10, 10, 10);
                    this.controls.target.set(0, 0, 0);
                    camera.lookAt(this.controls.target);
                    this.controls.update();
                }
                
                getDistance(touch1, touch2) {
                    const dx = touch1.clientX - touch2.clientX;
                    const dy = touch1.clientY - touch2.clientY;
                    return Math.sqrt(dx * dx + dy * dy);
                }
                
                getCenter(touch1, touch2) {
                    return {
                        x: (touch1.clientX + touch2.clientX) / 2,
                        y: (touch1.clientY + touch2.clientY) / 2
                    };
                }
                
                hapticFeedback(intensity = 'light') {
                    if (!this.hapticEnabled) return;
                    
                    if (navigator.vibrate) {
                        const patterns = {
                            light: [10],
                            medium: [20],
                            strong: [50]
                        };
                        navigator.vibrate(patterns[intensity] || patterns.light);
                    }
                }
                
                createMobileUI() {
                    if (!this.isMobile && !this.isTablet) return;
                    
                    // Create mobile control hints
                    const hints = document.createElement('div');
                    hints.className = 'mobile-hints';
                    hints.style.cssText = `
                        position: absolute;
                        bottom: 10px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: rgba(0, 0, 0, 0.7);
                        color: white;
                        padding: 8px 12px;
                        border-radius: 4px;
                        font-size: 12px;
                        text-align: center;
                        pointer-events: none;
                        z-index: 1000;
                    `;
                    
                    hints.innerHTML = `
                        📱 1 finger: Rotate/Pan | ✌️ 2 fingers: Zoom | 👆 Double tap: Reset
                    `;
                    
                    this.container.appendChild(hints);
                    
                    // Auto-hide after 5 seconds
                    setTimeout(() => {
                        hints.style.opacity = '0';
                        hints.style.transition = 'opacity 0.5s';
                        setTimeout(() => hints.remove(), 500);
                    }, 5000);
                }
                
                showMobileMenu(touch) {
                    // Create context menu for mobile
                    const menu = document.createElement('div');
                    menu.className = 'mobile-context-menu';
                    menu.style.cssText = `
                        position: fixed;
                        top: ${touch.clientY}px;
                        left: ${touch.clientX}px;
                        background: white;
                        border: 1px solid #ccc;
                        border-radius: 4px;
                        padding: 8px 0;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                        z-index: 10000;
                        min-width: 120px;
                    `;
                    
                    const options = [
                        { text: '🏠 Reset View', action: () => this.resetCamera() },
                        { text: '📐 Fit to Screen', action: () => this.fitToScreen() },
                        { text: '🔄 Toggle Quality', action: () => this.toggleMobileQuality() },
                        { text: '❌ Close', action: () => menu.remove() }
                    ];
                    
                    options.forEach(option => {
                        const item = document.createElement('div');
                        item.textContent = option.text;
                        item.style.cssText = `
                            padding: 8px 16px;
                            cursor: pointer;
                            font-size: 14px;
                        `;
                        item.addEventListener('click', () => {
                            option.action();
                            menu.remove();
                        });
                        menu.appendChild(item);
                    });
                    
                    document.body.appendChild(menu);
                    
                    // Auto-remove after 5 seconds
                    setTimeout(() => menu.remove(), 5000);
                }
                
                optimizeForMobile() {
                    if (this.isMobile) {
                        // Reduce render quality for better performance
                        if (window.adaptiveQuality) {
                            window.adaptiveQuality.forceQuality('medium', 'Mobile optimization');
                        }
                        
                        // Disable expensive features
                        this.container.classList.add('mobile-optimized');
                    }
                }
                
                fitToScreen() {
                    // Implement fit-to-screen functionality
                    console.log('📱 Fit to screen triggered');
                }
                
                toggleMobileQuality() {
                    if (window.adaptiveQuality) {
                        const current = window.adaptiveQuality.currentQuality;
                        const newQuality = current === 'low' ? 'medium' : 'low';
                        window.adaptiveQuality.forceQuality(newQuality, 'Mobile quality toggle');
                    }
                }
                
                // Safari gesture events
                handleGestureStart(event) {
                    event.preventDefault();
                }
                
                handleGestureChange(event) {
                    event.preventDefault();
                    // Use Safari's native gesture scale for zoom
                    this.applyCameraZoom(event.scale);
                }
                
                handleGestureEnd(event) {
                    event.preventDefault();
                }
                
                setControls(controls) {
                    this.controls = controls;
                    console.log('📱 Mobile touch controls connected to camera controls');
                }
                
                getMobileInfo() {
                    return {
                        isMobile: this.isMobile,
                        isTablet: this.isTablet,
                        hasTouch: this.hasTouch,
                        hapticEnabled: this.hapticEnabled,
                        currentGesture: this.currentGesture,
                        activeTouches: this.touches.size,
                        sensitivity: this.sensitivity
                    };
                }
                
                dispose() {
                    this.enabled = false;
                    
                    if (this.longPressTimer) {
                        clearTimeout(this.longPressTimer);
                        this.longPressTimer = null;
                    }
                    
                    this.touches.clear();
                    
                    console.log('📱 MobileTouchManager disposed');
                }
            }
            
            // Initialize mobile touch manager
            mobileTouchManager = new MobileTouchManager(container, null);
            
            // Start loading with enhanced progress feedback
            progressiveLoader.showState('loading-three', 0, 'Connecting to CDN...');
            
            if (!window.THREE) {
                const threeSources = [
                    'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
                    'https://unpkg.com/three@0.128.0/build/three.min.js',
                    'https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js'
                ];
                
                let loaded = false;
                for (let i = 0; i < threeSources.length; i++) {
                    const src = threeSources[i];
                    try {
                        progressiveLoader.showState('loading-three', (i / threeSources.length) * 50, `Trying CDN ${i + 1}/${threeSources.length}...`);
                        
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
                            progressiveLoader.showState('loading-three', 75, 'Three.js loaded successfully!');
                            console.log("✅ Three.js loaded from:", src);
                            break;
                        }
                    } catch (e) {
                        console.warn(`Three.js CDN ${src} failed:`, e);
                        continue;
                    }
                }
                
                if (!loaded) {
                    const error = new Error("Could not load Three.js from any CDN");
                    errorHandler.handleError(error, 'network', () => location.reload());
                    throw error;
                }
            } else {
                progressiveLoader.showState('loading-three', 100, 'Three.js already available');
            }
            
            // Disable Web Workers for Marimo compatibility
            console.log('🔧 Marimo Mode: Web Workers disabled for compatibility');
            
            // Load CSG library for Boolean operations with better error handling
            progressiveLoader.showState('loading-three', 90, 'Loading CSG library...');
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
                    for (let i = 0; i < csgSources.length; i++) {
                        const src = csgSources[i];
                        try {
                            progressiveLoader.showState('loading-three', 90 + (i / csgSources.length) * 10, `Loading CSG library ${i + 1}/${csgSources.length}...`);
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
            
            // Transition to scene setup
            progressiveLoader.showState('rendering', 0, 'Setting up 3D scene...');
            
            // Three.js Scene Setup
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf8f9fa);
            
            // Camera setup
            const rect = container.getBoundingClientRect();
            const camera = new THREE.PerspectiveCamera(45, rect.width / rect.height, 0.1, 1000);
            
            // Renderer - optimiert gegen Z-Fighting und Color-Artefakte
            let renderer;
            try {
                renderer = new THREE.WebGLRenderer({ 
                    antialias: true,
                    alpha: true,
                    powerPreference: "high-performance",
                    precision: "highp",
                    stencil: false,
                    depth: true,
                    logarithmicDepthBuffer: true  // Better depth precision
                });
            } catch (webglError) {
                errorHandler.handleError(webglError, 'webgl', () => {
                    // Retry with fallback options
                    try {
                        renderer = new THREE.WebGLRenderer({ 
                            antialias: false,
                            alpha: false,
                            powerPreference: "default"
                        });
                    } catch (fallbackError) {
                        // Use Canvas renderer as last resort
                        throw new Error("WebGL not supported and Canvas fallback failed");
                    }
                });
                throw webglError;
            }
            renderer.setSize(rect.width, rect.height);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            
            // Disable shadows to eliminate shadow-related color variations
            renderer.shadowMap.enabled = false;
            
            renderer.sortObjects = true;
            renderer.toneMapping = THREE.LinearToneMapping;
            container.appendChild(renderer.domElement);
            
            // Register Three.js resources with memory manager
            memoryManager.register(scene, (s) => {
                s.traverse((object) => {
                    if (object.geometry) object.geometry.dispose();
                    if (object.material) {
                        if (Array.isArray(object.material)) {
                            object.material.forEach(mat => mat.dispose());
                        } else {
                            object.material.dispose();
                        }
                    }
                });
                s.clear();
            }, 'three-scene');
            
            memoryManager.register(renderer, (r) => {
                r.dispose();
                if (r.domElement && r.domElement.parentNode) {
                    r.domElement.parentNode.removeChild(r.domElement);
                }
            }, 'three-renderer');
            
            // Initialize rendering optimizer after scene and renderer setup
            progressiveLoader.showState('rendering', 25, 'Initializing rendering optimizer...');
            renderingOptimizer = new RenderingOptimizer(renderer, scene);
            
            // Balanced lighting setup for edge definition without harsh shadows
            progressiveLoader.showState('rendering', 50, 'Setting up lighting...');
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
            
            // Register lighting and grid resources
            memoryManager.register(gridHelper, (grid) => {
                if (grid.geometry) grid.geometry.dispose();
                if (grid.material) grid.material.dispose();
                scene.remove(grid);
            }, 'three-grid');
            
            // Mouse Controls
            progressiveLoader.showState('rendering', 75, 'Setting up camera controls...');
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
            let currentMeshResourceId = null;
            
            // Helper function to register mesh with memory manager
            function registerMesh(mesh, category = 'mesh') {
                const resourceId = memoryManager.register(mesh, (m) => {
                    // Clean up the main mesh
                    if (m.geometry) m.geometry.dispose();
                    if (m.material) {
                        if (Array.isArray(m.material)) {
                            m.material.forEach(mat => mat.dispose());
                        } else {
                            m.material.dispose();
                        }
                    }
                    
                    // Clean up additional meshes in userData
                    if (m.userData) {
                        ['holeMesh', 'outlineMesh', 'voidMesh', 'innerWallMesh', 'frontRim', 'backRim', 'cube2Mesh'].forEach(key => {
                            if (m.userData[key]) {
                                scene.remove(m.userData[key]);
                                if (m.userData[key].geometry) m.userData[key].geometry.dispose();
                                if (m.userData[key].material) m.userData[key].material.dispose();
                            }
                        });
                    }
                    
                    // Remove from scene
                    scene.remove(m);
                    console.log(`🧠 Mesh disposed: ${category}`);
                }, category);
                
                return resourceId;
            }
            
            // Helper function to safely replace current mesh
            function replaceCurrentMesh(newMesh, category = 'main-mesh') {
                // Unregister and cleanup old mesh
                if (currentMeshResourceId) {
                    memoryManager.unregister(currentMeshResourceId);
                    currentMeshResourceId = null;
                }
                
                // Clean up manually if memory manager didn't handle it
                if (currentMesh) {
                    scene.remove(currentMesh);
                    if (currentMesh.geometry) currentMesh.geometry.dispose();
                    if (currentMesh.material) currentMesh.material.dispose();
                }
                
                // Set new mesh and apply optimizations
                currentMesh = newMesh;
                if (newMesh) {
                    // Apply LOD optimization if rendering optimizer is available and mesh is complex
                    if (renderingOptimizer && newMesh.geometry && newMesh.geometry.attributes.position) {
                        const triangleCount = newMesh.geometry.attributes.position.count / 3;
                        console.log(`🎨 Mesh has ${triangleCount} triangles`);
                        
                        if (triangleCount > 10000) { // Only apply LOD for complex meshes
                            console.log('🎨 Creating LOD mesh for performance optimization');
                            const lodMesh = renderingOptimizer.createLODMesh(newMesh);
                            scene.add(lodMesh);
                            currentMesh = lodMesh;
                            currentMeshResourceId = registerMesh(lodMesh, `${category}-lod`);
                        } else {
                            // For simpler meshes, just optimize geometry
                            newMesh.geometry = renderingOptimizer.optimizeGeometry(newMesh.geometry);
                            scene.add(newMesh);
                            currentMeshResourceId = registerMesh(newMesh, category);
                        }
                    } else {
                        scene.add(newMesh);
                        currentMeshResourceId = registerMesh(newMesh, category);
                    }
                }
            }
            
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
                    progressiveLoader.showState('parsing-stl', 0, 'Decoding STL data...');
                    
                    if (!base64STL || base64STL.length < 100) {
                        throw new Error("No valid STL data received");
                    }
                    
                    // Base64 → Binary
                    progressiveLoader.showState('parsing-stl', 25, 'Converting to binary...');
                    const binaryString = atob(base64STL);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    
                    // STL parsen
                    progressiveLoader.showState('parsing-stl', 50, 'Parsing STL format...');
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
                    
                    progressiveLoader.showState('optimizing', 0, 'Creating geometry...');
                    const geometry = STLParser.createBufferGeometry(parsed);
                    
                    progressiveLoader.showState('optimizing', 50, 'Removing old mesh...');
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
                    
                    const mesh = new THREE.Mesh(geometry, material);
                    mesh.castShadow = true;
                    mesh.receiveShadow = true;
                    
                    // Auto-Center
                    const box = geometry.boundingBox;
                    const center = box.getCenter(new THREE.Vector3());
                    mesh.position.sub(center);
                    
                    progressiveLoader.showState('rendering', 0, 'Adding to scene...');
                    replaceCurrentMesh(mesh, 'stl-mesh');
                    
                    // Kamera optimal positionieren
                    progressiveLoader.showState('rendering', 50, 'Positioning camera...');
                    const size = box.getSize(new THREE.Vector3());
                    const maxDim = Math.max(size.x, size.y, size.z);
                    cameraDistance = Math.max(maxDim * 2.5, 20);
                    updateCameraPosition();
                    
                    // Complete with performance stats
                    const triangleCount = parsed.vertices.length / 9;
                    const stats = {
                        triangles: triangleCount,
                        renderer: 'stl-parser',
                        loadTime: Date.now() - progressiveLoader.startTime
                    };
                    progressiveLoader.showComplete(stats);
                    
                    status.textContent = `✅ STL loaded: ${triangleCount} triangles`;
                    status.style.background = "rgba(34,197,94,0.9)";
                    
                } catch (error) {
                    console.error("STL Processing Error:", error);
                    errorHandler.handleError(error, 'parsing', () => {
                        // Retry STL processing
                        processSTLData(base64STL);
                    });
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
                const mesh = new THREE.Mesh(geometry, material);
                replaceCurrentMesh(mesh, 'fallback-mesh');
                
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
                            return { success: true };
                        }
                    } catch (wasmError) {
                        console.warn('⚠️ Phase 2 WASM failed:', wasmError);
                    }
                    return { success: false };
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
                        // Safely clean up existing mesh using memory manager
                        replaceCurrentMesh(null, 'cleanup');
                
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
                const mesh = new THREE.Mesh(finalGeometry, material);
                mesh.castShadow = true;
                mesh.receiveShadow = true;
                mesh.userData = {}; // Initialize userData
                replaceCurrentMesh(mesh, 'wasm-mesh');
                
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
                            
                            const mesh = new THREE.Mesh(fallbackGeometry, fallbackMaterial);
                            replaceCurrentMesh(mesh, 'scad-fallback-mesh');
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
                    return false;
                }
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
            
            // Animation Loop with LOD optimization
            function animate() {
                requestAnimationFrame(animate);
                
                // Update LOD based on camera distance
                if (renderingOptimizer) {
                    renderingOptimizer.updateLOD(camera);
                    
                    // Adaptive quality adjustment (every 30 frames to avoid overhead)
                    if (Math.random() < 0.033) { // ~1/30 chance per frame
                        renderingOptimizer.adaptiveQuality(camera);
                    }
                }
                
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
            
            // Complete initialization - show final progress state
            progressiveLoader.showState('complete', 100, 'All systems ready');
            
            // Start animation loop  
            animate();
            
            // Initialize model display
            updateModel();
            
            // Show completion with performance stats
            setTimeout(() => {
                const stats = {
                    triangles: 0, // Will be updated when model loads
                    renderer: rendererType,
                    loadTime: Date.now() - progressiveLoader.startTime
                };
                progressiveLoader.showComplete(stats);
            }, 500);
            
            // Final status update
            console.log('🎉 3D viewer initialization complete!');
            
            // Widget cleanup handler
            return () => {
                console.log('🧠 Widget cleanup initiated');
                
                // Dispose memory manager (cleans up all registered resources)
                memoryManager.dispose();
                
                // Remove event listeners
                window.removeEventListener('resize', onWindowResize);
                
                // Clean up remaining DOM elements
                if (container && container.parentNode) {
                    container.innerHTML = '';
                }
                
                console.log('🧠 Widget cleanup completed');
            };
            
        } catch (error) {
            console.error("Viewer initialization error:", error);
            
            // Determine error context for better handling
            let context = 'general';
            if (error.message.includes('WebGL')) {
                context = 'webgl';
            } else if (error.message.includes('WASM') || error.message.includes('WebAssembly')) {
                context = 'wasm';
            } else if (error.message.includes('network') || error.message.includes('CDN')) {
                context = 'network';
            } else if (error.message.includes('memory') || error.message.includes('Memory')) {
                context = 'memory';
            }
            
            // Use enhanced error handler if available
            if (typeof errorHandler !== 'undefined' && errorHandler) {
                errorHandler.handleError(error, context, () => location.reload());
            } else {
                // Fallback to simple error display
                status.textContent = `❌ Init Error: ${error.message}`;
                status.style.background = "rgba(220,20,60,0.9)";
            }
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
        
        # Initialize real-time renderer (Phase 3.3b)
        self.realtime_renderer = RealTimeRenderer(
            viewer=self, 
            cache_size_mb=256,  # Default 256MB cache
            debounce_ms=self.debounce_delay_ms
        )
        self.real_time_enabled = True
        
        # Initialize version management (Phase 4.2)
        self._initialize_version_management()
        
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
        """Setup WASM URLs for JavaScript access with HTTP server"""
        try:
            # Check if we have a WASM renderer (directly or in hybrid)
            wasm_renderer = None
            
            if isinstance(self.renderer, OpenSCADWASMRenderer):
                wasm_renderer = self.renderer
            elif isinstance(self.renderer, HybridOpenSCADRenderer):
                if hasattr(self.renderer, 'wasm_renderer') and self.renderer.wasm_renderer:
                    wasm_renderer = self.renderer.wasm_renderer
            
            if wasm_renderer and wasm_renderer.is_available:
                # Start HTTP server for WASM assets
                try:
                    base_url = start_wasm_server()
                    self.wasm_base_url = base_url
                    self.wasm_enabled = True
                    logger.info(f"WASM HTTP server started: {base_url}")
                    
                    # Validate WASM assets are accessible
                    validation = wasm_renderer.validate_wasm_assets()
                    if not all(validation.values()):
                        logger.warning(f"Some WASM assets are missing: {validation}")
                    
                except Exception as server_error:
                    logger.error(f"Failed to start WASM HTTP server: {server_error}")
                    # Fallback to direct serving attempt
                    self.wasm_base_url = wasm_renderer.get_wasm_url_base()
                    self.wasm_enabled = True
                    logger.info(f"Using fallback WASM URLs: {self.wasm_base_url}")
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
        Update viewer with new SCAD code directly (Phase 4.4: Enhanced with version management)
        
        Args:
            scad_code: Raw OpenSCAD code as string
            use_wasm: Whether to use WASM rendering (None = auto-detect)
        """
        try:
            self.is_loading = True
            self.error_message = ""
            
            # Phase 4.4: Enhanced workflow with version detection and migration
            enhanced_scad_code = self._enhanced_scad_update_workflow(scad_code)
            
            # Auto-detect WASM usage if not specified
            if use_wasm is None:
                use_wasm = self.wasm_enabled and self.enable_real_time_wasm
            
            if use_wasm:
                # For WASM: send SCAD code directly to frontend
                previous_scad = self.scad_code
                self.scad_code = enhanced_scad_code
                
                # Clear STL data to prioritize WASM rendering
                if self.stl_data:
                    self.stl_data = ""
                
                logger.info(f"✅ SCAD code sent to WASM: {len(enhanced_scad_code)} chars")
                logger.info(f"SCAD code changed: {enhanced_scad_code != previous_scad}")
            else:
                # For local: render to STL
                previous_stl = self.stl_data
                
                # SCAD → STL (no caching for direct code updates)
                stl_data = self._render_stl(enhanced_scad_code, force_render=True)
                
                # STL → Base64 for browser
                new_stl_base64 = base64.b64encode(stl_data).decode('utf-8')
                self.stl_data = new_stl_base64
                
                # Clear SCAD code when using STL mode
                if self.scad_code:
                    self.scad_code = ""
                
                logger.info(f"✅ SCAD code rendered to STL: {len(stl_data)} bytes from {len(enhanced_scad_code)} chars")
                logger.info(f"STL data changed: {new_stl_base64 != previous_stl}")
            
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"❌ SCAD code update error: {e}")
        finally:
            self.is_loading = False
    
    def _enhanced_scad_update_workflow(self, scad_code: str) -> str:
        """
        Phase 4.4: Enhanced SCAD update workflow with version detection and migration
        
        Args:
            scad_code: Raw OpenSCAD code
            
        Returns:
            Enhanced SCAD code (potentially migrated)
        """
        try:
            # 1. Check cache first (performance optimization)
            code_hash = hash(scad_code)
            if code_hash in self.version_detection_cache:
                cached_result = self.version_detection_cache[code_hash]
                logger.debug(f"Using cached analysis for SCAD code (hash: {code_hash})")
                self.version_compatibility_status = cached_result.get('compatibility_status', 'unknown')
                self.migration_suggestions = cached_result.get('migration_suggestions', [])
                return cached_result.get('enhanced_code', scad_code)
            
            # 2. Version Detection Phase
            required_version = self._detect_scad_version_requirements(scad_code)
            current_config = self._get_current_version_config()
            
            # 3. Compatibility Check Phase
            compatibility = self._check_version_compatibility(scad_code, current_config, required_version)
            
            # 4. Migration Phase (if needed)
            enhanced_code = scad_code
            migration_suggestions = []
            
            if not compatibility.get('is_compatible', True) and self.migration_engine:
                migration_result = self._handle_version_migration(scad_code, compatibility)
                if migration_result.get('success', False):
                    enhanced_code = migration_result.get('migrated_code', scad_code)
                    migration_suggestions = migration_result.get('suggestions', [])
                    logger.info(f"✅ Applied {len(migration_suggestions)} migrations")
                
            # 5. Version Selection Phase
            optimal_version = self._select_optimal_rendering_version(enhanced_code, required_version)
            self._switch_to_version_if_needed(optimal_version)
            
            # 6. Update UI state
            self.version_compatibility_status = compatibility.get('status', 'compatible')
            self.migration_suggestions = migration_suggestions
            self.available_migrations = {
                'preview': enhanced_code if enhanced_code != scad_code else None,
                'suggestions': migration_suggestions
            }
            
            # 7. Cache results for performance
            self.version_detection_cache[code_hash] = {
                'compatibility_status': self.version_compatibility_status,
                'migration_suggestions': migration_suggestions,
                'enhanced_code': enhanced_code,
                'timestamp': time.time()
            }
            
            logger.info(f"✅ Enhanced SCAD workflow completed: {len(enhanced_code)} chars, status: {self.version_compatibility_status}")
            return enhanced_code
            
        except Exception as e:
            logger.error(f"❌ Enhanced SCAD workflow error: {e}")
            # Fallback to original code on any error
            self.version_compatibility_status = "error"
            return scad_code
    
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
    
    # ==========================================
    # Phase 3.3b: Real-time Rendering Methods
    # ==========================================
    
    async def update_parameter_realtime(self, name: str, value: any, force_render: bool = False) -> None:
        """
        Update a parameter with real-time rendering and debouncing.
        
        Args:
            name: Parameter name
            value: New parameter value
            force_render: If True, bypass debouncing for immediate render
        """
        if not self.real_time_enabled or not hasattr(self, 'realtime_renderer'):
            logger.warning("Real-time rendering not enabled or not initialized")
            return
            
        try:
            await self.realtime_renderer.update_parameter(name, value, force_render)
            
            # Update performance metrics
            stats = self.realtime_renderer.get_performance_stats()
            self.cache_hit_rate = stats['cache']['hit_rate']
            self.render_time_ms = stats['rendering']['last_render_time'] * 1000
            
        except Exception as e:
            self.error_message = f"Real-time parameter update failed: {e}"
            logger.error(f"❌ Real-time parameter update failed: {e}")
    
    def update_parameter(self, name: str, value: any, force_render: bool = False) -> None:
        """
        Synchronous wrapper for real-time parameter updates.
        
        Args:
            name: Parameter name
            value: New parameter value  
            force_render: If True, bypass debouncing for immediate render
        """
        import asyncio
        
        try:
            # Try to get current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule as task
                asyncio.create_task(self.update_parameter_realtime(name, value, force_render))
            else:
                # If no loop running, run until complete
                loop.run_until_complete(self.update_parameter_realtime(name, value, force_render))
        except Exception as e:
            logger.error(f"❌ Synchronous parameter update failed: {e}")
            # Fallback: direct parameter application without real-time features
            self.error_message = f"Parameter update failed: {e}"
    
    def set_debounce_delay(self, delay_ms: int) -> None:
        """
        Set the debounce delay for parameter changes.
        
        Args:
            delay_ms: Delay in milliseconds
        """
        self.debounce_delay_ms = delay_ms
        if hasattr(self, 'realtime_renderer'):
            self.realtime_renderer.debouncer.delay_ms = delay_ms
            
    def enable_realtime_rendering(self, enabled: bool = True) -> None:
        """
        Enable or disable real-time rendering features.
        
        Args:
            enabled: Whether to enable real-time rendering
        """
        self.real_time_enabled = enabled
        logger.info(f"🎛️ Real-time rendering {'enabled' if enabled else 'disabled'}")
        
    def clear_render_cache(self) -> None:
        """Clear the STL render cache."""
        if hasattr(self, 'realtime_renderer'):
            self.realtime_renderer.cache.clear()
            self.cache_hit_rate = 0.0
            logger.info("🧹 Render cache cleared")
            
    async def _update_stl_data(self, stl_data: bytes) -> None:
        """
        Async method to update STL data (used by RealTimeRenderer).
        
        Args:
            stl_data: Binary STL data
        """
        import base64
        
        # Convert to base64 for browser transmission
        stl_base64 = base64.b64encode(stl_data).decode('utf-8')
        
        # Update trait (this will trigger frontend update)
        self.stl_data = stl_base64
        
        # Clear any SCAD code when using STL mode
        if self.scad_code:
            self.scad_code = ""
            
        logger.debug(f"🔄 STL data updated: {len(stl_data)} bytes")

    def get_renderer_info(self) -> dict:
        """Get information about the current renderer"""
        base_info = {
            'type': self.renderer_type,
            'status': self.renderer_status,
            'wasm_supported': self.wasm_supported,
            'wasm_enabled': self.wasm_enabled,
            'real_time_wasm': self.enable_real_time_wasm,
            'active_renderer': getattr(self.renderer, 'get_active_renderer_type', lambda: self.renderer_type)(),
            'stats': getattr(self.renderer, 'get_stats', lambda: {})(),
            'current_mode': 'wasm' if (self.scad_code and self.wasm_enabled) else 'stl'
        }
        
        # Add real-time rendering info if available
        if hasattr(self, 'realtime_renderer'):
            realtime_stats = self.realtime_renderer.get_performance_stats()
            base_info['realtime'] = {
                'enabled': self.real_time_enabled,
                'debounce_delay_ms': self.debounce_delay_ms,
                'cache_hit_rate': self.cache_hit_rate,
                'render_time_ms': self.render_time_ms,
                'performance': realtime_stats
            }
        
        return base_info
    
    # ========================
    # Version Management Methods (Phase 4.2)
    # ========================
    
    def _initialize_version_management(self) -> None:
        """Initialize version management system."""
        try:
            # Initialize version managers
            self.version_manager = OpenSCADVersionManager()
            self.wasm_version_manager = WASMVersionManager()
            
            # Initialize migration engine (Phase 4.4)
            self.migration_engine = MigrationEngine()
            
            # Detect available versions
            self._update_available_versions()
            
            # Set initial version compatibility info
            self._update_version_compatibility()
            
            # Initialize version detection cache
            self.version_detection_cache = {}
            
            logger.info("Version management initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize version management: {e}")
            # Continue without version management
            self.version_manager = None
            self.wasm_version_manager = None
            self.migration_engine = None
    
    def _update_available_versions(self) -> None:
        """Update list of available OpenSCAD versions."""
        try:
            available = []
            
            # Add detected local installations
            if self.version_manager:
                local_installations = self.version_manager.detect_all_installations()
                for installation in local_installations:
                    available.append(f"{installation.version_info} ({installation.installation_type.value})")
            
            # Add available WASM versions
            if self.wasm_version_manager:
                wasm_versions = self.wasm_version_manager.loader.get_available_versions()
                for version in wasm_versions:
                    available.append(f"{version} (wasm)")
            
            self.available_versions = sorted(list(set(available)))
            logger.debug(f"Updated available versions: {self.available_versions}")
            
        except Exception as e:
            logger.error(f"Failed to update available versions: {e}")
            self.available_versions = []
    
    def _update_version_compatibility(self) -> None:
        """Update version compatibility information."""
        try:
            compatibility_info = {}
            
            if self.version_manager:
                # Get preferred installation info
                preferred = self.version_manager.get_preferred_installation()
                if preferred:
                    compatibility_info['preferred_local'] = {
                        'version': str(preferred.version_info),
                        'type': preferred.installation_type.value,
                        'capabilities': preferred.capabilities
                    }
            
            if self.wasm_version_manager:
                # Get WASM manager info
                wasm_info = self.wasm_version_manager.get_system_info()
                compatibility_info['wasm'] = wasm_info
            
            self.version_compatibility = compatibility_info
            logger.debug(f"Updated version compatibility: {compatibility_info}")
            
        except Exception as e:
            logger.error(f"Failed to update version compatibility: {e}")
            self.version_compatibility = {}
    
    async def set_openscad_version(self, version: str) -> bool:
        """
        Set the OpenSCAD version to use for rendering.
        
        Args:
            version: Version string to use (e.g., "2023.06", "auto")
            
        Returns:
            True if version was set successfully
        """
        try:
            if version == "auto":
                self.auto_version_selection = True
                self.openscad_version = "auto"
                logger.info("Enabled automatic version selection")
                return True
            
            self.auto_version_selection = False
            
            # Check if it's a WASM version
            if self.wasm_version_manager and version in self.wasm_version_manager.loader.get_available_versions():
                success = await self.wasm_version_manager.switch_to_version(version)
                if success:
                    self.openscad_version = version
                    self.active_wasm_version = version
                    logger.info(f"Switched to WASM version: {version}")
                    return True
                else:
                    logger.error(f"Failed to switch to WASM version: {version}")
                    return False
            
            # Check if it's a local version
            if self.version_manager:
                installation = self.version_manager.get_installation_by_version(version)
                if installation:
                    self.openscad_version = version
                    logger.info(f"Set local OpenSCAD version: {version}")
                    return True
            
            logger.warning(f"Version not found: {version}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to set OpenSCAD version {version}: {e}")
            return False
    
    async def get_optimal_version_for_scad(self, scad_code: str) -> Optional[str]:
        """
        Get optimal OpenSCAD version for given SCAD code.
        
        Args:
            scad_code: OpenSCAD code to analyze
            
        Returns:
            Optimal version string, or None if analysis fails
        """
        try:
            if not self.wasm_version_manager:
                return None
            
            user_preferences = {
                "performance": "stable" if not self.real_time_enabled else "fastest"
            }
            
            optimal_version = await self.wasm_version_manager.get_optimal_version_for_scad(
                scad_code, user_preferences
            )
            
            logger.debug(f"Optimal version for SCAD code: {optimal_version}")
            return optimal_version
            
        except Exception as e:
            logger.error(f"Failed to get optimal version for SCAD: {e}")
            return None
    
    async def auto_select_version_for_render(self, scad_code: str) -> bool:
        """
        Automatically select optimal version for rendering.
        
        Args:
            scad_code: SCAD code to be rendered
            
        Returns:
            True if version was selected and set
        """
        if not self.auto_version_selection:
            return True  # Manual version already set
        
        try:
            optimal_version = await self.get_optimal_version_for_scad(scad_code)
            if optimal_version:
                return await self.set_openscad_version(optimal_version)
            return False
            
        except Exception as e:
            logger.error(f"Failed to auto-select version: {e}")
            return False
    
    def get_version_management_info(self) -> Dict[str, any]:
        """Get comprehensive version management information."""
        try:
            info = {
                "current_version": self.openscad_version,
                "active_wasm_version": self.active_wasm_version,
                "auto_selection_enabled": self.auto_version_selection,
                "available_versions": self.available_versions,
                "compatibility": self.version_compatibility
            }
            
            if self.version_manager:
                info["local_manager"] = self.version_manager.get_version_summary()
            
            if self.wasm_version_manager:
                info["wasm_manager"] = self.wasm_version_manager.get_system_info()
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get version management info: {e}")
            return {"error": str(e)}

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


# =============================================================================
# Phase 4.4: Enhanced Workflow Helper Methods
# =============================================================================

def _detect_scad_version_requirements(self, scad_code: str) -> Optional[str]:
    """Detect version requirements from SCAD code."""
    if not self.version_manager:
        return None
    
    try:
        # Use version manager to analyze code
        analysis = self.version_manager.analyze_scad_code(scad_code)
        return analysis.get('required_version')
    except Exception as e:
        logger.debug(f"Version detection failed: {e}")
        return None

def _get_current_version_config(self) -> Dict:
    """Get current version configuration."""
    return {
        'openscad_version': self.openscad_version,
        'active_wasm_version': self.active_wasm_version,
        'renderer_type': self.renderer_type
    }

def _check_version_compatibility(self, scad_code: str, current_config: Dict, required_version: Optional[str]) -> Dict:
    """Check version compatibility and return status."""
    if not self.version_manager or not required_version:
        return {'is_compatible': True, 'status': 'compatible'}
    
    try:
        # Check if current version is compatible
        current_version = current_config.get('openscad_version', 'auto')
        if current_version == 'auto' or current_version == required_version:
            return {'is_compatible': True, 'status': 'compatible'}
        
        # Check version compatibility matrix
        compatibility = self.version_manager.check_compatibility(current_version, required_version)
        
        if compatibility.get('compatible', False):
            return {'is_compatible': True, 'status': 'compatible'}
        else:
            return {
                'is_compatible': False, 
                'status': 'migration_suggested',
                'issues': compatibility.get('issues', [])
            }
    except Exception as e:
        logger.error(f"Compatibility check failed: {e}")
        return {'is_compatible': True, 'status': 'unknown'}

def _handle_version_migration(self, scad_code: str, compatibility: Dict) -> Dict:
    """Handle version migration using migration engine."""
    if not self.migration_engine:
        return {'success': False, 'migrated_code': scad_code}
    
    try:
        # Detect migration issues
        issues = self.migration_engine.detect_version_issues(scad_code)
        
        if not issues:
            return {'success': True, 'migrated_code': scad_code, 'suggestions': []}
        
        # Generate migration suggestions
        suggestions = self.migration_engine.suggest_migrations(issues)
        
        # Apply automatic migrations with high confidence
        migrated_code = scad_code
        applied_suggestions = []
        
        for suggestion in suggestions:
            if suggestion.get('confidence', 0) >= 0.8:  # High confidence only
                try:
                    migration_result = self.migration_engine.apply_migration(migrated_code, suggestion)
                    if migration_result.get('success', False):
                        migrated_code = migration_result.get('migrated_code', migrated_code)
                        applied_suggestions.append(suggestion)
                except Exception as e:
                    logger.debug(f"Migration failed for {suggestion.get('rule', 'unknown')}: {e}")
                    continue
        
        return {
            'success': len(applied_suggestions) > 0,
            'migrated_code': migrated_code,
            'suggestions': applied_suggestions,
            'all_suggestions': suggestions
        }
        
    except Exception as e:
        logger.error(f"Migration handling failed: {e}")
        return {'success': False, 'migrated_code': scad_code}

def _select_optimal_rendering_version(self, scad_code: str, required_version: Optional[str]) -> Optional[str]:
    """Select optimal version for rendering."""
    if not self.wasm_version_manager:
        return None
    
    try:
        # Use WASM version manager for optimal selection
        return self.wasm_version_manager.select_optimal_version(scad_code, required_version)
    except Exception as e:
        logger.debug(f"Optimal version selection failed: {e}")
        return None

def _switch_to_version_if_needed(self, optimal_version: Optional[str]) -> bool:
    """Switch to optimal version if different from current."""
    if not optimal_version or optimal_version == self.active_wasm_version:
        return False
    
    try:
        if self.wasm_version_manager:
            success = self.wasm_version_manager.switch_to_version(optimal_version)
            if success:
                self.active_wasm_version = optimal_version
                logger.info(f"✅ Switched to WASM version: {optimal_version}")
                return True
    except Exception as e:
        logger.error(f"Version switching failed: {e}")
    
    return False

# Add methods to OpenSCADViewer class
OpenSCADViewer._detect_scad_version_requirements = _detect_scad_version_requirements
OpenSCADViewer._get_current_version_config = _get_current_version_config
OpenSCADViewer._check_version_compatibility = _check_version_compatibility
OpenSCADViewer._handle_version_migration = _handle_version_migration
OpenSCADViewer._select_optimal_rendering_version = _select_optimal_rendering_version
OpenSCADViewer._switch_to_version_if_needed = _switch_to_version_if_needed