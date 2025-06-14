import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    # Einfacher Import-Test
    import marimo as mo
    from marimo_openscad import openscad_viewer
    from solid2 import cube, cylinder, difference

    mo.md("# 🎯 Einfacher PyPI Test")
    return cube, mo, openscad_viewer


@app.cell
def _(mo):
    # UI-Parameter
    size_slider = mo.ui.slider(5, 20, value=10, label="Größe", show_value=True)
    size_slider
    return size_slider,


@app.cell
def _(cube, size_slider):
    # Einfaches Modell
    simple_cube = cube([size_slider.value, size_slider.value, size_slider.value])
    return simple_cube,


@app.cell
def _(openscad_viewer, simple_cube):
    # 3D Viewer
    viewer = openscad_viewer(simple_cube, renderer_type="auto")
    return viewer,


@app.cell
def _(viewer):
    viewer


@app.cell
def _(mo):
    mo.md("""✅ **Test erfolgreich!** Das PyPI-Package funktioniert.""")


if __name__ == "__main__":
    app.run()
