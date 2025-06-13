/**
 * WASM Test Fixtures
 * 
 * Provides mock implementations and test utilities for OpenSCAD WASM testing
 */

/**
 * Mock OpenSCAD WASM Module
 * Simulates the behavior of the real OpenSCAD WASM module for testing
 */
export class MockOpenSCADWASM {
    constructor(options = {}) {
        this.options = options;
        this.FS = new MockFileSystem();
        this.renderDelay = options.renderDelay || 100; // Simulate rendering time
        this.shouldFail = options.shouldFail || false;
        this.callCount = 0;
    }

    /**
     * Mock callMain implementation
     * @param {string[]} args - Command line arguments
     * @returns {number} Exit code (0 for success)
     */
    callMain(args) {
        this.callCount++;
        console.log('Mock OpenSCAD callMain called with:', args);
        
        if (this.shouldFail) {
            throw new Error('Mock OpenSCAD rendering failed');
        }

        // Parse arguments to determine input/output files
        const inputFile = args[0];
        const outputIndex = args.indexOf('-o');
        const outputFile = outputIndex >= 0 ? args[outputIndex + 1] : null;

        if (!inputFile || !outputFile) {
            return 1; // Error exit code
        }

        // Read input file
        const inputData = this.FS.readFile(inputFile, { encoding: 'utf8' });
        
        // Generate mock STL data based on input
        const stlData = this._generateMockSTL(inputData);
        
        // Write output file
        this.FS.writeFile(outputFile, stlData);
        
        return 0; // Success exit code
    }

    /**
     * Generate mock STL data based on SCAD code
     * @private
     */
    _generateMockSTL(scadCode) {
        // Create different STL data for different SCAD code
        const hash = this._simpleHash(scadCode);
        const baseSTL = 'mock_stl_data_';
        
        if (scadCode.includes('cube')) {
            return new TextEncoder().encode(baseSTL + 'cube_' + hash);
        } else if (scadCode.includes('sphere')) {
            return new TextEncoder().encode(baseSTL + 'sphere_' + hash);
        } else if (scadCode.includes('cylinder')) {
            return new TextEncoder().encode(baseSTL + 'cylinder_' + hash);
        } else {
            return new TextEncoder().encode(baseSTL + 'generic_' + hash);
        }
    }

    /**
     * Simple hash function for generating unique mock data
     * @private
     */
    _simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash).toString(36);
    }

    /**
     * Get call statistics
     */
    getStats() {
        return {
            callCount: this.callCount,
            shouldFail: this.shouldFail,
            renderDelay: this.renderDelay
        };
    }

    /**
     * Reset mock state
     */
    reset() {
        this.callCount = 0;
        this.FS.reset();
    }
}

/**
 * Mock File System
 * Simulates Emscripten's file system for testing
 */
class MockFileSystem {
    constructor() {
        this.files = new Map();
    }

    /**
     * Write file to mock filesystem
     * @param {string} path - File path
     * @param {string|Uint8Array} data - File data
     */
    writeFile(path, data) {
        console.log(`Mock FS: Writing file ${path}`);
        this.files.set(path, data);
    }

    /**
     * Read file from mock filesystem
     * @param {string} path - File path
     * @param {Object} options - Read options
     * @returns {string|Uint8Array} File data
     */
    readFile(path, options = {}) {
        console.log(`Mock FS: Reading file ${path}`);
        
        if (!this.files.has(path)) {
            throw new Error(`File not found: ${path}`);
        }

        const data = this.files.get(path);
        
        if (options.encoding === 'utf8' && data instanceof Uint8Array) {
            return new TextDecoder().decode(data);
        }
        
        return data;
    }

    /**
     * Delete file from mock filesystem
     * @param {string} path - File path
     */
    unlink(path) {
        console.log(`Mock FS: Deleting file ${path}`);
        this.files.delete(path);
    }

    /**
     * Check if file exists
     * @param {string} path - File path
     * @returns {boolean} True if file exists
     */
    exists(path) {
        return this.files.has(path);
    }

    /**
     * List all files
     * @returns {string[]} Array of file paths
     */
    listFiles() {
        return Array.from(this.files.keys());
    }

    /**
     * Reset filesystem
     */
    reset() {
        this.files.clear();
    }

    /**
     * Get filesystem statistics
     */
    getStats() {
        return {
            fileCount: this.files.size,
            files: this.listFiles()
        };
    }
}

/**
 * Mock WASM Loader
 * Provides a mock implementation of the WASM loader for testing
 */
export class MockWASMLoader {
    constructor(options = {}) {
        this.options = options;
        this.isInitialized = false;
        this.isInitializing = false;
        this.mockInstance = null;
        this.initializationDelay = options.initializationDelay || 50;
        this.shouldFailInit = options.shouldFailInit || false;
    }

