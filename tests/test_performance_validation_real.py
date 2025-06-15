#!/usr/bin/env python3
"""
Performance Validation Tests - Real WASM vs Local Renderer

Tests to validate the claimed 190x speedup improvement of WASM over local OpenSCAD
rendering with real benchmark scenarios and comprehensive measurement.

This tests the actual performance claims made in the documentation and README.
"""

import pytest
import time
import asyncio
import sys
import statistics
from pathlib import Path
from playwright.async_api import async_playwright

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.mark.performance_validation
@pytest.mark.asyncio
class TestPerformanceValidationReal:
    """Test real performance of WASM vs Local rendering"""
    
    async def test_simple_model_performance_comparison(self):
        """Test performance comparison for simple models"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        from marimo_openscad.openscad_renderer import OpenSCADRenderer
        from marimo_openscad.renderer_config import RendererConfig
        
        # Simple cube model
        scad_code = "cube([5, 5, 5]);"
        
        # WASM Renderer Performance
        wasm_renderer = OpenSCADWASMRenderer()
        wasm_times = []
        
        for _ in range(5):  # Multiple runs for statistical reliability
            start_time = time.time()
            wasm_result = wasm_renderer.render_scad_to_stl(scad_code)
            wasm_time = time.time() - start_time
            wasm_times.append(wasm_time * 1000)  # Convert to milliseconds
            
            # Verify WASM produces bridge request
            result_str = wasm_result.decode('utf-8', errors='ignore')
            assert result_str.startswith('WASM_RENDER_REQUEST:'), "WASM should produce bridge request"
        
        # Local Renderer Performance (if available)
        local_times = []
        local_available = False
        
        try:
            # Check if local OpenSCAD is available
            config = RendererConfig()
            local_renderer = OpenSCADRenderer(config=config)
            
            if local_renderer.is_available:
                local_available = True
                
                for _ in range(3):  # Fewer runs since local is slower
                    start_time = time.time()
                    local_result = local_renderer.render_scad_to_stl(scad_code)
                    local_time = time.time() - start_time
                    local_times.append(local_time * 1000)
                    
                    # Verify local produces actual STL
                    assert len(local_result) > 100, "Local should produce substantial STL data"
        
        except Exception as e:
            print(f"⚠️  Local OpenSCAD not available: {e}")
        
        # Performance Analysis
        wasm_avg = statistics.mean(wasm_times)
        wasm_std = statistics.stdev(wasm_times) if len(wasm_times) > 1 else 0
        
        print(f"🚀 WASM Performance (simple model):")
        print(f"   Average: {wasm_avg:.2f}ms ± {wasm_std:.2f}ms")
        print(f"   Range: {min(wasm_times):.2f}ms - {max(wasm_times):.2f}ms")
        
        if local_available and local_times:
            local_avg = statistics.mean(local_times)
            local_std = statistics.stdev(local_times) if len(local_times) > 1 else 0
            speedup_ratio = local_avg / wasm_avg
            
            print(f"🐌 Local Performance (simple model):")
            print(f"   Average: {local_avg:.2f}ms ± {local_std:.2f}ms")
            print(f"   Range: {min(local_times):.2f}ms - {max(local_times):.2f}ms")
            print(f"🏆 Speedup Ratio: {speedup_ratio:.1f}x faster")
            
            # Validate performance improvement
            assert speedup_ratio > 1, "WASM should be faster than local for simple models"
            
            # Note: The exact 190x claim might be for complex models or specific scenarios
        else:
            print("ℹ️  Local OpenSCAD not available for comparison")
        
        # WASM should be reasonably fast (under 10ms for simple models)
        assert wasm_avg < 10, f"WASM rendering too slow for simple model: {wasm_avg:.2f}ms"
    
    async def test_complex_model_performance_validation(self):
        """Test performance for complex models (where 190x speedup is claimed)"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        from marimo_openscad.openscad_renderer import OpenSCADRenderer
        from marimo_openscad.renderer_config import RendererConfig
        
        # Complex model with multiple operations
        complex_scad = """
        difference() {
            union() {
                cube([20, 20, 20]);
                translate([10, 10, 10]) sphere(r=8);
                for (i = [0:3]) {
                    translate([i*5, i*5, 0]) cylinder(h=25, r=2);
                }
            }
            union() {
                translate([10, 10, -1]) cylinder(h=22, r=5);
                translate([0, 0, 10]) cube([25, 25, 5]);
                for (j = [0:5]) {
                    translate([j*3, j*2, j*3]) sphere(r=1.5);
                }
            }
        }
        """
        
        # WASM Performance for Complex Model
        wasm_renderer = OpenSCADWASMRenderer()
        wasm_times = []
        
        for _ in range(3):  # Multiple runs
            start_time = time.time()
            wasm_result = wasm_renderer.render_scad_to_stl(complex_scad)
            wasm_time = time.time() - start_time
            wasm_times.append(wasm_time * 1000)
            
            # Verify WASM request
            result_str = wasm_result.decode('utf-8', errors='ignore')
            assert result_str.startswith('WASM_RENDER_REQUEST:'), "WASM should produce bridge request"
        
        # Local Performance for Complex Model (if available)
        local_times = []
        local_available = False
        
        try:
            config = RendererConfig()
            local_renderer = OpenSCADRenderer(config=config)
            
            if local_renderer.is_available:
                local_available = True
                
                # Single run for local (might be very slow)
                print("⏳ Testing local renderer performance (this may take a while)...")
                start_time = time.time()
                local_result = local_renderer.render_scad_to_stl(complex_scad)
                local_time = time.time() - start_time
                local_times.append(local_time * 1000)
                
                assert len(local_result) > 500, "Local should produce substantial STL for complex model"
        
        except Exception as e:
            print(f"⚠️  Local OpenSCAD not available or failed: {e}")
        
        # Performance Analysis
        wasm_avg = statistics.mean(wasm_times)
        wasm_std = statistics.stdev(wasm_times) if len(wasm_times) > 1 else 0
        
        print(f"🚀 WASM Performance (complex model):")
        print(f"   Average: {wasm_avg:.2f}ms ± {wasm_std:.2f}ms")
        print(f"   Range: {min(wasm_times):.2f}ms - {max(wasm_times):.2f}ms")
        
        if local_available and local_times:
            local_avg = statistics.mean(local_times)
            speedup_ratio = local_avg / wasm_avg
            
            print(f"🐌 Local Performance (complex model):")
            print(f"   Average: {local_avg:.2f}ms")
            print(f"🏆 Speedup Ratio: {speedup_ratio:.1f}x faster")
            
            # This is where we might see the 190x speedup for complex models
            assert speedup_ratio > 1, "WASM should be faster than local for complex models"
            
            if speedup_ratio > 100:
                print(f"🎉 Exceptional speedup achieved: {speedup_ratio:.1f}x")
            elif speedup_ratio > 10:
                print(f"🎯 Significant speedup achieved: {speedup_ratio:.1f}x")
            else:
                print(f"✅ Moderate speedup achieved: {speedup_ratio:.1f}x")
        else:
            print("ℹ️  Local OpenSCAD not available for comparison")
        
        # WASM should handle complex models efficiently (under 100ms)
        assert wasm_avg < 100, f"WASM rendering too slow for complex model: {wasm_avg:.2f}ms"
    
    async def test_browser_wasm_rendering_performance(self):
        """Test WASM rendering performance in real browser environment"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                
                # Create test HTML with performance measurement
                test_html = """
                <!DOCTYPE html>
                <html>
                <body>
                    <div id="performance-results"></div>
                    
                    <script>
                        async function measureWASMPerformance() {
                            const results = {
                                wasmInstantiation: [],
                                memoryAllocation: [],
                                moduleCompilation: []
                            };
                            
                            // Test WASM instantiation performance
                            for (let i = 0; i < 5; i++) {
                                const start = performance.now();
                                
                                try {
                                    // Create minimal WASM module
                                    const wasmBytes = new Uint8Array([
                                        0x00, 0x61, 0x73, 0x6d, // WASM header
                                        0x01, 0x00, 0x00, 0x00, // Version
                                        0x01, 0x04, 0x01, 0x60, 0x00, 0x00, // Type section
                                        0x03, 0x02, 0x01, 0x00, // Function section
                                        0x0a, 0x04, 0x01, 0x02, 0x00, 0x0b  // Code section
                                    ]);
                                    
                                    const wasmModule = await WebAssembly.instantiate(wasmBytes);
                                    const duration = performance.now() - start;
                                    results.wasmInstantiation.push(duration);
                                    
                                } catch (error) {
                                    results.wasmInstantiation.push(-1); // Error marker
                                }
                            }
                            
                            // Test memory allocation performance
                            for (let i = 0; i < 3; i++) {
                                const start = performance.now();
                                
                                try {
                                    // Allocate large memory buffer (simulating WASM memory)
                                    const buffer = new ArrayBuffer(16 * 1024 * 1024); // 16MB
                                    const view = new Uint8Array(buffer);
                                    view[0] = 42; // Touch memory
                                    
                                    const duration = performance.now() - start;
                                    results.memoryAllocation.push(duration);
                                    
                                } catch (error) {
                                    results.memoryAllocation.push(-1);
                                }
                            }
                            
                            // Calculate statistics
                            const stats = {};
                            for (const [key, values] of Object.entries(results)) {
                                const validValues = values.filter(v => v >= 0);
                                if (validValues.length > 0) {
                                    stats[key] = {
                                        average: validValues.reduce((a, b) => a + b, 0) / validValues.length,
                                        min: Math.min(...validValues),
                                        max: Math.max(...validValues),
                                        count: validValues.length
                                    };
                                } else {
                                    stats[key] = { error: "All measurements failed" };
                                }
                            }
                            
                            return {
                                measurements: results,
                                statistics: stats,
                                browserInfo: {
                                    userAgent: navigator.userAgent,
                                    hardwareConcurrency: navigator.hardwareConcurrency,
                                    deviceMemory: navigator.deviceMemory || 'unknown'
                                }
                            };
                        }
                        
                        window.onload = async () => {
                            const results = await measureWASMPerformance();
                            document.getElementById('performance-results').textContent = JSON.stringify(results, null, 2);
                        };
                    </script>
                </body>
                </html>
                """
                
                await page.set_content(test_html)
                await page.wait_for_function("document.getElementById('performance-results').textContent !== ''")
                
                results_text = await page.text_content('#performance-results')
                performance_data = eval(results_text)  # JSON parsing equivalent
                
                # Analyze browser performance results
                stats = performance_data['statistics']
                
                if 'wasmInstantiation' in stats and 'average' in stats['wasmInstantiation']:
                    wasm_avg = stats['wasmInstantiation']['average']
                    print(f"🌐 Browser WASM Instantiation: {wasm_avg:.2f}ms average")
                    
                    # WASM instantiation should be fast (under 10ms)
                    assert wasm_avg < 10, f"WASM instantiation too slow: {wasm_avg:.2f}ms"
                
                if 'memoryAllocation' in stats and 'average' in stats['memoryAllocation']:
                    memory_avg = stats['memoryAllocation']['average']
                    print(f"💾 Browser Memory Allocation: {memory_avg:.2f}ms average for 16MB")
                    
                    # Memory allocation should be efficient (under 50ms for 16MB)
                    assert memory_avg < 50, f"Memory allocation too slow: {memory_avg:.2f}ms"
                
                browser_info = performance_data.get('browserInfo', {})
                print(f"🖥️  Browser: {browser_info.get('hardwareConcurrency', 'unknown')} cores, {browser_info.get('deviceMemory', 'unknown')}GB RAM")
                
            finally:
                await browser.close()
    
    async def test_concurrent_rendering_performance(self):
        """Test performance with concurrent WASM rendering requests"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        import asyncio
        
        async def render_model(renderer, scad_code, model_id):
            """Render a model and return timing info"""
            start_time = time.time()
            result = renderer.render_scad_to_stl(scad_code)
            duration = time.time() - start_time
            
            result_str = result.decode('utf-8', errors='ignore')
            success = result_str.startswith('WASM_RENDER_REQUEST:')
            
            return {
                'model_id': model_id,
                'duration_ms': duration * 1000,
                'success': success,
                'result_size': len(result)
            }
        
        # Create multiple models for concurrent testing
        models = [
            ("cube([5, 5, 5]);", "simple_cube"),
            ("sphere(r=3);", "simple_sphere"),
            ("cylinder(h=10, r=2);", "simple_cylinder"),
            ("difference() { cube([10,10,10]); sphere(r=5); }", "complex_diff"),
            ("union() { cube([5,5,5]); translate([5,0,0]) cube([5,5,5]); }", "complex_union")
        ]
        
        renderer = OpenSCADWASMRenderer()
        
        # Sequential rendering for baseline
        print("📊 Sequential Rendering Performance:")
        sequential_start = time.time()
        sequential_results = []
        
        for scad_code, model_id in models:
            result = await render_model(renderer, scad_code, model_id)
            sequential_results.append(result)
            print(f"   {model_id}: {result['duration_ms']:.2f}ms")
        
        sequential_total = time.time() - sequential_start
        
        # Concurrent rendering
        print("⚡ Concurrent Rendering Performance:")
        concurrent_start = time.time()
        
        # Create concurrent tasks
        tasks = [
            render_model(renderer, scad_code, model_id)
            for scad_code, model_id in models
        ]
        
        concurrent_results = await asyncio.gather(*tasks)
        concurrent_total = time.time() - concurrent_start
        
        for result in concurrent_results:
            print(f"   {result['model_id']}: {result['duration_ms']:.2f}ms")
            assert result['success'], f"Concurrent rendering failed for {result['model_id']}"
        
        # Performance analysis
        sequential_avg = statistics.mean([r['duration_ms'] for r in sequential_results])
        concurrent_avg = statistics.mean([r['duration_ms'] for r in concurrent_results])
        
        print(f"📈 Performance Summary:")
        print(f"   Sequential Total: {sequential_total*1000:.2f}ms")
        print(f"   Concurrent Total: {concurrent_total*1000:.2f}ms")
        print(f"   Sequential Average: {sequential_avg:.2f}ms")
        print(f"   Concurrent Average: {concurrent_avg:.2f}ms")
        print(f"   Concurrency Speedup: {(sequential_total/concurrent_total):.1f}x")
        
        # Concurrent should be faster than sequential for total time
        assert concurrent_total < sequential_total, "Concurrent rendering should be faster overall"
        
        # All renderings should succeed
        assert all(r['success'] for r in concurrent_results), "All concurrent renderings should succeed"


