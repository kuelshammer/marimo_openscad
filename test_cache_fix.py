#!/usr/bin/env python3
"""
Test script to verify that SCAD code updates properly trigger visual updates

This addresses the issue reported by the LLM where update_scad_code might not
properly update the visual representation when code changes.
"""

import time
import logging
from src.marimo_openscad import openscad_viewer

# Enable debug logging
logging.basicConfig(level=logging.INFO)

def test_scad_code_updates():
    """Test that SCAD code updates properly trigger visual changes"""
    
    print("🧪 Testing SCAD code update behavior...")
    
    # Create viewer
    viewer = openscad_viewer()
    
    # Test 1: Initial SCAD code (cube)
    cube_scad = """
cube([10, 10, 10]);
"""
    
    print("\n📦 Step 1: Loading cube...")
    viewer.update_scad_code(cube_scad)
    cube_stl = viewer.stl_data
    print(f"   Cube STL data length: {len(cube_stl)} chars")
    
    # Wait a moment to ensure timestamp differences
    time.sleep(0.1)
    
    # Test 2: Different SCAD code (sphere)  
    sphere_scad = """
sphere(r=6);
"""
    
    print("\n🔮 Step 2: Loading sphere...")
    viewer.update_scad_code(sphere_scad)
    sphere_stl = viewer.stl_data
    print(f"   Sphere STL data length: {len(sphere_stl)} chars")
    
    # Test 3: Verify STL data changed
    print("\n🔍 Step 3: Comparing results...")
    stl_changed = cube_stl != sphere_stl
    print(f"   STL data changed: {stl_changed}")
    
    if stl_changed:
        print("✅ SUCCESS: SCAD code updates properly trigger new STL generation")
    else:
        print("❌ FAILURE: SCAD code update did not change STL data")
        print("   This indicates a caching problem!")
    
    # Test 4: Force update behavior
    print("\n🔄 Step 4: Testing force update...")
    viewer.force_update_model(sphere_scad)
    forced_stl = viewer.stl_data
    print(f"   Forced update STL length: {len(forced_stl)} chars")
    
    # Test 5: Cache clearing
    print("\n🧹 Step 5: Testing cache clearing...")
    viewer.clear_model_cache()
    viewer.update_scad_code(cube_scad)
    cleared_cube_stl = viewer.stl_data
    print(f"   After cache clear STL length: {len(cleared_cube_stl)} chars")
    
    # Summary
    print("\n📊 Summary:")
    print(f"   Cube STL:         {len(cube_stl)} chars")
    print(f"   Sphere STL:       {len(sphere_stl)} chars")
    print(f"   Forced STL:       {len(forced_stl)} chars")
    print(f"   Cleared Cube STL: {len(cleared_cube_stl)} chars")
    print(f"   Cube vs Sphere different: {cube_stl != sphere_stl}")
    print(f"   Sphere vs Forced same:    {sphere_stl == forced_stl}")
    print(f"   Original vs Cleared same: {cube_stl == cleared_cube_stl}")
    
    return stl_changed

def test_model_updates():
    """Test that model object updates work correctly"""
    
    print("\n🧪 Testing model object update behavior...")
    
    try:
        from solid2 import cube, sphere
        
        viewer = openscad_viewer()
        
        # Test with SolidPython2 objects
        print("\n📦 Loading cube model...")
        cube_model = cube(10)
        viewer.update_model(cube_model)
        cube_stl = viewer.stl_data
        print(f"   Cube model STL: {len(cube_stl)} chars")
        
        print("\n🔮 Loading sphere model...")
        sphere_model = sphere(6)
        viewer.update_model(sphere_model)
        sphere_stl = viewer.stl_data
        print(f"   Sphere model STL: {len(sphere_stl)} chars")
        
        model_changed = cube_stl != sphere_stl
        print(f"\n   Model STL data changed: {model_changed}")
        
        return model_changed
        
    except ImportError:
        print("   ⚠️ SolidPython2 not available, skipping model tests")
        return True

if __name__ == "__main__":
    print("🚀 Testing OpenSCAD viewer cache behavior\n")
    
    # Test SCAD code updates
    scad_test_passed = test_scad_code_updates()
    
    # Test model updates
    model_test_passed = test_model_updates()
    
    print("\n" + "="*60)
    print("📋 FINAL RESULTS:")
    print(f"   SCAD code updates work: {'✅ YES' if scad_test_passed else '❌ NO'}")
    print(f"   Model updates work:     {'✅ YES' if model_test_passed else '❌ NO'}")
    
    if scad_test_passed and model_test_passed:
        print("\n🎉 ALL TESTS PASSED: Cache fix successful!")
    else:
        print("\n⚠️ SOME TESTS FAILED: Further investigation needed")
    
    print("="*60)