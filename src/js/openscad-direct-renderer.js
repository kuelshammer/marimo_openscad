/**
 * OpenSCAD Direct Renderer - WASM-safe Main Thread Implementation
 * 
 * Replaces the Web Worker-based approach with direct main thread execution
 * for compatibility with both local Marimo and Marimo WASM environments.
 */

import { OpenSCADWASMRenderer } from './openscad-wasm-renderer.js';

/**
 * Direct WASM renderer that works in main thread
 * Replaces the worker-based approach for WASM compatibility
 */
export class OpenSCADDirectRenderer {
    constructor(options = {}) {
        this.options = {
            enableManifold: true,
            outputFormat: 'binstl',
            timeout: 30000,
            ...options
        };
        
        this.isInitialized = false;
        this.wasmRenderer = null;
        this.initializationPromise = null;
        this.renderCount = 0;
    }

    /**
     * Initialize the WASM renderer directly in main thread
     */
    async initialize() {
        if (this.initializationPromise) {
            return this.initializationPromise;
        }

        this.initializationPromise = this._doInitialize();
        return this.initializationPromise;
    }

    /**
     * Internal initialization logic
     */
    async _doInitialize() {
        try {
            console.log('🚀 Initializing Direct WASM Renderer...');
            
            // Create WASM renderer instance
            this.wasmRenderer = new OpenSCADWASMRenderer(this.options);
            
            // Initialize the WASM environment
            await this.wasmRenderer.initialize();
            
            this.isInitialized = true;
            console.log('✅ Direct WASM Renderer initialized successfully');
            
            return {
                success: true,
                message: 'Direct WASM renderer initialized',
                capabilities: OpenSCADWASMRenderer.getCapabilities()
            };
            
        } catch (error) {
            console.error('❌ Failed to initialize Direct WASM Renderer:', error);
            this.isInitialized = false;
            throw new Error(`Direct WASM initialization failed: ${error.message}`);
        }
    }

    /**
     * Render OpenSCAD code to STL in main thread
     */
    async renderToSTL(scadCode, options = {}) {
        if (!this.isInitialized || !this.wasmRenderer) {
            throw new Error('Direct renderer not initialized');
        }

        try {
            console.log('🔄 Starting direct WASM rendering...');
            const startTime = performance.now();
            
            // Merge options with defaults
            const renderOptions = { ...this.options, ...options };
            
            // Render directly using WASM renderer
            const stlData = await this.wasmRenderer.renderToSTL(scadCode, renderOptions);
            
            const renderTime = performance.now() - startTime;
            this.renderCount++;
            
            console.log(`✅ Direct rendering completed in ${renderTime.toFixed(2)}ms`);
            
            return {
                success: true,
                stlData: stlData,
                renderTime: renderTime,
                size: stlData.length,
                renderCount: this.renderCount,
                renderer: 'direct-wasm'
            };
            
        } catch (error) {
            console.error('❌ Direct rendering failed:', error);
            throw new Error(`Direct WASM rendering failed: ${error.message}`);
        }
    }

    /**
     * Get renderer status and statistics
     */
    getStatus() {
        return {
            isInitialized: this.isInitialized,
            hasRenderer: this.wasmRenderer !== null,
            renderCount: this.renderCount,
            rendererStats: this.wasmRenderer ? this.wasmRenderer.getStats() : null,
            capabilities: this.isInitialized ? OpenSCADWASMRenderer.getCapabilities() : null,
            memoryUsage: this._getMemoryUsage(),
            mode: 'direct-main-thread'
        };
    }

    /**
     * Get memory usage information (if available)
     */
    _getMemoryUsage() {
        if (typeof performance !== 'undefined' && performance.memory) {
            return {
                used: performance.memory.usedJSHeapSize,
                total: performance.memory.totalJSHeapSize,
                limit: performance.memory.jsHeapSizeLimit,
                percentage: (performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit) * 100
            };
        }
        return null;
    }

    /**
     * Reset the renderer
     */
    async reset() {
        try {
            if (this.wasmRenderer) {
                this.wasmRenderer.reset();
            }
            
            this.isInitialized = false;
            this.renderCount = 0;
            this.initializationPromise = null;
            
            console.log('🔄 Direct renderer reset completed');
            return { success: true };
            
        } catch (error) {
            console.error('❌ Direct renderer reset failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Check if direct rendering is supported
     */
    static isSupported() {
        return OpenSCADWASMRenderer.isSupported();
    }

    /**
     * Get renderer capabilities
     */
    static getCapabilities() {
        return {
            ...OpenSCADWASMRenderer.getCapabilities(),
            supportsWorkers: false, // Explicitly disabled for WASM compatibility
            mode: 'direct-main-thread',
            environment: 'wasm-safe'
        };
    }
}

/**
 * Factory function to create the best available renderer
 * Automatically selects direct renderer for WASM compatibility
 */
export async function createOptimalRenderer(options = {}) {
    console.log('🏭 Creating optimal WASM-safe renderer...');
    
    // Always use direct renderer for WASM compatibility
    const renderer = new OpenSCADDirectRenderer(options);
    await renderer.initialize();
    
    console.log('✅ Direct renderer created and initialized');
    return renderer;
}

/**
 * Utility to detect WASM environment constraints
 */
export function detectEnvironmentConstraints() {
    return {
        hasWebWorkers: typeof Worker !== 'undefined',
        hasWebAssembly: typeof WebAssembly !== 'undefined',
        hasMemoryAPI: typeof performance !== 'undefined' && performance.memory,
        recommendedMode: 'direct', // Always recommend direct for compatibility
        isWASMSafe: true
    };
}

export default OpenSCADDirectRenderer;