/**
 * Phase 5.3.1 Performance Monitor Tests
 * Comprehensive tests for FPS tracking and memory monitoring
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

// Mock global APIs
global.performance = {
    memory: {
        usedJSHeapSize: 50 * 1024 * 1024,  // 50MB
        totalJSHeapSize: 100 * 1024 * 1024, // 100MB
        jsHeapSizeLimit: 200 * 1024 * 1024  // 200MB
    },
    now: vi.fn(() => Date.now())
};

global.window = {
    performance: global.performance,
    requestAnimationFrame: vi.fn((callback) => {
        setTimeout(callback, 16); // 60fps
        return 1;
    }),
    cancelAnimationFrame: vi.fn()
};

global.document = {
    createElement: vi.fn((tag) => ({
        tagName: tag.toUpperCase(),
        style: {},
        classList: {
            add: vi.fn(),
            remove: vi.fn(),
            contains: vi.fn(() => false)
        },
        setAttribute: vi.fn(),
        getAttribute: vi.fn(),
        appendChild: vi.fn(),
        removeChild: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        innerHTML: '',
        textContent: '',
        parentNode: { removeChild: vi.fn() },
        remove: vi.fn()
    })),
    body: {
        appendChild: vi.fn(),
        removeChild: vi.fn()
    }
};

// Create PerformanceMonitor test class
function createPerformanceMonitor() {
    const container = {
        style: {},
        classList: {
            add: vi.fn(),
            remove: vi.fn(),
            contains: vi.fn(() => false)
        },
        appendChild: vi.fn(),
        removeChild: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        getBoundingClientRect: () => ({ width: 600, height: 400 })
    };

    const statusElement = {
        style: {},
        innerHTML: '',
        textContent: ''
    };

    // Simplified PerformanceMonitor for testing
    class PerformanceMonitor {
        constructor(container, statusElement) {
            this.container = container;
            this.statusElement = statusElement;
            this.enabled = true;
            
            // FPS tracking
            this.fps = 60;
            this.frameTime = 16.67;
            this.lastFrameTime = performance.now();
            this.frameTimes = [];
            this.frameTimeWindow = 60; // Track last 60 frames
            
            // Memory monitoring
            this.memoryUsage = { used: 0, total: 0, limit: 0 };
            this.memoryHistory = [];
            this.memoryHistoryLimit = 100;
            
            // Performance levels and thresholds
            this.performanceLevel = 'good';
            this.thresholds = {
                excellent: { fps: 55, frameTime: 18 },
                good: { fps: 45, frameTime: 22 },
                poor: { fps: 25, frameTime: 40 },
                critical: { fps: 15, frameTime: 67 }
            };
            
            // Performance HUD
            this.hudVisible = false;
            this.performanceHUD = null;
            this.perfToggleBtn = null;
            
            // Alerts and notifications
            this.lastAlert = 0;
            this.alertCooldown = 5000; // 5 seconds between alerts
            
            // Render stats
            this.renderStats = {
                drawCalls: 0,
                triangles: 0,
                vertices: 0,
                textures: 0
            };
            
            // Monitoring state
            this.isMonitoring = false;
            this.monitoringIntervalId = null;
            
            this.setupPerformanceMonitoring();
        }

        setupPerformanceMonitoring() {
            this.createPerformanceHUD();
            this.createToggleButton();
            this.startMonitoring();
        }

        createPerformanceHUD() {
            this.performanceHUD = document.createElement('div');
            this.performanceHUD.id = 'performance-hud';
            this.performanceHUD.style.display = this.hudVisible ? 'block' : 'none';
            this.container.appendChild(this.performanceHUD);
        }

        createToggleButton() {
            this.perfToggleBtn = document.createElement('button');
            this.perfToggleBtn.textContent = '📊';
            this.perfToggleBtn.addEventListener('click', () => this.toggleHUD());
            this.container.appendChild(this.perfToggleBtn);
        }

        startMonitoring() {
            if (this.isMonitoring) return;
            
            this.isMonitoring = true;
            this.lastFrameTime = performance.now();
            
            const monitorFrame = () => {
                if (!this.enabled || !this.isMonitoring) return;
                
                this.updateFPS();
                this.updateMemoryUsage();
                this.classifyPerformance();
                this.updateHUD();
                
                window.requestAnimationFrame(monitorFrame);
            };
            
            window.requestAnimationFrame(monitorFrame);
            
            // Set up periodic memory monitoring
            this.monitoringIntervalId = setInterval(() => {
                this.updateMemoryUsage();
                this.checkMemoryPressure();
            }, 1000); // Every second
        }

        stopMonitoring() {
            this.isMonitoring = false;
            
            if (this.monitoringIntervalId) {
                clearInterval(this.monitoringIntervalId);
                this.monitoringIntervalId = null;
            }
        }

        updateFPS() {
            const now = performance.now();
            const frameTime = now - this.lastFrameTime;
            
            this.frameTime = frameTime;
            this.fps = frameTime > 0 ? 1000 / frameTime : 60;
            
            // Add to sliding window
            this.frameTimes.push(frameTime);
            if (this.frameTimes.length > this.frameTimeWindow) {
                this.frameTimes.shift();
            }
            
            this.lastFrameTime = now;
        }

        updateMemoryUsage() {
            if (performance.memory) {
                const memory = performance.memory;
                this.memoryUsage = {
                    used: Math.round(memory.usedJSHeapSize / (1024 * 1024)), // MB
                    total: Math.round(memory.totalJSHeapSize / (1024 * 1024)), // MB
                    limit: Math.round(memory.jsHeapSizeLimit / (1024 * 1024)) // MB
                };
                
                // Add to history
                this.memoryHistory.push({
                    timestamp: Date.now(),
                    usage: this.memoryUsage.used,
                    total: this.memoryUsage.total
                });
                
                if (this.memoryHistory.length > this.memoryHistoryLimit) {
                    this.memoryHistory.shift();
                }
            }
        }

        classifyPerformance() {
            const avgFPS = this.getAverageFPS();
            const avgFrameTime = this.getAverageFrameTime();
            
            let newLevel = 'good';
            
            if (avgFPS >= this.thresholds.excellent.fps && avgFrameTime <= this.thresholds.excellent.frameTime) {
                newLevel = 'excellent';
            } else if (avgFPS >= this.thresholds.good.fps && avgFrameTime <= this.thresholds.good.frameTime) {
                newLevel = 'good';
            } else if (avgFPS >= this.thresholds.poor.fps && avgFrameTime <= this.thresholds.poor.frameTime) {
                newLevel = 'poor';
            } else {
                newLevel = 'critical';
            }
            
            if (newLevel !== this.performanceLevel) {
                const oldLevel = this.performanceLevel;
                this.performanceLevel = newLevel;
                this.onPerformanceLevelChange(newLevel, oldLevel);
            }
        }

        onPerformanceLevelChange(newLevel, oldLevel) {
            console.log(`📊 Performance level changed: ${oldLevel} → ${newLevel}`);
            
            // Show alert for performance degradation
            if (this.getPerformanceLevelRank(newLevel) < this.getPerformanceLevelRank(oldLevel)) {
                this.showAlert(`Performance decreased to ${newLevel}`, 'warning');
            }
            
            // Trigger external callbacks
            if (this.onPerformanceChange) {
                this.onPerformanceChange(newLevel, {
                    fps: this.getAverageFPS(),
                    frameTime: this.getAverageFrameTime(),
                    memory: this.memoryUsage
                });
            }
        }

        getPerformanceLevelRank(level) {
            const ranks = { critical: 0, poor: 1, good: 2, excellent: 3 };
            return ranks[level] !== undefined ? ranks[level] : 1;
        }

        checkMemoryPressure() {
            if (!this.memoryUsage.limit) return;
            
            const usageRatio = this.memoryUsage.used / this.memoryUsage.limit;
            
            if (usageRatio > 0.9) {
                this.showAlert('Critical memory usage detected', 'warning');
                if (this.onMemoryPressure) {
                    this.onMemoryPressure(this.memoryUsage);
                }
            } else if (usageRatio > 0.7) {
                this.showAlert('High memory usage detected', 'info');
            }
        }

        showAlert(message, type = 'info') {
            const now = Date.now();
            if (now - this.lastAlert < this.alertCooldown) return;
            
            console.log(`📊 Performance Alert [${type}]: ${message}`);
            this.lastAlert = now;
            
            if (this.performanceHUD) {
                const originalText = this.performanceHUD.textContent;
                const originalBg = this.performanceHUD.style.background;
                
                this.performanceHUD.textContent = `⚠️ ${message}`;
                this.performanceHUD.style.background = type === 'warning' ? 'rgba(255, 193, 7, 0.9)' : 'rgba(0, 123, 255, 0.9)';
                
                setTimeout(() => {
                    this.performanceHUD.textContent = originalText;
                    this.performanceHUD.style.background = originalBg;
                }, 3000);
            }
        }

        getAverageFPS() {
            if (this.frameTimes.length === 0) return 60;
            const avgFrameTime = this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length;
            return 1000 / avgFrameTime;
        }

        getAverageFrameTime() {
            if (this.frameTimes.length === 0) return 16.67;
            return this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length;
        }

        toggleHUD() {
            this.hudVisible = !this.hudVisible;
            this.performanceHUD.style.display = this.hudVisible ? 'block' : 'none';
            
            if (this.hudVisible) {
                this.updateHUD();
            }
            
            console.log(`📊 Performance HUD: ${this.hudVisible ? 'shown' : 'hidden'}`);
        }

        updateHUD() {
            if (!this.hudVisible || !this.performanceHUD) return;
            
            const avgFPS = this.getAverageFPS();
            const avgFrameTime = this.getAverageFrameTime();
            
            const getPerformanceColor = (level) => {
                const colors = {
                    excellent: '#22c55e',
                    good: '#eab308', 
                    poor: '#f97316',
                    critical: '#ef4444'
                };
                return colors[level] || '#6b7280';
            };
            
            const perfColor = getPerformanceColor(this.performanceLevel);
            
            this.performanceHUD.innerHTML = `
                <div style="color: ${perfColor}; font-weight: bold; margin-bottom: 4px;">
                    📊 Performance Monitor
                </div>
                <div>FPS: <span style="color: ${perfColor}">${Math.round(avgFPS)}</span></div>
                <div>Frame: <span style="color: ${perfColor}">${avgFrameTime.toFixed(1)}ms</span></div>
                <div>Memory: <span style="color: #60a5fa">${this.memoryUsage.used}MB</span></div>
                <div style="font-size: 9px; margin-top: 4px; color: #9ca3af;">
                    Level: ${this.performanceLevel.toUpperCase()}
                </div>
                <div style="font-size: 9px; color: #9ca3af;">
                    Frames: ${this.frameTimes.length}/${this.frameTimeWindow}
                </div>
            `;
        }

        getPerformanceReport() {
            return {
                fps: {
                    current: this.fps,
                    average: this.getAverageFPS(),
                    min: this.frameTimes.length > 0 ? Math.min(...this.frameTimes.map(ft => 1000 / ft)) : 60,
                    max: this.frameTimes.length > 0 ? Math.max(...this.frameTimes.map(ft => 1000 / ft)) : 60
                },
                frameTime: {
                    current: this.frameTime,
                    average: this.getAverageFrameTime(),
                    min: this.frameTimes.length > 0 ? Math.min(...this.frameTimes) : 16.67,
                    max: this.frameTimes.length > 0 ? Math.max(...this.frameTimes) : 16.67
                },
                memory: this.memoryUsage,
                memoryHistory: this.memoryHistory.slice(-10),
                level: this.performanceLevel,
                renderStats: this.renderStats
            };
        }

        updateRenderStats(drawCalls, triangles, vertices, textures) {
            this.renderStats = { drawCalls, triangles, vertices, textures };
        }

        setThresholds(newThresholds) {
            this.thresholds = { ...this.thresholds, ...newThresholds };
        }

        getThresholds() {
            return { ...this.thresholds };
        }

        resetStats() {
            this.frameTimes = [];
            this.memoryHistory = [];
            this.renderStats = {
                drawCalls: 0,
                triangles: 0,
                vertices: 0,
                textures: 0
            };
        }

        dispose() {
            this.enabled = false;
            this.stopMonitoring();
            
            if (this.performanceHUD && this.performanceHUD.parentNode) {
                this.performanceHUD.parentNode.removeChild(this.performanceHUD);
            }
            
            if (this.perfToggleBtn && this.perfToggleBtn.parentNode) {
                this.perfToggleBtn.parentNode.removeChild(this.perfToggleBtn);
            }
            
            console.log('📊 PerformanceMonitor disposed');
        }
    }

    return new PerformanceMonitor(container, statusElement);
}

describe('Phase 5.3.1 PerformanceMonitor', () => {
    let performanceMonitor;
    let container;
    let statusElement;

    beforeEach(() => {
        vi.clearAllMocks();
        
        // Reset performance.now mock
        let time = 0;
        performance.now.mockImplementation(() => {
            time += 16.67; // Simulate 60fps
            return time;
        });
        
        performanceMonitor = createPerformanceMonitor();
        container = performanceMonitor.container;
        statusElement = performanceMonitor.statusElement;
    });

    afterEach(() => {
        if (performanceMonitor) {
            performanceMonitor.dispose();
        }
    });

    describe('Initialization', () => {
        it('should initialize with correct default values', () => {
            expect(performanceMonitor.enabled).toBe(true);
            expect(performanceMonitor.fps).toBe(60);
            expect(performanceMonitor.frameTime).toBe(16.67);
            expect(performanceMonitor.performanceLevel).toBe('good');
            expect(performanceMonitor.hudVisible).toBe(false);
            expect(performanceMonitor.frameTimes).toEqual([]);
            expect(performanceMonitor.memoryHistory).toEqual([]);
        });

        it('should create performance HUD', () => {
            expect(performanceMonitor.performanceHUD).toBeDefined();
            expect(container.appendChild).toHaveBeenCalled();
        });

        it('should create toggle button', () => {
            expect(performanceMonitor.perfToggleBtn).toBeDefined();
            expect(performanceMonitor.perfToggleBtn.textContent).toBe('📊');
        });

        it('should start monitoring automatically', () => {
            expect(performanceMonitor.isMonitoring).toBe(true);
            expect(performanceMonitor.monitoringIntervalId).toBeDefined();
        });

        it('should have correct default thresholds', () => {
            const thresholds = performanceMonitor.getThresholds();
            
            expect(thresholds.excellent.fps).toBe(55);
            expect(thresholds.good.fps).toBe(45);
            expect(thresholds.poor.fps).toBe(25);
            expect(thresholds.critical.fps).toBe(15);
        });
    });

    describe('FPS Tracking', () => {
        it('should update FPS correctly', () => {
            const initialFrameTime = performanceMonitor.lastFrameTime;
            
            performanceMonitor.updateFPS();
            
            expect(performanceMonitor.frameTime).toBeGreaterThan(0);
            expect(performanceMonitor.fps).toBeGreaterThan(0);
            expect(performanceMonitor.lastFrameTime).toBeGreaterThan(initialFrameTime);
        });

        it('should maintain sliding window of frame times', () => {
            for (let i = 0; i < 65; i++) {
                performanceMonitor.updateFPS();
            }
            
            expect(performanceMonitor.frameTimes.length).toBe(60); // frameTimeWindow
        });

        it('should calculate average FPS correctly', () => {
            // Add known frame times
            performanceMonitor.frameTimes = [16.67, 16.67, 16.67]; // 60fps
            
            const avgFPS = performanceMonitor.getAverageFPS();
            
            expect(avgFPS).toBeCloseTo(60, 1);
        });

        it('should calculate average frame time correctly', () => {
            performanceMonitor.frameTimes = [16.67, 20, 25];
            
            const avgFrameTime = performanceMonitor.getAverageFrameTime();
            
            expect(avgFrameTime).toBeCloseTo(20.56, 1);
        });

        it('should handle empty frame times gracefully', () => {
            performanceMonitor.frameTimes = [];
            
            expect(performanceMonitor.getAverageFPS()).toBe(60);
            expect(performanceMonitor.getAverageFrameTime()).toBe(16.67);
        });
    });

    describe('Memory Monitoring', () => {
        it('should update memory usage correctly', () => {
            performanceMonitor.updateMemoryUsage();
            
            expect(performanceMonitor.memoryUsage.used).toBeGreaterThan(0);
            expect(performanceMonitor.memoryUsage.total).toBeGreaterThan(0);
            expect(performanceMonitor.memoryUsage.limit).toBeGreaterThan(0);
        });

        it('should maintain memory history', () => {
            performanceMonitor.updateMemoryUsage();
            performanceMonitor.updateMemoryUsage();
            
            expect(performanceMonitor.memoryHistory.length).toBe(2);
            expect(performanceMonitor.memoryHistory[0]).toHaveProperty('timestamp');
            expect(performanceMonitor.memoryHistory[0]).toHaveProperty('usage');
            expect(performanceMonitor.memoryHistory[0]).toHaveProperty('total');
        });

        it('should limit memory history size', () => {
            // Fill history to exactly the limit
            for (let i = 0; i < 102; i++) {
                performanceMonitor.memoryHistory.push({
                    timestamp: Date.now(),
                    usage: 50,
                    total: 100
                });
            }
            
            // This should trigger the history limiting
            performanceMonitor.updateMemoryUsage();
            
            expect(performanceMonitor.memoryHistory.length).toBe(100); // memoryHistoryLimit
        });

        it('should detect memory pressure', () => {
            const showAlertSpy = vi.spyOn(performanceMonitor, 'showAlert');
            
            // Mock high memory usage (>90% for critical)
            performanceMonitor.memoryUsage = {
                used: 185,
                total: 190,
                limit: 200
            };
            
            performanceMonitor.checkMemoryPressure();
            
            expect(showAlertSpy).toHaveBeenCalledWith('Critical memory usage detected', 'warning');
        });

        it('should trigger memory pressure callback', () => {
            const memoryPressureCallback = vi.fn();
            performanceMonitor.onMemoryPressure = memoryPressureCallback;
            
            performanceMonitor.memoryUsage = {
                used: 190,
                total: 195,
                limit: 200
            };
            
            performanceMonitor.checkMemoryPressure();
            
            expect(memoryPressureCallback).toHaveBeenCalledWith(performanceMonitor.memoryUsage);
        });
    });

    describe('Performance Classification', () => {
        it('should classify excellent performance', () => {
            performanceMonitor.frameTimes = [16, 16, 16]; // ~62.5 fps
            
            performanceMonitor.classifyPerformance();
            
            expect(performanceMonitor.performanceLevel).toBe('excellent');
        });

        it('should classify good performance', () => {
            performanceMonitor.frameTimes = [20, 20, 20]; // 50 fps
            
            performanceMonitor.classifyPerformance();
            
            expect(performanceMonitor.performanceLevel).toBe('good');
        });

        it('should classify poor performance', () => {
            performanceMonitor.frameTimes = [35, 35, 35]; // ~28.6 fps
            
            performanceMonitor.classifyPerformance();
            
            expect(performanceMonitor.performanceLevel).toBe('poor');
        });

        it('should classify critical performance', () => {
            performanceMonitor.frameTimes = [80, 80, 80]; // 12.5 fps
            
            performanceMonitor.classifyPerformance();
            
            expect(performanceMonitor.performanceLevel).toBe('critical');
        });

        it('should trigger performance change callback', () => {
            const performanceChangeCallback = vi.fn();
            performanceMonitor.onPerformanceChange = performanceChangeCallback;
            
            performanceMonitor.performanceLevel = 'good';
            performanceMonitor.frameTimes = [80, 80, 80]; // Critical performance
            
            performanceMonitor.classifyPerformance();
            
            expect(performanceChangeCallback).toHaveBeenCalledWith(
                'critical',
                expect.objectContaining({
                    fps: expect.any(Number),
                    frameTime: expect.any(Number),
                    memory: expect.any(Object)
                })
            );
        });

        it('should get performance level rank correctly', () => {
            expect(performanceMonitor.getPerformanceLevelRank('critical')).toBe(0);
            expect(performanceMonitor.getPerformanceLevelRank('poor')).toBe(1);
            expect(performanceMonitor.getPerformanceLevelRank('good')).toBe(2);
            expect(performanceMonitor.getPerformanceLevelRank('excellent')).toBe(3);
        });
    });

    describe('HUD Management', () => {
        it('should toggle HUD visibility', () => {
            expect(performanceMonitor.hudVisible).toBe(false);
            
            performanceMonitor.toggleHUD();
            
            expect(performanceMonitor.hudVisible).toBe(true);
            expect(performanceMonitor.performanceHUD.style.display).toBe('block');
        });

        it('should update HUD content when visible', () => {
            performanceMonitor.hudVisible = true;
            performanceMonitor.frameTimes = [16.67, 16.67, 16.67];
            performanceMonitor.memoryUsage = { used: 50, total: 100, limit: 200 };
            performanceMonitor.performanceLevel = 'good';
            
            performanceMonitor.updateHUD();
            
            expect(performanceMonitor.performanceHUD.innerHTML).toContain('Performance Monitor');
            expect(performanceMonitor.performanceHUD.innerHTML).toContain('FPS:');
            expect(performanceMonitor.performanceHUD.innerHTML).toContain('Frame:');
            expect(performanceMonitor.performanceHUD.innerHTML).toContain('Memory:');
            expect(performanceMonitor.performanceHUD.innerHTML).toContain('GOOD');
        });

        it('should not update HUD when not visible', () => {
            performanceMonitor.hudVisible = false;
            const originalContent = performanceMonitor.performanceHUD.innerHTML;
            
            performanceMonitor.updateHUD();
            
            expect(performanceMonitor.performanceHUD.innerHTML).toBe(originalContent);
        });

        it('should show color-coded performance level', () => {
            performanceMonitor.hudVisible = true;
            performanceMonitor.performanceLevel = 'critical';
            
            performanceMonitor.updateHUD();
            
            expect(performanceMonitor.performanceHUD.innerHTML).toContain('#ef4444'); // Critical color
        });
    });

    describe('Alert System', () => {
        it('should show alert with cooldown', () => {
            const consoleSpy = vi.spyOn(console, 'log');
            
            performanceMonitor.showAlert('Test alert', 'info');
            
            expect(consoleSpy).toHaveBeenCalledWith('📊 Performance Alert [info]: Test alert');
        });

        it('should respect alert cooldown period', () => {
            const consoleSpy = vi.spyOn(console, 'log');
            
            performanceMonitor.showAlert('First alert', 'info');
            performanceMonitor.showAlert('Second alert', 'info'); // Should be blocked
            
            expect(consoleSpy).toHaveBeenCalledTimes(1);
        });

        it('should update HUD during alert', () => {
            performanceMonitor.performanceHUD = {
                textContent: 'Original',
                style: { background: 'original' }
            };
            
            performanceMonitor.showAlert('Test alert', 'warning');
            
            expect(performanceMonitor.performanceHUD.textContent).toBe('⚠️ Test alert');
            expect(performanceMonitor.performanceHUD.style.background).toBe('rgba(255, 193, 7, 0.9)');
        });
    });

    describe('Render Stats', () => {
        it('should update render stats correctly', () => {
            performanceMonitor.updateRenderStats(10, 5000, 15000, 3);
            
            expect(performanceMonitor.renderStats.drawCalls).toBe(10);
            expect(performanceMonitor.renderStats.triangles).toBe(5000);
            expect(performanceMonitor.renderStats.vertices).toBe(15000);
            expect(performanceMonitor.renderStats.textures).toBe(3);
        });

        it('should include render stats in performance report', () => {
            performanceMonitor.updateRenderStats(5, 2000, 6000, 2);
            
            const report = performanceMonitor.getPerformanceReport();
            
            expect(report.renderStats.drawCalls).toBe(5);
            expect(report.renderStats.triangles).toBe(2000);
        });
    });

    describe('Performance Report', () => {
        it('should generate comprehensive performance report', () => {
            performanceMonitor.frameTimes = [16, 20, 18];
            performanceMonitor.memoryUsage = { used: 50, total: 100, limit: 200 };
            performanceMonitor.performanceLevel = 'good';
            
            const report = performanceMonitor.getPerformanceReport();
            
            expect(report).toHaveProperty('fps');
            expect(report).toHaveProperty('frameTime');
            expect(report).toHaveProperty('memory');
            expect(report).toHaveProperty('memoryHistory');
            expect(report).toHaveProperty('level');
            expect(report).toHaveProperty('renderStats');
            
            expect(report.fps).toHaveProperty('current');
            expect(report.fps).toHaveProperty('average');
            expect(report.fps).toHaveProperty('min');
            expect(report.fps).toHaveProperty('max');
            
            expect(report.level).toBe('good');
        });

        it('should include recent memory history in report', () => {
            // Add memory history entries
            for (let i = 0; i < 15; i++) {
                performanceMonitor.memoryHistory.push({
                    timestamp: Date.now() + i,
                    usage: 50 + i,
                    total: 100
                });
            }
            
            const report = performanceMonitor.getPerformanceReport();
            
            expect(report.memoryHistory.length).toBe(10); // Last 10 entries
        });
    });

    describe('Threshold Management', () => {
        it('should set custom thresholds', () => {
            const newThresholds = {
                excellent: { fps: 50, frameTime: 20 },
                good: { fps: 40, frameTime: 25 }
            };
            
            performanceMonitor.setThresholds(newThresholds);
            
            const thresholds = performanceMonitor.getThresholds();
            expect(thresholds.excellent.fps).toBe(50);
            expect(thresholds.good.fps).toBe(40);
            expect(thresholds.poor.fps).toBe(25); // Should remain unchanged
        });

        it('should preserve existing thresholds when setting partial updates', () => {
            const originalThresholds = performanceMonitor.getThresholds();
            
            performanceMonitor.setThresholds({
                excellent: { fps: 50, frameTime: 20 }
            });
            
            const newThresholds = performanceMonitor.getThresholds();
            expect(newThresholds.excellent.fps).toBe(50);
            expect(newThresholds.good.fps).toBe(originalThresholds.good.fps);
        });
    });

    describe('Monitoring Control', () => {
        it('should stop monitoring correctly', () => {
            expect(performanceMonitor.isMonitoring).toBe(true);
            
            performanceMonitor.stopMonitoring();
            
            expect(performanceMonitor.isMonitoring).toBe(false);
            expect(performanceMonitor.monitoringIntervalId).toBeNull();
        });

        it('should restart monitoring after stopping', () => {
            performanceMonitor.stopMonitoring();
            expect(performanceMonitor.isMonitoring).toBe(false);
            
            performanceMonitor.startMonitoring();
            
            expect(performanceMonitor.isMonitoring).toBe(true);
            expect(performanceMonitor.monitoringIntervalId).toBeDefined();
        });

        it('should not start monitoring if already monitoring', () => {
            const originalIntervalId = performanceMonitor.monitoringIntervalId;
            
            performanceMonitor.startMonitoring(); // Should do nothing
            
            expect(performanceMonitor.monitoringIntervalId).toBe(originalIntervalId);
        });
    });

    describe('Stats Reset', () => {
        it('should reset all stats correctly', () => {
            // Add some data
            performanceMonitor.frameTimes = [16, 20, 18];
            performanceMonitor.memoryHistory = [{ timestamp: Date.now(), usage: 50, total: 100 }];
            performanceMonitor.updateRenderStats(10, 5000, 15000, 3);
            
            performanceMonitor.resetStats();
            
            expect(performanceMonitor.frameTimes).toEqual([]);
            expect(performanceMonitor.memoryHistory).toEqual([]);
            expect(performanceMonitor.renderStats.drawCalls).toBe(0);
            expect(performanceMonitor.renderStats.triangles).toBe(0);
            expect(performanceMonitor.renderStats.vertices).toBe(0);
            expect(performanceMonitor.renderStats.textures).toBe(0);
        });
    });

    describe('Cleanup and Disposal', () => {
        it('should dispose properly', () => {
            performanceMonitor.dispose();
            
            expect(performanceMonitor.enabled).toBe(false);
            expect(performanceMonitor.isMonitoring).toBe(false);
            expect(performanceMonitor.performanceHUD.parentNode.removeChild).toHaveBeenCalled();
            expect(performanceMonitor.perfToggleBtn.parentNode.removeChild).toHaveBeenCalled();
        });

        it('should handle disposal when elements have no parent', () => {
            performanceMonitor.performanceHUD.parentNode = null;
            performanceMonitor.perfToggleBtn.parentNode = null;
            
            expect(() => {
                performanceMonitor.dispose();
            }).not.toThrow();
        });

        it('should stop monitoring on disposal', () => {
            const stopMonitoringSpy = vi.spyOn(performanceMonitor, 'stopMonitoring');
            
            performanceMonitor.dispose();
            
            expect(stopMonitoringSpy).toHaveBeenCalled();
        });
    });
});