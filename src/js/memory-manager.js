/**
 * Memory Manager for OpenSCAD WASM
 * 
 * Manages memory usage, garbage collection, and resource cleanup
 * for optimal performance in long-running sessions.
 */

export class MemoryManager {
    constructor() {
        this.instances = new Map();
        this.cleanupCallbacks = new Set();
        this.memoryThreshold = 50 * 1024 * 1024; // 50MB threshold
        this.checkInterval = 30000; // Check every 30 seconds
        this.intervalId = null;
        this.isMonitoring = false;
    }

    /**
     * Register a WASM instance for memory management
     * @param {string} id - Unique identifier for the instance
     * @param {Object} instance - WASM instance object
     */
    registerInstance(id, instance) {
        this.instances.set(id, {
            instance: instance,
            createdAt: Date.now(),
            lastUsed: Date.now(),
            memoryUsage: this.getInstanceMemoryUsage(instance)
        });

        console.log(`Memory Manager: Registered instance ${id}`);
        
        if (!this.isMonitoring) {
            this.startMonitoring();
        }
    }

    /**
     * Unregister a WASM instance
     * @param {string} id - Instance identifier
     */
    unregisterInstance(id) {
        if (this.instances.has(id)) {
            const instanceData = this.instances.get(id);
            this.cleanupInstance(instanceData.instance);
            this.instances.delete(id);
            console.log(`Memory Manager: Unregistered instance ${id}`);
        }

        if (this.instances.size === 0) {
            this.stopMonitoring();
        }
    }

    /**
     * Update last used timestamp for an instance
     * @param {string} id - Instance identifier
     */
    touchInstance(id) {
        if (this.instances.has(id)) {
            const instanceData = this.instances.get(id);
            instanceData.lastUsed = Date.now();
            instanceData.memoryUsage = this.getInstanceMemoryUsage(instanceData.instance);
        }
    }

    /**
     * Get memory usage for a specific instance
     * @param {Object} instance - WASM instance
     * @returns {number} Memory usage in bytes
     */
    getInstanceMemoryUsage(instance) {
        if (!instance || !instance.FS) {
            return 0;
        }

        try {
            // Estimate memory usage based on file system and heap
            let totalSize = 0;
            
            // Check temporary files in filesystem
            if (instance.FS.analyzePath) {
                try {
                    const tmpPath = instance.FS.analyzePath('/tmp');
                    if (tmpPath.exists && instance.FS.readdir) {
                        const files = instance.FS.readdir('/tmp');
                        for (const file of files) {
                            if (file !== '.' && file !== '..') {
                                try {
                                    const stat = instance.FS.stat(`/tmp/${file}`);
                                    totalSize += stat.size || 0;
                                } catch (e) {
                                    // File might not exist anymore
                                }
                            }
                        }
                    }
                } catch (e) {
                    // /tmp might not exist
                }
            }

            return totalSize;
        } catch (error) {
            console.warn('Memory Manager: Failed to get instance memory usage:', error);
            return 0;
        }
    }

    /**
     * Get system memory information
     * @returns {Object} Memory information
     */
    getSystemMemory() {
        const memory = {
            supported: false,
            used: 0,
            total: 0,
            limit: 0,
            percentage: 0
        };

        if (typeof performance !== 'undefined' && performance.memory) {
            memory.supported = true;
            memory.used = performance.memory.usedJSHeapSize;
            memory.total = performance.memory.totalJSHeapSize;
            memory.limit = performance.memory.jsHeapSizeLimit;
            memory.percentage = (memory.used / memory.limit) * 100;
        }

        return memory;
    }

    /**
     * Get comprehensive memory statistics
     * @returns {Object} Memory statistics
     */
    getMemoryStats() {
        const systemMemory = this.getSystemMemory();
        const instances = [];
        let totalInstanceMemory = 0;

        for (const [id, data] of this.instances) {
            const memUsage = this.getInstanceMemoryUsage(data.instance);
            instances.push({
                id: id,
                createdAt: data.createdAt,
                lastUsed: data.lastUsed,
                memoryUsage: memUsage,
                age: Date.now() - data.createdAt,
                idle: Date.now() - data.lastUsed
            });
            totalInstanceMemory += memUsage;
        }

        return {
            system: systemMemory,
            instances: instances,
            totalInstances: this.instances.size,
            totalInstanceMemory: totalInstanceMemory,
            threshold: this.memoryThreshold,
            isMonitoring: this.isMonitoring
        };
    }

    /**
     * Clean up an instance
     * @param {Object} instance - WASM instance to clean up
     */
    cleanupInstance(instance) {
        if (!instance) return;

        try {
            // Clean up temporary files
            if (instance.FS) {
                this.cleanupTemporaryFiles(instance);
            }

            // Run any registered cleanup callbacks
            for (const callback of this.cleanupCallbacks) {
                try {
                    callback(instance);
                } catch (error) {
                    console.warn('Memory Manager: Cleanup callback failed:', error);
                }
            }

            console.log('Memory Manager: Instance cleanup completed');
        } catch (error) {
            console.warn('Memory Manager: Instance cleanup failed:', error);
        }
    }

