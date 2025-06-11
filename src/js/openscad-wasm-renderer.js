/**
 * OpenSCAD WASM Renderer
 * 
 * Provides a high-level interface for rendering OpenSCAD code to STL
 * using the WebAssembly OpenSCAD module.
 */

import wasmLoader from './wasm-loader.js';

export class OpenSCADWASMRenderer {
    constructor(options = {}) {
        this.options = {
            enableManifold: true,
            outputFormat: 'binstl',
            timeout: 30000, // 30 seconds default timeout
            ...options
        };
        
        this.isReady = false;
        this.renderCount = 0;
    }

    /**
     * Initialize the renderer
     * @param {Object} wasmOptions - Options for WASM loader
     * @returns {Promise<void>}
     */
    async initialize(wasmOptions = {}) {
        try {
            await wasmLoader.initialize(wasmOptions);
            this.isReady = true;
            console.log('OpenSCAD WASM Renderer initialized');
        } catch (error) {
            console.error('Failed to initialize WASM renderer:', error);
            throw error;
        }
    }

    /**
     * Render OpenSCAD code to STL binary data
     * @param {string} scadCode - The OpenSCAD code to render
     * @param {Object} options - Rendering options
     * @returns {Promise<Uint8Array>} The STL binary data
     */
    async renderToSTL(scadCode, options = {}) {
        if (!this.isReady) {
            throw new Error('Renderer not initialized. Call initialize() first.');
        }

        const instance = wasmLoader.getInstance();
        if (!instance) {
            throw new Error('WASM instance not available');
        }

        const renderOptions = { ...this.options, ...options };
        const renderContext = this._createRenderContext();

        try {
            console.log(`Starting WASM render ${renderContext.id}...`);
            
            // Write SCAD code to virtual filesystem
            const inputPath = renderContext.inputPath;
            const outputPath = renderContext.outputPath;
            
            instance.FS.writeFile(inputPath, scadCode);
            console.log(`Written SCAD code to ${inputPath}`);

            // Prepare command line arguments
            const args = this._buildCommandArgs(inputPath, outputPath, renderOptions);
            console.log('Executing OpenSCAD with args:', args);

            // Execute OpenSCAD rendering
            const startTime = performance.now();
            
            // Set up timeout
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Rendering timeout')), renderOptions.timeout);
            });

            const renderPromise = new Promise((resolve, reject) => {
                try {
                    const exitCode = instance.callMain(args);
                    if (exitCode !== 0) {
                        reject(new Error(`OpenSCAD exited with code ${exitCode}`));
                    } else {
                        resolve();
                    }
                } catch (error) {
                    reject(error);
                }
            });

            // Wait for rendering with timeout
            await Promise.race([renderPromise, timeoutPromise]);

            const renderTime = performance.now() - startTime;
            console.log(`Rendering completed in ${renderTime.toFixed(2)}ms`);

            // Read the output file
            let outputData;
            try {
                outputData = instance.FS.readFile(outputPath);
                console.log(`Read output file: ${outputData.length} bytes`);
            } catch (error) {
                throw new Error(`Failed to read output file: ${error.message}`);
            }

            // Clean up temporary files
            this._cleanupRenderContext(instance, renderContext);

            // Validate output
            if (!outputData || outputData.length === 0) {
                throw new Error('Rendering produced empty output');
            }

            this.renderCount++;
            console.log(`WASM render ${renderContext.id} completed successfully`);
            
            return outputData;

        } catch (error) {
            console.error(`WASM render ${renderContext.id} failed:`, error);
            
            // Clean up on error
            this._cleanupRenderContext(instance, renderContext);
            
            // Re-throw with more context
            throw new Error(`OpenSCAD WASM rendering failed: ${error.message}`);
        }
    }

    /**
     * Create a unique render context
     * @private
     */
    _createRenderContext() {
        const id = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        return {
            id,
            inputPath: `/tmp/input_${id}.scad`,
            outputPath: `/tmp/output_${id}.stl`
        };
    }

    /**
     * Build command line arguments for OpenSCAD
     * @private
     */
    _buildCommandArgs(inputPath, outputPath, options) {
        const args = [inputPath];

        // Enable manifold if requested
        if (options.enableManifold) {
            args.push('--enable=manifold');
        }

        // Set output format
        if (options.outputFormat === 'binstl') {
            args.push('--export-format=binstl');
        }

        // Output file
        args.push('-o', outputPath);

        return args;
    }

    /**
     * Clean up temporary files
     * @private
     */
    _cleanupRenderContext(instance, context) {
        try {
            if (instance.FS) {
                // Remove input file
                try {
                    instance.FS.unlink(context.inputPath);
                } catch (e) {
                    // File might not exist, ignore
                }

                // Remove output file
                try {
                    instance.FS.unlink(context.outputPath);
                } catch (e) {
                    // File might not exist, ignore
                }
            }
        } catch (error) {
            console.warn('Failed to cleanup render context:', error);
        }
    }

    /**
     * Get renderer statistics
     * @returns {Object} Renderer statistics
     */
    getStats() {
        return {
            isReady: this.isReady,
            renderCount: this.renderCount,
            wasmStatus: wasmLoader.getStatus()
        };
    }

    /**
     * Reset the renderer
     */
    reset() {
        this.isReady = false;
        this.renderCount = 0;
        wasmLoader.reset();
    }

    /**
     * Check if WASM rendering is supported in this environment
     * @static
     * @returns {boolean} True if WASM is supported
     */
    static isSupported() {
        try {
            return typeof WebAssembly !== 'undefined' &&
                   typeof WebAssembly.instantiate === 'function' &&
                   typeof fetch !== 'undefined';
        } catch (error) {
            return false;
        }
    }

    /**
     * Get capabilities of the WASM renderer
     * @static
     * @returns {Object} Capabilities information
     */
    static getCapabilities() {
        return {
            supportsWASM: OpenSCADWASMRenderer.isSupported(),
            supportsFonts: true,
            supportsMCAD: true,
            supportsManifold: true,
            outputFormats: ['binstl'],
            maxFileSize: 50 * 1024 * 1024, // 50MB limit for WASM
            supportsWebWorkers: typeof Worker !== 'undefined'
        };
    }
}

export default OpenSCADWASMRenderer;