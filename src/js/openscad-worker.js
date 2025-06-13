/**
 * OpenSCAD Web Worker
 * 
 * Provides non-blocking OpenSCAD WASM rendering in a web worker
 * to prevent UI freezing during complex model generation.
 */

// Import the WASM loader in worker context
importScripts('./wasm-loader.js');

class OpenSCADWorker {
    constructor() {
        this.isInitialized = false;
        this.wasmLoader = null;
        this.renderer = null;
    }

    /**
     * Initialize the OpenSCAD WASM environment in worker
     */
    async initialize(options = {}) {
        try {
            console.log('Worker: Initializing OpenSCAD WASM...');
            
            // Create WASM loader instance
            this.wasmLoader = new OpenSCADWASMLoader();
            
            // Initialize with options
            const wasmInstance = await this.wasmLoader.initialize(options);
            
            // Create renderer
            this.renderer = new OpenSCADWASMRenderer();
            await this.renderer.initialize();
            
            this.isInitialized = true;
            console.log('Worker: OpenSCAD WASM initialized successfully');
            
            return {
                success: true,
                message: 'OpenSCAD WASM initialized successfully',
                capabilities: this.renderer.getCapabilities()
            };
            
        } catch (error) {
            console.error('Worker: Failed to initialize OpenSCAD WASM:', error);
            return {
                success: false,
                error: error.message,
                stack: error.stack
            };
        }
    }

    /**
     * Render OpenSCAD code to STL
     */
    async renderToSTL(scadCode, options = {}) {
        if (!this.isInitialized || !this.renderer) {
            return {
                success: false,
                error: 'Worker not initialized'
            };
        }

        try {
            console.log('Worker: Starting SCAD rendering...');
            const startTime = performance.now();
            
            // Render with the WASM renderer
            const stlData = await this.renderer.renderToSTL(scadCode, options);
            
            const renderTime = performance.now() - startTime;
            console.log(`Worker: Rendering completed in ${renderTime.toFixed(2)}ms`);
            
            return {
                success: true,
                stlData: stlData,
                renderTime: renderTime,
                size: stlData.length
            };
            
        } catch (error) {
            console.error('Worker: Rendering failed:', error);
            return {
                success: false,
                error: error.message,
                stack: error.stack
            };
        }
    }

    /**
     * Get worker status and statistics
     */
    async getStatus() {
        const loaderStatus = this.wasmLoader ? await this.wasmLoader.getStatus() : null;
        const rendererStats = this.renderer ? this.renderer.getStats() : null;
        
        return {
            isInitialized: this.isInitialized,
            hasLoader: this.wasmLoader !== null,
            hasRenderer: this.renderer !== null,
            loaderStatus: loaderStatus,
            rendererStats: rendererStats,
            memoryUsage: this.getMemoryUsage()
        };
    }

    /**
     * Get memory usage information
     */
    getMemoryUsage() {
        if (typeof performance !== 'undefined' && performance.memory) {
            return {
                used: performance.memory.usedJSHeapSize,
                total: performance.memory.totalJSHeapSize,
                limit: performance.memory.jsHeapSizeLimit
            };
        }
        return null;
    }

    /**
     * Clear caches and reset worker state
     */
    async reset() {
        try {
            if (this.wasmLoader) {
                await this.wasmLoader.clearCache();
                this.wasmLoader.reset();
            }
            
            if (this.renderer) {
                this.renderer.reset();
            }
            
            this.isInitialized = false;
            console.log('Worker: Reset completed');
            
            return { success: true };
            
        } catch (error) {
            console.error('Worker: Reset failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
}

// Create worker instance
const worker = new OpenSCADWorker();

// Message handler for communication with main thread
self.onmessage = async function(event) {
    const { id, command, data } = event.data;
    
    try {
        let result;
        
        switch (command) {
        case 'initialize':
            result = await worker.initialize(data);
            break;
                
        case 'render':
            result = await worker.renderToSTL(data.scadCode, data.options);
            break;
                
        case 'status':
            result = await worker.getStatus();
            break;
                
        case 'reset':
            result = await worker.reset();
            break;
                
        default:
            result = {
                success: false,
                error: `Unknown command: ${command}`
            };
        }
        
        // Send result back to main thread
        self.postMessage({
            id: id,
            success: true,
            result: result
        });
        
    } catch (error) {
        console.error('Worker: Message handling error:', error);
        
        // Send error back to main thread
        self.postMessage({
            id: id,
            success: false,
            error: error.message,
            stack: error.stack
        });
    }
};

// Handle worker errors
self.onerror = function(error) {
    console.error('Worker: Global error:', error);
    self.postMessage({
        id: null,
        success: false,
        error: 'Worker global error: ' + error.message
    });
};

console.log('OpenSCAD Worker initialized and ready for commands');