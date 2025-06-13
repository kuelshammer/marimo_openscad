/**
 * Performance Benchmark for OpenSCAD WASM Renderer
 * 
 * Provides utilities for benchmarking WASM rendering performance
 */

export class PerformanceBenchmark {
    constructor() {
        this.results = [];
        this.isRunning = false;
    }

    /**
     * Run a benchmark test
     * @param {string} testName - Name of the test
     * @param {Function} testFunction - Function to benchmark
     * @param {Object} options - Benchmark options
     * @returns {Promise<Object>} Benchmark results
     */
    async runBenchmark(testName, testFunction, options = {}) {
        const {
            iterations = 1,
            warmupRuns = 0,
            timeout = 30000
        } = options;

        console.log(`Starting benchmark: ${testName}`);
        this.isRunning = true;

        try {
            // Warmup runs
            for (let i = 0; i < warmupRuns; i++) {
                console.log(`Warmup run ${i + 1}/${warmupRuns}`);
                await testFunction();
            }

            // Actual benchmark runs
            const times = [];
            const memoryUsage = [];

            for (let i = 0; i < iterations; i++) {
                console.log(`Benchmark run ${i + 1}/${iterations}`);
                
                // Collect memory before
                const memBefore = this._getMemoryUsage();
                
                // Run test with timing
                const startTime = performance.now();
                await Promise.race([
                    testFunction(),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Benchmark timeout')), timeout)
                    )
                ]);
                const endTime = performance.now();
                
                // Collect memory after
                const memAfter = this._getMemoryUsage();
                
                times.push(endTime - startTime);
                memoryUsage.push({
                    before: memBefore,
                    after: memAfter,
                    delta: memAfter - memBefore
                });
            }

            // Calculate statistics
            const result = this._calculateStats(testName, times, memoryUsage);
            this.results.push(result);
            
            console.log(`Benchmark completed: ${testName}`, result.summary);
            return result;

        } catch (error) {
            console.error(`Benchmark failed: ${testName}`, error);
            throw error;
        } finally {
            this.isRunning = false;
        }
    }

    /**
     * Get memory usage (approximation)
     * @private
     */
    _getMemoryUsage() {
        if (typeof performance !== 'undefined' && performance.memory) {
            return performance.memory.usedJSHeapSize;
        }
        return 0;
    }

    /**
     * Calculate benchmark statistics
     * @private
     */
    _calculateStats(testName, times, memoryUsage) {
        const sortedTimes = [...times].sort((a, b) => a - b);
        const totalTime = times.reduce((sum, time) => sum + time, 0);
        
        const result = {
            testName,
            iterations: times.length,
            timing: {
                min: Math.min(...times),
                max: Math.max(...times),
                mean: totalTime / times.length,
                median: sortedTimes[Math.floor(sortedTimes.length / 2)],
                p95: sortedTimes[Math.floor(sortedTimes.length * 0.95)],
                p99: sortedTimes[Math.floor(sortedTimes.length * 0.99)],
                total: totalTime
            },
            memory: {
                averageDelta: memoryUsage.reduce((sum, mem) => sum + mem.delta, 0) / memoryUsage.length,
                maxDelta: Math.max(...memoryUsage.map(mem => mem.delta)),
                minDelta: Math.min(...memoryUsage.map(mem => mem.delta))
            },
            timestamp: new Date().toISOString()
        };

        result.summary = {
            averageTime: `${result.timing.mean.toFixed(2)}ms`,
            medianTime: `${result.timing.median.toFixed(2)}ms`,
            throughput: `${(1000 / result.timing.mean).toFixed(2)} ops/sec`
        };

        return result;
    }

    /**
     * Compare two benchmark results
     * @param {Object} baseline - Baseline benchmark result
     * @param {Object} comparison - Comparison benchmark result
     * @returns {Object} Comparison analysis
     */
    compare(baseline, comparison) {
        const speedRatio = baseline.timing.mean / comparison.timing.mean;
        const memoryRatio = comparison.memory.averageDelta / baseline.memory.averageDelta;

        return {
            baseline: baseline.testName,
            comparison: comparison.testName,
            performance: {
                speedImprovement: speedRatio > 1 ? `${((speedRatio - 1) * 100).toFixed(1)}% faster` : 
                    `${((1 - speedRatio) * 100).toFixed(1)}% slower`,
                speedRatio: speedRatio,
                isImprovement: speedRatio > 1
            },
            memory: {
                memoryChange: memoryRatio > 1 ? `${((memoryRatio - 1) * 100).toFixed(1)}% more memory` :
                    `${((1 - memoryRatio) * 100).toFixed(1)}% less memory`,
                memoryRatio: memoryRatio,
                isImprovement: memoryRatio < 1
            }
        };
    }

    /**
     * Get all benchmark results
     * @returns {Array} All benchmark results
     */
    getAllResults() {
        return [...this.results];
    }

    /**
     * Generate benchmark report
     * @returns {Object} Comprehensive benchmark report
     */
    generateReport() {
        return {
            summary: {
                totalBenchmarks: this.results.length,
                averageTime: this.results.reduce((sum, result) => sum + result.timing.mean, 0) / this.results.length,
                fastestTest: this.results.reduce((fastest, current) => 
                    current.timing.mean < fastest.timing.mean ? current : fastest),
                slowestTest: this.results.reduce((slowest, current) => 
                    current.timing.mean > slowest.timing.mean ? current : slowest)
            },
            results: this.results,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Clear all results
     */
    clear() {
        this.results = [];
    }
}

/**
 * WASM-specific benchmark tests
 */
export class WASMBenchmarkSuite {
    constructor(renderer) {
        this.renderer = renderer;
        this.benchmark = new PerformanceBenchmark();
    }

    /**
     * Run initialization benchmark
     */
    async benchmarkInitialization() {
        return this.benchmark.runBenchmark(
            'WASM Initialization',
            () => this.renderer.initialize(),
            { iterations: 5, warmupRuns: 1 }
        );
    }

    /**
     * Run simple rendering benchmark
     */
    async benchmarkSimpleRendering() {
        const scadCode = 'cube([10, 10, 10]);';
        
        return this.benchmark.runBenchmark(
            'Simple Cube Rendering',
            () => this.renderer.renderToSTL(scadCode),
            { iterations: 10, warmupRuns: 2 }
        );
    }

    /**
     * Run complex rendering benchmark
     */
    async benchmarkComplexRendering() {
        const scadCode = `
            difference() {
                union() {
                    cube([20, 20, 20]);
                    translate([0, 0, 20]) sphere(r=10);
                }
                for(i = [0:5]) {
                    translate([i*3, 0, 0]) cylinder(r=2, h=30, center=true);
                }
            }
        `;
        
        return this.benchmark.runBenchmark(
            'Complex Model Rendering',
            () => this.renderer.renderToSTL(scadCode),
            { iterations: 5, warmupRuns: 1 }
        );
    }

    /**
     * Run memory stress test
     */
    async benchmarkMemoryStress() {
        const scadCode = `
            for(i = [0:50]) {
                for(j = [0:50]) {
                    translate([i*0.5, j*0.5, 0]) cube([0.4, 0.4, 1]);
                }
            }
        `;
        
        return this.benchmark.runBenchmark(
            'Memory Stress Test',
            () => this.renderer.renderToSTL(scadCode),
            { iterations: 3, warmupRuns: 1, timeout: 60000 }
        );
    }

    /**
     * Run throughput benchmark
     */
    async benchmarkThroughput() {
        const scadCodes = [
            'cube([5, 5, 5]);',
            'sphere(r=3);',
            'cylinder(r=2, h=8);',
            'translate([0, 0, 5]) cube([3, 3, 3]);'
        ];
        
        let index = 0;
        return this.benchmark.runBenchmark(
            'Throughput Test',
            () => {
                const code = scadCodes[index % scadCodes.length];
                index++;
                return this.renderer.renderToSTL(code);
            },
            { iterations: 20, warmupRuns: 3 }
        );
    }

    /**
     * Run complete benchmark suite
     */
    async runFullSuite() {
        console.log('Starting WASM benchmark suite...');
        
        const results = {};
        
        try {
            results.initialization = await this.benchmarkInitialization();
            results.simpleRendering = await this.benchmarkSimpleRendering();
            results.complexRendering = await this.benchmarkComplexRendering();
            results.throughput = await this.benchmarkThroughput();
            
            // Optional stress test (may be slow)
            try {
                results.memoryStress = await this.benchmarkMemoryStress();
            } catch (error) {
                console.warn('Memory stress test failed or timed out:', error.message);
                results.memoryStress = { error: error.message };
            }
            
            console.log('WASM benchmark suite completed');
            return results;
            
        } catch (error) {
            console.error('Benchmark suite failed:', error);
            throw error;
        }
    }

    /**
     * Get benchmark report
     */
    getReport() {
        return this.benchmark.generateReport();
    }
}

/**
 * Utility functions for benchmarking
 */
export const BenchmarkUtils = {
    /**
     * Format time in human-readable format
     */
    formatTime(milliseconds) {
        if (milliseconds < 1) {
            return `${(milliseconds * 1000).toFixed(2)}μs`;
        } else if (milliseconds < 1000) {
            return `${milliseconds.toFixed(2)}ms`;
        } else {
            return `${(milliseconds / 1000).toFixed(2)}s`;
        }
    },

    /**
     * Format memory in human-readable format
     */
    formatMemory(bytes) {
        const units = ['B', 'KB', 'MB', 'GB'];
        let value = bytes;
        let unitIndex = 0;
        
        while (value >= 1024 && unitIndex < units.length - 1) {
            value /= 1024;
            unitIndex++;
        }
        
        return `${value.toFixed(2)} ${units[unitIndex]}`;
    },

    /**
     * Create performance baseline
     */
    createBaseline(renderer, options = {}) {
        const suite = new WASMBenchmarkSuite(renderer);
        return suite.runFullSuite();
    }
};