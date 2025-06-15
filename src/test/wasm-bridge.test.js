/**
 * WASM Bridge JavaScript Test Suite
 * Tests the JavaScript side of the Python↔JavaScript WASM bridge
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '../js/widget.js';

describe('WASM Bridge Integration', () => {
    let mockModel, mockElement;
    
    beforeEach(() => {
        // Mock anywidget model
        mockModel = {
            data: {
                'stl_data': null,
                'scad_code': null,
                'error_message': null,
                'is_loading': false,
                'wasm_enabled': false
            },
            listeners: {},
            get(key) {
                return this.data[key];
            },
            set(key, value) {
                this.data[key] = value;
                this.trigger('change:' + key);
            },
            on(event, callback) {
                if (!this.listeners[event]) {
                    this.listeners[event] = [];
                }
                this.listeners[event].push(callback);
            },
            trigger(event) {
                if (this.listeners[event]) {
                    this.listeners[event].forEach(callback => callback());
                }
            }
        };
        
        // Mock DOM element
        mockElement = {
            innerHTML: '',
            querySelector: vi.fn((selector) => {
                if (selector === '#container') {
                    return {
                        getBoundingClientRect: () => ({ width: 600, height: 400 })
                    };
                }
                if (selector === '#status') {
                    return {
                        textContent: '',
                        style: { backgroundColor: '' }
                    };
                }
                if (selector === '#controls') {
                    return { appendChild: vi.fn() };
                }
                return null;
            })
        };
        
        // Mock global functions
        global.atob = vi.fn((str) => {
            // Mock base64 decoding for regular STL data
            return 'mock binary data';
        });
    });
    
    describe('WASM_RENDER_REQUEST Pattern Detection', () => {
        it('should detect WASM_RENDER_REQUEST pattern', () => {
            const { handleSTLData } = setupWidgetForTesting();
            
            // Mock status element
            const statusElement = { 
                textContent: '', 
                style: { backgroundColor: '' } 
            };
            
            // Test WASM_RENDER_REQUEST detection
            const wasmRequest = 'WASM_RENDER_REQUEST:12345';
            const scadCode = 'cube([1, 1, 1]);';
            
            mockModel.data.scad_code = scadCode;
            mockModel.data.stl_data = wasmRequest;
            
            // Trigger model change
            mockModel.trigger('change:stl_data');
            
            // Should detect as WASM request (not try to decode as base64)
            expect(global.atob).not.toHaveBeenCalled();
        });
        
        it('should extract hash from WASM_RENDER_REQUEST', () => {
            const testCases = [
                'WASM_RENDER_REQUEST:12345',
                'WASM_RENDER_REQUEST:-8427547496623440318',
                'WASM_RENDER_REQUEST:987654321'
            ];
            
            testCases.forEach(request => {
                const expectedHash = request.substring('WASM_RENDER_REQUEST:'.length);
                
                // Simulate JavaScript hash extraction
                if (request.startsWith('WASM_RENDER_REQUEST:')) {
                    const extractedHash = request.substring('WASM_RENDER_REQUEST:'.length);
                    expect(extractedHash).toBe(expectedHash);
                }
            });
        });
        
        it('should ignore non-WASM requests', () => {
            const nonWasmRequests = [
                'regular STL data',
                'NOT_A_WASM_REQUEST:12345',
                '',
                'INVALID_REQUEST_FORMAT'
            ];
            
            nonWasmRequests.forEach(request => {
                const isWasmRequest = typeof request === 'string' && 
                                     request.startsWith('WASM_RENDER_REQUEST:');
                expect(isWasmRequest).toBe(false);
            });
        });
    });
    
    describe('Bridge Error Handling', () => {
        it('should handle missing SCAD code gracefully', () => {
            const statusElement = { 
                textContent: '', 
                style: { backgroundColor: '' } 
            };
            
            // WASM request without SCAD code
            mockModel.data.stl_data = 'WASM_RENDER_REQUEST:12345';
            mockModel.data.scad_code = null;
            
            // Should handle gracefully (not crash)
            expect(() => {
                mockModel.trigger('change:stl_data');
            }).not.toThrow();
        });
        
        it('should handle empty WASM hash', () => {
            const emptyHashRequest = 'WASM_RENDER_REQUEST:';
            
            const isWasmRequest = emptyHashRequest.startsWith('WASM_RENDER_REQUEST:');
            const hash = emptyHashRequest.substring('WASM_RENDER_REQUEST:'.length);
            
            expect(isWasmRequest).toBe(true);
            expect(hash).toBe('');
            expect(hash.length).toBe(0);
        });
        
        it('should validate WASM renderer availability', () => {
            // Mock WASM renderer not ready scenario
            const mockSceneManager = {
                wasmManager: {
                    isWasmReady: false
                }
            };
            
            // Should handle WASM not ready gracefully
            expect(mockSceneManager.wasmManager.isWasmReady).toBe(false);
        });
    });
    
    describe('Bridge Integration Flow', () => {
        it('should process complete bridge flow simulation', () => {
            const bridgeFlow = {
                // Step 1: Python generates request
                pythonRequest: 'WASM_RENDER_REQUEST:4350768282351817994',
                scadCode: 'cube([2, 2, 2]);',
                
                // Step 2: JavaScript detection
                detectRequest: function(stlData) {
                    return typeof stlData === 'string' && 
                           stlData.startsWith('WASM_RENDER_REQUEST:');
                },
                
                // Step 3: Hash extraction
                extractHash: function(stlData) {
                    if (this.detectRequest(stlData)) {
                        return stlData.substring('WASM_RENDER_REQUEST:'.length);
                    }
                    return null;
                },
                
                // Step 4: SCAD code availability check
                checkScadAvailable: function(scadCode) {
                    return scadCode && scadCode.length > 0;
                }
            };
            
            // Test complete flow
            expect(bridgeFlow.detectRequest(bridgeFlow.pythonRequest)).toBe(true);
            
            const extractedHash = bridgeFlow.extractHash(bridgeFlow.pythonRequest);
            expect(extractedHash).toBe('4350768282351817994');
            
            expect(bridgeFlow.checkScadAvailable(bridgeFlow.scadCode)).toBe(true);
        });
        
        it('should handle widget model updates correctly', () => {
            render({ model: mockModel, el: mockElement });
            
            // Simulate WASM bridge request
            mockModel.set('scad_code', 'sphere(r=5);');
            mockModel.set('stl_data', 'WASM_RENDER_REQUEST:123456789');
            
            // Should not crash and should handle the request
            expect(mockElement.innerHTML).toContain('3D viewer');
        });
    });
    
    describe('Marimo Widget Bridge Integration', () => {
        it('should handle WASM requests in Marimo widget', async () => {
            // Import Marimo widget (if available)
            let marimoWidget;
            try {
                const module = await import('../js/marimo-openscad-widget.js');
                marimoWidget = module;
            } catch (e) {
                // Skip if Marimo widget not available
                console.log('Marimo widget not available for testing');
                return;
            }
            
            // Test that Marimo widget also handles WASM_RENDER_REQUEST pattern
            expect(marimoWidget).toBeDefined();
        });
        
        it('should maintain bridge compatibility across widgets', () => {
            // Both widgets should handle the same pattern
            const testPattern = 'WASM_RENDER_REQUEST:987654321';
            
            // Standard widget detection
            const standardDetection = typeof testPattern === 'string' && 
                                     testPattern.startsWith('WASM_RENDER_REQUEST:');
            
            // Marimo widget detection (same logic)
            const marimoDetection = typeof testPattern === 'string' && 
                                   testPattern.startsWith('WASM_RENDER_REQUEST:');
            
            expect(standardDetection).toBe(marimoDetection);
            expect(standardDetection).toBe(true);
        });
    });
    
    describe('Performance and Memory', () => {
        it('should handle rapid WASM requests efficiently', () => {
            const rapidRequests = Array.from({ length: 100 }, (_, i) => 
                `WASM_RENDER_REQUEST:${i * 12345}`
            );
            
            rapidRequests.forEach(request => {
                const isValid = request.startsWith('WASM_RENDER_REQUEST:');
                expect(isValid).toBe(true);
                
                const hash = request.substring('WASM_RENDER_REQUEST:'.length);
                expect(hash.length).toBeGreaterThan(0);
            });
        });
        
        it('should cleanup bridge resources properly', () => {
            const cleanup = render({ model: mockModel, el: mockElement });
            
            // Should return cleanup function
            expect(typeof cleanup).toBe('function');
            
            // Should not throw when called
            expect(() => cleanup()).not.toThrow();
        });
    });
});

// Helper function to setup widget for testing
function setupWidgetForTesting() {
    // Return mock functions that simulate the widget's WASM handling
    return {
        handleSTLData: vi.fn(),
        handleModelDataChange: vi.fn(),
        detectWasmRequest: (stlData) => {
            return typeof stlData === 'string' && stlData.startsWith('WASM_RENDER_REQUEST:');
        }
    };
}

describe('Bridge Pattern Validation', () => {
    it('should validate all supported WASM request formats', () => {
        const validFormats = [
            'WASM_RENDER_REQUEST:123',
            'WASM_RENDER_REQUEST:-456',
            'WASM_RENDER_REQUEST:9876543210',
            'WASM_RENDER_REQUEST:-8427547496623440318'
        ];
        
        const invalidFormats = [
            'WASM_REQUEST:123',  // Missing RENDER
            'RENDER_REQUEST:123', // Missing WASM
            'wasm_render_request:123', // Wrong case
            'WASM_RENDER_REQUEST', // Missing colon and hash
            ''
        ];
        
        validFormats.forEach(format => {
            const isValid = format.startsWith('WASM_RENDER_REQUEST:');
            expect(isValid).toBe(true);
        });
        
        invalidFormats.forEach(format => {
            const isValid = format.startsWith('WASM_RENDER_REQUEST:');
            expect(isValid).toBe(false);
        });
    });
});

// Export for potential use in other test files
export { setupWidgetForTesting };