#!/usr/bin/env python3
"""
Quick Phase 2 WASM Test
"""

import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from marimo_openscad import openscad_viewer
    from solid2 import cube, union
    
    mo.md("# 🚀 Phase 2 WASM Test")
    return cube, mo, openscad_viewer, union


@app.cell  
def _(cube, mo, openscad_viewer, union):
    # Simple union test
    cube1 = cube([10, 10, 10])
    cube2 = cube([8, 8, 8]).translate([5, 0, 0])
    model = union()(cube1, cube2)
    
    # Test WASM renderer specifically
    viewer = openscad_viewer(model, renderer_type="wasm")
    
    scad_code = model.as_scad()
    
    mo.md(f"""
    **Phase 2 WASM Test - Union Operation**
    
    ```openscad
    {scad_code}
    ```
    """)
    return (viewer,)


@app.cell
def _(viewer):
    viewer
    return


if __name__ == "__main__":
    app.run()