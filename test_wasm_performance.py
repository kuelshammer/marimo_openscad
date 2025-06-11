#!/usr/bin/env python3
"""
Test WASM Performance Optimizations

Test the performance improvements from caching, web workers,
and memory management.
"""

import sys
import time
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from marimo_openscad.viewer import OpenSCADViewer
from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer

def test_performance_improvements():
    """Test performance improvements from Phase 3"""
    
    print("🚀 Testing WASM Performance Optimizations")
    print("="*60)
    
    # Test models of increasing complexity
    test_models = {
        "Simple": "cube([5, 5, 5]);",
        "Medium": """
            difference() {
                cube([20, 20, 20]);
                sphere(r=8);
            }
        """,
        "Complex": """
            union() {
                for(i = [0:5]) {
                    for(j = [0:5]) {
                        translate([i*3, j*3, 0])
                        cylinder(r=1, h=5);
                    }
                }
            }
        """,
        "Very Complex": """
            difference() {
                union() {
                    cube([30, 30, 30]);
                    for(i = [0:3]) {
                        rotate([0, 0, i*90])
                        translate([35, 0, 15])
                        cylinder(r=5, h=30, center=true);
                    }
                }
                
                // Create complex internal structure
                for(x = [5:5:25]) {
                    for(y = [5:5:25]) {
                        for(z = [5:5:25]) {
                            translate([x, y, z])
                            sphere(r=2);
                        }
                    }
                }
            }
        """
    }
    
    results = {}
    
    for model_name, scad_code in test_models.items():
        print(f"\n🧪 Testing {model_name} Model")
        print("-" * 40)
        
        model_results = {}
        
        # Test different renderer configurations
        configs = [
            ("Auto (WASM preferred)", {"renderer_type": "auto"}),
            ("Explicit WASM", {"renderer_type": "wasm"}),
            ("Local fallback", {"renderer_type": "local"})
        ]
        
        for config_name, config in configs:
            print(f"\n   📊 {config_name}:")
            
            try:
                # Create viewer with configuration
                start_time = time.time()
                viewer = OpenSCADViewer(**config)
                init_time = time.time() - start_time
                
                # Render model
                render_start = time.time()
                viewer.update_model(scad_code)
                render_time = time.time() - render_start
                
                # Check if STL was generated
                stl_data = viewer.stl_data
                stl_size = len(stl_data) if stl_data else 0
                
                # Get renderer info
                info = viewer.get_renderer_info()
                
                model_results[config_name] = {
                    "init_time": init_time * 1000,  # Convert to ms
                    "render_time": render_time * 1000,
                    "total_time": (init_time + render_time) * 1000,
                    "stl_size": stl_size,
                    "active_renderer": info.get('active_renderer', 'unknown'),
                    "status": info.get('status', 'unknown'),
                    "success": stl_size > 0
                }
                
                print(f"      Init: {init_time*1000:.2f}ms")
                print(f"      Render: {render_time*1000:.2f}ms") 
                print(f"      Total: {(init_time + render_time)*1000:.2f}ms")
                print(f"      STL Size: {stl_size} chars")
                print(f"      Renderer: {info.get('active_renderer', 'unknown')}")
                print(f"      Status: ✅ Success" if stl_size > 0 else "      Status: ❌ Failed")
                
            except Exception as e:
                model_results[config_name] = {
                    "error": str(e),
                    "success": False
                }
                print(f"      Status: ❌ Error - {e}")
        
        results[model_name] = model_results
    
    return results

def test_cache_performance():
    """Test caching performance improvements"""
    
    print("\n🗄️ Testing Cache Performance")
    print("="*40)
    
    # Test repeated rendering of the same model
    test_scad = """
        difference() {
            cube([15, 15, 15]);
            sphere(r=7);
        }
    """
    
    print("\n📦 First render (cold cache):")
    start_time = time.time()
    viewer1 = OpenSCADViewer(renderer_type="wasm")
    viewer1.update_model(test_scad)
    cold_time = time.time() - start_time
    print(f"   Cold cache time: {cold_time*1000:.2f}ms")
    
    print("\n🔥 Second render (warm cache):")
    start_time = time.time() 
    viewer2 = OpenSCADViewer(renderer_type="wasm")
    viewer2.update_model(test_scad)
    warm_time = time.time() - start_time
    print(f"   Warm cache time: {warm_time*1000:.2f}ms")
    
    if cold_time > 0 and warm_time > 0:
        improvement = ((cold_time - warm_time) / cold_time) * 100
        print(f"   Cache improvement: {improvement:.1f}% faster")
    
    return {
        "cold_cache_time": cold_time * 1000,
        "warm_cache_time": warm_time * 1000,
        "improvement_percent": improvement if 'improvement' in locals() else 0
    }

