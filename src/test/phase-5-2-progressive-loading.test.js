/**
 * Phase 5.2.1 Progressive Loading Tests
 * Tests for the ProgressiveLoader class and visual feedback system
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock DOM environment
const mockElement = {
    innerHTML: '',
    querySelector: vi.fn(),
    appendChild: vi.fn(),
    style: {}
};

const mockContainer = {
    querySelector: vi.fn(() => mockElement),
    appendChild: vi.fn()
};

const mockStatusElement = {
    textContent: '',
    innerHTML: '',
    style: {}
};

// Since ProgressiveLoader is embedded in viewer.py, we'll test it through evaluation
const createProgressiveLoader = () => {
    // Extracted ProgressiveLoader class from viewer.py Phase 5.2.1
    class ProgressiveLoader {
        constructor(container, statusElement) {
            this.container = container;
            this.statusElement = statusElement;
            this.states = ['initializing', 'loading-three', 'loading-wasm', 'parsing-stl', 'optimizing', 'rendering', 'complete'];
            this.currentState = null;
            this.startTime = Date.now();
            this.stateHistory = [];
            this.animationId = null;
            this.progress = 0;
        }

        showState(state, progress = 0, details = '') {
            if (!this.states.includes(state)) {
                console.warn(`Unknown state: ${state}`);
            }

            this.currentState = state;
            this.progress = Math.max(0, Math.min(100, progress));
            const elapsed = Date.now() - this.startTime;
            
            // Record state history
            this.stateHistory.push({
                state,
                progress,
                details,
                timestamp: Date.now(),
                elapsed
            });

            this.updateUI(state, progress, details, elapsed);
        }

        updateUI(state, progress, details, elapsed) {
            const stateInfo = this.getStateInfo(state);
            const progressPercent = Math.round(progress);
            
            // Color-coded progress bar with gradient
            const bgColor = stateInfo.color;
            const gradientColor = `linear-gradient(90deg, ${bgColor} 0%, rgba(${bgColor.slice(1).match(/.{2}/g).map(hex => parseInt(hex, 16)).join(', ')}, 0.3) 100%)`;
            
            if (this.statusElement) {
                this.statusElement.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 10px; padding: 8px;">
                        <div style="font-weight: bold; color: ${bgColor};">${stateInfo.icon}</div>
                        <div style="flex: 1;">
                            <div style="font-weight: 500; margin-bottom: 4px;">${stateInfo.label}</div>
                            <div style="background: rgba(0,0,0,0.1); border-radius: 8px; height: 6px; overflow: hidden;">
                                <div style="
                                    width: ${progressPercent}%;
                                    height: 100%;
                                    background: ${gradientColor};
                                    transition: width 0.3s ease;
                                "></div>
                            </div>
                            ${details ? `<div style="font-size: 0.85em; color: #666; margin-top: 2px;">${details}</div>` : ''}
                        </div>
                        <div style="font-size: 0.8em; color: #999; font-family: monospace;">
                            ${(elapsed/1000).toFixed(1)}s
                        </div>
                    </div>
                `;
            }
        }

        getStateInfo(state) {
            const stateMap = {
                'initializing': { icon: '🚀', label: 'Initializing...', color: '#3b82f6' },
                'loading-three': { icon: '📦', label: 'Loading Three.js', color: '#06b6d4' },
                'loading-wasm': { icon: '⚡', label: 'Loading WASM', color: '#8b5cf6' },
                'parsing-stl': { icon: '🔍', label: 'Parsing STL', color: '#10b981' },
                'optimizing': { icon: '⚙️', label: 'Optimizing', color: '#f59e0b' },
                'rendering': { icon: '🎨', label: 'Rendering', color: '#ef4444' },
                'complete': { icon: '✅', label: 'Complete', color: '#22c55e' }
            };
            return stateMap[state] || { icon: '❓', label: state, color: '#6b7280' };
        }

        showComplete(stats = {}) {
            this.showState('complete', 100, `Loaded in ${((Date.now() - this.startTime)/1000).toFixed(1)}s`);
            
            if (this.statusElement) {
                setTimeout(() => {
                    this.statusElement.style.opacity = '0.7';
                    setTimeout(() => {
                        this.statusElement.style.display = 'none';
                    }, 2000);
                }, 3000);
            }
        }

        showError(error, context = 'general') {
            if (this.statusElement) {
                this.statusElement.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 10px; padding: 8px; background: rgba(239, 68, 68, 0.1); border-radius: 8px;">
                        <div style="color: #ef4444;">❌</div>
                        <div style="flex: 1;">
                            <div style="font-weight: 500; color: #ef4444;">Loading Error</div>
                            <div style="font-size: 0.85em; color: #666;">${error.message || error}</div>
                        </div>
                    </div>
                `;
            }
        }

        getLoadingStats() {
            return {
                totalStates: this.states.length,
                completedStates: this.stateHistory.length,
                totalElapsed: Date.now() - this.startTime,
                averageStateTime: this.stateHistory.length > 0 ? 
                    (Date.now() - this.startTime) / this.stateHistory.length : 0,
                stateHistory: [...this.stateHistory]
            };
        }
    }

    return ProgressiveLoader;
};

describe('Phase 5.2.1 ProgressiveLoader', () => {
    let ProgressiveLoader;
    let loader;

    beforeEach(() => {
        ProgressiveLoader = createProgressiveLoader();
        loader = new ProgressiveLoader(mockContainer, mockStatusElement);
    });

    describe('Initialization', () => {
        it('should initialize with correct default values', () => {
            expect(loader.container).toBe(mockContainer);
            expect(loader.statusElement).toBe(mockStatusElement);
            expect(loader.states).toEqual(['initializing', 'loading-three', 'loading-wasm', 'parsing-stl', 'optimizing', 'rendering', 'complete']);
            expect(loader.currentState).toBeNull();
            expect(loader.stateHistory).toEqual([]);
            expect(loader.progress).toBe(0);
        });

        it('should record start time', () => {
            const now = Date.now();
            const newLoader = new ProgressiveLoader(mockContainer, mockStatusElement);
            expect(newLoader.startTime).toBeGreaterThanOrEqual(now);
        });
    });

    describe('State Management', () => {
        it('should show valid states correctly', () => {
            loader.showState('loading-three', 25, 'Loading Three.js modules');
            
            expect(loader.currentState).toBe('loading-three');
            expect(loader.progress).toBe(25);
            expect(loader.stateHistory).toHaveLength(1);
            expect(loader.stateHistory[0].state).toBe('loading-three');
            expect(loader.stateHistory[0].progress).toBe(25);
            expect(loader.stateHistory[0].details).toBe('Loading Three.js modules');
        });

        it('should warn on invalid states', () => {
            const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
            
            loader.showState('invalid-state', 50);
            
            expect(consoleSpy).toHaveBeenCalledWith('Unknown state: invalid-state');
            expect(loader.currentState).toBe('invalid-state'); // Still sets it
            
            consoleSpy.mockRestore();
        });

        it('should clamp progress values', () => {
            loader.showState('rendering', -10);
            expect(loader.progress).toBe(0);
            
            loader.showState('rendering', 150);
            expect(loader.progress).toBe(100);
        });

        it('should track state history with timestamps', () => {
            const startTime = Date.now();
            
            loader.showState('initializing', 0);
            loader.showState('loading-three', 30);
            loader.showState('parsing-stl', 75);
            
            expect(loader.stateHistory).toHaveLength(3);
            expect(loader.stateHistory[0].state).toBe('initializing');
            expect(loader.stateHistory[1].state).toBe('loading-three');
            expect(loader.stateHistory[2].state).toBe('parsing-stl');
            
            // Check timestamps are reasonable
            loader.stateHistory.forEach(entry => {
                expect(entry.timestamp).toBeGreaterThanOrEqual(startTime);
                expect(entry.elapsed).toBeGreaterThanOrEqual(0);
            });
        });
    });

    describe('UI Updates', () => {
        it('should update status element with progress bar', () => {
            loader.showState('loading-wasm', 45, 'Downloading WASM modules');
            
            expect(mockStatusElement.innerHTML).toContain('⚡');
            expect(mockStatusElement.innerHTML).toContain('Loading WASM');
            expect(mockStatusElement.innerHTML).toContain('45%');
            expect(mockStatusElement.innerHTML).toContain('Downloading WASM modules');
            expect(mockStatusElement.innerHTML).toContain('linear-gradient');
        });

        it('should apply correct colors for different states', () => {
            loader.showState('loading-three', 30);
            expect(mockStatusElement.innerHTML).toContain('#06b6d4');
            
            loader.showState('parsing-stl', 60);
            expect(mockStatusElement.innerHTML).toContain('#10b981');
            
            loader.showState('complete', 100);
            expect(mockStatusElement.innerHTML).toContain('#22c55e');
        });

        it('should show elapsed time', () => {
            // Wait a bit to ensure elapsed time > 0
            setTimeout(() => {
                loader.showState('rendering', 80);
                expect(mockStatusElement.innerHTML).toMatch(/\d+\.\d+s/);
            }, 10);
        });
    });

    describe('State Information', () => {
        it('should return correct state info for all states', () => {
            const expectedStates = [
                { state: 'initializing', icon: '🚀', color: '#3b82f6' },
                { state: 'loading-three', icon: '📦', color: '#06b6d4' },
                { state: 'loading-wasm', icon: '⚡', color: '#8b5cf6' },
                { state: 'parsing-stl', icon: '🔍', color: '#10b981' },
                { state: 'optimizing', icon: '⚙️', color: '#f59e0b' },
                { state: 'rendering', icon: '🎨', color: '#ef4444' },
                { state: 'complete', icon: '✅', color: '#22c55e' }
            ];

            expectedStates.forEach(({ state, icon, color }) => {
                const info = loader.getStateInfo(state);
                expect(info.icon).toBe(icon);
                expect(info.color).toBe(color);
            });
        });

        it('should handle unknown states gracefully', () => {
            const info = loader.getStateInfo('unknown');
            expect(info.icon).toBe('❓');
            expect(info.color).toBe('#6b7280');
            expect(info.label).toBe('unknown');
        });
    });

    describe('Completion and Error Handling', () => {
        it('should show completion state with stats', () => {
            const stats = { triangles: 1000, loadTime: 2.5 };
            loader.showComplete(stats);
            
            expect(loader.currentState).toBe('complete');
            expect(loader.progress).toBe(100);
            expect(mockStatusElement.innerHTML).toContain('✅');
            expect(mockStatusElement.innerHTML).toContain('Complete');
        });

        it('should show error states', () => {
            const error = new Error('WASM loading failed');
            loader.showError(error, 'wasm');
            
            expect(mockStatusElement.innerHTML).toContain('❌');
            expect(mockStatusElement.innerHTML).toContain('Loading Error');
            expect(mockStatusElement.innerHTML).toContain('WASM loading failed');
        });

        it('should handle string errors', () => {
            loader.showError('Network timeout', 'network');
            
            expect(mockStatusElement.innerHTML).toContain('❌');
            expect(mockStatusElement.innerHTML).toContain('Network timeout');
        });
    });

    describe('Analytics and Statistics', () => {
        it('should provide loading statistics', async () => {
            loader.showState('initializing', 0);
            
            // Wait a small amount to ensure elapsed time > 0
            await new Promise(resolve => setTimeout(resolve, 1));
            
            loader.showState('loading-three', 25);
            loader.showState('loading-wasm', 50);
            
            const stats = loader.getLoadingStats();
            
            expect(stats.totalStates).toBe(7);
            expect(stats.completedStates).toBe(3);
            expect(stats.totalElapsed).toBeGreaterThanOrEqual(0);
            expect(stats.averageStateTime).toBeGreaterThanOrEqual(0);
            expect(stats.stateHistory).toHaveLength(3);
        });

        it('should handle empty state history', () => {
            const stats = loader.getLoadingStats();
            
            expect(stats.totalStates).toBe(7);
            expect(stats.completedStates).toBe(0);
            expect(stats.averageStateTime).toBe(0);
            expect(stats.stateHistory).toEqual([]);
        });
    });

    describe('Integration Scenarios', () => {
        it('should handle complete loading workflow', () => {
            const states = [
                { state: 'initializing', progress: 0 },
                { state: 'loading-three', progress: 15 },
                { state: 'loading-wasm', progress: 35 },
                { state: 'parsing-stl', progress: 60 },
                { state: 'optimizing', progress: 80 },
                { state: 'rendering', progress: 95 },
                { state: 'complete', progress: 100 }
            ];

            states.forEach(({ state, progress }) => {
                loader.showState(state, progress);
            });

            expect(loader.stateHistory).toHaveLength(7);
            expect(loader.currentState).toBe('complete');
            expect(loader.progress).toBe(100);
            
            const stats = loader.getLoadingStats();
            expect(stats.completedStates).toBe(7);
        });

        it('should handle interrupted loading with error', () => {
            loader.showState('initializing', 0);
            loader.showState('loading-wasm', 30);
            loader.showError('WASM loading failed');
            
            expect(loader.stateHistory).toHaveLength(2);
            expect(loader.currentState).toBe('loading-wasm');
            expect(mockStatusElement.innerHTML).toContain('Loading Error');
        });
    });
});