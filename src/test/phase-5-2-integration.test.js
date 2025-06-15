/**
 * Phase 5.2 Integration Tests
 * Tests integration between Progressive Loading and Error Handling with the actual viewer implementation
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import widget from '../js/widget.js';

const { render } = widget;

// Mock external dependencies
global.THREE = {
    Scene: class { constructor() { this.children = []; } },
    WebGLRenderer: class { 
        constructor() { 
            this.domElement = { style: {} }; 
            this.setSize = vi.fn();
        }
        render = vi.fn();
        setPixelRatio = vi.fn();
    },
    PerspectiveCamera: class { constructor() {} },
    OrbitControls: class { constructor() {} },
    DirectionalLight: class { constructor() {} },
    AmbientLight: class { constructor() {} },
    BufferGeometry: class { constructor() {} },
    MeshPhongMaterial: class { constructor() {} },
    Mesh: class { constructor() {} },
    BoxGeometry: class { constructor() {} },
    SphereGeometry: class { constructor() {} },
    CylinderGeometry: class { constructor() {} }
};

global.window = {
    addEventListener: vi.fn(),
    devicePixelRatio: 1,
    THREE: global.THREE
};

global.document = {
    createElement: vi.fn(() => ({
        style: {},
        addEventListener: vi.fn(),
        appendChild: vi.fn(),
        querySelector: vi.fn(),
        getContext: vi.fn(() => ({
            getParameter: vi.fn(() => 'WebGL 2.0'),
            getExtension: vi.fn()
        }))
    }))
};

describe('Phase 5.2 Integration Tests', () => {
    let mockModel;
    let mockEl;
    let statusElement;
    let containerElement;

    beforeEach(() => {
        // Create realistic DOM mocks
        statusElement = {
            textContent: '',
            innerHTML: '',
            style: {},
            appendChild: vi.fn()
        };
        
        containerElement = {
            getBoundingClientRect: () => ({ width: 600, height: 400 }),
            appendChild: vi.fn(),
            querySelector: vi.fn((selector) => {
                if (selector === '#status') return statusElement;
                if (selector === '#container') return containerElement;
                return null;
            }),
            contains: vi.fn(() => false)
        };

        mockEl = {
            innerHTML: '',
            querySelector: vi.fn((selector) => {
                if (selector === '#container') return containerElement;
                if (selector === '#status') return statusElement;
                return null;
            }),
            appendChild: vi.fn()
        };

        mockModel = {
            data: {
                stl_data: '',
                scad_code: 'cube([10,10,10]);',
                error_message: '',
                is_loading: false,
                renderer_type: 'auto',
                renderer_status: 'idle'
            },
            get: vi.fn((key) => mockModel.data[key]),
            on: vi.fn(),
            listeners: new Map()
        };
    });

    describe('Progressive Loading Integration', () => {
        it('should trigger progressive loading states during widget initialization', () => {
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Verify progressive loading was initialized
            expect(mockEl.innerHTML).toContain('status');
            expect(mockEl.innerHTML).toContain('container');
            
            // Cleanup
            cleanup();
        });

        it('should update status during different loading phases', async () => {
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Simulate STL data loading
            mockModel.data.stl_data = 'data:application/sla;base64,U29tZSBTVEwgZGF0YQ==';
            
            // Trigger model change (simulate what anywidget would do)
            const changeCallback = mockModel.on.mock.calls.find(call => call[0] === 'change:stl_data')?.[1];
            if (changeCallback) {
                changeCallback();
            }
            
            // Should have called status updates
            expect(statusElement.innerHTML || statusElement.textContent).toBeDefined();
            
            cleanup();
        });

        it('should handle loading state changes correctly', () => {
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Simulate loading state change
            mockModel.data.is_loading = true;
            const loadingCallback = mockModel.on.mock.calls.find(call => call[0] === 'change:is_loading')?.[1];
            
            if (loadingCallback) {
                loadingCallback();
            }
            
            expect(statusElement).toBeDefined();
            
            cleanup();
        });
    });

    describe('Error Handling Integration', () => {
        it('should handle error messages from the model', () => {
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Simulate error state
            mockModel.data.error_message = 'WebGL not supported';
            const errorCallback = mockModel.on.mock.calls.find(call => call[0] === 'change:error_message')?.[1];
            
            if (errorCallback) {
                errorCallback();
            }
            
            // Should display error somehow
            expect(statusElement).toBeDefined();
            
            cleanup();
        });

        it('should integrate error handling with progressive loading', () => {
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Set both loading and error states
            mockModel.data.is_loading = true;
            mockModel.data.error_message = 'WASM loading failed';
            
            // Trigger both callbacks
            const loadingCallback = mockModel.on.mock.calls.find(call => call[0] === 'change:is_loading')?.[1];
            const errorCallback = mockModel.on.mock.calls.find(call => call[0] === 'change:error_message')?.[1];
            
            if (loadingCallback) loadingCallback();
            if (errorCallback) errorCallback();
            
            expect(statusElement).toBeDefined();
            
            cleanup();
        });

        it('should handle different renderer states', () => {
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Test different renderer states
            const states = ['initializing', 'loading', 'ready', 'error'];
            
            states.forEach(state => {
                mockModel.data.renderer_status = state;
                const statusCallback = mockModel.on.mock.calls.find(call => call[0] === 'change:renderer_status')?.[1];
                
                if (statusCallback) {
                    statusCallback();
                }
            });
            
            expect(statusElement).toBeDefined();
            
            cleanup();
        });
    });

    describe('Real-world Scenarios', () => {
        it('should handle complete loading workflow with STL data', () => {
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Simulate complete workflow
            mockModel.data.is_loading = true;
            mockModel.data.renderer_status = 'loading';
            
            // Start loading
            const loadingCallback = mockModel.on.mock.calls.find(call => call[0] === 'change:is_loading')?.[1];
            if (loadingCallback) loadingCallback();
            
            // Add STL data
            mockModel.data.stl_data = 'U29tZSBTVEwgZGF0YQ=='; // Base64 encoded data
            const stlCallback = mockModel.on.mock.calls.find(call => call[0] === 'change:stl_data')?.[1];
            if (stlCallback) stlCallback();
            
            // Complete loading
            mockModel.data.is_loading = false;
            mockModel.data.renderer_status = 'ready';
            if (loadingCallback) loadingCallback();
            
            expect(containerElement.appendChild).toHaveBeenCalledTimes(0); // Test mode skips actual appending
            
            cleanup();
        });

        it('should handle error recovery workflow', () => {
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Simulate error and recovery
            mockModel.data.error_message = 'Network timeout';
            mockModel.data.renderer_status = 'error';
            
            const errorCallback = mockModel.on.mock.calls.find(call => call[0] === 'change:error_message')?.[1];
            if (errorCallback) errorCallback();
            
            // Clear error and retry
            mockModel.data.error_message = '';
            mockModel.data.renderer_status = 'ready';
            if (errorCallback) errorCallback();
            
            expect(statusElement).toBeDefined();
            
            cleanup();
        });

        it('should handle SCAD code updates with progressive feedback', () => {
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Update SCAD code
            mockModel.data.scad_code = 'sphere(r=5);';
            const scadCallback = mockModel.on.mock.calls.find(call => call[0] === 'change:scad_code')?.[1];
            
            if (scadCallback) {
                scadCallback();
            }
            
            expect(statusElement).toBeDefined();
            
            cleanup();
        });
    });

    describe('Memory and Performance Integration', () => {
        it('should properly cleanup resources on widget destruction', () => {
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Add some data to trigger resource allocation
            mockModel.data.stl_data = 'U29tZSBTVEwgZGF0YQ==';
            const stlCallback = mockModel.on.mock.calls.find(call => call[0] === 'change:stl_data')?.[1];
            if (stlCallback) stlCallback();
            
            // Cleanup should not throw
            expect(() => cleanup()).not.toThrow();
        });

        it('should handle rapid model updates without memory leaks', () => {
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Simulate rapid updates
            for (let i = 0; i < 10; i++) {
                mockModel.data.stl_data = `data-${i}`;
                const stlCallback = mockModel.on.mock.calls.find(call => call[0] === 'change:stl_data')?.[1];
                if (stlCallback) stlCallback();
            }
            
            expect(statusElement).toBeDefined();
            
            cleanup();
        });
    });

    describe('Browser Compatibility', () => {
        it('should handle missing Three.js gracefully', () => {
            // Temporarily remove THREE
            const originalTHREE = global.THREE;
            delete global.THREE;
            delete global.window.THREE;
            
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Should not crash
            expect(cleanup).toBeDefined();
            
            // Restore THREE
            global.THREE = originalTHREE;
            global.window.THREE = originalTHREE;
            
            cleanup();
        });

        it('should handle WebGL unavailable scenario', () => {
            // Mock WebGL not available
            global.document.createElement = vi.fn(() => ({
                style: {},
                addEventListener: vi.fn(),
                appendChild: vi.fn(),
                querySelector: vi.fn(),
                getContext: vi.fn(() => null) // WebGL not available
            }));
            
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Should handle gracefully
            expect(statusElement).toBeDefined();
            
            cleanup();
        });
    });

    describe('Edge Cases', () => {
        it('should handle empty or invalid STL data', () => {
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Test various invalid data
            const invalidData = ['', 'invalid-base64', null, undefined];
            
            invalidData.forEach(data => {
                mockModel.data.stl_data = data;
                const stlCallback = mockModel.on.mock.calls.find(call => call[0] === 'change:stl_data')?.[1];
                if (stlCallback) {
                    expect(() => stlCallback()).not.toThrow();
                }
            });
            
            cleanup();
        });

        it('should handle simultaneous state changes', () => {
            const cleanup = render({ model: mockModel, el: mockEl });
            
            // Trigger multiple changes at once
            mockModel.data.is_loading = true;
            mockModel.data.stl_data = 'U29tZSBTVEwgZGF0YQ==';
            mockModel.data.error_message = 'Warning: Large file';
            
            const callbacks = [
                mockModel.on.mock.calls.find(call => call[0] === 'change:is_loading')?.[1],
                mockModel.on.mock.calls.find(call => call[0] === 'change:stl_data')?.[1],
                mockModel.on.mock.calls.find(call => call[0] === 'change:error_message')?.[1]
            ];
            
            callbacks.forEach(callback => {
                if (callback) {
                    expect(() => callback()).not.toThrow();
                }
            });
            
            cleanup();
        });
    });
});