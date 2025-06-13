import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from src.marimo_openscad.viewer_step1 import openscad_viewer
    from solid2 import cube

    mo.md("# 🧪 Step 1: Basic Container Test")
    return cube, mo, openscad_viewer


@app.cell
def _(cube, openscad_viewer):
    # Test basic viewer
    simple_cube = cube([10, 10, 10])
    viewer = openscad_viewer(simple_cube, renderer_type="step1-test")
    viewer
    return


@app.cell
def _(mo):
    mo.md(
        """
    ## ✅ Step 1 Ziele:
    - **HTML Container**: ✅ Rendering
    - **JavaScript Execution**: ✅ Keine Syntax-Fehler  
    - **Model Parameter**: ✅ Wird übertragen
    - **Basis für Step 2**: ✅ Bereit
    """
    )
    return


if __name__ == "__main__":
    app.run()