    /**
     * Mock initialization
     * @param {Object} initOptions - Initialization options
     * @returns {Promise<Object>} Mock OpenSCAD instance
     */
    async initialize(initOptions = {}) {
        if (this.isInitialized) {
            return this.mockInstance;
        }

        if (this.isInitializing) {
            // Wait for existing initialization
            while (this.isInitializing) {
                await new Promise(resolve => setTimeout(resolve, 10));
            }
            return this.mockInstance;
        }

        this.isInitializing = true;

        try {
            // Simulate initialization delay
            await new Promise(resolve => setTimeout(resolve, this.initializationDelay));

            if (this.shouldFailInit) {
                throw new Error('Mock WASM initialization failed');
            }

            this.mockInstance = new MockOpenSCADWASM({
                ...this.options,
                ...initOptions
            });

            this.isInitialized = true;
            this.isInitializing = false;

            console.log('Mock WASM loader initialized');
            return this.mockInstance;

        } catch (error) {
            this.isInitializing = false;
            throw error;
        }
    }

    /**
     * Get mock instance
     * @returns {Object|null} Mock instance
     */
    getInstance() {
        return this.mockInstance;
    }

    /**
     * Check if ready
     * @returns {boolean} True if ready
     */
    isReady() {
        return this.isInitialized && this.mockInstance !== null;
    }

    /**
     * Get status
     * @returns {Object} Status information
     */
    getStatus() {
        return {
            isInitialized: this.isInitialized,
            isInitializing: this.isInitializing,
            hasInstance: this.mockInstance !== null
        };
    }

    /**
     * Reset mock loader
     */
    reset() {
        this.isInitialized = false;
        this.isInitializing = false;
        if (this.mockInstance) {
            this.mockInstance.reset();
        }
        this.mockInstance = null;
    }
}

/**
 * Test utility functions
 */
export const TestUtils = {
    /**
     * Create sample SCAD codes for testing
     */
    getSampleSCADCodes() {
        return {
            cube: 'cube([10, 10, 10]);',
            sphere: 'sphere(r=5);',
            cylinder: 'cylinder(r=3, h=8);',
            complex: `
                difference() {
                    cube([20, 20, 20]);
                    sphere(r=8);
                }
            `,
            empty: '',
            invalid: 'invalid_scad_syntax_here:::'
        };
    },

    /**
     * Create mock WASM options for different test scenarios
     */
    getMockWASMOptions() {
        return {
            normal: {},
            slow: { renderDelay: 500, initializationDelay: 200 },
            failing: { shouldFail: true },
            failingInit: { shouldFailInit: true },
            fastInit: { initializationDelay: 1 }
        };
    },

    /**
     * Validate STL-like output
     * @param {Uint8Array} data - Data to validate
     * @returns {boolean} True if data looks like valid STL
     */
    isValidSTLLike(data) {
        if (!data || data.length === 0) {
            return false;
        }

        // For mock data, just check that it contains our mock markers
        const text = new TextDecoder().decode(data);
        return text.includes('mock_stl_data_');
    },

    /**
     * Extract shape type from mock STL data
     * @param {Uint8Array} data - Mock STL data
     * @returns {string} Shape type or 'unknown'
     */
    extractShapeType(data) {
        const text = new TextDecoder().decode(data);
        
        if (text.includes('cube')) return 'cube';
        if (text.includes('sphere')) return 'sphere';
        if (text.includes('cylinder')) return 'cylinder';
        return 'generic';
    }
};

/**
 * Integration test helpers
 */
export const IntegrationTestHelpers = {
    /**
     * Set up mock environment for WASM tests
     */
    async setupMockEnvironment(options = {}) {
        const mockLoader = new MockWASMLoader(options);
        
        // Replace global references if they exist
        if (typeof global !== 'undefined') {
            global.mockWASMLoader = mockLoader;
        }
        
        if (typeof window !== 'undefined') {
            window.mockWASMLoader = mockLoader;
        }
        
        return mockLoader;
    },

    /**
     * Clean up mock environment
     */
    cleanupMockEnvironment() {
        if (typeof global !== 'undefined') {
            delete global.mockWASMLoader;
        }
        
        if (typeof window !== 'undefined') {
            delete window.mockWASMLoader;
        }
    },

    /**
     * Run a rendering test with timeout
     */
    async runRenderingTest(renderer, scadCode, timeout = 5000) {
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Test timeout')), timeout);
        });

        const renderPromise = renderer.renderToSTL(scadCode);
        
        return Promise.race([renderPromise, timeoutPromise]);
    }
};