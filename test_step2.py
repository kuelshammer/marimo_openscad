import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from src.marimo_openscad.viewer_step2 import openscad_viewer
    from solid2 import cube

    mo.md("# 🧪 Step 2: Three.js Integration Test")
    return cube, mo, openscad_viewer


@app.cell
def _(cube, openscad_viewer):
    # Test Three.js viewer
    simple_cube = cube([10, 10, 10])
    viewer = openscad_viewer(simple_cube, renderer_type="step2-threejs")
    viewer
    return


@app.cell
def _(mo):
    mo.md(
        """
    ## ✅ Step 2 Ziele:
    - **Three.js Loading**: ✅ CDN-Integration
    - **WebGL Context**: ✅ Renderer erstellen
    - **Basic Geometry**: ✅ Würfel-Wireframe
    - **Animation**: ✅ Rotation
    - **Error Handling**: ✅ Robuste Fallbacks

    **Wenn du einen rotierenden Drahtrahmen-Würfel siehst, ist Step 2 erfolgreich!**
    """
    )
    return


if __name__ == "__main__":
    app.run()
