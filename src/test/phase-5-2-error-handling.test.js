/**
 * Phase 5.2.2 Enhanced Error Handling Tests
 * Tests for the ErrorHandler class and contextual error strategies
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock DOM environment
const mockElement = {
    innerHTML: '',
    querySelector: vi.fn(),
    appendChild: vi.fn(),
    style: {},
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    remove: vi.fn(),
    contains: vi.fn(() => false)
};

const mockContainer = {
    querySelector: vi.fn(() => mockElement),
    appendChild: vi.fn(),
    contains: vi.fn(() => false)
};

const mockProgressiveLoader = {
    showError: vi.fn()
};

// Mock clipboard API
global.navigator = {
    clipboard: {
        writeText: vi.fn().mockResolvedValue()
    }
};

// Mock window.open and document
global.window = {
    open: vi.fn()
};

global.document = {
    createElement: vi.fn(() => ({
        ...mockElement,
        id: ''
    }))
};

// Extracted ErrorHandler class from viewer.py Phase 5.2.2
const createErrorHandler = () => {
    class ErrorHandler {
        constructor(container, progressiveLoader) {
            this.container = container;
            this.progressiveLoader = progressiveLoader;
            this.errorHistory = [];
            this.maxErrorHistory = 10;
            this.retryCount = 0;
            this.maxRetries = 3;
            this.severityColors = {
                low: '#fbbf24',
                medium: '#f97316', 
                high: '#ef4444'
            };
        }

        handleError(error, context = 'general', retryCallback = null) {
            console.error(`[${context.toUpperCase()}] Error:`, error);
            
            // Record error in history
            this.errorHistory.push({
                error: error.message || error.toString(),
                context,
                timestamp: Date.now(),
                stack: error.stack || 'No stack trace',
                retryCount: this.retryCount
            });
            
            // Limit error history size
            if (this.errorHistory.length > this.maxErrorHistory) {
                this.errorHistory = this.errorHistory.slice(-this.maxErrorHistory);
            }
            
            // Get contextual error strategy
            const strategy = this.getErrorStrategy(context, error);
            
            // Show contextual error UI
            this.showContextualError(error, context, retryCallback);
            
            // Execute automatic actions if available
            if (strategy.autoActions && strategy.autoActions.length > 0) {
                this.executeAutoActions(strategy.autoActions, error, context);
            }
            
            return strategy;
        }

        getErrorStrategy(context, error) {
            const strategies = {
                webgl: {
                    severity: 'high',
                    title: 'WebGL Error',
                    description: 'Graphics rendering failed. Your browser may not support WebGL or hardware acceleration.',
                    suggestions: [
                        'Try enabling hardware acceleration in browser settings',
                        'Update your graphics drivers',
                        'Use a different browser (Chrome/Firefox recommended)',
                        'Check if WebGL is supported: get.webgl.org'
                    ],
                    actions: ['check_webgl', 'fallback', 'retry'],
                    autoActions: ['check_webgl']
                },
                wasm: {
                    severity: 'medium',
                    title: 'WebAssembly Error',
                    description: 'WASM module failed to load or execute. Falling back to alternative rendering.',
                    suggestions: [
                        'Check your internet connection',
                        'Clear browser cache and reload',
                        'Try disabling browser extensions',
                        'Use local OpenSCAD renderer as fallback'
                    ],
                    actions: ['retry', 'fallback', 'cleanup'],
                    autoActions: ['cleanup']
                },
                network: {
                    severity: 'medium',
                    title: 'Network Error',
                    description: 'Failed to load external resources. Check your connection.',
                    suggestions: [
                        'Check your internet connection',
                        'Try refreshing the page',
                        'Check if CDN resources are accessible',
                        'Use offline mode if available'
                    ],
                    actions: ['retry', 'network_check', 'fallback'],
                    autoActions: ['network_check']
                },
                parsing: {
                    severity: 'low',
                    title: 'Parsing Error',
                    description: 'Failed to parse STL or SCAD data. The file may be corrupted.',
                    suggestions: [
                        'Check if the file is valid STL/SCAD format',
                        'Try re-exporting from your CAD software',
                        'Reduce model complexity',
                        'Use ASCII STL format instead of binary'
                    ],
                    actions: ['retry', 'fallback', 'copy_error'],
                    autoActions: []
                },
                memory: {
                    severity: 'high',
                    title: 'Memory Error',
                    description: 'Insufficient memory to process the model. Try reducing complexity.',
                    suggestions: [
                        'Close other browser tabs',
                        'Reduce model complexity or resolution',
                        'Try on a device with more RAM',
                        'Use mesh decimation tools'
                    ],
                    actions: ['cleanup', 'fallback', 'retry'],
                    autoActions: ['cleanup']
                },
                timeout: {
                    severity: 'medium',
                    title: 'Timeout Error',
                    description: 'Operation took too long to complete.',
                    suggestions: [
                        'Try again with a smaller model',
                        'Check your internet connection speed',
                        'Increase timeout settings if available',
                        'Consider using local rendering'
                    ],
                    actions: ['retry', 'fallback', 'cleanup'],
                    autoActions: []
                },
                general: {
                    severity: 'low',
                    title: 'General Error',
                    description: 'An unexpected error occurred.',
                    suggestions: [
                        'Try refreshing the page',
                        'Check browser console for details',
                        'Report the issue if it persists',
                        'Try using a different browser'
                    ],
                    actions: ['retry', 'copy_error', 'report_bug'],
                    autoActions: []
                }
            };
            
            return strategies[context] || strategies.general;
        }

        showContextualError(error, context, retryCallback) {
            const strategy = this.getErrorStrategy(context, error);
            
            // Use progressive loader if available
            if (this.progressiveLoader && this.progressiveLoader.showError) {
                this.progressiveLoader.showError(error, context);
            }
            
            this.showEnhancedErrorUI(strategy, error, retryCallback);
        }

        showEnhancedErrorUI(strategy, error, retryCallback) {
            if (!this.container) return;
            
            const errorContainer = this.container.querySelector('#error-container') || 
                                 document.createElement('div');
            errorContainer.id = 'error-container';
            
            const severityColor = this.severityColors[strategy.severity];
            const suggestionsHtml = strategy.suggestions
                .map(s => `<li style="margin: 4px 0;">${s}</li>`)
                .join('');
            
            const actionsHtml = strategy.actions
                .map(action => {
                    const actionInfo = this.getActionInfo(action);
                    return `
                        <button onclick="errorHandler.executeAction('${action}', '${error.message || error}', '${strategy.title}')" 
                                style="margin: 4px; padding: 6px 12px; border: 1px solid ${severityColor}; 
                                       background: white; color: ${severityColor}; border-radius: 4px; cursor: pointer;">
                            ${actionInfo.icon} ${actionInfo.label}
                        </button>
                    `;
                })
                .join('');
            
            errorContainer.innerHTML = `
                <div style="border: 2px solid ${severityColor}; border-radius: 8px; margin: 10px; 
                           background: rgba(${this.hexToRgb(severityColor)}, 0.05);">
                    <div style="background: ${severityColor}; color: white; padding: 12px; font-weight: bold;">
                        🚨 ${strategy.title} (${strategy.severity.toUpperCase()})
                    </div>
                    <div style="padding: 16px;">
                        <div style="margin-bottom: 12px; font-weight: 500;">
                            ${strategy.description}
                        </div>
                        <div style="background: #f8f9fa; padding: 8px; border-radius: 4px; margin-bottom: 12px; font-family: monospace; font-size: 0.9em;">
                            ${error.message || error}
                        </div>
                        <details style="margin-bottom: 12px;">
                            <summary style="cursor: pointer; font-weight: 500;">💡 Suggestions</summary>
                            <ul style="margin: 8px 0; padding-left: 20px;">
                                ${suggestionsHtml}
                            </ul>
                        </details>
                        <div style="margin-bottom: 12px;">
                            <strong>🔧 Actions:</strong><br>
                            ${actionsHtml}
                        </div>
                        <details>
                            <summary style="cursor: pointer; font-size: 0.9em; color: #666;">🔍 Error History (${this.errorHistory.length})</summary>
                            <div style="max-height: 150px; overflow-y: auto; margin-top: 8px;">
                                ${this.renderErrorHistory()}
                            </div>
                        </details>
                    </div>
                </div>
            `;
            
            if (!this.container.contains(errorContainer)) {
                this.container.appendChild(errorContainer);
            }
        }

        getActionInfo(action) {
            const actions = {
                retry: { icon: '🔄', label: 'Retry' },
                fallback: { icon: '🔄', label: 'Use Fallback' },
                copy_error: { icon: '📋', label: 'Copy Error' },
                report_bug: { icon: '🐛', label: 'Report Bug' },
                check_webgl: { icon: '🎮', label: 'Check WebGL' },
                network_check: { icon: '🌐', label: 'Check Network' },
                cleanup: { icon: '🧹', label: 'Cleanup Memory' }
            };
            return actions[action] || { icon: '❓', label: action };
        }

        executeAction(action, errorMessage, errorTitle) {
            console.log(`Executing action: ${action} for error: ${errorTitle}`);
            
            switch (action) {
                case 'retry':
                    this.retryOperation();
                    break;
                case 'fallback':
                    this.activateFallback();
                    break;
                case 'copy_error':
                    this.copyErrorToClipboard(errorMessage, errorTitle);
                    break;
                case 'report_bug':
                    this.openBugReport(errorMessage, errorTitle);
                    break;
                case 'check_webgl':
                    this.checkWebGLSupport();
                    break;
                case 'network_check':
                    this.runNetworkDiagnostics();
                    break;
                case 'cleanup':
                    this.performMemoryCleanup();
                    break;
                default:
                    console.warn(`Unknown action: ${action}`);
            }
        }

        executeAutoActions(actions, error, context) {
            actions.forEach(action => {
                try {
                    this.executeAction(action, error.message || error, context);
                } catch (autoError) {
                    console.warn(`Auto-action ${action} failed:`, autoError);
                }
            });
        }

        retryOperation() {
            if (this.retryCount >= this.maxRetries) {
                this.showMaxRetriesReached();
                return false;
            }
            
            this.retryCount++;
            console.log(`Retry attempt ${this.retryCount}/${this.maxRetries}`);
            
            // Clear error UI
            const errorContainer = this.container?.querySelector('#error-container');
            if (errorContainer) {
                errorContainer.remove();
            }
            
            return true;
        }

        showMaxRetriesReached() {
            if (this.container) {
                const notice = document.createElement('div');
                notice.innerHTML = `
                    <div style="background: #fee; border: 1px solid #fcc; padding: 12px; border-radius: 6px; margin: 10px;">
                        🚫 <strong>Maximum retries reached (${this.maxRetries})</strong><br>
                        Please try a different approach or contact support.
                    </div>
                `;
                this.container.appendChild(notice);
            }
        }

        activateFallback() {
            console.log('🔄 Activating fallback mode');
            // Implementation would depend on specific fallback strategy
        }

        async copyErrorToClipboard(errorMessage, errorTitle) {
            const errorReport = this.generateErrorReport(errorMessage, errorTitle);
            try {
                await navigator.clipboard.writeText(errorReport);
                console.log('✅ Error copied to clipboard');
            } catch (err) {
                console.warn('Failed to copy to clipboard:', err);
            }
        }

        openBugReport(errorMessage, errorTitle) {
            const errorReport = this.generateErrorReport(errorMessage, errorTitle);
            const url = `https://github.com/your-repo/issues/new?title=${encodeURIComponent(errorTitle)}&body=${encodeURIComponent(errorReport)}`;
            window.open(url, '_blank');
        }

        generateErrorReport(errorMessage, errorTitle) {
            return `
# Error Report: ${errorTitle}

**Error Message:** ${errorMessage}
**Timestamp:** ${new Date().toISOString()}
**Browser:** ${navigator.userAgent}
**Error History:** ${this.errorHistory.length} recent errors

## Recent Error History:
${this.errorHistory.slice(-3).map(err => 
    `- [${new Date(err.timestamp).toLocaleTimeString()}] ${err.context}: ${err.error}`
).join('\n')}

## Additional Context:
Please add any additional context about what you were trying to do when this error occurred.
            `.trim();
        }

        checkWebGLSupport() {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            
            if (gl) {
                console.log('✅ WebGL is supported');
                const info = {
                    vendor: gl.getParameter(gl.VENDOR),
                    renderer: gl.getParameter(gl.RENDERER),
                    version: gl.getParameter(gl.VERSION)
                };
                console.log('WebGL Info:', info);
            } else {
                console.log('❌ WebGL is not supported');
            }
        }

        runNetworkDiagnostics() {
            console.log('🌐 Running network diagnostics...');
            // Implementation would test various network endpoints
        }

        performMemoryCleanup() {
            console.log('🧹 Performing memory cleanup...');
            // Implementation would clean up Three.js objects, WASM memory, etc.
        }

        renderErrorHistory() {
            return this.errorHistory
                .slice(-5)
                .reverse()
                .map(err => `
                    <div style="border-bottom: 1px solid #eee; padding: 4px 0; font-size: 0.85em;">
                        <span style="color: #666;">[${new Date(err.timestamp).toLocaleTimeString()}]</span>
                        <strong>${err.context}:</strong> ${err.error}
                    </div>
                `).join('');
        }

        hexToRgb(hex) {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? 
                `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` :
                '0, 0, 0';
        }
    }

    return ErrorHandler;
};

describe('Phase 5.2.2 ErrorHandler', () => {
    let ErrorHandler;
    let errorHandler;

    beforeEach(() => {
        ErrorHandler = createErrorHandler();
        errorHandler = new ErrorHandler(mockContainer, mockProgressiveLoader);
        
        // Reset mocks
        mockProgressiveLoader.showError.mockClear();
        global.navigator.clipboard.writeText.mockClear();
        global.window.open.mockClear();
    });

    describe('Initialization', () => {
        it('should initialize with correct default values', () => {
            expect(errorHandler.container).toBe(mockContainer);
            expect(errorHandler.progressiveLoader).toBe(mockProgressiveLoader);
            expect(errorHandler.errorHistory).toEqual([]);
            expect(errorHandler.maxErrorHistory).toBe(10);
            expect(errorHandler.retryCount).toBe(0);
            expect(errorHandler.maxRetries).toBe(3);
            expect(errorHandler.severityColors).toEqual({
                low: '#fbbf24',
                medium: '#f97316',
                high: '#ef4444'
            });
        });
    });

    describe('Error Handling', () => {
        it('should handle basic errors', () => {
            const error = new Error('Test error');
            const strategy = errorHandler.handleError(error, 'general');
            
            expect(errorHandler.errorHistory).toHaveLength(1);
            expect(errorHandler.errorHistory[0]).toEqual({
                error: 'Test error',
                context: 'general',
                timestamp: expect.any(Number),
                stack: expect.any(String),
                retryCount: 0
            });
            expect(strategy).toBeDefined();
            expect(strategy.title).toBe('General Error');
        });

        it('should handle string errors', () => {
            errorHandler.handleError('String error message', 'network');
            
            expect(errorHandler.errorHistory).toHaveLength(1);
            expect(errorHandler.errorHistory[0].error).toBe('String error message');
            expect(errorHandler.errorHistory[0].context).toBe('network');
        });

        it('should limit error history size', () => {
            // Add more errors than maxErrorHistory
            for (let i = 0; i < 15; i++) {
                errorHandler.handleError(`Error ${i}`, 'test');
            }
            
            expect(errorHandler.errorHistory).toHaveLength(10);
            expect(errorHandler.errorHistory[0].error).toBe('Error 5'); // Should keep latest 10
        });

        it('should call progressive loader showError', () => {
            const error = new Error('WASM error');
            errorHandler.handleError(error, 'wasm');
            
            expect(mockProgressiveLoader.showError).toHaveBeenCalledWith(error, 'wasm');
        });
    });

    describe('Error Strategies', () => {
        it('should return correct strategy for WebGL errors', () => {
            const strategy = errorHandler.getErrorStrategy('webgl', new Error('WebGL error'));
            
            expect(strategy.severity).toBe('high');
            expect(strategy.title).toBe('WebGL Error');
            expect(strategy.actions).toContain('check_webgl');
            expect(strategy.autoActions).toContain('check_webgl');
        });

        it('should return correct strategy for WASM errors', () => {
            const strategy = errorHandler.getErrorStrategy('wasm', new Error('WASM error'));
            
            expect(strategy.severity).toBe('medium');
            expect(strategy.title).toBe('WebAssembly Error');
            expect(strategy.actions).toContain('fallback');
            expect(strategy.autoActions).toContain('cleanup');
        });

        it('should return correct strategy for network errors', () => {
            const strategy = errorHandler.getErrorStrategy('network', new Error('Network error'));
            
            expect(strategy.severity).toBe('medium');
            expect(strategy.title).toBe('Network Error');
            expect(strategy.actions).toContain('network_check');
            expect(strategy.autoActions).toContain('network_check');
        });

        it('should fall back to general strategy for unknown contexts', () => {
            const strategy = errorHandler.getErrorStrategy('unknown', new Error('Unknown error'));
            
            expect(strategy.severity).toBe('low');
            expect(strategy.title).toBe('General Error');
        });
    });

    describe('Action Information', () => {
        it('should return correct action info for all actions', () => {
            const expectedActions = [
                { action: 'retry', icon: '🔄', label: 'Retry' },
                { action: 'fallback', icon: '🔄', label: 'Use Fallback' },
                { action: 'copy_error', icon: '📋', label: 'Copy Error' },
                { action: 'report_bug', icon: '🐛', label: 'Report Bug' },
                { action: 'check_webgl', icon: '🎮', label: 'Check WebGL' },
                { action: 'network_check', icon: '🌐', label: 'Check Network' },
                { action: 'cleanup', icon: '🧹', label: 'Cleanup Memory' }
            ];

            expectedActions.forEach(({ action, icon, label }) => {
                const info = errorHandler.getActionInfo(action);
                expect(info.icon).toBe(icon);
                expect(info.label).toBe(label);
            });
        });

        it('should handle unknown actions gracefully', () => {
            const info = errorHandler.getActionInfo('unknown');
            expect(info.icon).toBe('❓');
            expect(info.label).toBe('unknown');
        });
    });

    describe('Retry Mechanism', () => {
        it('should allow retries within limit', () => {
            const result1 = errorHandler.retryOperation();
            expect(result1).toBe(true);
            expect(errorHandler.retryCount).toBe(1);

            const result2 = errorHandler.retryOperation();
            expect(result2).toBe(true);
            expect(errorHandler.retryCount).toBe(2);

            const result3 = errorHandler.retryOperation();
            expect(result3).toBe(true);
            expect(errorHandler.retryCount).toBe(3);
        });

        it('should reject retries when limit exceeded', () => {
            // Exhaust retries
            errorHandler.retryCount = 3;
            
            const result = errorHandler.retryOperation();
            expect(result).toBe(false);
            expect(errorHandler.retryCount).toBe(3);
        });
    });

    describe('Error Report Generation', () => {
        it('should generate comprehensive error reports', () => {
            errorHandler.handleError('Test error 1', 'webgl');
            errorHandler.handleError('Test error 2', 'wasm');
            
            const report = errorHandler.generateErrorReport('Current error', 'Test Error');
            
            expect(report).toContain('# Error Report: Test Error');
            expect(report).toContain('**Error Message:** Current error');
            expect(report).toContain('**Error History:** 2 recent errors');
            expect(report).toContain('webgl: Test error 1');
            expect(report).toContain('wasm: Test error 2');
        });
    });

    describe('Clipboard Integration', () => {
        it('should copy error reports to clipboard', async () => {
            await errorHandler.copyErrorToClipboard('Test error', 'Test Title');
            
            expect(global.navigator.clipboard.writeText).toHaveBeenCalledWith(
                expect.stringContaining('# Error Report: Test Title')
            );
        });

        it('should handle clipboard failures gracefully', async () => {
            global.navigator.clipboard.writeText.mockRejectedValueOnce(new Error('Clipboard failed'));
            
            const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
            
            await errorHandler.copyErrorToClipboard('Test error', 'Test Title');
            
            expect(consoleSpy).toHaveBeenCalledWith('Failed to copy to clipboard:', expect.any(Error));
            consoleSpy.mockRestore();
        });
    });

    describe('Bug Report Integration', () => {
        it('should open bug report URLs', () => {
            errorHandler.openBugReport('Test error', 'Test Title');
            
            expect(global.window.open).toHaveBeenCalledWith(
                expect.stringContaining('github.com'),
                '_blank'
            );
            
            const calledUrl = global.window.open.mock.calls[0][0];
            expect(calledUrl).toContain('title=Test%20Title');
            expect(calledUrl).toContain('Error%20Report%3A%20Test%20Title');
        });
    });

    describe('Error History Rendering', () => {
        it('should render error history HTML', () => {
            errorHandler.handleError('Error 1', 'webgl');
            errorHandler.handleError('Error 2', 'wasm');
            errorHandler.handleError('Error 3', 'network');
            
            const historyHtml = errorHandler.renderErrorHistory();
            
            expect(historyHtml).toContain('network:</strong> Error 3');
            expect(historyHtml).toContain('wasm:</strong> Error 2');
            expect(historyHtml).toContain('webgl:</strong> Error 1');
        });

        it('should limit history rendering to 5 most recent', () => {
            for (let i = 0; i < 8; i++) {
                errorHandler.handleError(`Error ${i}`, 'test');
            }
            
            const historyHtml = errorHandler.renderErrorHistory();
            const errorCount = (historyHtml.match(/test:<\/strong>/g) || []).length;
            
            expect(errorCount).toBeLessThanOrEqual(5);
        });
    });

    describe('Utility Functions', () => {
        it('should convert hex colors to RGB', () => {
            expect(errorHandler.hexToRgb('#ff0000')).toBe('255, 0, 0');
            expect(errorHandler.hexToRgb('#00ff00')).toBe('0, 255, 0');
            expect(errorHandler.hexToRgb('#0000ff')).toBe('0, 0, 255');
        });

        it('should handle invalid hex colors', () => {
            expect(errorHandler.hexToRgb('invalid')).toBe('0, 0, 0');
        });
    });
});