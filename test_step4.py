import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from src.marimo_openscad.viewer_step4 import openscad_viewer
    from solid2 import cube, cylinder, difference, union, sphere

    mo.md("# 🧪 Step 4: Real OpenSCAD Integration Test")
    return cube, cylinder, difference, mo, openscad_viewer, sphere, union


@app.cell
def _(cube, openscad_viewer):
    # Test with simple cube (should use real OpenSCAD)
    simple_cube = cube([2, 2, 2])
    viewer_cube = openscad_viewer(simple_cube, renderer_type="auto")
    viewer_cube
    return


@app.cell
def _(cube, cylinder, difference, openscad_viewer):
    # Test with CSG operation (more complex)
    base = cube([4, 4, 2])
    hole = cylinder(r=1, h=3).translate([0, 0, -0.5])
    csg_model = difference()(base, hole)

    viewer_csg = openscad_viewer(csg_model, renderer_type="auto")
    viewer_csg
    return


@app.cell
def _(cube, openscad_viewer, sphere, union):
    # Test with union operation
    box = cube([3, 3, 3])
    ball = sphere(r=2).translate([2, 2, 2])
    union_model = union()(box, ball)

    viewer_union = openscad_viewer(union_model, renderer_type="auto")
    viewer_union
    return


@app.cell
def _(mo):
    mo.md(
        """
    ## ✅ Step 4 Ziele:
    - **WASM Renderer**: ✅ Primärer OpenSCAD-Renderer
    - **Local Fallback**: ✅ OpenSCAD CLI als Backup
    - **Real STL Data**: ✅ Echte OpenSCAD-Ausgabe
    - **CSG Operations**: ✅ Difference, Union, etc.
    - **Error Handling**: ✅ Robuste Fallback-Kette
    - **Status Reporting**: ✅ Renderer-Info im Widget

    **Schau auf die Renderer-Info (unten links) - zeigt es "wasm_success" oder "local_success"?**
    """
    )
    return


if __name__ == "__main__":
    app.run()
