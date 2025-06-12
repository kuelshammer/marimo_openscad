/**
 * WASM Cache Manager
 * 
 * Manages caching of OpenSCAD WASM modules and related resources
 * for improved performance and offline capabilities.
 */

export class WASMCacheManager {
    constructor() {
        this.cache = null;
        this.cacheEnabled = this._checkCacheSupport();
        this.cacheName = 'openscad-wasm-v1';
        this.maxCacheAge = 7 * 24 * 60 * 60 * 1000; // 7 days
        this.initPromise = null;
    }

    /**
     * Check if caching is supported in the current environment
     * @private
     */
    _checkCacheSupport() {
        return typeof caches !== 'undefined' && 
               typeof Cache !== 'undefined' &&
               typeof Request !== 'undefined';
    }

    /**
     * Initialize the cache manager
     * @returns {Promise<void>}
     */
    async initialize() {
        if (this.initPromise) {
            return this.initPromise;
        }

        this.initPromise = this._doInitialize();
        return this.initPromise;
    }

    /**
     * Internal initialization logic
     * @private
     */
    async _doInitialize() {
        if (!this.cacheEnabled) {
            console.warn('WASM Cache: Cache API not supported, caching disabled');
            return;
        }

        try {
            this.cache = await caches.open(this.cacheName);
            console.log('WASM Cache: Cache initialized successfully');
            
            // Clean up old entries on initialization
            await this._cleanupExpiredEntries();
            
        } catch (error) {
            console.warn('WASM Cache: Failed to initialize cache:', error);
            this.cacheEnabled = false;
        }
    }

    /**
     * Cache a WASM resource
     * @param {string} url - URL of the resource to cache
     * @param {Response} response - Response to cache
     * @returns {Promise<void>}
     */
    async cacheResource(url, response) {
        if (!this.cacheEnabled || !this.cache) {
            return;
        }

        try {
            // Clone response for caching (response can only be consumed once)
            const responseClone = response.clone();
            
            // Add cache metadata
            const cacheEntry = new Response(responseClone.body, {
                status: responseClone.status,
                statusText: responseClone.statusText,
                headers: {
                    ...Object.fromEntries(responseClone.headers.entries()),
                    'x-wasm-cache-timestamp': Date.now().toString(),
                    'x-wasm-cache-url': url
                }
            });

            await this.cache.put(url, cacheEntry);
            console.log(`WASM Cache: Cached resource ${url}`);
            
        } catch (error) {
            console.warn(`WASM Cache: Failed to cache ${url}:`, error);
        }
    }

    /**
     * Retrieve a cached resource
     * @param {string} url - URL of the resource to retrieve
     * @returns {Promise<Response|null>} Cached response or null if not found
     */
    async getCachedResource(url) {
        if (!this.cacheEnabled || !this.cache) {
            return null;
        }

        try {
            const cachedResponse = await this.cache.match(url);
            
            if (!cachedResponse) {
                return null;
            }

            // Check if cache entry is expired
            const cacheTimestamp = cachedResponse.headers.get('x-wasm-cache-timestamp');
            if (cacheTimestamp) {
                const age = Date.now() - parseInt(cacheTimestamp);
                if (age > this.maxCacheAge) {
                    console.log(`WASM Cache: Cache entry expired for ${url}, removing`);
                    await this.cache.delete(url);
                    return null;
                }
            }

            console.log(`WASM Cache: Retrieved cached resource ${url}`);
            return cachedResponse;
            
        } catch (error) {
            console.warn(`WASM Cache: Failed to retrieve cached ${url}:`, error);
            return null;
        }
    }

    /**
     * Fetch a resource with caching
     * @param {string} url - URL to fetch
     * @param {RequestInit} options - Fetch options
     * @returns {Promise<Response>} Response from cache or network
     */
    async fetchWithCache(url, options = {}) {
        await this.initialize();

        // Try to get from cache first
        const cachedResponse = await this.getCachedResource(url);
        if (cachedResponse) {
            return cachedResponse.clone();
        }

        // Fetch from network
        try {
            console.log(`WASM Cache: Fetching ${url} from network`);
            const response = await fetch(url, options);
            
            if (response.ok) {
                // Cache successful responses
                await this.cacheResource(url, response);
                return response.clone();
            }
            
            return response;
            
        } catch (error) {
            console.error(`WASM Cache: Network fetch failed for ${url}:`, error);
            throw error;
        }
    }

