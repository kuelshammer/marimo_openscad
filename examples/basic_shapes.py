import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import sys
    from pathlib import Path
    
    # Add src to path for development
    project_root = Path(__file__).parent.parent / "src"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    mo.md("# 📐 Basic Shapes Demo - SolidPython2 + Marimo")
    return Path, mo, project_root, sys


@app.cell
def _():
    from solid2 import cube, sphere, cylinder, translate
    from marimo_openscad import InteractiveViewer
    return InteractiveViewer, cube, cylinder, sphere, translate


@app.cell
def _(mo):
    # Interactive parameters
    cube_size = mo.ui.slider(5, 25, value=15, label="Cube Size")
    sphere_radius = mo.ui.slider(3, 15, value=8, label="Sphere Radius")
    cylinder_height = mo.ui.slider(5, 30, value=20, label="Cylinder Height")
    cylinder_radius = mo.ui.slider(2, 10, value=5, label="Cylinder Radius")
    
    mo.md("## Shape Parameters")
    [cube_size, sphere_radius, cylinder_height, cylinder_radius]
    return cube_size, cylinder_height, cylinder_radius, sphere_radius


@app.cell
def _(cube, cube_size, cylinder, cylinder_height, cylinder_radius, sphere, sphere_radius, translate):
    # Create composite model
    def create_composite_model():
        # Base cube
        base = cube(cube_size.value, center=True)
        
        # Sphere on top
        ball = translate([0, 0, cube_size.value/2 + sphere_radius.value])(
            sphere(sphere_radius.value)
        )
        
        # Cylinder through the middle
        hole = cylinder(r=cylinder_radius.value, h=cylinder_height.value, center=True)
        
        # Combine: cube + sphere - cylinder hole
        model = base + ball - hole
        
        return model
    
    composite_model = create_composite_model()
    composite_model
    return composite_model, create_composite_model


@app.cell
def _(InteractiveViewer, composite_model):
    # 3D viewer
    viewer = InteractiveViewer()
    viewer.update_model(composite_model)
    viewer
    return viewer,


@app.cell
def _(mo, cube_size, cylinder_height, cylinder_radius, sphere_radius):
    mo.md(f"""
    **Current Model:**
    - Cube: {cube_size.value}×{cube_size.value}×{cube_size.value}mm
    - Sphere: radius {sphere_radius.value}mm
    - Cylinder hole: radius {cylinder_radius.value}mm, height {cylinder_height.value}mm
    
    **Model Construction:**
    ```python
    model = cube + sphere - cylinder_hole
    ```
    """)
    return


if __name__ == "__main__":
    app.run()