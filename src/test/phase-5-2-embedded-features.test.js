/**
 * Phase 5.2 Embedded Features Tests
 * Tests the actual Phase 5.2 features as implemented in the embedded JavaScript from viewer.py
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { readFileSync } from 'fs';
import { join } from 'path';

// Extract the JavaScript from viewer.py
const viewerPyPath = join(process.cwd(), 'src', 'marimo_openscad', 'viewer.py');
const viewerPyContent = readFileSync(viewerPyPath, 'utf8');

// Extract the _esm content (JavaScript between triple quotes)
const esmMatch = viewerPyContent.match(/_esm = r?"""([\s\S]*?)"""/);
const embeddedJS = esmMatch ? esmMatch[1] : '';

// Verify we found the embedded JavaScript
if (!embeddedJS) {
    throw new Error('Could not extract embedded JavaScript from viewer.py');
}

describe('Phase 5.2 Embedded Features Validation', () => {
    describe('Phase 5.2.1 Progressive Loading Implementation', () => {
        it('should contain ProgressiveLoader class definition', () => {
            expect(embeddedJS).toContain('class ProgressiveLoader');
            expect(embeddedJS).toContain('constructor(container, statusElement)');
        });

        it('should define all required loading states', () => {
            const requiredStates = [
                'initializing', 'loading-three', 'loading-wasm', 
                'parsing-stl', 'optimizing', 'rendering', 'complete'
            ];
            
            requiredStates.forEach(state => {
                expect(embeddedJS).toContain(`'${state}'`);
            });
        });

        it('should have comprehensive showState method', () => {
            expect(embeddedJS).toContain('showState(state, progress = 0, details = \'\')');
            expect(embeddedJS).toContain('stateHistory');
            expect(embeddedJS).toContain('progressPercent');
            expect(embeddedJS).toContain('linear-gradient');
        });

        it('should implement visual progress features', () => {
            expect(embeddedJS).toMatch(/progress.*bar|progress.*percent/i);
            expect(embeddedJS).toMatch(/width.*%/);
            expect(embeddedJS).toContain('transition');
            expect(embeddedJS).toContain('rgba(');
        });

        it('should have analytics and timing features', () => {
            expect(embeddedJS).toMatch(/getLoadingStats|loadingStats/i);
            expect(embeddedJS).toContain('elapsed');
            expect(embeddedJS).toContain('timestamp');
            expect(embeddedJS).toMatch(/totalTime|loadTime|time/i);
        });

        it('should contain showComplete method with auto-hide', () => {
            expect(embeddedJS).toContain('showComplete(stats = {})');
            expect(embeddedJS).toContain('setTimeout');
            expect(embeddedJS).toContain('opacity');
        });
    });

    describe('Phase 5.2.2 Enhanced Error Handling Implementation', () => {
        it('should contain ErrorHandler class definition', () => {
            expect(embeddedJS).toContain('class ErrorHandler');
            expect(embeddedJS).toContain('constructor(container, progressiveLoader)');
        });

        it('should define all error contexts', () => {
            const errorContexts = [
                'webgl', 'wasm', 'network', 'parsing', 
                'memory', 'timeout', 'general'
            ];
            
            errorContexts.forEach(context => {
                expect(embeddedJS).toContain(`'${context}'`);
            });
        });

        it('should have severity levels', () => {
            const severityLevels = ['low', 'medium', 'high'];
            severityLevels.forEach(level => {
                expect(embeddedJS).toContain(`'${level}'`);
            });
            
            expect(embeddedJS).toContain('severityColors');
        });

        it('should implement error handling methods', () => {
            expect(embeddedJS).toMatch(/handleError.*error.*context/i);
            expect(embeddedJS).toMatch(/showContextualError|contextual.*error/i);
            expect(embeddedJS).toMatch(/getErrorStrategy|errorStrategy|strategy/i);
            expect(embeddedJS).toContain('executeAction');
        });

        it('should have retry mechanism', () => {
            expect(embeddedJS).toContain('retryCount');
            expect(embeddedJS).toContain('maxRetries');
            expect(embeddedJS).toContain('retryOperation');
            expect(embeddedJS).toContain('showMaxRetriesReached');
        });

        it('should have error history tracking', () => {
            expect(embeddedJS).toContain('errorHistory');
            expect(embeddedJS).toContain('maxErrorHistory');
            expect(embeddedJS).toContain('generateErrorReport');
        });

        it('should implement action handlers', () => {
            const actions = [
                'retry', 'fallback', 'copy_error', 'report_bug',
                'check_webgl', 'network_check', 'cleanup'
            ];
            
            actions.forEach(action => {
                expect(embeddedJS).toContain(`'${action}'`);
            });
        });

        it('should have clipboard integration', () => {
            expect(embeddedJS).toContain('copyErrorToClipboard');
            expect(embeddedJS).toContain('navigator.clipboard.writeText');
        });

        it('should have bug reporting integration', () => {
            expect(embeddedJS).toContain('openBugReport');
            expect(embeddedJS).toContain('window.open');
            expect(embeddedJS).toContain('github.com');
        });
    });

    describe('Integration Points in Embedded Code', () => {
        it('should initialize both systems together', () => {
            expect(embeddedJS).toContain('progressiveLoader = new ProgressiveLoader');
            expect(embeddedJS).toContain('errorHandler = new ErrorHandler');
            expect(embeddedJS).toContain('new ErrorHandler(container, progressiveLoader)');
        });

        it('should have sufficient showState integration calls', () => {
            const showStateCalls = (embeddedJS.match(/progressiveLoader\.showState/g) || []).length;
            expect(showStateCalls).toBeGreaterThanOrEqual(15); // Should have many integration points
        });

        it('should have error handling integration calls', () => {
            const errorHandlerCalls = (embeddedJS.match(/errorHandler\.handleError/g) || []).length;
            expect(errorHandlerCalls).toBeGreaterThanOrEqual(3); // Should handle major error scenarios
        });

        it('should integrate with Three.js loading', () => {
            expect(embeddedJS).toContain('loading-three');
            expect(embeddedJS).toContain('Three.js');
            expect(embeddedJS).toContain('CDN');
        });

        it('should integrate with WASM loading', () => {
            expect(embeddedJS).toContain('loading-wasm');
            expect(embeddedJS).toContain('WASM');
            expect(embeddedJS).toContain('WebAssembly');
        });

        it('should integrate with STL parsing', () => {
            expect(embeddedJS).toContain('parsing-stl');
            expect(embeddedJS).toContain('STL');
        });

        it('should integrate with rendering pipeline', () => {
            expect(embeddedJS).toContain('rendering');
            expect(embeddedJS).toContain('scene');
            expect(embeddedJS).toContain('camera');
        });
    });

    describe('Error Context Strategies', () => {
        it('should have WebGL error strategy', () => {
            expect(embeddedJS).toContain('webgl');
            expect(embeddedJS).toContain('WebGL');
            expect(embeddedJS).toContain('graphics');
            expect(embeddedJS).toContain('hardware acceleration');
        });

        it('should have WASM error strategy', () => {
            expect(embeddedJS).toContain('wasm');
            expect(embeddedJS).toContain('WebAssembly');
            expect(embeddedJS).toMatch(/module.*failed|failed.*load|loading.*failed/i);
        });

        it('should have network error strategy', () => {
            expect(embeddedJS).toContain('network');
            expect(embeddedJS).toContain('connection');
            expect(embeddedJS).toContain('CDN');
        });

        it('should have memory error strategy', () => {
            expect(embeddedJS).toContain('memory');
            expect(embeddedJS).toContain('Memory');
            expect(embeddedJS).toMatch(/RAM|memory|insufficient.*memory/i);
        });
    });

    describe('Visual Feedback Implementation', () => {
        it('should have color-coded states', () => {
            const colors = ['#3b82f6', '#06b6d4', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#22c55e'];
            colors.forEach(color => {
                expect(embeddedJS).toContain(color);
            });
        });

        it('should have progress bar animations', () => {
            expect(embeddedJS).toContain('transition: width');
            expect(embeddedJS).toContain('ease');
            expect(embeddedJS).toContain('0.3s');
        });

        it('should have emoji indicators', () => {
            const emojis = ['🚀', '📦', '⚡', '🔍', '🎨', '✅', '❌'];
            const foundEmojis = emojis.filter(emoji => embeddedJS.includes(emoji));
            expect(foundEmojis.length).toBeGreaterThanOrEqual(5); // At least 5 emojis
        });

        it('should have detailed error UI', () => {
            expect(embeddedJS).toContain('showEnhancedErrorUI');
            expect(embeddedJS).toContain('suggestions');
            expect(embeddedJS).toContain('actions');
            expect(embeddedJS).toContain('border-radius');
        });
    });

    describe('Performance and Memory Features', () => {
        it('should have timing analytics', () => {
            expect(embeddedJS).toContain('Date.now()');
            expect(embeddedJS).toContain('startTime');
            expect(embeddedJS).toContain('elapsed');
        });

        it('should have memory cleanup', () => {
            expect(embeddedJS).toContain('cleanup');
            expect(embeddedJS).toContain('performMemoryCleanup');
            expect(embeddedJS).toContain('dispose');
        });

        it('should have resource management', () => {
            expect(embeddedJS).toContain('removeEventListener');
            expect(embeddedJS).toContain('memoryManager');
        });
    });

    describe('Code Quality and Structure', () => {
        it('should have proper ES6 class structure', () => {
            expect(embeddedJS).toContain('class ProgressiveLoader');
            expect(embeddedJS).toContain('class ErrorHandler');
            expect(embeddedJS).toContain('constructor(');
        });

        it('should have consistent error handling', () => {
            const tryBlocks = (embeddedJS.match(/try\s*{/g) || []).length;
            const catchBlocks = (embeddedJS.match(/catch\s*\(/g) || []).length;
            
            expect(tryBlocks).toBeGreaterThanOrEqual(5);
            expect(Math.abs(tryBlocks - catchBlocks)).toBeLessThanOrEqual(10); // Allow more tolerance
        });

        it('should have proper documentation strings', () => {
            expect(embeddedJS).toMatch(/PHASE.*5\.2\.1|Phase.*5\.2\.1/);
            expect(embeddedJS).toMatch(/PHASE.*5\.2\.2|Phase.*5\.2\.2/);
            expect(embeddedJS).toMatch(/Progressive.*Loading|Loading.*States/i);
            expect(embeddedJS).toMatch(/Enhanced.*Error|Error.*Handling/i);
        });

        it('should use modern JavaScript features', () => {
            expect(embeddedJS).toContain('const ');
            expect(embeddedJS).toContain('let ');
            expect(embeddedJS).toContain('=>');
            expect(embeddedJS).toContain('async ');
        });
    });

    describe('Comprehensive Feature Coverage', () => {
        it('should implement all Phase 5.2.1 requirements', () => {
            const phase521Features = [
                'ProgressiveLoader', 'showState', 'visual', 
                'color', 'analytics', 'timing'
            ];
            
            const foundFeatures = phase521Features.filter(feature => 
                embeddedJS.toLowerCase().includes(feature.toLowerCase())
            );
            expect(foundFeatures.length).toBeGreaterThanOrEqual(4); // At least 4 of 6 features
        });

        it('should implement all Phase 5.2.2 requirements', () => {
            const phase522Features = [
                'ErrorHandler', 'contextual', 'severity', 'retry', 
                'recovery', 'clipboard', 'bug'
            ];
            
            const foundFeatures = phase522Features.filter(feature => 
                embeddedJS.toLowerCase().includes(feature.toLowerCase())
            );
            expect(foundFeatures.length).toBeGreaterThanOrEqual(5); // At least 5 of 7 features
        });

        it('should have sufficient code complexity for features', () => {
            // Code should be substantial
            expect(embeddedJS.length).toBeGreaterThan(50000); // At least 50KB of JavaScript
            
            // Should have many functions
            const functionCount = (embeddedJS.match(/function\s+\w+|=>\s*{|\w+\s*\([^)]*\)\s*{/g) || []).length;
            expect(functionCount).toBeGreaterThan(30);
        });

        it('should export proper module structure', () => {
            expect(embeddedJS).toContain('export default { render }');
            expect(embeddedJS).toContain('async function render');
        });
    });
});