    /**
     * Preload critical WASM resources
     * @param {string[]} urls - URLs to preload
     * @returns {Promise<void>}
     */
    async preloadResources(urls) {
        console.log('WASM Cache: Preloading resources:', urls);
        
        const preloadPromises = urls.map(async (url) => {
            try {
                await this.fetchWithCache(url);
                console.log(`WASM Cache: Preloaded ${url}`);
            } catch (error) {
                console.warn(`WASM Cache: Failed to preload ${url}:`, error);
            }
        });

        await Promise.allSettled(preloadPromises);
    }

    /**
     * Clean up expired cache entries
     * @private
     */
    async _cleanupExpiredEntries() {
        if (!this.cache) return;

        try {
            const requests = await this.cache.keys();
            const now = Date.now();
            
            for (const request of requests) {
                const response = await this.cache.match(request);
                if (response) {
                    const timestamp = response.headers.get('x-wasm-cache-timestamp');
                    if (timestamp) {
                        const age = now - parseInt(timestamp);
                        if (age > this.maxCacheAge) {
                            await this.cache.delete(request);
                            console.log(`WASM Cache: Cleaned up expired entry ${request.url}`);
                        }
                    }
                }
            }
        } catch (error) {
            console.warn('WASM Cache: Cleanup failed:', error);
        }
    }

    /**
     * Clear all cached resources
     * @returns {Promise<void>}
     */
    async clearCache() {
        if (!this.cacheEnabled) return;

        try {
            await caches.delete(this.cacheName);
            this.cache = await caches.open(this.cacheName);
            console.log('WASM Cache: Cache cleared successfully');
        } catch (error) {
            console.warn('WASM Cache: Failed to clear cache:', error);
        }
    }

    /**
     * Get cache statistics
     * @returns {Promise<Object>} Cache statistics
     */
    async getCacheStats() {
        if (!this.cache) {
            return {
                enabled: false,
                entries: 0,
                totalSize: 0
            };
        }

        try {
            const requests = await this.cache.keys();
            let totalSize = 0;
            let validEntries = 0;
            const now = Date.now();

            for (const request of requests) {
                const response = await this.cache.match(request);
                if (response) {
                    const timestamp = response.headers.get('x-wasm-cache-timestamp');
                    if (timestamp) {
                        const age = now - parseInt(timestamp);
                        if (age <= this.maxCacheAge) {
                            validEntries++;
                            // Estimate size (not exact, but good approximation)
                            const contentLength = response.headers.get('content-length');
                            if (contentLength) {
                                totalSize += parseInt(contentLength);
                            }
                        }
                    }
                }
            }

            return {
                enabled: this.cacheEnabled,
                entries: validEntries,
                totalSize: totalSize,
                maxAge: this.maxCacheAge,
                cacheName: this.cacheName
            };
            
        } catch (error) {
            console.warn('WASM Cache: Failed to get stats:', error);
            return {
                enabled: this.cacheEnabled,
                entries: 0,
                totalSize: 0,
                error: error.message
            };
        }
    }

    /**
     * Check if a resource is cached
     * @param {string} url - URL to check
     * @returns {Promise<boolean>} True if cached and valid
     */
    async isCached(url) {
        const cachedResponse = await this.getCachedResource(url);
        return cachedResponse !== null;
    }
}

/**
 * Singleton cache manager instance
 */
export const wasmCacheManager = new WASMCacheManager();

/**
 * Utility functions for WASM caching
 */
export const WASMCacheUtils = {
    /**
     * Preload all OpenSCAD WASM resources
     */
    async preloadOpenSCADResources(basePath = '/wasm/') {
        const resources = [
            'openscad.js',
            'openscad.wasm.js', 
            'openscad.wasm',
            'openscad.fonts.js',
            'openscad.mcad.js'
        ];

        const urls = resources.map(resource => basePath + resource);
        await wasmCacheManager.preloadResources(urls);
    },

    /**
     * Get formatted cache information
     */
    async getCacheInfo() {
        const stats = await wasmCacheManager.getCacheStats();
        return {
            ...stats,
            totalSizeFormatted: this.formatBytes(stats.totalSize),
            maxAgeFormatted: this.formatDuration(stats.maxAge)
        };
    },

    /**
     * Format bytes for human-readable display
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
    },

    /**
     * Format duration for human-readable display
     */
    formatDuration(ms) {
        const days = Math.floor(ms / (24 * 60 * 60 * 1000));
        const hours = Math.floor((ms % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000));
        return `${days}d ${hours}h`;
    }
};

export default wasmCacheManager;