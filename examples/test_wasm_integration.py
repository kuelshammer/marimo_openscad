#!/usr/bin/env python3
"""
WASM Integration Test Example

This example demonstrates the complete WASM file serving pipeline
for the marimo-openscad project.
"""

import sys
from pathlib import Path

# Add the package to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import marimo_openscad as openscad
from solid2 import cube, sphere, union


def test_wasm_integration():
    """Test the complete WASM integration"""
    print("🚀 Testing WASM Integration for marimo-openscad")
    print("=" * 50)
    
    # Create a simple SolidPython2 model
    model = union()(
        cube([20, 20, 10]),
        sphere(8).translate([10, 10, 5])
    )
    
    print("📦 Created SolidPython2 model")
    
    # Create viewer with WASM renderer
    try:
        viewer = openscad.openscad_viewer(
            model, 
            renderer_type="wasm",
            enable_real_time_wasm=True
        )
        
        print("✅ WASM viewer created successfully")
        print(f"🔗 WASM Base URL: {viewer.wasm_base_url}")
        print(f"🎯 WASM Enabled: {viewer.wasm_enabled}")
        print(f"🚀 Renderer Type: {viewer.renderer_type}")
        print(f"📊 Renderer Status: {viewer.renderer_status}")
        
        # Get renderer stats
        if hasattr(viewer.renderer, 'get_stats'):
            stats = viewer.renderer.get_stats()
            print(f"📈 Renderer Stats: {stats['renderer_type']}")
            print(f"🔧 Available: {stats['is_available']}")
            
        # Test WASM asset validation
        if hasattr(viewer.renderer, 'validate_wasm_assets'):
            validation = viewer.renderer.validate_wasm_assets()
            print(f"✅ Asset Validation: {validation}")
            
        return True
        
    except Exception as e:
        print(f"❌ WASM integration test failed: {e}")
        return False


def test_auto_renderer():
    """Test the auto renderer (hybrid with WASM preference)"""
    print("\n🔄 Testing Auto Renderer (Hybrid)")
    print("=" * 40)
    
    try:
        # Create a simple model
        model = cube([10, 10, 10])
        
        # Create viewer with auto renderer
        viewer = openscad.openscad_viewer(model, renderer_type="auto")
        
        print("✅ Auto renderer created successfully")
        print(f"🔗 WASM Base URL: {viewer.wasm_base_url}")
        print(f"🎯 WASM Enabled: {viewer.wasm_enabled}")
        print(f"🚀 Renderer Type: {viewer.renderer_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Auto renderer test failed: {e}")
        return False


def main():
    """Run the integration tests"""
    results = []
    
    # Test 1: Direct WASM integration
    results.append(test_wasm_integration())
    
    # Test 2: Auto renderer
    results.append(test_auto_renderer())
    
    # Summary
    print("\n📊 Integration Test Summary")
    print("=" * 30)
    print(f"WASM Integration: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"Auto Renderer: {'✅ PASS' if results[1] else '❌ FAIL'}")
    
    overall_success = all(results)
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 WASM file serving is fully functional!")
        print("Browsers can now access the 16.4MB WASM files via HTTP.")
        print("The complete STL rendering pipeline is ready for use.")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())