/**
 * OpenSCAD WASM Loader Utility
 * 
 * Provides a centralized loader for OpenSCAD WebAssembly module
 * with error handling, advanced caching, and lifecycle management.
 */

import { wasmCacheManager } from './wasm-cache-manager.js';

class OpenSCADWASMLoader {
    constructor() {
        this.instance = null;
        this.isInitialized = false;
        this.isInitializing = false;
        this.initializationPromise = null;
        this.wasmBasePath = this.detectWASMBasePath();
    }

    /**
     * Detect appropriate WASM base path based on environment
     * @private
     */
    detectWASMBasePath() {
        // Phase 2: Enhanced path detection for anywidget compatibility
        
        // Check if we have a wasm_base_url from the Python backend (preferred)
        if (typeof window !== 'undefined' && window.anywidget && window.anywidget.model) {
            try {
                const wasmBaseUrl = window.anywidget.model.get('wasm_base_url');
                if (wasmBaseUrl) {
                    console.log('🔍 Phase 2: Using wasm_base_url from Python backend:', wasmBaseUrl);
                    return wasmBaseUrl.endsWith('/') ? wasmBaseUrl : wasmBaseUrl + '/';
                }
            } catch (e) {
                console.warn('🔍 Phase 2: Could not get wasm_base_url from model:', e);
            }
        }
        
        // Check if running in anywidget context
        if (typeof window !== 'undefined' && window.anywidget) {
            console.log('🔍 Phase 2: anywidget context detected');
            return '/static/wasm/';  // Package static path
        }
        
        // Check if running in marimo WASM environment
        if (typeof window !== 'undefined' && window.location.href.includes('marimo')) {
            console.log('🔍 Phase 2: Marimo environment detected');
            return './wasm/';  // Relative to marimo
        }
        
        // Check for file:// protocol (development)
        if (typeof window !== 'undefined' && window.location.protocol === 'file:') {
            console.log('🔍 Phase 2: Local file development detected');
            return './wasm/';  // Relative to HTML
        }
        
        // Default fallback
        console.log('🔍 Phase 2: Using default WASM path');
        return '/wasm/';
    }
    
    /**
     * Load WASM module with fallback paths
     * @param {string} filename - WASM filename
     * @returns {Promise<ArrayBuffer>} WASM module bytes
     * @private
     */
    async loadWASMWithFallbacks(filename) {
        const fallbackPaths = [
            `${this.wasmBasePath}${filename}`,           // Primary detected path (includes HTTP server)
            `${this.wasmBasePath}wasm/${filename}`,      // HTTP server with wasm/ prefix
            `/static/wasm/${filename}`,                  // Package static
            `./wasm/${filename}`,                        // Relative
            `../src/marimo_openscad/wasm/${filename}`,   // Development
            `./dist/wasm/${filename}`,                   // Build output
            `/dist/wasm/${filename}`,                    // Deployed build
            `http://localhost:8000/wasm/${filename}`,    // Local HTTP server fallback
            `http://127.0.0.1:8000/wasm/${filename}`     // Alternative local server
        ];
        
        for (const path of fallbackPaths) {
            try {
                console.log(`🔍 Phase 2: Trying WASM path: ${path}`);
                const response = await fetch(path);
                if (response.ok) {
                    const wasmBytes = await response.arrayBuffer();
                    console.log(`✅ Phase 2: WASM loaded from: ${path} (${wasmBytes.byteLength} bytes)`);
                    return wasmBytes;
                }
            } catch (error) {
                console.warn(`❌ Phase 2: WASM path failed: ${path} - ${error.message}`);
                continue;
            }
        }
        
        throw new Error(`Phase 2: All WASM loading paths failed for ${filename}`);
    }

    /**
     * Initialize the OpenSCAD WASM module
     * @param {Object} options - Configuration options
     * @param {string} options.basePath - Base path for WASM files
     * @param {boolean} options.includeFonts - Whether to load fonts
     * @param {boolean} options.includeMCAD - Whether to load MCAD library
     * @returns {Promise<Object>} The initialized OpenSCAD instance
     */
    async initialize(options = {}) {
        // Return existing promise if already initializing
        if (this.isInitializing) {
            return this.initializationPromise;
        }

        // Return cached instance if already initialized
        if (this.isInitialized && this.instance) {
            return this.instance;
        }

        this.isInitializing = true;
        
        this.initializationPromise = this._doInitialize(options);
        
        try {
            const instance = await this.initializationPromise;
            this.instance = instance;
            this.isInitialized = true;
            this.isInitializing = false;
            return instance;
        } catch (error) {
            this.isInitializing = false;
            this.initializationPromise = null;
            throw error;
        }
    }

