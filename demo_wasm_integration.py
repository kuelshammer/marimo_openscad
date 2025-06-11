"""
Demo: OpenSCAD WASM Integration in Marimo

This notebook demonstrates the new WASM-based OpenSCAD rendering
that works entirely in the browser without requiring local OpenSCAD installation.
"""

import marimo as mo

def __():
    mo.md("""
    # 🚀 OpenSCAD WASM Integration Demo
    
    Welcome to the OpenSCAD WASM integration demo! This notebook showcases browser-native 3D modeling 
    using OpenSCAD WebAssembly, eliminating the need for local OpenSCAD installation.
    
    ## Features
    - **Browser-Native Rendering**: No local OpenSCAD required
    - **Multiple Renderer Options**: WASM, Local, or Auto-selection  
    - **Full SolidPython2 Compatibility**: Seamless integration
    - **Real-time 3D Visualization**: Interactive Three.js viewer
    """)

def __():
    import sys
    from pathlib import Path
    
    # Add src to path for demo
    demo_src = Path("./src")
    if demo_src.exists():
        sys.path.insert(0, str(demo_src))
    
    from marimo_openscad.viewer import openscad_viewer
    
    mo.md("## Setup Complete ✅")

def __():
    mo.md("""
    ## 🎯 Demo 1: Auto Renderer Selection
    
    The auto renderer intelligently chooses between WASM and local OpenSCAD based on availability.
    In most cases, it will prefer WASM for better performance and no installation requirements.
    """)

def __():
    # Demo 1: Auto renderer with simple cube
    cube_scad = """
    // Simple colored cube
    color("red") 
    cube([15, 15, 15]);
    """
    
    viewer_auto = openscad_viewer(cube_scad, renderer_type="auto")
    
    # Display renderer info
    info = viewer_auto.get_renderer_info()
    
    mo.md(f"""
    **Renderer Information:**
    - Type: {info['type']} 
    - Active: {info['active_renderer']}
    - Status: {info['status']}
    - WASM Supported: {info['wasm_supported']}
    """)

def __():
    return viewer_auto

def __():
    mo.md("""
    ## 🚀 Demo 2: Explicit WASM Renderer
    
    Force the use of WASM renderer for guaranteed browser-native execution.
    """)

def __():
    # Demo 2: Explicit WASM renderer with sphere
    sphere_scad = """
    // Smooth sphere with high resolution
    $fn = 64;
    color("blue") 
    sphere(r=10);
    """
    
    viewer_wasm = openscad_viewer(sphere_scad, renderer_type="wasm")
    return viewer_wasm

def __():
    mo.md("""
    ## 🔧 Demo 3: Local Renderer (Fallback)
    
    Use local OpenSCAD installation when available. This is useful for 
    complex models or when specific OpenSCAD features are needed.
    """)

def __():
    # Demo 3: Local renderer with complex model
    complex_scad = """
    // Complex difference operation
    difference() {
        // Main body
        union() {
            color("green") cube([20, 20, 20]);
            color("yellow") translate([0, 0, 20]) sphere(r=12);
        }
        
        // Holes
        for(i = [0:2]) {
            for(j = [0:2]) {
                translate([i*7 + 3, j*7 + 3, -1])
                cylinder(r=2, h=25);
            }
        }
        
        // Central hole
        cylinder(r=6, h=40, center=true);
    }
    """
    
    try:
        viewer_local = openscad_viewer(complex_scad, renderer_type="local")
        result = viewer_local
    except Exception as e:
        # Fallback to WASM if local fails
        mo.md(f"⚠️ Local renderer failed: {e}")
        mo.md("🚀 Falling back to WASM renderer...")
        viewer_local = openscad_viewer(complex_scad, renderer_type="wasm")
        result = viewer_local
    
    return result

def __():
    mo.md("""
    ## 🎮 Interactive Demo: Real-time Model Updates
    
    Modify the SCAD code below and see the 3D model update in real-time!
    """)

