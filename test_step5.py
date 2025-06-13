import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from src.marimo_openscad.viewer_step5 import openscad_viewer
    from solid2 import cube, cylinder, difference, union, sphere, intersection

    mo.md("# 🧪 Step 5: Real CSG Operations Debug Test")
    return cube, cylinder, difference, intersection, mo, openscad_viewer, sphere, union


@app.cell
def _(cube, openscad_viewer):
    # Test 1: Simple cube (baseline)
    simple_cube = cube([3, 3, 3])
    viewer_cube = openscad_viewer(simple_cube, renderer_type="auto")
    viewer_cube
    return


@app.cell
def _(cube, cylinder, difference, openscad_viewer):
    # Test 2: Difference operation (cube with hole)
    base = cube([4, 4, 2])
    hole = cylinder(r=1, h=3).translate([0, 0, -0.5])
    csg_difference = difference()(base, hole)

    viewer_diff = openscad_viewer(csg_difference, renderer_type="auto")
    viewer_diff
    return


@app.cell
def _(cube, openscad_viewer, sphere, union):
    # Test 3: Union operation (cube + sphere)
    box = cube([3, 3, 3])
    ball = sphere(r=1.8).translate([1.5, 1.5, 1.5])
    csg_union = union()(box, ball)

    viewer_union = openscad_viewer(csg_union, renderer_type="auto")
    viewer_union
    return


@app.cell
def _(cube, cylinder, intersection, openscad_viewer):
    # Test 4: Intersection operation (cube ∩ cylinder)
    big_cube = cube([4, 4, 4])
    big_cylinder = cylinder(r=2, h=4)
    csg_intersection = intersection()(big_cube, big_cylinder)

    viewer_intersect = openscad_viewer(csg_intersection, renderer_type="auto")
    viewer_intersect
    return


@app.cell
def _(cube, cylinder, difference, openscad_viewer, union):
    # Test 5: Complex CSG (multiple operations)
    base = cube([6, 6, 2])
    hole1 = cylinder(r=0.8, h=3).translate([1.5, 1.5, -0.5])
    hole2 = cylinder(r=0.8, h=3).translate([4.5, 1.5, -0.5])
    hole3 = cylinder(r=0.8, h=3).translate([1.5, 4.5, -0.5])
    hole4 = cylinder(r=0.8, h=3).translate([4.5, 4.5, -0.5])
    
    # Create union of all holes
    holes = union()(hole1, hole2, hole3, hole4)
    
    # Subtract holes from base
    complex_csg = difference()(base, holes)

    viewer_complex = openscad_viewer(complex_csg, renderer_type="auto")
    viewer_complex
    return


@app.cell
def _(mo):
    mo.md(
        """
    ## 🔍 Step 5 Debug-Ziele:
    - **Real CSG Rendering**: ✅ Echte OpenSCAD CSG-Operationen
    - **WASM Debug**: 🔍 Detaillierte WASM STL-Ausgabe-Analyse
    - **STL Parsing**: 🔍 Enhanced ASCII STL Parser mit Debugging
    - **Visual Feedback**: ✅ Grün = Echte STL, Rot = Fallback
    - **Enhanced UI**: ✅ Debug-Info, SCAD-Preview, Status-Tracking
    - **Mouse/Zoom**: ✅ Erweiterte Kamera-Kontrollen

    **Debug-Panel (oben rechts) zeigt STL-Analyse Details!**
    **SCAD-Preview (unten rechts) zeigt den generierten OpenSCAD-Code!**
    **Grüne Objekte = Echte STL von OpenSCAD | Rote Objekte = Fallback-Geometrie**
    
    Schau auf die Debug-Informationen und Renderer-Status!
    """
    )
    return


if __name__ == "__main__":
    app.run()