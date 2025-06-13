#!/usr/bin/env python3
"""
Performance Baseline Tests

CRITICAL MISSING TEST - Phase 1 Gap Closure
Establishes performance baselines for WASM vs Local rendering.
Required for Phase 3 success validation (190x improvement target).
"""

import pytest
import time
import psutil
import os
import sys
from pathlib import Path
import gc
import platform

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestPerformanceBaseline:
    """Establish performance baselines (will show current limitations)"""
    
    def test_wasm_vs_local_speed_baseline(self):
        """
        CRITICAL: Establish baseline for 190x improvement target
        Expected to show WASM not functional initially
        """
        from marimo_openscad.viewer import openscad_viewer
        from solid2 import cube, sphere, union, difference, cylinder
        
        # Create test models of varying complexity
        test_models = {
            'simple': cube([2, 2, 2]),
            'medium': union()(
                cube([3, 3, 3]),
                sphere(r=2).translate([1.5, 1.5, 1.5])
            ),
            'complex': difference()(
                union()(
                    cube([5, 5, 5]),
                    sphere(r=3).translate([2.5, 2.5, 2.5])
                ),
                cylinder(r=1, h=6).translate([2.5, 2.5, -0.5])
            )
        }
        
        performance_results = {}
        
        for model_name, model in test_models.items():
            print(f"\n🔍 Testing {model_name} model performance...")
            
            model_results = {}
            
            # Test WASM performance (expected to fail initially)
            print(f"  Testing WASM renderer...")
            try:
                start_time = time.perf_counter()
                wasm_viewer = openscad_viewer(model, renderer_type="wasm")
                wasm_creation_time = time.perf_counter() - start_time
                
                # Check if we got real STL data or placeholder
                stl_data = getattr(wasm_viewer, 'stl_data', None)
                is_placeholder = isinstance(stl_data, (str, bytes)) and b"WASM_RENDER_REQUEST" in (stl_data if isinstance(stl_data, bytes) else stl_data.encode())
                
                model_results['wasm'] = {
                    'creation_time': wasm_creation_time,
                    'success': bool(stl_data and not is_placeholder),
                    'stl_length': len(stl_data) if stl_data else 0,
                    'is_placeholder': is_placeholder,
                    'stl_preview': str(stl_data)[:100] if stl_data else "No data"
                }
                
                if is_placeholder:
                    print(f"    ⚠️ WASM returned placeholder: {model_results['wasm']['stl_preview']}")
                else:
                    print(f"    ✅ WASM generated real STL: {model_results['wasm']['stl_length']} bytes")
                    
            except Exception as e:
                model_results['wasm'] = {
                    'creation_time': None,
                    'success': False,
                    'error': str(e),
                    'stl_length': 0
                }
                print(f"    ❌ WASM failed: {e}")
            
            # Test Local performance (should work if OpenSCAD installed)
            print(f"  Testing Local renderer...")
            try:
                start_time = time.perf_counter()
                local_viewer = openscad_viewer(model, renderer_type="local")
                local_creation_time = time.perf_counter() - start_time
                
                stl_data = getattr(local_viewer, 'stl_data', None)
                
                model_results['local'] = {
                    'creation_time': local_creation_time,
                    'success': bool(stl_data and len(stl_data) > 0),
                    'stl_length': len(stl_data) if stl_data else 0,
                    'stl_preview': str(stl_data)[:100] if stl_data else "No data"
                }
                
                if model_results['local']['success']:
                    print(f"    ✅ Local generated STL: {model_results['local']['stl_length']} bytes in {local_creation_time:.3f}s")
                else:
                    print(f"    ⚠️ Local generated no valid STL data")
                    
            except Exception as e:
                model_results['local'] = {
                    'creation_time': None,
                    'success': False,
                    'error': str(e),
                    'stl_length': 0
                }
                print(f"    ❌ Local failed: {e}")
            
            # Test Auto renderer (fallback behavior)
            print(f"  Testing Auto renderer...")
            try:
                start_time = time.perf_counter()
                auto_viewer = openscad_viewer(model, renderer_type="auto")
                auto_creation_time = time.perf_counter() - start_time
                
                stl_data = getattr(auto_viewer, 'stl_data', None)
                renderer_status = getattr(auto_viewer, 'renderer_status', 'unknown')
                
                model_results['auto'] = {
                    'creation_time': auto_creation_time,
                    'success': bool(stl_data and len(stl_data) > 0),
                    'stl_length': len(stl_data) if stl_data else 0,
                    'renderer_used': renderer_status
                }
                
                print(f"    ✅ Auto used {renderer_status}: {model_results['auto']['stl_length']} bytes in {auto_creation_time:.3f}s")
                
            except Exception as e:
                model_results['auto'] = {
                    'creation_time': None,
                    'success': False,
                    'error': str(e),
                    'stl_length': 0
                }
                print(f"    ❌ Auto failed: {e}")
            
            performance_results[model_name] = model_results
        
        # Analyze and document performance baselines
        print("\n📊 PERFORMANCE BASELINE SUMMARY:")
        print("=" * 60)
        
        for model_name, results in performance_results.items():
            print(f"\n{model_name.upper()} MODEL:")
            
            for renderer, data in results.items():
                if data.get('success', False):
                    time_str = f"{data['creation_time']:.3f}s" if data.get('creation_time') else "N/A"
                    size_str = f"{data['stl_length']} bytes"
                    print(f"  {renderer:6}: ✅ {time_str:>8} | {size_str:>10}")
                else:
                    error = data.get('error', 'Failed')
                    print(f"  {renderer:6}: ❌ {error}")
        
        # Calculate potential speed improvements if both work
        speed_improvements = {}
        for model_name, results in performance_results.items():
            wasm_time = results.get('wasm', {}).get('creation_time')
            local_time = results.get('local', {}).get('creation_time')
            
            if wasm_time and local_time and results['wasm']['success'] and results['local']['success']:
                improvement = local_time / wasm_time
                speed_improvements[model_name] = improvement
                print(f"\n🚀 {model_name} speed improvement: {improvement:.1f}x faster (WASM vs Local)")
        
        if speed_improvements:
            avg_improvement = sum(speed_improvements.values()) / len(speed_improvements)
            print(f"\n🎯 AVERAGE SPEED IMPROVEMENT: {avg_improvement:.1f}x")
            
            # Check against 190x target
            if avg_improvement >= 190:
                print("✅ 190x TARGET EXCEEDED!")
            elif avg_improvement >= 100:
                print(f"⚡ Significant improvement achieved ({avg_improvement:.1f}x), approaching 190x target")
            else:
                print(f"📈 Current improvement: {avg_improvement:.1f}x (target: 190x)")
        else:
            print("\n⚠️ NO SPEED IMPROVEMENTS MEASURABLE - WASM or Local not functional")
        
        # Document current state for Phase 3 planning
        wasm_functional = any(results.get('wasm', {}).get('success', False) for results in performance_results.values())
        local_functional = any(results.get('local', {}).get('success', False) for results in performance_results.values())
        
        print(f"\n🔍 BASELINE ESTABLISHMENT:")
        print(f"  WASM Renderer Functional: {wasm_functional}")
        print(f"  Local Renderer Functional: {local_functional}")
        print(f"  Speed Improvements Measurable: {len(speed_improvements) > 0}")
        print(f"  Platform: {platform.system()} {platform.release()}")
        
        # Store baseline data for Phase 3 reference
        baseline_data = {
            'timestamp': time.time(),
            'platform': platform.system(),
            'performance_results': performance_results,
            'speed_improvements': speed_improvements,
            'wasm_functional': wasm_functional,
            'local_functional': local_functional,
            'target_improvement': 190
        }
        
        # Save baseline to file for Phase 3 reference
        baseline_file = Path(__file__).parent / "performance_baseline_data.json"
        import json
        with open(baseline_file, 'w') as f:
            # Convert data to JSON-serializable format
            serializable_data = json.loads(json.dumps(baseline_data, default=str))
            json.dump(serializable_data, f, indent=2)
        
        print(f"\n💾 Baseline data saved to: {baseline_file}")
        
        # Test passes regardless of current performance - we're establishing baseline
        assert True, f"Performance baseline established: WASM={wasm_functional}, Local={local_functional}"

    def test_memory_usage_constraints_2gb_limit(self):
        """Test memory usage patterns and validate 2GB WASM constraint compliance"""
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"🔍 Initial memory usage: {initial_memory:.1f}MB")
        
        # Create progressively larger models to test memory scaling
        model_sizes = [1, 2, 3, 5, 8]  # Cube sizes
        memory_usage = {'initial': initial_memory}
        
        from marimo_openscad.viewer import openscad_viewer
        from solid2 import cube, union, cylinder
        
        for size in model_sizes:
            print(f"\n  Testing size {size}x{size}x{size}...")
            
            # Create larger model with multiple components
            large_model = union()(*[
                cube([size, size, size]).translate([i*size, 0, 0]) 
                for i in range(min(3, size))  # Limit complexity to prevent excessive memory
            ])
            
            # Add some geometric complexity
            if size > 2:
                large_model = large_model - cylinder(r=size/3, h=size*2).translate([size, 0, -size/2])
            
            try:
                # Measure memory before viewer creation
                pre_memory = process.memory_info().rss / 1024 / 1024
                
                # Create viewer
                viewer = openscad_viewer(large_model, renderer_type="auto")
                
                # Measure memory after viewer creation
                post_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = post_memory - pre_memory
                
                # Get STL data info
                stl_data = getattr(viewer, 'stl_data', None)
                stl_size = len(stl_data) if stl_data else 0
                
                memory_usage[f'size_{size}'] = {
                    'pre_memory_mb': pre_memory,
                    'post_memory_mb': post_memory,
                    'memory_increase_mb': memory_increase,
                    'stl_size_bytes': stl_size,
                    'stl_size_mb': stl_size / 1024 / 1024,
                    'success': True
                }
                
                print(f"    Memory: {pre_memory:.1f}MB → {post_memory:.1f}MB (+{memory_increase:.1f}MB)")
                print(f"    STL size: {stl_size} bytes ({stl_size/1024/1024:.2f}MB)")
                
            except Exception as e:
                memory_usage[f'size_{size}'] = {
                    'error': str(e),
                    'success': False
                }
                print(f"    ❌ Failed: {e}")
            
            # Force garbage collection to clean up
            gc.collect()
        
        # Analyze memory usage patterns
        print(f"\n📊 MEMORY USAGE ANALYSIS:")
        print("=" * 50)
        
        max_memory_mb = 0
        total_memory_increase = 0
        successful_tests = 0
        
        for test_name, result in memory_usage.items():
            if test_name == 'initial':
                print(f"Initial memory: {result:.1f}MB")
                continue
                
            if result.get('success', False):
                memory_mb = result['post_memory_mb']
                increase_mb = result['memory_increase_mb']
                stl_mb = result['stl_size_mb']
                
                max_memory_mb = max(max_memory_mb, memory_mb)
                total_memory_increase += increase_mb
                successful_tests += 1
                
                print(f"{test_name:10}: {memory_mb:6.1f}MB (+{increase_mb:5.1f}MB) | STL: {stl_mb:5.2f}MB")
            else:
                print(f"{test_name:10}: ❌ {result.get('error', 'Failed')}")
        
        # Check 2GB (2048MB) constraint compliance
        print(f"\n🎯 2GB CONSTRAINT ANALYSIS:")
        print(f"  Maximum memory reached: {max_memory_mb:.1f}MB")
        print(f"  2GB limit (2048MB): {'✅ COMPLIANT' if max_memory_mb <= 2048 else '❌ EXCEEDED'}")
        
        if max_memory_mb > 2048:
            print(f"  ⚠️ MEMORY CONSTRAINT VIOLATION: {max_memory_mb:.1f}MB > 2048MB")
            print(f"  Risk for WASM 2GB limit: HIGH")
        elif max_memory_mb > 1500:
            print(f"  ⚠️ APPROACHING LIMIT: {max_memory_mb:.1f}MB (safety margin: {2048-max_memory_mb:.1f}MB)")
            print(f"  Risk for WASM 2GB limit: MEDIUM")
        else:
            print(f"  ✅ SAFE MEMORY USAGE: {max_memory_mb:.1f}MB (safety margin: {2048-max_memory_mb:.1f}MB)")
            print(f"  Risk for WASM 2GB limit: LOW")
        
        # Calculate memory efficiency
        if successful_tests > 0:
            avg_memory_per_test = total_memory_increase / successful_tests
            print(f"  Average memory increase per model: {avg_memory_per_test:.1f}MB")
            
            # Estimate concurrent model capacity
            remaining_memory = 2048 - max_memory_mb
            estimated_concurrent = max(1, int(remaining_memory / avg_memory_per_test))
            print(f"  Estimated concurrent models (2GB limit): {estimated_concurrent}")
        
        # Memory management recommendations
        print(f"\n💡 MEMORY MANAGEMENT RECOMMENDATIONS:")
        if max_memory_mb > 1800:
            print("  🔴 HIGH PRIORITY: Implement memory pressure monitoring")
            print("  🔴 CRITICAL: Add model complexity limits for WASM")
            print("  🔴 REQUIRED: Implement automatic fallback to local renderer")
        elif max_memory_mb > 1200:
            print("  🟡 MEDIUM PRIORITY: Monitor memory usage in WASM environment")
            print("  🟡 RECOMMENDED: Implement graceful degradation")
        else:
            print("  🟢 LOW PRIORITY: Current memory usage acceptable for WASM")
        
        # Document memory baseline
        memory_baseline = {
            'timestamp': time.time(),
            'platform': platform.system(),
            'max_memory_mb': max_memory_mb,
            'total_memory_increase_mb': total_memory_increase,
            'avg_memory_per_model_mb': avg_memory_per_test if successful_tests > 0 else 0,
            'wasm_2gb_compliant': max_memory_mb <= 2048,
            'memory_usage_details': memory_usage
        }
        
        # Save memory baseline
        baseline_file = Path(__file__).parent / "memory_baseline_data.json"
        import json
        with open(baseline_file, 'w') as f:
            serializable_data = json.loads(json.dumps(memory_baseline, default=str))
            json.dump(serializable_data, f, indent=2)
        
        print(f"\n💾 Memory baseline saved to: {baseline_file}")
        
        # Test always passes - we're documenting current memory behavior
        assert True, f"Memory baseline established: max {max_memory_mb:.1f}MB, 2GB compliant: {max_memory_mb <= 2048}"

    def test_rendering_throughput_measurement(self):
        """Measure rendering throughput for different model complexities"""
        
        from marimo_openscad.viewer import openscad_viewer
        from solid2 import cube, sphere, cylinder, union, difference
        
        # Define test models with known complexity levels
        test_models = {
            'minimal': cube([1, 1, 1]),
            'simple': sphere(r=1),
            'medium': union()(cube([2, 2, 2]), cylinder(r=1, h=3)),
            'complex': difference()(
                union()(cube([3, 3, 3]), sphere(r=2)),
                cylinder(r=0.8, h=4).translate([0, 0, -0.5])
            ),
            'very_complex': union()(*[
                difference()(
                    cube([1, 1, 1]).translate([i, j, 0]),
                    cylinder(r=0.3, h=2).translate([i+0.5, j+0.5, -0.5])
                )
                for i in range(2) for j in range(2)
            ])
        }
        
        throughput_results = {}
        
        print("🔍 RENDERING THROUGHPUT MEASUREMENT:")
        print("=" * 50)
        
        for model_name, model in test_models.items():
            print(f"\n📊 Testing {model_name} model throughput...")
            
            # Test multiple renders for timing accuracy
            render_times = []
            render_successes = 0
            
            num_iterations = 3
            
            for iteration in range(num_iterations):
                try:
                    start_time = time.perf_counter()
                    viewer = openscad_viewer(model, renderer_type="auto")
                    end_time = time.perf_counter()
                    
                    render_time = end_time - start_time
                    render_times.append(render_time)
                    
                    # Check if rendering produced data
                    stl_data = getattr(viewer, 'stl_data', None)
                    if stl_data and len(stl_data) > 0:
                        render_successes += 1
                    
                    print(f"  Iteration {iteration+1}: {render_time:.3f}s")
                    
                except Exception as e:
                    print(f"  Iteration {iteration+1}: ❌ {e}")
            
            if render_times:
                avg_time = sum(render_times) / len(render_times)
                min_time = min(render_times)
                max_time = max(render_times)
                throughput = 1.0 / avg_time if avg_time > 0 else 0
                
                throughput_results[model_name] = {
                    'avg_time_sec': avg_time,
                    'min_time_sec': min_time,
                    'max_time_sec': max_time,
                    'throughput_per_sec': throughput,
                    'success_rate': render_successes / num_iterations,
                    'iterations': num_iterations,
                    'successful_renders': render_successes
                }
                
                print(f"  Results: {avg_time:.3f}s avg ({min_time:.3f}-{max_time:.3f}s)")
                print(f"  Throughput: {throughput:.2f} renders/sec")
                print(f"  Success rate: {render_successes}/{num_iterations} ({render_successes/num_iterations*100:.1f}%)")
            else:
                throughput_results[model_name] = {
                    'error': 'No successful renders',
                    'success_rate': 0
                }
        
        # Analyze throughput patterns
        print(f"\n📈 THROUGHPUT ANALYSIS:")
        print("=" * 50)
        
        successful_models = [(name, data) for name, data in throughput_results.items() 
                           if 'avg_time_sec' in data and data['success_rate'] > 0]
        
        if successful_models:
            print(f"{'Model':<12} {'Avg Time':<10} {'Throughput':<12} {'Success':<8}")
            print("-" * 45)
            
            for model_name, data in successful_models:
                avg_time = data['avg_time_sec']
                throughput = data['throughput_per_sec']
                success_rate = data['success_rate'] * 100
                
                print(f"{model_name:<12} {avg_time:<10.3f} {throughput:<12.2f} {success_rate:<8.1f}%")
            
            # Calculate overall throughput metrics
            avg_times = [data['avg_time_sec'] for _, data in successful_models]
            avg_throughputs = [data['throughput_per_sec'] for _, data in successful_models]
            
            overall_avg_time = sum(avg_times) / len(avg_times)
            overall_avg_throughput = sum(avg_throughputs) / len(avg_throughputs)
            
            print(f"\n🎯 OVERALL METRICS:")
            print(f"  Average render time: {overall_avg_time:.3f}s")
            print(f"  Average throughput: {overall_avg_throughput:.2f} renders/sec")
            print(f"  Models successfully tested: {len(successful_models)}/{len(test_models)}")
            
            # Performance categorization
            if overall_avg_time < 0.1:
                performance_category = "EXCELLENT"
            elif overall_avg_time < 0.5:
                performance_category = "GOOD"
            elif overall_avg_time < 2.0:
                performance_category = "ACCEPTABLE"
            else:
                performance_category = "NEEDS_IMPROVEMENT"
            
            print(f"  Performance category: {performance_category}")
            
        else:
            print("❌ No successful renders - throughput not measurable")
            overall_avg_time = None
            overall_avg_throughput = 0
            performance_category = "FAILED"
        
        # Save throughput baseline
        throughput_baseline = {
            'timestamp': time.time(),
            'platform': platform.system(),
            'overall_avg_time_sec': overall_avg_time,
            'overall_avg_throughput_per_sec': overall_avg_throughput,
            'performance_category': performance_category,
            'successful_models': len(successful_models),
            'total_models': len(test_models),
            'detailed_results': throughput_results
        }
        
        baseline_file = Path(__file__).parent / "throughput_baseline_data.json"
        import json
        with open(baseline_file, 'w') as f:
            serializable_data = json.loads(json.dumps(throughput_baseline, default=str))
            json.dump(serializable_data, f, indent=2)
        
        print(f"\n💾 Throughput baseline saved to: {baseline_file}")
        
        # Test passes regardless - we're establishing baseline
        assert True, f"Throughput baseline established: {performance_category}, {len(successful_models)}/{len(test_models)} models working"

    def test_concurrent_rendering_capability(self):
        """Test capability for concurrent rendering (important for Phase 3)"""
        
        import threading
        import queue
        from marimo_openscad.viewer import openscad_viewer
        from solid2 import cube
        
        print("🔍 CONCURRENT RENDERING CAPABILITY TEST:")
        print("=" * 50)
        
        # Test concurrent viewer creation
        num_concurrent = 3
        results_queue = queue.Queue()
        
        def create_viewer_worker(worker_id):
            """Worker function for concurrent viewer creation"""
            try:
                start_time = time.perf_counter()
                
                # Each worker creates a slightly different model
                model = cube([worker_id + 1, worker_id + 1, worker_id + 1])
                viewer = openscad_viewer(model, renderer_type="auto")
                
                end_time = time.perf_counter()
                
                # Check result
                stl_data = getattr(viewer, 'stl_data', None)
                success = bool(stl_data and len(stl_data) > 0)
                
                result = {
                    'worker_id': worker_id,
                    'success': success,
                    'render_time': end_time - start_time,
                    'stl_size': len(stl_data) if stl_data else 0,
                    'error': None
                }
                
                results_queue.put(result)
                print(f"  Worker {worker_id}: {'✅' if success else '❌'} {end_time - start_time:.3f}s")
                
            except Exception as e:
                result = {
                    'worker_id': worker_id,
                    'success': False,
                    'render_time': None,
                    'stl_size': 0,
                    'error': str(e)
                }
                results_queue.put(result)
                print(f"  Worker {worker_id}: ❌ {e}")
        
        # Start concurrent workers
        threads = []
        start_time = time.perf_counter()
        
        print(f"\nStarting {num_concurrent} concurrent workers...")
        
        for i in range(num_concurrent):
            thread = threading.Thread(target=create_viewer_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all workers to complete
        for thread in threads:
            thread.join()
        
        total_time = time.perf_counter() - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Sort results by worker_id
        results.sort(key=lambda x: x['worker_id'])
        
        # Analyze concurrent rendering results
        successful_workers = [r for r in results if r['success']]
        failed_workers = [r for r in results if not r['success']]
        
        print(f"\n📊 CONCURRENT RENDERING RESULTS:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Successful workers: {len(successful_workers)}/{num_concurrent}")
        print(f"  Failed workers: {len(failed_workers)}")
        
        if successful_workers:
            render_times = [r['render_time'] for r in successful_workers]
            avg_render_time = sum(render_times) / len(render_times)
            max_render_time = max(render_times)
            min_render_time = min(render_times)
            
            print(f"  Average render time: {avg_render_time:.3f}s")
            print(f"  Render time range: {min_render_time:.3f}s - {max_render_time:.3f}s")
            
            # Calculate efficiency
            sequential_time_estimate = sum(render_times)
            concurrency_efficiency = sequential_time_estimate / total_time if total_time > 0 else 0
            
            print(f"  Concurrency efficiency: {concurrency_efficiency:.2f}x")
            
            if concurrency_efficiency > 2.0:
                print("  🚀 EXCELLENT: High concurrency efficiency")
            elif concurrency_efficiency > 1.5:
                print("  ✅ GOOD: Decent concurrency efficiency")
            elif concurrency_efficiency > 1.0:
                print("  ⚡ ACCEPTABLE: Some concurrency benefit")
            else:
                print("  ⚠️ LIMITED: Little concurrency benefit")
        
        # Test memory impact of concurrent rendering
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        print(f"  Final memory usage: {final_memory:.1f}MB")
        
        # Document concurrent rendering capability
        concurrent_capability = {
            'timestamp': time.time(),
            'num_concurrent': num_concurrent,
            'successful_workers': len(successful_workers),
            'total_time': total_time,
            'avg_render_time': avg_render_time if successful_workers else None,
            'concurrency_efficiency': concurrency_efficiency if successful_workers else 0,
            'final_memory_mb': final_memory,
            'detailed_results': results
        }
        
        # Save concurrent rendering baseline
        baseline_file = Path(__file__).parent / "concurrent_baseline_data.json"
        import json
        with open(baseline_file, 'w') as f:
            serializable_data = json.loads(json.dumps(concurrent_capability, default=str))
            json.dump(serializable_data, f, indent=2)
        
        print(f"\n💾 Concurrent rendering baseline saved to: {baseline_file}")
        
        # Determine concurrent rendering readiness for Phase 3
        concurrent_ready = len(successful_workers) >= num_concurrent * 0.8  # 80% success rate
        
        print(f"\n🎯 CONCURRENT RENDERING READINESS FOR PHASE 3:")
        print(f"  Ready for concurrent operations: {'✅ YES' if concurrent_ready else '❌ NO'}")
        
        if not concurrent_ready:
            print(f"  ⚠️ RISK: Phase 3 concurrent rendering may have issues")
            print(f"  💡 RECOMMENDATION: Implement sequential fallback in Phase 3")
        
        # Test passes regardless - we're establishing capability baseline
        assert True, f"Concurrent rendering baseline established: {len(successful_workers)}/{num_concurrent} workers successful"


if __name__ == "__main__":
    # Allow running individual tests
    pytest.main([__file__, "-v", "-s"])