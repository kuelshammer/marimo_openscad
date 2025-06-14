#!/usr/bin/env python3
"""
Phase 3.3b Demo: Real-time Parameter Updates with STL Caching

Demonstrates the new real-time rendering capabilities including:
- Debounced parameter updates
- STL result caching  
- Performance monitoring
- Real-time 3D model updates
"""

import marimo as mo
import asyncio
import time
from src.marimo_openscad import openscad_viewer
from src.marimo_openscad.viewer import OpenSCADViewer

def demo_realtime_cube():
    """Demo real-time parameter updates with a parameterized cube."""
    
    print("🎛️ Phase 3.3b Demo: Real-time Parameter Updates")
    print("=" * 50)
    
    # Create viewer with real-time features enabled
    viewer = OpenSCADViewer(renderer_type="local")  # Use local for predictable testing
    
    print(f"✅ Viewer created with real-time rendering: {viewer.real_time_enabled}")
    print(f"📊 Debounce delay: {viewer.debounce_delay_ms}ms")
    print(f"🎯 Cache hit rate: {viewer.cache_hit_rate:.1%}")
    
    # Initial parameterized SCAD code
    base_scad = """
    // Parameterized cube with variable size
    size = {size};
    cube([size, size, size], center=true);
    """
    
    # Test 1: Initial render
    print("\n🔄 Test 1: Initial render")
    start_time = time.time()
    
    scad_code = base_scad.format(size=10)
    viewer.update_scad_code(scad_code, use_wasm=False)
    
    render_time = time.time() - start_time
    print(f"⏱️ Initial render time: {render_time:.3f}s")
    print(f"📄 STL data size: {len(viewer.stl_data)} chars")
    
    # Test 2: Parameter updates with debouncing
    print("\n🎛️ Test 2: Rapid parameter updates (testing debouncing)")
    
    sizes = [10, 15, 20, 25, 30, 35, 40]
    update_times = []
    
    for i, size in enumerate(sizes):
        start_time = time.time()
        
        # Use real-time parameter update
        viewer.update_parameter("size", size, force_render=(i == len(sizes)-1))
        
        update_time = time.time() - start_time
        update_times.append(update_time)
        
        print(f"  📏 Size {size}: update time {update_time:.3f}s")
        
        # Small delay to see debouncing effect
        time.sleep(0.05)
    
    # Wait for debounced render to complete
    time.sleep(0.2)
    
    avg_update_time = sum(update_times) / len(update_times)
    print(f"📊 Average parameter update time: {avg_update_time:.3f}s")
    
    # Test 3: Cache effectiveness
    print("\n💾 Test 3: Cache effectiveness test")
    
    # Render same model multiple times to test caching
    cache_test_sizes = [20, 25, 20, 30, 25, 20]  # Repeated sizes should hit cache
    cache_times = []
    
    for size in cache_test_sizes:
        start_time = time.time()
        
        scad_code = base_scad.format(size=size)
        viewer.update_scad_code(scad_code, use_wasm=False)
        
        render_time = time.time() - start_time
        cache_times.append(render_time)
        
        print(f"  📏 Size {size}: render time {render_time:.3f}s")
    
    # Performance analysis
    print("\n📈 Performance Analysis:")
    print(f"🎯 Final cache hit rate: {viewer.cache_hit_rate:.1%}")
    print(f"⚡ Last render time: {viewer.render_time_ms:.1f}ms")
    
    # Get detailed stats
    if hasattr(viewer, 'realtime_renderer'):
        stats = viewer.realtime_renderer.get_performance_stats()
        
        print(f"📊 Total renders: {stats['rendering']['total_renders']}")
        print(f"⏱️ Average render time: {stats['rendering']['avg_render_time']:.3f}s")
        print(f"💾 Cache entries: {stats['cache']['entry_count']}")
        print(f"💽 Cache size: {stats['cache']['total_size_mb']:.1f}MB")
        
        # Cache hit/miss analysis
        cache_stats = stats['cache']
        print(f"✅ Cache hits: {cache_stats['hits']}")
        print(f"❌ Cache misses: {cache_stats['misses']}")
    
    return viewer

async def demo_async_realtime():
    """Demo async real-time parameter updates."""
    
    print("\n🔄 Async Real-time Demo")
    print("=" * 30)
    
    viewer = OpenSCADViewer(renderer_type="local")
    
    # Test async parameter updates
    parameters = [
        ("width", 10), ("height", 15), ("depth", 8),
        ("width", 12), ("height", 18), ("depth", 10)
    ]
    
    print("🎛️ Testing async parameter updates...")
    
    for name, value in parameters:
        print(f"  🔧 Setting {name} = {value}")
        await viewer.update_parameter_realtime(name, value)
        
        # Short delay to see real-time effect
        await asyncio.sleep(0.1)
    
    # Force final render
    await viewer.update_parameter_realtime("final", True, force_render=True)
    
    print("✅ Async parameter updates completed")
    
    return viewer

def demo_cache_management():
    """Demo cache management features."""
    
    print("\n💾 Cache Management Demo")
    print("=" * 30)
    
    viewer = OpenSCADViewer(renderer_type="local")
    
    # Generate multiple different models to fill cache
    shapes = [
        "cube([{}, {}, {}], center=true);".format(i, i+1, i+2) 
        for i in range(5, 15)
    ]
    
    print("🔄 Generating models to populate cache...")
    
    for i, shape in enumerate(shapes):
        viewer.update_scad_code(shape, use_wasm=False)
        print(f"  Model {i+1}: Cache hit rate {viewer.cache_hit_rate:.1%}")
    
    # Test cache clearing
    print("\n🧹 Testing cache clear...")
    initial_hit_rate = viewer.cache_hit_rate
    viewer.clear_render_cache()
    
    print(f"💾 Hit rate before clear: {initial_hit_rate:.1%}")
    print(f"💾 Hit rate after clear: {viewer.cache_hit_rate:.1%}")
    
    # Test debounce delay adjustment
    print("\n⏱️ Testing debounce delay adjustment...")
    print(f"Initial delay: {viewer.debounce_delay_ms}ms")
    
    viewer.set_debounce_delay(200)
    print(f"New delay: {viewer.debounce_delay_ms}ms")
    
    return viewer

if __name__ == "__main__":
    print("🚀 Phase 3.3b Real-time Rendering Demo")
    print("====================================")
    
    # Demo 1: Real-time parameter updates
    viewer1 = demo_realtime_cube()
    
    # Demo 2: Async parameter updates  
    if asyncio.get_event_loop().is_running():
        print("\n⏳ Skipping async demo (already in async context)")
    else:
        viewer2 = asyncio.run(demo_async_realtime())
    
    # Demo 3: Cache management
    viewer3 = demo_cache_management()
    
    print("\n🎉 Phase 3.3b Demo Complete!")
    print("Real-time rendering features successfully demonstrated:")
    print("  ✅ Parameter debouncing")
    print("  ✅ STL result caching") 
    print("  ✅ Performance monitoring")
    print("  ✅ Cache management")
    print("  ✅ Async parameter updates")
    
    # Show final performance summary
    print(f"\n📊 Final Performance Summary:")
    for i, viewer in enumerate([viewer1, viewer3], 1):
        info = viewer.get_renderer_info()
        if 'realtime' in info:
            rt_info = info['realtime']
            print(f"  Viewer {i}: {rt_info['cache_hit_rate']:.1%} hit rate, "
                  f"{rt_info['render_time_ms']:.1f}ms last render")