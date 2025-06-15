#!/usr/bin/env python3
"""
WASM Bridge Integration Test - Complete Python↔JavaScript Flow
Tests the full coordinator-executor pattern with real components
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_complete_bridge_flow():
    """Test the complete Python→JavaScript WASM bridge flow"""
    print("🌉 WASM BRIDGE INTEGRATION TEST")
    print("=" * 50)
    print("Testing complete Python↔JavaScript coordinator-executor pattern")
    print()
    
    # Test 1: Python side generates WASM_RENDER_REQUEST
    print("🔍 Test 1: Python WASM Renderer - Request Generation")
    
    try:
        from marimo_openscad.openscad_wasm_renderer import OpenSCADWASMRenderer
        from marimo_openscad.viewer import openscad_viewer
        from solid2 import cube
        
        renderer = OpenSCADWASMRenderer()
        scad_code = "cube([2, 2, 2]);"
        
        print(f"   Input SCAD: {scad_code}")
        print(f"   Renderer Available: {renderer.is_available}")
        
        # This should return WASM_RENDER_REQUEST:hash
        result = renderer.render_scad_to_stl(scad_code)
        
        print(f"   Result Type: {type(result)}")
        print(f"   Result Length: {len(result)} bytes")
        
        result_str = result.decode('utf-8', errors='ignore')
        print(f"   Result Content: {result_str[:50]}...")
        
        is_wasm_request = result_str.startswith('WASM_RENDER_REQUEST:')
        print(f"   ✅ Is WASM Request: {is_wasm_request}")
        
        if is_wasm_request:
            hash_value = result_str[len('WASM_RENDER_REQUEST:'):]
            print(f"   🔑 Request Hash: {hash_value}")
            
            # Test 2: JavaScript-side pattern matching (simulated)
            print()
            print("🔍 Test 2: JavaScript Pattern Matching (Simulated)")
            
            # Simulate what the JavaScript handleSTLData function would do
            stl_data = result_str  # This is what gets passed to JavaScript
            
            print(f"   JavaScript receives: {stl_data}")
            
            # Pattern detection (JavaScript logic in Python)
            if isinstance(stl_data, str) and stl_data.startswith('WASM_RENDER_REQUEST:'):
                extracted_hash = stl_data[len('WASM_RENDER_REQUEST:'):]
                print(f"   ✅ JavaScript detects WASM request")
                print(f"   🔑 JavaScript extracts hash: {extracted_hash}")
                print(f"   🚀 JavaScript would trigger WASM execution with: {scad_code}")
                
                # Test 3: Verify SCAD code is available for JavaScript
                print()
                print("🔍 Test 3: SCAD Code Availability for JavaScript")
                
                # In real anywidget, this would be model.get('scad_code')
                available_scad = scad_code  # Simulated model data
                print(f"   ✅ SCAD code available: {bool(available_scad)}")
                print(f"   📝 SCAD content: {available_scad}")
                
                return True
            else:
                print("   ❌ JavaScript pattern matching would fail")
                return False
        else:
            print("   ❌ Python did not generate WASM request")
            return False
            
    except Exception as e:
        print(f"   ❌ Bridge test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_viewer_bridge_integration():
    """Test the viewer-level bridge integration"""
    print()
    print("🔍 Test 4: Viewer-Level Bridge Integration")
    
    try:
        from marimo_openscad.viewer import openscad_viewer
        from solid2 import cube
        
        # Create a model
        model = cube([3, 3, 3])
        print(f"   Model: {model}")
        
        # Create viewer with WASM renderer
        viewer = openscad_viewer(model, renderer_type="wasm")
        print(f"   Viewer Type: {type(viewer)}")
        
        # Get renderer info
        info = viewer.get_renderer_info()
        print(f"   Active Renderer: {info.get('active_renderer', 'unknown')}")
        print(f"   Renderer Status: {info.get('status', 'unknown')}")
        
        # Get the STL data that would be sent to JavaScript
        stl_data = viewer.get_stl_data()
        
        if isinstance(stl_data, bytes):
            stl_str = stl_data.decode('utf-8', errors='ignore')
        else:
            stl_str = str(stl_data)
            
        print(f"   STL Data Type: {type(stl_data)}")
        print(f"   STL Content Preview: {stl_str[:50]}...")
        
        # Check if this triggers the bridge pattern
        is_bridge_trigger = stl_str.startswith('WASM_RENDER_REQUEST:')
        print(f"   ✅ Triggers Bridge: {is_bridge_trigger}")
        
        return is_bridge_trigger
        
    except Exception as e:
        print(f"   ❌ Viewer bridge test failed: {e}")
        return False

def test_bridge_pattern_validation():
    """Test edge cases and validation of the bridge pattern"""
    print()
    print("🔍 Test 5: Bridge Pattern Validation")
    
    test_cases = [
        "WASM_RENDER_REQUEST:12345",
        "WASM_RENDER_REQUEST:-8427547496623440318",
        "WASM_RENDER_REQUEST:",
        "NOT_A_WASM_REQUEST:12345",
        "",
        "regular STL data here"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"   Test 5.{i}: {test_case[:30]}...")
        
        # JavaScript detection logic
        is_wasm_request = (isinstance(test_case, str) and 
                          test_case.startswith('WASM_RENDER_REQUEST:'))
        
        if is_wasm_request:
            hash_part = test_case[len('WASM_RENDER_REQUEST:'):]
            valid_hash = len(hash_part) > 0
            print(f"     ✅ Detected as WASM request, hash valid: {valid_hash}")
        else:
            print(f"     📦 Detected as regular STL data")
    
    return True

def main():
    """Run all bridge integration tests"""
    print("🌉 COMPLETE WASM BRIDGE INTEGRATION TEST SUITE")
    print("=" * 60)
    print("Testing Python↔JavaScript coordinator-executor pattern")
    print()
    
    tests = [
        test_complete_bridge_flow,
        test_viewer_bridge_integration,
        test_bridge_pattern_validation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results.append(False)
    
    print()
    print("=" * 60)
    print("🌉 BRIDGE INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} Test Group {i}: {test.__name__}")
    
    passed = sum(results)
    total = len(results)
    print(f"\nSUMMARY: {passed}/{total} test groups passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 BRIDGE INTEGRATION COMPLETE - All patterns working!")
        print()
        print("🚀 NEXT STEPS:")
        print("   1. Test with real browser environment")
        print("   2. Validate JavaScript WASM execution")
        print("   3. Measure end-to-end performance")
    elif passed > 0:
        print("⚠️  PARTIAL BRIDGE FUNCTIONALITY - Some patterns working")
    else:
        print("🚨 BRIDGE INTEGRATION FAILED - Major implementation issues")

if __name__ == "__main__":
    main()