    /**
     * Internal initialization logic
     * @private
     */
    async _doInitialize(options) {
        const {
            basePath = this.wasmBasePath,
            includeFonts = true,
            includeMCAD = true
        } = options;

        try {
            // Dynamic import of OpenSCAD module
            const OpenSCADModule = await this._loadOpenSCADModule(basePath);
            
            // Initialize the WASM instance
            console.log('Initializing OpenSCAD WASM instance...');
            const instance = await OpenSCADModule({
                noInitialRun: true,
                locateFile: (path, prefix) => {
                    // Ensure correct path resolution for WASM files
                    if (path.endsWith('.wasm')) {
                        return basePath + path;
                    }
                    return prefix + path;
                }
            });

            // Add optional libraries
            if (includeFonts) {
                await this._loadFonts(instance, basePath);
            }

            if (includeMCAD) {
                await this._loadMCAD(instance, basePath);
            }

            console.log('OpenSCAD WASM instance initialized successfully');
            return instance;

        } catch (error) {
            console.error('Failed to initialize OpenSCAD WASM:', error);
            throw new Error(`OpenSCAD WASM initialization failed: ${error.message}`);
        }
    }

    /**
     * Load the main OpenSCAD module with caching
     * @private
     */
    async _loadOpenSCADModule(basePath) {
        try {
            // Initialize cache manager
            await wasmCacheManager.initialize();
            
            // Load the wrapper module with caching
            const response = await wasmCacheManager.fetchWithCache(basePath + 'openscad.js');
            if (!response.ok) {
                throw new Error(`Failed to fetch openscad.js: ${response.status}`);
            }
            
            const moduleText = await response.text();
            
            // Create a blob URL for the module
            const blob = new Blob([moduleText], { type: 'application/javascript' });
            const moduleUrl = URL.createObjectURL(blob);
            
            // Import the module
            const module = await import(moduleUrl);
            
            // Clean up the blob URL
            URL.revokeObjectURL(moduleUrl);
            
            console.log('OpenSCAD module loaded successfully (with caching)');
            return module.default || module;
        } catch (error) {
            console.error('Failed to load OpenSCAD module:', error);
            throw error;
        }
    }

    /**
     * Load fonts library with caching
     * @private
     */
    async _loadFonts(instance, basePath) {
        try {
            const response = await wasmCacheManager.fetchWithCache(basePath + 'openscad.fonts.js');
            if (!response.ok) {
                console.warn('Fonts library not available, continuing without fonts');
                return;
            }
            
            const fontsText = await response.text();
            const blob = new Blob([fontsText], { type: 'application/javascript' });
            const fontsUrl = URL.createObjectURL(blob);
            
            const fontsModule = await import(fontsUrl);
            URL.revokeObjectURL(fontsUrl);
            
            if (fontsModule.addFonts) {
                await fontsModule.addFonts(instance);
                console.log('Fonts loaded successfully (cached)');
            }
        } catch (error) {
            console.warn('Failed to load fonts, continuing without:', error.message);
        }
    }

    /**
     * Load MCAD library with caching
     * @private
     */
    async _loadMCAD(instance, basePath) {
        try {
            const response = await wasmCacheManager.fetchWithCache(basePath + 'openscad.mcad.js');
            if (!response.ok) {
                console.warn('MCAD library not available, continuing without MCAD');
                return;
            }
            
            const mcadText = await response.text();
            const blob = new Blob([mcadText], { type: 'application/javascript' });
            const mcadUrl = URL.createObjectURL(blob);
            
            const mcadModule = await import(mcadUrl);
            URL.revokeObjectURL(mcadUrl);
            
            if (mcadModule.addMCAD) {
                await mcadModule.addMCAD(instance);
                console.log('MCAD library loaded successfully (cached)');
            }
        } catch (error) {
            console.warn('Failed to load MCAD library, continuing without:', error.message);
        }
    }

    /**
     * Get the current instance (if initialized)
     * @returns {Object|null} The OpenSCAD instance or null
     */
    getInstance() {
        return this.instance;
    }

    /**
     * Check if the loader is initialized
     * @returns {boolean} True if initialized
     */
    isReady() {
        return this.isInitialized && this.instance !== null;
    }

    /**
     * Reset the loader (for testing or re-initialization)
     */
    reset() {
        this.instance = null;
        this.isInitialized = false;
        this.isInitializing = false;
        this.initializationPromise = null;
    }

    /**
     * Get initialization status including cache information
     * @returns {Object} Status information
     */
    async getStatus() {
        const cacheStats = await wasmCacheManager.getCacheStats();
        
        return {
            isInitialized: this.isInitialized,
            isInitializing: this.isInitializing,
            hasInstance: this.instance !== null,
            cache: cacheStats
        };
    }

    /**
     * Preload WASM resources for faster initialization
     * @returns {Promise<void>}
     */
    async preloadResources() {
        const resources = [
            'openscad.js',
            'openscad.wasm.js',
            'openscad.wasm',
            'openscad.fonts.js',
            'openscad.mcad.js'
        ];

        const basePath = this.wasmBasePath;
        const urls = resources.map(resource => basePath + resource);
        
        console.log('Preloading WASM resources for faster initialization...');
        await wasmCacheManager.preloadResources(urls);
        console.log('WASM resources preloaded successfully');
    }

    /**
     * Clear WASM cache
     * @returns {Promise<void>}
     */
    async clearCache() {
        await wasmCacheManager.clearCache();
        console.log('WASM cache cleared');
    }
}

// Export singleton instance
export const wasmLoader = new OpenSCADWASMLoader();
export default wasmLoader;