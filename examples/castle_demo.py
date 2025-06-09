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
    
    mo.md("# 🏰 Interactive Castle Demo - Marimo + OpenSCAD")
    return Path, mo, project_root, sys


@app.cell
def _():
    from solid2 import cube, cylinder
    from marimo_openscad import InteractiveViewer
    return InteractiveViewer, cube, cylinder


@app.cell
def _(mo):
    # Interactive parameters for the castle
    wall_size = mo.ui.slider(300, 500, value=400, label="Wall Size (mm)")
    wall_height = mo.ui.slider(30, 80, value=50, label="Wall Height (mm)")
    tower_height = mo.ui.slider(80, 150, value=100, label="Tower Height (mm)")
    tower_radius = mo.ui.slider(30, 80, value=50, label="Tower Radius (mm)")
    
    mo.md("## Castle Parameters")
    [wall_size, wall_height, tower_height, tower_radius]
    return tower_height, tower_radius, wall_height, wall_size


@app.cell
def _(cube, cylinder, tower_height, tower_radius, wall_height, wall_size):
    # Create the SolidPython2 castle model
    def create_castle():
        size = wall_size.value
        height = wall_height.value
        t_height = tower_height.value
        t_radius = tower_radius.value
        
        # Start with empty model
        model = cube(0)
        
        # Outer walls
        model += cube(size, size, height, center=True)
        
        # Hollow interior (smaller cube to subtract)
        model -= cube(size-20, size-20, height, center=True)
        
        # Add towers at corners
        for i in range(4):
            tower = cylinder(r=t_radius, h=t_height, center=True)
            # Position tower at corner
            x_pos = (size/2 - t_radius) if i % 2 == 0 else -(size/2 - t_radius)
            y_pos = (size/2 - t_radius) if i < 2 else -(size/2 - t_radius)
            tower = tower.translate([x_pos, y_pos, t_height/2 - height/2])
            model += tower
        
        return model
    
    castle_model = create_castle()
    castle_model
    return castle_model, create_castle


@app.cell
def _(InteractiveViewer, castle_model):
    # 3D viewer with interactive controls
    viewer = InteractiveViewer()
    viewer.update_model(castle_model)
    viewer
    return viewer,


@app.cell
def _(castle_model):
    # Export functionality
    castle_model.save_as_scad("castle_model.scad")
    "✅ Model saved as castle_model.scad"
    return


@app.cell
def _(mo, tower_height, tower_radius, wall_height, wall_size):
    mo.md(f"""
    **Current Castle Configuration:**
    - Wall Size: {wall_size.value}×{wall_size.value}mm
    - Wall Height: {wall_height.value}mm  
    - Tower Height: {tower_height.value}mm
    - Tower Radius: {tower_radius.value}mm
    
    **3D Controls:**
    - **Mouse Drag**: Rotate camera around castle
    - **Mouse Wheel**: Zoom in/out
    - **Automatic Updates**: Model updates when you change parameters
    """)
    return


if __name__ == "__main__":
    app.run()