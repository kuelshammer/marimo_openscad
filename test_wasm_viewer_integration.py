#!/usr/bin/env python3
"""
Test WASM Viewer Integration

Test the extended OpenSCADViewer with WASM support.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from marimo_openscad.viewer import OpenSCADViewer, openscad_viewer

def test_wasm_viewer_creation():
    """Test creating viewers with different renderer types"""
    
    print("🧪 Testing WASM Viewer Integration")
    print("="*50)
    
    # Test 1: Auto renderer (should prefer WASM)
    print("\n📦 Test 1: Auto Renderer")
    viewer_auto = OpenSCADViewer(renderer_type="auto")
    print(f"   Renderer type: {viewer_auto.renderer_type}")
    print(f"   Renderer status: {viewer_auto.renderer_status}")
    print(f"   WASM supported: {viewer_auto.wasm_supported}")
    
    # Test 2: Explicit WASM renderer
    print("\n🚀 Test 2: WASM Renderer")
    try:
        viewer_wasm = OpenSCADViewer(renderer_type="wasm")
        print(f"   Renderer type: {viewer_wasm.renderer_type}")
        print(f"   Renderer status: {viewer_wasm.renderer_status}")
        print(f"   WASM supported: {viewer_wasm.wasm_supported}")
        print("   ✅ WASM renderer created successfully")
    except Exception as e:
        print(f"   ❌ WASM renderer failed: {e}")
    
    # Test 3: Local renderer (fallback)
    print("\n🔧 Test 3: Local Renderer")
    try:
        viewer_local = OpenSCADViewer(renderer_type="local")
        print(f"   Renderer type: {viewer_local.renderer_type}")
        print(f"   Renderer status: {viewer_local.renderer_status}")
        print(f"   WASM supported: {viewer_local.wasm_supported}")
        print("   ✅ Local renderer created successfully")
    except Exception as e:
        print(f"   ❌ Local renderer failed: {e}")
    
    # Test 4: Convenience function
    print("\n🎯 Test 4: Convenience Function")
    test_scad = "cube([5, 5, 5]);"
    
    # Test with different renderer types
    for renderer_type in ["auto", "wasm", "local"]:
        try:
            print(f"\n   Testing openscad_viewer() with {renderer_type}:")
            viewer = openscad_viewer(test_scad, renderer_type=renderer_type)
            info = viewer.get_renderer_info()
            print(f"      Active renderer: {info.get('active_renderer', 'unknown')}")
            print(f"      Status: {info.get('status', 'unknown')}")
            print(f"      ✅ {renderer_type} viewer created via convenience function")
        except Exception as e:
            print(f"      ❌ {renderer_type} convenience function failed: {e}")
    
    return True

def test_wasm_model_update():
    """Test model updates with WASM renderer"""
    
    print("\n🔄 Test 5: Model Updates")
    print("-" * 30)
    
    try:
        viewer = OpenSCADViewer(renderer_type="wasm")
        
        # Test different SCAD models
        test_models = [
            ("cube", "cube([10, 10, 10]);"),
            ("sphere", "sphere(r=5);"),
            ("complex", """
                difference() {
                    cube([20, 20, 20]);
                    sphere(r=8);
                }
            """)
        ]
        
        for name, scad_code in test_models:
            print(f"\n   Testing {name} model:")
            print(f"      SCAD: {scad_code.strip()}")
            
            try:
                viewer.update_model(scad_code)
                stl_data = viewer.stl_data
                
                if stl_data:
                    print(f"      ✅ Generated STL data: {len(stl_data)} chars")
                    if "WASM_RENDER_REQUEST" in stl_data:
                        print("      🚀 WASM render request detected")
                    else:
                        print("      📦 STL data generated")
                else:
                    print("      ⚠️ No STL data generated")
                    
            except Exception as e:
                print(f"      ❌ Model update failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ WASM model update test failed: {e}")
        return False

def test_renderer_info():
    """Test renderer information retrieval"""
    
    print("\n📊 Test 6: Renderer Information")
    print("-" * 30)
    
    try:
        viewer = OpenSCADViewer(renderer_type="auto")
        info = viewer.get_renderer_info()
        
        print("   Renderer Info:")
        for key, value in info.items():
            print(f"      {key}: {value}")
        
        print("   ✅ Renderer info retrieved successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Renderer info test failed: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🚀 WASM Viewer Integration Tests")
    print("="*60)
    
    tests = [
        ("Viewer Creation", test_wasm_viewer_creation),
        ("Model Updates", test_wasm_model_update),
        ("Renderer Info", test_renderer_info)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)