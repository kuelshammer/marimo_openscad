/**
 * Web Worker Manager for OpenSCAD WASM
 * 
 * Manages web worker lifecycle and provides a clean API
 * for non-blocking OpenSCAD rendering.
 */

export class OpenSCADWorkerManager {
    constructor() {
        this.worker = null;
        this.isInitialized = false;
        this.isSupported = this._checkWorkerSupport();
        this.messageId = 0;
        this.pendingMessages = new Map();
        this.initPromise = null;
    }

    /**
     * Check if web workers are supported
     * @private
     */
    _checkWorkerSupport() {
        return typeof Worker !== 'undefined' && 
               typeof URL !== 'undefined' &&
               typeof Blob !== 'undefined';
    }

    /**
     * Initialize the web worker
     * @param {Object} options - Initialization options
     * @returns {Promise<boolean>} Success status
     */
    async initialize(options = {}) {
        if (this.initPromise) {
            return this.initPromise;
        }

        this.initPromise = this._doInitialize(options);
        return this.initPromise;
    }

    /**
     * Internal initialization logic
     * @private
     */
    async _doInitialize(options) {
        if (!this.isSupported) {
            console.warn('Web Workers not supported, falling back to main thread');
            return false;
        }

        try {
            // Create worker from our worker script
            this.worker = new Worker('./openscad-worker.js', {
                type: 'module'
            });

            // Set up message handling
            this.worker.onmessage = (event) => {
                this._handleWorkerMessage(event);
            };

            this.worker.onerror = (error) => {
                console.error('Worker error:', error);
                this._rejectPendingMessages(new Error(`Worker error: ${error.message}`));
            };

            // Initialize the worker
            const initResult = await this._sendCommand('initialize', options);
            
            if (initResult.success) {
                this.isInitialized = true;
                console.log('Worker Manager: Worker initialized successfully');
                return true;
            } else {
                throw new Error(`Worker initialization failed: ${initResult.error}`);
            }

        } catch (error) {
            console.error('Worker Manager: Failed to initialize worker:', error);
            this._cleanup();
            return false;
        }
    }

    /**
     * Render OpenSCAD code using the worker
     * @param {string} scadCode - OpenSCAD code to render
     * @param {Object} options - Rendering options
     * @returns {Promise<Object>} Rendering result
     */
    async renderToSTL(scadCode, options = {}) {
        if (!this.isInitialized || !this.worker) {
            throw new Error('Worker not initialized');
        }

        try {
            const result = await this._sendCommand('render', {
                scadCode: scadCode,
                options: options
            });

            if (result.success) {
                return result.result;
            } else {
                throw new Error(`Rendering failed: ${result.error}`);
            }

        } catch (error) {
            console.error('Worker Manager: Rendering failed:', error);
            throw error;
        }
    }

    /**
     * Get worker status
     * @returns {Promise<Object>} Worker status
     */
    async getStatus() {
        if (!this.isInitialized || !this.worker) {
            return {
                isSupported: this.isSupported,
                isInitialized: false,
                hasWorker: false
            };
        }

        try {
            const result = await this._sendCommand('status');
            return {
                isSupported: this.isSupported,
                isInitialized: this.isInitialized,
                hasWorker: true,
                ...result.result
            };
        } catch (error) {
            console.error('Worker Manager: Failed to get status:', error);
            return {
                isSupported: this.isSupported,
                isInitialized: this.isInitialized,
                hasWorker: true,
                error: error.message
            };
        }
    }

    /**
     * Reset the worker
     * @returns {Promise<void>}
     */
    async reset() {
        if (this.worker && this.isInitialized) {
            try {
                await this._sendCommand('reset');
                console.log('Worker Manager: Worker reset successfully');
            } catch (error) {
                console.error('Worker Manager: Failed to reset worker:', error);
            }
        }
        
        this._cleanup();
    }

    /**
     * Terminate the worker
     */
    terminate() {
        this._cleanup();
    }