def __():
    # Interactive demo with UI controls
    scad_input = mo.ui.text_area(
        value="""// Interactive SCAD Model
// Modify this code and run to see updates!

$fn = 32;

// Main shape
difference() {
    // Outer shape
    union() {
        cube([20, 20, 10]);
        translate([10, 10, 10])
        cylinder(r=8, h=10);
    }
    
    // Inner cutouts  
    translate([10, 10, -1])
    cylinder(r=5, h=22);
    
    // Side holes
    for(angle = [0:60:300]) {
        rotate([0, 0, angle])
        translate([15, 0, 5])
        cylinder(r=2, h=10, center=true);
    }
}""",
        placeholder="Enter OpenSCAD code here...",
        rows=20
    )
    
    renderer_selector = mo.ui.dropdown(
        options=["auto", "wasm", "local"],
        value="auto",
        label="Renderer Type:"
    )
    
    mo.md("### SCAD Code Editor")
    return mo.hstack([
        mo.vstack([scad_input, renderer_selector]),
    ])

def __():
    if scad_input.value.strip():
        interactive_viewer = openscad_viewer(
            scad_input.value, 
            renderer_type=renderer_selector.value
        )
        return interactive_viewer
    else:
        return mo.md("⏳ Enter SCAD code above to see the 3D model...")

def __():
    mo.md("""
    ## 📊 Performance Comparison
    
    Compare rendering performance between different renderer types.
    """)

def __():
    import time
    
    # Performance test models
    test_models = {
        "Simple": "cube([10, 10, 10]);",
        "Medium": """
            difference() {
                cube([15, 15, 15]);
                sphere(r=8);
            }
        """,
        "Complex": """
            union() {
                for(i = [0:4]) {
                    for(j = [0:4]) {
                        translate([i*3, j*3, 0])
                        cylinder(r=1, h=5);
                    }
                }
            }
        """
    }
    
    results = []
    
    for model_name, scad_code in test_models.items():
        for renderer_type in ["wasm", "local"]:
            try:
                start_time = time.time()
                viewer = openscad_viewer(scad_code, renderer_type=renderer_type)
                end_time = time.time()
                
                duration = (end_time - start_time) * 1000  # Convert to ms
                
                results.append({
                    "Model": model_name,
                    "Renderer": renderer_type,
                    "Time (ms)": f"{duration:.2f}",
                    "Status": "✅ Success"
                })
                
            except Exception as e:
                results.append({
                    "Model": model_name,
                    "Renderer": renderer_type,  
                    "Time (ms)": "N/A",
                    "Status": f"❌ {str(e)[:30]}..."
                })
    
    # Display results table
    import pandas as pd
    df = pd.DataFrame(results)
    
    mo.md("### Performance Results")
    return mo.ui.table(df)

def __():
    mo.md("""
    ## 🛠️ Technical Details
    
    ### WASM Renderer Features
    - **OpenSCAD WASM 2022.03.20**: Latest stable WASM build
    - **Manifold Engine**: Advanced geometric operations
    - **Font Support**: Text rendering capabilities  
    - **MCAD Library**: Additional geometric functions
    - **Web Worker Support**: Non-blocking rendering
    
    ### Integration Architecture
    ```
    SolidPython2 → OpenSCAD WASM → STL Binary → Three.js → WebGL
                     ↑
             Runs entirely in browser
    ```
    
    ### Benefits
    - **No Installation**: Works out of the box
    - **Cross-Platform**: Consistent behavior everywhere
    - **Offline Capable**: Works without internet after initial load
    - **Fast Setup**: Immediate availability
    - **Secure**: Sandboxed execution environment
    
    ### Migration Path
    Existing code works unchanged! Simply specify `renderer_type="wasm"` or let 
    auto-selection handle it for you.
    """)

def __():
    mo.md("""
    ## 🎉 Next Steps
    
    1. **Try the Examples**: Modify the SCAD code in the interactive demo
    2. **Explore Features**: Test complex models with different renderers
    3. **Performance Testing**: Compare WASM vs local rendering
    4. **Integration**: Use in your own marimo notebooks
    
    **Happy 3D Modeling! 🚀**
    """)

if __name__ == "__main__":
    app = mo.App(width="full")
    app.run()