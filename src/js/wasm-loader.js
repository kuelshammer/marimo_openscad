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
        this.wasmBasePath = '/wasm/';
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