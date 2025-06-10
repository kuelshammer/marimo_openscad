import marimo

__generated_with = "0.9.27"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    mo.md("""
    # 🎯 Marimo-OpenSCAD Simple Demo
    
    **Interactive 3D CAD modeling with SolidPython2**
    - Reaktive Parameter mit Marimo-Widgets
    - Echte OpenSCAD-Pipeline: SolidPython2 → STL → Three.js
    - Inspired by JupyterSCAD architecture
    """)
    return mo,


@app.cell
def __(mo):
    # Interactive Parameters
    size = mo.ui.slider(8, 25, value=15, label="📦 Cube Size")
    height = mo.ui.slider(5, 30, value=12, label="📏 Height")
    
    mo.hstack([size, height])
    return height, size


@app.cell
def __(height, size):
    # SolidPython2 Model - normal syntax
    from solid2 import cube, cylinder, difference, translate
    
    # Cube with hole - simple but effective
    base_cube = cube([size.value, size.value, height.value])
    hole = cylinder(r=size.value/4, h=height.value + 2).translate([size.value/2, size.value/2, -1])
    
    model = difference()(base_cube, hole)
    
    print(f"🔧 Model: {size.value}×{size.value}×{height.value} cube with ⌀{size.value/2} hole")
    
    model
    return base_cube, hole, model


@app.cell
def __(model):
    # 3D Viewer
    from marimo_openscad import openscad_viewer
    
    viewer = openscad_viewer(model)
    viewer
    return viewer,


@app.cell
def __(model, mo):
    # Generated SCAD Code
    scad_code = model.as_scad()
    
    mo.md(f"""
    ## 📊 Pipeline Analysis
    
    **Generated Code:** {len(scad_code)} characters  
    **Operations:** difference() with cube() and cylinder()
    
    **Pipeline:**
    1. ✅ SolidPython2 → SCAD conversion
    2. ✅ SCAD → OpenSCAD CLI → STL
    3. ✅ STL → Three.js BufferGeometry
    4. ✅ WebGL rendering with OrbitControls
    
    <details>
    <summary>🔍 Generated SCAD Code</summary>
    
    ```openscad
    {scad_code}
    ```
    </details>
    """)
    return scad_code,


if __name__ == "__main__":
    app.run()