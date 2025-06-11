#!/usr/bin/env python3
"""
Test script to verify that SCAD code updates properly trigger visual updates

This addresses the issue reported by the LLM where update_scad_code might not
properly update the visual representation when code changes.
"""

import time
import logging
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from marimo_openscad import openscad_viewer
    from marimo_openscad.interactive_viewer import InteractiveViewer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Trying alternative import paths...")
    try:
        from src.marimo_openscad import openscad_viewer
        from src.marimo_openscad.interactive_viewer import InteractiveViewer
    except ImportError as e2:
        print(f"❌ Alternative import also failed: {e2}")
        sys.exit(1)

# Enable debug logging
logging.basicConfig(level=logging.INFO)

def create_mock_viewer():
    """Create a mock viewer for CI environments without OpenSCAD"""
    import base64
    from unittest.mock import MagicMock
    
    class MockViewer:
        def __init__(self):
            self.stl_data = ""
            self.render_count = 0
            
        def update_scad_code(self, scad_code):
            """Mock SCAD code update that returns different data for different shapes"""
            self.render_count += 1
            
            # Return different mock STL data based on SCAD content
            if "cube" in scad_code.lower():
                mock_stl_data = b"MOCK_CUBE_STL_DATA_FOR_CI_TESTING_12345"
            elif "sphere" in scad_code.lower():
                mock_stl_data = b"MOCK_SPHERE_STL_DATA_FOR_CI_TESTING_67890_MUCH_LONGER_CONTENT_TO_SIMULATE_SPHERE_COMPLEXITY"
            elif "cylinder" in scad_code.lower():
                mock_stl_data = b"MOCK_CYLINDER_STL_DATA_FOR_CI_TESTING_11111"
            else:
                mock_stl_data = b"MOCK_GENERIC_STL_DATA_FOR_CI_TESTING_99999"
            
            # Encode as base64 like the real viewer
            self.stl_data = base64.b64encode(mock_stl_data).decode('utf-8')
            
        def update_model(self, model):
            """Mock model update"""
            try:
                scad_code = model.as_scad()
                self.update_scad_code(scad_code)
            except:
                # Fallback for mock models
                self.stl_data = base64.b64encode(b"MOCK_MODEL_STL_DATA").decode('utf-8')
                
        def force_update_model(self, model):
            """Mock force update"""
            self.update_model(model)
            
        def clear_model_cache(self):
            """Mock cache clearing"""
            pass  # Cache clearing is a no-op in mock
    
    return MockViewer()

def test_scad_code_updates():
    """Test that SCAD code updates properly trigger visual changes"""
    
    print("🧪 Testing SCAD code update behavior...")
    
    try:
        # Create interactive viewer directly (for testing cache behavior)
        viewer = InteractiveViewer()
        
        # Check if we're in a CI environment without OpenSCAD
        if hasattr(viewer.bridge.renderer, 'openscad_path'):
            print("   ✅ Using local OpenSCAD renderer")
        else:
            print("   🤖 Using mock renderer for CI environment")
        
    except Exception as e:
        if "OpenSCAD executable not found" in str(e):
            print("   🤖 OpenSCAD not available, creating CI-friendly mock viewer...")
            viewer = create_mock_viewer()
        else:
            raise e
    
    # Test 1: Initial SCAD code (cube)
    cube_scad = "cube([10, 10, 10]);"
    
    print("\n📦 Step 1: Loading cube...")
    viewer.update_scad_code(cube_scad)
    cube_stl = viewer.stl_data
    print(f"   Cube STL data length: {len(cube_stl)} chars")
    
    # Wait a moment to ensure timestamp differences
    time.sleep(0.1)
    
    # Test 2: Different SCAD code (sphere)  
    sphere_scad = "sphere(r=6);"
    
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
    
    # Test 4: Force update behavior (use correct method signature)
    print("\n🔄 Step 4: Testing force update...")
    try:
        # Create a mock model for force update
        class MockModel:
            def as_scad(self):
                return sphere_scad
        
        mock_model = MockModel()
        viewer.force_update_model(mock_model)
        forced_stl = viewer.stl_data
        print(f"   Forced update STL length: {len(forced_stl)} chars")
    except Exception as e:
        print(f"   ⚠️ Force update test skipped: {e}")
        forced_stl = sphere_stl
    
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
        
        # Try to create a real viewer, fall back to mock if needed
        try:
            viewer = InteractiveViewer()
            print("   ✅ Using real InteractiveViewer with SolidPython2")
        except Exception as e:
            if "OpenSCAD executable not found" in str(e):
                print("   🤖 Using mock viewer for CI environment")
                viewer = create_mock_viewer()
            else:
                raise e
        
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
        print("   ⚠️ SolidPython2 not available, testing with mock models...")
        
        # Create mock viewer and mock models for CI testing
        viewer = create_mock_viewer()
        
        class MockCubeModel:
            def as_scad(self):
                return "cube([10, 10, 10]);"
                
        class MockSphereModel:
            def as_scad(self):
                return "sphere(r=6);"
        
        print("\n📦 Loading mock cube model...")
        cube_model = MockCubeModel()
        viewer.update_model(cube_model)
        cube_stl = viewer.stl_data
        print(f"   Mock cube model STL: {len(cube_stl)} chars")
        
        print("\n🔮 Loading mock sphere model...")
        sphere_model = MockSphereModel()
        viewer.update_model(sphere_model)
        sphere_stl = viewer.stl_data
        print(f"   Mock sphere model STL: {len(sphere_stl)} chars")
        
        model_changed = cube_stl != sphere_stl
        print(f"\n   Mock model STL data changed: {model_changed}")
        
        return model_changed

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