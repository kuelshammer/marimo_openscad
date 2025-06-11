#!/usr/bin/env python3
"""Test the mock cache functionality"""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test the mock functionality directly
from test_cache_fix import create_mock_viewer

def test_mock_functionality():
    print("🧪 Testing mock viewer functionality...")
    
    viewer = create_mock_viewer()
    
    # Test cube
    print("\n📦 Testing cube...")
    viewer.update_scad_code("cube([10, 10, 10]);")
    cube_stl = viewer.stl_data
    print(f"   Cube STL length: {len(cube_stl)} chars")
    
    # Test sphere
    print("\n🔮 Testing sphere...")
    viewer.update_scad_code("sphere(r=6);")
    sphere_stl = viewer.stl_data
    print(f"   Sphere STL length: {len(sphere_stl)} chars")
    
    # Test difference
    stl_changed = cube_stl != sphere_stl
    print(f"\n🔍 STL data changed: {stl_changed}")
    
    if stl_changed:
        print("✅ SUCCESS: Mock viewer produces different outputs for different shapes")
    else:
        print("❌ FAILURE: Mock viewer produces same output")
    
    return stl_changed

if __name__ == "__main__":
    success = test_mock_functionality()
    sys.exit(0 if success else 1)