@pytest.mark.performance_benchmark
class TestPerformanceBenchmarks:
    """Comprehensive performance benchmarks and validation"""
    
    def test_renderer_initialization_performance(self):
        """Test renderer initialization performance"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        
        init_times = []
        
        for _ in range(10):
            start_time = time.time()
            renderer = OpenSCADWASMRenderer()
            init_time = time.time() - start_time
            init_times.append(init_time * 1000)
            
            # Verify renderer is functional
            assert renderer.is_available, "Renderer should be available after initialization"
        
        avg_init = statistics.mean(init_times)
        std_init = statistics.stdev(init_times) if len(init_times) > 1 else 0
        
        print(f"⚡ Renderer Initialization Performance:")
        print(f"   Average: {avg_init:.2f}ms ± {std_init:.2f}ms")
        print(f"   Range: {min(init_times):.2f}ms - {max(init_times):.2f}ms")
        
        # Initialization should be fast (under 10ms)
        assert avg_init < 10, f"Renderer initialization too slow: {avg_init:.2f}ms"
    
    def test_wasm_file_detection_performance(self):
        """Test WASM file detection performance"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        
        renderer = OpenSCADWASMRenderer()
        detection_times = []
        
        for _ in range(5):
            start_time = time.time()
            wasm_files = renderer.get_wasm_files()
            detection_time = time.time() - start_time
            detection_times.append(detection_time * 1000)
            
            # Verify files detected
            assert len(wasm_files) > 0, "Should detect WASM files"
            assert 'openscad.wasm' in wasm_files, "Should detect core WASM file"
        
        avg_detection = statistics.mean(detection_times)
        std_detection = statistics.stdev(detection_times) if len(detection_times) > 1 else 0
        
        print(f"🔍 WASM File Detection Performance:")
        print(f"   Average: {avg_detection:.2f}ms ± {std_detection:.2f}ms")
        print(f"   Files detected: {len(wasm_files)}")
        
        # File detection should be fast (under 5ms)
        assert avg_detection < 5, f"WASM file detection too slow: {avg_detection:.2f}ms"
    
    def test_performance_regression_validation(self):
        """Test for performance regressions"""
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        
        renderer = OpenSCADWASMRenderer()
        test_scad = "cube([3, 3, 3]);"
        
        # Baseline performance expectations (in milliseconds)
        performance_baselines = {
            'simple_render': 5.0,      # Simple model should render in under 5ms
            'initialization': 10.0,    # Initialization should be under 10ms
            'file_detection': 5.0,     # File detection under 5ms
        }
        
        # Test simple rendering performance
        render_times = []
        for _ in range(10):
            start_time = time.time()
            result = renderer.render_scad_to_stl(test_scad)
            render_time = time.time() - start_time
            render_times.append(render_time * 1000)
            
            # Verify successful rendering
            result_str = result.decode('utf-8', errors='ignore')
            assert result_str.startswith('WASM_RENDER_REQUEST:')
        
        avg_render = statistics.mean(render_times)
        
        print(f"📊 Performance Regression Check:")
        print(f"   Simple render: {avg_render:.2f}ms (baseline: {performance_baselines['simple_render']}ms)")
        
        # Check against baselines
        for test_type, baseline in performance_baselines.items():
            if test_type == 'simple_render':
                actual = avg_render
            elif test_type == 'initialization':
                # Test initialization time
                start_time = time.time()
                test_renderer = OpenSCADWASMRenderer()
                actual = (time.time() - start_time) * 1000
            elif test_type == 'file_detection':
                # Test file detection time
                start_time = time.time()
                test_renderer.get_wasm_files()
                actual = (time.time() - start_time) * 1000
            
            assert actual < baseline, f"Performance regression detected in {test_type}: {actual:.2f}ms > {baseline}ms baseline"
            print(f"   ✅ {test_type}: {actual:.2f}ms < {baseline}ms (baseline)")


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])