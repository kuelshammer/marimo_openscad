import marimo

__generated_with = "0.9.27"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    mo.md("""
    # 🔧 Mechanical Parts Showcase
    
    **Professional CAD modeling with SolidPython2**
    - Mechanical bracket with mounting holes
    - Parametric design with real-time updates
    - Production-ready models
    """)
    return mo,


@app.cell
def __(mo):
    # Mechanical Parameters
    width = mo.ui.slider(20, 60, value=40, label="🔩 Bracket Width")
    height = mo.ui.slider(15, 40, value=25, label="📏 Bracket Height") 
    thickness = mo.ui.slider(3, 8, value=5, label="🧱 Wall Thickness")
    hole_dia = mo.ui.slider(4, 12, value=6, label="🕳️ Hole Diameter")
    
    mo.vstack([
        mo.hstack([width, height]),
        mo.hstack([thickness, hole_dia])
    ])
    return height, hole_dia, thickness, width


@app.cell
def __(height, hole_dia, thickness, width):
    # L-shaped mechanical bracket
    from solid2 import cube, cylinder, union, difference
    
    w, h, t, hole_d = width.value, height.value, thickness.value, hole_dia.value
    
    # Basic L-shape
    horizontal_arm = cube([w, t, h])
    vertical_arm = cube([t, w, h])
    bracket_base = union()(horizontal_arm, vertical_arm)
    
    # Reinforcement diagonal
    diagonal_support = cube([w-t, 2, h]).translate([t, t, 0])
    bracket_with_support = union()(bracket_base, diagonal_support)
    
    # Mounting holes
    hole1 = cylinder(d=hole_d, h=h+2).translate([w/2, t/2, -1])
    hole2 = cylinder(d=hole_d, h=h+2).translate([t/2, w/2, -1])
    hole3 = cylinder(d=hole_d, h=h+2).translate([w-hole_d*1.5, t/2, -1])
    
    bracket = difference()(bracket_with_support, hole1, hole2, hole3)
    
    print(f"🔩 Mechanical Bracket: {w}×{h}×{t}mm, Holes: ⌀{hole_d}mm")
    
    bracket
    return bracket, bracket_base, bracket_with_support, diagonal_support, hole1, hole2, hole3, w


@app.cell
def __(bracket):
    # 3D Viewer
    from marimo_openscad import openscad_viewer
    
    viewer = openscad_viewer(bracket)
    viewer
    return viewer,


@app.cell
def __(bracket, mo):
    # Engineering Analysis
    scad_code = bracket.as_scad()
    
    mo.md(f"""
    ## 🔍 Engineering Analysis
    
    **Model Complexity:**
    - Code length: {len(scad_code)} characters
    - Lines: {len(scad_code.splitlines())}
    - Boolean operations: {scad_code.count('union') + scad_code.count('difference')}
    - Primitives: {scad_code.count('cube') + scad_code.count('cylinder')}
    
    **Features:**
    - ✅ L-shaped bracket design
    - ✅ Reinforcement diagonal for stability  
    - ✅ Three mounting holes for fasteners
    - ✅ Parametric design for customization
    - ✅ Production-ready CAD model
    
    **Manufacturing Notes:**
    - Material: Aluminum or steel recommended
    - Machining: CNC milling or 3D printing
    - Tolerances: ±0.1mm for holes
    """)
    return scad_code,


if __name__ == "__main__":
    app.run()