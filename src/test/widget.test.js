/**
 * Tests for the Marimo-OpenSCAD Widget
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render } from '../js/widget.js';

describe('Marimo-OpenSCAD Widget', () => {
    let mockModel;
    let mockEl;
    
    beforeEach(() => {
        // Mock the anywidget model
        mockModel = {
            data: {
                stl_data: '',
                error_message: '',
                is_loading: false
            },
            get: vi.fn((key) => mockModel.data[key]),
            on: vi.fn(),
            listeners: new Map()
        };
        
        // Mock DOM element
        mockEl = {
            innerHTML: '',
            querySelector: vi.fn((selector) => {
                if (selector === '#container') {
                    return {
                        getBoundingClientRect: () => ({ width: 600, height: 400 }),
                        appendChild: vi.fn()
                    };
                }
                if (selector === '#status') {
                    return {
                        textContent: ''
                    };
                }
                return null;
            })
        };
        
        // Mock addEventListener
        global.window = {
            addEventListener: vi.fn(),
            devicePixelRatio: 1
        };
        
        global.document = {
            createElement: vi.fn(() => ({
                style: {},
                addEventListener: vi.fn()
            }))
        };
    });
    
    it('should initialize widget container', () => {
        render({ model: mockModel, el: mockEl });
        
        expect(mockEl.innerHTML).toContain('3D viewer');
        expect(mockEl.innerHTML).toContain('container');
        expect(mockEl.innerHTML).toContain('status');
    });
    
    it('should handle model data changes', () => {
        render({ model: mockModel, el: mockEl });
        
        // Verify that model change listeners are registered
        expect(mockModel.on).toHaveBeenCalledWith('change:stl_data', expect.any(Function));
        expect(mockModel.on).toHaveBeenCalledWith('change:error_message', expect.any(Function));
        expect(mockModel.on).toHaveBeenCalledWith('change:is_loading', expect.any(Function));
    });
    
    it('should return cleanup function', () => {
        const cleanup = render({ model: mockModel, el: mockEl });
        
        expect(typeof cleanup).toBe('function');
        
        // Should not throw when called
        expect(() => cleanup()).not.toThrow();
    });
    
    it('should handle empty STL data', () => {
        mockModel.data.stl_data = '';
        
        const cleanup = render({ model: mockModel, el: mockEl });
        
        // Should initialize without errors
        expect(cleanup).toBeDefined();
    });
    
    it('should handle error states', () => {
        mockModel.data.error_message = 'Test error';
        
        const cleanup = render({ model: mockModel, el: mockEl });
        
        // Should still initialize
        expect(cleanup).toBeDefined();
    });
    
    it('should handle loading states', () => {
        mockModel.data.is_loading = true;
        
        const cleanup = render({ model: mockModel, el: mockEl });
        
        // Should still initialize
        expect(cleanup).toBeDefined();
    });
});

describe('STL Parser', () => {
    // Note: STLParser is not exported, but we can test it indirectly
    // through the widget functionality
    
    it('should handle base64 encoded STL data', () => {
        // Create a simple binary STL file (minimal valid format)
        const header = new ArrayBuffer(80);
        const faceCount = new ArrayBuffer(4);
        const faceCountView = new DataView(faceCount);
        faceCountView.setUint32(0, 0, true); // 0 faces for simplicity
        
        const stlBuffer = new ArrayBuffer(84); // Header + face count
        const headerArray = new Uint8Array(header);
        const faceArray = new Uint8Array(faceCount);
        const stlArray = new Uint8Array(stlBuffer);
        
        stlArray.set(headerArray, 0);
        stlArray.set(faceArray, 80);
        
        // Convert to base64
        const binaryString = String.fromCharCode(...stlArray);
        const base64Data = btoa(binaryString);
        
        mockModel.data.stl_data = base64Data;
        
        const cleanup = render({ model: mockModel, el: mockEl });
        
        // Should not throw errors with valid STL data
        expect(cleanup).toBeDefined();
    });
});

describe('Scene Manager', () => {
    it('should handle resize events', () => {
        const cleanup = render({ model: mockModel, el: mockEl });
        
        // Trigger resize event
        const resizeHandler = global.window.addEventListener.mock.calls
            .find(call => call[0] === 'resize')?.[1];
        
        if (resizeHandler) {
            expect(() => resizeHandler()).not.toThrow();
        }
        
        cleanup();
    });
});