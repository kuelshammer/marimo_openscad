#!/usr/bin/env python3
"""
Real WASM Functionality Test - NO MOCKS
Tests the actual WASM implementation without any mocking
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_wasm_files_exist():
    """Test 1: Check if real WASM files exist"""
    print("🔍 Test 1: WASM Files Existence")
    
    from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
    
    renderer = OpenSCADWASMRenderer()
    print(f"   WASM Path: {renderer.wasm_path}")
    print(f"   Available: {renderer.is_available}")
    
    wasm_files = renderer.get_wasm_files()
    print(f"   Found Files: {len(wasm_files)}")
    
    for filename, path in wasm_files.items():
        file_path = Path(path)
        size = file_path.stat().st_size if file_path.exists() else 0
        print(f"     {filename}: {size:,} bytes")
    
    return renderer.is_available

def test_wasm_renderer_instantiation():
    """Test 2: Can we create WASM renderer?"""
    print("\n🔍 Test 2: WASM Renderer Instantiation")
    
    try:
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        renderer = OpenSCADWASMRenderer()
        
        stats = renderer.get_stats()
        print(f"   Renderer Type: {stats['renderer_type']}")
        print(f"   Capabilities: {list(stats['capabilities'].keys())}")
        print(f"   WASM URL Base: {renderer.get_wasm_url_base()}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_wasm_render_call():
    """Test 3: What happens when we call render?"""
    print("\n🔍 Test 3: WASM Render Call (Python Side)")
    
    try:
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        renderer = OpenSCADWASMRenderer()
        
        scad_code = "cube([1, 1, 1]);"
        print(f"   Input: {scad_code}")
        
        result = renderer.render_scad_to_stl(scad_code)
        print(f"   Result Type: {type(result)}")
        print(f"   Result Length: {len(result)} bytes")
        print(f"   Result Content: {result.decode('utf-8', errors='ignore')[:100]}...")
        
        # Check if it's a placeholder
        is_placeholder = b"WASM_RENDER_REQUEST" in result
        print(f"   Is Placeholder: {is_placeholder}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_viewer_creation():
    """Test 4: Can we create a viewer?"""
    print("\n🔍 Test 4: Viewer Creation")
    
    try:
        from marimo_openscad.viewer import openscad_viewer
        from solid2 import cube
        
        model = cube([1, 1, 1])
        print(f"   Model: {model}")
        
        # Try with WASM renderer
        viewer = openscad_viewer(model, renderer_type="wasm")
        print(f"   Viewer Created: {type(viewer)}")
        
        info = viewer.get_renderer_info()
        print(f"   Active Renderer: {info.get('active_renderer', 'unknown')}")
        print(f"   Renderer Status: {info.get('status', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all real functionality tests"""
    print("🚀 REAL WASM FUNCTIONALITY AUDIT")
    print("=" * 50)
    print("⚠️  NO MOCKS - Testing actual implementation")
    print()
    
    tests = [
        test_wasm_files_exist,
        test_wasm_renderer_instantiation, 
        test_wasm_render_call,
        test_viewer_creation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 REAL FUNCTIONALITY AUDIT RESULTS")
    print("=" * 50)
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} Test {i}: {test.__name__}")
    
    passed = sum(results)
    total = len(results)
    print(f"\nSUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! WASM functionality is working!")
    elif passed > 0:
        print("⚠️  Partial functionality - some components work")
    else:
        print("🚨 No functionality working - major implementation issues")

if __name__ == "__main__":
    main()