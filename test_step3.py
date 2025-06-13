import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from src.marimo_openscad.viewer_step3 import openscad_viewer
    from solid2 import cube, cylinder, difference

    mo.md("# 🧪 Step 3: STL Parsing + SolidPython2 Test")
    return cube, cylinder, difference, mo, openscad_viewer


@app.cell
def _(cube, openscad_viewer):
    # Test with simple cube
    simple_cube = cube([2, 2, 2])
    viewer_cube = openscad_viewer(simple_cube, renderer_type="step3-stl")
    viewer_cube
    return


@app.cell
def _(cube, cylinder, difference, openscad_viewer):
    # Test with more complex model
    base = cube([3, 3, 1])
    hole = cylinder(r=0.5, h=2).translate([0, 0, -0.5])
    complex_model = difference()(base, hole)

    viewer_complex = openscad_viewer(complex_model, renderer_type="step3-complex")
    viewer_complex
    return


@app.cell
def _(mo):
    mo.md(
        """
    ## ✅ Step 3 Ziele:
    - **SolidPython2 → SCAD**: ✅ Code-Generierung
    - **SCAD → STL**: ✅ OpenSCAD-Rendering (oder Fallback)
    - **STL Parsing**: ✅ ASCII-STL-Parser
    - **Three.js Geometry**: ✅ BufferGeometry-Erstellung
    - **Lighting & Materials**: ✅ Realistische Darstellung
    - **Model Centering**: ✅ Automatische Skalierung

    **Wenn du 3D-Modelle (statt Wireframes) siehst, ist Step 3 erfolgreich!**
    """
    )
    return


if __name__ == "__main__":
    app.run()
