#!/usr/bin/env python3
"""
Phase 2 Integration Test

Test the bundled JavaScript viewer to validate Phase 2 improvements.
"""

import sys
sys.path.insert(0, 'src')

from marimo_openscad.viewer_phase2 import openscad_viewer_phase2
from solid2 import cube, sphere, union

def test_phase2_viewer():
    """Test Phase 2 viewer with bundled JavaScript"""
    print("🚀 Phase 2 Integration Test")
    
    # Create simple model
    model = cube([2, 2, 2])
    
    # Create Phase 2 viewer
    viewer = openscad_viewer_phase2(model, renderer_type="auto")
    
    print(f"✅ Viewer created: {type(viewer)}")
    print(f"📊 STL Data Length: {len(viewer.stl_data)} characters")
    print(f"🔧 Renderer Type: {viewer.renderer_type}")
    print(f"📋 Renderer Status: {viewer.renderer_status}")
    print(f"📄 SCAD Code: {viewer.scad_code[:50]}...")
    
    # Check if bundle loading works
    try:
        bundle_content = viewer._get_bundled_javascript()
        print(f"✅ Bundle loaded: {len(bundle_content)} characters")
        print(f"🔍 Bundle preview: {bundle_content[:100]}...")
        
        # Check ESM generation
        esm_content = viewer._esm
        print(f"✅ ESM generated: {len(esm_content)} characters")
        
        if "Phase 2" in esm_content:
            print("✅ Phase 2 markers found in ESM")
        else:
            print("❌ Phase 2 markers missing in ESM")
            
    except Exception as e:
        print(f"❌ Bundle loading failed: {e}")
    
    return viewer

if __name__ == "__main__":
    viewer = test_phase2_viewer()
    print("\n🎯 Phase 2 Test Complete")
    print(f"Final Status: {viewer.renderer_status}")