    /**
     * Clean up temporary files in an instance
     * @param {Object} instance - WASM instance
     */
    cleanupTemporaryFiles(instance) {
        if (!instance.FS) return;

        try {
            // Clean up /tmp directory
            if (instance.FS.analyzePath) {
                const tmpPath = instance.FS.analyzePath('/tmp');
                if (tmpPath.exists && instance.FS.readdir) {
                    const files = instance.FS.readdir('/tmp');
                    for (const file of files) {
                        if (file !== '.' && file !== '..') {
                            try {
                                instance.FS.unlink(`/tmp/${file}`);
                                console.log(`Memory Manager: Cleaned up temp file /tmp/${file}`);
                            } catch (e) {
                                // File might already be deleted
                            }
                        }
                    }
                }
            }
        } catch (error) {
            console.warn('Memory Manager: Failed to cleanup temporary files:', error);
        }
    }

    /**
     * Force garbage collection if available
     */
    forceGarbageCollection() {
        try {
            // Try to trigger garbage collection
            if (typeof window !== 'undefined' && window.gc) {
                window.gc();
                console.log('Memory Manager: Forced garbage collection');
            } else if (typeof global !== 'undefined' && global.gc) {
                global.gc();
                console.log('Memory Manager: Forced garbage collection');
            } else {
                console.log('Memory Manager: Garbage collection not available');
            }
        } catch (error) {
            console.warn('Memory Manager: Failed to force garbage collection:', error);
        }
    }

    /**
     * Perform automatic cleanup based on thresholds
     */
    performAutomaticCleanup() {
        const stats = this.getMemoryStats();
        const now = Date.now();
        
        // Clean up old instances (unused for more than 5 minutes)
        const maxIdleTime = 5 * 60 * 1000; // 5 minutes
        
        for (const instanceInfo of stats.instances) {
            if (instanceInfo.idle > maxIdleTime) {
                console.log(`Memory Manager: Cleaning up idle instance ${instanceInfo.id}`);
                this.unregisterInstance(instanceInfo.id);
            }
        }

        // Clean up if memory usage is high
        if (stats.system.supported && stats.system.percentage > 80) {
            console.log('Memory Manager: High memory usage detected, performing cleanup');
            
            // Clean up all instances
            for (const [id, data] of this.instances) {
                this.cleanupInstance(data.instance);
            }
            
            // Force garbage collection
            this.forceGarbageCollection();
        }
    }

    /**
     * Start memory monitoring
     */
    startMonitoring() {
        if (this.isMonitoring) return;

        this.isMonitoring = true;
        this.intervalId = setInterval(() => {
            this.performAutomaticCleanup();
        }, this.checkInterval);

        console.log('Memory Manager: Started monitoring');
    }

    /**
     * Stop memory monitoring
     */
    stopMonitoring() {
        if (!this.isMonitoring) return;

        this.isMonitoring = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }

        console.log('Memory Manager: Stopped monitoring');
    }

    /**
     * Register a cleanup callback
     * @param {Function} callback - Cleanup function
     */
    addCleanupCallback(callback) {
        this.cleanupCallbacks.add(callback);
    }

    /**
     * Remove a cleanup callback
     * @param {Function} callback - Cleanup function to remove
     */
    removeCleanupCallback(callback) {
        this.cleanupCallbacks.delete(callback);
    }

    /**
     * Cleanup all resources
     */
    cleanup() {
        // Clean up all instances
        for (const [id, data] of this.instances) {
            this.cleanupInstance(data.instance);
        }
        
        this.instances.clear();
        this.stopMonitoring();
        this.cleanupCallbacks.clear();
        
        console.log('Memory Manager: Complete cleanup performed');
    }

    /**
     * Set memory threshold for automatic cleanup
     * @param {number} threshold - Memory threshold in bytes
     */
    setMemoryThreshold(threshold) {
        this.memoryThreshold = threshold;
        console.log(`Memory Manager: Memory threshold set to ${threshold} bytes`);
    }

    /**
     * Set monitoring interval
     * @param {number} interval - Interval in milliseconds
     */
    setMonitoringInterval(interval) {
        this.checkInterval = interval;
        
        if (this.isMonitoring) {
            this.stopMonitoring();
            this.startMonitoring();
        }
        
        console.log(`Memory Manager: Monitoring interval set to ${interval}ms`);
    }
}

/**
 * Singleton memory manager instance
 */
export const memoryManager = new MemoryManager();

/**
 * Utility functions for memory management
 */
export const MemoryUtils = {
    /**
     * Format memory size for human-readable display
     */
    formatMemorySize(bytes) {
        if (bytes === 0) return '0 B';
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
    },

    /**
     * Get memory pressure level
     */
    getMemoryPressure() {
        const stats = memoryManager.getMemoryStats();
        
        if (!stats.system.supported) {
            return 'unknown';
        }
        
        const percentage = stats.system.percentage;
        
        if (percentage > 90) return 'critical';
        if (percentage > 75) return 'high';
        if (percentage > 50) return 'medium';
        return 'low';
    },

    /**
     * Optimize memory usage
     */
    async optimizeMemory() {
        console.log('MemoryUtils: Starting memory optimization...');
        
        // Perform cleanup
        memoryManager.performAutomaticCleanup();
        
        // Force garbage collection
        memoryManager.forceGarbageCollection();
        
        // Wait a bit for cleanup to complete
        await new Promise(resolve => setTimeout(resolve, 100));
        
        const stats = memoryManager.getMemoryStats();
        console.log('MemoryUtils: Memory optimization completed', {
            instances: stats.totalInstances,
            memory: this.formatMemorySize(stats.system.used),
            pressure: this.getMemoryPressure()
        });
        
        return stats;
    }
};

export default memoryManager;