def test_memory_efficiency():
    """Test memory efficiency improvements"""
    
    print("\n💾 Testing Memory Efficiency")
    print("="*40)
    
    # Create multiple viewers and test memory usage
    viewers = []
    memory_stats = []
    
    for i in range(5):
        print(f"\n   Creating viewer {i+1}/5...")
        
        viewer = OpenSCADViewer(renderer_type="wasm")
        viewers.append(viewer)
        
        # Render a model
        viewer.update_model(f"cube([{5+i}, {5+i}, {5+i}]);")
        
        # Get memory stats if available
        info = viewer.get_renderer_info()
        stats = info.get('stats', {})
        
        memory_stats.append({
            "viewer_id": i+1,
            "stats": stats
        })
        
        print(f"      Renderer: {info.get('active_renderer', 'unknown')}")
        print(f"      Status: {info.get('status', 'unknown')}")
    
    print(f"\n   Created {len(viewers)} viewers successfully")
    print(f"   Memory stats collected: {len(memory_stats)} entries")
    
    # Clean up
    del viewers
    
    return {
        "viewers_created": len(viewers) if 'viewers' in locals() else 0,
        "memory_stats": memory_stats
    }

def generate_performance_report(results, cache_results, memory_results):
    """Generate a comprehensive performance report"""
    
    print("\n📊 Performance Report")
    print("="*60)
    
    # Model complexity analysis
    print("\n🎯 Model Complexity Performance:")
    for model_name, model_results in results.items():
        print(f"\n   {model_name} Model:")
        
        for config_name, config_results in model_results.items():
            if config_results.get('success', False):
                total_time = config_results.get('total_time', 0)
                renderer = config_results.get('active_renderer', 'unknown')
                print(f"      {config_name}: {total_time:.2f}ms ({renderer})")
            else:
                error = config_results.get('error', 'Unknown error')
                print(f"      {config_name}: ❌ {error}")
    
    # Cache performance
    print(f"\n🗄️ Cache Performance:")
    cold_time = cache_results.get('cold_cache_time', 0)
    warm_time = cache_results.get('warm_cache_time', 0)
    improvement = cache_results.get('improvement_percent', 0)
    
    print(f"   Cold cache: {cold_time:.2f}ms")
    print(f"   Warm cache: {warm_time:.2f}ms")
    print(f"   Improvement: {improvement:.1f}% faster")
    
    # Memory efficiency
    print(f"\n💾 Memory Efficiency:")
    viewers_created = memory_results.get('viewers_created', 0)
    print(f"   Concurrent viewers: {viewers_created}")
    print(f"   Memory stats: {len(memory_results.get('memory_stats', []))} collected")
    
    # Overall assessment
    print(f"\n🏆 Overall Assessment:")
    
    # Count successful configurations
    total_tests = 0
    successful_tests = 0
    
    for model_results in results.values():
        for config_results in model_results.values():
            total_tests += 1
            if config_results.get('success', False):
                successful_tests += 1
    
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"   Success rate: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    print(f"   Cache improvement: {'✅ Significant' if improvement > 10 else '⚠️ Minimal'}")
    print(f"   Memory efficiency: {'✅ Good' if viewers_created >= 5 else '⚠️ Limited'}")
    
    if success_rate > 80 and improvement > 10:
        print(f"   🎉 Performance optimizations working well!")
    elif success_rate > 60:
        print(f"   ⚠️ Performance optimizations partially working")
    else:
        print(f"   ❌ Performance optimizations need improvement")

def main():
    """Run all performance tests"""
    
    print("🚀 WASM Performance Testing Suite")
    print("="*70)
    
    try:
        # Run performance tests
        print("\n1️⃣ Running model complexity tests...")
        results = test_performance_improvements()
        
        print("\n2️⃣ Running cache performance tests...")
        cache_results = test_cache_performance()
        
        print("\n3️⃣ Running memory efficiency tests...")
        memory_results = test_memory_efficiency()
        
        # Generate comprehensive report
        generate_performance_report(results, cache_results, memory_results)
        
        print("\n✅ Performance testing completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Performance testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)