/**
 * Tests for Marimo OpenSCAD Widget - WASM-safe Architecture
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import marimoWidget from '../js/marimo-openscad-widget.js';
const { render } = marimoWidget;
import { OpenSCADDirectRenderer, detectEnvironmentConstraints } from '../js/openscad-direct-renderer.js';

// Mock THREE.js for testing
vi.mock('three', () => ({
    Scene: vi.fn(() => ({
        background: null,
        add: vi.fn(),
        remove: vi.fn(),
        clear: vi.fn(),
        children: []
    })),
    PerspectiveCamera: vi.fn(() => ({
        position: { x: 0, y: 0, z: 0 },
        aspect: 1,
        updateProjectionMatrix: vi.fn(),
        lookAt: vi.fn()
    })),
    WebGLRenderer: vi.fn(() => ({
        setSize: vi.fn(),
        setPixelRatio: vi.fn(),
        domElement: document.createElement('canvas'),
        render: vi.fn(),
        dispose: vi.fn()
    })),
    AmbientLight: vi.fn(),
    DirectionalLight: vi.fn(() => ({
        position: { set: vi.fn() }
    })),
    GridHelper: vi.fn(() => ({
        position: { y: 0 }
    })),
    BoxGeometry: vi.fn(),
    MeshPhongMaterial: vi.fn(),
    Mesh: vi.fn(() => ({
        position: { set: vi.fn(), copy: vi.fn() },
        name: 'testMesh'
    })),
    BufferGeometry: vi.fn(() => ({
        setAttribute: vi.fn(),
        computeBoundingBox: vi.fn(),
        boundingBox: {
            getCenter: vi.fn(() => ({ negate: vi.fn(() => ({})) })),
            getSize: vi.fn(() => ({ x: 1, y: 1, z: 1 }))
        },
        dispose: vi.fn()
    })),
    Float32BufferAttribute: vi.fn(),
    Color: vi.fn(),
    Vector3: vi.fn(() => ({})),
    DoubleSide: 'DoubleSide'
}));

describe('Environment Detection', () => {
    it('should detect environment constraints', () => {
        const constraints = detectEnvironmentConstraints();
        
        expect(constraints).toHaveProperty('hasWebWorkers');
        expect(constraints).toHaveProperty('hasWebAssembly');
        expect(constraints).toHaveProperty('recommendedMode');
        expect(constraints.isWASMSafe).toBe(true);
        expect(constraints.recommendedMode).toBe('direct');
    });
});

describe('OpenSCADDirectRenderer', () => {
    let renderer;
    
    beforeEach(() => {
        renderer = new OpenSCADDirectRenderer();
    });
    
    it('should create renderer with correct mode', () => {
        expect(renderer).toBeDefined();
        expect(renderer.options.enableManifold).toBe(true);
        expect(renderer.options.outputFormat).toBe('binstl');
    });
    
    it('should report correct capabilities', () => {
        const capabilities = OpenSCADDirectRenderer.getCapabilities();
        
        expect(capabilities.supportsWorkers).toBe(false);
        expect(capabilities.mode).toBe('direct-main-thread');
        expect(capabilities.environment).toBe('wasm-safe');
    });
    
    it('should provide status information', () => {
        const status = renderer.getStatus();
        
        expect(status).toHaveProperty('isInitialized');
        expect(status).toHaveProperty('hasRenderer');
        expect(status).toHaveProperty('renderCount');
        expect(status.mode).toBe('direct-main-thread');
    });
    
    it('should support WASM detection', () => {
        const isSupported = OpenSCADDirectRenderer.isSupported();
        // In test environment, this depends on WASM availability
        expect(typeof isSupported).toBe('boolean');
    });
});

describe('Marimo OpenSCAD Widget', () => {
    let mockModel;
    let mockElement;
    
    beforeEach(() => {
        // Mock anywidget model
        mockModel = {
            data: {},
            get: vi.fn((key) => mockModel.data[key]),
            set: vi.fn((key, value) => { mockModel.data[key] = value; }),
            on: vi.fn()
        };
        
        // Mock DOM element
        mockElement = {
            innerHTML: '',
            querySelector: vi.fn((selector) => {
                if (selector === '#container') {
                    return {
                        getBoundingClientRect: () => ({ width: 800, height: 600 }),
                        appendChild: vi.fn()
                    };
                }
                if (selector === '#status') {
                    return {
                        textContent: '',
                        style: {}
                    };
                }
                return null;
            })
        };
        
        // Mock global objects
        global.window = {
            addEventListener: vi.fn(),
            devicePixelRatio: 1
        };
        global.requestAnimationFrame = vi.fn();
    });
    
    it('should initialize widget in test mode', async () => {
        // Set test environment
        process.env.NODE_ENV = 'test';
        
        const cleanup = await render({ model: mockModel, el: mockElement });
        
        expect(mockElement.innerHTML).toContain('container');
        expect(mockElement.innerHTML).toContain('status');
        expect(mockElement.innerHTML).toContain('Direct WASM');
        expect(typeof cleanup).toBe('function');
    });
    
    it('should set up model change listeners', async () => {
        process.env.NODE_ENV = 'test';
        
        await render({ model: mockModel, el: mockElement });
        
        expect(mockModel.on).toHaveBeenCalledWith('change:stl_data', expect.any(Function));
        expect(mockModel.on).toHaveBeenCalledWith('change:scad_code', expect.any(Function));
        expect(mockModel.on).toHaveBeenCalledWith('change:error_message', expect.any(Function));
        expect(mockModel.on).toHaveBeenCalledWith('change:is_loading', expect.any(Function));
    });
    
    it('should handle empty model data', async () => {
        process.env.NODE_ENV = 'test';
        mockModel.data = {};
        
        const cleanup = await render({ model: mockModel, el: mockElement });
        
        expect(cleanup).toBeDefined();
        expect(typeof cleanup).toBe('function');
    });
    
    it('should handle STL data', async () => {
        process.env.NODE_ENV = 'test';
        const mockSTLData = btoa('mock stl data'); // Base64 encoded
        mockModel.data = { stl_data: mockSTLData };
        
        const cleanup = await render({ model: mockModel, el: mockElement });
        
        expect(cleanup).toBeDefined();
    });
    
    it('should handle SCAD code', async () => {
        process.env.NODE_ENV = 'test';
        mockModel.data = { scad_code: 'cube([1,1,1]);' };
        
        const cleanup = await render({ model: mockModel, el: mockElement });
        
        expect(cleanup).toBeDefined();
    });
    
    it('should handle error states', async () => {
        process.env.NODE_ENV = 'test';
        mockModel.data = { error_message: 'Test error' };
        
        const cleanup = await render({ model: mockModel, el: mockElement });
        
        expect(cleanup).toBeDefined();
    });
    
    it('should handle loading states', async () => {
        process.env.NODE_ENV = 'test';
        mockModel.data = { is_loading: true };
        
        const cleanup = await render({ model: mockModel, el: mockElement });
        
        expect(cleanup).toBeDefined();
    });
});

describe('WASM Compatibility', () => {
    it('should work without Web Workers', () => {
        // Simulate environment without Worker support
        const originalWorker = global.Worker;
        delete global.Worker;
        
        const constraints = detectEnvironmentConstraints();
        expect(constraints.hasWebWorkers).toBe(false);
        expect(constraints.recommendedMode).toBe('direct');
        
        // Restore
        global.Worker = originalWorker;
    });
    
    it('should work without advanced memory API', () => {
        // Simulate environment without performance.memory
        const originalPerformance = global.performance;
        global.performance = {};
        
        const constraints = detectEnvironmentConstraints();
        expect(constraints.hasMemoryAPI || false).toBe(false);
        
        // Restore
        global.performance = originalPerformance;
    });
    
    it('should prioritize WASM-safe operations', () => {
        const capabilities = OpenSCADDirectRenderer.getCapabilities();
        
        expect(capabilities.supportsWorkers).toBe(false);
        expect(capabilities.environment).toBe('wasm-safe');
        expect(capabilities.mode).toBe('direct-main-thread');
    });
});

describe('Performance and Memory', () => {
    it('should track render count', () => {
        const renderer = new OpenSCADDirectRenderer();
        const status = renderer.getStatus();
        
        expect(status.renderCount).toBe(0);
    });
    
    it('should provide memory information when available', () => {
        const renderer = new OpenSCADDirectRenderer();
        const status = renderer.getStatus();
        
        // Memory info availability depends on environment
        expect(status).toHaveProperty('memoryUsage');
    });
    
    it('should support renderer reset', async () => {
        const renderer = new OpenSCADDirectRenderer();
        const resetResult = await renderer.reset();
        
        expect(resetResult.success).toBe(true);
        expect(renderer.renderCount).toBe(0);
    });
});

describe('Error Handling', () => {
    it('should handle renderer initialization failure gracefully', async () => {
        const renderer = new OpenSCADDirectRenderer();
        
        // Mock initialization failure
        vi.spyOn(renderer, '_doInitialize').mockRejectedValue(new Error('Mock initialization error'));
        
        await expect(renderer.initialize()).rejects.toThrow('Mock initialization error');
        expect(renderer.isInitialized).toBe(false);
    });
    
    it('should handle render requests before initialization', async () => {
        const renderer = new OpenSCADDirectRenderer();
        
        await expect(renderer.renderToSTL('cube([1,1,1]);')).rejects.toThrow('Direct renderer not initialized');
    });
});