    /**
     * Send a command to the worker
     * @private
     */
    async _sendCommand(command, data = null) {
        return new Promise((resolve, reject) => {
            if (!this.worker) {
                reject(new Error('Worker not available'));
                return;
            }

            const messageId = ++this.messageId;
            
            // Store promise resolvers
            this.pendingMessages.set(messageId, { resolve, reject });

            // Send message to worker
            this.worker.postMessage({
                id: messageId,
                command: command,
                data: data
            });

            // Set timeout for long-running operations
            const timeout = command === 'render' ? 30000 : 10000; // 30s for render, 10s for others
            setTimeout(() => {
                if (this.pendingMessages.has(messageId)) {
                    this.pendingMessages.delete(messageId);
                    reject(new Error(`Worker command timeout: ${command}`));
                }
            }, timeout);
        });
    }

    /**
     * Handle messages from the worker
     * @private
     */
    _handleWorkerMessage(event) {
        const { id, success, result, error, stack } = event.data;

        if (id && this.pendingMessages.has(id)) {
            const { resolve, reject } = this.pendingMessages.get(id);
            this.pendingMessages.delete(id);

            if (success) {
                resolve(result);
            } else {
                const workerError = new Error(error || 'Worker operation failed');
                if (stack) {
                    workerError.stack = stack;
                }
                reject(workerError);
            }
        } else if (!id) {
            // Global worker message (e.g., errors)
            console.warn('Worker Manager: Received global worker message:', event.data);
        }
    }

    /**
     * Reject all pending messages
     * @private
     */
    _rejectPendingMessages(error) {
        for (const [id, { reject }] of this.pendingMessages) {
            reject(error);
        }
        this.pendingMessages.clear();
    }

    /**
     * Clean up worker resources
     * @private
     */
    _cleanup() {
        if (this.worker) {
            this.worker.terminate();
            this.worker = null;
        }

        this.isInitialized = false;
        this.initPromise = null;
        
        // Reject any pending messages
        this._rejectPendingMessages(new Error('Worker terminated'));
    }

    /**
     * Check if workers are supported in this environment
     * @static
     */
    static isSupported() {
        return typeof Worker !== 'undefined' && 
               typeof URL !== 'undefined' &&
               typeof Blob !== 'undefined';
    }
}

/**
 * Singleton worker manager instance
 */
export const workerManager = new OpenSCADWorkerManager();

/**
 * Utility functions for worker management
 */
export const WorkerUtils = {
    /**
     * Create a worker-aware WASM renderer
     */
    async createRenderer(preferWorker = true) {
        if (preferWorker && OpenSCADWorkerManager.isSupported()) {
            const success = await workerManager.initialize();
            if (success) {
                return {
                    type: 'worker',
                    renderToSTL: (scadCode, options) => workerManager.renderToSTL(scadCode, options),
                    getStatus: () => workerManager.getStatus(),
                    reset: () => workerManager.reset()
                };
            }
        }

        // Fallback to main thread renderer
        const { OpenSCADWASMRenderer } = await import('./openscad-wasm-renderer.js');
        const renderer = new OpenSCADWASMRenderer();
        await renderer.initialize();

        return {
            type: 'main-thread',
            renderToSTL: (scadCode, options) => renderer.renderToSTL(scadCode, options),
            getStatus: () => renderer.getStats(),
            reset: () => renderer.reset()
        };
    },

    /**
     * Performance comparison between worker and main thread
     */
    async benchmarkRenderers(scadCode, iterations = 3) {
        const results = {};

        // Test worker renderer
        try {
            const workerRenderer = await this.createRenderer(true);
            if (workerRenderer.type === 'worker') {
                const times = [];
                for (let i = 0; i < iterations; i++) {
                    const start = performance.now();
                    await workerRenderer.renderToSTL(scadCode);
                    times.push(performance.now() - start);
                }
                results.worker = {
                    averageTime: times.reduce((a, b) => a + b) / times.length,
                    times: times
                };
            }
        } catch (error) {
            results.worker = { error: error.message };
        }

        // Test main thread renderer
        try {
            const mainRenderer = await this.createRenderer(false);
            const times = [];
            for (let i = 0; i < iterations; i++) {
                const start = performance.now();
                await mainRenderer.renderToSTL(scadCode);
                times.push(performance.now() - start);
            }
            results.mainThread = {
                averageTime: times.reduce((a, b) => a + b) / times.length,
                times: times
            };
        } catch (error) {
            results.mainThread = { error: error.message };
        }

        return results;
    }
};

export default workerManager;